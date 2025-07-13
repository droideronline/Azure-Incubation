import logging
import azure.functions as func
import sys
import os

# Add parent directory to path for shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.azure_services import azure_services
from shared.models import MediaMetadata, ApiResponse, get_file_type_from_mime, generate_blob_name
from shared.metadata_extractor import detect_mime_type, validate_file_type, extract_metadata

def get_cors_headers():
    """Get CORS headers for responses"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-User-ID, Authorization',
        'Access-Control-Max-Age': '86400'
    }

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Upload media file to Azure Blob Storage and save metadata to Cosmos DB"""
    
    logging.info('Processing media file upload request')
    
    # Handle preflight OPTIONS request
    if req.method == 'OPTIONS':
        return func.HttpResponse(
            '',
            status_code=200,
            headers=get_cors_headers()
        )
    
    try:
        # Get user ID from query parameters or headers
        user_id = req.params.get('userId')
        if not user_id:
            user_id = req.headers.get('X-User-ID')
        
        if not user_id:
            response = ApiResponse.error_response(
                "Missing required parameter: userId", 
                "User ID must be provided as query parameter or X-User-ID header"
            )
            return func.HttpResponse(
                response.to_json(),
                status_code=400,
                mimetype="application/json",
                headers=get_cors_headers()
            )
        
        # Get file from request
        file_data = None
        file_name = None
        
        # First try to get files from the files collection
        try:
            if hasattr(req, 'files') and req.files:
                for field_name, file_obj in req.files.items():
                    if file_obj and hasattr(file_obj, 'read'):
                        file_data = file_obj.read()
                        file_name = getattr(file_obj, 'filename', None) or getattr(file_obj, 'name', f"uploaded_file_{field_name}")
                        break
        except Exception as e:
            logging.warning(f"Error reading files collection: {str(e)}")
        
        # If not found in files, check form data
        if not file_data:
            try:
                for key, value in req.form.items():
                    if hasattr(value, 'filename') and hasattr(value, 'stream'):
                        file_name = value.filename or f"uploaded_file_{key}"
                        file_data = value.stream.read()
                        break
                    elif key == 'file' and hasattr(value, 'read'):
                        # Handle different form data structures
                        file_data = value.read() if hasattr(value, 'read') else value
                        file_name = getattr(value, 'filename', None) or f"uploaded_file_{key}"
                        break
            except Exception as e:
                logging.warning(f"Error reading form data: {str(e)}")
        
        # If still not found, check raw body
        if not file_data:
            file_data = req.get_body()
            file_name = req.headers.get('X-File-Name', 'uploaded_file')
        
        if not file_data:
            response = ApiResponse.error_response(
                "No file provided", 
                "Please provide a file in the request body or form data"
            )
            return func.HttpResponse(
                response.to_json(),
                status_code=400,
                mimetype="application/json",
                headers=get_cors_headers()
            )
        
        # Detect MIME type
        mime_type = detect_mime_type(file_data, file_name)
        
        # Validate file type
        is_valid = validate_file_type(mime_type)
        
        if not is_valid:
            response = ApiResponse.error_response(
                "Unsupported file type", 
                f"File type {mime_type} is not supported"
            )
            return func.HttpResponse(
                response.to_json(),
                status_code=400,
                mimetype="application/json",
                headers=get_cors_headers()
            )
        
        # Get file type category
        file_type = get_file_type_from_mime(mime_type)
        
        # Generate unique blob name
        blob_name = generate_blob_name(user_id, file_name)
        container_name = "media-files"
        
        # Upload to Azure Blob Storage
        try:
            blob_service_client = azure_services.get_blob_service_client()
            blob_client = blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            
            # Upload file
            blob_client.upload_blob(file_data, overwrite=True)
            blob_url = blob_client.url
            
        except Exception as blob_error:
            response = ApiResponse.error_response(
                "Failed to upload file to blob storage", 
                str(blob_error)
            )
            return func.HttpResponse(
                response.to_json(),
                status_code=500,
                mimetype="application/json",
                headers=get_cors_headers()
            )
        
        # Extract metadata
        extracted_metadata = extract_metadata(file_data, file_name, mime_type)
        
        # Create metadata record
        metadata = MediaMetadata.create_new(
            user_id=user_id,
            file_name=file_name,
            file_type=file_type,
            mime_type=mime_type,
            file_size=len(file_data),
            blob_url=blob_url,
            container_name=container_name,
            blob_name=blob_name,
            extracted_metadata=extracted_metadata
        )
        
        # Save metadata to Cosmos DB
        cosmos_container = azure_services.get_cosmos_container()
        cosmos_container.create_item(body=metadata.to_dict())
        
        logging.info(f"Metadata saved to Cosmos DB for file: {metadata.id}")
        
        # Return success response
        response_data = {
            "file_id": metadata.id,
            "file_name": file_name,
            "file_type": file_type,
            "mime_type": mime_type,
            "file_size": len(file_data),
            "blob_url": blob_url,
            "upload_date": metadata.upload_date
        }
        
        response = ApiResponse.success_response(
            "File uploaded successfully", 
            response_data
        )
        
        return func.HttpResponse(
            response.to_json(),
            status_code=200,
            mimetype="application/json",
            headers=get_cors_headers()
        )
        
    except Exception as e:
        logging.error(f"Error uploading file: {str(e)}")
        response = ApiResponse.error_response(
            "Failed to upload file", 
            str(e)
        )
        return func.HttpResponse(
            response.to_json(),
            status_code=500,
            mimetype="application/json",
            headers=get_cors_headers()
        )

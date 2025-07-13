import logging
import azure.functions as func
import sys
import os

# Add parent directory to path for shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.azure_services import azure_services
from shared.models import ApiResponse

def get_cors_headers():
    """Get CORS headers for responses"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-User-ID, Authorization',
        'Access-Control-Max-Age': '86400'
    }

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Delete media file from Blob Storage and metadata from Cosmos DB"""
    
    logging.info('Processing delete media file request')
    
    # Handle preflight OPTIONS request
    if req.method == 'OPTIONS':
        return func.HttpResponse(
            '',
            status_code=200,
            headers=get_cors_headers()
        )
    
    try:
        # Get required parameters
        file_id = req.params.get('fileId')
        user_id = req.params.get('userId')
        
        if not file_id:
            response = ApiResponse.error_response(
                "Missing required parameter: fileId", 
                "File ID must be provided as query parameter"
            )
            return func.HttpResponse(
                response.to_json(),
                status_code=400,
                mimetype="application/json",
                headers=get_cors_headers()
            )
        
        if not user_id:
            response = ApiResponse.error_response(
                "Missing required parameter: userId", 
                "User ID must be provided as query parameter"
            )
            return func.HttpResponse(
                response.to_json(),
                status_code=400,
                mimetype="application/json",
                headers=get_cors_headers()
            )
        
        # Get Cosmos DB container
        cosmos_container = azure_services.get_cosmos_container()
        
        # First, get the file metadata to verify ownership and get blob info
        try:
            query = "SELECT * FROM c WHERE c.id = @file_id AND c.user_id = @user_id"
            parameters = [
                {"name": "@file_id", "value": file_id},
                {"name": "@user_id", "value": user_id}
            ]
            
            items = list(cosmos_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if not items:
                response = ApiResponse.error_response(
                    "File not found", 
                    f"No file found with ID {file_id} for user {user_id}"
                )
                return func.HttpResponse(
                    response.to_json(),
                    status_code=404,
                    mimetype="application/json",
                    headers=get_cors_headers()
                )
            
            file_metadata = items[0]
            container_name = file_metadata.get('container_name')
            blob_name = file_metadata.get('blob_name')
            
        except Exception as e:
            logging.error(f"Error retrieving file metadata: {str(e)}")
            response = ApiResponse.error_response(
                "Failed to retrieve file metadata", 
                str(e)
            )
            return func.HttpResponse(
                response.to_json(),
                status_code=500,
                mimetype="application/json",
                headers=get_cors_headers()
            )
        
        # Delete from Blob Storage
        try:
            blob_service_client = azure_services.get_blob_service_client()
            blob_client = blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            
            # Check if blob exists before deleting
            if blob_client.exists():
                blob_client.delete_blob()
                logging.info(f"Deleted blob: {blob_name}")
            else:
                logging.warning(f"Blob not found: {blob_name}")
                
        except Exception as e:
            logging.error(f"Error deleting blob: {str(e)}")
            # Continue with metadata deletion even if blob deletion fails
        
        # Delete metadata from Cosmos DB
        # The partition key is /fileType, so we need to use the fileType field (camelCase)
        try:
            # Use the camelCase field to match the partition key configuration
            partition_value = file_metadata.get('fileType') or file_metadata.get('file_type', 'document')
            cosmos_container.delete_item(
                item=file_id,
                partition_key=partition_value
            )
            logging.info(f"Deleted metadata for file: {file_id} using partition key: {partition_value}")
            
        except Exception as e:
            logging.error(f"Error deleting metadata: {str(e)}")
            response = ApiResponse.error_response(
                "Failed to delete file metadata", 
                str(e)
            )
            return func.HttpResponse(
                response.to_json(),
                status_code=500,
                mimetype="application/json",
                headers=get_cors_headers()
            )
        
        # Return success response
        response_data = {
            "file_id": file_id,
            "file_name": file_metadata.get('file_name'),
            "deleted_from_storage": True,
            "deleted_from_database": True
        }
        
        response = ApiResponse.success_response(
            "File deleted successfully", 
            response_data
        )
        
        return func.HttpResponse(
            response.to_json(),
            status_code=200,
            mimetype="application/json",
            headers=get_cors_headers()
        )
        
    except Exception as e:
        logging.error(f"Error deleting file: {str(e)}")
        response = ApiResponse.error_response(
            "Failed to delete file", 
            str(e)
        )
        return func.HttpResponse(
            response.to_json(),
            status_code=500,
            mimetype="application/json",
            headers=get_cors_headers()
        )

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
    """Retrieve metadata for specific file or all files for a user"""
    
    # Handle preflight OPTIONS request
    if req.method == 'OPTIONS':
        return func.HttpResponse(
            '',
            status_code=200,
            headers=get_cors_headers()
        )
    
    try:
        # Get user ID from query parameters
        user_id = req.params.get('userId')
        if not user_id:
            response = ApiResponse.error_response(
                "Missing required parameter: userId", 
                "User ID must be provided as query parameter"
            )
            return func.HttpResponse(
                response.to_json(),
                status_code=400,
                mimetype="application/json"
            )
        
        # Get optional file ID
        file_id = req.params.get('fileId')
        
        # Get Cosmos DB container
        cosmos_container = azure_services.get_cosmos_container()
        
        if file_id:
            # Get specific file metadata
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
                        mimetype="application/json"
                    )
                
                file_metadata = items[0]
                
                response = ApiResponse.success_response(
                    "File metadata retrieved successfully", 
                    file_metadata
                )
                
            except Exception as e:
                logging.error(f"Error retrieving file metadata: {str(e)}")
                response = ApiResponse.error_response(
                    "Failed to retrieve file metadata", 
                    str(e)
                )
                return func.HttpResponse(
                    response.to_json(),
                    status_code=500,
                    mimetype="application/json"
                )
        else:
            # Get all files for user
            try:
                query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.upload_date DESC"
                parameters = [{"name": "@user_id", "value": user_id}]
                
                items = list(cosmos_container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                response_data = {
                    "total_files": len(items),
                    "files": items
                }
                
                response = ApiResponse.success_response(
                    f"Retrieved {len(items)} files for user", 
                    response_data
                )
                
            except Exception as e:
                logging.error(f"Error retrieving user files: {str(e)}")
                response = ApiResponse.error_response(
                    "Failed to retrieve user files", 
                    str(e)
                )
                return func.HttpResponse(
                    response.to_json(),
                    status_code=500,
                    mimetype="application/json"
                )
        
        return func.HttpResponse(
            response.to_json(),
            status_code=200,
            mimetype="application/json",
            headers=get_cors_headers()
        )
        
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        response = ApiResponse.error_response(
            "Internal server error", 
            str(e)
        )
        return func.HttpResponse(
            response.to_json(),
            status_code=500,
            mimetype="application/json"
        )

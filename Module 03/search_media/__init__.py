import logging
import azure.functions as func
import sys
import os
from datetime import datetime

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
    """Search and filter media files by type, tags, or date range"""
    
    # Handle preflight OPTIONS request
    if req.method == 'OPTIONS':
        return func.HttpResponse(
            '',
            status_code=200,
            headers=get_cors_headers()
        )
    
    try:
        # Get required user ID
        user_id = req.params.get('userId')
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
        
        # Get optional filter parameters
        file_type = req.params.get('fileType')  # image, video, audio, document
        tag = req.params.get('tag')
        from_date = req.params.get('fromDate')  # ISO format: 2024-01-01T00:00:00
        to_date = req.params.get('toDate')      # ISO format: 2024-12-31T23:59:59
        
        # Build query and parameters
        query_conditions = ["c.user_id = @user_id"]
        parameters = [{"name": "@user_id", "value": user_id}]
        
        # Add file type filter
        if file_type:
            valid_types = ['image', 'video', 'audio', 'document']
            if file_type.lower() not in valid_types:
                response = ApiResponse.error_response(
                    "Invalid file type", 
                    f"File type must be one of: {', '.join(valid_types)}"
                )
                return func.HttpResponse(
                    response.to_json(),
                    status_code=400,
                    mimetype="application/json",
                    headers=get_cors_headers()
                )
            query_conditions.append("c.file_type = @file_type")
            parameters.append({"name": "@file_type", "value": file_type.lower()})
        
        # Add tag filter
        if tag:
            query_conditions.append("ARRAY_CONTAINS(c.tags, @tag)")
            parameters.append({"name": "@tag", "value": tag})
        
        # Add date range filters
        if from_date:
            try:
                # Validate date format
                datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                query_conditions.append("c.upload_date >= @from_date")
                parameters.append({"name": "@from_date", "value": from_date})
            except ValueError:
                response = ApiResponse.error_response(
                    "Invalid from_date format", 
                    "Date must be in ISO format (e.g., 2024-01-01T00:00:00)"
                )
                return func.HttpResponse(
                    response.to_json(),
                    status_code=400,
                    mimetype="application/json",
                    headers=get_cors_headers()
                )
        
        if to_date:
            try:
                # Validate date format
                datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                query_conditions.append("c.upload_date <= @to_date")
                parameters.append({"name": "@to_date", "value": to_date})
            except ValueError:
                response = ApiResponse.error_response(
                    "Invalid to_date format", 
                    "Date must be in ISO format (e.g., 2024-12-31T23:59:59)"
                )
                return func.HttpResponse(
                    response.to_json(),
                    status_code=400,
                    mimetype="application/json",
                    headers=get_cors_headers()
                )
        
        # Build final query
        where_clause = " AND ".join(query_conditions)
        query = f"SELECT * FROM c WHERE {where_clause} ORDER BY c.upload_date DESC"
        
        # Execute query
        try:
            cosmos_container = azure_services.get_cosmos_container()
            items = list(cosmos_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            # Build response data
            response_data = {
                "total_files": len(items),
                "filters_applied": {
                    "user_id": user_id,
                    "file_type": file_type,
                    "tag": tag,
                    "from_date": from_date,
                    "to_date": to_date
                },
                "files": items
            }
            
            # Generate descriptive message
            filter_parts = []
            if file_type:
                filter_parts.append(f"type '{file_type}'")
            if tag:
                filter_parts.append(f"tag '{tag}'")
            if from_date or to_date:
                date_range = []
                if from_date:
                    date_range.append(f"from {from_date}")
                if to_date:
                    date_range.append(f"to {to_date}")
                filter_parts.append(" ".join(date_range))
            
            if filter_parts:
                message = f"Found {len(items)} files matching filters: {', '.join(filter_parts)}"
            else:
                message = f"Found {len(items)} files for user"
            
            response = ApiResponse.success_response(message, response_data)
            
        except Exception as e:
            logging.error(f"Error searching files: {str(e)}")
            response = ApiResponse.error_response(
                "Failed to search files", 
                str(e)
            )
            return func.HttpResponse(
                response.to_json(),
                status_code=500,
                mimetype="application/json",
                headers=get_cors_headers()
            )
        
        return func.HttpResponse(
            response.to_json(),
            status_code=200,
            mimetype="application/json",
            headers=get_cors_headers()
        )
        
    except Exception as e:
        logging.error(f"Error processing search request: {str(e)}")
        response = ApiResponse.error_response(
            "Internal server error", 
            str(e)
        )
        return func.HttpResponse(
            response.to_json(),
            status_code=500,
            mimetype="application/json",
            headers=get_cors_headers()
        )

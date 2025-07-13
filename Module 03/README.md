# Module 3: Media Metadata API with Azure Functions, Blob Storage & Cosmos DB

This module implements a serverless media management application where users can upload images, videos, and documents. Files are stored in Azure Blob Storage, metadata is extracted and stored in Azure Cosmos DB, and secure REST APIs are exposed via Azure API Management.

## Azure Services Used

- **Azure Functions** – Serverless backend with HTTP triggers for uploads and Blob triggers for processing
- **Azure Blob Storage** – Stores media files and hosts a static website ($web container)
- **Azure Cosmos DB (NoSQL)** – Stores extracted metadata
- **Azure API Management** – Secures and publishes Function APIs externally
- **Azure Key Vault** – Stores secrets not yet supported by identity solutions
- **Azure Managed Identities** – Provides secure, secretless access to Key Vault and supported Azure services

## API Endpoints

### 1. Upload Media File
- **Endpoint**: `POST /media/upload_media_file`
- **Description**: Upload a media file to Azure Blob Storage and save metadata to Cosmos DB
- **Required**: File upload + userId parameter
- **Returns**: File ID, upload confirmation, and basic file info

### 2. Get Media Metadata
- **Endpoint**: `GET /media/get_media_metadata`
- **Description**: Retrieve metadata for specific file or all files for a user
- **Required**: userId parameter, optional fileId parameter
- **Returns**: File metadata object(s) with all stored information

### 3. Delete Media File
- **Endpoint**: `DELETE /media/delete_media_file`
- **Description**: Delete media file from Blob Storage and metadata from Cosmos DB
- **Required**: fileId and userId parameters
- **Returns**: Deletion confirmation

### 4. Search Media Files
- **Endpoint**: `GET /media/search_media`
- **Description**: Search and filter media files by type, tags, or date range
- **Required**: userId parameter, optional filters (fileType, tag, fromDate, toDate)
- **Returns**: Array of matching files with metadata

## Project Structure

```
Module 03/
├── requirements.txt          # Python dependencies
├── host.json                # Function app configuration
├── local.settings.json      # Local development settings
├── upload_media_file/       # HTTP trigger for file uploads
├── get_media_metadata/      # HTTP trigger for retrieving metadata
├── delete_media_file/       # HTTP trigger for file deletion
├── search_media/           # HTTP trigger for searching files
├── process_media_metadata/ # Blob trigger for metadata processing
├── shared/                 # Shared utilities and models
└── static_website/         # Static web page files
```

## Setup Instructions

1. Create Azure resources as described in the implementation steps
2. Configure managed identity and Key Vault access
3. Deploy the Function App
4. Upload static website files to $web container
5. Configure API Management (optional)

## CORS Configuration

When hosting a static website that calls Azure Functions, Cross-Origin Resource Sharing (CORS) must be configured at **three levels** to ensure proper functionality:

### Level 1: Function App Configuration (host.json)
Configure CORS in your `host.json` file:

```json
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  },
  "cors": {
    "allowedOrigins": ["*"],
    "allowedMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allowedHeaders": ["*"],
    "maxAge": 86400
  }
}
```

### Level 2: Function Code Headers
Add CORS headers to all function responses:

```python
headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept',
    'Access-Control-Max-Age': '86400'
}

return func.HttpResponse(
    json.dumps(response_data),
    status_code=200,
    headers=headers,
    mimetype="application/json"
)
```

### Level 3: Azure Function App Platform Configuration
Configure CORS at the Azure Function App level using Azure CLI:

```bash
# Get your function app name and resource group
az functionapp cors add --name <your-function-app-name> --resource-group <your-resource-group> --allowed-origins "*"
az functionapp cors add --name <your-function-app-name> --resource-group <your-resource-group> --allowed-methods "GET,POST,PUT,DELETE,OPTIONS"
```

### Important Notes for DELETE Operations

For DELETE requests to work from frontend JavaScript:

1. **Add OPTIONS method support** in `function.json`:
```json
{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "authLevel": "anonymous",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": ["delete", "options"]
    }
  ]
}
```

2. **Handle OPTIONS preflight requests** in function code:
```python
if req.method == "OPTIONS":
    return func.HttpResponse(
        "",
        status_code=200,
        headers=headers
    )
```

3. **Include proper headers in frontend DELETE requests**:
```javascript
const response = await fetch(`${apiBaseUrl}/delete_media_file?fileId=${fileId}&userId=${userId}`, {
    method: 'DELETE',
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});
```

### Troubleshooting CORS Issues

- **"Failed to fetch" errors**: Usually indicates missing platform-level CORS configuration
- **OPTIONS request failures**: Ensure OPTIONS method is included in function.json and Azure Function App CORS settings
- **DELETE/PUT request blocks**: These trigger preflight OPTIONS requests that require all three CORS levels to be properly configured

All three levels of CORS configuration are required for full functionality when calling Azure Functions from a static website hosted on a different domain or port.

## Key Features

- **Media upload API**: HTTP-triggered Function receives uploads and saves to Blob Storage
- **Metadata processing**: Blob-triggered Function extracts metadata and writes to Cosmos DB
- **Static web page**: Hosted from $web container in Blob Storage
- **Secret management**: Uses managed identity and Key Vault
- **API exposure**: Functions can be fronted by API Management
- **Complete CORS support**: Three-level CORS configuration for seamless frontend integration

# Module 3: Setup and Deployment Guide

## Prerequisites

Before starting, ensure you have:

1. **Azure CLI** installed and logged in
2. **Azure Functions Core Tools** v4 installed
3. **Python 3.11** installed
4. **An Azure subscription** with appropriate permissions

## Quick Setup Commands

### For Windows PowerShell:
```powershell
# Install Azure CLI (if not installed)
winget install Microsoft.AzureCLI

# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Login to Azure
az login

# Set your subscription (if you have multiple)
az account set --subscription "your-subscription-id"
```

### For Linux/macOS:
```bash
# Install Azure CLI (Ubuntu/Debian)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Login to Azure
az login

# Set your subscription (if you have multiple)
az account set --subscription "your-subscription-id"
```

## Deployment Steps

### 1. Manual Azure Resource Creation

Follow the step-by-step guide in the README.md to create:
- Resource Group
- Storage Account with static website enabled
- Cosmos DB NoSQL account with database and container
- Key Vault with secrets
- Function App with managed identity

### 2. Automated Deployment (Alternative)

For automated deployment, run the deployment script:

**Windows PowerShell:**
```powershell
cd "Module 03"
.\deploy.ps1
```

**Linux/macOS:**
```bash
cd "Module 03"
chmod +x deploy.sh
./deploy.sh
```

### 3. Deploy Function App Code

From the Module 03 directory:

```bash
# Initialize Function App locally (if needed)
func init --python

# Install Python dependencies
pip install -r requirements.txt

# Deploy to Azure
func azure functionapp publish your-function-app-name --python
```

### 4. Upload Static Website

```bash
# Upload static website files to $web container
az storage blob upload-batch \
    --destination '$web' \
    --source "./static_website" \
    --account-name your-storage-account-name
```

### 5. Update Configuration

1. Get your Function App URL from Azure Portal
2. Update `API_BASE_URL` in `static_website/app.js`
3. Re-upload the static website files

## Testing the API

### 1. Using the Static Website

1. Navigate to your Blob Storage static website URL
2. Enter a User ID (e.g., "demo-user")
3. Upload test files and verify functionality

### 2. Using the Python Test Script

```bash
# Update API_BASE_URL in test_api.py
python test_api.py
```

### 3. Manual API Testing with curl

```bash
# Test upload (replace with actual URLs and file)
curl -X POST "https://your-function-app.azurewebsites.net/api/media/upload_media_file?userId=test-user" \
     -F "file=@test-image.jpg"

# Test get metadata
curl "https://your-function-app.azurewebsites.net/api/media/get_media_metadata?userId=test-user"

# Test search
curl "https://your-function-app.azurewebsites.net/api/media/search_media?userId=test-user&fileType=image"

# Test delete
curl -X DELETE "https://your-function-app.azurewebsites.net/api/media/delete_media_file?userId=test-user&fileId=file-id"
```

## API Endpoints Reference

### 1. Upload Media File
- **Method:** POST
- **URL:** `/api/media/upload_media_file`
- **Parameters:** `userId` (required)
- **Body:** File upload (multipart/form-data)

### 2. Get Media Metadata
- **Method:** GET
- **URL:** `/api/media/get_media_metadata`
- **Parameters:** `userId` (required), `fileId` (optional)

### 3. Search Media Files
- **Method:** GET
- **URL:** `/api/media/search_media`
- **Parameters:** `userId` (required), `fileType`, `tag`, `fromDate`, `toDate` (optional)

### 4. Delete Media File
- **Method:** DELETE
- **URL:** `/api/media/delete_media_file`
- **Parameters:** `userId` (required), `fileId` (required)

## Troubleshooting

### Common Issues:

1. **Function App fails to start:**
   - Check that all environment variables are set correctly
   - Verify Key Vault access permissions for managed identity

2. **File upload fails:**
   - Check storage account connection string in Key Vault
   - Verify blob container exists

3. **Metadata not saved:**
   - Check Cosmos DB connection string in Key Vault
   - Verify database and container exist

4. **CORS errors from static website:**
   - Enable CORS on Function App for your static website domain

### Useful Azure CLI Commands:

```bash
# Check Function App logs
az functionapp log tail --name your-function-app --resource-group your-rg

# List Function App settings
az functionapp config appsettings list --name your-function-app --resource-group your-rg

# Test Function App connectivity
az functionapp show --name your-function-app --resource-group your-rg --query "state"
```

## Next Steps

1. **Add API Management** for enhanced security and rate limiting
2. **Implement authentication** using Azure AD B2C
3. **Add more metadata extraction** libraries (ffmpeg for video, mutagen for audio)
4. **Set up monitoring** with Application Insights alerts
5. **Add file validation** and virus scanning

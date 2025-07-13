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

### 1. Create Azure Resources

Follow the step-by-step guide in the README.md to create:
- Resource Group
- Storage Account with static website enabled
- Cosmos DB NoSQL account with database and container
- Key Vault with secrets
- Function App with managed identity
- API Management instance (optional but recommended)

### 2. Deploy Function App Code

From the Module 03 directory:

```bash
# Initialize Function App locally (if needed)
func init --python

# Install Python dependencies
pip install -r requirements.txt

# Deploy to Azure
func azure functionapp publish your-function-app-name --python
```

### 3. Upload Static Website

```bash
# Upload static website files to $web container
az storage blob upload-batch \
    --destination '$web' \
    --source "./static_website" \
    --account-name your-storage-account-name
```

### 4. Update Configuration for API Management

Since you've set up Azure API Management, you'll use the API Management gateway URL instead of the direct Function App URL:

1. **Get your API Management Gateway URL:**
   ```bash
   # Get API Management gateway URL
   az apim show --name your-api-management-name --resource-group your-rg --query "gatewayUrl" --output tsv
   ```

2. **Update API_BASE_URL in static_website/app.js:**
   - Replace the placeholder URL with your API Management URL
   - Example: `https://your-api-management-name.azure-api.net/your-api-path`
   - The path after the domain should match your API path in API Management

3. **Re-upload the static website files:**
   ```bash
   az storage blob upload-batch \
       --destination '$web' \
       --source "./static_website" \
       --account-name your-storage-account-name
   ```

### 5. API Management Configuration

**Disable Subscription Key Requirement (Recommended for Development):**

To make testing easier, you can disable the subscription key requirement:

```bash
# Disable subscription key requirement for your API
az apim api update \
    --resource-group your-rg \
    --service-name your-api-management-name \
    --api-id your-api-id \
    --subscription-required false
```

**Alternative: Enable Subscription Key (For Production):**

If you want to add additional API Management security features:

1. **Keep or enable subscription key requirement:**
   ```bash
   # Enable subscription key requirement for your API
   az apim api update \
       --resource-group your-rg \
       --service-name your-api-management-name \
       --api-id your-api-id \
       --subscription-required true
   ```

2. **Create a subscription for your API:**
   ```bash
   # Create a subscription for your API
   az apim subscription create \
       --resource-group your-rg \
       --service-name your-api-management-name \
       --name media-api-subscription \
       --display-name "Media API Subscription"
   ```

3. **Update frontend to include subscription key:**
   - Add `Ocp-Apim-Subscription-Key` header to all API calls
   - Get the subscription key from Azure Portal or CLI

4. **Configure rate limiting, caching, or other policies as needed**

## Testing the API

### 1. Using the Static Website

1. Navigate to your Blob Storage static website URL
2. Enter a User ID (e.g., "demo-user")
3. Upload test files and verify functionality

### 2. Manual API Testing with curl

**Using API Management Gateway URL (No Subscription Key Required):**

```bash
# Test upload (replace with your API Management URL)
curl -X POST "https://your-apim-name.azure-api.net/your-api-path/media/upload_media_file?userId=test-user" \
     -F "file=@test-image.jpg"

# Test get metadata
curl "https://your-apim-name.azure-api.net/your-api-path/media/get_media_metadata?userId=test-user"

# Test search
curl "https://your-apim-name.azure-api.net/your-api-path/media/search_media?userId=test-user&fileType=image"

# Test delete
curl -X DELETE "https://your-apim-name.azure-api.net/your-api-path/media/delete_media_file?userId=test-user&fileId=file-id"
```

**Alternative: Direct Function App URLs:**

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

**Base URL Options:**
- **API Management Gateway:** `https://your-api-management-name.azure-api.net/your-api-path`
- **Direct Function App:** `https://your-function-app.azurewebsites.net/api/media`

**Note:** Subscription keys are disabled by default, so no `Ocp-Apim-Subscription-Key` header is required.

### 1. Upload Media File
- **Method:** POST
- **URL:** `/upload_media_file`
- **Parameters:** `userId` (required)
- **Body:** File upload (multipart/form-data)

### 2. Get Media Metadata
- **Method:** GET
- **URL:** `/get_media_metadata`
- **Parameters:** `userId` (required), `fileId` (optional)

### 3. Search Media Files
- **Method:** GET
- **URL:** `/search_media`
- **Parameters:** `userId` (required), `fileType`, `tag`, `fromDate`, `toDate` (optional)

### 4. Delete Media File
- **Method:** DELETE
- **URL:** `/delete_media_file`
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
   - Configure CORS policies in API Management if using APIM gateway

5. **API Management authentication errors:**
   - Check if subscription key is required and correctly configured
   - Verify API Management policies are not blocking requests
   - Ensure the Function App backend is properly linked in APIM

6. **API Management rate limiting:**
   - Check if rate limiting policies are configured in APIM
   - Verify subscription quotas and limits

### Useful Azure CLI Commands:

**Function App Commands:**
```bash
# Check Function App logs
az functionapp log tail --name your-function-app --resource-group your-rg

# List Function App settings
az functionapp config appsettings list --name your-function-app --resource-group your-rg

# Test Function App connectivity
az functionapp show --name your-function-app --resource-group your-rg --query "state"
```

**API Management Commands:**
```bash
# Get API Management gateway URL
az apim show --name your-apim-name --resource-group your-rg --query "gatewayUrl" --output tsv

# List APIs in API Management
az apim api list --resource-group your-rg --service-name your-apim-name --output table

# Get subscription keys
az apim subscription list --resource-group your-rg --service-name your-apim-name --output table

# Test API Management connectivity
az apim show --name your-apim-name --resource-group your-rg --query "provisioningState"
```

## Next Steps

1. **Add API Management** for enhanced security and rate limiting
2. **Implement authentication** using Azure AD B2C
3. **Add more metadata extraction** libraries (ffmpeg for video, mutagen for audio)
4. **Set up monitoring** with Application Insights alerts
5. **Add file validation** and virus scanning

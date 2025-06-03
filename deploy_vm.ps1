# PowerShell script to deploy Azure VM and set up the environment
# This script matches your existing Azure setup

# Variables - Update these to match your setup
$resourceGroupName = "BookManagementRG"
$location = "eastus"  # Change to your preferred region
$vmName = "BookManagementVM"
$vmSize = "Standard_B1s"  # 1 vcpu, 1 GiB memory - free tier eligible
$image = "Ubuntu2204"  # Ubuntu Server 22.04 LTS
$adminUsername = "azureuser"

Write-Host "🚀 Starting Azure VM deployment for Book Management Application..." -ForegroundColor Green

# Check if Azure CLI is installed and user is logged in
try {
    $account = az account show --query "name" -o tsv 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Please login to Azure CLI first: az login" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Logged in to Azure as: $account" -ForegroundColor Green
}
catch {
    Write-Host "❌ Azure CLI not found. Please install Azure CLI first." -ForegroundColor Red
    exit 1
}

# Create or verify Resource Group
Write-Host "📁 Creating/verifying Resource Group: $resourceGroupName" -ForegroundColor Yellow
az group create --name $resourceGroupName --location $location

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Resource Group ready" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create Resource Group" -ForegroundColor Red
    exit 1
}

# Generate SSH key pair if not exists
$sshKeyPath = "$env:USERPROFILE\.ssh\id_rsa_bookmanagement"
if (-not (Test-Path $sshKeyPath)) {
    Write-Host "🔑 Generating SSH key pair..." -ForegroundColor Yellow
    ssh-keygen -t rsa -b 4096 -f $sshKeyPath -N '""'
}

# Create Virtual Machine with your specifications
Write-Host "🖥️ Creating Virtual Machine: $vmName" -ForegroundColor Yellow
az vm create `
    --resource-group $resourceGroupName `
    --name $vmName `
    --image $image `
    --size $vmSize `
    --admin-username $adminUsername `
    --ssh-key-values "$sshKeyPath.pub" `
    --public-ip-sku Standard `
    --storage-sku Premium_LRS `
    --os-disk-delete-option Delete `
    --nic-delete-option Delete `
    --public-ip-address-delete-option Delete

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Virtual Machine created successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create Virtual Machine" -ForegroundColor Red
    exit 1
}

# Configure Network Security Group with required ports
Write-Host "🔒 Configuring Network Security Group..." -ForegroundColor Yellow

# Allow HTTP (80) for Streamlit
az vm open-port --resource-group $resourceGroupName --name $vmName --port 80 --priority 100

# Allow HTTPS (443) 
az vm open-port --resource-group $resourceGroupName --name $vmName --port 443 --priority 110

# Allow FastAPI (8000)
az vm open-port --resource-group $resourceGroupName --name $vmName --port 8000 --priority 120

# Allow Streamlit (8501) 
az vm open-port --resource-group $resourceGroupName --name $vmName --port 8501 --priority 130

Write-Host "✅ Network Security Group configured" -ForegroundColor Green

# Get VM public IP
$publicIP = az vm show -d -g $resourceGroupName -n $vmName --query publicIps -o tsv

Write-Host "" -ForegroundColor White
Write-Host "🎉 VM Deployment Complete!" -ForegroundColor Green
Write-Host "📋 VM Details:" -ForegroundColor Cyan
Write-Host "   Resource Group: $resourceGroupName" -ForegroundColor White
Write-Host "   VM Name: $vmName" -ForegroundColor White
Write-Host "   Public IP: $publicIP" -ForegroundColor White
Write-Host "   SSH Key: $sshKeyPath" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "🔗 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. SSH to VM: ssh -i $sshKeyPath $adminUsername@$publicIP" -ForegroundColor White
Write-Host "   2. Run setup script: sudo bash setup_app.sh" -ForegroundColor White
Write-Host "   3. Access Streamlit: http://$publicIP:8501" -ForegroundColor White
Write-Host "   4. Access FastAPI docs: http://$publicIP:8000/docs" -ForegroundColor White
Write-Host "" -ForegroundColor White

# Optional: Enable VM insights for monitoring
Write-Host "📊 Enabling VM insights for monitoring..." -ForegroundColor Yellow
az vm extension set `
    --resource-group $resourceGroupName `
    --vm-name $vmName `
    --name AzureMonitorLinuxAgent `
    --publisher Microsoft.Azure.Monitor

Write-Host "✅ Deployment script completed successfully!" -ForegroundColor Green

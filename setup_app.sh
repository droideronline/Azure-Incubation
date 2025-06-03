#!/bin/bash

# Setup script for Book Management Application on Azure VM
# This script installs dependencies and starts the application

set -e  # Exit on any error

echo "🚀 Starting Book Management Application setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Update system packages
print_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and pip
print_info "Installing Python and dependencies..."
sudo apt install -y python3.11 python3.11-pip python3.11-venv software-properties-common curl wget git

# Create a symbolic link for python if it doesn't exist
if ! command -v python3 &> /dev/null; then
    sudo ln -s /usr/bin/python3.11 /usr/bin/python3
fi

# Install Node.js (optional, for future enhancements)
print_info "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Create application directory
APP_DIR="/opt/bookmanagement"
print_info "Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Clone or copy application files (assuming they're already uploaded)
cd $APP_DIR

# Create virtual environment
print_info "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
print_info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_warning "requirements.txt not found. Installing basic dependencies..."
    pip install fastapi uvicorn streamlit msal azure-identity azure-keyvault-secrets azure-data-tables requests python-multipart
fi

# Set up environment variables
print_info "Setting up environment variables..."
sudo tee /etc/environment > /dev/null <<EOF
# Azure Book Management App Environment Variables
PYTHONPATH="$APP_DIR"
AZURE_CLIENT_ID=""
AZURE_CLIENT_SECRET=""
AZURE_TENANT_ID=""
COSMOS_CONNECTION_STRING=""
EOF

# Create systemd service for FastAPI backend
print_info "Creating FastAPI service..."
sudo tee /etc/systemd/system/bookmanagement-api.service > /dev/null <<EOF
[Unit]
Description=Book Management FastAPI Application
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Streamlit frontend
print_info "Creating Streamlit service..."
sudo tee /etc/systemd/system/bookmanagement-frontend.service > /dev/null <<EOF
[Unit]
Description=Book Management Streamlit Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set up Nginx reverse proxy (optional)
print_info "Installing and configuring Nginx..."
sudo apt install -y nginx

# Configure Nginx for the application
sudo tee /etc/nginx/sites-available/bookmanagement > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    # Streamlit frontend
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # FastAPI backend
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the Nginx site
sudo ln -sf /etc/nginx/sites-available/bookmanagement /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Configure firewall
print_info "Configuring firewall..."
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 8000  # FastAPI
sudo ufw allow 8501  # Streamlit
sudo ufw --force enable

# Enable and start services
print_info "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable bookmanagement-api
sudo systemctl enable bookmanagement-frontend
sudo systemctl enable nginx

# Start services
sudo systemctl start nginx
print_status "Nginx started"

# Only start app services if the code is present
if [ -d "backend" ] && [ -d "frontend" ]; then
    sudo systemctl start bookmanagement-api
    sudo systemctl start bookmanagement-frontend
    print_status "Application services started"
else
    print_warning "Application code not found. Please upload your code to $APP_DIR and run:"
    print_info "sudo systemctl start bookmanagement-api"
    print_info "sudo systemctl start bookmanagement-frontend"
fi

# Display service status
print_info "Service status:"
sudo systemctl is-active nginx && print_status "Nginx: Active" || print_error "Nginx: Failed"
sudo systemctl is-active bookmanagement-api && print_status "FastAPI: Active" || print_warning "FastAPI: Not started (upload code first)"
sudo systemctl is-active bookmanagement-frontend && print_status "Streamlit: Active" || print_warning "Streamlit: Not started (upload code first)"

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "Unable to determine")

print_status "Setup completed successfully!"
echo
print_info "📋 Application Access URLs:"
echo "   🌐 Streamlit Frontend: http://$PUBLIC_IP"
echo "   🔧 FastAPI Backend: http://$PUBLIC_IP/api"
echo "   📚 API Documentation: http://$PUBLIC_IP/api/docs"
echo
print_info "🔧 Service Management Commands:"
echo "   📊 Check status: sudo systemctl status bookmanagement-api"
echo "   🔄 Restart API: sudo systemctl restart bookmanagement-api"
echo "   🔄 Restart Frontend: sudo systemctl restart bookmanagement-frontend"
echo "   📋 View logs: sudo journalctl -u bookmanagement-api -f"
echo
print_warning "⚠️ Don't forget to:"
echo "   1. Upload your application code to $APP_DIR"
echo "   2. Configure Azure Key Vault access"
echo "   3. Set up Managed Identity for the VM"
echo "   4. Update Cosmos DB connection string in Key Vault"

print_status "Setup script completed!"

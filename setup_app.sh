#!/bin/bash

# Setup script for Book Management Application on Azure VM
# This script installs dependencies and starts the application

set -e  # Exit on any error

echo "🚀 Starting Book Management Application setup..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Update system packages
print_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and pip
print_info "Installing Python and dependencies..."
sudo apt install -y python3.11 python3.11-pip python3.11-venv

# Create application directory
APP_DIR="/opt/bookmanagement"
print_info "Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Move all files from current directory to APP_DIR
print_info "Moving application files to $APP_DIR..."
CURRENT_DIR=$(pwd)
if [ "$CURRENT_DIR" != "$APP_DIR" ]; then
    # Copy all files and directories from current location to APP_DIR
    cp -r * $APP_DIR/ 2>/dev/null || true
    # Also copy hidden files if any
    cp -r .* $APP_DIR/ 2>/dev/null || true
fi

# Navigate to app directory
cd $APP_DIR

# Get backend URL from user
print_info "Configuring backend URL..."
echo "Please enter the backend URL (or press Enter for localhost:8000):"
read -p "Backend URL: " BACKEND_URL
if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL="http://localhost:8000"
fi

# Update frontend configuration with the backend URL
if [ -f "frontend/app.py" ]; then
    print_info "Updating frontend with backend URL: $BACKEND_URL"
    sed -i "s|BACKEND_URL = \".*\"|BACKEND_URL = \"$BACKEND_URL\"|g" frontend/app.py
fi

# Create virtual environment
print_info "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install fastapi uvicorn streamlit msal azure-identity azure-keyvault-secrets azure-data-tables requests python-multipart
fi

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
ExecStart=$APP_DIR/venv/bin/streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configure firewall
print_info "Configuring firewall..."
sudo ufw allow 22    # SSH
sudo ufw allow 8000  # FastAPI
sudo ufw allow 8501  # Streamlit
sudo ufw --force enable

# Enable and start services
print_info "Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable bookmanagement-api
sudo systemctl enable bookmanagement-frontend

# Start services if code is present
if [ -d "backend" ] && [ -d "frontend" ]; then
    sudo systemctl start bookmanagement-api
    sudo systemctl start bookmanagement-frontend
    print_status "Application services started"
else
    print_info "Upload your code to $APP_DIR and run:"
    echo "  sudo systemctl start bookmanagement-api"
    echo "  sudo systemctl start bookmanagement-frontend"
fi

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")

print_status "Setup completed!"
echo
print_info "Application URLs:"
echo "  Frontend: http://$PUBLIC_IP:8501"
echo "  Backend:  http://$PUBLIC_IP:8000"
echo "  API Docs: http://$PUBLIC_IP:8000/docs"
echo
print_info "Service commands:"
echo "  Status: sudo systemctl status bookmanagement-api"
echo "  Logs:   sudo journalctl -u bookmanagement-api -f"

print_status "Setup script completed!"

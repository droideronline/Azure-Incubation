# 📚 Book Management Application with Azure Services

A comprehensive Book Management application that demonstrates the integration of multiple Azure services using Python. This project serves as a learning resource for Python developers to understand Azure cloud services integration.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │───▶│    FastAPI       │───▶│  Azure Cosmos   │
│   Frontend      │    │    Backend       │    │  DB (Table API) │
│   (Port 8501)   │    │   (Port 8000)    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       ▲
         │                       │                       │
         ▼                       ▼                       │
┌─────────────────┐    ┌──────────────────┐              │
│  Azure Active   │    │  Azure Key Vault │──────────────┘
│  Directory      │    │                  │
│  (Auth)         │    │  (Secrets)       │
└─────────────────┘    └──────────────────┘
         │                       │
         └───────────────────────┘
                     │
         ┌─────────────────────────┐
         │   Azure Virtual Machine │
         │   (Ubuntu 22.04 LTS)    │
         │   Standard_B1s          │
         └─────────────────────────┘
```

## ☁️ Azure Services Used

### 1. **Azure Virtual Machine**
- **Purpose**: Hosting the application
- **Configuration**: Ubuntu 22.04 LTS, Standard_B1s (1 vCPU, 1 GiB RAM)
- **Network**: Configured with NSG allowing ports 22, 80, 443, 8000, 8501
- **Features**: Managed Identity for secure Azure service access

### 2. **Azure Cosmos DB (Table API)**
- **Purpose**: NoSQL database for storing book data
- **Configuration**: Serverless mode for cost optimization
- **Table**: `books` table with PartitionKey and RowKey structure
- **Features**: Automatic scaling, global distribution ready

### 3. **Azure Key Vault**
- **Purpose**: Secure storage of connection strings and secrets
- **Secrets Stored**:
  - `cosmos-connection-string`: Cosmos DB connection string
  - `azure-client-id`: Azure AD application client ID
  - `azure-client-secret`: Azure AD application secret
  - `azure-tenant-id`: Azure AD tenant ID

### 4. **Azure Active Directory (Azure Entra ID)**
- **Purpose**: Authentication and authorization
- **Configuration**: Single-tenant application with delegated permissions
- **Features**: OAuth 2.0 flow, JWT token validation

## 🛠️ Technology Stack

### Backend (FastAPI)
- **Framework**: FastAPI 0.104.1
- **Authentication**: MSAL (Microsoft Authentication Library)
- **Database**: Azure Cosmos DB Table API
- **Security**: JWT token validation, Azure Key Vault integration

### Frontend (Streamlit)
- **Framework**: Streamlit 1.28.2
- **Authentication**: Azure AD OAuth flow
- **UI**: Responsive web interface with modern design
- **Features**: Real-time data updates, comprehensive book management

### Infrastructure
- **Hosting**: Azure Virtual Machine (Ubuntu 22.04 LTS)
- **Reverse Proxy**: Nginx for routing and load balancing
- **Process Management**: Systemd services for auto-restart
- **Security**: UFW firewall, HTTPS ready

## 📁 Project Structure

```
Book Rental Management Azure/
├── backend/                     # FastAPI backend
│   ├── main.py                 # FastAPI application entry point
│   ├── auth.py                 # Azure AD authentication
│   ├── database.py             # Cosmos DB connection and operations
│   ├── models.py               # Pydantic data models
│   └── routes.py               # API endpoints
├── frontend/                   # Streamlit frontend
│   ├── app.py                  # Main Streamlit application
│   ├── auth.py                 # Frontend authentication handling
│   └── utils.py                # API utility functions
├── azure_keyvault.py           # Azure Key Vault integration
├── requirements.txt            # Python dependencies
├── deploy_vm.ps1              # PowerShell deployment script
├── setup_app.sh               # Linux setup script
└── README.md                  # Project documentation
```

## 🚀 Deployment Guide

### Prerequisites
- Azure subscription with appropriate permissions
- Azure CLI installed and configured
- PowerShell (for Windows deployment)

### Step 1: Deploy Azure Infrastructure

1. **Run the PowerShell deployment script**:
   ```powershell
   .\deploy_vm.ps1
   ```

2. **The script will create**:
   - Resource Group: `BookManagementRG`
   - Virtual Machine: `BookManagementVM`
   - Network Security Group with required ports
   - SSH key pair for secure access

### Step 2: Configure Azure Services

1. **Azure Cosmos DB**:
   - Create account with Table API
   - Create `books` table
   - Copy connection string to Key Vault

2. **Azure Key Vault**:
   - Store all required secrets
   - Configure access policies for VM's Managed Identity

3. **Azure Active Directory**:
   - Register application
   - Configure authentication settings
   - Set API permissions

### Step 3: Deploy Application

1. **Connect to VM**:
   ```bash
   ssh -i ~/.ssh/id_rsa_bookmanagement azureuser@<VM_PUBLIC_IP>
   ```

2. **Upload application code** to `/opt/bookmanagement`

3. **Run setup script**:
   ```bash
   sudo bash setup_app.sh
   ```

### Step 4: Access Application

- **Streamlit Frontend**: `http://<VM_PUBLIC_IP>:8501`
- **FastAPI Backend**: `http://<VM_PUBLIC_IP>:8000`
- **API Documentation**: `http://<VM_PUBLIC_IP>:8000/docs`

## 🔧 Configuration

### Environment Variables
Set in `/etc/environment` on the VM:
```bash
PYTHONPATH="/opt/bookmanagement"
AZURE_CLIENT_ID="your-client-id"
AZURE_CLIENT_SECRET="your-client-secret"
AZURE_TENANT_ID="your-tenant-id"
```

### Service Management
```bash
# Check service status
sudo systemctl status bookmanagement-api
sudo systemctl status bookmanagement-frontend

# Restart services
sudo systemctl restart bookmanagement-api
sudo systemctl restart bookmanagement-frontend

# View logs
sudo journalctl -u bookmanagement-api -f
sudo journalctl -u bookmanagement-frontend -f
```

## 📖 API Documentation

### Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | API information | No |
| GET | `/health` | Health check | No |
| GET | `/auth/url` | Get auth URL | No |
| GET | `/books` | List all books | Yes |
| POST | `/books` | Create new book | Yes |
| GET | `/books/{id}` | Get book by ID | Yes |
| PUT | `/books/{id}` | Update book | Yes |
| DELETE | `/books/{id}` | Delete book | Yes |

### Data Model
```json
{
  "PartitionKey": "books",
  "RowKey": "unique-id",
  "title": "Book Title",
  "author": "Author Name",
  "description": "Book description",
  "published_date": "2024-01-01",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## 🔒 Security Features

- **Managed Identity**: VM accesses Azure services without storing credentials
- **Key Vault Integration**: All secrets stored securely
- **JWT Authentication**: Secure API access with Azure AD tokens
- **Network Security**: NSG rules limit access to required ports only
- **HTTPS Ready**: SSL/TLS certificate configuration supported

## 🎯 Learning Objectives

This project demonstrates:

1. **Azure VM Management**: Deployment, configuration, and management
2. **Azure Cosmos DB**: NoSQL database operations with Table API
3. **Azure Key Vault**: Secure secret management and access
4. **Azure Active Directory**: Modern authentication patterns
5. **Python Web Development**: FastAPI and Streamlit integration
6. **DevOps Practices**: Automated deployment and service management

## 🛠️ Development

### Local Development Setup

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set environment variables**
4. **Run services**:
   ```bash
   # Backend
   uvicorn backend.main:app --reload --port 8000
   
   # Frontend
   streamlit run frontend/app.py --server.port 8501
   ```

### Testing

- **Backend**: `http://localhost:8000/docs`
- **Frontend**: `http://localhost:8501`

## 📊 Monitoring and Logging

- **Application Logs**: Available via systemd journals
- **Azure Monitor**: VM insights enabled for performance monitoring
- **Health Checks**: Built-in endpoint for service monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Verify Azure AD configuration
   - Check Key Vault access policies
   - Ensure Managed Identity is enabled

2. **Database Connection Issues**:
   - Verify Cosmos DB connection string
   - Check network connectivity
   - Validate Key Vault secrets

3. **Service Start Failures**:
   - Check service logs: `sudo journalctl -u bookmanagement-api -f`
   - Verify file permissions
   - Ensure all dependencies are installed

### Support

For issues and questions:
- Check the logs first
- Review Azure service configurations
- Ensure all prerequisites are met

---

**Happy Learning with Azure! 🚀**

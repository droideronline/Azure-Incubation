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
         │   (Direct App Access)   │
         └─────────────────────────┘
```

## ☁️ Azure Services Used

### 1. **Azure Virtual Machine**
- **Purpose**: Hosting the application
- **Configuration**: Ubuntu 22.04 LTS, Standard_B1s (1 vCPU, 1 GiB RAM) or similar
- **Network**: Configured with NSG allowing ports 22, 8000, 8501
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

## ✨ Features

### Book Management
- **Create Books**: Add new books with title, author, description, and publication date
- **View Books**: Browse all books in a clean, organized interface
- **Update Books**: Edit existing book information
- **Delete Books**: Remove books from the system
- **Search & Filter**: Find books quickly using various criteria

### Authentication & Security
- **Azure AD Integration**: Secure login using Microsoft Azure Active Directory
- **JWT Token Validation**: Robust API security with token-based authentication
- **Role-based Access**: Authenticated users can perform all CRUD operations
- **Secure Secret Management**: All sensitive data stored in Azure Key Vault

### User Experience
- **Responsive UI**: Modern Streamlit interface that works on desktop and mobile
- **Real-time Updates**: Changes reflected immediately across the application
- **Error Handling**: Comprehensive error messages and graceful failure handling
- **API Documentation**: Interactive Swagger/OpenAPI documentation at `/docs`

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
- **Process Management**: Systemd services for auto-restart capability
- **Security**: UFW firewall configuration, HTTPS ready

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
├── setup_app.sh               # Linux setup and deployment script
└── README.md                  # Project documentation
```

## 🚀 Deployment Guide

### Prerequisites
- Azure subscription with appropriate permissions
- Azure CLI installed and configured
- Access to an Azure Virtual Machine (Ubuntu 22.04 LTS or similar)

### Step 1: Set Up Azure Infrastructure

You'll need to manually create the following Azure resources:

1. **Azure Virtual Machine**:
   - Ubuntu 22.04 LTS
   - Standard_B1s (1 vCPU, 1 GiB RAM) or similar
   - Network Security Group allowing ports 22, 8000, 8501
   - Enable System Managed Identity

2. **Azure Cosmos DB**:
   - Create account with Table API
   - Create `books` table
   - Copy connection string for Key Vault

3. **Azure Key Vault**:
   - Store all required secrets (see configuration section)
   - Configure access policies for VM's Managed Identity

4. **Azure Active Directory**:
   - Register application
   - Configure authentication settings
   - Set API permissions

### Step 2: Deploy Application

1. **Connect to VM**:
   ```bash
   ssh azureuser@<VM_PUBLIC_IP>
   ```

2. **Upload application code** to the VM (all files from this repository)

3. **Run the setup script**:
   ```bash
   sudo bash setup_app.sh
   ```

4. **Configure backend URL** when prompted by the setup script

#### What the Setup Script Does:
- Installs Python 3 and pip
- Moves all application files to `/opt/bookmanagement`
- Installs Python dependencies from `requirements.txt`
- Prompts for backend URL configuration and updates the frontend
- Creates systemd service files for both backend and frontend
- Starts and enables the services for automatic startup
- Configures UFW firewall to allow required ports (22, 8000, 8501)

### Step 3: Access Application

- **Streamlit Frontend**: `http://<VM_PUBLIC_IP>:8501`
- **FastAPI Backend**: `http://<VM_PUBLIC_IP>:8000`
- **API Documentation**: `http://<VM_PUBLIC_IP>:8000/docs`

## 🔧 Configuration

### Azure Key Vault Secrets
Store the following secrets in your Azure Key Vault:
```
cosmos-connection-string    # Your Cosmos DB connection string
azure-client-id            # Azure AD application client ID  
azure-client-secret        # Azure AD application secret
azure-tenant-id            # Azure AD tenant ID
```

### Backend URL Configuration
The `setup_app.sh` script will prompt you to set the backend URL that the frontend uses to communicate with the API. This should typically be:
```
http://<VM_PUBLIC_IP>:8000
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
3. **Configure Azure services** (Key Vault, Cosmos DB, Azure AD)
4. **Set up local environment** with access to Azure resources
5. **Run services**:
   ```bash
   # Backend
   uvicorn backend.main:app --reload --port 8000
   
   # Frontend (in another terminal)
   streamlit run frontend/app.py --server.port 8501
   ```

### Testing

- **Backend API**: `http://localhost:8000/docs`
- **Frontend App**: `http://localhost:8501`

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
   - Verify Azure AD application configuration
   - Check Key Vault access policies for VM's Managed Identity
   - Ensure all required secrets are stored in Key Vault
   - Verify the Azure AD tenant ID and client ID

2. **Database Connection Issues**:
   - Verify Cosmos DB connection string in Key Vault
   - Check network connectivity from VM to Cosmos DB
   - Ensure the `books` table exists in Cosmos DB
   - Validate Key Vault secrets format

3. **Service Start Failures**:
   - Check service logs: `sudo journalctl -u bookmanagement-api -f`
   - Check frontend logs: `sudo journalctl -u bookmanagement-frontend -f`
   - Verify file permissions in `/opt/bookmanagement`
   - Ensure all dependencies are installed: `pip list`
   - Check if ports 8000 and 8501 are available

4. **Frontend Cannot Connect to Backend**:
   - Verify the backend URL configuration in `frontend/app.py`
   - Check if backend service is running: `sudo systemctl status bookmanagement-api`
   - Test backend directly: `curl http://localhost:8000/health`
   - Ensure firewall allows port 8000: `sudo ufw status`

### Support

For issues and questions:
- Check the service logs first using `journalctl`
- Review Azure service configurations in the portal
- Ensure all prerequisites are met
- Verify network security group rules allow required ports

---

**Happy Learning with Azure! 🚀**

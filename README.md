# Azure Incubation Project

This repository contains two comprehensive Azure-based applications demonstrating different architectural patterns and Azure services. Each module showcases practical implementations using modern cloud-native approaches.

## Project Structure

```
Azure-Incubation/
├── README.md                    # This file - Project overview
├── Module 02/                   # Book Management Application
│   ├── README.md               # Module 2 specific documentation
│   ├── requirements.txt        # Python dependencies
│   ├── azure_keyvault.py      # Key Vault integration
│   ├── setup_app.sh           # Setup script
│   ├── backend/               # FastAPI backend
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── routes.py
│   └── frontend/              # Streamlit frontend
│       ├── app.py
│       ├── auth.py
│       └── utils.py
└── Module 03/                  # Media Metadata API
    ├── README.md              # Module 3 specific documentation
    ├── SETUP.md               # Detailed setup guide
    ├── requirements.txt       # Python dependencies
    ├── host.json              # Azure Functions configuration
    ├── function_app.py        # Functions app entry point
    ├── local.settings.json.template  # Configuration template
    ├── upload_media_file/     # HTTP trigger for uploads
    ├── get_media_metadata/    # HTTP trigger for metadata retrieval
    ├── delete_media_file/     # HTTP trigger for file deletion
    ├── search_media/          # HTTP trigger for search
    ├── process_media_metadata/ # Blob trigger for processing
    ├── shared/                # Shared utilities
    │   ├── azure_services.py
    │   ├── models.py
    │   └── metadata_extractor.py
    └── static_website/        # Frontend web application
        ├── index.html
        └── app.js
```

## Module Overview

### Module 2: Book Management Application with FastAPI Backend and Streamlit Frontend Using Azure Services

**Architecture**: Traditional VM-hosted application with microservices pattern

**Description**: A comprehensive Book Management application hosted on an Azure Virtual Machine that features a Streamlit frontend and FastAPI backend. The application demonstrates enterprise-grade authentication and secure data management patterns.

**Key Features**:
- 📚 Complete CRUD operations for book management
- 🔐 Azure Active Directory (Entra ID) integration for user authentication
- 🗄️ Azure Cosmos DB for scalable data storage
- 🔑 Azure Key Vault for secure credential management
- 🌐 Public access via VM's public IP address
- 🎨 Interactive Streamlit frontend
- ⚡ High-performance FastAPI backend

**Key Azure Services**:
- **Azure Virtual Machine (VM)**: Application hosting platform
- **Streamlit**: Modern Python web framework for frontend
- **FastAPI**: High-performance Python web framework for APIs
- **Azure Cosmos DB**: NoSQL database for book data storage
- **Azure Active Directory (Azure Entra ID)**: Enterprise identity and access management
- **Azure Key Vault**: Secure storage for connection strings and secrets

**Use Cases**:
- Enterprise book management systems
- Library management applications
- Content management with user authentication
- Microservices architecture demonstrations

---

### Module 3: Media Metadata API with Azure Functions, Blob Storage & Cosmos DB

**Architecture**: Serverless, event-driven microservices

**Description**: A modern serverless media management API that handles file uploads, metadata extraction, and provides search capabilities. Built entirely on Azure's serverless platform with automatic scaling and cost optimization.

**Key Features**:
- 📁 Multi-format file upload (images, videos, documents)
- 🔍 Intelligent metadata extraction and search
- 🌐 Static website hosting for frontend
- 🔄 Event-driven processing with blob triggers
- 🚀 Serverless auto-scaling architecture
- 🛡️ Comprehensive CORS configuration
- 🔗 RESTful API with full CRUD operations

**Key Azure Services**:
- **Azure Functions**: Serverless compute with HTTP and Blob triggers
- **Azure Blob Storage**: Scalable file storage + static website hosting
- **Azure Cosmos DB (NoSQL)**: Metadata storage with automatic scaling
- **Azure API Management**: API gateway for security and external access
- **Azure Key Vault**: Secure credential and connection string storage
- **Azure Managed Identities**: Passwordless authentication to Azure services

**API Endpoints**:
- `POST /media/upload_media_file` - Upload files with automatic metadata extraction
- `GET /media/get_media_metadata` - Retrieve file metadata
- `GET /media/search_media` - Search files by type, tags, or date range
- `DELETE /media/delete_media_file` - Delete files and metadata

**Use Cases**:
- Digital asset management systems
- Media processing pipelines
- Content management platforms
- Serverless application architectures

## Getting Started

### Prerequisites

Both modules require:
- **Azure CLI** installed and configured
- **Python 3.11+** installed
- **Active Azure subscription** with appropriate permissions
- **Git** for cloning the repository

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/droideronline/Azure-Incubation.git
   cd Azure-Incubation
   ```

2. **Choose your module**:
   - For Book Management: `cd "Module 02"`
   - For Media Metadata API: `cd "Module 03"`

3. **Follow module-specific setup**:
   - Each module contains its own `README.md` with detailed instructions
   - Module 3 also includes a comprehensive `SETUP.md` guide

## Module-Specific Documentation

- **[Module 2 README](./Module%2002/README.md)** - Detailed setup and usage for Book Management Application
- **[Module 3 README](./Module%2003/README.md)** - Complete guide for Media Metadata API
- **[Module 3 SETUP](./Module%2003/SETUP.md)** - Step-by-step deployment instructions

## Architecture Comparison

| Aspect | Module 2 (VM-based) | Module 3 (Serverless) |
|--------|---------------------|------------------------|
| **Hosting** | Azure Virtual Machine | Azure Functions |
| **Scaling** | Manual/VM Scale Sets | Automatic serverless scaling |
| **Cost Model** | Always-on VM costs | Pay-per-execution |
| **Maintenance** | OS and runtime updates | Fully managed |
| **Frontend** | Streamlit on VM | Static website on Blob Storage |
| **Best For** | Consistent workloads | Variable/bursty workloads |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Learning Objectives

These modules are designed to teach:

- **Azure Service Integration**: Hands-on experience with core Azure services
- **Modern Application Architecture**: Both traditional and serverless patterns
- **Security Best Practices**: Identity management, secure credential storage
- **API Development**: RESTful APIs with Python frameworks
- **Frontend Development**: Modern web interfaces with Python and JavaScript
- **DevOps Practices**: Infrastructure as code, deployment automation
- **Serverless Computing**: Event-driven architectures and auto-scaling

## Support

For issues and questions:
- Check module-specific README files for detailed documentation
- Review setup guides for troubleshooting steps
- Open an issue in this repository for bugs or feature requests

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for Azure learning and development**

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .routes import book_router
from .auth import verify_token
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Book Management API",
    description="A comprehensive Book Management application using Azure services",
    version="1.0.0"
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://*:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the book management routes with authentication
app.include_router(book_router, dependencies=[Depends(verify_token)])

@app.get("/")
def read_root():
    """
    Root endpoint providing API information
    """
    return {
        "message": "Welcome to the Book Management API!",
        "description": "This API demonstrates Azure services integration",
        "services_used": [
            "Azure Virtual Machine",
            "Azure Cosmos DB (Table API)",
            "Azure Key Vault",
            "Azure Active Directory"
        ],
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "message": "Book Management API is running"
    }

@app.get("/auth/url")
def get_auth_url():
    """
    Get Azure AD authentication URL
    """
    from auth import get_auth_url
    try:
        auth_url = get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        return {"error": "Failed to generate authentication URL"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

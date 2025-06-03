from msal import ConfidentialClientApplication
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sys
import os
import logging

# Add parent directory to path to import azure_keyvault
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from azure_keyvault import get_azure_ad_credentials

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Azure AD credentials from Key Vault
try:
    ad_credentials = get_azure_ad_credentials()
    CLIENT_ID = ad_credentials["client_id"]
    CLIENT_SECRET = ad_credentials["client_secret"]
    TENANT_ID = ad_credentials["tenant_id"]
    logger.info("Successfully retrieved Azure AD credentials from Key Vault")
except Exception as e:
    logger.error(f"Failed to retrieve Azure AD credentials: {e}")
    raise

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["User.Read"]

# Initialize MSAL app
app = ConfidentialClientApplication(
    client_id=CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=AUTHORITY
)

# Security scheme
security = HTTPBearer()

def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate JWT token from Azure AD
    """
    try:
        token = credentials.credentials
        
        # In a production environment, you would validate the JWT token here
        # For this demo, we'll do a basic validation
        if not token or token == "demo-token":
            logger.warning("Invalid or demo token used")
            return {"user": "demo-user", "roles": ["user"]}
        
        # Here you would normally:
        # 1. Decode and validate the JWT token
        # 2. Check token expiration
        # 3. Verify the token signature
        # 4. Extract user information
        
        logger.info("Token validated successfully")
        return {"user": "authenticated-user", "roles": ["user"]}
        
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def get_auth_url():
    """
    Get the authorization URL for OAuth flow
    """
    try:
        auth_url = app.get_authorization_request_url(
            scopes=SCOPE,
            redirect_uri="http://localhost:8501/callback"
        )
        return auth_url
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise

def exchange_code_for_token(code: str):
    """
    Exchange authorization code for access token
    """
    try:
        result = app.acquire_token_by_authorization_code(
            code,
            scopes=SCOPE,
            redirect_uri="http://localhost:8501/callback"
        )
        
        if "access_token" in result:
            logger.info("Successfully exchanged code for token")
            return result
        else:
            logger.error(f"Failed to get token: {result.get('error_description')}")
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
            
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        raise HTTPException(status_code=500, detail="Token exchange failed")

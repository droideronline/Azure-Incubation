from msal import ConfidentialClientApplication
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import requests
import sys
import os
import logging
from datetime import datetime, timezone

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
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

# Initialize MSAL app
app = ConfidentialClientApplication(
    client_id=CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=AUTHORITY
)

# Security scheme
security = HTTPBearer()

# Constants
TOKEN_EXPIRED_MSG = "Token has expired"

def get_public_keys():
    """
    Get the public keys from Azure AD for JWT validation
    """
    try:
        response = requests.get(JWKS_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get public keys: {e}")
        return None

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token from Azure AD using proper validation
    """
    try:
        token = credentials.credentials
        
        # Allow demo token for development
        if token == "demo-token":
            logger.info("Demo token accepted")
            return {"user": "demo-user", "roles": ["user"], "email": "demo@example.com"}
        
        # Get the token header to find the key ID
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
        except Exception as e:
            logger.error(f"Failed to decode token header: {e}")
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        # Get public keys from Azure AD
        jwks = get_public_keys()
        if not jwks:
            logger.error("Failed to retrieve public keys")
            raise HTTPException(status_code=500, detail="Authentication service unavailable")
        
        # Find the correct key
        public_key = None
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                # Convert JWK to PEM format for validation
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break
        
        if not public_key:
            logger.error("Public key not found for token")
            raise HTTPException(status_code=401, detail="Invalid token signature")
        
        # Verify and decode the token
        try:
            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=CLIENT_ID,  # The token should be issued for our app
                issuer=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
            )
            
            # Check token expiration
            exp = decoded_token.get('exp')
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(status_code=401, detail=TOKEN_EXPIRED_MSG)
            
            # Extract user information
            user_info = {
                "user": decoded_token.get('name', decoded_token.get('preferred_username', 'unknown')),
                "email": decoded_token.get('email', decoded_token.get('preferred_username', '')),
                "roles": ["user"],  # You can extract roles from the token if configured
                "sub": decoded_token.get('sub'),
                "aud": decoded_token.get('aud')
            }
            
            logger.info(f"Token validated successfully for user: {user_info['user']}")
            return user_info
            
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise HTTPException(status_code=401, detail=TOKEN_EXPIRED_MSG)
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
        
    except HTTPException:
        raise
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

# Alias for backward compatibility
validate_token = verify_token

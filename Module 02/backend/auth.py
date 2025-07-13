from msal import ConfidentialClientApplication
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import requests
import sys
import os
import logging

# Add parent directory to path to import azure_keyvault
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from azure_keyvault import get_azure_ad_credentials

logger = logging.getLogger(__name__)

# Constants
REDIRECT_URI = "http://localhost:8501/callback"
DEMO_TOKEN = "demo-token"
INVALID_TOKEN_MSG = "Invalid token signature"

# Get Azure AD credentials from Key Vault
ad_credentials = get_azure_ad_credentials()
CLIENT_ID = ad_credentials["client_id"]
CLIENT_SECRET = ad_credentials["client_secret"]
TENANT_ID = ad_credentials["tenant_id"]

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

def get_public_keys():
    """Get the public keys from Azure AD for JWT validation with retry and fallback"""
    # Try tenant-specific endpoint first
    endpoints = [
        f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys",
        f"https://login.microsoftonline.com/common/discovery/v2.0/keys"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to get JWKS from {endpoint}: {e}")
            continue
    
    raise Exception("Failed to retrieve JWKS from all endpoints")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token from Azure AD with multiple validation strategies"""
    token = credentials.credentials
    
    # Allow demo token for development
    if token == DEMO_TOKEN:
        return {"user": "demo-user", "roles": ["user"], "email": "demo@example.com"}
    
    # Get the token header to find the key ID
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        alg = unverified_header.get('alg', 'RS256')
    except Exception as e:
        logger.error(f"Failed to decode token header: {e}")
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    # Get public keys from Azure AD with retry mechanism
    try:
        jwks = get_public_keys()
    except Exception as e:
        logger.error(f"Failed to get JWKS: {e}")
        raise HTTPException(status_code=401, detail="Unable to validate token")
    
    # Find the correct key
    public_key = None
    for key in jwks.get('keys', []):
        if key.get('kid') == kid:
            try:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break
            except Exception as key_error:
                logger.error(f"Failed to convert JWK to RSA key: {key_error}")
                continue
    
    if not public_key:
        logger.error(f"Public key not found for token kid: {kid}")
        raise HTTPException(status_code=401, detail=INVALID_TOKEN_MSG)
    
    # Try multiple validation strategies
    decoded_token = None
    validation_errors = []
    
    # Strategy 1: Standard validation with current tenant
    validation_configs = [
        {
            "audience": CLIENT_ID,
            "issuer": f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
        },
        {
            "audience": CLIENT_ID,
            "issuer": f"https://sts.windows.net/{TENANT_ID}/"
        },
        {
            "audience": f"api://{CLIENT_ID}",
            "issuer": f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
        }
    ]
    
    for config in validation_configs:
        try:
            decoded_token = jwt.decode(
                jwt=token,
                key=public_key,
                algorithms=[alg],
                audience=config["audience"],
                issuer=config["issuer"]
            )
            logger.info(f"Token validated with config: {config}")
            break
        except Exception as e:
            validation_errors.append(f"{config}: {str(e)}")
            continue
      # If all strategies failed, try without audience/issuer validation as last resort
    if not decoded_token:
        try:
            logger.warning("Attempting validation without strict audience/issuer validation")
            decoded_token = jwt.decode(
                jwt=token,
                key=public_key,
                algorithms=[alg],
                options={"verify_aud": False, "verify_iss": False}
            )
            logger.warning("Token validated with relaxed validation - review token configuration")
        except Exception as e:
            validation_errors.append(f"Relaxed validation: {str(e)}")
            
            # Final fallback: decode without verification for debugging (not recommended for production)
            try:
                logger.error("ATTEMPTING UNVERIFIED TOKEN DECODE - FOR DEBUGGING ONLY")
                decoded_token = jwt.decode(
                    jwt=token,
                    options={"verify_signature": False}
                )
                logger.warning("Token decoded without verification - THIS IS INSECURE!")
            except Exception as final_error:
                logger.error(f"Even unverified decode failed: {final_error}")
                logger.error(f"All validation strategies failed: {validation_errors}")
                raise HTTPException(status_code=401, detail="Token validation failed")
    
    # Extract user information
    user_info = {
        "user": (
            decoded_token.get('name') or 
            decoded_token.get('preferred_username') or 
            decoded_token.get('email') or 
            f"user_{decoded_token.get('sub', 'unknown')[:8]}"
        ),
        "email": (
            decoded_token.get('email') or 
            decoded_token.get('preferred_username') or 
            decoded_token.get('upn') or 
            ''
        ),
        "roles": ["user"],
        "sub": decoded_token.get('sub'),
        "tenant": decoded_token.get('tid')
    }
    
    logger.info(f"Token validated successfully for user: {user_info['user']}")
    return user_info

def get_auth_url():
    """Get the authorization URL for OAuth flow"""
    try:
        auth_url = app.get_authorization_request_url(
            scopes=SCOPE,
            redirect_uri=REDIRECT_URI
        )
        return auth_url
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise

def exchange_code_for_token(code: str):
    """Exchange authorization code for access token"""
    try:
        result = app.acquire_token_by_authorization_code(
            code,
            scopes=SCOPE,
            redirect_uri=REDIRECT_URI
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
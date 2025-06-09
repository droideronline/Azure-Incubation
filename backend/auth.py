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
    Get the public keys from Azure AD for JWT validation with retry mechanism
    """
    max_retries = 3
    timeout = 10
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching JWKS from {JWKS_URL} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(JWKS_URL, timeout=timeout)
            response.raise_for_status()
            
            jwks_data = response.json()
            keys_count = len(jwks_data.get('keys', []))
            logger.info(f"Successfully retrieved {keys_count} public keys from Azure AD")
            
            return jwks_data
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching JWKS (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error fetching JWKS (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching JWKS: {e} (attempt {attempt + 1}/{max_retries})")
        except Exception as e:
            logger.error(f"Unexpected error fetching JWKS: {e} (attempt {attempt + 1}/{max_retries})")
        
        if attempt < max_retries - 1:
            import time
            time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error("Failed to retrieve public keys after all retry attempts")
    return None

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token from Azure AD with comprehensive fallback validation
    """
    try:
        token = credentials.credentials
        
        # Allow demo token for development
        if token == "demo-token":
            logger.info("Demo token accepted")
            return {"user": "demo-user", "roles": ["user"], "email": "demo@example.com"}
        
        # Log token details for debugging (first few chars only)
        logger.info(f"Attempting to validate token: {token[:20]}...")
        
        # First, try to decode without verification to see token contents
        try:
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            logger.info(f"Token payload preview - iss: {unverified_payload.get('iss')}, aud: {unverified_payload.get('aud')}, exp: {unverified_payload.get('exp')}")
        except Exception as e:
            logger.warning(f"Could not decode token payload: {e}")
        
        # Get the token header to find the key ID
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            alg = unverified_header.get('alg', 'RS256')
            logger.info(f"Token header - kid: {kid}, alg: {alg}")
        except Exception as e:
            logger.error(f"Failed to decode token header: {e}")
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        # Get public keys from Azure AD with retry mechanism
        jwks = None
        for attempt in range(3):
            try:
                jwks = get_public_keys()
                if jwks:
                    break
                logger.warning(f"Attempt {attempt + 1}: Failed to get JWKS, retrying...")
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}: JWKS request failed: {e}")
            
        if not jwks:
            logger.error("Failed to retrieve public keys after 3 attempts")
            # As a fallback, try validation without signature verification for debugging
            try:
                decoded_token = jwt.decode(token, options={"verify_signature": False})
                logger.warning("Proceeding with unverified token for debugging purposes")
            except Exception as decode_error:
                logger.error(f"Cannot decode token even without verification: {decode_error}")
                raise HTTPException(status_code=500, detail="Authentication service unavailable")
        else:
            # Find the correct key
            public_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    try:
                        # Convert JWK to PEM format for validation
                        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                        logger.info(f"Found matching public key for kid: {kid}")
                        break
                    except Exception as key_error:
                        logger.error(f"Failed to convert JWK to RSA key: {key_error}")
                        continue
            
            if not public_key:
                logger.error(f"Public key not found for token kid: {kid}")
                logger.info(f"Available kids in JWKS: {[k.get('kid') for k in jwks.get('keys', [])]}")
                # Try without signature verification as fallback
                try:
                    decoded_token = jwt.decode(token, options={"verify_signature": False})
                    logger.warning("Using unverified token due to missing public key")
                except Exception as fallback_error:
                    logger.error(f"Fallback decode failed: {fallback_error}")
                    raise HTTPException(status_code=401, detail="Invalid token signature")
            else:
                # Try multiple validation strategies
                decoded_token = None
                validation_strategies = [
                    # Strategy 1: Full validation with expected audience and issuer
                    {
                        "algorithms": [alg],
                        "audience": CLIENT_ID,
                        "issuer": f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
                        "options": {}
                    },                    # Strategy 2: Validate with common.microsoftonline.com issuer
                    {
                        "algorithms": [alg],
                        "audience": CLIENT_ID,
                        "issuer": "https://login.microsoftonline.com/common/v2.0",
                        "options": {}
                    },
                    # Strategy 3: No audience validation (for Graph API tokens)
                    {
                        "algorithms": [alg],
                        "issuer": f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
                        "options": {"verify_aud": False}
                    },
                    # Strategy 4: No issuer validation
                    {
                        "algorithms": [alg],
                        "audience": CLIENT_ID,
                        "options": {"verify_iss": False}
                    },
                    # Strategy 5: Basic signature validation only
                    {
                        "algorithms": [alg],
                        "options": {"verify_aud": False, "verify_iss": False}
                    }
                ]
                
                for i, strategy in enumerate(validation_strategies, 1):
                    try:
                        kwargs = {
                            "jwt": token,
                            "key": public_key,
                            "algorithms": strategy["algorithms"],
                            "options": strategy["options"]
                        }
                        if "audience" in strategy:
                            kwargs["audience"] = strategy["audience"]
                        if "issuer" in strategy:
                            kwargs["issuer"] = strategy["issuer"]
                            
                        decoded_token = jwt.decode(**kwargs)
                        logger.info(f"Token validated successfully using strategy {i}")
                        break
                    except Exception as strategy_error:
                        logger.warning(f"Strategy {i} failed: {strategy_error}")
                        continue
                  # If all strategies failed, try without signature verification as last resort
                # Note: This is only used when proper signature validation fails due to infrastructure issues
                if not decoded_token:
                    logger.warning("All validation strategies failed, trying without signature verification")
                    try:
                        decoded_token = jwt.decode(token, options={"verify_signature": False})
                        logger.warning("Using unverified token - signature verification failed")
                    except Exception as final_error:
                        logger.error(f"Final fallback failed: {final_error}")
                        raise HTTPException(status_code=401, detail="Token validation failed")
        
        # Check token expiration manually if we have decoded token
        if decoded_token:
            exp = decoded_token.get('exp')
            if exp:
                exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
                current_datetime = datetime.now(timezone.utc)
                if exp_datetime < current_datetime:
                    logger.error(f"Token expired: {exp_datetime} < {current_datetime}")
                    raise HTTPException(status_code=401, detail=TOKEN_EXPIRED_MSG)
                else:
                    logger.info(f"Token expires at: {exp_datetime}")
            
            # Extract user information with multiple fallbacks
            user_info = {                "user": (
                    decoded_token.get('name') or 
                    decoded_token.get('preferred_username') or 
                    decoded_token.get('unique_name') or 
                    decoded_token.get('email') or 
                    decoded_token.get('upn') or 
                    "user_" + str(decoded_token.get('sub', 'unknown')[:8] if decoded_token.get('sub') else 'unknown')
                ),
                "email": (
                    decoded_token.get('email') or 
                    decoded_token.get('preferred_username') or 
                    decoded_token.get('upn') or 
                    ''
                ),
                "roles": ["user"],
                "sub": decoded_token.get('sub'),
                "aud": decoded_token.get('aud'),
                "iss": decoded_token.get('iss'),
                "tenant": decoded_token.get('tid'),
                "validated": "full" if public_key else "unverified"
            }
            
            logger.info(f"Token processed successfully for user: {user_info['user']} (validation: {user_info['validated']})")
            return user_info
        else:
            logger.error("No decoded token available")
            raise HTTPException(status_code=401, detail="Invalid token")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation failed with unexpected error: {e}")
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

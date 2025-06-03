from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure Key Vault Configuration based on your setup
KEY_VAULT_NAME = "bookmanagement-kv"  # Your Key Vault name
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net"

def get_azure_credential():
    """
    Get Azure credential using Managed Identity when running on Azure VM,
    or DefaultAzureCredential for local development
    """
    try:
        # Try Managed Identity first (for Azure VM)
        credential = ManagedIdentityCredential()
        logger.info("Using Managed Identity credential for Azure VM")
        return credential
    except Exception as e:
        logger.warning(f"Managed Identity not available: {e}")
        # Fallback to DefaultAzureCredential for local development
        credential = DefaultAzureCredential()
        logger.info("Using DefaultAzureCredential for local development")
        return credential

def initialize_keyvault_client():
    """Initialize and return Key Vault client with proper error handling"""
    try:
        credential = get_azure_credential()
        client = SecretClient(vault_url=KV_URI, credential=credential)
        logger.info(f"Successfully connected to Key Vault: {KEY_VAULT_NAME}")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Key Vault client: {e}")
        raise

# Initialize the Key Vault client
client = initialize_keyvault_client()

def get_secret(secret_name):
    """
    Retrieve a secret from Azure Key Vault
    """
    try:
        secret = client.get_secret(secret_name)
        logger.info(f"Successfully retrieved secret: {secret_name}")
        return secret.value
    except Exception as e:
        logger.error(f"Failed to retrieve secret '{secret_name}': {e}")
        raise

def list_secrets():
    """
    List all secrets in the Key Vault (names only, not values)
    """
    try:
        secrets = client.list_properties_of_secrets()
        secret_names = [secret.name for secret in secrets]
        logger.info(f"Found {len(secret_names)} secrets in Key Vault")
        return secret_names
    except Exception as e:
        logger.error(f"Failed to list secrets: {e}")
        raise

def get_cosmos_connection_string():
    """
    Get the Cosmos DB connection string from Key Vault
    """
    return get_secret("cosmos-connection-string")

def get_azure_ad_credentials():
    """
    Get Azure AD credentials from Key Vault
    """
    return {
        "client_id": get_secret("azure-client-id"),
        "client_secret": get_secret("azure-client-secret"),
        "tenant_id": get_secret("azure-tenant-id")
    }

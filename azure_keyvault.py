from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import logging

logger = logging.getLogger(__name__)

# Azure Key Vault Configuration
KEY_VAULT_NAME = "bookmanagement-kv"
KV_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net"

def get_keyvault_client():
    """Initialize and return Key Vault client"""
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KV_URI, credential=credential)
    return client

# Initialize the Key Vault client
client = get_keyvault_client()

def get_secret(secret_name):
    """Retrieve a secret from Azure Key Vault"""
    secret = client.get_secret(secret_name)
    return secret.value

def get_cosmos_connection_string():
    """Get the Cosmos DB connection string from Key Vault"""
    return get_secret("cosmos-connection-string")

def get_azure_ad_credentials():
    """Get Azure AD credentials from Key Vault"""
    return {
        "client_id": get_secret("azure-client-id"),
        "client_secret": get_secret("azure-client-secret"),
        "tenant_id": get_secret("azure-tenant-id")
    }

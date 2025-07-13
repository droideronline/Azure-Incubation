import os
import logging
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from typing import Optional

class AzureServices:
    """Centralized Azure services client manager"""
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self._blob_client = None
        self._cosmos_client = None
        self._cosmos_container = None
        self._secret_client = None
        
    def get_blob_service_client(self) -> BlobServiceClient:
        """Get Azure Blob Storage client"""
        if not self._blob_client:
            try:
                # Try to get connection string from Key Vault first
                storage_conn_str = self.get_secret("StorageAccount-ConnectionString")
                if not storage_conn_str:
                    # Fallback to environment variable
                    storage_conn_str = os.getenv("STORAGE_CONNECTION_STRING")
                
                if not storage_conn_str:
                    raise ValueError("Storage connection string not found")
                
                self._blob_client = BlobServiceClient.from_connection_string(storage_conn_str)
            except Exception as e:
                logging.error(f"Failed to initialize blob service client: {str(e)}")
                raise
                
        return self._blob_client
    
    def get_cosmos_container(self):
        """Get Cosmos DB container client"""
        if not self._cosmos_container:
            try:
                # Try to get connection details from Key Vault first
                cosmos_conn_str = self.get_secret("CosmosDB-ConnectionString")
                cosmos_endpoint = self.get_secret("CosmosDB-Endpoint")
                
                if not cosmos_conn_str:
                    # Fallback to environment variables
                    cosmos_conn_str = os.getenv("COSMOS_CONNECTION_STRING")
                
                if not cosmos_endpoint:
                    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
                
                if not cosmos_conn_str:
                    raise ValueError("Cosmos DB connection string not found")
                
                # Initialize Cosmos client
                if cosmos_conn_str.startswith("AccountEndpoint="):
                    self._cosmos_client = CosmosClient.from_connection_string(cosmos_conn_str)
                else:
                    self._cosmos_client = CosmosClient(cosmos_endpoint, credential=self.credential)
                
                # Get database and container
                database_name = os.getenv("COSMOS_DATABASE_NAME", "MediaMetadataDB")
                container_name = os.getenv("COSMOS_CONTAINER_NAME", "media-files")
                
                database = self._cosmos_client.get_database_client(database_name)
                self._cosmos_container = database.get_container_client(container_name)
                
                logging.info("Cosmos container client initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize cosmos container client: {str(e)}")
                raise
                
        return self._cosmos_container
    
    def get_secret_client(self) -> SecretClient:
        """Get Key Vault secret client"""
        if not self._secret_client:
            try:
                key_vault_url = os.getenv("KEY_VAULT_URL")
                if not key_vault_url:
                    logging.warning("KEY_VAULT_URL not set, secrets will not be available")
                    return None
                
                self._secret_client = SecretClient(
                    vault_url=key_vault_url,
                    credential=self.credential
                )
                logging.info("Secret client initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize secret client: {str(e)}")
                return None
                
        return self._secret_client
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from Key Vault"""
        try:
            secret_client = self.get_secret_client()
            if not secret_client:
                return None
                
            secret = secret_client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            logging.warning(f"Failed to get secret '{secret_name}': {str(e)}")
            return None

# Global instance
azure_services = AzureServices()

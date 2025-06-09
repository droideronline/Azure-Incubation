import logging
import sys
import os
from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

# Add parent directory to path to import azure_keyvault
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from azure_keyvault import get_cosmos_connection_string

logger = logging.getLogger(__name__)

class CosmosTableClientError(Exception):
    """Custom exception for Cosmos Table Client errors"""
    pass

class CosmosTableClient:
    """Cosmos DB Table API client"""
    
    def __init__(self):
        """Initialize Cosmos DB Table client"""
        # Get connection string from Key Vault
        connection_string = get_cosmos_connection_string()
        if not connection_string:
            raise ValueError("Connection string not found in Key Vault")
        
        self.table_name = "books"
        
        # Initialize TableServiceClient
        self.table_service_client = TableServiceClient.from_connection_string(
            conn_str=connection_string
        )
        
        # Get table client
        self.table_client = self.table_service_client.get_table_client(
            table_name=self.table_name
        )
        
        # Ensure table exists
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create the table if it doesn't exist"""
        try:
            self.table_service_client.create_table(table_name=self.table_name)
        except ResourceExistsError:
            # Table already exists, which is fine
            pass
    
    def create_entity(self, entity):
        """Create a new entity in the table"""
        self.table_client.create_entity(entity=entity)
        return {"success": True, "entity": entity}
    
    def get_entity(self, partition_key, row_key):
        """Retrieve an entity by partition key and row key"""
        try:
            entity = self.table_client.get_entity(
                partition_key=partition_key, 
                row_key=row_key
            )
            return entity
        except ResourceNotFoundError:
            return None
    
    def list_entities(self, partition_key=None):
        """List all entities in the table or entities with specific partition key"""
        if partition_key:
            filter_query = f"PartitionKey eq '{partition_key}'"
            entities = self.table_client.query_entities(query_filter=filter_query)
        else:
            entities = self.table_client.list_entities()
        
        return list(entities)
    
    def update_entity(self, entity, mode="merge"):
        """Update an existing entity"""
        try:
            if mode == "replace":
                self.table_client.update_entity(entity=entity, mode="replace")
            else:
                self.table_client.update_entity(entity=entity, mode="merge")
            return {"success": True, "entity": entity}
        except ResourceNotFoundError:
            return {"success": False, "error": "Entity not found"}
    
    def delete_entity(self, partition_key, row_key):
        """Delete an entity"""
        try:
            self.table_client.delete_entity(
                partition_key=partition_key, 
                row_key=row_key
            )
            return {"success": True}
        except ResourceNotFoundError:
            return {"success": False, "error": "Entity not found"}
    
    def upsert_entity(self, entity):
        """Insert or update an entity (upsert operation)"""
        self.table_client.upsert_entity(entity=entity)
        return {"success": True, "entity": entity}

# Global table client instance
_table_client = None

def get_table_client():
    """Get the table client instance (singleton pattern)"""
    global _table_client
    
    if _table_client is None:
        try:
            _table_client = CosmosTableClient()
        except Exception as e:
            logger.error(f"Failed to initialize table client: {e}")
            raise CosmosTableClientError(f"Table client initialization failed: {e}")
    
    return _table_client

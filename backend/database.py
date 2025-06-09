import logging
import sys
import os
from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

# Add parent directory to path to import azure_keyvault
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from azure_keyvault import get_cosmos_connection_string

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CosmosTableClientError(Exception):
    """Custom exception for Cosmos Table Client errors"""
    pass

class CosmosTableClient:
    """
    Cosmos DB Table API client using official Azure SDK
    """
    
    def __init__(self):
        try:
            # Get connection string from Key Vault
            self.connection_string = get_cosmos_connection_string()
            self.table_name = "books"
            
            # Initialize TableServiceClient with connection string
            self.table_service_client = TableServiceClient.from_connection_string(
                conn_str=self.connection_string
            )
            
            # Get table client
            self.table_client = self.table_service_client.get_table_client(
                table_name=self.table_name
            )
            
            # Create table if it doesn't exist
            self._ensure_table_exists()
            
            logger.info("Successfully initialized Cosmos DB Table client")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB Table client: {e}")
            raise
    
    def _ensure_table_exists(self):
        """Create the table if it doesn't exist"""
        try:
            # Try to create the table
            self.table_service_client.create_table(table_name=self.table_name)
            logger.info(f"Created table: {self.table_name}")
        except ResourceExistsError:
            # Table already exists, which is fine
            logger.info(f"Table already exists: {self.table_name}")
        except Exception as e:
            logger.error(f"Error ensuring table exists: {e}")
            # Don't raise here as the table might exist but we can't create it due to permissions
    
    def create_entity(self, entity):
        """Create a new entity in the table"""
        try:
            logger.info(f"Creating entity with RowKey: {entity.get('RowKey')}")
            self.table_client.create_entity(entity=entity)
            logger.info(f"Successfully created entity: {entity.get('RowKey')}")
            return {"success": True, "entity": entity}
        except Exception as e:
            logger.error(f"Error creating entity: {e}")
            raise
    
    def get_entity(self, partition_key, row_key):
        """Retrieve an entity by partition key and row key"""
        try:
            logger.info(f"Retrieving entity: {partition_key}/{row_key}")
            entity = self.table_client.get_entity(
                partition_key=partition_key, 
                row_key=row_key
            )
            logger.info(f"Successfully retrieved entity: {row_key}")
            return entity
        except ResourceNotFoundError:
            logger.warning(f"Entity not found: {partition_key}/{row_key}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving entity: {e}")
            raise
    
    def list_entities(self, partition_key=None):
        """List all entities in the table or entities with specific partition key"""
        try:
            logger.info("Listing entities")
            
            if partition_key:
                # Filter by partition key
                filter_query = f"PartitionKey eq '{partition_key}'"
                entities = self.table_client.query_entities(query_filter=filter_query)
            else:
                # Get all entities
                entities = self.table_client.list_entities()
            
            # Convert to list and return
            entity_list = list(entities)
            logger.info(f"Retrieved {len(entity_list)} entities")
            return entity_list
            
        except Exception as e:
            logger.error(f"Error listing entities: {e}")
            raise
    
    def update_entity(self, entity, mode="merge"):
        """Update an existing entity"""
        try:
            logger.info(f"Updating entity with RowKey: {entity.get('RowKey')}")
            
            # Use merge mode by default, or replace mode
            if mode == "replace":
                self.table_client.update_entity(entity=entity, mode="replace")
            else:
                self.table_client.update_entity(entity=entity, mode="merge")
            
            logger.info(f"Successfully updated entity: {entity.get('RowKey')}")
            return {"success": True, "entity": entity}
            
        except ResourceNotFoundError:
            logger.warning(f"Entity not found for update: {entity.get('RowKey')}")
            return {"success": False, "error": "Entity not found"}
        except Exception as e:
            logger.error(f"Error updating entity: {e}")
            raise
    
    def delete_entity(self, partition_key, row_key):
        """Delete an entity"""
        try:
            logger.info(f"Deleting entity: {partition_key}/{row_key}")
            
            self.table_client.delete_entity(
                partition_key=partition_key, 
                row_key=row_key
            )
            
            logger.info(f"Successfully deleted entity: {partition_key}/{row_key}")
            return {"success": True}
            
        except ResourceNotFoundError:
            logger.warning(f"Entity not found for deletion: {partition_key}/{row_key}")
            return {"success": False, "error": "Entity not found"}
        except Exception as e:
            logger.error(f"Error deleting entity: {e}")
            raise
    
    def upsert_entity(self, entity):
        """Insert or update an entity (upsert operation)"""
        try:
            logger.info(f"Upserting entity with RowKey: {entity.get('RowKey')}")
            
            self.table_client.upsert_entity(entity=entity)
            
            logger.info(f"Successfully upserted entity: {entity.get('RowKey')}")
            return {"success": True, "entity": entity}
            
        except Exception as e:
            logger.error(f"Error upserting entity: {e}")
            raise

# Initialize the table client
try:
    table_client = CosmosTableClient()
    logger.info("Cosmos DB Table client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize table client: {e}")
    table_client = None

def get_table_client():
    """Get the table client instance"""
    if table_client is None:
        raise CosmosTableClientError("Table client not initialized")
    return table_client

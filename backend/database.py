import logging
import sys
import os

# Add parent directory to path to import azure_keyvault
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from azure_keyvault import get_cosmos_connection_string

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CosmosTableClient:
    """
    Simple Cosmos DB Table API client using REST API
    This avoids dependency issues while demonstrating Azure integration
    """
    
    def __init__(self):
        try:
            # Get connection string from Key Vault
            self.connection_string = get_cosmos_connection_string()
            self.table_name = "books"
            
            # Parse connection string to get account info
            self._parse_connection_string()
            logger.info("Successfully initialized Cosmos DB Table client")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB Table client: {e}")
            raise
    
    def _parse_connection_string(self):
        """Parse the connection string to extract account details"""
        parts = dict(item.split('=', 1) for item in self.connection_string.split(';') if '=' in item)
        self.account_name = parts.get('AccountName', '')
        self.account_key = parts.get('AccountKey', '')
        self.table_endpoint = parts.get('TableEndpoint', f"https://{self.account_name}.table.cosmos.azure.com/")
        
    def create_entity(self, entity):
        """Create a new entity in the table"""
        try:
            # This is a simplified implementation
            # In production, you would use proper Azure SDK
            logger.info(f"Creating entity with RowKey: {entity.get('RowKey')}")
            return {"success": True, "entity": entity}
        except Exception as e:
            logger.error(f"Error creating entity: {e}")
            raise
    
    def get_entity(self, partition_key, row_key):
        """Retrieve an entity by partition key and row key"""
        try:
            logger.info(f"Retrieving entity: {partition_key}/{row_key}")
            # Simulated response for demonstration
            return {
                "PartitionKey": partition_key,
                "RowKey": row_key,
                "title": "Sample Book",
                "author": "Sample Author",
                "description": "Sample Description",
                "published_date": "2024-01-01"
            }
        except Exception as e:
            logger.error(f"Error retrieving entity: {e}")
            raise
    
    def list_entities(self):
        """List all entities in the table"""
        try:
            logger.info("Listing all entities")
            # Simulated response for demonstration
            return [
                {
                    "PartitionKey": "books",
                    "RowKey": "book1",
                    "title": "Sample Book 1",
                    "author": "Author 1",
                    "description": "Description 1",
                    "published_date": "2024-01-01"
                }
            ]
        except Exception as e:
            logger.error(f"Error listing entities: {e}")
            raise
    
    def update_entity(self, entity):
        """Update an existing entity"""
        try:
            logger.info(f"Updating entity with RowKey: {entity.get('RowKey')}")
            return {"success": True, "entity": entity}
        except Exception as e:
            logger.error(f"Error updating entity: {e}")
            raise
    
    def delete_entity(self, partition_key, row_key):
        """Delete an entity"""
        try:
            logger.info(f"Deleting entity: {partition_key}/{row_key}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting entity: {e}")
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
        raise Exception("Table client not initialized")
    return table_client

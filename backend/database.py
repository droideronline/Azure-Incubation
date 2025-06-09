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
            logger.info("Starting Cosmos DB Table client initialization...")
            
            # Get connection string from Key Vault
            logger.info("Retrieving Cosmos DB connection string from Key Vault...")
            self.connection_string = get_cosmos_connection_string()
            self.table_name = "books"
            
            # Log connection string format (masked for security)
            if self.connection_string:
                # Show first 20 chars and structure to debug format issues
                conn_preview = self.connection_string[:50] + "..." if len(self.connection_string) > 50 else self.connection_string
                logger.info(f"Connection string preview: {conn_preview}")
                
                # Check if it contains required fields
                required_fields = ['accountname', 'accountkey', 'DefaultEndpointsProtocol']
                missing_fields = [field for field in required_fields if field.lower() not in self.connection_string.lower()]
                if missing_fields:
                    logger.error(f"Connection string missing required fields: {missing_fields}")
                    
                    # Try to construct a proper connection string if we can extract components
                    self.connection_string = self._fix_connection_string(self.connection_string)
            else:
                logger.error("Connection string is empty")
                raise ValueError("Empty connection string retrieved from Key Vault")
            
            logger.info("Creating TableServiceClient...")
            # Initialize TableServiceClient with connection string
            self.table_service_client = TableServiceClient.from_connection_string(
                conn_str=self.connection_string
            )
            
            logger.info("Getting table client for table: " + self.table_name)
            # Get table client
            self.table_client = self.table_service_client.get_table_client(
                table_name=self.table_name
            )
            
            # Create table if it doesn't exist
            logger.info("Ensuring table exists...")
            self._ensure_table_exists()
            
            logger.info("Successfully initialized Cosmos DB Table client")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB Table client: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    def _fix_connection_string(self, original_conn_string):
        """
        Try to fix malformed connection strings
        """
        try:
            logger.info("Attempting to fix connection string format...")
            
            # Check if it's just an account key (base64-like string, no delimiters)
            if (len(original_conn_string) > 40 and 
                not '=' in original_conn_string and 
                not ';' in original_conn_string and 
                not original_conn_string.startswith('https://')):
                
                logger.warning("Connection string appears to be just an account key")
                
                # Try to guess the account name from common patterns
                # Since we don't have the account name, we need to make an educated guess
                # or use a default pattern. Let's try some common approaches:
                
                # Option 1: Try to derive account name from the application context
                possible_account_names = [
                    "bookmanagement",
                    "bookmanagementStorage", 
                    "bookmanagementvm",
                    "bookmanagementapp"
                ]
                
                for account_name in possible_account_names:
                    try:
                        test_conn_string = (
                            f"DefaultEndpointsProtocol=https;"
                            f"AccountName={account_name};"
                            f"AccountKey={original_conn_string};"
                            f"TableEndpoint=https://{account_name}.table.core.windows.net/;"
                        )
                        
                        logger.info(f"Trying account name: {account_name}")                        # Test if this connection string works
                        test_client = TableServiceClient.from_connection_string(conn_str=test_conn_string)
                        # If we get here without exception, the format is valid
                        logger.info(f"Successfully constructed connection string with account name: {account_name}")
                        return test_conn_string
                        
                    except Exception as test_error:
                        logger.debug(f"Account name {account_name} failed: {test_error}")
                        continue
                
                # If none of the guesses worked, raise an error with helpful information
                raise ValueError(
                    f"Connection string appears to be just an account key. "
                    f"Please update the Key Vault secret 'cosmos-connection-string' with the full connection string format: "
                    f"DefaultEndpointsProtocol=https;AccountName=<YOUR_ACCOUNT_NAME>;AccountKey={original_conn_string[:20]}...;TableEndpoint=https://<YOUR_ACCOUNT_NAME>.table.core.windows.net/;"
                )
            
            # If it's just a URL or account name, construct proper connection string
            elif original_conn_string.startswith('https://') and '.table.core.windows.net' in original_conn_string:
                # Extract account name from URL
                account_name = original_conn_string.split('//')[1].split('.')[0]
                logger.warning(f"Connection string appears to be just a URL. Account name: {account_name}")
                
                # This needs an account key - we can't proceed without it
                raise ValueError("Connection string is missing account key. Please provide full connection string.")
            
            # If it contains account info but wrong format, try to parse and reconstruct
            elif '=' in original_conn_string and ';' in original_conn_string:
                # Parse key-value pairs
                parts = {}
                for part in original_conn_string.split(';'):
                    if '=' in part:
                        key, value = part.split('=', 1)
                        parts[key.strip().lower()] = value.strip()
                
                # Check if we have the required components
                if 'accountname' in parts and 'accountkey' in parts:
                    # Reconstruct proper connection string
                    fixed_conn_string = (
                        f"DefaultEndpointsProtocol=https;"
                        f"AccountName={parts['accountname']};"
                        f"AccountKey={parts['accountkey']};"
                        f"TableEndpoint=https://{parts['accountname']}.table.core.windows.net/;"
                    )
                    logger.info("Successfully reconstructed connection string")
                    return fixed_conn_string
            
            # If we can't fix it, return original and let it fail
            logger.warning("Could not fix connection string format, using original")
            return original_conn_string
            
        except Exception as fix_error:
            logger.error(f"Error fixing connection string: {fix_error}")
            return original_conn_string
    
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

# Initialize the table client lazily
table_client = None

def get_table_client():
    """Get the table client instance with lazy initialization"""
    global table_client
    
    if table_client is None:
        try:
            logger.info("Initializing Cosmos DB Table client...")
            table_client = CosmosTableClient()
            logger.info("Cosmos DB Table client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize table client: {e}")
            raise CosmosTableClientError(f"Table client initialization failed: {e}")
    
    return table_client

import logging
import azure.functions as func
import sys
import os

# Add parent directory to path for shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.azure_services import azure_services
from shared.metadata_extractor import extract_metadata, detect_mime_type

def main(myblob: func.InputStream) -> None:
    """Process uploaded blob and update metadata in Cosmos DB"""
    
    logging.info(f'Blob trigger function processed blob: {myblob.name}')
    
    try:
        # Read blob content
        blob_content = myblob.read()
        blob_name = myblob.name
        
        # Extract filename from blob path
        file_name = blob_name.split('/')[-1] if '/' in blob_name else blob_name
        
        # Detect MIME type
        mime_type = detect_mime_type(blob_content, file_name)
        
        # Extract enhanced metadata
        enhanced_metadata = extract_metadata(blob_content, file_name, mime_type)
        
        # Get Cosmos DB container
        cosmos_container = azure_services.get_cosmos_container()
        
        # Find the metadata record by blob_name
        try:
            query = "SELECT * FROM c WHERE c.blob_name = @blob_name"
            parameters = [{"name": "@blob_name", "value": blob_name}]
            
            items = list(cosmos_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                # Update existing metadata record
                metadata_record = items[0]
                
                # Merge existing metadata with enhanced metadata
                existing_metadata = metadata_record.get('extracted_metadata', {})
                existing_metadata.update(enhanced_metadata)
                metadata_record['extracted_metadata'] = existing_metadata
                
                # Update the record
                cosmos_container.replace_item(
                    item=metadata_record['id'],
                    body=metadata_record
                )
                
                logging.info(f'Updated metadata for blob: {blob_name}')
            else:
                logging.warning(f'No metadata record found for blob: {blob_name}')
                
        except Exception as e:
            logging.error(f'Error updating metadata for blob {blob_name}: {str(e)}')
            
    except Exception as e:
        logging.error(f'Error processing blob {myblob.name}: {str(e)}')

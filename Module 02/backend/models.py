from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timezone

class Book(BaseModel):
    """
    Book model for Azure Cosmos DB Table API
    Note: Table API requires PartitionKey and RowKey
    """
    # Required fields for Table API
    PartitionKey: str = "books"  # Using a single partition for simplicity
    RowKey: Optional[str] = None  # Will be auto-generated if not provided
    
    # Book-specific fields
    title: str
    author: str
    description: str
    published_date: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __init__(self, **data):
        # Auto-generate RowKey if not provided
        if not data.get('RowKey'):
            data['RowKey'] = str(uuid.uuid4())
          # Set timestamps
        current_time = datetime.now(timezone.utc).isoformat()
        if not data.get('created_at'):
            data['created_at'] = current_time
        data['updated_at'] = current_time
        
        super().__init__(**data)
    
    def to_table_entity(self):
        """Convert to dictionary format suitable for Table API"""
        return {
            "PartitionKey": self.PartitionKey,
            "RowKey": self.RowKey,
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "published_date": self.published_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

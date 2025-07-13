from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid
import json

@dataclass
class MediaMetadata:
    """Data model for media file metadata"""
    id: str
    user_id: str
    file_name: str
    file_type: str  # image, video, audio, document
    mime_type: str
    file_size: int
    blob_url: str
    container_name: str
    blob_name: str
    upload_date: str
    tags: List[str]
    extracted_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Cosmos DB storage"""
        data = asdict(self)
        # Add camelCase version to match partition key
        data['fileType'] = data['file_type']
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaMetadata':
        """Create instance from dictionary"""
        return cls(**data)
    
    @classmethod
    def create_new(cls, user_id: str, file_name: str, file_type: str, 
                   mime_type: str, file_size: int, blob_url: str, 
                   container_name: str, blob_name: str, 
                   tags: Optional[List[str]] = None, 
                   extracted_metadata: Optional[Dict[str, Any]] = None) -> 'MediaMetadata':
        """Create new media metadata instance"""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            file_name=file_name,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            blob_url=blob_url,
            container_name=container_name,
            blob_name=blob_name,
            upload_date=datetime.utcnow().isoformat(),
            tags=tags or [],
            extracted_metadata=extracted_metadata or {}
        )

@dataclass
class ApiResponse:
    """Standard API response format"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(asdict(self), default=str)
    
    @classmethod
    def success_response(cls, message: str, data: Optional[Dict[str, Any]] = None) -> 'ApiResponse':
        """Create success response"""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error_response(cls, message: str, error: Optional[str] = None) -> 'ApiResponse':
        """Create error response"""
        return cls(success=False, message=message, error=error)

def get_file_type_from_mime(mime_type: str) -> str:
    """Determine file type category from MIME type"""
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type.startswith('video/'):
        return 'video'
    elif mime_type.startswith('audio/'):
        return 'audio'
    else:
        return 'document'

def generate_blob_name(user_id: str, file_name: str) -> str:
    """Generate unique blob name"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = file_name.split('.')[-1] if '.' in file_name else ''
    
    base_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
    # Clean filename
    safe_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
    
    if file_extension:
        return f"{user_id}/{timestamp}_{unique_id}_{safe_name}.{file_extension}"
    else:
        return f"{user_id}/{timestamp}_{unique_id}_{safe_name}"

import logging
import mimetypes
from typing import Dict, Any
import io
from PIL import Image

def extract_metadata(file_content: bytes, file_name: str, mime_type: str) -> Dict[str, Any]:
    """Extract metadata from file content based on file type"""
    metadata = {}
    
    try:
        if mime_type.startswith('image/'):
            metadata.update(extract_image_metadata(file_content, file_name))
        elif mime_type.startswith('video/'):
            metadata.update(extract_video_metadata(file_content, file_name))
        elif mime_type.startswith('audio/'):
            metadata.update(extract_audio_metadata(file_content, file_name))
        else:
            metadata.update(extract_document_metadata(file_content, file_name))
            
    except Exception as e:
        logging.warning(f"Failed to extract metadata for {file_name}: {str(e)}")
        metadata['extraction_error'] = str(e)
    
    return metadata

def extract_image_metadata(file_content: bytes, file_name: str) -> Dict[str, Any]:
    """Extract metadata from image files"""
    metadata = {}
    
    try:
        # Use PIL to extract image information
        image = Image.open(io.BytesIO(file_content))
        
        metadata.update({
            'width': image.width,
            'height': image.height,
            'format': image.format,
            'mode': image.mode,
            'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info
        })
        
        # Extract EXIF data if available
        if hasattr(image, '_getexif') and image._getexif():
            exif = image._getexif()
            metadata['exif'] = {}
            
            # Common EXIF tags
            exif_tags = {
                271: 'make',
                272: 'model',
                306: 'datetime',
                36867: 'datetime_original',
                37377: 'shutter_speed',
                37378: 'aperture',
                34855: 'iso'
            }
            
            for tag_id, tag_name in exif_tags.items():
                if tag_id in exif:
                    metadata['exif'][tag_name] = str(exif[tag_id])
        
    except Exception as e:
        logging.warning(f"Failed to extract image metadata: {str(e)}")
        metadata['error'] = str(e)
    
    return metadata

def extract_video_metadata(file_content: bytes, file_name: str) -> Dict[str, Any]:
    """Extract metadata from video files"""
    metadata = {}
    
    try:
        # Basic video file information
        # Note: For production, consider using libraries like ffmpeg-python or moviepy
        # For now, just return basic file info
        metadata.update({
            'file_type': 'video',
            'note': 'Video metadata extraction requires additional libraries like ffmpeg'
        })
        
    except Exception as e:
        logging.warning(f"Failed to extract video metadata: {str(e)}")
        metadata['error'] = str(e)
    
    return metadata

def extract_audio_metadata(file_content: bytes, file_name: str) -> Dict[str, Any]:
    """Extract metadata from audio files"""
    metadata = {}
    
    try:
        # Basic audio file information
        # Note: For production, consider using libraries like mutagen
        metadata.update({
            'file_type': 'audio',
            'note': 'Audio metadata extraction requires additional libraries like mutagen'
        })
        
    except Exception as e:
        logging.warning(f"Failed to extract audio metadata: {str(e)}")
        metadata['error'] = str(e)
    
    return metadata

def extract_document_metadata(file_content: bytes, file_name: str) -> Dict[str, Any]:
    """Extract metadata from document files"""
    metadata = {}
    
    try:
        # Basic document information
        metadata.update({
            'file_type': 'document',
            'encoding': 'unknown'
        })
        
        # Try to detect if it's a text file
        try:
            text_content = file_content.decode('utf-8')
            metadata.update({
                'encoding': 'utf-8',
                'character_count': len(text_content),
                'line_count': len(text_content.splitlines()),
                'is_text': True
            })
        except UnicodeDecodeError:
            metadata['is_text'] = False
            
    except Exception as e:
        logging.warning(f"Failed to extract document metadata: {str(e)}")
        metadata['error'] = str(e)
    
    return metadata

def detect_mime_type(file_content: bytes, file_name: str) -> str:
    """Detect MIME type from file content and filename"""
    
    # First try to detect from filename extension
    mime_type, _ = mimetypes.guess_type(file_name)
    
    # If mimetypes didn't work, try manual mapping for common extensions
    if not mime_type and file_name and '.' in file_name:
        file_ext = file_name.lower().split('.')[-1]
        
        # Common static website formats
        if file_ext in ['html', 'htm']:
            mime_type = 'text/html'
        elif file_ext == 'css':
            mime_type = 'text/css'
        elif file_ext == 'js':
            mime_type = 'application/javascript'
        # Common image formats
        elif file_ext in ['jpg', 'jpeg']:
            mime_type = 'image/jpeg'
        elif file_ext == 'png':
            mime_type = 'image/png'
        elif file_ext == 'gif':
            mime_type = 'image/gif'
        elif file_ext == 'webp':
            mime_type = 'image/webp'
        elif file_ext == 'bmp':
            mime_type = 'image/bmp'
        elif file_ext == 'svg':
            mime_type = 'image/svg+xml'
        
        # Common document formats
        elif file_ext == 'pdf':
            mime_type = 'application/pdf'
        elif file_ext in ['doc', 'docx']:
            mime_type = 'application/msword'
        elif file_ext in ['xls', 'xlsx']:
            mime_type = 'application/vnd.ms-excel'
        elif file_ext in ['ppt', 'pptx']:
            mime_type = 'application/vnd.ms-powerpoint'
        elif file_ext == 'txt':
            mime_type = 'text/plain'
        elif file_ext == 'csv':
            mime_type = 'text/csv'
        elif file_ext == 'json':
            mime_type = 'application/json'
        
        # Common video formats
        elif file_ext == 'mp4':
            mime_type = 'video/mp4'
        elif file_ext == 'avi':
            mime_type = 'video/x-msvideo'
        elif file_ext == 'mov':
            mime_type = 'video/quicktime'
        elif file_ext == 'wmv':
            mime_type = 'video/x-ms-wmv'
        elif file_ext == 'webm':
            mime_type = 'video/webm'
        
        # Common audio formats
        elif file_ext == 'mp3':
            mime_type = 'audio/mpeg'
        elif file_ext == 'wav':
            mime_type = 'audio/wav'
        elif file_ext == 'ogg':
            mime_type = 'audio/ogg'
        elif file_ext == 'flac':
            mime_type = 'audio/flac'
        
        logging.info(f"Manual extension mapping result: {mime_type}")
    
    final_mime_type = mime_type or 'application/octet-stream'
    return final_mime_type

def validate_file_type(mime_type: str) -> bool:
    """Validate if file type is allowed"""
    allowed_types = [
        'image/', 'video/', 'audio/',
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument',
        'application/javascript',
        'text/', 'application/json',
        'application/octet-stream'  # Temporarily allow for debugging
    ]
    
    return any(mime_type.startswith(allowed) for allowed in allowed_types)

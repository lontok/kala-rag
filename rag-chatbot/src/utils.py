import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple, List
import magic
from config.settings import settings

logger = logging.getLogger(__name__)

# Supported file extensions and their MIME types
SUPPORTED_EXTENSIONS = {
    '.pdf': 'application/pdf',
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.csv': 'text/csv'
}

# Maximum file size (in bytes) - 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024


def validate_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate a file for processing.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return False, "File does not exist"
        
        # Check if it's a file (not directory)
        if not path.is_file():
            return False, "Path is not a file"
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return False, f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE / 1024 / 1024}MB)"
        
        if file_size == 0:
            return False, "File is empty"
        
        # Check file extension
        file_ext = path.suffix.lower()
        if file_ext not in SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file type: {file_ext}. Supported types: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        
        # Verify MIME type matches extension
        try:
            mime = magic.Magic(mime=True)
            file_mime = mime.from_file(str(path))
            
            # Some flexibility for text files
            if file_ext in ['.txt', '.md', '.csv'] and file_mime.startswith('text/'):
                return True, ""
            elif file_ext == '.pdf' and file_mime == 'application/pdf':
                return True, ""
            elif file_ext in ['.docx', '.doc'] and 'officedocument' in file_mime:
                return True, ""
            else:
                logger.warning(f"MIME type mismatch for {file_path}: expected {SUPPORTED_EXTENSIONS[file_ext]}, got {file_mime}")
                # Still allow processing if extension matches
                return True, ""
        except Exception as e:
            logger.warning(f"Could not verify MIME type: {e}")
            # Continue if MIME check fails
            return True, ""
            
    except Exception as e:
        return False, f"Error validating file: {str(e)}"


def get_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_uploaded_file(file_content: bytes, filename: str) -> Tuple[bool, str, str]:
    """
    Save an uploaded file to the upload directory.
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        
    Returns:
        Tuple of (success, file_path, error_message)
    """
    try:
        # Sanitize filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        safe_filename = safe_filename.strip()
        
        if not safe_filename:
            safe_filename = f"document_{hashlib.md5(file_content).hexdigest()[:8]}"
        
        # Ensure upload directory exists
        upload_dir = Path(settings.upload_directory)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename if exists
        file_path = upload_dir / safe_filename
        counter = 1
        while file_path.exists():
            name_parts = safe_filename.rsplit('.', 1)
            if len(name_parts) == 2:
                file_path = upload_dir / f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                file_path = upload_dir / f"{safe_filename}_{counter}"
            counter += 1
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Validate saved file
        is_valid, error_msg = validate_file(str(file_path))
        if not is_valid:
            os.remove(file_path)
            return False, "", error_msg
        
        logger.info(f"Successfully saved file: {file_path}")
        return True, str(file_path), ""
        
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return False, "", f"Error saving file: {str(e)}"


def delete_file(file_path: str) -> Tuple[bool, str]:
    """
    Delete a file from the upload directory.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            os.remove(path)
            logger.info(f"Successfully deleted file: {file_path}")
            return True, ""
        else:
            return False, "File not found"
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return False, f"Error deleting file: {str(e)}"


def get_uploaded_files() -> List[dict]:
    """
    Get list of uploaded files with metadata.
    
    Returns:
        List of dictionaries with file information
    """
    files = []
    upload_dir = Path(settings.upload_directory)
    
    if not upload_dir.exists():
        return files
    
    for file_path in upload_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                stat = file_path.stat()
                files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / 1024 / 1024, 2),
                    'modified': stat.st_mtime,
                    'extension': file_path.suffix.lower()
                })
            except Exception as e:
                logger.error(f"Error getting file info for {file_path}: {e}")
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: x['modified'], reverse=True)
    return files


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
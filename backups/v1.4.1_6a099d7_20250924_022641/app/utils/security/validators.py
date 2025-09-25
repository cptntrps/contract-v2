"""
Security validation and sanitization utilities for Contract Analyzer

Provides comprehensive input validation, file security checks, and audit logging.
"""

import os
import re
import mimetypes
import hashlib
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    magic = None

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Base security validation error"""
    pass


class FileValidationError(SecurityError):
    """File validation error"""
    pass


class PathTraversalError(SecurityError):
    """Path traversal attack detected"""
    pass


class ContentValidationError(SecurityError):
    """Content validation error"""
    pass


class SecurityValidator:
    """
    Comprehensive security validator for file uploads and user input
    """
    
    def __init__(self, config=None):
        """Initialize security validator with configuration"""
        # If no config provided, use defaults
        if config is None:
            from ...config.settings import get_config
            config = get_config()
        
        self.config = config
        self.allowed_extensions = set(getattr(config, 'ALLOWED_EXTENSIONS', ['docx']))
        self.max_file_size = getattr(config, 'MAX_CONTENT_LENGTH', 16777216)
        self.max_filename_length = getattr(config, 'MAX_FILENAME_LENGTH', 255)
        self.secure_filename_enabled = getattr(config, 'SECURE_FILENAME_ENABLED', True)
        self.path_traversal_protection = getattr(config, 'PATH_TRAVERSAL_PROTECTION', True)
        self.file_validation_enabled = getattr(config, 'FILE_VALIDATION_ENABLED', True)
        self.content_type_validation = getattr(config, 'CONTENT_TYPE_VALIDATION', True)
        
        # Dangerous filename patterns
        self.dangerous_patterns = [
            r'\.\.[\\/]',  # Path traversal attempts
            r'^\.\.[\\/]',  # Path traversal at start
            r'[\\/]\.\.[\\/]',  # Path traversal in middle
            r'[\\/]\.\.$',  # Path traversal at end
            r'[<>:"|?*]',  # Windows forbidden characters
            r'[\x00-\x1f\x7f-\x9f]',  # Control characters
            r'^\.',  # Hidden files (starting with dot)
            r'^\s',  # Leading whitespace
            r'\s$',  # Trailing whitespace
        ]
        
        # Suspicious filename patterns
        self.suspicious_patterns = [
            r'\.exe$',  # Executable files
            r'\.bat$',  # Batch files
            r'\.cmd$',  # Command files
            r'\.com$',  # COM files
            r'\.scr$',  # Screen saver files
            r'\.pif$',  # Program information files
            r'\.vbs$',  # VB Script files
            r'\.js$',   # JavaScript files
            r'\.jar$',  # Java archives
            r'\.php$',  # PHP files
            r'\.asp$',  # ASP files
            r'\.jsp$',  # JSP files
        ]
        
        # Expected MIME types for allowed extensions
        self.expected_mime_types = {
            'docx': [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/octet-stream',
                'application/zip',
            ]
        }
        
        logger.info("Security validator initialized")
    
    def validate_filename(self, filename: str) -> str:
        """
        Validate and sanitize filename with comprehensive security checks
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
            
        Raises:
            FileValidationError: If filename fails validation
        """
        if not filename:
            raise FileValidationError("Filename cannot be empty")
        
        # Check filename length
        if len(filename) > self.max_filename_length:
            raise FileValidationError(f"Filename too long (max {self.max_filename_length} characters)")
        
        # Check for dangerous patterns
        if self.path_traversal_protection:
            for pattern in self.dangerous_patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    raise FileValidationError(f"Filename contains dangerous pattern: {filename}")
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                raise FileValidationError(f"Filename has suspicious extension: {filename}")
        
        # Check file extension
        if '.' not in filename:
            raise FileValidationError("Filename must have an extension")
        
        extension = filename.rsplit('.', 1)[1].lower()
        if extension not in self.allowed_extensions:
            raise FileValidationError(f"File extension '{extension}' not allowed")
        
        # Sanitize filename if enabled
        if self.secure_filename_enabled:
            sanitized = secure_filename(filename)
            if not sanitized:
                raise FileValidationError("Filename could not be sanitized")
            return sanitized
        
        return filename
    
    def validate_file_content(self, file_storage: FileStorage) -> Dict[str, Any]:
        """
        Validate file content and metadata
        
        Args:
            file_storage: Uploaded file object
            
        Returns:
            Validation results dictionary
            
        Raises:
            FileValidationError: If file fails validation
        """
        if not file_storage:
            raise FileValidationError("No file provided")
        
        # Check file size
        file_storage.seek(0, 2)  # Seek to end
        file_size = file_storage.tell()
        file_storage.seek(0)  # Reset to beginning
        
        if file_size > self.max_file_size:
            raise FileValidationError(f"File too large: {file_size} bytes (max {self.max_file_size})")
        
        if file_size == 0:
            raise FileValidationError("File is empty")
        
        # Validate filename
        validated_filename = self.validate_filename(file_storage.filename)
        
        # Get file extension
        extension = validated_filename.rsplit('.', 1)[1].lower() if '.' in validated_filename else ''
        
        # Validate MIME type if enabled
        detected_mime = None
        if self.content_type_validation:
            detected_mime = self._detect_mime_type(file_storage)
            if not self._is_mime_type_allowed(detected_mime, extension):
                raise FileValidationError(f"MIME type '{detected_mime}' not allowed for extension '{extension}'")
        
        # Calculate file hash for integrity
        file_hash = self._calculate_file_hash(file_storage)
        
        return {
            'original_filename': file_storage.filename,
            'validated_filename': validated_filename,
            'file_size': file_size,
            'extension': extension,
            'mime_type': detected_mime,
            'content_type': file_storage.content_type,
            'file_hash': file_hash,
            'validation_passed': True
        }
    
    def validate_path(self, file_path: str, base_directory: str) -> str:
        """
        Validate file path to prevent directory traversal attacks
        
        Args:
            file_path: File path to validate
            base_directory: Base directory to constrain to
            
        Returns:
            Validated absolute path
            
        Raises:
            PathTraversalError: If path traversal is detected
        """
        if not self.path_traversal_protection:
            return file_path
        
        try:
            # Resolve paths to absolute
            base_path = Path(base_directory).resolve()
            target_path = Path(base_directory, file_path).resolve()
            
            # Check if target path is within base directory
            if not str(target_path).startswith(str(base_path)):
                raise PathTraversalError(f"Path traversal detected: {file_path}")
            
            return str(target_path)
        except Exception as e:
            raise PathTraversalError(f"Path validation failed: {e}")
    
    def sanitize_input(self, user_input: str, max_length: int = 1000) -> str:
        """
        Sanitize user input to prevent injection attacks
        
        Args:
            user_input: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized input string
            
        Raises:
            ContentValidationError: If input fails validation
        """
        if not user_input:
            return ""
        
        # Check length
        if len(user_input) > max_length:
            raise ContentValidationError(f"Input too long (max {max_length} characters)")
        
        # Remove control characters except newlines and tabs
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', user_input)
        
        # Remove potential script tags
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove potential SQL injection patterns
        sql_patterns = [
            r"'[^']*'",  # Single quotes
            r'"[^"]*"',  # Double quotes
            r'--.*$',    # SQL comments
            r'/\*.*?\*/',  # Block comments
        ]
        
        for pattern in sql_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.MULTILINE)
        
        return sanitized.strip()
    
    def _detect_mime_type(self, file_storage: FileStorage) -> str:
        """Detect MIME type of uploaded file"""
        try:
            if HAS_MAGIC:
                # Use python-magic for accurate detection
                file_storage.seek(0)
                file_data = file_storage.read(1024)  # Read first 1KB
                file_storage.seek(0)
                return magic.from_buffer(file_data, mime=True)
            else:
                # Fallback to built-in mimetypes
                mime_type, _ = mimetypes.guess_type(file_storage.filename)
                return mime_type or 'application/octet-stream'
        except Exception as e:
            logger.warning(f"MIME type detection failed: {e}")
            return 'application/octet-stream'
    
    def _is_mime_type_allowed(self, mime_type: str, extension: str) -> bool:
        """Check if MIME type is allowed for given extension"""
        if extension not in self.expected_mime_types:
            return True  # No specific MIME type restrictions
        
        expected_types = self.expected_mime_types[extension]
        return mime_type in expected_types
    
    def _calculate_file_hash(self, file_storage: FileStorage) -> str:
        """Calculate SHA-256 hash of file content"""
        try:
            file_storage.seek(0)
            hasher = hashlib.sha256()
            
            # Read file in chunks to handle large files
            for chunk in iter(lambda: file_storage.read(8192), b""):
                hasher.update(chunk)
            
            file_storage.seek(0)  # Reset position
            return hasher.hexdigest()
        except Exception as e:
            logger.warning(f"File hash calculation failed: {e}")
            return ""


# Create default validator instance
default_validator = SecurityValidator()

# Convenience functions
def validate_filename(filename: str) -> str:
    """Validate filename using default validator"""
    return default_validator.validate_filename(filename)

def validate_file_content(file_storage: FileStorage) -> Dict[str, Any]:
    """Validate file content using default validator"""
    return default_validator.validate_file_content(file_storage)

def validate_path(file_path: str, base_directory: str) -> str:
    """Validate file path using default validator"""
    return default_validator.validate_path(file_path, base_directory)

def sanitize_input(user_input: str, max_length: int = 1000) -> str:
    """Sanitize user input using default validator"""
    return default_validator.sanitize_input(user_input, max_length)


__all__ = [
    'SecurityValidator',
    'SecurityError',
    'FileValidationError', 
    'PathTraversalError',
    'ContentValidationError',
    'default_validator',
    'validate_filename',
    'validate_file_content',
    'validate_path',
    'sanitize_input'
]
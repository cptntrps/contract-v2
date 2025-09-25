"""
Input validation utilities with comprehensive error handling
"""
import re
import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from marshmallow import Schema, fields, ValidationError as MarshmallowValidationError, validate

from .exceptions import ValidationError, SecurityError, FileProcessingError
from ..logging.setup import get_logger

logger = get_logger(__name__)


class ValidationHandler:
    """Enhanced validation handler with detailed error messages"""
    
    @staticmethod
    def validate_contract_id(contract_id: str) -> str:
        """
        Validate contract ID format
        
        Args:
            contract_id: Contract identifier to validate
            
        Returns:
            Validated contract ID
            
        Raises:
            ValidationError: If contract ID is invalid
        """
        if not contract_id:
            raise ValidationError("Contract ID is required", field="contract_id")
        
        if not isinstance(contract_id, str):
            raise ValidationError("Contract ID must be a string", field="contract_id", value=contract_id)
        
        # Allow alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', contract_id):
            raise ValidationError(
                "Contract ID can only contain letters, numbers, and underscores",
                field="contract_id",
                value=contract_id
            )
        
        if len(contract_id) > 50:
            raise ValidationError(
                "Contract ID cannot exceed 50 characters",
                field="contract_id",
                value=f"Length: {len(contract_id)}"
            )
        
        if len(contract_id) < 3:
            raise ValidationError(
                "Contract ID must be at least 3 characters",
                field="contract_id",
                value=f"Length: {len(contract_id)}"
            )
        
        return contract_id
    
    @staticmethod
    def validate_analysis_id(analysis_id: str) -> str:
        """
        Validate analysis ID format
        
        Args:
            analysis_id: Analysis identifier to validate
            
        Returns:
            Validated analysis ID
            
        Raises:
            ValidationError: If analysis ID is invalid
        """
        if not analysis_id:
            raise ValidationError("Analysis ID is required", field="analysis_id")
        
        if not isinstance(analysis_id, str):
            raise ValidationError("Analysis ID must be a string", field="analysis_id", value=analysis_id)
        
        # Allow alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', analysis_id):
            raise ValidationError(
                "Analysis ID can only contain letters, numbers, underscores, and hyphens",
                field="analysis_id",
                value=analysis_id
            )
        
        if len(analysis_id) > 100:
            raise ValidationError(
                "Analysis ID cannot exceed 100 characters",
                field="analysis_id",
                value=f"Length: {len(analysis_id)}"
            )
        
        return analysis_id
    
    @staticmethod
    def validate_file_upload(file, allowed_extensions: List[str] = None, max_size: int = None) -> Dict[str, Any]:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file object
            allowed_extensions: List of allowed file extensions
            max_size: Maximum file size in bytes
            
        Returns:
            Dictionary with file information
            
        Raises:
            ValidationError: If file validation fails
        """
        if not file:
            raise ValidationError("No file provided", field="file")
        
        if not file.filename:
            raise ValidationError("No file selected", field="file")
        
        filename = file.filename
        file_size = None
        
        # Get file size if possible
        try:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)  # Reset file pointer
        except Exception:
            pass
        
        # Validate file extension
        if allowed_extensions:
            file_ext = Path(filename).suffix.lower()
            if file_ext not in [f".{ext.lower()}" for ext in allowed_extensions]:
                raise ValidationError(
                    f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}",
                    field="file",
                    value=file_ext
                )
        
        # Validate file size
        if max_size and file_size and file_size > max_size:
            raise ValidationError(
                f"File too large. Maximum size: {max_size // (1024*1024)}MB",
                field="file",
                value=f"{file_size // (1024*1024)}MB"
            )
        
        # Security validation for filename
        ValidationHandler.validate_filename(filename)
        
        return {
            'filename': filename,
            'size': file_size,
            'extension': Path(filename).suffix.lower()
        }
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate filename for security issues
        
        Args:
            filename: Filename to validate
            
        Returns:
            Validated filename
            
        Raises:
            SecurityError: If filename contains security risks
        """
        if not filename:
            raise ValidationError("Filename is required", field="filename")
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            raise SecurityError("path_traversal", f"Invalid filename: {filename}")
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        for char in dangerous_chars:
            if char in filename:
                raise SecurityError("invalid_characters", f"Filename contains invalid character: {char}")
        
        # Check filename length
        if len(filename) > 255:
            raise ValidationError(
                "Filename too long (max 255 characters)",
                field="filename",
                value=f"Length: {len(filename)}"
            )
        
        return filename
    
    @staticmethod
    def validate_template_id(template_id: str) -> str:
        """
        Validate template ID format
        
        Args:
            template_id: Template identifier to validate
            
        Returns:
            Validated template ID
            
        Raises:
            ValidationError: If template ID is invalid
        """
        if not template_id:
            raise ValidationError("Template ID is required", field="template_id")
        
        if not isinstance(template_id, str):
            raise ValidationError("Template ID must be a string", field="template_id", value=template_id)
        
        # Allow alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', template_id):
            raise ValidationError(
                "Template ID can only contain letters, numbers, underscores, and hyphens",
                field="template_id",
                value=template_id
            )
        
        if len(template_id) > 100:
            raise ValidationError(
                "Template ID cannot exceed 100 characters",
                field="template_id",
                value=f"Length: {len(template_id)}"
            )
        
        return template_id
    
    @staticmethod
    def validate_pagination(page: Union[str, int], per_page: Union[str, int]) -> Dict[str, int]:
        """
        Validate pagination parameters
        
        Args:
            page: Page number
            per_page: Items per page
            
        Returns:
            Dictionary with validated pagination values
            
        Raises:
            ValidationError: If pagination parameters are invalid
        """
        try:
            page_num = int(page) if page else 1
            per_page_num = int(per_page) if per_page else 20
        except ValueError:
            raise ValidationError("Page and per_page must be integers", field="pagination")
        
        if page_num < 1:
            raise ValidationError("Page number must be greater than 0", field="page", value=page_num)
        
        if per_page_num < 1 or per_page_num > 100:
            raise ValidationError(
                "Items per page must be between 1 and 100",
                field="per_page",
                value=per_page_num
            )
        
        return {
            'page': page_num,
            'per_page': per_page_num,
            'offset': (page_num - 1) * per_page_num
        }
    
    @staticmethod
    def validate_analysis_request(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate analysis request data
        
        Args:
            data: Analysis request data
            
        Returns:
            Validated data
            
        Raises:
            ValidationError: If validation fails
        """
        validated = {}
        
        # Validate required fields
        if 'contract_id' not in data:
            raise ValidationError("Contract ID is required", field="contract_id")
        
        if 'template_id' not in data:
            raise ValidationError("Template ID is required", field="template_id")
        
        # Validate individual fields
        validated['contract_id'] = ValidationHandler.validate_contract_id(data['contract_id'])
        validated['template_id'] = ValidationHandler.validate_template_id(data['template_id'])
        
        # Validate optional fields
        if 'include_llm_analysis' in data:
            if not isinstance(data['include_llm_analysis'], bool):
                raise ValidationError(
                    "include_llm_analysis must be a boolean",
                    field="include_llm_analysis",
                    value=data['include_llm_analysis']
                )
            validated['include_llm_analysis'] = data['include_llm_analysis']
        
        return validated


# Marshmallow schemas for complex validation
class ContractUploadSchema(Schema):
    """Schema for contract upload validation"""
    file = fields.Raw(required=True)
    description = fields.Str(load_default=None, validate=validate.Length(max=500))
    tags = fields.List(fields.Str(validate=validate.Length(max=50)), load_default=[])


class AnalysisRequestSchema(Schema):
    """Schema for analysis request validation"""
    contract_id = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    template_id = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    include_llm_analysis = fields.Bool(load_default=True)
    priority = fields.Str(load_default='normal', validate=validate.OneOf(['low', 'normal', 'high']))


class ReportGenerationSchema(Schema):
    """Schema for report generation validation"""
    analysis_id = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    report_type = fields.Str(required=True, validate=validate.OneOf(['pdf', 'excel', 'word', 'changes']))
    include_details = fields.Bool(load_default=True)
    format_options = fields.Dict(load_default={})


def validate_schema(schema_class: Schema, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate data against Marshmallow schema
    
    Args:
        schema_class: Marshmallow schema class
        data: Data to validate
        
    Returns:
        Validated and cleaned data
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        schema = schema_class()
        result = schema.load(data)
        return result
    except MarshmallowValidationError as e:
        # Convert Marshmallow errors to our ValidationError
        errors = []
        for field, messages in e.messages.items():
            for message in messages if isinstance(messages, list) else [messages]:
                errors.append(f"{field}: {message}")
        
        raise ValidationError(
            f"Validation failed: {'; '.join(errors)}",
            details={'validation_errors': e.messages}
        )
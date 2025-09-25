"""
Custom exception classes for contract analyzer application.

Provides structured exception hierarchy with detailed error information
for comprehensive error handling and debugging throughout the application.

AI Context: These exceptions provide structured error information for debugging.
When errors occur, check the exception details dictionary for specific context
about what failed and why.
"""
from typing import Any, Dict, Optional


class ContractAnalyzerError(Exception):
    """
    Base exception for all contract analyzer errors.
    
    Purpose: Provides structured error handling with error codes, messages,
    and detailed context. All application exceptions inherit from this base
    to ensure consistent error reporting and debugging information.
    
    AI Context: Base class for all application errors. Provides standardized
    error structure with details dictionary for debugging context. Check
    the to_dict() method output for comprehensive error information.
    """
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON responses"""
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }


class ValidationError(ContractAnalyzerError):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        super().__init__(message, **kwargs)
        if field:
            self.details['field'] = field
        if value is not None:
            self.details['value'] = str(value)


class NotFoundError(ContractAnalyzerError):
    """Raised when a requested resource is not found"""
    
    def __init__(self, resource: str, identifier: str = None, **kwargs):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, **kwargs)
        self.details['resource'] = resource
        if identifier:
            self.details['identifier'] = identifier


class ConfigurationError(ContractAnalyzerError):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, parameter: str, message: str = None, **kwargs):
        msg = message or f"Invalid configuration parameter: {parameter}"
        super().__init__(msg, **kwargs)
        self.details['parameter'] = parameter


class DatabaseError(ContractAnalyzerError):
    """Raised when database operations fail"""
    
    def __init__(self, operation: str, message: str = None, **kwargs):
        msg = message or f"Database operation failed: {operation}"
        super().__init__(msg, **kwargs)
        self.details['operation'] = operation


class FileProcessingError(ContractAnalyzerError):
    """Raised when file processing fails"""
    
    def __init__(self, filename: str, operation: str, message: str = None, **kwargs):
        msg = message or f"File processing failed: {operation} on {filename}"
        super().__init__(msg, **kwargs)
        self.details.update({
            'filename': filename,
            'operation': operation
        })


class LLMError(ContractAnalyzerError):
    """Raised when LLM operations fail"""
    
    def __init__(self, provider: str, operation: str, message: str = None, **kwargs):
        msg = message or f"LLM operation failed: {operation} with {provider}"
        super().__init__(msg, **kwargs)
        self.details.update({
            'provider': provider,
            'operation': operation
        })


class SecurityError(ContractAnalyzerError):
    """Raised when security validation fails"""
    
    def __init__(self, violation_type: str, message: str = None, **kwargs):
        msg = message or f"Security violation: {violation_type}"
        super().__init__(msg, **kwargs)
        self.details['violation_type'] = violation_type


class RateLimitError(ContractAnalyzerError):
    """Raised when rate limits are exceeded"""
    
    def __init__(self, limit: int, window: str, message: str = None, **kwargs):
        msg = message or f"Rate limit exceeded: {limit} requests per {window}"
        super().__init__(msg, **kwargs)
        self.details.update({
            'limit': limit,
            'window': window
        })


class AnalysisError(ContractAnalyzerError):
    """Raised when contract analysis fails"""
    
    def __init__(self, contract_id: str, step: str, message: str = None, **kwargs):
        msg = message or f"Analysis failed at step {step} for contract {contract_id}"
        super().__init__(msg, **kwargs)
        self.details.update({
            'contract_id': contract_id,
            'step': step
        })


class TemplateError(ContractAnalyzerError):
    """Raised when template operations fail"""
    
    def __init__(self, template_id: str, operation: str, message: str = None, **kwargs):
        msg = message or f"Template operation failed: {operation} for {template_id}"
        super().__init__(msg, **kwargs)
        self.details.update({
            'template_id': template_id,
            'operation': operation
        })


class ReportGenerationError(ContractAnalyzerError):
    """Raised when report generation fails"""
    
    def __init__(self, report_type: str, analysis_id: str, message: str = None, **kwargs):
        msg = message or f"Report generation failed: {report_type} for analysis {analysis_id}"
        super().__init__(msg, **kwargs)
        self.details.update({
            'report_type': report_type,
            'analysis_id': analysis_id
        })


class TaskError(ContractAnalyzerError):
    """Raised when async task operations fail"""
    
    def __init__(self, task_type: str, message: str = None, **kwargs):
        msg = message or f"Task operation failed: {task_type}"
        super().__init__(msg, **kwargs)
        self.details['task_type'] = task_type
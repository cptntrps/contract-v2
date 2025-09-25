"""
Standardized error response formatting
"""
from typing import Any, Dict, Optional, Union
from flask import jsonify, request
from datetime import datetime

from .exceptions import ContractAnalyzerError, ValidationError, NotFoundError, SecurityError, RateLimitError
from ..logging.setup import get_logger

logger = get_logger(__name__)


class ErrorResponse:
    """Standardized error response formatter"""
    
    @staticmethod
    def format_error(
        error: Union[Exception, ContractAnalyzerError], 
        status_code: int = 500,
        include_details: bool = True,
        request_id: str = None
    ) -> Dict[str, Any]:
        """
        Format error for JSON API response
        
        Args:
            error: Exception to format
            status_code: HTTP status code
            include_details: Whether to include error details
            request_id: Optional request ID for tracking
            
        Returns:
            Formatted error dictionary
        """
        response = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'status_code': status_code
        }
        
        # Add request information if available
        try:
            if request and hasattr(request, 'endpoint'):
                response['endpoint'] = request.endpoint
                response['method'] = request.method
        except RuntimeError:
            # Outside of request context
            pass
        
        if request_id:
            response['request_id'] = request_id
        
        # Format error details
        if isinstance(error, ContractAnalyzerError):
            response.update(error.to_dict())
            if not include_details:
                response.pop('details', None)
        else:
            response.update({
                'error': error.__class__.__name__,
                'message': str(error)
            })
        
        return response
    
    @staticmethod
    def validation_error(field: str, message: str, value: Any = None) -> Dict[str, Any]:
        """Create validation error response"""
        return ErrorResponse.format_error(
            ValidationError(message, field=field, value=value),
            status_code=400
        )
    
    @staticmethod
    def not_found_error(resource: str, identifier: str = None) -> Dict[str, Any]:
        """Create not found error response"""
        return ErrorResponse.format_error(
            NotFoundError(resource, identifier=identifier),
            status_code=404
        )
    
    @staticmethod
    def unauthorized_error(message: str = "Authentication required") -> Dict[str, Any]:
        """Create unauthorized error response"""
        return ErrorResponse.format_error(
            SecurityError("authentication_required", message=message),
            status_code=401
        )
    
    @staticmethod
    def forbidden_error(message: str = "Access denied") -> Dict[str, Any]:
        """Create forbidden error response"""
        return ErrorResponse.format_error(
            SecurityError("access_denied", message=message),
            status_code=403
        )
    
    @staticmethod
    def rate_limit_error(limit: int, window: str) -> Dict[str, Any]:
        """Create rate limit error response"""
        return ErrorResponse.format_error(
            RateLimitError(limit, window),
            status_code=429
        )
    
    @staticmethod
    def internal_error(error: Exception, show_details: bool = False) -> Dict[str, Any]:
        """Create internal server error response"""
        return ErrorResponse.format_error(
            error,
            status_code=500,
            include_details=show_details
        )


def create_error_response(error: Exception, status_code: int = None) -> tuple:
    """
    Create Flask error response tuple
    
    Args:
        error: Exception to format
        status_code: HTTP status code (auto-detected if None)
        
    Returns:
        Tuple of (response, status_code) for Flask
    """
    # Auto-detect status code based on error type
    if status_code is None:
        if isinstance(error, NotFoundError):
            status_code = 404
        elif isinstance(error, ValidationError):
            status_code = 400
        elif isinstance(error, SecurityError):
            if "authentication" in str(error).lower():
                status_code = 401
            elif "access" in str(error).lower() or "forbidden" in str(error).lower():
                status_code = 403
            else:
                status_code = 400
        elif isinstance(error, RateLimitError):
            status_code = 429
        else:
            status_code = 500
    
    # Log error for internal tracking
    if status_code >= 500:
        logger.error(f"Internal error: {error}", exc_info=True)
    elif status_code >= 400:
        logger.warning(f"Client error ({status_code}): {error}")
    
    # Format response
    response_data = ErrorResponse.format_error(error, status_code)
    
    return jsonify(response_data), status_code


def handle_database_error(error: Exception) -> tuple:
    """Handle database-specific errors"""
    from sqlalchemy.exc import IntegrityError, OperationalError, InvalidRequestError
    from .exceptions import DatabaseError
    
    if isinstance(error, IntegrityError):
        return create_error_response(
            DatabaseError("constraint_violation", "Database constraint violation"),
            400
        )
    elif isinstance(error, OperationalError):
        return create_error_response(
            DatabaseError("connection_error", "Database connection failed"),
            503
        )
    elif isinstance(error, InvalidRequestError):
        return create_error_response(
            DatabaseError("invalid_request", "Invalid database request"),
            400
        )
    else:
        return create_error_response(
            DatabaseError("unknown", f"Database error: {str(error)}"),
            500
        )
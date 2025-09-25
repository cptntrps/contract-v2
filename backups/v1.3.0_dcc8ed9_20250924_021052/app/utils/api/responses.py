"""
Standardized API response utilities

Provides consistent response formatting for all API endpoints.
"""

from flask import jsonify
from typing import Any, Dict, Optional, List
from datetime import datetime
import uuid


class APIResponse:
    """Standardized API response formatter"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
        """
        Create a successful API response
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            
        Returns:
            Tuple of (response, status_code)
        """
        response = {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4())[:8]
        }
        
        return jsonify(response), status_code
    
    @staticmethod
    def error(
        message: str,
        error_code: str = "GENERIC_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ) -> tuple:
        """
        Create an error API response
        
        Args:
            message: Error message
            error_code: Specific error code for client handling
            details: Additional error details
            status_code: HTTP status code
            
        Returns:
            Tuple of (response, status_code)
        """
        response = {
            "success": False,
            "error": {
                "message": message,
                "code": error_code,
                "details": details or {}
            },
            "timestamp": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4())[:8]
        }
        
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(errors: List[str], status_code: int = 400) -> tuple:
        """
        Create a validation error response
        
        Args:
            errors: List of validation error messages
            status_code: HTTP status code
            
        Returns:
            Tuple of (response, status_code)
        """
        return APIResponse.error(
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            details={"validation_errors": errors},
            status_code=status_code
        )
    
    @staticmethod
    def not_found(resource: str = "Resource", status_code: int = 404) -> tuple:
        """
        Create a not found error response
        
        Args:
            resource: Name of the resource not found
            status_code: HTTP status code
            
        Returns:
            Tuple of (response, status_code)
        """
        return APIResponse.error(
            message=f"{resource} not found",
            error_code="NOT_FOUND",
            status_code=status_code
        )
    
    @staticmethod
    def unauthorized(message: str = "Unauthorized access", status_code: int = 401) -> tuple:
        """
        Create an unauthorized error response
        
        Args:
            message: Error message
            status_code: HTTP status code
            
        Returns:
            Tuple of (response, status_code)
        """
        return APIResponse.error(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=status_code
        )
    
    @staticmethod
    def forbidden(message: str = "Access forbidden", status_code: int = 403) -> tuple:
        """
        Create a forbidden error response
        
        Args:
            message: Error message
            status_code: HTTP status code
            
        Returns:
            Tuple of (response, status_code)
        """
        return APIResponse.error(
            message=message,
            error_code="FORBIDDEN",
            status_code=status_code
        )
    
    @staticmethod
    def rate_limited(message: str = "Rate limit exceeded", status_code: int = 429) -> tuple:
        """
        Create a rate limited error response
        
        Args:
            message: Error message
            status_code: HTTP status code
            
        Returns:
            Tuple of (response, status_code)
        """
        return APIResponse.error(
            message=message,
            error_code="RATE_LIMITED",
            status_code=status_code
        )
"""
Error handlers for Flask application
"""
import traceback
from typing import Any, Dict
from flask import Flask, request, jsonify, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from .exceptions import *
from .responses import ErrorResponse, create_error_response, handle_database_error
from ..logging.setup import get_logger
from ..security.audit import SecurityAuditor

logger = get_logger(__name__)


class ErrorHandler:
    """Central error handler for the application"""
    
    def __init__(self, app: Flask = None, auditor: SecurityAuditor = None):
        self.app = app
        self.auditor = auditor or SecurityAuditor()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize error handlers with Flask app"""
        self.app = app
        self.register_handlers(app)
    
    def register_handlers(self, app: Flask):
        """Register all error handlers"""
        
        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            """Handle validation errors"""
            self.auditor.log_security_event(
                event_type='validation_error',
                details={'field': error.details.get('field'), 'message': error.message},
                request=request
            )
            return create_error_response(error, 400)
        
        @app.errorhandler(NotFoundError)
        def handle_not_found_error(error):
            """Handle not found errors"""
            return create_error_response(error, 404)
        
        @app.errorhandler(SecurityError)
        def handle_security_error(error):
            """Handle security errors"""
            self.auditor.log_security_event(
                event_type='security_violation',
                details={'violation_type': error.details.get('violation_type'), 'message': error.message},
                severity='HIGH',
                request=request
            )
            
            # Determine status code based on violation type
            violation_type = error.details.get('violation_type', '')
            if 'authentication' in violation_type:
                status_code = 401
            elif 'access' in violation_type or 'forbidden' in violation_type:
                status_code = 403
            else:
                status_code = 400
            
            return create_error_response(error, status_code)
        
        @app.errorhandler(DatabaseError)
        def handle_database_error_custom(error):
            """Handle database errors"""
            logger.error(f"Database error: {error}")
            return create_error_response(error, 500)
        
        @app.errorhandler(SQLAlchemyError)
        def handle_sqlalchemy_error(error):
            """Handle SQLAlchemy errors"""
            logger.error(f"SQLAlchemy error: {error}")
            return handle_database_error(error)
        
        @app.errorhandler(FileProcessingError)
        def handle_file_processing_error(error):
            """Handle file processing errors"""
            logger.error(f"File processing error: {error}")
            return create_error_response(error, 400)
        
        @app.errorhandler(LLMError)
        def handle_llm_error(error):
            """Handle LLM errors"""
            logger.error(f"LLM error: {error}")
            return create_error_response(error, 502)  # Bad Gateway
        
        @app.errorhandler(RateLimitError)
        def handle_rate_limit_error(error):
            """Handle rate limit errors"""
            logger.warning(f"Rate limit exceeded: {error}")
            return create_error_response(error, 429)
        
        @app.errorhandler(AnalysisError)
        def handle_analysis_error(error):
            """Handle analysis errors"""
            logger.error(f"Analysis error: {error}")
            return create_error_response(error, 422)  # Unprocessable Entity
        
        @app.errorhandler(ConfigurationError)
        def handle_configuration_error(error):
            """Handle configuration errors"""
            logger.error(f"Configuration error: {error}")
            return create_error_response(error, 500)
        
        @app.errorhandler(400)
        def handle_bad_request(error):
            """Handle bad request errors"""
            return create_error_response(
                ValidationError("Bad request", details={'description': error.description}),
                400
            )
        
        @app.errorhandler(401)
        def handle_unauthorized(error):
            """Handle unauthorized access"""
            return create_error_response(
                SecurityError("authentication_required", "Authentication required"),
                401
            )
        
        @app.errorhandler(403)
        def handle_forbidden(error):
            """Handle forbidden access"""
            return create_error_response(
                SecurityError("access_denied", "Access denied"),
                403
            )
        
        @app.errorhandler(404)
        def handle_not_found(error):
            """Handle 404 errors"""
            # For API endpoints, return JSON error
            if request.path.startswith('/api/'):
                return create_error_response(
                    NotFoundError("endpoint", request.path),
                    404
                )
            else:
                # For web routes, serve the main dashboard
                from flask import render_template
                return render_template('dashboard.html'), 200
        
        @app.errorhandler(405)
        def handle_method_not_allowed(error):
            """Handle method not allowed errors"""
            return create_error_response(
                ValidationError(f"Method {request.method} not allowed for {request.path}"),
                405
            )
        
        @app.errorhandler(413)
        def handle_payload_too_large(error):
            """Handle file too large errors"""
            return create_error_response(
                FileProcessingError("uploaded_file", "size_validation", "File too large"),
                413
            )
        
        @app.errorhandler(415)
        def handle_unsupported_media_type(error):
            """Handle unsupported media type errors"""
            return create_error_response(
                FileProcessingError("uploaded_file", "type_validation", "Unsupported file type"),
                415
            )
        
        @app.errorhandler(429)
        def handle_rate_limit(error):
            """Handle rate limit errors"""
            return create_error_response(
                RateLimitError(100, "hour", "Rate limit exceeded"),
                429
            )
        
        @app.errorhandler(500)
        def handle_internal_error(error):
            """Handle internal server errors"""
            # Log detailed error information
            logger.error(f"Internal server error: {error}")
            if current_app.debug:
                logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Log security event for server errors
            self.auditor.log_security_event(
                event_type='server_error',
                details={'error_type': type(error).__name__, 'message': str(error)},
                severity='HIGH',
                request=request
            )
            
            # Return generic error in production, detailed in debug
            if current_app.debug:
                return create_error_response(error, 500)
            else:
                return create_error_response(
                    ContractAnalyzerError("Internal server error"),
                    500
                )
        
        @app.errorhandler(502)
        def handle_bad_gateway(error):
            """Handle bad gateway errors (e.g., LLM service unavailable)"""
            return create_error_response(
                LLMError("external_service", "connection", "External service unavailable"),
                502
            )
        
        @app.errorhandler(503)
        def handle_service_unavailable(error):
            """Handle service unavailable errors"""
            return create_error_response(
                DatabaseError("connection", "Service temporarily unavailable"),
                503
            )
        
        @app.errorhandler(Exception)
        def handle_unexpected_error(error):
            """Handle any unexpected exceptions"""
            # Log the full traceback for debugging
            logger.exception(f"Unexpected error: {error}")
            
            # Log security event for unexpected errors
            self.auditor.log_security_event(
                event_type='unexpected_error',
                details={
                    'error_type': type(error).__name__,
                    'message': str(error),
                    'traceback': traceback.format_exc() if current_app.debug else None
                },
                severity='HIGH',
                request=request
            )
            
            # Return appropriate response based on environment
            if current_app.debug:
                return create_error_response(error, 500)
            else:
                return create_error_response(
                    ContractAnalyzerError("An unexpected error occurred"),
                    500
                )


def register_error_handlers(app: Flask, auditor: SecurityAuditor = None) -> ErrorHandler:
    """
    Register error handlers with Flask application
    
    Args:
        app: Flask application instance
        auditor: Security auditor instance
        
    Returns:
        ErrorHandler instance
    """
    error_handler = ErrorHandler(app, auditor)
    logger.info("Error handlers registered successfully")
    return error_handler
"""
Flask Application Factory

Creates and configures the Flask application with all routes, middleware,
and error handlers.
"""

import logging
from pathlib import Path
from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from ..utils.security.audit import default_auditor, SecurityEventType
from ..utils.logging.setup import get_logger

logger = get_logger(__name__)


def create_api_app(config) -> Flask:
    """
    Create and configure Flask application
    
    Args:
        config: Configuration object
        
    Returns:
        Configured Flask application
    """
    # Create Flask app
    app = Flask(
        __name__,
        template_folder=str(config.BASE_DIR / config.TEMPLATE_FOLDER),
        static_folder=str(config.BASE_DIR / config.STATIC_FOLDER)
    )
    
    # Configure Flask app
    app.config.update({
        'SECRET_KEY': config.SECRET_KEY,
        'ENV': config.ENV,
        'DEBUG': config.DEBUG,
        'UPLOAD_FOLDER': str(config.BASE_DIR / config.UPLOAD_FOLDER),
        'TEMPLATES_FOLDER': str(config.BASE_DIR / config.TEMPLATES_FOLDER),
        'REPORTS_FOLDER': str(config.BASE_DIR / config.REPORTS_FOLDER),
        'MAX_CONTENT_LENGTH': config.MAX_CONTENT_LENGTH,
        'TESTING': getattr(config, 'TESTING', False)
    })
    
    # Add proxy fix for production deployments
    if config.ENV == 'production':
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Register middleware
    register_middleware(app, config)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register routes
    register_routes(app, config)
    
    # Log application startup
    default_auditor.log_server_event('started', {
        'env': config.ENV,
        'debug': config.DEBUG,
        'host': config.HOST,
        'port': config.PORT
    })
    
    logger.info(f"Flask application created - Environment: {config.ENV}")
    return app


def register_middleware(app: Flask, config):
    """Register application middleware"""
    
    @app.before_request
    def log_request_info():
        """Log incoming requests for security audit"""
        # Skip logging for static files and health checks
        if request.endpoint in ['static', 'health_check']:
            return
        
        logger.debug(f"Request: {request.method} {request.path} from {request.remote_addr}")
    
    @app.before_request
    def start_timer():
        """Start timing the request"""
        import time
        request._start_time = time.time()
    
    @app.after_request
    def log_response_info(response):
        """Log response information"""
        # Skip logging for static files and health checks
        if request.endpoint in ['static', 'health_check']:
            return response
        
        # Calculate response time
        import time
        response_time = 0.0
        if hasattr(request, '_start_time'):
            response_time = time.time() - request._start_time
            response._response_time = response_time
        
        # Log API access for security audit
        if request.path.startswith('/api/'):
            default_auditor.log_api_access(
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                response_time=response_time,
                user_ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        
        return response
    
    @app.before_request
    def ensure_directories():
        """Ensure required directories exist"""
        required_dirs = [
            app.config['UPLOAD_FOLDER'],
            app.config['TEMPLATES_FOLDER'], 
            app.config['REPORTS_FOLDER']
        ]
        
        for directory in required_dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)


def register_error_handlers(app: Flask):
    """Register application error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad request errors"""
        logger.warning(f"Bad request: {error}")
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors"""
        logger.warning(f"Not found: {request.path}")
        
        # Differentiate between API and web requests
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint not found'}), 404
        else:
            # Serve the main dashboard for web routes
            from flask import render_template
            return render_template('dashboard.html'), 200
    
    @app.errorhandler(413)
    def payload_too_large(error):
        """Handle file too large errors"""
        logger.warning(f"File too large: {error}")
        return jsonify({'error': 'File too large'}), 413
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle rate limit errors"""
        logger.warning(f"Rate limit exceeded: {error}")
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors"""
        logger.error(f"Internal server error: {error}")
        
        # Log security event for server errors
        default_auditor.log_security_event(
            SecurityEventType.ERROR_OCCURRED,
            {'error_type': 'internal_server_error', 'error': str(error)},
            'ERROR',
            request.remote_addr if request else None
        )
        
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions"""
        logger.exception(f"Unhandled exception: {error}")
        
        # Log security event for unexpected errors
        default_auditor.log_security_event(
            SecurityEventType.ERROR_OCCURRED,
            {'error_type': 'unhandled_exception', 'error': str(error)},
            'ERROR',
            request.remote_addr if request else None
        )
        
        return jsonify({'error': 'An unexpected error occurred'}), 500


def register_routes(app: Flask, config):
    """Register application routes"""
    
    # Main dashboard route
    @app.route('/')
    def index():
        """Main dashboard page"""
        from flask import render_template
        return render_template('dashboard.html')
    
    # Import and register route blueprints
    from .routes.health import health_bp
    from .routes.contracts import contracts_bp
    from .routes.analysis import analysis_bp
    from .routes.reports import reports_bp
    from .routes.prompts import prompts_bp
    from .routes.compatibility import compatibility_bp
    
    # Register blueprints
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(contracts_bp, url_prefix='/api')
    app.register_blueprint(analysis_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api')
    app.register_blueprint(prompts_bp, url_prefix='/api')
    app.register_blueprint(compatibility_bp, url_prefix='/api')  # Legacy compatibility
    
    logger.info("Application routes registered")


__all__ = ['create_api_app']
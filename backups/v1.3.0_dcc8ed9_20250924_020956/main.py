"""
Application Factory Pattern

Creates and configures the Flask application with all necessary components,
middleware, and route registrations.
"""

import logging
from pathlib import Path
from flask import Flask

from .config.settings import get_config
from .api.app import create_api_app
from .utils.logging.setup import setup_logging


def create_app(config_name: str = None) -> Flask:
    """
    Application factory function.
    
    Args:
        config_name: Configuration environment name (development, production, testing)
        
    Returns:
        Configured Flask application instance
    """
    # Determine configuration
    config = get_config(config_name)
    
    # Setup logging first
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    # Create Flask app
    app = create_api_app(config)
    
    # Log application startup
    logger.info(f"Contract Analyzer started - Environment: {config.ENV}")
    logger.info(f"Debug mode: {config.DEBUG}")
    logger.info(f"Base directory: {config.BASE_DIR}")
    
    return app


def get_app_info() -> dict:
    """Get application information for health checks."""
    from . import __version__
    
    return {
        "name": "Contract Analyzer",
        "version": __version__,
        "status": "healthy"
    }
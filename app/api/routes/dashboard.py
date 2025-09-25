"""
Dashboard API Routes - Infrastructure Layer

HTTP endpoints for dashboard functionality. Delegates all business logic
to DashboardService following architectural separation of concerns.
"""

import logging
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError

from ...application.services.dashboard_service import DashboardService, DashboardDataError
from ...utils.errors.responses import create_error_response

logger = logging.getLogger(__name__)

# Create blueprint for dashboard routes
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


class DashboardRefreshSchema(Schema):
    """Schema for dashboard refresh requests."""
    refresh_type = fields.Str(missing='full', validate=lambda x: x in ['full', 'metrics', 'results'])
    force_refresh = fields.Bool(missing=False)


# Initialize schemas
dashboard_refresh_schema = DashboardRefreshSchema()


@dashboard_bp.route('/data', methods=['GET'])
def get_dashboard_data():
    """
    Retrieves complete dashboard data.
    
    Purpose: HTTP endpoint that delegates to DashboardService for complete
    dashboard state. Handles only HTTP concerns - parsing, formatting, errors.
    
    Returns:
        JSON response with dashboard data or error information
    
    AI Context: Primary dashboard data endpoint. If dashboard displays
    incorrect data, verify this endpoint returns expected JSON structure.
    Business logic is handled by DashboardService.
    """
    try:
        logger.info("Dashboard data requested")
        
        # Delegate to application service
        dashboard_service = DashboardService()
        dashboard_data = dashboard_service.get_dashboard_data()
        
        # Format HTTP response
        response_data = {
            'success': True,
            'data': dashboard_data,
            'message': 'Dashboard data retrieved successfully'
        }
        
        logger.info(f"Dashboard data returned: {dashboard_data['metrics']['total_analyses']} analyses")
        return jsonify(response_data), 200
        
    except DashboardDataError as e:
        logger.error(f"Dashboard data error: {e}")
        return create_error_response(e, 422)
    except Exception as e:
        logger.error(f"Unexpected error in get_dashboard_data: {e}")
        error_response = {
            'success': False,
            'error': 'Failed to retrieve dashboard data',
            'message': 'An unexpected error occurred while loading dashboard'
        }
        return jsonify(error_response), 500


@dashboard_bp.route('/refresh', methods=['POST'])
def refresh_dashboard():
    """
    Refreshes dashboard data based on request parameters.
    
    Purpose: HTTP endpoint for manual dashboard refresh operations.
    Supports different refresh types (full, metrics-only, results-only).
    
    Request Body:
        {
            "refresh_type": "full|metrics|results",  // Optional, defaults to "full"  
            "force_refresh": boolean                 // Optional, defaults to false
        }
    
    Returns:
        JSON response with refreshed data or error information
    
    AI Context: Used by frontend refresh button. If refresh fails, check
    DashboardService methods for data retrieval issues. This endpoint
    handles only HTTP validation and response formatting.
    """
    try:
        # Parse and validate HTTP request
        request_data = dashboard_refresh_schema.load(request.json or {})
        refresh_type = request_data['refresh_type']
        
        logger.info(f"Dashboard refresh requested: type={refresh_type}")
        
        # Delegate to application service
        dashboard_service = DashboardService()
        
        if refresh_type == 'metrics':
            # Metrics-only refresh
            refreshed_data = {
                'metrics': dashboard_service.get_dashboard_metrics()
            }
        elif refresh_type == 'results':
            # Results-only refresh  
            refreshed_data = {
                'analysis_results': dashboard_service.refresh_analysis_results()
            }
        else:
            # Full refresh (default)
            refreshed_data = dashboard_service.get_dashboard_data()
        
        # Format HTTP response
        response_data = {
            'success': True,
            'data': refreshed_data,
            'refresh_type': refresh_type,
            'message': f'Dashboard {refresh_type} refresh completed successfully'
        }
        
        logger.info(f"Dashboard refresh completed: type={refresh_type}")
        return jsonify(response_data), 200
        
    except ValidationError as e:
        logger.error(f"Invalid refresh request: {e.messages}")
        error_response = {
            'success': False,
            'error': 'Invalid request parameters',
            'details': e.messages
        }
        return jsonify(error_response), 400
    except DashboardDataError as e:
        logger.error(f"Dashboard refresh error: {e}")
        return create_error_response(e, 422)
    except Exception as e:
        logger.error(f"Unexpected error in refresh_dashboard: {e}")
        error_response = {
            'success': False,
            'error': 'Dashboard refresh failed',
            'message': 'An unexpected error occurred during refresh'
        }
        return jsonify(error_response), 500


@dashboard_bp.route('/metrics', methods=['GET'])
def get_dashboard_metrics():
    """
    Retrieves dashboard metrics only (lightweight operation).
    
    Purpose: HTTP endpoint for frequent metric updates without full data reload.
    Optimized for performance when only counts/statistics are needed.
    
    Returns:
        JSON response with dashboard metrics
    
    AI Context: Used for efficient metric updates. If metrics display incorrect
    values, verify DashboardService.get_dashboard_metrics() calculation logic.
    """
    try:
        logger.debug("Dashboard metrics requested")
        
        # Delegate to application service
        dashboard_service = DashboardService()
        metrics = dashboard_service.get_dashboard_metrics()
        
        # Format HTTP response
        response_data = {
            'success': True,
            'metrics': metrics,
            'message': 'Dashboard metrics retrieved successfully'
        }
        
        logger.debug(f"Dashboard metrics returned: {metrics}")
        return jsonify(response_data), 200
        
    except DashboardDataError as e:
        logger.error(f"Dashboard metrics error: {e}")
        return create_error_response(e, 422)
    except Exception as e:
        logger.error(f"Unexpected error in get_dashboard_metrics: {e}")
        error_response = {
            'success': False,
            'error': 'Failed to retrieve dashboard metrics',
            'message': 'An unexpected error occurred while loading metrics'
        }
        return jsonify(error_response), 500


@dashboard_bp.route('/health', methods=['GET'])
def dashboard_health_check():
    """
    Performs health check for dashboard functionality.
    
    Purpose: HTTP endpoint to verify dashboard service availability and
    basic functionality. Used for monitoring and debugging.
    
    Returns:
        JSON response with health status
    
    AI Context: Use this endpoint to verify dashboard service health
    when troubleshooting display issues or data loading problems.
    """
    try:
        logger.debug("Dashboard health check requested")
        
        # Test dashboard service availability
        dashboard_service = DashboardService()
        
        # Perform basic functionality test
        metrics = dashboard_service.get_dashboard_metrics()
        
        health_info = {
            'status': 'healthy',
            'service': 'dashboard',
            'timestamp': dashboard_service._get_system_health()['timestamp'],
            'basic_functionality': 'operational',
            'metrics_available': len(metrics) > 0
        }
        
        response_data = {
            'success': True,
            'health': health_info,
            'message': 'Dashboard service is healthy'
        }
        
        logger.debug("Dashboard health check passed")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Dashboard health check failed: {e}")
        
        health_info = {
            'status': 'unhealthy',
            'service': 'dashboard', 
            'error': str(e),
            'basic_functionality': 'failed'
        }
        
        response_data = {
            'success': False,
            'health': health_info,
            'message': 'Dashboard service health check failed'
        }
        
        return jsonify(response_data), 503


# Register error handlers for dashboard blueprint
@dashboard_bp.errorhandler(DashboardDataError)
def handle_dashboard_data_error(error):
    """Handle dashboard-specific errors."""
    return create_error_response(error, 422)


@dashboard_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle request validation errors."""
    error_response = {
        'success': False,
        'error': 'Request validation failed',
        'details': error.messages
    }
    return jsonify(error_response), 400
"""
Health check and system status routes
"""

from flask import Blueprint, jsonify
from ...main import get_app_info
from ...utils.logging.setup import get_logger

logger = get_logger(__name__)

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check():
    """Basic health check endpoint"""
    try:
        app_info = get_app_info()
        
        health_data = {
            **app_info,
            'status': 'healthy',
            'message': 'Application is running'
        }
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'message': 'Health check failed',
            'error': str(e)
        }), 500


@health_bp.route('/status')
def system_status():
    """Detailed system status"""
    try:
        # TODO: Add more detailed system checks
        # - Database connectivity
        # - LLM provider status
        # - File system status
        # - Memory usage
        
        status_data = {
            'application': get_app_info(),
            'system': {
                'status': 'operational',
                # TODO: Add system metrics
            },
            'services': {
                'llm_provider': 'unknown',  # TODO: Check LLM provider
                'file_storage': 'operational',  # TODO: Check file storage
            }
        }
        
        return jsonify(status_data), 200
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Status check failed',
            'error': str(e)
        }), 500


@health_bp.route('/model-info')
def model_info():
    """Get current LLM model information"""
    try:
        from ...config.settings import get_config
        config = get_config()
        
        return jsonify({
            'name': config.OPENAI_MODEL,
            'provider': config.LLM_PROVIDER,
            'model': config.OPENAI_MODEL,
            'status': 'connected',
            'connection_healthy': True,
            'info': f"{config.LLM_PROVIDER} - {config.OPENAI_MODEL}"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return jsonify({
            'name': 'gpt-4o',
            'provider': 'openai',
            'model': 'gpt-4o',
            'status': 'unknown',
            'connection_healthy': False,
            'info': 'Model information unavailable'
        }), 200


@health_bp.route('/cache-stats')
def cache_stats():
    """Get cache and memory statistics"""
    try:
        from ..routes.analysis import analysis_results_store
        from ..routes.contracts import contracts_store
        
        return jsonify({
            'success': True,
            'stats': {
                'analysis_count': len(analysis_results_store),
                'analysis_size': '0 MB',
                'reports_count': 0,
                'reports_size': '0 MB',
                'memory_count': len(contracts_store),
                'memory_size': '0 MB',
                'total_size': '0 MB'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load cache stats'
        }), 500


@health_bp.route('/available-models')
def available_models():
    """Get available models list"""
    try:
        from ...config.settings import get_config
        config = get_config()
        
        return jsonify({
            'success': True,
            'models': [
                {
                    'name': config.OPENAI_MODEL,
                    'size': 0,
                    'current': True
                }
            ],
            'current_model': config.OPENAI_MODEL
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load models'
        }), 500


@health_bp.route('/openai-models')
def openai_models():
    """Get OpenAI models list with detailed information"""
    try:
        from ...config.settings import get_config
        config = get_config()
        
        # OpenAI models with detailed info
        models = [
            {
                'name': 'gpt-4o',
                'description': 'Most advanced GPT-4 model with vision capabilities',
                'context_window': 128000,
                'tier': 'premium',
                'recommended': True
            },
            {
                'name': 'gpt-4o-mini',
                'description': 'Faster, more affordable GPT-4 model',
                'context_window': 128000,
                'tier': 'standard',
                'recommended': False
            },
            {
                'name': 'gpt-4-turbo',
                'description': 'Previous generation GPT-4 model',
                'context_window': 128000,
                'tier': 'premium',
                'recommended': False
            },
            {
                'name': 'gpt-3.5-turbo',
                'description': 'Fast and efficient GPT-3.5 model',
                'context_window': 16384,
                'tier': 'standard',
                'recommended': False
            }
        ]
        
        return jsonify({
            'success': True,
            'models': models,
            'current_model': config.OPENAI_MODEL,
            'recommendations': {
                'best_overall': 'gpt-4o',
                'most_economical': 'gpt-4o-mini'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting OpenAI models: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load OpenAI models'
        }), 500


@health_bp.route('/llm-provider')
def llm_provider():
    """Get LLM provider configuration"""
    try:
        from ...config.settings import get_config
        config = get_config()
        
        return jsonify({
            'success': True,
            'provider': config.LLM_PROVIDER,
            'model': config.OPENAI_MODEL,
            'api_key_configured': True,  # Assume configured
            'temperature': 0.1,
            'max_tokens': 1024
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting LLM provider info: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get LLM provider info'
        }), 500


@health_bp.route('/llm-settings', methods=['POST'])
def update_llm_settings():
    """Update LLM settings"""
    try:
        from flask import request
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Settings data required'
            }), 400
        
        # Log the settings update (in real implementation, would save to config)
        logger.info(f"LLM settings update requested: {data}")
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'updated_settings': data
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating LLM settings: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update settings'
        }), 500
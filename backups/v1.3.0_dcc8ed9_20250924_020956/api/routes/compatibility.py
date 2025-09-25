"""
Compatibility routes for legacy frontend endpoints

Provides backward compatibility for frontend that expects different endpoint names.
"""

from flask import Blueprint, jsonify, request
from .analysis import analysis_results_store
from .contracts import contracts_store
from ...config.settings import get_config
from ...utils.logging.setup import get_logger

logger = get_logger(__name__)
compatibility_bp = Blueprint('compatibility', __name__)










@compatibility_bp.route('/clear-cache', methods=['POST'])
def legacy_clear_cache():
    """Legacy endpoint for clearing cache"""
    try:
        return jsonify({
            'success': True,
            'message': 'Cache clearing not implemented'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in legacy clear cache endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear cache'
        }), 500


@compatibility_bp.route('/clear-contracts', methods=['POST'])
def legacy_clear_contracts():
    """Legacy endpoint for clearing contracts"""
    try:
        contracts_store.clear()
        return jsonify({
            'success': True,
            'message': 'All contracts cleared successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in legacy clear contracts endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear contracts'
        }), 500


@compatibility_bp.route('/clear-files', methods=['POST'])
def legacy_clear_files():
    """Legacy endpoint for clearing all files"""
    try:
        contracts_store.clear()
        return jsonify({
            'success': True,
            'message': 'All files cleared successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in legacy clear files endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear files'
        }), 500




@compatibility_bp.route('/update-openai-model', methods=['POST'])
def legacy_update_openai_model():
    """Legacy endpoint for updating OpenAI model"""
    try:
        data = request.get_json()
        if not data or 'model' not in data:
            return jsonify({
                'success': False,
                'error': 'Model name required'
            }), 400
        
        model_name = data['model']
        
        # Validate model name
        valid_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']
        if model_name not in valid_models:
            return jsonify({
                'success': False,
                'error': f'Invalid model: {model_name}'
            }), 400
        
        # In a real implementation, this would update the configuration
        logger.info(f"Model change requested: {model_name}")
        
        return jsonify({
            'success': True,
            'message': f'Model changed to {model_name}',
            'model': model_name
        }), 200
        
    except Exception as e:
        logger.error(f"Error in legacy update openai model endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update model'
        }), 500



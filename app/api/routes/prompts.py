"""
Prompt Management Routes - Infrastructure Layer

HTTP endpoints for prompt template management. Delegates all business logic
to PromptManagementService following architectural separation of concerns.
"""

import logging
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError

from ...core.services.prompt_management_service import PromptManagementService, PromptStorageError, ValidationError as PromptValidationError
from ...utils.errors.responses import create_error_response

logger = logging.getLogger(__name__)

# Create blueprint for prompt routes
prompts_bp = Blueprint('prompts', __name__)

# Frontend compatibility mapping for legacy support
PROMPT_TYPE_MAPPING = {
    'individual_analysis': 'contract_analysis',
    'batch_analysis': 'contract_analysis', 
    'ultra_fast': 'change_classification'
}


class PromptSchema(Schema):
    """Schema for prompt template requests."""
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    template = fields.Str(required=True)
    variables = fields.List(fields.Str(), missing=[])


class PromptValidationSchema(Schema):
    """Schema for prompt validation requests."""
    template = fields.Str(required=True)
    variables = fields.List(fields.Str(), missing=[])


class PromptPreviewSchema(Schema):
    """Schema for prompt preview requests."""
    template = fields.Str(required=True)
    prompt_type = fields.Str(missing='')
    sample_data = fields.Dict(missing={})


# Initialize schemas
prompt_schema = PromptSchema()
validation_schema = PromptValidationSchema()
preview_schema = PromptPreviewSchema()


@prompts_bp.route('/prompts', methods=['GET'])
def list_prompts():
    """
    List all available prompt templates.
    
    Purpose: HTTP endpoint that retrieves all prompt templates including both
    system defaults and user customizations. Handles only HTTP concerns.
    
    Returns:
        JSON response with prompt templates or error information
    
    AI Context: Thin HTTP adapter for prompt listing. All business logic is in
    PromptManagementService. For debugging prompt loading issues, check the service.
    """
    try:
        logger.debug("Prompt listing requested")
        
        # Delegate to service
        prompt_service = PromptManagementService()
        prompts = prompt_service.list_all_prompts()
        
        # Format HTTP response
        response_data = {
            'success': True,
            'prompts': prompts,
            'count': len(prompts),
            'message': 'Prompts retrieved successfully'
        }
        
        logger.debug(f"Listed {len(prompts)} prompt templates")
        return jsonify(response_data), 200
        
    except PromptStorageError as e:
        logger.error(f"Prompt storage error in list_prompts: {e}")
        return create_error_response(e, 422)
    except Exception as e:
        logger.error(f"Unexpected error in list_prompts: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve prompts',
            'message': 'An unexpected error occurred while loading prompts'
        }), 500


@prompts_bp.route('/prompts/<prompt_id>', methods=['GET'])
def get_prompt(prompt_id: str):
    """
    Retrieve specific prompt template by ID.
    
    Args:
        prompt_id: Unique identifier for the prompt template
    
    Returns:
        JSON response with prompt template or error information
    
    AI Context: HTTP adapter for single prompt retrieval. Delegates to service.
    """
    try:
        logger.debug(f"Prompt requested: {prompt_id}")
        
        # Apply compatibility mapping for legacy frontend support
        mapped_prompt_id = PROMPT_TYPE_MAPPING.get(prompt_id, prompt_id)
        
        # Delegate to service
        prompt_service = PromptManagementService()
        prompt_data = prompt_service.get_prompt_by_id(mapped_prompt_id)
        
        if not prompt_data:
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404
        
        # Format HTTP response
        response_data = {
            'success': True,
            'prompt': prompt_data,
            'message': f'Prompt {prompt_id} retrieved successfully'
        }
        
        logger.debug(f"Retrieved prompt: {prompt_id}")
        return jsonify(response_data), 200
        
    except PromptStorageError as e:
        logger.error(f"Prompt storage error in get_prompt: {e}")
        return create_error_response(e, 422)
    except Exception as e:
        logger.error(f"Unexpected error in get_prompt: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve prompt',
            'message': f'An unexpected error occurred while loading prompt {prompt_id}'
        }), 500


@prompts_bp.route('/prompts/<prompt_id>', methods=['POST', 'PUT'])
def save_prompt(prompt_id: str):
    """
    Save or update a prompt template.
    
    Args:
        prompt_id: Unique identifier for the prompt template
    
    Request Body:
        {
            "name": "Prompt Display Name",
            "description": "Description of prompt purpose",
            "template": "Template string with {variables}",
            "variables": ["variable1", "variable2"]
        }
    
    Returns:
        JSON response with save status or error information
    
    AI Context: HTTP adapter for prompt saving. All validation and business logic
    is handled by PromptManagementService.
    """
    try:
        # Parse and validate HTTP request
        request_data = prompt_schema.load(request.json or {})
        
        logger.info(f"Saving prompt: {prompt_id}")
        
        # Delegate to service
        prompt_service = PromptManagementService()
        success = prompt_service.save_prompt(prompt_id, request_data)
        
        if success:
            response_data = {
                'success': True,
                'message': f'Prompt {prompt_id} saved successfully'
            }
            return jsonify(response_data), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save prompt'
            }), 422
            
    except ValidationError as e:
        logger.warning(f"Validation error in save_prompt: {e.messages}")
        return jsonify({
            'success': False,
            'error': 'Request validation failed',
            'details': e.messages
        }), 400
    except PromptValidationError as e:
        logger.warning(f"Prompt validation error in save_prompt: {e}")
        return jsonify({
            'success': False,
            'error': 'Prompt validation failed',
            'details': str(e)
        }), 400
    except PromptStorageError as e:
        logger.error(f"Prompt storage error in save_prompt: {e}")
        return create_error_response(e, 422)
    except Exception as e:
        logger.error(f"Unexpected error in save_prompt: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to save prompt',
            'message': f'An unexpected error occurred while saving prompt {prompt_id}'
        }), 500


@prompts_bp.route('/prompts/<prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id: str):
    """
    Delete a prompt template.
    
    Args:
        prompt_id: Unique identifier for the prompt template
    
    Returns:
        JSON response with deletion status or error information
    
    AI Context: HTTP adapter for prompt deletion. Delegates to service.
    """
    try:
        logger.info(f"Deleting prompt: {prompt_id}")
        
        # Delegate to service
        prompt_service = PromptManagementService()
        success = prompt_service.delete_prompt(prompt_id)
        
        if success:
            response_data = {
                'success': True,
                'message': f'Prompt {prompt_id} deleted successfully'
            }
            return jsonify(response_data), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404
            
    except PromptValidationError as e:
        logger.warning(f"Validation error in delete_prompt: {e}")
        return jsonify({
            'success': False,
            'error': 'Cannot delete system prompt',
            'details': str(e)
        }), 400
    except PromptStorageError as e:
        logger.error(f"Prompt storage error in delete_prompt: {e}")
        return create_error_response(e, 422)
    except Exception as e:
        logger.error(f"Unexpected error in delete_prompt: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete prompt',
            'message': f'An unexpected error occurred while deleting prompt {prompt_id}'
        }), 500


@prompts_bp.route('/prompts/validate', methods=['POST'])
def validate_prompt():
    """
    Validate prompt template structure and variables.
    
    Request Body:
        {
            "template": "Template string with {variables}",
            "variables": ["variable1", "variable2"]
        }
    
    Returns:
        JSON response with validation results
    
    AI Context: HTTP adapter for prompt validation. Delegates to service.
    """
    try:
        # Parse and validate HTTP request
        request_data = validation_schema.load(request.json or {})
        
        logger.debug("Prompt validation requested")
        
        # Delegate to service
        prompt_service = PromptManagementService()
        validation_result = prompt_service.validate_prompt_template(
            template=request_data['template'],
            variables=request_data['variables']
        )
        
        # Format HTTP response
        response_data = {
            'success': True,
            'validation': validation_result,
            'message': 'Prompt validation completed'
        }
        
        return jsonify(response_data), 200
        
    except ValidationError as e:
        logger.warning(f"Request validation error in validate_prompt: {e.messages}")
        return jsonify({
            'success': False,
            'error': 'Request validation failed',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error in validate_prompt: {e}")
        return jsonify({
            'success': False,
            'error': 'Prompt validation failed',
            'message': f'An unexpected error occurred during validation: {str(e)}'
        }), 500


@prompts_bp.route('/prompts/preview', methods=['POST'])
def preview_prompt():
    """
    Generate preview of prompt with sample data.
    
    Request Body:
        {
            "template": "Template string with {variables}",
            "prompt_type": "contract_analysis",  // Optional, for sample data selection
            "sample_data": {                     // Optional, custom sample data
                "variable1": "value1",
                "variable2": "value2"
            }
        }
    
    Returns:
        JSON response with rendered prompt preview
    
    AI Context: HTTP adapter for prompt preview generation. Delegates to service.
    """
    try:
        # Parse and validate HTTP request
        request_data = preview_schema.load(request.json or {})
        
        logger.debug("Prompt preview requested")
        
        # Generate sample data if not provided
        sample_data = request_data.get('sample_data', {})
        if not sample_data:
            sample_data = _get_sample_data_for_type(request_data.get('prompt_type', ''))
        
        # Delegate to service
        prompt_service = PromptManagementService()
        preview_result = prompt_service.preview_prompt(
            template=request_data['template'],
            sample_data=sample_data
        )
        
        # Format HTTP response
        response_data = {
            'success': True,
            'preview': preview_result,
            'sample_data_used': sample_data,
            'message': 'Prompt preview generated successfully'
        }
        
        return jsonify(response_data), 200
        
    except ValidationError as e:
        logger.warning(f"Request validation error in preview_prompt: {e.messages}")
        return jsonify({
            'success': False,
            'error': 'Request validation failed',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error in preview_prompt: {e}")
        return jsonify({
            'success': False,
            'error': 'Prompt preview failed',
            'message': f'An unexpected error occurred during preview: {str(e)}'
        }), 500


@prompts_bp.route('/prompts/backups/<prompt_id>', methods=['GET'])
def get_prompt_backups(prompt_id: str):
    """
    Get backup list for a specific prompt.
    
    Args:
        prompt_id: Prompt identifier
        
    Returns:
        JSON response with backup list
    """
    try:
        logger.debug(f"Prompt backups requested for: {prompt_id}")
        
        # Apply compatibility mapping for legacy frontend support
        mapped_prompt_id = PROMPT_TYPE_MAPPING.get(prompt_id, prompt_id)
        
        # Delegate to service
        prompt_service = PromptManagementService()
        backups = prompt_service.list_prompt_backups(mapped_prompt_id)
        
        response_data = {
            'success': True,
            'backups': backups,
            'prompt_id': prompt_id,
            'message': f'Backups for {prompt_id} retrieved successfully'
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get_prompt_backups: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve backups',
            'backups': [],
            'message': f'An unexpected error occurred: {str(e)}'
        }), 500


@prompts_bp.route('/prompts/backup', methods=['POST'])
def create_backup():
    """
    Create backup of all current prompts.
    
    Request Body (Optional):
        {
            "backup_name": "custom_backup_name"
        }
    
    Returns:
        JSON response with backup creation status
    
    AI Context: HTTP adapter for prompt backup creation. Delegates to service.
    """
    try:
        request_data = request.get_json() or {}
        backup_name = request_data.get('backup_name')
        
        logger.info(f"Prompt backup requested: {backup_name or 'auto-generated name'}")
        
        # Delegate to service
        prompt_service = PromptManagementService()
        backup_path = prompt_service.create_backup(backup_name)
        
        # Format HTTP response
        response_data = {
            'success': True,
            'backup_path': backup_path,
            'message': 'Prompt backup created successfully'
        }
        
        return jsonify(response_data), 200
        
    except PromptStorageError as e:
        logger.error(f"Backup creation error: {e}")
        return create_error_response(e, 422)
    except Exception as e:
        logger.error(f"Unexpected error in create_backup: {e}")
        return jsonify({
            'success': False,
            'error': 'Backup creation failed',
            'message': f'An unexpected error occurred during backup: {str(e)}'
        }), 500


@prompts_bp.route('/prompts/stats', methods=['GET'])
def get_prompt_stats():
    """
    Get prompt statistics (alias for statistics endpoint).
    
    Returns:
        JSON response with prompt statistics
    """
    return get_prompt_statistics()


@prompts_bp.route('/prompts/statistics', methods=['GET'])
def get_prompt_statistics():
    """
    Get prompt usage and management statistics.
    
    Returns:
        JSON response with prompt statistics
    
    AI Context: HTTP adapter for prompt statistics. Delegates to service.
    """
    try:
        logger.debug("Prompt statistics requested")
        
        # Delegate to service
        prompt_service = PromptManagementService()
        stats = prompt_service.get_prompt_statistics()
        
        # Format HTTP response
        response_data = {
            'success': True,
            'statistics': stats,
            'message': 'Prompt statistics retrieved successfully'
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get_prompt_statistics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve statistics',
            'message': f'An unexpected error occurred: {str(e)}'
        }), 500


def _get_sample_data_for_type(prompt_type: str) -> dict:
    """
    Generate sample data for different prompt types.
    
    Args:
        prompt_type: Type of prompt for sample data generation
    
    Returns:
        dict: Sample data appropriate for the prompt type
    
    AI Context: Helper function that provides realistic sample data for prompt
    previews. Maps legacy frontend types to current prompt types.
    """
    # Map frontend types to backend types for compatibility
    mapped_type = PROMPT_TYPE_MAPPING.get(prompt_type, prompt_type)
    
    sample_data_map = {
        'contract_analysis': {
            'template_text': 'SAMPLE TEMPLATE: This is the original contract template with standard payment terms of 30 days, liability cap of $50,000, and standard termination clauses...',
            'contract_text': 'SAMPLE CONTRACT: This is the modified contract with updated payment terms of 45 days, increased liability cap of $100,000, and revised termination notice period...',
            'changes_summary': '''DETECTED CHANGES:
1. Payment terms changed from "30 days" to "45 days"
2. Liability cap increased from "$50,000" to "$100,000"
3. Termination notice period extended from "30 days" to "60 days"'''
        },
        'risk_assessment': {
            'critical_count': '2',
            'significant_count': '3',
            'inconsequential_count': '5',
            'changes_detail': '''Critical Changes:
1. Payment terms modification (30 → 45 days)
2. Liability cap increase ($50K → $100K)

Significant Changes:
1. Termination notice extension (30 → 60 days)
2. Service level agreement updates
3. Compliance requirement additions'''
        },
        'change_classification': {
            'original_text': 'Payment due within 30 days of invoice date',
            'modified_text': 'Payment due within 45 days of invoice date',
            'context': 'Payment terms section of service agreement'
        }
    }
    
    return sample_data_map.get(mapped_type, {
        'template_text': 'Sample template content',
        'contract_text': 'Sample contract content',
        'changes_summary': 'Sample changes detected'
    })


# Register error handlers for prompts blueprint
@prompts_bp.errorhandler(PromptStorageError)
def handle_prompt_storage_error(error):
    """Handle prompt storage errors."""
    return create_error_response(error, 422)


@prompts_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle request validation errors."""
    error_response = {
        'success': False,
        'error': 'Request validation failed',
        'details': error.messages
    }
    return jsonify(error_response), 400
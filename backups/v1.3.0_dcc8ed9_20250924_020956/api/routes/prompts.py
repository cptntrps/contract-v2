"""
Prompt management routes

Handles LLM prompt templates and configuration.
"""

import json
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app

from ...utils.security.audit import SecurityAuditor
from ...utils.logging.setup import get_logger

logger = get_logger(__name__)
prompts_bp = Blueprint('prompts', __name__)

# Initialize security auditor
security_auditor = SecurityAuditor()

# Frontend compatibility mapping
PROMPT_TYPE_MAPPING = {
    'individual_analysis': 'contract_analysis',
    'batch_analysis': 'contract_analysis', 
    'ultra_fast': 'change_classification'
}

# Default prompt templates
DEFAULT_PROMPTS = {
    'contract_analysis': {
        'name': 'Contract Analysis',
        'description': 'Main prompt for analyzing contract changes',
        'template': '''Analyze the following contract changes and classify each change as CRITICAL, SIGNIFICANT, or INCONSEQUENTIAL.

TEMPLATE (Original):
{template_text}

CONTRACT (Modified):
{contract_text}

DETECTED CHANGES:
{changes_summary}

For each change, provide:
1. Classification (CRITICAL/SIGNIFICANT/INCONSEQUENTIAL)
2. Brief explanation of the change's business impact
3. Risk assessment
4. Recommendation

Classification Guidelines:
- CRITICAL: Changes that alter key business terms (price, scope, liability, termination)
- SIGNIFICANT: Changes that modify important terms but don't affect core business
- INCONSEQUENTIAL: Minor wording changes, formatting, or placeholder replacements

Respond in JSON format:
{{
  "changes": [
    {{
      "change_number": 1,
      "classification": "CRITICAL|SIGNIFICANT|INCONSEQUENTIAL",
      "explanation": "Brief explanation",
      "risk_impact": "Risk description",
      "recommendation": "Recommended action"
    }}
  ]
}}''',
        'variables': ['template_text', 'contract_text', 'changes_summary']
    },
    'risk_assessment': {
        'name': 'Risk Assessment',
        'description': 'Prompt for overall contract risk evaluation',
        'template': '''Evaluate the overall risk level of this contract based on the detected changes.

CHANGES SUMMARY:
Critical Changes: {critical_count}
Significant Changes: {significant_count}
Inconsequential Changes: {inconsequential_count}

DETAILED CHANGES:
{changes_details}

Provide:
1. Overall risk level (HIGH/MEDIUM/LOW)
2. Risk explanation
3. Key concerns
4. Recommended actions

Risk Assessment Guidelines:
- HIGH: Any critical changes or numerous significant changes
- MEDIUM: Several significant changes requiring review
- LOW: Mostly inconsequential changes or placeholder updates

Respond in JSON format:
{{
  "risk_level": "HIGH|MEDIUM|LOW",
  "risk_explanation": "Detailed explanation",
  "key_concerns": ["concern1", "concern2"],
  "recommended_actions": ["action1", "action2"]
}}''',
        'variables': ['critical_count', 'significant_count', 'inconsequential_count', 'changes_details']
    },
    'change_classification': {
        'name': 'Change Classification',
        'description': 'Prompt for classifying individual changes',
        'template': '''Classify this specific contract change:

ORIGINAL TEXT: {original_text}
MODIFIED TEXT: {modified_text}
CONTEXT: {context}

Determine:
1. Change type (Addition, Deletion, Modification)
2. Classification level (CRITICAL, SIGNIFICANT, INCONSEQUENTIAL)
3. Business impact
4. Risk level

Classification Rules:
- CRITICAL: Price, dates, scope, liability, termination clauses
- SIGNIFICANT: Service levels, responsibilities, compliance requirements
- INCONSEQUENTIAL: Formatting, minor wording, placeholder content

Response format:
{{
  "change_type": "Addition|Deletion|Modification",
  "classification": "CRITICAL|SIGNIFICANT|INCONSEQUENTIAL",
  "business_impact": "Description of impact",
  "risk_level": "High|Medium|Low",
  "confidence": 0.85
}}''',
        'variables': ['original_text', 'modified_text', 'context']
    }
}


@prompts_bp.route('/prompts')
def list_prompts():
    """List all available prompt templates"""
    try:
        # Try to load prompts from file
        prompts_file = Path(current_app.config.get('PROMPTS_FILE', 'data/prompts/prompts.json'))
        
        if prompts_file.exists():
            try:
                with open(prompts_file, 'r') as f:
                    saved_prompts = json.load(f)
                    
                # Merge with defaults (saved prompts take precedence)
                all_prompts = DEFAULT_PROMPTS.copy()
                all_prompts.update(saved_prompts)
                
            except Exception as e:
                logger.warning(f"Failed to load saved prompts: {e}")
                all_prompts = DEFAULT_PROMPTS
        else:
            all_prompts = DEFAULT_PROMPTS
        
        # Prepare response (exclude template content from list view)
        prompts_list = []
        for prompt_id, prompt_data in all_prompts.items():
            try:
                prompts_list.append({
                    'id': prompt_id,
                    'name': prompt_data.get('name', prompt_id),
                    'description': prompt_data.get('description', 'No description available'),
                    'variables': prompt_data.get('variables', []),
                    'template_length': len(prompt_data.get('template', ''))
                })
            except Exception as e:
                logger.warning(f"Error processing prompt {prompt_id}: {e}")
                # Add a basic entry for problematic prompts
                prompts_list.append({
                    'id': prompt_id,
                    'name': prompt_id,
                    'description': 'Error loading prompt data',
                    'variables': [],
                    'template_length': 0
                })
        
        return jsonify({
            'success': True,
            'prompts': prompts_list,
            'total': len(prompts_list)
        })
        
    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list prompts'
        }), 500


@prompts_bp.route('/prompts/<prompt_type>')
def get_prompt(prompt_type):
    """Get specific prompt template with frontend mapping support"""
    try:
        # Map frontend prompt types to backend types
        actual_prompt_type = PROMPT_TYPE_MAPPING.get(prompt_type, prompt_type)
        
        # Try to load prompts from file
        prompts_file = Path(current_app.config.get('PROMPTS_FILE', 'data/prompts/prompts.json'))
        
        if prompts_file.exists():
            try:
                with open(prompts_file, 'r') as f:
                    saved_prompts = json.load(f)
                    
                # Merge with defaults
                all_prompts = DEFAULT_PROMPTS.copy()
                all_prompts.update(saved_prompts)
                
            except Exception as e:
                logger.warning(f"Failed to load saved prompts: {e}")
                all_prompts = DEFAULT_PROMPTS
        else:
            all_prompts = DEFAULT_PROMPTS
        
        # Get specific prompt using mapped type
        if actual_prompt_type not in all_prompts:
            return jsonify({
                'success': False,
                'error': f'Prompt template {prompt_type} not found'
            }), 404
        
        prompt_data = all_prompts[actual_prompt_type]
        
        return jsonify({
            'success': True,
            'template': prompt_data['template'],
            'version': '1.0',
            'status': 'Active'
        })
        
    except Exception as e:
        logger.error(f"Error retrieving prompt {prompt_type}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve prompt'
        }), 500


@prompts_bp.route('/prompts/<prompt_type>', methods=['PUT'])
def update_prompt(prompt_type):
    """Update a prompt template"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No request data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'description', 'template']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Load existing prompts
        prompts_file = Path(current_app.config.get('PROMPTS_FILE', 'data/prompts/prompts.json'))
        
        if prompts_file.exists():
            try:
                with open(prompts_file, 'r') as f:
                    saved_prompts = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load saved prompts: {e}")
                saved_prompts = {}
        else:
            saved_prompts = {}
        
        # Update prompt
        saved_prompts[prompt_type] = {
            'name': data['name'],
            'description': data['description'],
            'template': data['template'],
            'variables': data.get('variables', [])
        }
        
        # Ensure prompts directory exists
        prompts_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save updated prompts
        with open(prompts_file, 'w') as f:
            json.dump(saved_prompts, f, indent=2)
        
        # Log update
        security_auditor.log_security_event(
            event_type='prompt_updated',
            details={'prompt_type': prompt_type, 'name': data['name']},
            request=request
        )
        
        logger.info(f"Prompt template {prompt_type} updated")
        
        return jsonify({
            'success': True,
            'message': f'Prompt template {prompt_type} updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating prompt {prompt_type}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update prompt'
        }), 500


@prompts_bp.route('/prompts/<prompt_type>', methods=['DELETE'])
def delete_prompt(prompt_type):
    """Delete a prompt template (only custom ones, not defaults)"""
    try:
        # Check if it's a default prompt
        if prompt_type in DEFAULT_PROMPTS:
            return jsonify({
                'success': False,
                'error': 'Cannot delete default prompt templates'
            }), 400
        
        # Load existing prompts
        prompts_file = Path(current_app.config.get('PROMPTS_FILE', 'data/prompts/prompts.json'))
        
        if not prompts_file.exists():
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404
        
        try:
            with open(prompts_file, 'r') as f:
                saved_prompts = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load saved prompts: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to load prompts'
            }), 500
        
        # Check if prompt exists
        if prompt_type not in saved_prompts:
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404
        
        # Delete prompt
        prompt_name = saved_prompts[prompt_type].get('name', prompt_type)
        del saved_prompts[prompt_type]
        
        # Save updated prompts
        with open(prompts_file, 'w') as f:
            json.dump(saved_prompts, f, indent=2)
        
        # Log deletion
        security_auditor.log_security_event(
            event_type='prompt_deleted',
            details={'prompt_type': prompt_type, 'name': prompt_name},
            request=request
        )
        
        logger.info(f"Prompt template {prompt_type} deleted")
        
        return jsonify({
            'success': True,
            'message': f'Prompt template {prompt_type} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting prompt {prompt_type}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete prompt'
        }), 500


@prompts_bp.route('/prompts/render/<prompt_type>', methods=['POST'])
def render_prompt(prompt_type):
    """Render a prompt template with variables"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No request data provided'
            }), 400
        
        variables = data.get('variables', {})
        
        # Get prompt template
        prompts_file = Path(current_app.config.get('PROMPTS_FILE', 'data/prompts/prompts.json'))
        
        all_prompts = DEFAULT_PROMPTS.copy()
        if prompts_file.exists():
            try:
                with open(prompts_file, 'r') as f:
                    saved_prompts = json.load(f)
                    all_prompts.update(saved_prompts)
            except Exception as e:
                logger.warning(f"Failed to load saved prompts: {e}")
        
        if prompt_type not in all_prompts:
            return jsonify({
                'success': False,
                'error': f'Prompt template {prompt_type} not found'
            }), 404
        
        prompt_data = all_prompts[prompt_type]
        template = prompt_data['template']
        
        # Render template with variables
        try:
            rendered_prompt = template.format(**variables)
        except KeyError as e:
            return jsonify({
                'success': False,
                'error': f'Missing variable: {str(e)}'
            }), 400
        
        return jsonify({
            'success': True,
            'prompt_type': prompt_type,
            'rendered_prompt': rendered_prompt,
            'variables_used': variables
        })
        
    except Exception as e:
        logger.error(f"Error rendering prompt {prompt_type}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to render prompt'
        }), 500


# Frontend compatibility routes


@prompts_bp.route('/prompts/stats')
def get_prompt_stats():
    """Get prompt management statistics"""
    try:
        # Load prompts
        prompts_file = Path(current_app.config.get('PROMPTS_FILE', 'data/prompts/prompts.json'))
        
        all_prompts = DEFAULT_PROMPTS.copy()
        if prompts_file.exists():
            try:
                with open(prompts_file, 'r') as f:
                    saved_prompts = json.load(f)
                    all_prompts.update(saved_prompts)
            except Exception:
                pass
        
        # Count backups
        backups_dir = Path(current_app.config.get('PROMPTS_BACKUPS_DIR', 'data/prompts/backups'))
        backup_count = 0
        if backups_dir.exists():
            backup_count = len(list(backups_dir.glob('*.json')))
        
        # Get last modified time
        last_modified = None
        if prompts_file.exists():
            last_modified = prompts_file.stat().st_mtime
        
        return jsonify({
            'success': True,
            'total_prompts': len(all_prompts),
            'active_prompts': len([p for p in all_prompts.values() if len(p.get('template', '')) > 0]),
            'total_backups': backup_count,
            'last_modified': last_modified
        })
        
    except Exception as e:
        logger.error(f"Error getting prompt stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get prompt statistics'
        }), 500


@prompts_bp.route('/prompts/backups/<prompt_type>')
def get_prompt_backups(prompt_type):
    """Get available backups for a prompt type"""
    try:
        backups_dir = Path(current_app.config.get('PROMPTS_BACKUPS_DIR', 'data/prompts/backups'))
        
        if not backups_dir.exists():
            return jsonify({
                'success': True,
                'backups': []
            })
        
        backups = []
        backup_files = list(backups_dir.glob('*.json'))
        
        for backup_file in backup_files:
            try:
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
                    
                # Check if this backup contains the requested prompt type
                if prompt_type in backup_data.get('prompts', {}):
                    backups.append({
                        'id': backup_file.stem,
                        'name': backup_data.get('name', backup_file.stem),
                        'created_at': backup_file.stat().st_ctime,
                        'prompt_types': list(backup_data.get('prompts', {}).keys())
                    })
            except Exception as e:
                logger.warning(f"Failed to read backup {backup_file}: {e}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'backups': backups
        })
        
    except Exception as e:
        logger.error(f"Error getting prompt backups: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get prompt backups'
        }), 500


@prompts_bp.route('/prompts/validate', methods=['POST'])
def validate_prompt():
    """Validate a prompt template"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No request data provided'
            }), 400
        
        template = data.get('template', '')
        prompt_type = data.get('prompt_type', '')
        
        if not template:
            return jsonify({
                'valid': False,
                'message': 'Template cannot be empty'
            })
        
        # Basic validation
        suggestions = []
        
        # Check for required variables based on prompt type
        required_vars = {
            'individual_analysis': ['template_text', 'contract_text'],
            'batch_analysis': ['template_text', 'contract_text'],
            'ultra_fast': ['original_text', 'modified_text']
        }
        
        mapped_type = PROMPT_TYPE_MAPPING.get(prompt_type, prompt_type)
        if mapped_type in ['contract_analysis']:
            expected_vars = ['template_text', 'contract_text', 'changes_summary']
        elif mapped_type in ['change_classification']:
            expected_vars = ['original_text', 'modified_text', 'context']
        else:
            expected_vars = []
        
        missing_vars = []
        for var in expected_vars:
            if f'{{{var}}}' not in template:
                missing_vars.append(var)
        
        if missing_vars:
            suggestions.append(f"Consider adding variables: {', '.join(missing_vars)}")
        
        # Check template length
        if len(template) < 50:
            suggestions.append("Template seems very short. Consider adding more detailed instructions.")
        
        return jsonify({
            'valid': len(missing_vars) == 0,
            'message': 'Template is valid' if len(missing_vars) == 0 else f'Missing required variables: {", ".join(missing_vars)}',
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Error validating prompt: {e}")
        return jsonify({
            'valid': False,
            'message': 'Failed to validate prompt'
        }), 500


@prompts_bp.route('/prompts/preview', methods=['POST'])
def preview_prompt():
    """Preview a prompt with sample data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No request data provided'
            }), 400
        
        template = data.get('template', '')
        prompt_type = data.get('prompt_type', '')
        
        if not template:
            return jsonify({
                'success': False,
                'error': 'Template cannot be empty'
            })
        
        # Sample data for different prompt types
        sample_data = {
            'individual_analysis': {
                'template_text': 'SAMPLE TEMPLATE: This is the original contract template with standard terms...',
                'contract_text': 'SAMPLE CONTRACT: This is the modified contract with some changes...',
                'changes_summary': 'DETECTED CHANGES:\n1. Changed payment terms from 30 to 45 days\n2. Added liability cap of $100,000'
            },
            'batch_analysis': {
                'template_text': 'SAMPLE TEMPLATE: Standard contract template...',
                'contract_text': 'SAMPLE CONTRACT: Modified contract version...',
                'changes_summary': 'BATCH CHANGES: Multiple changes detected across contracts...'
            },
            'ultra_fast': {
                'original_text': 'Payment due within 30 days',
                'modified_text': 'Payment due within 45 days',
                'context': 'Payment terms section'
            }
        }
        
        # Get appropriate sample data
        sample_vars = sample_data.get(prompt_type, sample_data['individual_analysis'])
        
        try:
            preview_text = template.format(**sample_vars)
        except KeyError as e:
            return jsonify({
                'success': False,
                'error': f'Missing variable in template: {str(e)}'
            })
        
        return jsonify({
            'success': True,
            'preview_text': preview_text
        })
        
    except Exception as e:
        logger.error(f"Error generating prompt preview: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate preview'
        }), 500



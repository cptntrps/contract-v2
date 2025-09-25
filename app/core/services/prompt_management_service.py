"""
Prompt Management Service - Domain Layer

Handles LLM prompt templates, configuration, and management operations.
Following architectural standards: single responsibility, comprehensive documentation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)


class PromptManagementService:
    """
    Manages LLM prompt templates and their lifecycle operations.
    
    Purpose: Centralizes all prompt template management including CRUD operations,
    validation, versioning, backup/restore, and template compilation. Separates
    prompt business logic from HTTP routing concerns.
    
    AI Context: This service handles all prompt-related business logic. When debugging
    prompt issues, start here. The service manages template storage, validation,
    and variable substitution. All prompt operations flow through this service.
    """
    
    def __init__(self, prompts_file_path: Optional[str] = None):
        """
        Initialize prompt management service.
        
        Args:
            prompts_file_path: Optional path to prompts storage file.
                             If None, uses Flask config or defaults to 'data/prompts/prompts.json'
        """
        self._prompts_file_path = prompts_file_path
        self._prompt_cache = {}
        self._cache_timestamp = None
        
    def list_all_prompts(self) -> Dict[str, Any]:
        """
        Retrieve all available prompt templates with metadata.
        
        Purpose: Provides complete inventory of prompt templates including both
        default system prompts and user-saved customizations. Merges defaults
        with saved prompts (saved take precedence).
        
        Returns:
            Dict[str, Any]: Dictionary mapping prompt IDs to prompt definitions containing:
                - name: Human-readable prompt name
                - description: Purpose and usage description
                - template: Template string with variable placeholders
                - variables: List of required variable names
                - metadata: Creation/modification timestamps, version info
        
        Raises:
            PromptStorageError: If prompt file exists but cannot be read
            
        AI Context: Primary prompt retrieval function. Returns merged view of
        default and custom prompts. If prompts not loading correctly, check
        file permissions and JSON format validation.
        """
        try:
            logger.debug("Loading all prompt templates")
            
            # Start with default prompts
            all_prompts = self._get_default_prompts().copy()
            
            # Load and merge saved prompts
            saved_prompts = self._load_saved_prompts()
            if saved_prompts:
                all_prompts.update(saved_prompts)
                logger.debug(f"Merged {len(saved_prompts)} saved prompts with {len(self._get_default_prompts())} defaults")
            
            # Add metadata to all prompts
            for prompt_id, prompt_data in all_prompts.items():
                if 'metadata' not in prompt_data:
                    prompt_data['metadata'] = {
                        'created_at': datetime.now().isoformat(),
                        'version': '1.0',
                        'source': 'system' if prompt_id in self._get_default_prompts() else 'custom'
                    }
            
            logger.info(f"Loaded {len(all_prompts)} total prompt templates")
            return all_prompts
            
        except Exception as e:
            logger.error(f"Failed to load prompt templates: {e}")
            raise PromptStorageError(f"Prompt loading failed: {str(e)}")
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific prompt template by ID.
        
        Args:
            prompt_id: Unique identifier for the prompt template
        
        Returns:
            Optional[Dict[str, Any]]: Prompt definition or None if not found
        
        Raises:
            PromptStorageError: If prompt storage access fails
        """
        try:
            all_prompts = self.list_all_prompts()
            return all_prompts.get(prompt_id)
        except PromptStorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve prompt {prompt_id}: {e}")
            raise PromptStorageError(f"Prompt retrieval failed: {str(e)}")
    
    def save_prompt(self, prompt_id: str, prompt_data: Dict[str, Any]) -> bool:
        """
        Save or update a prompt template.
        
        Purpose: Persists prompt templates to storage with validation and
        automatic backup of existing data. Handles both new prompt creation
        and updates to existing templates.
        
        Args:
            prompt_id: Unique identifier for the prompt
            prompt_data: Prompt definition containing:
                - name: Display name for the prompt
                - description: Usage description
                - template: Template string with variables
                - variables: List of required variable names
        
        Returns:
            bool: True if save successful, False otherwise
        
        Raises:
            ValidationError: If prompt data validation fails
            PromptStorageError: If storage operation fails
            
        AI Context: Primary prompt persistence function. Validates prompt structure
        and variable consistency before saving. Creates backup of existing data.
        """
        try:
            logger.info(f"Saving prompt template: {prompt_id}")
            
            # Validate prompt data structure
            self._validate_prompt_data(prompt_data)
            
            # Load existing prompts
            existing_prompts = self._load_saved_prompts() or {}
            
            # Create backup if prompt exists
            if prompt_id in existing_prompts:
                self._create_prompt_backup(prompt_id, existing_prompts[prompt_id])
            
            # Add metadata
            prompt_data['metadata'] = {
                'created_at': existing_prompts.get(prompt_id, {}).get('metadata', {}).get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat(),
                'version': self._increment_version(existing_prompts.get(prompt_id, {})),
                'source': 'custom'
            }
            
            # Update prompts collection
            existing_prompts[prompt_id] = prompt_data
            
            # Save to storage
            self._save_prompts_to_file(existing_prompts)
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info(f"Prompt template saved successfully: {prompt_id}")
            return True
            
        except (ValidationError, PromptStorageError):
            raise
        except Exception as e:
            logger.error(f"Failed to save prompt {prompt_id}: {e}")
            raise PromptStorageError(f"Prompt save failed: {str(e)}")
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """
        Delete a prompt template.
        
        Args:
            prompt_id: Unique identifier for the prompt to delete
        
        Returns:
            bool: True if deletion successful, False if prompt not found
        
        Raises:
            PromptStorageError: If storage operation fails
        """
        try:
            logger.info(f"Deleting prompt template: {prompt_id}")
            
            # Cannot delete default prompts
            if prompt_id in self._get_default_prompts():
                raise ValidationError(f"Cannot delete system default prompt: {prompt_id}")
            
            # Load existing prompts
            existing_prompts = self._load_saved_prompts() or {}
            
            if prompt_id not in existing_prompts:
                logger.warning(f"Prompt not found for deletion: {prompt_id}")
                return False
            
            # Create backup before deletion
            self._create_prompt_backup(prompt_id, existing_prompts[prompt_id])
            
            # Remove from collection
            del existing_prompts[prompt_id]
            
            # Save updated collection
            self._save_prompts_to_file(existing_prompts)
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info(f"Prompt template deleted successfully: {prompt_id}")
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete prompt {prompt_id}: {e}")
            raise PromptStorageError(f"Prompt deletion failed: {str(e)}")
    
    def validate_prompt_template(self, template: str, variables: List[str]) -> Dict[str, Any]:
        """
        Validate prompt template structure and variable consistency.
        
        Purpose: Ensures prompt templates are syntactically correct and all
        required variables are properly defined. Catches template errors
        before deployment to prevent analysis failures.
        
        Args:
            template: Template string with variable placeholders
            variables: List of expected variable names
        
        Returns:
            Dict[str, Any]: Validation results containing:
                - valid: Boolean indicating if template is valid
                - errors: List of validation error messages
                - warnings: List of potential issues
                - variables_found: List of variables detected in template
                - missing_variables: Variables declared but not used in template
                - undefined_variables: Variables used in template but not declared
        
        AI Context: Critical validation function that prevents malformed prompts
        from breaking analysis workflows. Use this to debug template syntax issues.
        """
        try:
            logger.debug(f"Validating prompt template with {len(variables)} declared variables")
            
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'variables_found': [],
                'missing_variables': [],
                'undefined_variables': []
            }
            
            if not template or not template.strip():
                validation_result['valid'] = False
                validation_result['errors'].append("Template cannot be empty")
                return validation_result
            
            # Find all variables in template
            import re
            variable_pattern = r'\{([^}]+)\}'
            template_variables = set(re.findall(variable_pattern, template))
            validation_result['variables_found'] = list(template_variables)
            
            # Check for undefined variables (in template but not declared)
            declared_variables = set(variables or [])
            undefined_vars = template_variables - declared_variables
            if undefined_vars:
                validation_result['undefined_variables'] = list(undefined_vars)
                validation_result['warnings'].append(f"Undefined variables found: {', '.join(undefined_vars)}")
            
            # Check for missing variables (declared but not used)
            missing_vars = declared_variables - template_variables
            if missing_vars:
                validation_result['missing_variables'] = list(missing_vars)
                validation_result['warnings'].append(f"Declared variables not used: {', '.join(missing_vars)}")
            
            # Additional syntax checks
            if template.count('{') != template.count('}'):
                validation_result['valid'] = False
                validation_result['errors'].append("Mismatched braces in template")
            
            # Check for nested braces (not supported)
            if '{{' in template or '}}' in template:
                validation_result['warnings'].append("Double braces detected - ensure this is intentional for JSON output")
            
            logger.debug(f"Template validation completed: valid={validation_result['valid']}, {len(validation_result['errors'])} errors")
            return validation_result
            
        except Exception as e:
            logger.error(f"Template validation failed: {e}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'variables_found': [],
                'missing_variables': [],
                'undefined_variables': []
            }
    
    def preview_prompt(self, template: str, sample_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate preview of prompt with sample data substitution.
        
        Purpose: Shows how prompt template will appear when rendered with actual
        data. Helps users verify template formatting and variable placement.
        
        Args:
            template: Template string with variable placeholders
            sample_data: Dictionary of sample values for variable substitution
        
        Returns:
            Dict[str, Any]: Preview results containing:
                - rendered_prompt: Template with variables substituted
                - substitutions_made: List of successful variable substitutions
                - missing_data: Variables that couldn't be substituted
                - preview_truncated: Boolean if output was truncated for display
        
        AI Context: Use this function to debug template rendering issues.
        Shows exact output that will be sent to LLM for analysis.
        """
        try:
            logger.debug(f"Generating prompt preview with {len(sample_data)} data values")
            
            preview_result = {
                'rendered_prompt': template,
                'substitutions_made': [],
                'missing_data': [],
                'preview_truncated': False
            }
            
            if not template:
                preview_result['rendered_prompt'] = "Empty template"
                return preview_result
            
            # Perform variable substitution
            rendered = template
            import re
            variable_pattern = r'\{([^}]+)\}'
            
            for match in re.finditer(variable_pattern, template):
                variable_name = match.group(1)
                placeholder = match.group(0)  # Full {variable} string
                
                if variable_name in sample_data:
                    replacement_value = str(sample_data[variable_name])
                    rendered = rendered.replace(placeholder, replacement_value)
                    preview_result['substitutions_made'].append(variable_name)
                else:
                    preview_result['missing_data'].append(variable_name)
            
            # Truncate if too long for preview
            max_preview_length = 2000
            if len(rendered) > max_preview_length:
                rendered = rendered[:max_preview_length] + "\n\n[Preview truncated...]"
                preview_result['preview_truncated'] = True
            
            preview_result['rendered_prompt'] = rendered
            
            logger.debug(f"Prompt preview generated: {len(preview_result['substitutions_made'])} substitutions, {len(preview_result['missing_data'])} missing")
            return preview_result
            
        except Exception as e:
            logger.error(f"Prompt preview generation failed: {e}")
            return {
                'rendered_prompt': f"Preview error: {str(e)}",
                'substitutions_made': [],
                'missing_data': [],
                'preview_truncated': False
            }
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create backup of all current prompts.
        
        Args:
            backup_name: Optional name for the backup. If None, uses timestamp
        
        Returns:
            str: Path to created backup file
        
        Raises:
            PromptStorageError: If backup creation fails
        """
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"prompts_backup_{timestamp}"
            
            logger.info(f"Creating prompt backup: {backup_name}")
            
            # Get current prompts
            all_prompts = self.list_all_prompts()
            
            # Create backup directory
            backup_dir = Path(current_app.config.get('BACKUPS_FOLDER', 'data/backups'))
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Save backup
            backup_path = backup_dir / f"{backup_name}.json"
            with open(backup_path, 'w') as f:
                json.dump(all_prompts, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Prompt backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise PromptStorageError(f"Backup creation failed: {str(e)}")
    
    def get_prompt_statistics(self) -> Dict[str, Any]:
        """
        Generate statistics about prompt templates.
        
        Returns:
            Dict[str, Any]: Statistics including total counts, types, usage metrics
        """
        try:
            all_prompts = self.list_all_prompts()
            
            default_prompts = self._get_default_prompts()
            custom_count = len(all_prompts) - len(default_prompts)
            
            stats = {
                'total_prompts': len(all_prompts),
                'default_prompts': len(default_prompts),
                'custom_prompts': custom_count,
                'prompt_types': list(all_prompts.keys()),
                'last_updated': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to generate prompt statistics: {e}")
            return {'error': str(e)}
    
    def _get_default_prompts(self) -> Dict[str, Any]:
        """Get default system prompt templates."""
        return {
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

CHANGE DETAILS:
{changes_detail}

Provide overall risk assessment with:
1. Overall risk level (LOW/MEDIUM/HIGH)
2. Key risk factors
3. Recommendations for review
4. Approval workflow suggestion

Response format:
{{
  "overall_risk": "LOW|MEDIUM|HIGH",
  "risk_factors": ["factor1", "factor2"],
  "recommendations": ["recommendation1", "recommendation2"],
  "approval_workflow": "Standard|Enhanced|Executive"
}}''',
                'variables': ['critical_count', 'significant_count', 'inconsequential_count', 'changes_detail']
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
    
    def _get_prompts_file_path(self) -> Path:
        """Get path to prompts storage file."""
        if self._prompts_file_path:
            return Path(self._prompts_file_path)
        else:
            return Path(current_app.config.get('PROMPTS_FILE', 'data/prompts/prompts.json'))
    
    def _load_saved_prompts(self) -> Optional[Dict[str, Any]]:
        """Load saved prompts from file storage."""
        try:
            prompts_file = self._get_prompts_file_path()
            
            if not prompts_file.exists():
                return None
            
            with open(prompts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in prompts file: {e}")
            raise PromptStorageError(f"Prompts file contains invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load saved prompts: {e}")
            return None
    
    def _save_prompts_to_file(self, prompts: Dict[str, Any]) -> None:
        """Save prompts to file storage."""
        prompts_file = self._get_prompts_file_path()
        
        # Ensure directory exists
        prompts_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(prompts_file, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
    
    def _validate_prompt_data(self, prompt_data: Dict[str, Any]) -> None:
        """Validate prompt data structure."""
        required_fields = ['name', 'description', 'template']
        
        for field in required_fields:
            if field not in prompt_data:
                raise ValidationError(f"Missing required field: {field}")
            if not prompt_data[field] or not str(prompt_data[field]).strip():
                raise ValidationError(f"Field cannot be empty: {field}")
        
        # Validate variables field if present
        if 'variables' in prompt_data:
            variables = prompt_data['variables']
            if not isinstance(variables, list):
                raise ValidationError("Variables field must be a list")
    
    def _create_prompt_backup(self, prompt_id: str, prompt_data: Dict[str, Any]) -> None:
        """Create backup of individual prompt before modification."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{prompt_id}_backup_{timestamp}"
            
            backup_dir = Path(current_app.config.get('BACKUPS_FOLDER', 'data/backups'))
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_path = backup_dir / f"{backup_name}.json"
            with open(backup_path, 'w') as f:
                json.dump({prompt_id: prompt_data}, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Individual prompt backup created: {backup_path}")
            
        except Exception as e:
            logger.warning(f"Failed to create individual prompt backup: {e}")
            # Don't raise - backup failure shouldn't prevent main operation
    
    def list_prompt_backups(self, prompt_id: str) -> List[Dict[str, Any]]:
        """
        List available backups for a specific prompt.
        
        Args:
            prompt_id: Prompt identifier to find backups for
            
        Returns:
            List of backup information dictionaries
            
        AI Context: Lists available backup files for a specific prompt.
        Returns empty list if no backups found rather than raising errors.
        """
        try:
            backups = []
            backup_dir = Path(current_app.config.get('BACKUPS_FOLDER', 'data/backups'))
            
            if not backup_dir.exists():
                return backups
            
            # Find backup files matching the prompt_id pattern
            pattern = f"{prompt_id}_backup_*.json"
            for backup_file in backup_dir.glob(pattern):
                try:
                    stat = backup_file.stat()
                    backups.append({
                        'name': backup_file.stem,
                        'filename': backup_file.name,
                        'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'size': stat.st_size
                    })
                except Exception as e:
                    logger.warning(f"Error reading backup file {backup_file}: {e}")
                    continue
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            logger.debug(f"Found {len(backups)} backups for prompt {prompt_id}")
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups for prompt {prompt_id}: {e}")
            return []
    
    def _increment_version(self, existing_prompt: Dict[str, Any]) -> str:
        """Increment version number for prompt update."""
        if not existing_prompt or 'metadata' not in existing_prompt:
            return '1.0'
        
        current_version = existing_prompt['metadata'].get('version', '1.0')
        try:
            major, minor = map(int, current_version.split('.'))
            return f"{major}.{minor + 1}"
        except (ValueError, AttributeError):
            return '1.0'
    
    def _invalidate_cache(self) -> None:
        """Invalidate internal prompt cache."""
        self._prompt_cache.clear()
        self._cache_timestamp = None


class PromptStorageError(Exception):
    """Exception raised when prompt storage operations fail."""
    pass


class ValidationError(Exception):
    """Exception raised when prompt validation fails."""
    pass
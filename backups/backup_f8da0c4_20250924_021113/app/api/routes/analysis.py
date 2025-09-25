"""
Contract analysis routes

Handles contract analysis operations and results.
"""

import os
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app

from ...core.services.analyzer import create_contract_analyzer, ContractAnalysisError
from ...core.models.contract import Contract
from ...utils.security.audit import SecurityAuditor
from ...utils.logging.setup import get_logger

# Import contracts store from contracts routes
from .contracts import contracts_store

logger = get_logger(__name__)
analysis_bp = Blueprint('analysis', __name__)

# Initialize security auditor
security_auditor = SecurityAuditor()

# Store analysis results (in production, use database)
analysis_results_store = {}


def find_best_template(contract):
    """
    Find the best matching template based on intelligent matching rules:
    1. Vendor-specific: Capgemini, Blue Optima, EPAM
    2. Document type: SOW vs Change Order
    3. Similarity-based: Best match across all templates
    """
    from pathlib import Path
    from flask import current_app
    from ...core.services.document_processor import DocumentProcessor
    
    templates_dir = Path(current_app.config.get('TEMPLATES_FOLDER', 'data/templates'))
    template_files = list(templates_dir.glob('*.docx'))
    
    if not template_files:
        return None
    
    # Read contract content
    doc_processor = DocumentProcessor()
    try:
        contract_content = doc_processor.extract_text_from_docx(contract.file_path)
        contract_content_lower = contract_content.lower()
    except Exception as e:
        logger.error(f"Error reading contract content: {e}")
        return str(template_files[0])  # Fallback to first template
    
    # Rule 1: Vendor-specific matching
    vendor_templates = {
        'capgemini': 'VENDOR_CAPGEMINI_SOW_v1.docx',
        'blue optima': 'VENDOR_BLUEOPTIMA_SOW_v1.docx',
        'blueoptima': 'VENDOR_BLUEOPTIMA_SOW_v1.docx',
        'epam': 'VENDOR_EPAM_SOW_v1.docx'
    }
    
    for vendor, template_name in vendor_templates.items():
        if vendor in contract_content_lower:
            template_path = templates_dir / template_name
            if template_path.exists():
                logger.info(f"Selected vendor template: {template_name} (found '{vendor}' in contract)")
                return str(template_path)
    
    # Rule 2: Document type matching
    sow_keywords = ['statement of work', 'sow', 'scope of work', 'work statement', 'services agreement']
    co_keywords = ['change order', 'change request', 'amendment', 'modification', 'addendum']
    
    sow_count = sum(1 for keyword in sow_keywords if keyword in contract_content_lower)
    co_count = sum(1 for keyword in co_keywords if keyword in contract_content_lower)
    
    if sow_count > co_count and sow_count > 0:
        # Prefer SOW template
        sow_template = templates_dir / 'TYPE_SOW_Standard_v1.docx'
        if sow_template.exists():
            logger.info(f"Selected SOW template: found {sow_count} SOW keywords")
            return str(sow_template)
    elif co_count > 0:
        # Prefer Change Order template
        co_template = templates_dir / 'TYPE_CHANGEORDER_Standard_v1.docx'
        if co_template.exists():
            logger.info(f"Selected Change Order template: found {co_count} CO keywords")
            return str(co_template)
    
    # Rule 3: Similarity-based matching against all templates
    logger.info("No specific vendor/type match found, using similarity-based matching")
    
    from ...core.services.comparison_engine import ComparisonEngine
    comparison_engine = ComparisonEngine()
    
    best_template = None
    best_similarity = 0.0
    
    for template_file in template_files:
        try:
            template_content = doc_processor.extract_text_from_docx(str(template_file))
            similarity = comparison_engine.calculate_similarity(contract_content, template_content)
            
            logger.debug(f"Template {template_file.name}: similarity = {similarity:.3f}")
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_template = str(template_file)
                
        except Exception as e:
            logger.warning(f"Error processing template {template_file}: {e}")
            continue
    
    if best_template:
        logger.info(f"Selected best matching template: {Path(best_template).name} (similarity: {best_similarity:.3f})")
        return best_template
    
    # Fallback to first available template
    logger.warning("No suitable template found, using first available template")
    return str(template_files[0])


@analysis_bp.route('/analysis')
def list_analysis_results():
    """List all analysis results"""
    try:
        results_list = []
        
        for analysis_result in analysis_results_store.values():
            results_list.append(analysis_result.get_summary())
        
        # Sort by analysis date (newest first)
        results_list.sort(key=lambda x: x['analysis_date'], reverse=True)
        
        return jsonify({
            'success': True,
            'analysis_results': results_list,
            'total': len(results_list)
        })
        
    except Exception as e:
        logger.error(f"Error listing analysis results: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list analysis results'
        }), 500


@analysis_bp.route('/analysis-results')
def analysis_results():
    """Get analysis results in frontend-compatible format"""
    try:
        # Convert analysis results to frontend-expected format
        results = []
        for analysis_id, result in analysis_results_store.items():
            # Handle different result formats
            if hasattr(result, 'get_summary'):
                # If it's a domain object with get_summary method
                summary = result.get_summary()
                results.append({
                    'id': analysis_id,
                    'contract': summary.get('contract_name', 'Unknown'),
                    'template': summary.get('template_name', 'Unknown'),
                    'date': summary.get('analysis_timestamp', ''),
                    'status': summary.get('status', 'completed'),
                    'changes': summary.get('total_changes', 0),
                    'similarity': summary.get('similarity_score', 0) * 100,
                    'analysis': summary.get('analysis_results', [])
                })
            else:
                # If it's a dictionary (legacy format)
                results.append({
                    'id': analysis_id,
                    'contract': result.get('contract_name', result.get('contract', 'Unknown')),
                    'template': result.get('template_name', result.get('template', 'Unknown')),
                    'date': result.get('analysis_timestamp', result.get('date', '')),
                    'status': result.get('status', 'completed'),
                    'changes': result.get('total_changes', result.get('changes', 0)),
                    'similarity': result.get('similarity_score', result.get('similarity', 0)) * 100 if result.get('similarity_score', result.get('similarity', 0)) <= 1 else result.get('similarity_score', result.get('similarity', 0)),
                    'analysis': result.get('analysis_results', result.get('analysis', []))
                })
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Error in analysis results endpoint: {e}")
        return jsonify([]), 200  # Return empty array on error


@analysis_bp.route('/analyze-contract', methods=['POST'])
def analyze_contract():
    """Analyze a contract against the best matching template"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No request data provided'
            }), 400
        
        contract_id = data.get('contract_id')
        if not contract_id:
            return jsonify({
                'success': False,
                'error': 'Contract ID is required'
            }), 400
        
        # Validate contract ID format to prevent injection attacks
        if not contract_id.replace('_', '').isalnum() or len(contract_id) > 50:
            return jsonify({
                'success': False,
                'error': 'Invalid contract ID format'
            }), 400
        
        # Check if contract exists
        if contract_id not in contracts_store:
            return jsonify({
                'success': False,
                'error': 'Contract not found'
            }), 404
        
        # Get contract
        contract = contracts_store[contract_id]
        
        logger.info(f"Starting contract analysis for: {contract_id}")
        
        # Import required modules for analysis
        from pathlib import Path
        import uuid
        from datetime import datetime
        
        # Initialize analyzer with configuration
        config = {
            'llm_settings': {
                'provider': 'openai',
                'model': 'gpt-4o',
                'temperature': 0.1,
                'max_tokens': 2048
            },
            'analysis_settings': {
                'include_llm_analysis': True,
                'batch_size': 10,
                'similarity_threshold': 0.7
            }
        }
        
        analyzer = create_contract_analyzer(config)
        
        # Find the best matching template using intelligent matching
        template_path = find_best_template(contract)
        
        if not template_path:
            return jsonify({
                'success': False,
                'error': 'No suitable template found'
            }), 404
        
        # Mark contract as processing
        contract.mark_processing()
        
        # Perform the actual analysis
        analysis_result = analyzer.analyze_contract(
            contract=contract,
            template_path=template_path,
            include_llm_analysis=True
        )
        
        # Get template name from path
        template_name = Path(template_path).name
        
        # Mark contract as analyzed
        contract.mark_analyzed(
            template_used=template_name,
            changes_count=analysis_result.total_changes,
            similarity_score=analysis_result.similarity_score,
            risk_level=analysis_result.overall_risk_level
        )
        
        # Convert to frontend-compatible format
        frontend_result = {
            'id': analysis_result.analysis_id,
            'contract': contract.get_display_name(),
            'template': template_name,
            'status': f'Changes - {analysis_result.overall_risk_level}',
            'changes': analysis_result.total_changes,
            'similarity': round(analysis_result.similarity_score * 100, 1),
            'date': datetime.now().isoformat(),
            'analysis': [
                {
                    'explanation': change.explanation,
                    'classification': change.classification.value if hasattr(change.classification, 'value') else str(change.classification),
                    'deleted_text': change.deleted_text,
                    'inserted_text': change.inserted_text
                }
                for change in analysis_result.changes
            ]
        }
        
        # Store the analysis result
        analysis_results_store[analysis_result.analysis_id] = frontend_result
        
        logger.info(f"Contract analysis completed for {contract_id}: {analysis_result.total_changes} changes, {analysis_result.overall_risk_level} risk")
        
        return jsonify({
            'success': True,
            'result': frontend_result,
            'message': 'Contract analyzed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in analyze contract endpoint: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to analyze contract: {str(e)}'
        }), 500


@analysis_bp.route('/analysis/start', methods=['POST'])
def start_analysis():
    """Start contract analysis"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No request data provided'
            }), 400
        
        contract_id = data.get('contract_id')
        template_filename = data.get('template')
        include_llm = data.get('include_llm_analysis', True)
        
        # Validate required fields
        if not contract_id:
            return jsonify({
                'success': False,
                'error': 'Contract ID is required'
            }), 400
        
        # Validate contract ID format to prevent injection attacks
        if not contract_id.replace('_', '').isalnum() or len(contract_id) > 50:
            return jsonify({
                'success': False,
                'error': 'Invalid contract ID format'
            }), 400
        
        if not template_filename:
            return jsonify({
                'success': False,
                'error': 'Template filename is required'
            }), 400
        
        # Get contract
        if contract_id not in contracts_store:
            return jsonify({
                'success': False,
                'error': 'Contract not found'
            }), 404
        
        contract = contracts_store[contract_id]
        
        # Validate contract file exists
        if not Path(contract.file_path).exists():
            return jsonify({
                'success': False,
                'error': 'Contract file not found on disk'
            }), 404
        
        # Find template file
        templates_dir = Path(current_app.config.get('TEMPLATES_FOLDER', 'data/templates'))
        
        # Validate template filename to prevent path traversal
        if not template_filename or '/' in template_filename or '\\' in template_filename or '..' in template_filename:
            return jsonify({
                'success': False,
                'error': 'Invalid template filename'
            }), 400
        
        template_path = templates_dir / template_filename
        
        # Security check - ensure template is within templates directory
        try:
            template_path.resolve().relative_to(templates_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid template path'
            }), 400
        
        if not template_path.exists():
            return jsonify({
                'success': False,
                'error': f'Template file {template_filename} not found'
            }), 404
        
        # Initialize analyzer
        config = {
            'llm_settings': current_app.config.get('LLM_SETTINGS', {}),
            'analysis_settings': current_app.config.get('ANALYSIS_SETTINGS', {})
        }
        
        analyzer = create_contract_analyzer(config)
        
        # Log analysis start
        security_auditor.log_security_event(
            event_type='analysis_started',
            details={
                'contract_id': contract_id,
                'template': template_filename,
                'include_llm': include_llm
            },
            request=request
        )
        
        # Perform analysis
        logger.info(f"Starting analysis for contract {contract_id} with template {template_filename}")
        
        analysis_result = analyzer.analyze_contract(
            contract=contract,
            template_path=str(template_path),
            include_llm_analysis=include_llm
        )
        
        # Store analysis result
        analysis_results_store[analysis_result.analysis_id] = analysis_result
        
        # Log analysis completion
        security_auditor.log_security_event(
            event_type='analysis_completed',
            details={
                'analysis_id': analysis_result.analysis_id,
                'contract_id': contract_id,
                'total_changes': analysis_result.total_changes,
                'risk_level': analysis_result.overall_risk_level,
                'processing_time': analysis_result.processing_time_seconds
            },
            request=request
        )
        
        logger.info(
            f"Analysis {analysis_result.analysis_id} completed - "
            f"Changes: {analysis_result.total_changes}, Risk: {analysis_result.overall_risk_level}"
        )
        
        return jsonify({
            'success': True,
            'analysis_result': analysis_result.get_summary(),
            'message': 'Analysis completed successfully'
        })
        
    except ContractAnalysisError as e:
        logger.error(f"Contract analysis error: {e}")
        security_auditor.log_security_event(
            event_type='analysis_failed',
            details={'error': str(e)},
            request=request
        )
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        security_auditor.log_security_event(
            event_type='analysis_error',
            details={'error': str(e)},
            request=request
        )
        return jsonify({
            'success': False,
            'error': 'Failed to start analysis'
        }), 500


@analysis_bp.route('/analysis/<analysis_id>')
def get_analysis_result(analysis_id):
    """Get detailed analysis result by ID"""
    try:
        if analysis_id not in analysis_results_store:
            return jsonify({
                'success': False,
                'error': 'Analysis result not found'
            }), 404
        
        analysis_result = analysis_results_store[analysis_id]
        
        # Return detailed analysis data
        detailed_result = analysis_result.to_dict()
        
        return jsonify({
            'success': True,
            'analysis_result': detailed_result
        })
        
    except Exception as e:
        logger.error(f"Error retrieving analysis result {analysis_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve analysis result'
        }), 500


@analysis_bp.route('/analysis/<analysis_id>/changes')
def get_analysis_changes(analysis_id):
    """Get detailed changes for an analysis"""
    try:
        if analysis_id not in analysis_results_store:
            return jsonify({
                'success': False,
                'error': 'Analysis result not found'
            }), 404
        
        analysis_result = analysis_results_store[analysis_id]
        
        # Group changes by classification
        changes_by_type = {
            'critical': [change.to_dict() for change in analysis_result.get_critical_changes()],
            'significant': [change.to_dict() for change in analysis_result.get_significant_changes()],
            'inconsequential': [change.to_dict() for change in analysis_result.get_inconsequential_changes()]
        }
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'changes_by_type': changes_by_type,
            'total_changes': analysis_result.total_changes,
            'risk_level': analysis_result.overall_risk_level
        })
        
    except Exception as e:
        logger.error(f"Error retrieving changes for analysis {analysis_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve analysis changes'
        }), 500


@analysis_bp.route('/templates')
def list_templates():
    """List available template files"""
    try:
        templates_dir = Path(current_app.config.get('TEMPLATES_FOLDER', 'data/templates'))
        
        if not templates_dir.exists():
            return jsonify({
                'success': True,
                'templates': [],
                'message': 'Templates directory not found'
            })
        
        templates = []
        for template_file in templates_dir.glob('*.docx'):
            try:
                stat = template_file.stat()
                templates.append({
                    'filename': template_file.name,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'display_name': template_file.stem.replace('_', ' ').title()
                })
            except Exception as e:
                logger.warning(f"Error reading template {template_file}: {e}")
        
        # Sort by filename
        templates.sort(key=lambda x: x['filename'])
        
        return jsonify({
            'success': True,
            'templates': templates,
            'total': len(templates)
        })
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list templates'
        }), 500


@analysis_bp.route('/templates/upload', methods=['POST'])
def upload_template():
    """Upload a new template file"""
    try:
        # Import required modules
        from flask import request, current_app
        from werkzeug.utils import secure_filename
        from pathlib import Path
        import uuid
        
        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate file type
        if not file.filename.lower().endswith('.docx'):
            return jsonify({
                'success': False,
                'error': 'Only .docx files are allowed'
            }), 400
        
        # Validate file size (50MB limit)
        if hasattr(file, 'content_length') and file.content_length:
            if file.content_length > 50 * 1024 * 1024:  # 50MB
                return jsonify({
                    'success': False,
                    'error': 'File too large. Maximum size is 50MB'
                }), 400
        
        # Secure filename
        original_filename = file.filename
        filename = secure_filename(original_filename)
        
        # Ensure templates directory exists
        templates_dir = Path(current_app.config.get('TEMPLATES_FOLDER', 'data/templates'))
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename if file already exists
        file_path = templates_dir / filename
        if file_path.exists():
            name, ext = filename.rsplit('.', 1)
            unique_suffix = str(uuid.uuid4())[:8]
            filename = f"{name}_{unique_suffix}.{ext}"
            file_path = templates_dir / filename
        
        # Save file
        file.save(str(file_path))
        
        # Log successful upload
        logger.info(f"Template uploaded successfully: {filename}")
        
        # Return success response
        return jsonify({
            'success': True,
            'filename': filename,
            'original_filename': original_filename,
            'size': file_path.stat().st_size,
            'message': f'Template {original_filename} uploaded successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading template: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to upload template'
        }), 500


@analysis_bp.route('/analysis/<analysis_id>', methods=['DELETE'])
def delete_analysis_result(analysis_id):
    """Delete an analysis result"""
    try:
        if analysis_id not in analysis_results_store:
            return jsonify({
                'success': False,
                'error': 'Analysis result not found'
            }), 404
        
        analysis_result = analysis_results_store[analysis_id]
        contract_id = analysis_result.contract_id
        
        # Remove from store
        del analysis_results_store[analysis_id]
        
        # Log deletion
        security_auditor.log_security_event(
            event_type='analysis_deleted',
            details={'analysis_id': analysis_id, 'contract_id': contract_id},
            request=request
        )
        
        return jsonify({
            'success': True,
            'message': f'Analysis result {analysis_id} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting analysis result {analysis_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete analysis result'
        }), 500
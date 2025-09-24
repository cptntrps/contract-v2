"""
Report generation and download routes

Handles report creation and file downloads.
"""

from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app

from ...services.reports.generator import create_report_generator, ReportGenerationError
from ...utils.security.audit import SecurityAuditor, SecurityEventType
from ...utils.logging.setup import get_logger

# Import analysis results store from analysis routes
from .analysis import analysis_results_store

logger = get_logger(__name__)
reports_bp = Blueprint('reports', __name__)

# Initialize security auditor
security_auditor = SecurityAuditor()


@reports_bp.route('/reports')
def list_reports():
    """List all generated reports"""
    try:
        # Initialize report generator to list existing reports
        config = {
            'REPORTS_FOLDER': current_app.config.get('REPORTS_FOLDER', 'data/reports')
        }
        report_generator = create_report_generator(config)
        
        # Get list of reports
        reports_list = report_generator.list_reports()
        
        return jsonify({
            'success': True,
            'reports': reports_list,
            'total': len(reports_list)
        })
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list reports'
        }), 500


@reports_bp.route('/reports/generate', methods=['POST'])
def generate_report():
    """Generate reports for an analysis result"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No request data provided'
            }), 400
        
        analysis_id = data.get('analysis_id')
        formats = data.get('formats', ['excel', 'word'])  # Default formats
        
        # Validate required fields
        if not analysis_id:
            return jsonify({
                'success': False,
                'error': 'Analysis ID is required'
            }), 400
        
        # Get analysis result
        if analysis_id not in analysis_results_store:
            return jsonify({
                'success': False,
                'error': 'Analysis result not found'
            }), 404
        
        analysis_result = analysis_results_store[analysis_id]
        
        # Initialize report generator
        config = {
            'REPORTS_FOLDER': current_app.config.get('REPORTS_FOLDER', 'data/reports')
        }
        report_generator = create_report_generator(config)
        
        # Prepare analysis data for report generation
        # Handle both dictionary and object formats
        if isinstance(analysis_result, dict):
            # Dictionary format (frontend-compatible)
            analysis_data = {
                'id': analysis_result.get('id', analysis_id),
                'contract': analysis_result.get('contract', 'Unknown'),
                'template': analysis_result.get('template', 'Unknown'),
                'date': analysis_result.get('date', 'Unknown'),
                'changes': analysis_result.get('changes', 0),
                'similarity': analysis_result.get('similarity', 0),
                'status': 'completed',
                'analysis': analysis_result.get('analysis', [])
            }
            base_name = f"{analysis_result.get('contract', 'contract')}_{analysis_result.get('template', 'template')}_{analysis_result.get('date', 'date').replace('-', '').replace(':', '')}"
        else:
            # Object format (analysis result object)
            analysis_data = {
                'id': analysis_result.analysis_id,
                'contract': analysis_result.contract_id,
                'template': analysis_result.template_id,
                'date': analysis_result.analysis_timestamp.strftime('%Y-%m-%d'),
                'changes': analysis_result.total_changes,
                'similarity': round(analysis_result.similarity_score * 100, 1),
                'status': 'completed',
                'analysis': [change.to_dict() for change in analysis_result.changes]
            }
            base_name = f"{analysis_result.contract_id}_{analysis_result.template_id}_{analysis_result.analysis_timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Log report generation start
        security_auditor.log_security_event(
            event_type=SecurityEventType.REPORT_GENERATION_STARTED,
            details={
                'analysis_id': analysis_id,
                'formats': formats,
                'base_name': base_name
            },
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        logger.info(f"Starting report generation for analysis {analysis_id} - Formats: {formats}")
        
        # Generate reports
        generated_files = report_generator.generate_all_reports(
            analysis_data=analysis_data,
            base_name=base_name,
            formats=formats
        )
        
        if not generated_files:
            return jsonify({
                'success': False,
                'error': 'No reports were generated'
            }), 500
        
        # Prepare response with file metadata
        report_files = []
        for format_name, file_path in generated_files.items():
            if file_path:
                file_metadata = report_generator.get_report_metadata(file_path)
                file_metadata['format'] = format_name
                report_files.append(file_metadata)
        
        # Log successful generation
        security_auditor.log_security_event(
            event_type=SecurityEventType.REPORT_GENERATION_COMPLETED,
            details={
                'analysis_id': analysis_id,
                'generated_files': list(generated_files.keys()),
                'file_count': len(report_files)
            },
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        logger.info(f"Report generation completed for analysis {analysis_id} - Generated {len(report_files)} files")
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'generated_reports': report_files,
            'message': f'Generated {len(report_files)} reports successfully'
        })
        
    except ReportGenerationError as e:
        logger.error(f"Report generation error: {e}")
        security_auditor.log_security_event(
            event_type=SecurityEventType.REPORT_GENERATION_FAILED,
            details={'error': str(e)},
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error generating reports: {e}")
        security_auditor.log_security_event(
            event_type=SecurityEventType.REPORT_GENERATION_ERROR,
            details={'error': str(e)},
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return jsonify({
            'success': False,
            'error': 'Failed to generate reports'
        }), 500


@reports_bp.route('/reports/download/<filename>')
def download_report(filename):
    """Download a generated report file"""
    try:
        # Validate filename (security check)
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({
                'success': False,
                'error': 'Invalid filename'
            }), 400
        
        # Get reports directory
        reports_dir = Path(current_app.config.get('REPORTS_FOLDER', 'data/reports'))
        file_path = reports_dir / filename
        
        # Check if file exists and is within reports directory
        if not file_path.exists() or not file_path.is_file():
            return jsonify({
                'success': False,
                'error': 'Report file not found'
            }), 404
        
        # Security check - ensure file is within reports directory
        try:
            file_path.resolve().relative_to(reports_dir.resolve())
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Log download
        security_auditor.log_security_event(
            event_type=SecurityEventType.REPORT_DOWNLOADED,
            details={'filename': filename, 'file_size': file_path.stat().st_size},
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # Send file
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error downloading report {filename}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to download report'
        }), 500


@reports_bp.route('/download-redlined-document')
def download_redlined_document():
    """Download redlined document for an analysis"""
    try:
        analysis_id = request.args.get('id')
        if not analysis_id:
            return jsonify({
                'success': False,
                'error': 'Analysis ID is required'
            }), 400
        
        # Find the redlined document file
        reports_dir = Path(current_app.config.get('REPORTS_FOLDER', 'data/reports'))
        
        # Look for redlined document files with the analysis ID pattern
        redlined_files = list(reports_dir.glob(f"*{analysis_id}*redlined*.docx"))
        
        if not redlined_files:
            # Try alternate pattern - look for files matching the analysis result
            if analysis_id in analysis_results_store:
                result = analysis_results_store[analysis_id]
                # Try to find files based on contract name
                contract_name = result.get('contract', '').replace('.docx', '')
                redlined_files = list(reports_dir.glob(f"{contract_name}*redlined*.docx"))
        
        if not redlined_files:
            return jsonify({
                'success': False,
                'error': 'Redlined document not found'
            }), 404
        
        # Use the most recent file
        redlined_file = max(redlined_files, key=lambda f: f.stat().st_mtime)
        
        # Log download
        security_auditor.log_security_event(
            event_type=SecurityEventType.REDLINED_DOCUMENT_DOWNLOADED,
            details={'analysis_id': analysis_id, 'filename': redlined_file.name},
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return send_file(
            str(redlined_file),
            as_attachment=True,
            download_name=redlined_file.name
        )
        
    except Exception as e:
        logger.error(f"Error downloading redlined document for analysis {analysis_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to download redlined document'
        }), 500


@reports_bp.route('/download-changes-table')
def download_changes_table():
    """Download changes table for an analysis"""
    try:
        analysis_id = request.args.get('id')
        if not analysis_id:
            return jsonify({
                'success': False,
                'error': 'Analysis ID is required'
            }), 400
        
        # Find the changes table file
        reports_dir = Path(current_app.config.get('REPORTS_FOLDER', 'data/reports'))
        
        # Look for changes table files with the analysis ID pattern
        changes_files = list(reports_dir.glob(f"*{analysis_id}*changes_table*.xlsx"))
        
        if not changes_files:
            # Try alternate pattern - look for files matching the analysis result
            if analysis_id in analysis_results_store:
                result = analysis_results_store[analysis_id]
                # Try to find files based on contract name
                contract_name = result.get('contract', '').replace('.docx', '')
                changes_files = list(reports_dir.glob(f"{contract_name}*changes_table*.xlsx"))
        
        if not changes_files:
            return jsonify({
                'success': False,
                'error': 'Changes table not found'
            }), 404
        
        # Use the most recent file
        changes_file = max(changes_files, key=lambda f: f.stat().st_mtime)
        
        # Log download
        security_auditor.log_security_event(
            event_type=SecurityEventType.CHANGES_TABLE_DOWNLOADED,
            details={'analysis_id': analysis_id, 'filename': changes_file.name},
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return send_file(
            str(changes_file),
            as_attachment=True,
            download_name=changes_file.name
        )
        
    except Exception as e:
        logger.error(f"Error downloading changes table for analysis {analysis_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to download changes table'
        }), 500
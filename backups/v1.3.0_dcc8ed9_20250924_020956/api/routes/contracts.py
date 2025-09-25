"""
Contract management routes

Handles contract upload, validation, and file management operations.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from ...core.models.contract import Contract, validate_contract_file
from ...utils.security.validators import SecurityValidator
from ...utils.security.audit import SecurityAuditor
from ...utils.logging.setup import get_logger

logger = get_logger(__name__)
contracts_bp = Blueprint('contracts', __name__)

# Initialize security components
security_validator = SecurityValidator()
security_auditor = SecurityAuditor()

# Store contracts in memory for this session (in production, use database)
contracts_store = {}


def initialize_contracts_from_uploads():
    """Load existing contract files from uploads directory into memory store"""
    try:
        upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'data/uploads'))
        if not upload_dir.exists():
            logger.info("Upload directory does not exist, skipping contract initialization")
            return
        
        loaded_count = 0
        for file_path in upload_dir.glob('*.docx'):
            try:
                # Extract contract info from filename (assuming format: contract_id_timestamp_originalname.docx)
                filename = file_path.name
                
                # Try to extract contract ID from filename
                # Expected format: Contract_###_Name_Date.docx
                parts = filename.split('_')
                if len(parts) >= 2 and parts[0].lower() == 'contract':
                    contract_id = f"contract_{parts[1]}"
                else:
                    # Create a new contract ID based on filename
                    contract_id = f"contract_{uuid.uuid4().hex[:8]}"
                
                # Skip if contract already exists
                if contract_id in contracts_store:
                    continue
                
                # Get file info
                file_size = file_path.stat().st_size
                upload_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # Use the actual filename as original filename
                original_filename = filename
                
                # Create contract object
                contract = Contract(
                    id=contract_id,
                    filename=filename,
                    original_filename=original_filename,
                    file_path=str(file_path),
                    file_size=file_size,
                    upload_timestamp=upload_time,
                    status="uploaded"
                )
                
                contracts_store[contract_id] = contract
                loaded_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to load contract from {file_path}: {e}")
        
        logger.info(f"Initialized {loaded_count} contracts from uploads directory")
        
    except Exception as e:
        logger.error(f"Error initializing contracts from uploads: {e}")


# Initialize contracts when module loads
def init_contracts_store():
    """Initialize contracts store with existing files"""
    from flask import current_app
    if current_app:
        initialize_contracts_from_uploads()


@contracts_bp.route('/contracts')
def list_contracts():
    """List all uploaded contracts with metadata"""
    try:
        # Initialize contracts from uploads directory if store is empty
        if not contracts_store:
            initialize_contracts_from_uploads()
        
        contracts_list = []
        
        for contract in contracts_store.values():
            contracts_list.append(contract.get_summary())
        
        # Sort by upload date (newest first)
        contracts_list.sort(key=lambda x: x['upload_date'], reverse=True)
        
        return jsonify({
            'success': True,
            'contracts': contracts_list,
            'total': len(contracts_list)
        })
        
    except Exception as e:
        logger.error(f"Error listing contracts: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list contracts'
        }), 500


@contracts_bp.route('/contracts/upload', methods=['POST'])
def upload_contract():
    """Upload a new contract file"""
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Security validation
        validation_result = security_validator.validate_file_content(file)
        if not validation_result['valid']:
            security_auditor.log_security_event(
                event_type='file_upload_rejected',
                details={'filename': file.filename, 'errors': validation_result['errors']},
                request=request
            )
            return jsonify({
                'success': False,
                'error': 'File validation failed',
                'details': validation_result['errors']
            }), 400
        
        # Generate unique contract ID
        contract_id = f"contract_{uuid.uuid4().hex[:8]}"
        
        # Secure filename
        original_filename = file.filename
        secure_name = secure_filename(file.filename)
        
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name_parts = secure_name.rsplit('.', 1)
        if len(name_parts) == 2:
            final_filename = f"{contract_id}_{timestamp}_{name_parts[0]}.{name_parts[1]}"
        else:
            final_filename = f"{contract_id}_{timestamp}_{secure_name}"
        
        # Ensure uploads directory exists
        upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'data/uploads'))
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = upload_dir / final_filename
        file.save(str(file_path))
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Create contract object
        contract = Contract.create_from_upload(
            contract_id=contract_id,
            filename=final_filename,
            original_filename=original_filename,
            file_path=str(file_path),
            file_size=file_size
        )
        
        # Store contract (in production, save to database)
        contracts_store[contract_id] = contract
        
        # Log successful upload
        security_auditor.log_security_event(
            event_type='file_upload_success',
            details={
                'contract_id': contract_id,
                'filename': original_filename,
                'file_size': file_size
            },
            request=request
        )
        
        logger.info(f"Contract uploaded successfully: {contract_id}")
        
        return jsonify({
            'success': True,
            'contract': contract.get_summary(),
            'message': f'Contract {original_filename} uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error uploading contract: {e}")
        security_auditor.log_security_event(
            event_type='file_upload_error',
            details={'error': str(e)},
            request=request
        )
        return jsonify({
            'success': False,
            'error': 'Failed to upload contract'
        }), 500


@contracts_bp.route('/contracts/<contract_id>')
def get_contract(contract_id):
    """Get contract details by ID"""
    try:
        if contract_id not in contracts_store:
            return jsonify({
                'success': False,
                'error': 'Contract not found'
            }), 404
        
        contract = contracts_store[contract_id]
        
        return jsonify({
            'success': True,
            'contract': contract.get_summary()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving contract {contract_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve contract'
        }), 500


@contracts_bp.route('/contracts/<contract_id>', methods=['DELETE'])
def delete_contract(contract_id):
    """Delete a contract and its file"""
    try:
        if contract_id not in contracts_store:
            return jsonify({
                'success': False,
                'error': 'Contract not found'
            }), 404
        
        contract = contracts_store[contract_id]
        
        # Delete file if it exists
        try:
            file_path = Path(contract.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted contract file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete contract file: {e}")
        
        # Remove from store
        del contracts_store[contract_id]
        
        # Log deletion
        security_auditor.log_security_event(
            event_type='contract_deleted',
            details={'contract_id': contract_id, 'filename': contract.original_filename},
            request=request
        )
        
        return jsonify({
            'success': True,
            'message': f'Contract {contract.original_filename} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting contract {contract_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete contract'
        }), 500


@contracts_bp.route('/contracts/<contract_id>/validate')
def validate_contract_endpoint(contract_id):
    """Validate a contract file"""
    try:
        if contract_id not in contracts_store:
            return jsonify({
                'success': False,
                'error': 'Contract not found'
            }), 404
        
        contract = contracts_store[contract_id]
        
        # Validate file
        is_valid = validate_contract_file(contract.file_path)
        
        return jsonify({
            'success': True,
            'contract_id': contract_id,
            'valid': is_valid,
            'file_path': contract.file_path
        })
        
    except Exception as e:
        logger.error(f"Error validating contract {contract_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to validate contract'
        }), 500


@contracts_bp.route('/contracts/clear', methods=['POST'])
def clear_all_contracts():
    """Clear all contracts (development/admin function)"""
    try:
        deleted_count = 0
        
        # Delete all files and clear store
        for contract in contracts_store.values():
            try:
                file_path = Path(contract.file_path)
                if file_path.exists():
                    file_path.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete contract file {contract.file_path}: {e}")
        
        contracts_store.clear()
        
        # Log bulk deletion
        security_auditor.log_security_event(
            event_type='contracts_cleared',
            details={'deleted_count': deleted_count},
            request=request
        )
        
        logger.info(f"Cleared {deleted_count} contracts")
        
        return jsonify({
            'success': True,
            'message': f'Cleared {deleted_count} contracts successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing contracts: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear contracts'
        }), 500
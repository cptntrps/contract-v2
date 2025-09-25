"""
Test comprehensive error handling system
"""
import pytest
from flask import Flask, request
from unittest.mock import Mock, patch

from app.utils.errors.exceptions import *
from app.utils.errors.handlers import ErrorHandler, register_error_handlers
from app.utils.errors.validators import ValidationHandler, validate_schema, ContractUploadSchema
from app.utils.errors.responses import ErrorResponse, create_error_response
from app.utils.security.audit import SecurityAuditor


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_contract_analyzer_error_base(self):
        """Test base ContractAnalyzerError"""
        error = ContractAnalyzerError("Test error", "TEST_ERROR", {"key": "value"})
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
        
        error_dict = error.to_dict()
        assert error_dict['error'] == "TEST_ERROR"
        assert error_dict['message'] == "Test error"
        assert error_dict['details'] == {"key": "value"}
    
    def test_validation_error(self):
        """Test ValidationError with field information"""
        error = ValidationError("Invalid value", field="username", value="bad_value")
        
        assert error.message == "Invalid value"
        assert error.details['field'] == "username"
        assert error.details['value'] == "bad_value"
    
    def test_not_found_error(self):
        """Test NotFoundError with resource information"""
        error = NotFoundError("contract", identifier="contract_123")
        
        assert "contract not found" in error.message.lower()
        assert error.details['resource'] == "contract"
        assert error.details['identifier'] == "contract_123"
    
    def test_database_error(self):
        """Test DatabaseError with operation information"""
        error = DatabaseError("insert", "Constraint violation")
        
        assert error.message == "Constraint violation"
        assert error.details['operation'] == "insert"
    
    def test_security_error(self):
        """Test SecurityError with violation type"""
        error = SecurityError("path_traversal", "Invalid path detected")
        
        assert error.message == "Invalid path detected"
        assert error.details['violation_type'] == "path_traversal"


class TestValidationHandler:
    """Test ValidationHandler methods"""
    
    def test_validate_contract_id_valid(self):
        """Test valid contract ID validation"""
        valid_ids = ["contract_123", "test_contract", "CONTRACT_001", "abc123_def"]
        
        for contract_id in valid_ids:
            result = ValidationHandler.validate_contract_id(contract_id)
            assert result == contract_id
    
    def test_validate_contract_id_invalid(self):
        """Test invalid contract ID validation"""
        invalid_cases = [
            ("", "Contract ID is required"),
            (None, "Contract ID is required"),
            (123, "Contract ID must be a string"),
            ("ab", "Contract ID must be at least 3 characters"),
            ("a" * 51, "Contract ID cannot exceed 50 characters"),
            ("contract-123", "Contract ID can only contain letters, numbers, and underscores"),
            ("contract.123", "Contract ID can only contain letters, numbers, and underscores"),
            ("contract 123", "Contract ID can only contain letters, numbers, and underscores")
        ]
        
        for contract_id, expected_message in invalid_cases:
            with pytest.raises(ValidationError) as exc_info:
                ValidationHandler.validate_contract_id(contract_id)
            assert expected_message in str(exc_info.value)
    
    def test_validate_analysis_id_valid(self):
        """Test valid analysis ID validation"""
        valid_ids = ["analysis_123", "test-analysis", "ANALYSIS_001", "abc123_def-456"]
        
        for analysis_id in valid_ids:
            result = ValidationHandler.validate_analysis_id(analysis_id)
            assert result == analysis_id
    
    def test_validate_analysis_id_invalid(self):
        """Test invalid analysis ID validation"""
        invalid_cases = [
            ("", "Analysis ID is required"),
            (None, "Analysis ID is required"),
            (123, "Analysis ID must be a string"),
            ("a" * 101, "Analysis ID cannot exceed 100 characters"),
            ("analysis.123", "Analysis ID can only contain letters, numbers, underscores, and hyphens")
        ]
        
        for analysis_id, expected_message in invalid_cases:
            with pytest.raises(ValidationError) as exc_info:
                ValidationHandler.validate_analysis_id(analysis_id)
            assert expected_message in str(exc_info.value)
    
    def test_validate_filename_valid(self):
        """Test valid filename validation"""
        valid_names = ["contract.docx", "test_file.pdf", "document_v1.docx"]
        
        for filename in valid_names:
            result = ValidationHandler.validate_filename(filename)
            assert result == filename
    
    def test_validate_filename_invalid(self):
        """Test invalid filename validation"""
        invalid_cases = [
            ("", "Filename is required"),
            ("../etc/passwd", "Invalid filename"),
            ("file\\test.docx", "Invalid filename"),
            ("file<script>.docx", "Filename contains invalid character"),
            ("file?.docx", "Filename contains invalid character"),
            ("a" * 256, "Filename too long")
        ]
        
        for filename, expected_message in invalid_cases:
            with pytest.raises((ValidationError, SecurityError)) as exc_info:
                ValidationHandler.validate_filename(filename)
            assert any(msg in str(exc_info.value) for msg in [expected_message.split()[0]])
    
    def test_validate_file_upload_valid(self):
        """Test valid file upload validation"""
        # Mock file object
        mock_file = Mock()
        mock_file.filename = "test.docx"
        mock_file.seek.return_value = None
        mock_file.tell.return_value = 1024  # 1KB file
        
        result = ValidationHandler.validate_file_upload(
            mock_file,
            allowed_extensions=['docx'],
            max_size=10 * 1024 * 1024  # 10MB
        )
        
        assert result['filename'] == "test.docx"
        assert result['size'] == 1024
        assert result['extension'] == ".docx"
    
    def test_validate_file_upload_invalid(self):
        """Test invalid file upload validation"""
        # Test missing file
        with pytest.raises(ValidationError) as exc_info:
            ValidationHandler.validate_file_upload(None)
        assert "No file provided" in str(exc_info.value)
        
        # Test invalid extension
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.seek.return_value = None
        mock_file.tell.return_value = 1024
        
        with pytest.raises(ValidationError) as exc_info:
            ValidationHandler.validate_file_upload(
                mock_file,
                allowed_extensions=['docx']
            )
        assert "File type not allowed" in str(exc_info.value)
        
        # Test file too large
        mock_file.filename = "test.docx"
        mock_file.tell.return_value = 100 * 1024 * 1024  # 100MB
        
        with pytest.raises(ValidationError) as exc_info:
            ValidationHandler.validate_file_upload(
                mock_file,
                max_size=50 * 1024 * 1024  # 50MB limit
            )
        assert "File too large" in str(exc_info.value)
    
    def test_validate_pagination(self):
        """Test pagination validation"""
        # Valid pagination
        result = ValidationHandler.validate_pagination(2, 20)
        assert result['page'] == 2
        assert result['per_page'] == 20
        assert result['offset'] == 20
        
        # Default values
        result = ValidationHandler.validate_pagination(None, None)
        assert result['page'] == 1
        assert result['per_page'] == 20
        assert result['offset'] == 0
        
        # Invalid pagination
        with pytest.raises(ValidationError):
            ValidationHandler.validate_pagination("invalid", 20)
        
        with pytest.raises(ValidationError):
            ValidationHandler.validate_pagination(0, 20)
        
        with pytest.raises(ValidationError):
            ValidationHandler.validate_pagination(1, 101)


class TestErrorResponse:
    """Test error response formatting"""
    
    def test_format_error_custom_exception(self):
        """Test formatting custom exception"""
        error = ValidationError("Test validation error", field="test_field")
        response = ErrorResponse.format_error(error, 400)
        
        assert response['success'] is False
        assert response['status_code'] == 400
        assert response['error'] == "ValidationError"
        assert response['message'] == "Test validation error"
        assert 'timestamp' in response
    
    def test_format_error_standard_exception(self):
        """Test formatting standard exception"""
        error = ValueError("Standard error message")
        response = ErrorResponse.format_error(error, 500)
        
        assert response['success'] is False
        assert response['status_code'] == 500
        assert response['error'] == "ValueError"
        assert response['message'] == "Standard error message"
    
    def test_validation_error_response(self):
        """Test validation error response"""
        response = ErrorResponse.validation_error("username", "Username is required")
        
        assert response['status_code'] == 400
        assert response['error'] == "ValidationError"
        assert response['details']['field'] == "username"
    
    def test_not_found_error_response(self):
        """Test not found error response"""
        response = ErrorResponse.not_found_error("contract", "contract_123")
        
        assert response['status_code'] == 404
        assert response['error'] == "NotFoundError"
        assert response['details']['resource'] == "contract"
        assert response['details']['identifier'] == "contract_123"
    
    def test_create_error_response(self):
        """Test create_error_response function"""
        from flask import Flask
        app = Flask(__name__)
        
        with app.app_context():
            error = ValidationError("Test error")
            response, status_code = create_error_response(error)
            
            assert status_code == 400
            assert response.json['success'] is False
            assert response.json['error'] == "ValidationError"


class TestErrorHandlerIntegration:
    """Test error handler integration with Flask"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app with error handlers"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        
        # Register error handlers
        register_error_handlers(app)
        
        # Add test routes that raise errors
        @app.route('/test/validation-error')
        def test_validation_error():
            raise ValidationError("Test validation error", field="test")
        
        @app.route('/test/not-found-error')
        def test_not_found_error():
            raise NotFoundError("resource", "123")
        
        @app.route('/test/security-error')
        def test_security_error():
            raise SecurityError("test_violation", "Test security error")
        
        @app.route('/test/database-error')
        def test_database_error():
            raise DatabaseError("test_operation", "Test database error")
        
        @app.route('/test/generic-error')
        def test_generic_error():
            raise ValueError("Test generic error")
        
        return app
    
    def test_validation_error_handler(self, app):
        """Test validation error is handled correctly"""
        with app.test_client() as client:
            response = client.get('/test/validation-error')
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert data['error'] == "ValidationError"
            assert data['details']['field'] == "test"
    
    def test_not_found_error_handler(self, app):
        """Test not found error is handled correctly"""
        with app.test_client() as client:
            response = client.get('/test/not-found-error')
            
            assert response.status_code == 404
            data = response.get_json()
            assert data['success'] is False
            assert data['error'] == "NotFoundError"
    
    def test_security_error_handler(self, app):
        """Test security error is handled correctly"""
        with app.test_client() as client:
            response = client.get('/test/security-error')
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert data['error'] == "SecurityError"
    
    def test_database_error_handler(self, app):
        """Test database error is handled correctly"""
        with app.test_client() as client:
            response = client.get('/test/database-error')
            
            assert response.status_code == 500
            data = response.get_json()
            assert data['success'] is False
            assert data['error'] == "DatabaseError"
    
    def test_generic_error_handler(self, app):
        """Test generic error is handled correctly"""
        with app.test_client() as client:
            response = client.get('/test/generic-error')
            
            assert response.status_code == 500
            data = response.get_json()
            assert data['success'] is False
            assert data['error'] == "ValueError"
    
    def test_404_api_endpoint(self, app):
        """Test 404 handling for API endpoints"""
        with app.test_client() as client:
            response = client.get('/api/nonexistent')
            
            assert response.status_code == 404
            data = response.get_json()
            assert data['success'] is False
            assert data['error'] == "NotFoundError"
    
    def test_404_web_endpoint(self, app):
        """Test 404 handling for web endpoints"""
        with app.test_client() as client:
            response = client.get('/nonexistent')
            
            # Should serve dashboard for non-API routes
            assert response.status_code == 200


class TestSchemaValidation:
    """Test schema validation with Marshmallow"""
    
    def test_contract_upload_schema_valid(self):
        """Test valid contract upload schema"""
        mock_file = Mock()
        mock_file.filename = "test.docx"
        
        data = {
            'file': mock_file,
            'description': 'Test description',
            'tags': ['tag1', 'tag2']
        }
        
        result = validate_schema(ContractUploadSchema, data)
        assert result['file'] == mock_file
        assert result['description'] == 'Test description'
        assert result['tags'] == ['tag1', 'tag2']
    
    def test_contract_upload_schema_invalid(self):
        """Test invalid contract upload schema"""
        data = {
            'description': 'A' * 600,  # Too long
            'tags': ['A' * 60]  # Tag too long
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(ContractUploadSchema, data)
        
        assert "validation_errors" in str(exc_info.value)
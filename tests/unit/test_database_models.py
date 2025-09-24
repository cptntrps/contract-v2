"""
Test database models and repositories
"""
import pytest
from datetime import datetime
from flask import Flask
from sqlalchemy.exc import IntegrityError

from app.database import init_app, db
from app.database.models import ContractModel, AnalysisResultModel, ChangeModel
from app.database.repositories import ContractRepository, AnalysisRepository
from app.core.models.contract import Contract
from app.core.models.analysis_result import AnalysisResult, Change, ChangeType, ChangeClassification


@pytest.fixture
def app():
    """Create test Flask app"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    
    init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_contract():
    """Create test contract object"""
    return Contract(
        id="test_contract_001",
        filename="test_contract.docx",
        original_filename="Test Contract.docx",
        file_path="/tmp/test_contract.docx",
        file_size=1024,
        upload_timestamp=datetime.now()
    )


@pytest.fixture
def test_analysis_result():
    """Create test analysis result object"""
    analysis = AnalysisResult(
        analysis_id="test_analysis_001",
        contract_id="test_contract_001",
        template_id="template_001",
        analysis_timestamp=datetime.now(),
        similarity_score=0.85,
        overall_risk_level="MEDIUM"
    )
    
    # Add test change
    change = Change(
        change_id="change_001",
        change_type=ChangeType.MODIFICATION,
        classification=ChangeClassification.SIGNIFICANT,
        deleted_text="old text",
        inserted_text="new text",
        explanation="Test change"
    )
    
    analysis.add_change(change)
    return analysis


class TestContractModel:
    """Test ContractModel database operations"""
    
    def test_create_contract_model(self, app, test_contract):
        """Test creating contract model"""
        with app.app_context():
            contract_model = ContractModel.from_domain_object(test_contract)
            db.session.add(contract_model)
            db.session.commit()
            
            assert contract_model.id == "test_contract_001"
            assert contract_model.original_filename == "Test Contract.docx"
            assert contract_model.file_size == 1024
    
    def test_contract_to_domain_object(self, app, test_contract):
        """Test converting contract model to domain object"""
        with app.app_context():
            contract_model = ContractModel.from_domain_object(test_contract)
            domain_object = contract_model.to_domain_object()
            
            assert domain_object.id == test_contract.id
            assert domain_object.original_filename == test_contract.original_filename
            assert domain_object.file_size == test_contract.file_size
    
    def test_contract_summary(self, app, test_contract):
        """Test getting contract summary"""
        with app.app_context():
            contract_model = ContractModel.from_domain_object(test_contract)
            summary = contract_model.get_summary()
            
            assert summary['id'] == "test_contract_001"
            assert summary['filename'] == "Test Contract.docx"
            assert summary['file_size'] == 1024
            assert summary['status'] == 'uploaded'


class TestAnalysisResultModel:
    """Test AnalysisResultModel database operations"""
    
    def test_create_analysis_result_model(self, app, test_analysis_result):
        """Test creating analysis result model"""
        with app.app_context():
            # Create contract first
            contract_model = ContractModel(
                id="test_contract_001",
                filename="test.docx",
                original_filename="test.docx",
                file_path="/tmp/test.docx",
                file_size=1024
            )
            db.session.add(contract_model)
            
            # Create analysis result
            analysis_model = AnalysisResultModel.from_domain_object(test_analysis_result)
            db.session.add(analysis_model)
            
            # Create change models
            for change in test_analysis_result.changes:
                change_model = ChangeModel.from_domain_object(change, test_analysis_result.analysis_id)
                db.session.add(change_model)
            
            db.session.commit()
            
            assert analysis_model.id == "test_analysis_001"
            assert analysis_model.contract_id == "test_contract_001"
            assert analysis_model.overall_risk_level == "MEDIUM"
            assert len(analysis_model.changes) == 1
    
    def test_analysis_to_domain_object(self, app, test_analysis_result):
        """Test converting analysis model to domain object"""
        with app.app_context():
            # Create contract first
            contract_model = ContractModel(
                id="test_contract_001",
                filename="test.docx",
                original_filename="test.docx",
                file_path="/tmp/test.docx",
                file_size=1024
            )
            db.session.add(contract_model)
            
            # Create and save analysis
            analysis_model = AnalysisResultModel.from_domain_object(test_analysis_result)
            db.session.add(analysis_model)
            
            for change in test_analysis_result.changes:
                change_model = ChangeModel.from_domain_object(change, test_analysis_result.analysis_id)
                db.session.add(change_model)
            
            db.session.commit()
            
            # Convert back to domain object
            domain_object = analysis_model.to_domain_object()
            
            assert domain_object.analysis_id == test_analysis_result.analysis_id
            assert domain_object.contract_id == test_analysis_result.contract_id
            assert domain_object.overall_risk_level == test_analysis_result.overall_risk_level
            assert len(domain_object.changes) == 1


class TestContractRepository:
    """Test ContractRepository operations"""
    
    def test_create_contract(self, app, test_contract):
        """Test creating contract through repository"""
        with app.app_context():
            repo = ContractRepository()
            contract_model = repo.create_from_domain(test_contract)
            
            assert contract_model.id == "test_contract_001"
            assert repo.count() == 1
    
    def test_get_contract_by_id(self, app, test_contract):
        """Test getting contract by ID"""
        with app.app_context():
            repo = ContractRepository()
            repo.create_from_domain(test_contract)
            
            retrieved = repo.get_by_id("test_contract_001")
            assert retrieved is not None
            assert retrieved.id == "test_contract_001"
    
    def test_get_nonexistent_contract(self, app):
        """Test getting nonexistent contract returns None"""
        with app.app_context():
            repo = ContractRepository()
            retrieved = repo.get_by_id("nonexistent")
            assert retrieved is None
    
    def test_get_recent_contracts(self, app, test_contract):
        """Test getting recent contracts"""
        with app.app_context():
            repo = ContractRepository()
            repo.create_from_domain(test_contract)
            
            recent = repo.get_recent(limit=5)
            assert len(recent) == 1
            assert recent[0].id == "test_contract_001"
    
    def test_contract_exists(self, app, test_contract):
        """Test checking if contract exists"""
        with app.app_context():
            repo = ContractRepository()
            
            assert not repo.exists("test_contract_001")
            
            repo.create_from_domain(test_contract)
            assert repo.exists("test_contract_001")
    
    def test_update_analysis_tracking(self, app, test_contract):
        """Test updating contract analysis tracking"""
        with app.app_context():
            repo = ContractRepository()
            repo.create_from_domain(test_contract)
            
            success = repo.update_analysis_tracking("test_contract_001")
            assert success
            
            contract = repo.get_by_id("test_contract_001")
            assert contract.analysis_count == 1
            assert contract.last_analyzed is not None
            assert contract.status == 'analyzed'


class TestAnalysisRepository:
    """Test AnalysisRepository operations"""
    
    def test_create_analysis_result(self, app, test_contract, test_analysis_result):
        """Test creating analysis result through repository"""
        with app.app_context():
            # Create contract first
            contract_repo = ContractRepository()
            contract_repo.create_from_domain(test_contract)
            
            # Create analysis result
            analysis_repo = AnalysisRepository()
            analysis_model = analysis_repo.create_from_domain(test_analysis_result)
            
            assert analysis_model.id == "test_analysis_001"
            assert analysis_repo.count() == 1
    
    def test_get_analysis_with_changes(self, app, test_contract, test_analysis_result):
        """Test getting analysis result with changes loaded"""
        with app.app_context():
            # Setup
            contract_repo = ContractRepository()
            contract_repo.create_from_domain(test_contract)
            
            analysis_repo = AnalysisRepository()
            analysis_repo.create_from_domain(test_analysis_result)
            
            # Test
            retrieved = analysis_repo.get_with_changes("test_analysis_001")
            assert retrieved is not None
            assert len(retrieved.changes) == 1
            assert retrieved.changes[0].change_id == "change_001"
    
    def test_get_by_contract_id(self, app, test_contract, test_analysis_result):
        """Test getting analysis results by contract ID"""
        with app.app_context():
            # Setup
            contract_repo = ContractRepository()
            contract_repo.create_from_domain(test_contract)
            
            analysis_repo = AnalysisRepository()
            analysis_repo.create_from_domain(test_analysis_result)
            
            # Test
            results = analysis_repo.get_by_contract_id("test_contract_001")
            assert len(results) == 1
            assert results[0].id == "test_analysis_001"
    
    def test_get_by_risk_level(self, app, test_contract, test_analysis_result):
        """Test getting analysis results by risk level"""
        with app.app_context():
            # Setup
            contract_repo = ContractRepository()
            contract_repo.create_from_domain(test_contract)
            
            analysis_repo = AnalysisRepository()
            analysis_repo.create_from_domain(test_analysis_result)
            
            # Test
            results = analysis_repo.get_by_risk_level("MEDIUM")
            assert len(results) == 1
            assert results[0].overall_risk_level == "MEDIUM"
    
    def test_analysis_statistics(self, app, test_contract, test_analysis_result):
        """Test getting analysis statistics"""
        with app.app_context():
            # Setup
            contract_repo = ContractRepository()
            contract_repo.create_from_domain(test_contract)
            
            analysis_repo = AnalysisRepository()
            analysis_repo.create_from_domain(test_analysis_result)
            
            # Test
            stats = analysis_repo.get_analysis_statistics()
            assert stats['total_analyses'] == 1
            assert 'MEDIUM' in stats['risk_distribution']
            assert stats['risk_distribution']['MEDIUM'] == 1


class TestDatabaseIntegrity:
    """Test database integrity and constraints"""
    
    def test_foreign_key_constraint(self, app):
        """Test foreign key constraints are enforced"""
        with app.app_context():
            # Try to create analysis without contract - should fail
            analysis_model = AnalysisResultModel(
                analysis_id="test_analysis",
                contract_id="nonexistent_contract",
                template_id="template_001"
            )
            db.session.add(analysis_model)
            
            with pytest.raises(IntegrityError):
                db.session.commit()
    
    def test_cascade_delete(self, app, test_contract, test_analysis_result):
        """Test cascade delete removes related records"""
        with app.app_context():
            # Setup
            contract_repo = ContractRepository()
            contract_model = contract_repo.create_from_domain(test_contract)
            
            analysis_repo = AnalysisRepository()
            analysis_repo.create_from_domain(test_analysis_result)
            
            # Verify setup
            assert contract_repo.count() == 1
            assert analysis_repo.count() == 1
            
            # Delete contract should cascade to analysis results
            db.session.delete(contract_model)
            db.session.commit()
            
            assert contract_repo.count() == 0
            assert analysis_repo.count() == 0
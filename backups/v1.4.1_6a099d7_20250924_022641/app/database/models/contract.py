"""
Contract database model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from ..database import db


class ContractModel(db.Model):
    """Database model for contracts"""
    
    __tablename__ = 'contracts'
    
    # Primary key
    id = Column(String(50), primary_key=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # Content
    text_content = Column(Text, nullable=True)
    
    # Metadata
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default='uploaded', nullable=False)
    
    # Analysis tracking
    last_analyzed = Column(DateTime, nullable=True)
    analysis_count = Column(Integer, default=0)
    
    # Analysis results (one-to-many relationship)
    analysis_results = relationship('AnalysisResultModel', back_populates='contract', cascade='all, delete-orphan')
    
    def __init__(self, id, filename, original_filename, file_path, file_size, **kwargs):
        self.id = id
        self.filename = filename
        self.original_filename = original_filename
        self.file_path = file_path
        self.file_size = file_size
        
        # Optional fields
        self.text_content = kwargs.get('text_content', '')
        self.upload_timestamp = kwargs.get('upload_timestamp', datetime.utcnow())
        self.status = kwargs.get('status', 'uploaded')
        self.last_analyzed = kwargs.get('last_analyzed')
        self.analysis_count = kwargs.get('analysis_count', 0)
    
    def to_domain_object(self):
        """Convert to domain Contract object"""
        from ...core.models.contract import Contract
        
        contract = Contract(
            id=self.id,
            filename=self.filename,
            original_filename=self.original_filename,
            file_path=self.file_path,
            file_size=self.file_size,
            upload_timestamp=self.upload_timestamp,
            status=self.status
        )
        
        contract.text_content = self.text_content
        contract.last_analyzed = self.last_analyzed
        contract.analysis_count = self.analysis_count
        
        return contract
    
    @classmethod
    def from_domain_object(cls, contract):
        """Create from domain Contract object"""
        return cls(
            id=contract.id,
            filename=contract.filename,
            original_filename=contract.original_filename,
            file_path=contract.file_path,
            file_size=contract.file_size,
            text_content=getattr(contract, 'text_content', ''),
            upload_timestamp=contract.upload_timestamp,
            status=contract.status,
            last_analyzed=getattr(contract, 'last_analyzed', None),
            analysis_count=getattr(contract, 'analysis_count', 0)
        )
    
    def get_summary(self):
        """Get contract summary for API responses"""
        return {
            'id': self.id,
            'filename': self.original_filename,
            'file_size': self.file_size,
            'upload_date': self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            'status': self.status,
            'analysis_count': self.analysis_count,
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None
        }
    
    def __repr__(self):
        return f'<ContractModel {self.id}: {self.original_filename}>'
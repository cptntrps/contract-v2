"""
Analysis result database models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import db


class AnalysisResultModel(db.Model):
    """Database model for analysis results"""
    
    __tablename__ = 'analysis_results'
    
    # Primary key
    id = Column(String(50), primary_key=True)  # analysis_id
    
    # References
    contract_id = Column(String(50), ForeignKey('contracts.id'), nullable=False)
    template_id = Column(String(100), nullable=False)
    
    # Analysis metadata
    analysis_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    analyzer_version = Column(String(20), default='1.3.0', nullable=False)
    
    # Results summary
    total_changes = Column(Integer, default=0)
    similarity_score = Column(Float, default=0.0)
    
    # Risk assessment
    overall_risk_level = Column(String(20), default='LOW')
    risk_explanation = Column(Text, nullable=True)
    
    # Business recommendations (stored as JSON)
    recommendations = Column(JSON, nullable=True)
    
    # Processing metadata
    processing_time_seconds = Column(Float, default=0.0)
    llm_model_used = Column(String(100), nullable=True)
    
    # Additional metadata (stored as JSON)
    analysis_metadata = Column(JSON, nullable=True)
    
    # Relationships
    contract = relationship('ContractModel', back_populates='analysis_results')
    changes = relationship('ChangeModel', back_populates='analysis_result', cascade='all, delete-orphan')
    
    def __init__(self, analysis_id, contract_id, template_id, **kwargs):
        self.id = analysis_id
        self.contract_id = contract_id
        self.template_id = template_id
        
        # Optional fields
        self.analysis_timestamp = kwargs.get('analysis_timestamp', datetime.utcnow())
        self.analyzer_version = kwargs.get('analyzer_version', '1.3.0')
        self.total_changes = kwargs.get('total_changes', 0)
        self.similarity_score = kwargs.get('similarity_score', 0.0)
        self.overall_risk_level = kwargs.get('overall_risk_level', 'LOW')
        self.risk_explanation = kwargs.get('risk_explanation', '')
        self.recommendations = kwargs.get('recommendations', [])
        self.processing_time_seconds = kwargs.get('processing_time_seconds', 0.0)
        self.llm_model_used = kwargs.get('llm_model_used')
        self.analysis_metadata = kwargs.get('metadata', {})
    
    def to_domain_object(self):
        """Convert to domain AnalysisResult object"""
        from ...core.models.analysis_result import AnalysisResult
        
        analysis = AnalysisResult(
            analysis_id=self.id,
            contract_id=self.contract_id,
            template_id=self.template_id,
            analysis_timestamp=self.analysis_timestamp,
            analyzer_version=self.analyzer_version,
            total_changes=self.total_changes,
            similarity_score=self.similarity_score,
            overall_risk_level=self.overall_risk_level,
            risk_explanation=self.risk_explanation or '',
            recommendations=self.recommendations or [],
            processing_time_seconds=self.processing_time_seconds,
            llm_model_used=self.llm_model_used,
            metadata=self.analysis_metadata or {}
        )
        
        # Convert changes
        for change_model in self.changes:
            analysis.add_change(change_model.to_domain_object())
        
        return analysis
    
    @classmethod
    def from_domain_object(cls, analysis_result):
        """Create from domain AnalysisResult object"""
        return cls(
            analysis_id=analysis_result.analysis_id,
            contract_id=analysis_result.contract_id,
            template_id=analysis_result.template_id,
            analysis_timestamp=analysis_result.analysis_timestamp,
            analyzer_version=analysis_result.analyzer_version,
            total_changes=analysis_result.total_changes,
            similarity_score=analysis_result.similarity_score,
            overall_risk_level=analysis_result.overall_risk_level,
            risk_explanation=analysis_result.risk_explanation,
            recommendations=analysis_result.recommendations,
            processing_time_seconds=analysis_result.processing_time_seconds,
            llm_model_used=analysis_result.llm_model_used,
            analysis_metadata=analysis_result.metadata
        )
    
    def get_summary(self):
        """Get analysis summary for API responses"""
        return {
            'analysis_id': self.id,
            'contract_id': self.contract_id,
            'template_id': self.template_id,
            'analysis_date': self.analysis_timestamp.isoformat(),
            'total_changes': self.total_changes,
            'critical_changes': len([c for c in self.changes if c.classification == 'CRITICAL']),
            'significant_changes': len([c for c in self.changes if c.classification == 'SIGNIFICANT']),
            'inconsequential_changes': len([c for c in self.changes if c.classification == 'INCONSEQUENTIAL']),
            'similarity_percentage': round(self.similarity_score * 100, 1),
            'overall_risk_level': self.overall_risk_level,
            'processing_time': self.processing_time_seconds,
            'model_used': self.llm_model_used
        }
    
    def __repr__(self):
        return f'<AnalysisResultModel {self.id}: {self.contract_id}>'


class ChangeModel(db.Model):
    """Database model for individual changes"""
    
    __tablename__ = 'changes'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Change identification
    change_id = Column(String(100), nullable=False)
    change_type = Column(String(50), nullable=False)
    classification = Column(String(50), nullable=False)
    
    # References
    analysis_result_id = Column(String(50), ForeignKey('analysis_results.id'), nullable=False)
    
    # Change content
    deleted_text = Column(Text, default='')
    inserted_text = Column(Text, default='')
    context_before = Column(Text, default='')
    context_after = Column(Text, default='')
    
    # Position information
    line_number = Column(Integer, nullable=True)
    section = Column(String(200), nullable=True)
    
    # Analysis metadata
    explanation = Column(Text, default='')
    confidence_score = Column(Float, default=0.0)
    
    # Risk assessment
    risk_impact = Column(Text, default='')
    recommendation = Column(Text, default='')
    
    # Additional metadata (stored as JSON)
    change_metadata = Column(JSON, nullable=True)
    
    # Relationships
    analysis_result = relationship('AnalysisResultModel', back_populates='changes')
    
    def __init__(self, change_id, change_type, classification, analysis_result_id, **kwargs):
        self.change_id = change_id
        self.change_type = change_type
        self.classification = classification
        self.analysis_result_id = analysis_result_id
        
        # Optional fields
        self.deleted_text = kwargs.get('deleted_text', '')
        self.inserted_text = kwargs.get('inserted_text', '')
        self.context_before = kwargs.get('context_before', '')
        self.context_after = kwargs.get('context_after', '')
        self.line_number = kwargs.get('line_number')
        self.section = kwargs.get('section')
        self.explanation = kwargs.get('explanation', '')
        self.confidence_score = kwargs.get('confidence_score', 0.0)
        self.risk_impact = kwargs.get('risk_impact', '')
        self.recommendation = kwargs.get('recommendation', '')
        self.change_metadata = kwargs.get('metadata', {})
    
    def to_domain_object(self):
        """Convert to domain Change object"""
        from ...core.models.analysis_result import Change, ChangeType, ChangeClassification
        
        return Change(
            change_id=self.change_id,
            change_type=ChangeType(self.change_type),
            classification=ChangeClassification(self.classification),
            deleted_text=self.deleted_text,
            inserted_text=self.inserted_text,
            context_before=self.context_before,
            context_after=self.context_after,
            line_number=self.line_number,
            section=self.section,
            explanation=self.explanation,
            confidence_score=self.confidence_score,
            risk_impact=self.risk_impact,
            recommendation=self.recommendation,
            metadata=self.change_metadata or {}
        )
    
    @classmethod
    def from_domain_object(cls, change, analysis_result_id):
        """Create from domain Change object"""
        return cls(
            change_id=change.change_id,
            change_type=change.change_type.value,
            classification=change.classification.value,
            analysis_result_id=analysis_result_id,
            deleted_text=change.deleted_text,
            inserted_text=change.inserted_text,
            context_before=change.context_before,
            context_after=change.context_after,
            line_number=change.line_number,
            section=change.section,
            explanation=change.explanation,
            confidence_score=change.confidence_score,
            risk_impact=change.risk_impact,
            recommendation=change.recommendation,
            change_metadata=change.metadata
        )
    
    def __repr__(self):
        return f'<ChangeModel {self.change_id}: {self.classification}>'
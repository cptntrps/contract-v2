"""
Analysis Result Domain Model

Represents contract analysis results and change detection.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from ...utils.logging.setup import get_logger

logger = get_logger(__name__)


class ChangeClassification(Enum):
    """Enumeration for change classification levels"""
    CRITICAL = "CRITICAL"
    SIGNIFICANT = "SIGNIFICANT"
    INCONSEQUENTIAL = "INCONSEQUENTIAL"


class ChangeType(Enum):
    """Enumeration for types of changes"""
    INSERTION = "insertion"
    DELETION = "deletion"
    MODIFICATION = "modification"
    REPLACEMENT = "replacement"


@dataclass
class Change:
    """
    Individual change detected in contract analysis
    """
    
    # Change identification
    change_id: str
    change_type: ChangeType
    classification: ChangeClassification
    
    # Change content
    deleted_text: str = ""
    inserted_text: str = ""
    context_before: str = ""
    context_after: str = ""
    
    # Position information
    line_number: Optional[int] = None
    section: Optional[str] = None
    
    # Analysis metadata
    explanation: str = ""
    confidence_score: float = 0.0
    
    # Risk assessment
    risk_impact: str = ""
    recommendation: str = ""
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation"""
        if not self.change_id:
            raise ValueError("Change ID is required")
        
        if not isinstance(self.change_type, ChangeType):
            if isinstance(self.change_type, str):
                self.change_type = ChangeType(self.change_type)
            else:
                raise ValueError("Invalid change type")
        
        if not isinstance(self.classification, ChangeClassification):
            if isinstance(self.classification, str):
                self.classification = ChangeClassification(self.classification)
            else:
                raise ValueError("Invalid classification")
    
    def is_critical(self) -> bool:
        """Check if change is critical"""
        return self.classification == ChangeClassification.CRITICAL
    
    def is_significant(self) -> bool:
        """Check if change is significant"""
        return self.classification == ChangeClassification.SIGNIFICANT
    
    def is_content_change(self) -> bool:
        """Check if this represents actual content changes (not just formatting)"""
        return bool(self.deleted_text.strip() or self.inserted_text.strip())
    
    def get_change_summary(self) -> str:
        """Get a brief summary of the change"""
        if self.change_type == ChangeType.INSERTION:
            return f"Added: {self.inserted_text[:50]}..."
        elif self.change_type == ChangeType.DELETION:
            return f"Removed: {self.deleted_text[:50]}..."
        elif self.change_type == ChangeType.MODIFICATION:
            return f"Changed: {self.deleted_text[:25]}... → {self.inserted_text[:25]}..."
        else:
            return f"Changed: {self.explanation[:50]}..."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert change to dictionary"""
        return {
            "change_id": self.change_id,
            "change_type": self.change_type.value,
            "classification": self.classification.value,
            "deleted_text": self.deleted_text,
            "inserted_text": self.inserted_text,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "line_number": self.line_number,
            "section": self.section,
            "explanation": self.explanation,
            "confidence_score": self.confidence_score,
            "risk_impact": self.risk_impact,
            "recommendation": self.recommendation,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Change":
        """Create change from dictionary"""
        return cls(
            change_id=data["change_id"],
            change_type=ChangeType(data["change_type"]),
            classification=ChangeClassification(data["classification"]),
            deleted_text=data.get("deleted_text", ""),
            inserted_text=data.get("inserted_text", ""),
            context_before=data.get("context_before", ""),
            context_after=data.get("context_after", ""),
            line_number=data.get("line_number"),
            section=data.get("section"),
            explanation=data.get("explanation", ""),
            confidence_score=data.get("confidence_score", 0.0),
            risk_impact=data.get("risk_impact", ""),
            recommendation=data.get("recommendation", ""),
            metadata=data.get("metadata", {})
        )


@dataclass
class AnalysisResult:
    """
    Complete analysis result for a contract comparison
    """
    
    # Analysis identification
    analysis_id: str
    contract_id: str
    template_id: str
    
    # Analysis metadata
    analysis_timestamp: datetime
    analyzer_version: str = "1.1.0"
    
    # Results summary
    total_changes: int = 0
    similarity_score: float = 0.0
    
    # Change breakdown
    changes: List[Change] = field(default_factory=list)
    
    # Risk assessment
    overall_risk_level: str = "LOW"
    risk_explanation: str = ""
    
    # Business recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Processing metadata
    processing_time_seconds: float = 0.0
    llm_model_used: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization calculations"""
        if not self.analysis_id:
            raise ValueError("Analysis ID is required")
        
        # Update totals from changes list
        self.total_changes = len(self.changes)
        
        # Calculate risk level based on changes
        if not self.overall_risk_level or self.overall_risk_level == "LOW":
            self.overall_risk_level = self._calculate_risk_level()
    
    def add_change(self, change: Change):
        """Add a change to the analysis result"""
        self.changes.append(change)
        self.total_changes = len(self.changes)
        
        # Recalculate risk level
        self.overall_risk_level = self._calculate_risk_level()
    
    def get_critical_changes(self) -> List[Change]:
        """Get all critical changes"""
        return [c for c in self.changes if c.is_critical()]
    
    def get_significant_changes(self) -> List[Change]:
        """Get all significant changes"""
        return [c for c in self.changes if c.is_significant()]
    
    def get_inconsequential_changes(self) -> List[Change]:
        """Get all inconsequential changes"""
        return [c for c in self.changes if c.classification == ChangeClassification.INCONSEQUENTIAL]
    
    def get_changes_by_type(self, change_type: ChangeType) -> List[Change]:
        """Get changes by type"""
        return [c for c in self.changes if c.change_type == change_type]
    
    def _calculate_risk_level(self) -> str:
        """
        Calculate overall risk level based on changes using minimum criticality rule
        
        Business Rules:
        - Any critical change = HIGH risk
        - Multiple significant changes = HIGH risk  
        - Some significant changes = MEDIUM risk
        - Only inconsequential = LOW risk
        """
        critical_count = len(self.get_critical_changes())
        significant_count = len(self.get_significant_changes())
        
        if critical_count > 0:
            return "HIGH"
        elif significant_count > 5:
            return "HIGH"
        elif significant_count > 0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_similarity_percentage(self) -> float:
        """Get similarity as percentage"""
        return round(self.similarity_score * 100, 1)
    
    def is_high_risk(self) -> bool:
        """Check if analysis indicates high risk"""
        return self.overall_risk_level == "HIGH"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get analysis summary for API responses"""
        return {
            "analysis_id": self.analysis_id,
            "contract_id": self.contract_id,
            "template_id": self.template_id,
            "analysis_date": self.analysis_timestamp.isoformat(),
            "total_changes": self.total_changes,
            "critical_changes": len(self.get_critical_changes()),
            "significant_changes": len(self.get_significant_changes()),
            "inconsequential_changes": len(self.get_inconsequential_changes()),
            "similarity_percentage": self.get_similarity_percentage(),
            "overall_risk_level": self.overall_risk_level,
            "processing_time": self.processing_time_seconds,
            "model_used": self.llm_model_used
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis result to dictionary for persistence"""
        return {
            "analysis_id": self.analysis_id,
            "contract_id": self.contract_id,
            "template_id": self.template_id,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "analyzer_version": self.analyzer_version,
            "total_changes": self.total_changes,
            "similarity_score": self.similarity_score,
            "changes": [change.to_dict() for change in self.changes],
            "overall_risk_level": self.overall_risk_level,
            "risk_explanation": self.risk_explanation,
            "recommendations": self.recommendations,
            "processing_time_seconds": self.processing_time_seconds,
            "llm_model_used": self.llm_model_used,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        """Create analysis result from dictionary"""
        # Parse timestamp
        analysis_timestamp = datetime.fromisoformat(data["analysis_timestamp"])
        
        # Parse changes
        changes = [Change.from_dict(change_data) for change_data in data.get("changes", [])]
        
        return cls(
            analysis_id=data["analysis_id"],
            contract_id=data["contract_id"],
            template_id=data["template_id"],
            analysis_timestamp=analysis_timestamp,
            analyzer_version=data.get("analyzer_version", "1.1.0"),
            total_changes=data.get("total_changes", 0),
            similarity_score=data.get("similarity_score", 0.0),
            changes=changes,
            overall_risk_level=data.get("overall_risk_level", "LOW"),
            risk_explanation=data.get("risk_explanation", ""),
            recommendations=data.get("recommendations", []),
            processing_time_seconds=data.get("processing_time_seconds", 0.0),
            llm_model_used=data.get("llm_model_used"),
            metadata=data.get("metadata", {})
        )


def create_change_from_diff(
    change_id: str,
    deleted_text: str,
    inserted_text: str,
    explanation: str = "",
    classification: str = "INCONSEQUENTIAL"
) -> Change:
    """
    Create a Change object from diff results
    
    Args:
        change_id: Unique identifier for the change
        deleted_text: Text that was deleted
        inserted_text: Text that was inserted
        explanation: LLM explanation of the change
        classification: Change classification level
        
    Returns:
        Change object
    """
    # Determine change type
    if deleted_text and inserted_text:
        change_type = ChangeType.MODIFICATION
    elif inserted_text:
        change_type = ChangeType.INSERTION
    elif deleted_text:
        change_type = ChangeType.DELETION
    else:
        change_type = ChangeType.MODIFICATION
    
    return Change(
        change_id=change_id,
        change_type=change_type,
        classification=ChangeClassification(classification),
        deleted_text=deleted_text,
        inserted_text=inserted_text,
        explanation=explanation
    )


__all__ = [
    'Change', 
    'AnalysisResult', 
    'ChangeClassification', 
    'ChangeType',
    'create_change_from_diff'
]
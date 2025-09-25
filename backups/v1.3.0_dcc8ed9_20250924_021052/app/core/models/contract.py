"""
Contract Domain Model

Represents contract entities and related business logic.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from ...utils.logging.setup import get_logger

logger = get_logger(__name__)


@dataclass
class Contract:
    """
    Contract domain entity representing an uploaded contract document.
    """
    
    # Core identification
    id: str
    filename: str
    original_filename: str
    
    # File metadata
    file_path: str
    file_size: int
    upload_timestamp: datetime
    
    # Document content
    text_content: Optional[str] = None
    
    # Processing status
    status: str = "uploaded"  # uploaded, processing, analyzed, error
    
    # Analysis metadata
    template_used: Optional[str] = None
    analysis_timestamp: Optional[datetime] = None
    
    # Analysis results
    changes_count: int = 0
    similarity_score: float = 0.0
    risk_level: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        if not self.id:
            raise ValueError("Contract ID is required")
        
        if not self.filename:
            raise ValueError("Contract filename is required")
        
        # Ensure upload timestamp is set
        if not self.upload_timestamp:
            self.upload_timestamp = datetime.now()
    
    @classmethod
    def create_from_upload(
        cls,
        contract_id: str,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int
    ) -> "Contract":
        """
        Create a new contract from file upload
        
        Args:
            contract_id: Unique contract identifier
            filename: Processed filename
            original_filename: Original uploaded filename
            file_path: Path to stored file
            file_size: File size in bytes
            
        Returns:
            New Contract instance
        """
        return cls(
            id=contract_id,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            upload_timestamp=datetime.now(),
            status="uploaded"
        )
    
    def mark_processing(self):
        """Mark contract as being processed"""
        self.status = "processing"
        logger.debug(f"Contract {self.id} marked as processing")
    
    def mark_analyzed(
        self,
        template_used: str,
        changes_count: int,
        similarity_score: float,
        risk_level: str
    ):
        """
        Mark contract as analyzed with results
        
        Args:
            template_used: Template filename used for analysis
            changes_count: Number of changes detected
            similarity_score: Similarity score (0.0 to 1.0)
            risk_level: Risk assessment level
        """
        self.status = "analyzed"
        self.template_used = template_used
        self.analysis_timestamp = datetime.now()
        self.changes_count = changes_count
        self.similarity_score = similarity_score
        self.risk_level = risk_level
        
        logger.info(f"Contract {self.id} analysis completed - Changes: {changes_count}, Risk: {risk_level}")
    
    def mark_error(self, error_message: str):
        """
        Mark contract as having an error
        
        Args:
            error_message: Error description
        """
        self.status = "error"
        self.metadata["error_message"] = error_message
        self.metadata["error_timestamp"] = datetime.now().isoformat()
        
        logger.error(f"Contract {self.id} marked as error: {error_message}")
    
    def is_analyzed(self) -> bool:
        """Check if contract has been analyzed"""
        return self.status == "analyzed" and self.analysis_timestamp is not None
    
    def is_high_risk(self) -> bool:
        """Check if contract is high risk"""
        return self.risk_level == "HIGH"
    
    def get_age_days(self) -> int:
        """Get age of contract in days since upload"""
        return (datetime.now() - self.upload_timestamp).days
    
    def get_file_extension(self) -> str:
        """Get file extension"""
        return Path(self.filename).suffix.lower()
    
    def get_display_name(self) -> str:
        """Get display name for UI"""
        return self.original_filename or self.filename
    
    def get_summary(self) -> Dict[str, Any]:
        """Get contract summary for API responses"""
        return {
            "id": self.id,
            "filename": self.get_display_name(),
            "status": self.status,
            "upload_date": self.upload_timestamp.isoformat(),
            "analysis_date": self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            "template_used": self.template_used,
            "changes_count": self.changes_count,
            "similarity_score": round(self.similarity_score * 100, 1) if self.similarity_score else 0,
            "risk_level": self.risk_level,
            "file_size": self.file_size,
            "age_days": self.get_age_days()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary for persistence"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "upload_timestamp": self.upload_timestamp.isoformat(),
            "text_content": self.text_content,
            "status": self.status,
            "template_used": self.template_used,
            "analysis_timestamp": self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            "changes_count": self.changes_count,
            "similarity_score": self.similarity_score,
            "risk_level": self.risk_level,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contract":
        """Create contract from dictionary"""
        # Parse timestamps
        upload_timestamp = datetime.fromisoformat(data["upload_timestamp"])
        analysis_timestamp = None
        if data.get("analysis_timestamp"):
            analysis_timestamp = datetime.fromisoformat(data["analysis_timestamp"])
        
        return cls(
            id=data["id"],
            filename=data["filename"],
            original_filename=data["original_filename"],
            file_path=data["file_path"],
            file_size=data["file_size"],
            upload_timestamp=upload_timestamp,
            text_content=data.get("text_content"),
            status=data.get("status", "uploaded"),
            template_used=data.get("template_used"),
            analysis_timestamp=analysis_timestamp,
            changes_count=data.get("changes_count", 0),
            similarity_score=data.get("similarity_score", 0.0),
            risk_level=data.get("risk_level"),
            metadata=data.get("metadata", {})
        )


def validate_contract_file(file_path: str) -> bool:
    """
    Validate that a contract file exists and is accessible
    
    Args:
        file_path: Path to contract file
        
    Returns:
        True if file is valid
    """
    try:
        path = Path(file_path)
        return path.exists() and path.is_file() and path.suffix.lower() in ['.docx', '.doc']
    except Exception:
        return False


__all__ = ['Contract', 'validate_contract_file']
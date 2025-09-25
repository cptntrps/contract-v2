"""
Document domain model representing a processed document
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class Document:
    """
    Represents a processed document with extracted text and metadata
    
    Attributes:
        document_id: Unique identifier for the document
        filename: Original filename
        content: Extracted text content
        sections: List of document sections
        metadata: Document metadata (author, title, etc.)
        upload_timestamp: When document was uploaded
        file_type: Type of file (docx, pdf, txt)
        file_size: Size of original file in bytes
    """
    document_id: str
    filename: str
    content: str
    sections: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    upload_timestamp: datetime = field(default_factory=datetime.now)
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary representation"""
        return {
            'document_id': self.document_id,
            'filename': self.filename,
            'content': self.content,
            'sections': self.sections,
            'metadata': self.metadata,
            'upload_timestamp': self.upload_timestamp.isoformat(),
            'file_type': self.file_type,
            'file_size': self.file_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create Document instance from dictionary"""
        upload_timestamp = data.get('upload_timestamp')
        if isinstance(upload_timestamp, str):
            upload_timestamp = datetime.fromisoformat(upload_timestamp)
        elif not isinstance(upload_timestamp, datetime):
            upload_timestamp = datetime.now()
        
        return cls(
            document_id=data.get('document_id', ''),
            filename=data.get('filename', ''),
            content=data.get('content', ''),
            sections=data.get('sections', []),
            metadata=data.get('metadata', {}),
            upload_timestamp=upload_timestamp,
            file_type=data.get('file_type'),
            file_size=data.get('file_size')
        )
    
    def get_word_count(self) -> int:
        """Get word count of document content"""
        return len(self.content.split()) if self.content else 0
    
    def get_section_count(self) -> int:
        """Get number of sections in document"""
        return len(self.sections)
    
    def has_metadata(self, key: str) -> bool:
        """Check if metadata key exists"""
        return key in self.metadata
    
    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """Get metadata value with optional default"""
        return self.metadata.get(key, default)
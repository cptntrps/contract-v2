"""
Change domain model representing a single change between documents
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Change:
    """
    Represents a single change between original and modified text
    
    Attributes:
        operation: Type of change (insert, delete, replace)
        original_text: Text from original document (for delete/replace)
        modified_text: Text from modified document (for insert/replace)
        position: Position in document where change occurs
        context: Surrounding context for the change
    """
    operation: str
    original_text: Optional[str] = None
    modified_text: Optional[str] = None
    position: int = 0
    context: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert change to dictionary representation"""
        return {
            'operation': self.operation,
            'original_text': self.original_text,
            'modified_text': self.modified_text,
            'position': self.position,
            'context': self.context
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Change':
        """Create Change instance from dictionary"""
        return cls(
            operation=data.get('operation', 'unknown'),
            original_text=data.get('original_text'),
            modified_text=data.get('modified_text'),
            position=data.get('position', 0),
            context=data.get('context')
        )
    
    def __str__(self) -> str:
        """String representation of change"""
        if self.operation == 'insert':
            return f"Insert: '{self.modified_text}' at position {self.position}"
        elif self.operation == 'delete':
            return f"Delete: '{self.original_text}' at position {self.position}"
        elif self.operation == 'replace':
            return f"Replace: '{self.original_text}' -> '{self.modified_text}' at position {self.position}"
        else:
            return f"{self.operation}: at position {self.position}"
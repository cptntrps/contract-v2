"""
Base repository class with common database operations
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict
from sqlalchemy.exc import SQLAlchemyError
from ..database import db
from ...utils.logging.setup import get_logger

logger = get_logger(__name__)


class RepositoryError(Exception):
    """Exception raised for repository operation errors"""
    pass


class BaseRepository(ABC):
    """Abstract base repository class"""
    
    def __init__(self, model_class):
        self.model_class = model_class
        self.db = db
    
    def create(self, **kwargs) -> Any:
        """Create a new record"""
        try:
            instance = self.model_class(**kwargs)
            self.db.session.add(instance)
            self.db.session.commit()
            logger.debug(f"Created {self.model_class.__name__}: {instance}")
            return instance
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to create {self.model_class.__name__}: {e}")
    
    def get_by_id(self, id: str) -> Optional[Any]:
        """Get record by ID"""
        try:
            return self.db.session.get(self.model_class, id)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving {self.model_class.__name__} by ID {id}: {e}")
            raise RepositoryError(f"Failed to retrieve {self.model_class.__name__}: {e}")
    
    def get_all(self) -> List[Any]:
        """Get all records"""
        try:
            return self.db.session.query(self.model_class).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving all {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to retrieve {self.model_class.__name__} records: {e}")
    
    def update(self, id: str, **kwargs) -> Optional[Any]:
        """Update record by ID"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None
            
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            self.db.session.commit()
            logger.debug(f"Updated {self.model_class.__name__}: {instance}")
            return instance
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error updating {self.model_class.__name__} {id}: {e}")
            raise RepositoryError(f"Failed to update {self.model_class.__name__}: {e}")
    
    def delete(self, id: str) -> bool:
        """Delete record by ID"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False
            
            self.db.session.delete(instance)
            self.db.session.commit()
            logger.debug(f"Deleted {self.model_class.__name__}: {id}")
            return True
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error deleting {self.model_class.__name__} {id}: {e}")
            raise RepositoryError(f"Failed to delete {self.model_class.__name__}: {e}")
    
    def count(self) -> int:
        """Count total records"""
        try:
            return self.db.session.query(self.model_class).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to count {self.model_class.__name__} records: {e}")
    
    def exists(self, id: str) -> bool:
        """Check if record exists by ID"""
        try:
            return self.db.session.query(
                self.db.session.query(self.model_class).filter_by(id=id).exists()
            ).scalar()
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model_class.__name__} {id}: {e}")
            raise RepositoryError(f"Failed to check {self.model_class.__name__} existence: {e}")
    
    def bulk_create(self, items: List[Dict[str, Any]]) -> List[Any]:
        """Create multiple records"""
        try:
            instances = [self.model_class(**item) for item in items]
            self.db.session.add_all(instances)
            self.db.session.commit()
            logger.debug(f"Bulk created {len(instances)} {self.model_class.__name__} records")
            return instances
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error bulk creating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to bulk create {self.model_class.__name__}: {e}")
"""
Contract repository for database operations
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError

from .base_repository import BaseRepository, RepositoryError
from ..models.contract import ContractModel
from ...utils.logging.setup import get_logger

logger = get_logger(__name__)


class ContractRepository(BaseRepository):
    """Repository for contract database operations"""
    
    def __init__(self):
        super().__init__(ContractModel)
    
    def create_from_domain(self, contract) -> ContractModel:
        """Create contract from domain object"""
        try:
            contract_model = ContractModel.from_domain_object(contract)
            self.db.session.add(contract_model)
            self.db.session.commit()
            logger.info(f"Created contract in database: {contract.id}")
            return contract_model
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error creating contract {contract.id}: {e}")
            raise RepositoryError(f"Failed to create contract: {e}")
    
    def get_by_filename(self, filename: str) -> Optional[ContractModel]:
        """Get contract by original filename"""
        try:
            return self.db.session.query(ContractModel)\
                .filter_by(original_filename=filename)\
                .first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving contract by filename {filename}: {e}")
            raise RepositoryError(f"Failed to retrieve contract: {e}")
    
    def get_recent(self, limit: int = 10) -> List[ContractModel]:
        """Get most recently uploaded contracts"""
        try:
            return self.db.session.query(ContractModel)\
                .order_by(desc(ContractModel.upload_timestamp))\
                .limit(limit)\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving recent contracts: {e}")
            raise RepositoryError(f"Failed to retrieve recent contracts: {e}")
    
    def get_by_status(self, status: str) -> List[ContractModel]:
        """Get contracts by status"""
        try:
            return self.db.session.query(ContractModel)\
                .filter_by(status=status)\
                .order_by(desc(ContractModel.upload_timestamp))\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving contracts by status {status}: {e}")
            raise RepositoryError(f"Failed to retrieve contracts: {e}")
    
    def update_analysis_tracking(self, contract_id: str, template_used: str = None) -> bool:
        """Update contract analysis tracking"""
        try:
            contract = self.get_by_id(contract_id)
            if not contract:
                return False
            
            contract.analysis_count += 1
            contract.last_analyzed = datetime.utcnow()
            contract.status = 'analyzed'
            
            self.db.session.commit()
            logger.debug(f"Updated analysis tracking for contract {contract_id}")
            return True
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error updating analysis tracking for {contract_id}: {e}")
            raise RepositoryError(f"Failed to update contract: {e}")
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get contract analysis statistics"""
        try:
            total_contracts = self.count()
            analyzed_contracts = self.db.session.query(ContractModel)\
                .filter(ContractModel.analysis_count > 0)\
                .count()
            
            recent_contracts = self.db.session.query(ContractModel)\
                .filter(ContractModel.upload_timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))\
                .count()
            
            return {
                'total_contracts': total_contracts,
                'analyzed_contracts': analyzed_contracts,
                'recent_contracts': recent_contracts,
                'analysis_percentage': round((analyzed_contracts / total_contracts * 100) if total_contracts > 0 else 0, 1)
            }
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving analysis stats: {e}")
            raise RepositoryError(f"Failed to retrieve analysis stats: {e}")
    
    def search_contracts(self, query: str) -> List[ContractModel]:
        """Search contracts by filename or ID"""
        try:
            search_pattern = f"%{query}%"
            return self.db.session.query(ContractModel)\
                .filter(
                    ContractModel.original_filename.ilike(search_pattern) |
                    ContractModel.id.ilike(search_pattern)
                )\
                .order_by(desc(ContractModel.upload_timestamp))\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching contracts with query '{query}': {e}")
            raise RepositoryError(f"Failed to search contracts: {e}")
    
    def get_contracts_with_analysis(self) -> List[ContractModel]:
        """Get contracts that have been analyzed"""
        try:
            return self.db.session.query(ContractModel)\
                .filter(ContractModel.analysis_count > 0)\
                .order_by(desc(ContractModel.last_analyzed))\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving analyzed contracts: {e}")
            raise RepositoryError(f"Failed to retrieve analyzed contracts: {e}")
    
    def clear_all_contracts(self) -> int:
        """Clear all contracts (development/admin function)"""
        try:
            count = self.count()
            self.db.session.query(ContractModel).delete()
            self.db.session.commit()
            logger.info(f"Cleared {count} contracts from database")
            return count
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error clearing all contracts: {e}")
            raise RepositoryError(f"Failed to clear contracts: {e}")
    
    def migrate_from_memory_store(self, contracts_store: Dict[str, Any]) -> int:
        """Migrate contracts from in-memory store to database"""
        migrated_count = 0
        try:
            for contract_id, contract in contracts_store.items():
                if not self.exists(contract_id):
                    self.create_from_domain(contract)
                    migrated_count += 1
            
            logger.info(f"Migrated {migrated_count} contracts to database")
            return migrated_count
        except Exception as e:
            logger.error(f"Error migrating contracts: {e}")
            raise RepositoryError(f"Failed to migrate contracts: {e}")
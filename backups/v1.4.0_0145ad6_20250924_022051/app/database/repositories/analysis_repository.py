"""
Analysis repository for database operations
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from .base_repository import BaseRepository, RepositoryError
from ..models.analysis_result import AnalysisResultModel, ChangeModel
from ...utils.logging.setup import get_logger

logger = get_logger(__name__)


class AnalysisRepository(BaseRepository):
    """Repository for analysis result database operations"""
    
    def __init__(self):
        super().__init__(AnalysisResultModel)
    
    def create_from_domain(self, analysis_result) -> AnalysisResultModel:
        """Create analysis result from domain object"""
        try:
            # Create analysis result model
            analysis_model = AnalysisResultModel.from_domain_object(analysis_result)
            self.db.session.add(analysis_model)
            
            # Create change models
            for change in analysis_result.changes:
                change_model = ChangeModel.from_domain_object(change, analysis_result.analysis_id)
                self.db.session.add(change_model)
            
            self.db.session.commit()
            logger.info(f"Created analysis result in database: {analysis_result.analysis_id}")
            return analysis_model
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error creating analysis result {analysis_result.analysis_id}: {e}")
            raise RepositoryError(f"Failed to create analysis result: {e}")
    
    def get_by_contract_id(self, contract_id: str) -> List[AnalysisResultModel]:
        """Get all analysis results for a contract"""
        try:
            return self.db.session.query(AnalysisResultModel)\
                .options(joinedload(AnalysisResultModel.changes))\
                .filter_by(contract_id=contract_id)\
                .order_by(desc(AnalysisResultModel.analysis_timestamp))\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving analysis results for contract {contract_id}: {e}")
            raise RepositoryError(f"Failed to retrieve analysis results: {e}")
    
    def get_with_changes(self, analysis_id: str) -> Optional[AnalysisResultModel]:
        """Get analysis result with all changes loaded"""
        try:
            return self.db.session.query(AnalysisResultModel)\
                .options(joinedload(AnalysisResultModel.changes))\
                .filter_by(id=analysis_id)\
                .first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving analysis result with changes {analysis_id}: {e}")
            raise RepositoryError(f"Failed to retrieve analysis result: {e}")
    
    def get_recent(self, limit: int = 10) -> List[AnalysisResultModel]:
        """Get most recent analysis results"""
        try:
            return self.db.session.query(AnalysisResultModel)\
                .options(joinedload(AnalysisResultModel.changes))\
                .order_by(desc(AnalysisResultModel.analysis_timestamp))\
                .limit(limit)\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving recent analysis results: {e}")
            raise RepositoryError(f"Failed to retrieve recent analysis results: {e}")
    
    def get_by_risk_level(self, risk_level: str) -> List[AnalysisResultModel]:
        """Get analysis results by risk level"""
        try:
            return self.db.session.query(AnalysisResultModel)\
                .filter_by(overall_risk_level=risk_level)\
                .order_by(desc(AnalysisResultModel.analysis_timestamp))\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving analysis results by risk level {risk_level}: {e}")
            raise RepositoryError(f"Failed to retrieve analysis results: {e}")
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        try:
            total_analyses = self.count()
            
            # Risk level distribution
            risk_stats = self.db.session.query(
                AnalysisResultModel.overall_risk_level,
                func.count(AnalysisResultModel.id)
            ).group_by(AnalysisResultModel.overall_risk_level).all()
            
            # Recent analyses (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_analyses = self.db.session.query(AnalysisResultModel)\
                .filter(AnalysisResultModel.analysis_timestamp >= recent_cutoff)\
                .count()
            
            # Average processing time
            avg_processing_time = self.db.session.query(
                func.avg(AnalysisResultModel.processing_time_seconds)
            ).scalar() or 0
            
            # Average similarity score
            avg_similarity = self.db.session.query(
                func.avg(AnalysisResultModel.similarity_score)
            ).scalar() or 0
            
            return {
                'total_analyses': total_analyses,
                'risk_distribution': {level: count for level, count in risk_stats},
                'recent_analyses': recent_analyses,
                'average_processing_time': round(avg_processing_time, 2),
                'average_similarity': round(avg_similarity * 100, 1)
            }
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving analysis statistics: {e}")
            raise RepositoryError(f"Failed to retrieve analysis statistics: {e}")
    
    def search_analyses(self, query: str) -> List[AnalysisResultModel]:
        """Search analysis results by contract ID or template ID"""
        try:
            search_pattern = f"%{query}%"
            return self.db.session.query(AnalysisResultModel)\
                .filter(
                    AnalysisResultModel.contract_id.ilike(search_pattern) |
                    AnalysisResultModel.template_id.ilike(search_pattern)
                )\
                .order_by(desc(AnalysisResultModel.analysis_timestamp))\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching analysis results with query '{query}': {e}")
            raise RepositoryError(f"Failed to search analysis results: {e}")
    
    def get_changes_by_classification(self, classification: str) -> List[ChangeModel]:
        """Get all changes by classification level"""
        try:
            return self.db.session.query(ChangeModel)\
                .filter_by(classification=classification)\
                .join(AnalysisResultModel)\
                .order_by(desc(AnalysisResultModel.analysis_timestamp))\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving changes by classification {classification}: {e}")
            raise RepositoryError(f"Failed to retrieve changes: {e}")
    
    def clear_old_analyses(self, days_old: int = 30) -> int:
        """Clear analysis results older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            old_analyses = self.db.session.query(AnalysisResultModel)\
                .filter(AnalysisResultModel.analysis_timestamp < cutoff_date)\
                .all()
            
            count = len(old_analyses)
            for analysis in old_analyses:
                self.db.session.delete(analysis)
            
            self.db.session.commit()
            logger.info(f"Cleared {count} old analysis results")
            return count
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error clearing old analysis results: {e}")
            raise RepositoryError(f"Failed to clear old analyses: {e}")
    
    def migrate_from_memory_store(self, analysis_store: Dict[str, Any]) -> int:
        """Migrate analysis results from in-memory store to database"""
        migrated_count = 0
        try:
            for analysis_id, analysis in analysis_store.items():
                if not self.exists(analysis_id):
                    self.create_from_domain(analysis)
                    migrated_count += 1
            
            logger.info(f"Migrated {migrated_count} analysis results to database")
            return migrated_count
        except Exception as e:
            logger.error(f"Error migrating analysis results: {e}")
            raise RepositoryError(f"Failed to migrate analysis results: {e}")
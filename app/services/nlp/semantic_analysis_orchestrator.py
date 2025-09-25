"""
Semantic Analysis Orchestrator - Domain Layer

Coordinates semantic analysis workflow using specialized services.
Following architectural standards: single responsibility, comprehensive documentation.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .entity_extraction_service import EntityExtractionService, ExtractedEntity
from .risk_assessment_service import RiskAssessmentService, RiskAssessment

logger = logging.getLogger(__name__)


@dataclass
class SemanticAnalysisResult:
    """Complete semantic analysis results."""
    entities: List[ExtractedEntity]
    risk_assessment: RiskAssessment
    semantic_similarity: float
    analysis_insights: List[str]
    processing_metadata: Dict[str, Any]


class SemanticAnalysisOrchestrator:
    """
    Orchestrates comprehensive semantic analysis using specialized services.
    
    Purpose: Coordinates entity extraction, risk assessment, and semantic analysis
    workflows. Provides unified interface for semantic understanding of contract
    documents while maintaining clear separation of concerns.
    
    AI Context: This orchestrator coordinates multiple semantic analysis services.
    When debugging semantic analysis issues, check individual service logs first,
    then examine orchestration logic here. This class handles workflow coordination
    but delegates actual analysis to specialized services.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize semantic analysis orchestrator.
        
        Args:
            config: Configuration for semantic analysis components
        """
        self.config = config or {}
        
        # Initialize specialized services
        self.entity_service = EntityExtractionService(config.get('entity_extraction', {}))
        self.risk_service = RiskAssessmentService(config.get('risk_assessment', {}))
        
        logger.info("Semantic analysis orchestrator initialized")
    
    def analyze_semantic_changes(
        self,
        original_text: str,
        modified_text: str,
        changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze semantic impact of changes between contract versions.
        
        Purpose: Provides comprehensive semantic analysis of contract changes
        including entity impact, risk implications, and semantic similarity.
        Orchestrates multiple analysis services for complete understanding.
        
        Args:
            original_text: Original contract text
            modified_text: Modified contract text  
            changes: List of detected changes with metadata
            
        Returns:
            Dict[str, Any]: Complete semantic analysis results containing:
                - entities: Entity extraction results for both versions
                - risk_assessment: Risk analysis of changes and content
                - semantic_similarity: Similarity score between versions
                - change_impacts: Semantic impact analysis of each change
                - insights: High-level semantic insights and recommendations
        
        Raises:
            SemanticAnalysisError: If semantic analysis workflow fails
        
        AI Context: Primary semantic analysis orchestration function. Coordinates
        entity extraction and risk assessment services. For debugging, check
        individual service logs first, then orchestration workflow here.
        """
        try:
            logger.info("Starting comprehensive semantic change analysis")
            analysis_start_time = datetime.now()
            
            # Extract entities from both versions
            logger.debug("Extracting entities from original text")
            original_entities = self.entity_service.extract_entities(original_text)
            
            logger.debug("Extracting entities from modified text")
            modified_entities = self.entity_service.extract_entities(modified_text)
            
            # Perform risk assessment on modified contract with changes
            logger.debug("Performing risk assessment")
            risk_assessment = self.risk_service.assess_contract_risks(modified_text, changes)
            
            # Calculate semantic similarity between versions
            logger.debug("Calculating semantic similarity")
            semantic_similarity = self._calculate_semantic_similarity(original_text, modified_text)
            
            # Analyze change impacts
            logger.debug("Analyzing individual change impacts")
            change_impacts = self._analyze_change_impacts(changes, original_text, modified_text)
            
            # Generate semantic insights
            logger.debug("Generating semantic insights")
            insights = self._generate_semantic_insights(
                original_entities, modified_entities, risk_assessment, changes
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - analysis_start_time).total_seconds()
            
            # Compile comprehensive results
            analysis_results = {
                'entities': {
                    'original': [self._entity_to_dict(e) for e in original_entities],
                    'modified': [self._entity_to_dict(e) for e in modified_entities],
                    'entity_changes': self._compare_entities(original_entities, modified_entities)
                },
                'risk_assessment': {
                    'overall_risk_level': risk_assessment.overall_risk_level.value,
                    'risk_score': risk_assessment.risk_score,
                    'identified_risks': [self._risk_indicator_to_dict(r) for r in risk_assessment.identified_risks],
                    'risk_summary': risk_assessment.risk_summary,
                    'recommendations': risk_assessment.recommendations
                },
                'semantic_similarity': semantic_similarity,
                'change_impacts': change_impacts,
                'semantic_insights': insights,
                'analysis_metadata': {
                    'processing_time_seconds': processing_time,
                    'original_text_length': len(original_text),
                    'modified_text_length': len(modified_text),
                    'changes_analyzed': len(changes),
                    'entities_found': {
                        'original': len(original_entities),
                        'modified': len(modified_entities)
                    },
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            
            logger.info(f"Semantic analysis completed in {processing_time:.2f}s")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Semantic change analysis failed: {e}")
            raise SemanticAnalysisError(f"Semantic analysis failed: {str(e)}")
    
    def analyze_contract_semantic_content(self, contract_text: str) -> Dict[str, Any]:
        """
        Analyze semantic content of a single contract.
        
        Purpose: Provides semantic analysis of contract content without change
        comparison. Useful for initial contract assessment and understanding.
        
        Args:
            contract_text: Full contract text to analyze
        
        Returns:
            Dict[str, Any]: Semantic analysis results
        
        AI Context: Single contract semantic analysis. Use this for analyzing
        contracts without comparison to other versions. Results include entities,
        risks, and semantic patterns.
        """
        try:
            logger.info("Starting single contract semantic analysis")
            
            # Extract entities
            entities = self.entity_service.extract_entities(contract_text)
            
            # Assess risks
            risk_assessment = self.risk_service.assess_contract_risks(contract_text)
            
            # Generate content insights
            insights = self._generate_content_insights(entities, risk_assessment)
            
            results = {
                'entities': [self._entity_to_dict(e) for e in entities],
                'risk_assessment': {
                    'overall_risk_level': risk_assessment.overall_risk_level.value,
                    'risk_score': risk_assessment.risk_score,
                    'identified_risks': [self._risk_indicator_to_dict(r) for r in risk_assessment.identified_risks],
                    'risk_summary': risk_assessment.risk_summary,
                    'recommendations': risk_assessment.recommendations
                },
                'content_insights': insights,
                'analysis_metadata': {
                    'text_length': len(contract_text),
                    'entities_found': len(entities),
                    'analysis_type': 'single_contract',
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            
            logger.info(f"Single contract analysis completed: {len(entities)} entities, {risk_assessment.overall_risk_level.value} risk")
            return results
            
        except Exception as e:
            logger.error(f"Single contract semantic analysis failed: {e}")
            raise SemanticAnalysisError(f"Contract semantic analysis failed: {str(e)}")
    
    def _calculate_semantic_similarity(self, original_text: str, modified_text: str) -> float:
        """
        Calculate semantic similarity between two contract versions.
        
        Args:
            original_text: Original contract text
            modified_text: Modified contract text
        
        Returns:
            float: Similarity score between 0.0 and 1.0
        
        AI Context: Basic semantic similarity calculation using word overlap.
        For production, consider implementing more sophisticated similarity
        measures using embeddings or NLP models.
        """
        try:
            if not original_text or not modified_text:
                return 0.0
            
            # Simple word-based similarity (Jaccard similarity)
            original_words = set(original_text.lower().split())
            modified_words = set(modified_text.lower().split())
            
            intersection = len(original_words.intersection(modified_words))
            union = len(original_words.union(modified_words))
            
            similarity = intersection / union if union > 0 else 0.0
            
            logger.debug(f"Semantic similarity calculated: {similarity:.3f}")
            return similarity
            
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return 0.0
    
    def _analyze_change_impacts(self, changes: List[Dict], original_text: str, modified_text: str) -> List[Dict[str, Any]]:
        """Analyze semantic impact of each individual change."""
        change_impacts = []
        
        for change in changes:
            try:
                # Get change-specific risk assessment
                change_risks = self.risk_service.assess_change_risk(change, modified_text)
                
                # Analyze entity impact
                change_text = f"{change.get('original', '')} {change.get('modified', '')}"
                affected_entities = self.entity_service.extract_entities(change_text)
                
                impact_analysis = {
                    'change_id': change.get('id', 'unknown'),
                    'change_type': change.get('type', 'unknown'),
                    'semantic_impact_level': self._assess_change_impact_level(change_risks, affected_entities),
                    'affected_entities': [self._entity_to_dict(e) for e in affected_entities],
                    'identified_risks': [self._risk_indicator_to_dict(r) for r in change_risks],
                    'impact_description': self._generate_change_impact_description(change, change_risks, affected_entities)
                }
                
                change_impacts.append(impact_analysis)
                
            except Exception as e:
                logger.warning(f"Failed to analyze impact for change {change.get('id')}: {e}")
                continue
        
        return change_impacts
    
    def _assess_change_impact_level(self, risks, entities) -> str:
        """Assess the overall impact level of a change."""
        high_risk_count = len([r for r in risks if r.risk_level.value in ['high', 'critical']])
        critical_entities = len([e for e in entities if e.entity_type in ['MONEY', 'DATE', 'PARTY']])
        
        if high_risk_count > 0 or critical_entities > 2:
            return 'HIGH'
        elif len(risks) > 0 or critical_entities > 0:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_change_impact_description(self, change, risks, entities) -> str:
        """Generate human-readable description of change impact."""
        descriptions = []
        
        if risks:
            descriptions.append(f"Introduces {len(risks)} risk indicators")
        
        if entities:
            entity_types = [e.entity_type for e in entities]
            unique_types = list(set(entity_types))
            descriptions.append(f"Affects {len(entities)} entities ({', '.join(unique_types)})")
        
        change_type = change.get('type', 'modification')
        if change_type == 'addition':
            descriptions.append("Adds new contract terms")
        elif change_type == 'deletion':
            descriptions.append("Removes existing terms")
        else:
            descriptions.append("Modifies existing terms")
        
        return '. '.join(descriptions) if descriptions else 'Minimal semantic impact detected'
    
    def _compare_entities(self, original_entities: List[ExtractedEntity], modified_entities: List[ExtractedEntity]) -> Dict[str, Any]:
        """Compare entities between contract versions."""
        original_by_type = {}
        modified_by_type = {}
        
        for entity in original_entities:
            if entity.entity_type not in original_by_type:
                original_by_type[entity.entity_type] = []
            original_by_type[entity.entity_type].append(entity.text)
        
        for entity in modified_entities:
            if entity.entity_type not in modified_by_type:
                modified_by_type[entity.entity_type] = []
            modified_by_type[entity.entity_type].append(entity.text)
        
        changes = {
            'added_entities': {},
            'removed_entities': {},
            'entity_type_changes': {}
        }
        
        all_types = set(original_by_type.keys()) | set(modified_by_type.keys())
        
        for entity_type in all_types:
            original_set = set(original_by_type.get(entity_type, []))
            modified_set = set(modified_by_type.get(entity_type, []))
            
            added = modified_set - original_set
            removed = original_set - modified_set
            
            if added:
                changes['added_entities'][entity_type] = list(added)
            if removed:
                changes['removed_entities'][entity_type] = list(removed)
            
            changes['entity_type_changes'][entity_type] = {
                'original_count': len(original_set),
                'modified_count': len(modified_set),
                'net_change': len(modified_set) - len(original_set)
            }
        
        return changes
    
    def _generate_semantic_insights(self, original_entities, modified_entities, risk_assessment, changes) -> List[str]:
        """Generate high-level semantic insights."""
        insights = []
        
        # Entity-based insights
        entity_changes = self._compare_entities(original_entities, modified_entities)
        
        if entity_changes['added_entities']:
            added_types = list(entity_changes['added_entities'].keys())
            insights.append(f"New entities added: {', '.join(added_types)}")
        
        if entity_changes['removed_entities']:
            removed_types = list(entity_changes['removed_entities'].keys())
            insights.append(f"Entities removed: {', '.join(removed_types)}")
        
        # Risk-based insights
        high_risks = [r for r in risk_assessment.identified_risks if r.risk_level.value in ['high', 'critical']]
        if high_risks:
            risk_types = list(set(r.risk_type for r in high_risks))
            insights.append(f"High-risk areas identified: {', '.join(risk_types)}")
        
        # Change pattern insights
        change_types = [c.get('type', 'unknown') for c in changes]
        if 'deletion' in change_types:
            insights.append("Contract contains deletions - review for removed protections")
        
        if 'addition' in change_types:
            insights.append("Contract contains additions - review for new obligations")
        
        if not insights:
            insights.append("No significant semantic patterns detected")
        
        return insights
    
    def _generate_content_insights(self, entities, risk_assessment) -> List[str]:
        """Generate insights for single contract analysis."""
        insights = []
        
        # Entity insights
        entity_types = [e.entity_type for e in entities]
        entity_counts = {}
        for entity_type in entity_types:
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        if entity_counts:
            top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            insights.append(f"Primary entity types: {', '.join([f'{t}({c})' for t, c in top_entities])}")
        
        # Risk insights
        if risk_assessment.overall_risk_level.value != 'low':
            insights.append(f"Contract has {risk_assessment.overall_risk_level.value} risk level")
        
        high_risks = [r for r in risk_assessment.identified_risks if r.risk_level.value in ['high', 'critical']]
        if high_risks:
            insights.append(f"{len(high_risks)} high-priority risks require attention")
        
        if not insights:
            insights.append("Standard contract structure with typical risk profile")
        
        return insights
    
    def _entity_to_dict(self, entity: ExtractedEntity) -> Dict[str, Any]:
        """Convert ExtractedEntity to dictionary for JSON serialization."""
        return {
            'entity_type': entity.entity_type,
            'text': entity.text,
            'confidence': entity.confidence,
            'start_position': entity.start_position,
            'end_position': entity.end_position,
            'context': entity.context,
            'metadata': entity.metadata
        }
    
    def _risk_indicator_to_dict(self, risk) -> Dict[str, Any]:
        """Convert RiskIndicator to dictionary for JSON serialization."""
        return {
            'risk_type': risk.risk_type,
            'risk_level': risk.risk_level.value,
            'description': risk.description,
            'confidence': risk.confidence,
            'evidence': risk.evidence,
            'mitigation_suggestions': risk.mitigation_suggestions,
            'metadata': risk.metadata
        }


class SemanticAnalysisError(Exception):
    """Exception raised when semantic analysis fails."""
    pass
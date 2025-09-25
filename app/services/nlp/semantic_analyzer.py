"""
Semantic Analysis Facade - Domain Layer

Provides backward compatibility wrapper for the semantic analysis orchestrator.
Following architectural standards: facade pattern, delegation to specialized services.
"""

import logging
from typing import Dict, List, Any, Optional

from .semantic_analysis_orchestrator import SemanticAnalysisOrchestrator, SemanticAnalysisError

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    """
    Backward compatibility facade for semantic analysis functionality.
    
    Purpose: Maintains compatibility with existing code while delegating all
    semantic analysis work to the new orchestrator-based architecture. This
    facade ensures existing integrations continue working without changes.
    
    AI Context: This is a compatibility wrapper around SemanticAnalysisOrchestrator.
    All new features should be implemented in the orchestrator and specialized
    services. This facade only provides backward compatibility for existing API.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize semantic analyzer facade.
        
        Args:
            config: Configuration for semantic analysis components
            
        AI Context: Creates the orchestrator that handles actual semantic analysis.
        All configuration is passed through to the orchestrator.
        """
        self.config = config or {}
        self._orchestrator = SemanticAnalysisOrchestrator(config)
        
        logger.info("SemanticAnalyzer facade initialized (delegating to orchestrator)")
    
    def analyze_semantic_changes(
        self,
        original_text: str,
        modified_text: str,
        changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze semantic impact of changes between contract versions.
        
        Purpose: Backward compatibility method that delegates to the new
        semantic analysis orchestrator. Maintains the same API while using
        the improved architecture under the hood.
        
        Args:
            original_text: Original contract text
            modified_text: Modified contract text  
            changes: List of detected changes with metadata
            
        Returns:
            Dict[str, Any]: Semantic analysis results in backward-compatible format
            
        Raises:
            SemanticAnalysisError: If semantic analysis fails
        
        AI Context: Facade method that delegates to SemanticAnalysisOrchestrator.
        The orchestrator provides the actual implementation using specialized
        services. This method transforms the results to match the legacy API.
        """
        try:
            logger.debug("Delegating semantic change analysis to orchestrator")
            
            # Delegate to orchestrator
            orchestrator_results = self._orchestrator.analyze_semantic_changes(
                original_text, modified_text, changes
            )
            
            # Transform results to match legacy API format
            legacy_format = self._transform_to_legacy_format(orchestrator_results)
            
            logger.info("Semantic change analysis completed via orchestrator")
            return legacy_format
            
        except SemanticAnalysisError:
            # Re-raise orchestrator errors directly
            raise
        except Exception as e:
            logger.error(f"Semantic analyzer facade failed: {e}")
            raise SemanticAnalysisError(f"Semantic analysis failed: {str(e)}")
    
    def analyze_contract_semantic_content(self, contract_text: str) -> Dict[str, Any]:
        """
        Analyze semantic content of a single contract.
        
        Purpose: Provides semantic analysis for single contracts without
        change comparison. Delegates to orchestrator for actual analysis.
        
        Args:
            contract_text: Full contract text to analyze
        
        Returns:
            Dict[str, Any]: Semantic analysis results
            
        AI Context: Facade method for single contract analysis. Delegates to
        the orchestrator's single contract analysis capability.
        """
        try:
            logger.debug("Delegating single contract analysis to orchestrator")
            
            # Delegate to orchestrator
            orchestrator_results = self._orchestrator.analyze_contract_semantic_content(contract_text)
            
            # Results are already in the correct format for single contract analysis
            logger.info("Single contract semantic analysis completed")
            return orchestrator_results
            
        except SemanticAnalysisError:
            # Re-raise orchestrator errors directly
            raise
        except Exception as e:
            logger.error(f"Single contract semantic analysis failed: {e}")
            raise SemanticAnalysisError(f"Contract semantic analysis failed: {str(e)}")
    
    def _transform_to_legacy_format(self, orchestrator_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform orchestrator results to legacy API format.
        
        Purpose: Ensures backward compatibility by transforming the new
        orchestrator result format to match the expected legacy API format.
        
        Args:
            orchestrator_results: Results from semantic analysis orchestrator
            
        Returns:
            Dict[str, Any]: Results in legacy format
            
        AI Context: This transformation maintains backward compatibility.
        The orchestrator returns structured results, but legacy code expects
        a specific format. This method bridges the gap.
        """
        try:
            # Extract key components from orchestrator results
            entities_data = orchestrator_results.get('entities', {})
            risk_data = orchestrator_results.get('risk_assessment', {})
            semantic_similarity = orchestrator_results.get('semantic_similarity', 0.0)
            change_impacts = orchestrator_results.get('change_impacts', [])
            insights = orchestrator_results.get('semantic_insights', [])
            metadata = orchestrator_results.get('analysis_metadata', {})
            
            # Transform to legacy format
            legacy_results = {
                # Legacy semantic changes format
                'semantic_changes': self._transform_change_impacts_to_legacy(change_impacts),
                
                # Transform insights to legacy format
                'insights': self._transform_insights_to_legacy(insights, entities_data, risk_data),
                
                # Direct mappings
                'similarity_score': semantic_similarity,
                'impact_score': self._calculate_legacy_impact_score(change_impacts, risk_data),
                
                # Legacy context format
                'original_context': self._create_legacy_context(
                    entities_data.get('original', []),
                    'original'
                ),
                'modified_context': self._create_legacy_context(
                    entities_data.get('modified', []),
                    'modified'
                ),
                
                # Legacy metadata format
                'analysis_metadata': {
                    'timestamp': metadata.get('analysis_timestamp', ''),
                    'analyzer_version': '2.0.0',  # Updated version
                    'total_changes': metadata.get('changes_analyzed', 0),
                    'high_impact_changes': len([c for c in change_impacts if c.get('semantic_impact_level') == 'HIGH'])
                }
            }
            
            return legacy_results
            
        except Exception as e:
            logger.warning(f"Failed to transform results to legacy format: {e}")
            # Return minimal compatible structure on transformation failure
            return {
                'semantic_changes': [],
                'insights': [],
                'similarity_score': 0.0,
                'impact_score': 0.0,
                'original_context': {'text': '', 'entities': [], 'key_phrases': []},
                'modified_context': {'text': '', 'entities': [], 'key_phrases': []},
                'analysis_metadata': {'timestamp': '', 'analyzer_version': '2.0.0'}
            }
    
    def _transform_change_impacts_to_legacy(self, change_impacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform change impacts to legacy semantic_changes format."""
        legacy_changes = []
        
        for impact in change_impacts:
            legacy_change = {
                'change_id': impact.get('change_id', 'unknown'),
                'semantic_type': impact.get('change_type', 'general'),
                'impact_level': impact.get('semantic_impact_level', 'LOW'),
                'affected_concepts': [e.get('entity_type', '') for e in impact.get('affected_entities', [])],
                'context_analysis': {
                    'entity_impact': len(impact.get('affected_entities', [])),
                    'phrase_impact': 0,  # Not directly available in new format
                    'complexity_impact': 0,  # Not directly available
                    'sentiment_impact': 0  # Not directly available
                },
                'confidence_score': 0.8,  # Default confidence
                'risk_indicators': [r.get('risk_type', '') for r in impact.get('identified_risks', [])],
                'legal_implications': impact.get('impact_description', '')
            }
            legacy_changes.append(legacy_change)
        
        return legacy_changes
    
    def _transform_insights_to_legacy(
        self, 
        insights: List[str], 
        entities_data: Dict[str, Any],
        risk_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Transform insights to legacy format."""
        legacy_insights = []
        
        # Convert string insights to structured format
        for idx, insight_text in enumerate(insights):
            legacy_insight = {
                'insight_type': 'general_insight',
                'confidence': 0.8,
                'description': insight_text,
                'evidence': [insight_text],
                'metadata': {'source': 'orchestrator', 'index': idx}
            }
            legacy_insights.append(legacy_insight)
        
        # Add entity change insights if available
        entity_changes = entities_data.get('entity_changes', {})
        if entity_changes.get('added_entities') or entity_changes.get('removed_entities'):
            entity_insight = {
                'insight_type': 'entity_change',
                'confidence': 0.9,
                'description': 'Entity changes detected in contract analysis',
                'evidence': [
                    f"Added entities: {entity_changes.get('added_entities', {})}",
                    f"Removed entities: {entity_changes.get('removed_entities', {})}"
                ],
                'metadata': entity_changes
            }
            legacy_insights.append(entity_insight)
        
        # Add risk insights if available
        if risk_data.get('overall_risk_level', 'low') != 'low':
            risk_insight = {
                'insight_type': 'risk_pattern',
                'confidence': 0.8,
                'description': f"Contract has {risk_data.get('overall_risk_level', 'unknown')} risk level",
                'evidence': risk_data.get('recommendations', []),
                'metadata': {'risk_score': risk_data.get('risk_score', 0)}
            }
            legacy_insights.append(risk_insight)
        
        return legacy_insights
    
    def _calculate_legacy_impact_score(
        self, 
        change_impacts: List[Dict[str, Any]], 
        risk_data: Dict[str, Any]
    ) -> float:
        """Calculate impact score in legacy format."""
        if not change_impacts:
            return 0.0
        
        # Base impact from changes
        impact_weights = {'LOW': 0.2, 'MEDIUM': 0.5, 'HIGH': 1.0}
        total_impact = 0.0
        
        for impact in change_impacts:
            impact_level = impact.get('semantic_impact_level', 'LOW')
            total_impact += impact_weights.get(impact_level, 0.2)
        
        avg_impact = total_impact / len(change_impacts)
        
        # Adjust for overall risk level
        risk_score = risk_data.get('risk_score', 0.0)
        combined_impact = (avg_impact + risk_score) / 2
        
        return round(min(combined_impact, 1.0), 3)
    
    def _create_legacy_context(self, entities: List[Dict[str, Any]], context_type: str) -> Dict[str, Any]:
        """Create legacy semantic context format."""
        return {
            'text': '',  # Not available in new format
            'entities': entities,
            'key_phrases': [],  # Would need to be extracted separately
            'sentiment_score': 0.5,  # Neutral default
            'complexity_score': 0.5,  # Moderate default
            'domain_terms': []  # Would need to be extracted separately
        }


# Export for backward compatibility
__all__ = ['SemanticAnalyzer', 'SemanticAnalysisError']
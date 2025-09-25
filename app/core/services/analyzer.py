"""
Contract Analyzer Service

Main orchestrator for contract analysis workflow.
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from .document_processor import DocumentProcessor
from .comparison_engine import ComparisonEngine
from .incremental_analyzer import IncrementalAnalyzer
from ..models.contract import Contract
from ..models.analysis_result import AnalysisResult, Change, create_change_from_diff
from ...services.llm.providers import create_llm_provider
from ...services.nlp import SemanticAnalyzer, EntityExtractor, ClauseClassifier, RiskAnalyzer
from ...utils.logging.setup import get_logger

logger = get_logger(__name__)


class ContractAnalysisError(Exception):
    """Exception raised when contract analysis fails"""
    pass


class ContractAnalyzer:
    """
    Main contract analysis service that orchestrates the complete analysis workflow.
    
    Responsibilities:
    - Coordinate document processing
    - Manage LLM integration for analysis
    - Execute comparison logic
    - Produce structured analysis results
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize contract analyzer
        
        Args:
            config: Configuration dictionary containing LLM and processing settings
        """
        self.config = config
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.comparison_engine = ComparisonEngine()
        self.incremental_analyzer = None  # Will be initialized when LLM is available
        
        # LLM provider for analysis
        self.llm_provider = None
        self._initialize_llm_provider()
        
        # NLP components for semantic analysis
        self.semantic_analyzer = SemanticAnalyzer(config.get('nlp_settings', {}))
        self.entity_extractor = EntityExtractor(config.get('nlp_settings', {}))
        self.clause_classifier = ClauseClassifier(config.get('nlp_settings', {}))
        self.risk_analyzer = RiskAnalyzer(config.get('nlp_settings', {}))
        
        logger.info("Contract analyzer initialized")
    
    def _initialize_llm_provider(self):
        """Initialize LLM provider for analysis"""
        try:
            llm_config = self.config.get('llm_settings', {})
            provider_name = llm_config.get('provider', 'openai')
            
            # Ensure API key is included for OpenAI
            if provider_name == 'openai' and 'api_key' not in llm_config:
                import os
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key:
                    llm_config['api_key'] = api_key
            
            self.llm_provider = create_llm_provider(provider_name, llm_config)
            self.incremental_analyzer = IncrementalAnalyzer(self.llm_provider)
            logger.info(f"LLM provider and incremental analyzer initialized: {provider_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            self.llm_provider = None
            self.incremental_analyzer = None
    
    def analyze_contract(
        self,
        contract: Contract,
        template_path: str,
        include_llm_analysis: bool = True
    ) -> AnalysisResult:
        """
        Perform complete contract analysis
        
        Args:
            contract: Contract object to analyze
            template_path: Path to template file for comparison
            include_llm_analysis: Whether to include LLM-based analysis
            
        Returns:
            AnalysisResult with complete analysis
            
        Raises:
            ContractAnalysisError: If analysis fails
        """
        start_time = time.time()
        analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Starting analysis {analysis_id} for contract {contract.id}")
        
        try:
            # Mark contract as processing
            contract.mark_processing()
            
            # Step 1: Extract text from both documents
            contract_text = self.document_processor.extract_text_from_docx(contract.file_path)
            template_text = self.document_processor.extract_text_from_docx(template_path)
            
            if not contract_text:
                raise ContractAnalysisError("Failed to extract text from contract")
            if not template_text:
                raise ContractAnalysisError("Failed to extract text from template")
            
            # Store extracted text in contract
            contract.text_content = contract_text
            
            # Step 2: Perform text comparison
            similarity_score = self.comparison_engine.calculate_similarity(template_text, contract_text)
            text_changes = self.comparison_engine.find_detailed_changes(template_text, contract_text)
            
            logger.info(f"Text comparison completed - Similarity: {similarity_score:.3f}, Changes: {len(text_changes)}")
            
            # Step 3: Create initial analysis result
            analysis_result = AnalysisResult(
                analysis_id=analysis_id,
                contract_id=contract.id,
                template_id=Path(template_path).stem,
                analysis_timestamp=datetime.now(),
                similarity_score=similarity_score,
                processing_time_seconds=0,  # Will be updated at the end
                llm_model_used=self.llm_provider.model if self.llm_provider else None
            )
            
            # Step 4: Convert text changes to Change objects
            changes = []
            for i, change_dict in enumerate(text_changes):
                change_id = f"{analysis_id}_change_{i+1}"
                operation = change_dict['operation']
                deleted_text = change_dict.get('deleted_text', '')
                inserted_text = change_dict.get('inserted_text', '')
                
                # Generate appropriate explanation based on operation type
                if operation == 'delete':
                    explanation = "Text removed from template"
                elif operation == 'insert':
                    explanation = "Text added to contract"
                elif operation == 'replace':
                    explanation = "Text modified in contract"
                else:
                    continue  # Skip unknown operations
                
                change = create_change_from_diff(
                    change_id=change_id,
                    deleted_text=deleted_text,
                    inserted_text=inserted_text,
                    explanation=explanation
                )
                
                changes.append(change)
            
            # Step 5: Advanced Semantic Analysis
            try:
                semantic_analysis = self._perform_semantic_analysis(
                    contract_text, template_text, changes
                )
                analysis_result.metadata['semantic_analysis'] = semantic_analysis
                logger.info("Semantic analysis completed")
            except Exception as e:
                logger.warning(f"Semantic analysis failed: {e}")
            
            # Step 6: Incremental LLM Analysis (if enabled and provider available)
            if include_llm_analysis and self.incremental_analyzer:
                try:
                    enhanced_changes = self._perform_incremental_analysis(
                        changes, contract_text, template_text
                    )
                    changes = enhanced_changes
                    logger.info(f"Incremental LLM analysis completed - Enhanced {len(changes)} changes")
                    
                except Exception as e:
                    logger.warning(f"Incremental LLM analysis failed, using basic analysis: {e}")
                    # Continue with basic analysis
            
            # Step 7: Add changes to analysis result
            for change in changes:
                analysis_result.add_change(change)
            
            # Step 8: Generate business recommendations
            analysis_result.recommendations = self._generate_recommendations(analysis_result)
            analysis_result.risk_explanation = self._generate_risk_explanation(analysis_result)
            
            # Step 9: Calculate final processing time
            processing_time = time.time() - start_time
            analysis_result.processing_time_seconds = processing_time
            
            # Step 10: Update contract with analysis results
            contract.mark_analyzed(
                template_used=Path(template_path).name,
                changes_count=analysis_result.total_changes,
                similarity_score=similarity_score,
                risk_level=analysis_result.overall_risk_level
            )
            
            logger.info(
                f"Analysis {analysis_id} completed in {processing_time:.2f}s - "
                f"Risk: {analysis_result.overall_risk_level}, Changes: {analysis_result.total_changes}"
            )
            
            return analysis_result
            
        except ContractAnalysisError:
            # Re-raise specific analysis errors
            raise
        except FileNotFoundError as e:
            contract.mark_error(f"File not found: {str(e)}")
            raise ContractAnalysisError(f"Contract file not found: {e}")
        except PermissionError as e:
            contract.mark_error(f"Permission denied: {str(e)}")
            raise ContractAnalysisError(f"Permission denied accessing contract: {e}")
        except ValueError as e:
            contract.mark_error(f"Invalid data: {str(e)}")
            raise ContractAnalysisError(f"Invalid contract data: {e}")
        except Exception as e:
            contract.mark_error(f"Unexpected error: {str(e)}")
            logger.error(f"Unexpected error in contract analysis: {e}", exc_info=True)
            raise ContractAnalysisError(f"Contract analysis failed due to unexpected error: {e}")
    
    def _perform_llm_analysis(
        self,
        changes: List[Change],
        contract_text: str,
        template_text: str,
        analysis_result: AnalysisResult
    ) -> List[Change]:
        """
        Enhance changes with LLM analysis
        
        Args:
            changes: List of basic changes from text comparison
            contract_text: Full contract text
            template_text: Full template text
            analysis_result: Analysis result to update
            
        Returns:
            Enhanced changes with LLM explanations and classifications
        """
        if not changes:
            return changes
        
        # Prepare LLM prompt for analysis
        prompt = self._build_analysis_prompt(changes, contract_text, template_text)
        
        try:
            # Get LLM analysis
            response = self.llm_provider.generate_response(prompt)
            
            # Parse LLM response and enhance changes
            enhanced_changes = self._parse_llm_analysis(response.content, changes)
            
            # Update analysis result metadata
            analysis_result.metadata['llm_response_time'] = response.response_time
            analysis_result.metadata['llm_usage'] = response.usage
            
            return enhanced_changes
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return changes  # Return original changes if LLM fails
    
    def _perform_incremental_analysis(
        self,
        changes: List[Change],
        contract_text: str,
        template_text: str
    ) -> List[Change]:
        """
        Perform incremental analysis of changes, one at a time
        
        Args:
            changes: List of changes to analyze
            contract_text: Full contract text for context
            template_text: Full template text for context
            
        Returns:
            Enhanced changes with individual analysis
        """
        if not changes or not self.incremental_analyzer:
            return changes
        
        logger.info(f"Starting incremental analysis of {len(changes)} changes")
        enhanced_changes = []
        
        for i, change in enumerate(changes):
            try:
                # Get context for this change
                context = self.incremental_analyzer.get_change_context(
                    contract_text, change
                )
                
                # Analyze this specific change
                enhanced_change = self.incremental_analyzer.analyze_change(change, context)
                enhanced_changes.append(enhanced_change)
                
                logger.debug(f"Analyzed change {i+1}/{len(changes)}: {enhanced_change.classification}")
                
            except Exception as e:
                logger.warning(f"Failed to analyze change {i+1}: {e}")
                enhanced_changes.append(change)  # Keep original if analysis fails
        
        return enhanced_changes
    
    def _build_analysis_prompt(
        self,
        changes: List[Change],
        contract_text: str,
        template_text: str
    ) -> str:
        """Build LLM prompt for contract analysis"""
        
        # Limit text lengths for prompt
        max_text_length = 2000
        contract_excerpt = contract_text[:max_text_length] + "..." if len(contract_text) > max_text_length else contract_text
        template_excerpt = template_text[:max_text_length] + "..." if len(template_text) > max_text_length else template_text
        
        changes_summary = []
        for i, change in enumerate(changes[:10], 1):  # Limit to first 10 changes
            if change.deleted_text:
                changes_summary.append(f"{i}. DELETED: {change.deleted_text[:100]}...")
            if change.inserted_text:
                changes_summary.append(f"{i}. INSERTED: {change.inserted_text[:100]}...")
        
        prompt = f"""
Analyze the following contract changes and classify each change as CRITICAL, SIGNIFICANT, or INCONSEQUENTIAL.

TEMPLATE (Original):
{template_excerpt}

CONTRACT (Modified):
{contract_excerpt}

DETECTED CHANGES:
{chr(10).join(changes_summary)}

For each change, provide:
1. Classification (CRITICAL/SIGNIFICANT/INCONSEQUENTIAL)
2. Brief explanation of the change's business impact
3. Risk assessment
4. Recommendation

Classification Guidelines:
- CRITICAL: Changes that alter key business terms (price, scope, liability, termination)
- SIGNIFICANT: Changes that modify important terms but don't affect core business
- INCONSEQUENTIAL: Minor wording changes, formatting, or placeholder replacements

Respond in JSON format:
{{
  "changes": [
    {{
      "change_number": 1,
      "classification": "CRITICAL|SIGNIFICANT|INCONSEQUENTIAL",
      "explanation": "Brief explanation",
      "risk_impact": "Risk description",
      "recommendation": "Recommended action"
    }}
  ]
}}
"""
        return prompt
    
    def _parse_llm_analysis(self, llm_response: str, original_changes: List[Change]) -> List[Change]:
        """Parse LLM response and enhance changes"""
        try:
            import json
            
            # Try to parse JSON response
            response_data = json.loads(llm_response)
            analyzed_changes = response_data.get('changes', [])
            
            # Enhance original changes with LLM analysis
            enhanced_changes = []
            for i, change in enumerate(original_changes):
                if i < len(analyzed_changes):
                    analysis = analyzed_changes[i]
                    
                    # Update change with LLM analysis
                    change.classification = change.classification.__class__(
                        analysis.get('classification', 'INCONSEQUENTIAL')
                    )
                    change.explanation = analysis.get('explanation', change.explanation)
                    change.risk_impact = analysis.get('risk_impact', '')
                    change.recommendation = analysis.get('recommendation', '')
                    change.confidence_score = 0.8  # Default confidence for LLM analysis
                
                enhanced_changes.append(change)
            
            return enhanced_changes
            
        except Exception as e:
            logger.error(f"Failed to parse LLM analysis: {e}")
            return original_changes
    
    def _perform_semantic_analysis(
        self, 
        contract_text: str, 
        template_text: str, 
        changes: List[Change]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive semantic analysis using NLP components
        
        Args:
            contract_text: Full contract text
            template_text: Full template text
            changes: List of detected changes
            
        Returns:
            Dict containing comprehensive semantic analysis results
        """
        try:
            logger.info("Starting comprehensive semantic analysis")
            
            # Convert changes to dict format for semantic analysis
            change_dicts = []
            for change in changes:
                change_dict = {
                    'id': change.change_id,
                    'deleted_text': change.deleted_text or '',
                    'inserted_text': change.inserted_text or '',
                    'operation': 'replace' if change.deleted_text and change.inserted_text else ('delete' if change.deleted_text else 'insert')
                }
                change_dicts.append(change_dict)
            
            # 1. Semantic Analysis
            semantic_results = self.semantic_analyzer.analyze_semantic_changes(
                template_text, contract_text, change_dicts
            )
            
            # 2. Entity Extraction
            contract_entities = self.entity_extractor.extract_entities(contract_text)
            template_entities = self.entity_extractor.extract_entities(template_text)
            
            # 3. Clause Classification
            contract_clauses = self.clause_classifier.classify_clauses(contract_text)
            template_clauses = self.clause_classifier.classify_clauses(template_text)
            
            # 4. Risk Analysis
            risk_assessment = self.risk_analyzer.analyze_risks(contract_text, change_dicts)
            
            # Combine all analysis results
            comprehensive_analysis = {
                'semantic_analysis': semantic_results,
                'entity_analysis': {
                    'contract_entities': {
                        'entities': [entity.__dict__ for entity in contract_entities.entities],
                        'entity_counts': contract_entities.entity_counts,
                        'metadata': contract_entities.extraction_metadata
                    },
                    'template_entities': {
                        'entities': [entity.__dict__ for entity in template_entities.entities],
                        'entity_counts': template_entities.entity_counts,
                        'metadata': template_entities.extraction_metadata
                    }
                },
                'clause_analysis': {
                    'contract_clauses': {
                        'clauses': [clause.__dict__ for clause in contract_clauses.clauses],
                        'clause_counts': contract_clauses.clause_counts,
                        'missing_clauses': contract_clauses.missing_clauses,
                        'risk_summary': contract_clauses.risk_summary,
                        'metadata': contract_clauses.analysis_metadata
                    },
                    'template_clauses': {
                        'clauses': [clause.__dict__ for clause in template_clauses.clauses],
                        'clause_counts': template_clauses.clause_counts,
                        'missing_clauses': template_clauses.missing_clauses,
                        'risk_summary': template_clauses.risk_summary,
                        'metadata': template_clauses.analysis_metadata
                    }
                },
                'risk_analysis': {
                    'overall_risk_level': risk_assessment.overall_risk_level.value,
                    'risk_indicators': [indicator.__dict__ for indicator in risk_assessment.risk_indicators],
                    'risk_summary': risk_assessment.risk_summary,
                    'recommendations': risk_assessment.recommendations,
                    'risk_scores': risk_assessment.risk_scores,
                    'metadata': risk_assessment.analysis_metadata
                },
                'analysis_summary': {
                    'total_semantic_changes': len(semantic_results.get('semantic_changes', [])),
                    'contract_entities_count': len(contract_entities.entities),
                    'contract_clauses_count': len(contract_clauses.clauses),
                    'risk_indicators_count': len(risk_assessment.risk_indicators),
                    'overall_semantic_similarity': semantic_results.get('similarity_score', 0.0),
                    'overall_risk_level': risk_assessment.overall_risk_level.value,
                    'high_risk_changes': semantic_results.get('analysis_metadata', {}).get('high_impact_changes', 0)
                }
            }
            
            logger.info("Semantic analysis completed successfully")
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Semantic analysis failed: {str(e)}")
            return {
                'error': f"Semantic analysis failed: {str(e)}",
                'analysis_summary': {
                    'total_semantic_changes': 0,
                    'contract_entities_count': 0,
                    'contract_clauses_count': 0,
                    'risk_indicators_count': 0,
                    'overall_semantic_similarity': 0.0,
                    'overall_risk_level': 'UNKNOWN'
                }
            }
    
    def _generate_recommendations(self, analysis_result: AnalysisResult) -> List[str]:
        """Generate business recommendations based on analysis"""
        recommendations = []
        
        critical_count = len(analysis_result.get_critical_changes())
        significant_count = len(analysis_result.get_significant_changes())
        risk_level = analysis_result.overall_risk_level
        
        if risk_level == "HIGH":
            recommendations.extend([
                "🚨 CRITICAL: Schedule immediate legal review with qualified counsel",
                "🚨 Do not execute contract until all critical changes are approved",
                "🚨 Focus on value-to-value changes (price, service, company modifications)"
            ])
        elif risk_level == "MEDIUM":
            recommendations.extend([
                "⚠️ Schedule legal review before contract execution",
                "⚠️ Review all significant changes with stakeholders",
                "⚠️ Verify pricing and service level changes"
            ])
        else:
            recommendations.extend([
                "✅ Contract may proceed through standard review process",
                "✅ Verify placeholder content has been properly filled",
                "✅ Confirm standard terms and conditions"
            ])
        
        # Add general recommendations
        recommendations.extend([
            "📋 Document all approved changes for future reference",
            "📋 Ensure all parties acknowledge the modifications",
            "📋 Update contract management system with new terms"
        ])
        
        return recommendations
    
    def _generate_risk_explanation(self, analysis_result: AnalysisResult) -> str:
        """Generate risk explanation based on analysis"""
        critical_count = len(analysis_result.get_critical_changes())
        significant_count = len(analysis_result.get_significant_changes())
        risk_level = analysis_result.overall_risk_level
        
        if risk_level == "HIGH":
            if critical_count > 0:
                return (f"This contract contains {critical_count} critical change(s) involving "
                       "actual value-to-value modifications (e.g., price changes, service changes, "
                       "company changes). These require immediate legal review and approval before proceeding.")
            else:
                return ("This contract contains numerous significant changes that require "
                       "immediate legal review and approval before proceeding.")
        elif risk_level == "MEDIUM":
            return ("This contract contains significant changes that should be reviewed "
                   "by legal counsel before execution.")
        else:
            return ("This contract has minimal changes (mostly placeholder → actual content) "
                   "and can proceed through standard review processes.")
    
    def extract_text_from_docx(self, filepath: str) -> str:
        """
        Extract text content from a .docx file (legacy method for backwards compatibility)
        
        Args:
            filepath: Path to the .docx file
            
        Returns:
            Full text content as a single string
        """
        return self.document_processor.extract_text_from_docx(filepath)
    
    def find_changes(self, template_text: str, contract_text: str) -> List[Tuple[str, str]]:
        """
        Find changes between template and contract text (legacy method)
        
        Args:
            template_text: Original template text
            contract_text: Contract text to compare
            
        Returns:
            List of changes as tuples (operation, text)
        """
        return self.comparison_engine.find_changes(template_text, contract_text)
    
    def calculate_similarity(self, template_text: str, contract_text: str) -> float:
        """
        Calculate similarity between template and contract text (legacy method)
        
        Args:
            template_text: Original template text
            contract_text: Contract text to compare
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        return self.comparison_engine.calculate_similarity(template_text, contract_text)


def create_contract_analyzer(config: Dict[str, Any]) -> ContractAnalyzer:
    """
    Factory function to create a contract analyzer
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured ContractAnalyzer instance
    """
    return ContractAnalyzer(config)


__all__ = ['ContractAnalyzer', 'ContractAnalysisError', 'create_contract_analyzer']
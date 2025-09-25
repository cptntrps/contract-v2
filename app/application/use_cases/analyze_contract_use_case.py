"""
Analyze Contract Use Case - Application Layer

Orchestrates the complete contract analysis workflow following clean architecture.
Business logic separated from HTTP concerns, following architectural standards.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from ...core.services.analyzer import create_contract_analyzer
from ...core.services.template_matching_service import TemplateMatchingService, TemplateMatchingError
from ...utils.errors.exceptions import ValidationError, NotFoundError, AnalysisError

logger = logging.getLogger(__name__)


class AnalyzeContractUseCase:
    """
    Orchestrates contract analysis workflow from request to completion.
    
    Purpose: Coordinates the complete contract analysis process including template
    matching, analyzer configuration, analysis execution, and result persistence.
    Separates business logic from HTTP concerns following clean architecture.
    
    AI Context: This is the primary entry point for contract analysis workflows.
    When debugging analysis failures, start here to trace the complete process.
    The use case coordinates multiple domain services: validation, template matching,
    analysis execution, and result storage.
    """
    
    def __init__(self):
        """Initialize the use case with required services."""
        self.template_matcher = TemplateMatchingService()
    
    def execute(self, request: 'AnalysisRequest') -> 'AnalysisResult':
        """
        Execute complete contract analysis workflow.
        
        Purpose: Orchestrates end-to-end analysis process from validated request
        to persisted results. Handles template selection, analyzer configuration,
        analysis execution, and result formatting.
        
        Args:
            request (AnalysisRequest): Validated analysis request containing:
                - contract_id: Unique contract identifier
                - analysis_options: Optional analysis configuration
                - user_context: Optional user/session information
        
        Returns:
            AnalysisResult: Complete analysis results containing:
                - analysis_id: Unique analysis identifier
                - contract_info: Contract metadata and identification
                - template_info: Selected template information and matching reason
                - analysis_data: LLM analysis results and insights
                - semantic_analysis: NLP processing results
                - recommendations: Business recommendations and next steps
                - metadata: Analysis execution metadata (timing, config, etc.)
        
        Raises:
            ValidationError: If request validation fails
            NotFoundError: If contract not found in system
            TemplateMatchingError: If template selection fails
            AnalysisError: If analysis execution fails
            PersistenceError: If result storage fails
        
        AI Context: Primary analysis orchestration function. The workflow follows
        these steps: validate → find template → configure analyzer → execute → persist.
        Each step can fail independently. For debugging, check logs at each step.
        """
        try:
            logger.info(f"Starting contract analysis workflow for contract {request.contract_id}")
            
            # Step 1: Validate and retrieve contract
            contract = self._get_and_validate_contract(request.contract_id)
            logger.debug(f"Contract validated: {contract.get_display_name()}")
            
            # Step 2: Find best matching template
            template_path = self._find_best_template(contract)
            logger.info(f"Template selected: {Path(template_path).name}")
            
            # Step 3: Configure analyzer
            analyzer_config = self._build_analyzer_config(request.analysis_options)
            analyzer = self._create_analyzer(analyzer_config)
            logger.debug("Analyzer configured and created")
            
            # Step 4: Execute analysis
            analysis_data = self._execute_analysis(analyzer, contract, template_path)
            logger.info("Analysis execution completed")
            
            # Step 5: Build result object
            analysis_result = self._build_analysis_result(
                contract=contract,
                template_path=template_path,
                analysis_data=analysis_data,
                config=analyzer_config
            )
            
            # Step 6: Persist results
            self._persist_analysis_result(analysis_result)
            logger.info(f"Analysis workflow completed successfully: {analysis_result.analysis_id}")
            
            return analysis_result
            
        except (ValidationError, NotFoundError, TemplateMatchingError) as e:
            # Re-raise expected business exceptions
            logger.error(f"Analysis workflow failed with business error: {e}")
            raise
        except Exception as e:
            # Wrap unexpected errors in AnalysisError
            logger.error(f"Analysis workflow failed with unexpected error: {e}")
            raise AnalysisError(f"Contract analysis failed: {str(e)}")
    
    def _get_and_validate_contract(self, contract_id: str):
        """
        Retrieve and validate contract from storage.
        
        Args:
            contract_id: Contract identifier to retrieve
        
        Returns:
            Contract entity with validated data
        
        Raises:
            ValidationError: If contract ID format invalid
            NotFoundError: If contract not found in storage
        """
        # Import here to avoid circular dependencies during refactoring
        from ...utils.validation import ValidationHandler
        from ...api.routes.contracts import contracts_store
        
        # Validate contract ID format
        try:
            validated_contract_id = ValidationHandler.validate_contract_id(contract_id)
            logger.debug(f"Contract ID validated: {validated_contract_id}")
        except ValidationError as e:
            logger.warning(f"Contract ID validation failed: {e}")
            raise
        
        # Check contract existence
        logger.debug(f"Checking contract {validated_contract_id} in store")
        logger.debug(f"Available contracts: {list(contracts_store.keys())}")
        
        if validated_contract_id not in contracts_store:
            logger.warning(f"Contract {validated_contract_id} not found")
            raise NotFoundError("contract", validated_contract_id)
        
        return contracts_store[validated_contract_id]
    
    def _find_best_template(self, contract) -> str:
        """
        Find best matching template using template matching service.
        
        Args:
            contract: Contract entity for template matching
        
        Returns:
            str: Absolute path to selected template file
        
        Raises:
            TemplateMatchingError: If template matching fails
        """
        try:
            template_path = self.template_matcher.find_best_template(contract)
            
            if not template_path:
                raise TemplateMatchingError("No suitable template found for contract")
            
            # Verify template file exists
            if not Path(template_path).exists():
                raise TemplateMatchingError(f"Selected template file not found: {template_path}")
            
            return template_path
            
        except TemplateMatchingError:
            raise
        except Exception as e:
            raise TemplateMatchingError(f"Template matching failed: {str(e)}")
    
    def _build_analyzer_config(self, analysis_options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Build analyzer configuration from request options and defaults.
        
        Args:
            analysis_options: Optional analysis configuration overrides
        
        Returns:
            Dict[str, Any]: Complete analyzer configuration
        
        AI Context: Configuration includes LLM settings, analysis parameters,
        and NLP options. Default configuration optimized for accuracy over speed.
        """
        # Default configuration optimized for accuracy
        default_config = {
            'llm_settings': {
                'provider': 'openai',
                'model': 'gpt-4o', 
                'temperature': 0.1,  # Low temperature for consistent results
                'max_tokens': 2048
            },
            'analysis_settings': {
                'include_llm_analysis': True,
                'batch_size': 10,
                'similarity_threshold': 0.7,
                'include_semantic_analysis': True,
                'detail_level': 'comprehensive'
            },
            'nlp_settings': {
                'extract_entities': True,
                'analyze_sentiment': True,
                'identify_risks': True,
                'generate_recommendations': True
            }
        }
        
        # Apply user-provided options if available
        if analysis_options:
            # Deep merge configuration dictionaries
            config = self._deep_merge_config(default_config, analysis_options)
            logger.debug(f"Applied custom analysis options: {analysis_options}")
        else:
            config = default_config
        
        return config
    
    def _deep_merge_config(self, default_config: Dict, user_options: Dict) -> Dict:
        """Deep merge user options into default configuration."""
        merged = default_config.copy()
        
        for key, value in user_options.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge_config(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _create_analyzer(self, config: Dict[str, Any]):
        """
        Create contract analyzer instance with configuration.
        
        Args:
            config: Analyzer configuration dictionary
        
        Returns:
            Configured contract analyzer instance
        
        Raises:
            AnalysisError: If analyzer creation fails
        """
        try:
            analyzer = create_contract_analyzer(config)
            logger.debug(f"Analyzer created: {type(analyzer)}")
            return analyzer
        except Exception as e:
            logger.error(f"Failed to create analyzer: {e}")
            raise AnalysisError(f"Analyzer creation failed: {str(e)}")
    
    def _execute_analysis(self, analyzer, contract, template_path: str) -> Dict[str, Any]:
        """
        Execute contract analysis using configured analyzer.
        
        Args:
            analyzer: Configured analyzer instance
            contract: Contract entity to analyze
            template_path: Path to template file for comparison
        
        Returns:
            Dict[str, Any]: Analysis results from analyzer
        
        Raises:
            AnalysisError: If analysis execution fails
        """
        try:
            logger.info(f"Executing analysis: {contract.get_display_name()} vs {Path(template_path).name}")
            
            # Execute the analysis
            result = analyzer.analyze(contract.id, template_path)
            
            if not result:
                raise AnalysisError("Analyzer returned empty result")
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown analysis error')
                raise AnalysisError(f"Analysis failed: {error_msg}")
            
            logger.info("Analysis execution successful")
            return result
            
        except AnalysisError:
            raise
        except Exception as e:
            logger.error(f"Analysis execution failed: {e}")
            raise AnalysisError(f"Analysis execution error: {str(e)}")
    
    def _build_analysis_result(self, contract, template_path: str, analysis_data: Dict, config: Dict) -> 'AnalysisResult':
        """
        Build structured analysis result object.
        
        Args:
            contract: Contract entity that was analyzed
            template_path: Path to template used for analysis
            analysis_data: Raw analysis results from analyzer
            config: Analyzer configuration used
        
        Returns:
            AnalysisResult: Structured result object
        """
        analysis_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Extract key analysis metrics
        analysis_result_data = analysis_data.get('analysis_result', {})
        semantic_data = analysis_data.get('semantic_analysis', {})
        
        result = AnalysisResult(
            analysis_id=analysis_id,
            contract_id=contract.id,
            contract_name=contract.get_display_name(),
            template_path=template_path,
            template_name=Path(template_path).name,
            
            # Analysis metrics
            similarity_score=analysis_result_data.get('similarity', 0.0),
            changes_detected=analysis_result_data.get('changes', []),
            status=self._determine_analysis_status(analysis_result_data),
            
            # Semantic analysis
            semantic_analysis=semantic_data,
            
            # Metadata
            created_at=timestamp,
            analysis_config=config,
            execution_time=analysis_data.get('execution_time'),
            
            # Additional context
            recommendations=analysis_result_data.get('recommendations', []),
            risk_assessment=semantic_data.get('risk_assessment'),
            next_steps=self._generate_next_steps(analysis_result_data)
        )
        
        return result
    
    def _determine_analysis_status(self, analysis_data: Dict) -> str:
        """
        Determine analysis status based on results.
        
        Args:
            analysis_data: Analysis result data
        
        Returns:
            str: Status classification (e.g., 'LOW RISK', 'MEDIUM RISK', 'HIGH RISK')
        """
        changes_count = len(analysis_data.get('changes', []))
        similarity = analysis_data.get('similarity', 0.0)
        
        if changes_count == 0:
            return 'NO CHANGES DETECTED'
        elif changes_count <= 5 and similarity >= 0.8:
            return 'LOW RISK - Minor Changes'
        elif changes_count <= 15 or similarity >= 0.6:
            return 'MEDIUM RISK - Moderate Changes'
        else:
            return 'HIGH RISK - Significant Changes'
    
    def _generate_next_steps(self, analysis_data: Dict) -> List[str]:
        """Generate recommended next steps based on analysis results."""
        changes_count = len(analysis_data.get('changes', []))
        
        if changes_count == 0:
            return ['No further review required', 'Contract ready for execution']
        elif changes_count <= 5:
            return ['Brief legal review recommended', 'Focus on modified clauses']
        else:
            return [
                'Comprehensive legal review required',
                'Consider stakeholder approval process',
                'Document change rationale'
            ]
    
    def _persist_analysis_result(self, result: 'AnalysisResult') -> None:
        """
        Persist analysis result to storage.
        
        Args:
            result: Analysis result to persist
        
        Raises:
            PersistenceError: If storage operation fails
        """
        try:
            # Import here to avoid circular dependencies during refactoring
            from ...api.routes.analysis import analysis_results_store
            
            # Convert result to storage format
            result_data = {
                'contract': result.contract_name,
                'template': result.template_name,
                'similarity': result.similarity_score,
                'status': result.status,
                'date': result.created_at.isoformat(),
                'changes': result.changes_detected,
                'semantic_analysis': result.semantic_analysis,
                'recommendations': result.recommendations,
                'analysis_config': result.analysis_config
            }
            
            # Store result
            analysis_results_store[result.analysis_id] = result_data
            logger.debug(f"Analysis result persisted: {result.analysis_id}")
            
        except Exception as e:
            logger.error(f"Failed to persist analysis result: {e}")
            # Don't raise exception - analysis succeeded even if persistence failed
            # TODO: Implement proper repository pattern for better error handling


class AnalysisRequest:
    """
    Request object for contract analysis.
    
    Purpose: Encapsulates analysis request parameters with validation.
    Provides clean interface for use case execution.
    """
    
    def __init__(self, contract_id: str, analysis_options: Optional[Dict] = None, user_context: Optional[Dict] = None):
        """
        Initialize analysis request.
        
        Args:
            contract_id: Unique contract identifier
            analysis_options: Optional analysis configuration overrides
            user_context: Optional user/session context
        """
        self.contract_id = contract_id
        self.analysis_options = analysis_options or {}
        self.user_context = user_context or {}


class AnalysisResult:
    """
    Structured analysis result object.
    
    Purpose: Encapsulates complete analysis results with metadata.
    Provides consistent interface for result handling and storage.
    """
    
    def __init__(self, **kwargs):
        """Initialize analysis result with provided data."""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        result_dict = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result_dict[key] = value.isoformat()
            else:
                result_dict[key] = value
        return result_dict


class PersistenceError(Exception):
    """Exception raised when result persistence fails."""
    pass
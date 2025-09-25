# Contributing to Contract Analyzer

## Golden Rule
**Write code so both a human teammate and an AI assistant can instantly understand where to look and how to extend.**

## Project Structure

### Core Principles
- **One responsibility per file**: Each module should have a single, clear purpose
- **Standard folder organization**: Follow the established structure religiously
- **File size limits**: 100-300 lines per module. Split larger files immediately
- **Clear naming**: File and function names should be self-documenting

### Required Folder Structure
```
app/
├── domain/              # Core business entities and domain services
│   ├── entities/        # Business objects (Contract, Template, Analysis)
│   ├── services/        # Domain logic (AnalysisEngine, TemplateMatchingService)
│   └── repositories/    # Data access interfaces
├── application/         # Application-layer coordination
│   ├── use_cases/       # Business workflows (AnalyzeContractUseCase)
│   ├── dto/            # Data transfer objects
│   └── handlers/       # Command/query handlers
├── infrastructure/      # External concerns
│   ├── persistence/     # Database implementations
│   ├── external/        # Third-party integrations (LLM providers)
│   ├── web/            # HTTP/API concerns
│   └── storage/        # File system operations
├── api/                # HTTP endpoints ONLY
│   ├── routes/         # Route definitions
│   └── schemas/        # Request/response validation
└── utils/              # Pure utility functions
    ├── validation/     # Input validation helpers
    ├── formatting/     # Data formatting utilities
    └── logging/        # Logging configuration
```

## Function Design

### Single Purpose Functions
❌ **Bad**: Functions that do multiple things
```python
def process_contract(contract_id, template_id):
    # Validation
    # Template matching  
    # Analysis execution
    # Result formatting
    # Error handling
    # Notification sending
```

✅ **Good**: Functions with single responsibility
```python
def validate_analysis_request(request: AnalysisRequest) -> ValidationResult:
    """Validates analysis request parameters only."""
    
def match_contract_to_template(contract: Contract) -> Optional[Template]:
    """Finds best matching template for contract."""
    
def execute_analysis(contract: Contract, template: Template) -> AnalysisResult:
    """Performs contract analysis against template."""
```

### Required Docstring Format
Every function must have this docstring structure:

```python
def analyze_contract_semantic_content(contract_text: str, analysis_options: dict) -> SemanticAnalysisResult:
    """
    Extracts semantic entities and relationships from contract text.
    
    Purpose: Identifies key legal entities, clauses, and risk indicators in contract text
    using NLP processing to support contract analysis workflows.
    
    Args:
        contract_text (str): Full text content of the contract document
        analysis_options (dict): Configuration options with keys:
            - 'include_entities': bool, whether to extract named entities
            - 'include_sentiment': bool, whether to analyze clause sentiment
            - 'detail_level': str, one of 'basic', 'standard', 'comprehensive'
    
    Returns:
        SemanticAnalysisResult: Object containing:
            - entities: List[Entity] - Extracted entities with confidence scores
            - clauses: List[Clause] - Identified contract clauses
            - risk_indicators: List[RiskIndicator] - Potential risk areas
            - confidence_score: float - Overall analysis confidence (0.0-1.0)
    
    Raises:
        ValidationError: If contract_text is empty or analysis_options invalid
        ProcessingError: If NLP pipeline fails or times out
    
    AI Context: This function is the primary entry point for semantic analysis.
    It coordinates entity extraction, clause classification, and risk assessment
    workflows. For debugging, check the NLP pipeline status first.
    """
```

### Unimplemented Functions
Use this pattern for stubs:

```python
def generate_compliance_report(analysis: AnalysisResult) -> ComplianceReport:
    """
    Generate regulatory compliance report from analysis results.
    
    TODO: Implement compliance checking against regulatory frameworks.
    Priority: Medium - needed for enterprise compliance features.
    Dependencies: Requires regulatory database setup.
    """
    raise NotImplementedError("Compliance reporting not yet implemented")
```

## Naming Conventions

### CRUD Operations
- `get_contract(contract_id: str) -> Optional[Contract]`
- `create_contract(contract_data: ContractData) -> Contract`
- `update_contract(contract_id: str, updates: dict) -> Contract`
- `delete_contract(contract_id: str) -> bool`

### Service Operations
- `process_contract_upload(file_data: FileData) -> ProcessingResult`
- `validate_contract_format(file_path: str) -> ValidationResult`
- `analyze_contract_content(contract: Contract, template: Template) -> AnalysisResult`
- `generate_analysis_report(analysis: AnalysisResult, format: str) -> Report`

### Boolean Functions
- `is_contract_valid(contract: Contract) -> bool`
- `has_analysis_completed(analysis_id: str) -> bool`
- `can_user_access_contract(user_id: str, contract_id: str) -> bool`

## API Endpoints

### HTTP Concerns Only
API endpoints must handle ONLY HTTP-specific concerns:
- Request parsing and validation
- Authentication/authorization
- Response formatting
- HTTP status codes
- Error response formatting

❌ **Bad**: Business logic in endpoint
```python
@api.route('/analyze-contract', methods=['POST'])
def analyze_contract():
    data = request.json
    
    # BAD: Template matching logic in route
    best_template = None
    highest_similarity = 0.0
    for template in templates_store.values():
        similarity = calculate_similarity(data['content'], template['content'])
        if similarity > highest_similarity:
            highest_similarity = similarity
            best_template = template
    
    # BAD: Analysis configuration in route
    config = {
        'llm_settings': {
            'provider': 'openai',
            'model': 'gpt-4o',
            'temperature': 0.1,
        }
    }
    
    # BAD: Direct analyzer instantiation
    analyzer = create_contract_analyzer(config)
    result = analyzer.analyze(data['contract_id'], best_template['id'])
    
    return jsonify(result)
```

✅ **Good**: Delegate to service
```python
@api.route('/analyze-contract', methods=['POST'])
def analyze_contract():
    """
    Initiates contract analysis workflow.
    
    Delegates all business logic to AnalyzeContractUseCase.
    """
    try:
        # Parse and validate HTTP request
        request_data = AnalysisRequestSchema().load(request.json)
        
        # Delegate to application service
        use_case = AnalyzeContractUseCase()
        result = use_case.execute(request_data)
        
        # Format HTTP response
        response_data = AnalysisResponseSchema().dump(result)
        return jsonify(response_data), 200
        
    except ValidationError as e:
        return jsonify({'error': 'Invalid request', 'details': e.messages}), 400
    except BusinessLogicError as e:
        return jsonify({'error': str(e)}), 422
    except Exception as e:
        logger.error(f"Unexpected error in analyze_contract: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

## Documentation Requirements

### README.md
Must contain:
1. **One-sentence project description**
2. **Quick start guide** (< 5 steps)
3. **Core features list** (bullet points)
4. **API overview** (key endpoints)
5. **Development setup** (environment requirements)

### docs/architecture.md
**REQUIRED** - See architecture documentation section below.

### Function Docstrings
Every public function must have docstring explaining:
- **Purpose**: What does this function do?
- **AI Context**: How should an AI assistant understand this function's role?
- **Dependencies**: What does this function depend on?
- **Side Effects**: What changes does this function make?

## Testing Requirements

### Test Coverage
- **Every function must have tests** - no exceptions
- **Tests mirror module structure**: `/tests/domain/services/test_analysis_engine.py`
- **Behavioral specifications**: Tests describe what the function should do, not how

### Test Naming
Tests should read like specifications:

```python
class TestContractAnalysisEngine:
    def test_analyzes_simple_service_agreement_successfully(self):
        """Should return analysis result for valid service agreement contract."""
        
    def test_raises_validation_error_when_contract_text_empty(self):
        """Should raise ValidationError when given empty contract text."""
        
    def test_handles_llm_timeout_gracefully(self):
        """Should return partial results when LLM provider times out."""
        
    def test_identifies_high_risk_clauses_in_liability_section(self):
        """Should flag liability clauses as high risk when limits exceed threshold."""
```

### AI-Focused Testing
Frame tests as behavioral contracts that will catch regressions when AI rewrites code:

```python
def test_contract_analysis_behavior_contract(self):
    """
    Behavioral contract for contract analysis function.
    
    This test ensures that ANY implementation of contract analysis
    maintains these behavioral guarantees, even if the internal
    algorithm changes completely.
    """
    contract = create_test_contract()
    template = create_test_template()
    
    result = analyze_contract_content(contract, template)
    
    # Behavioral guarantees that must never break
    assert result.confidence_score >= 0.0 and result.confidence_score <= 1.0
    assert len(result.changes_detected) >= 0
    assert result.analysis_id is not None
    assert result.status in ['completed', 'partial', 'failed']
    assert isinstance(result.generated_at, datetime)
```

## Code Style

### Python Standards
- **Follow PEP 8** strictly
- **Import ordering**:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- **No catch-all imports**: `from module import *` is forbidden
- **No "misc" or "utils" without specific purpose**

### Import Organization
```python
# Standard library
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Third-party
import requests
from flask import Flask, request, jsonify
from marshmallow import Schema, fields

# Local application
from app.domain.entities.contract import Contract
from app.domain.services.analysis_engine import AnalysisEngine
from app.application.dto.analysis_request import AnalysisRequest
```

### Error Handling Patterns
Use domain-specific exceptions:

```python
# Define in app/domain/exceptions.py
class ContractAnalysisError(Exception):
    """Base exception for contract analysis domain."""

class TemplateNotFoundError(ContractAnalysisError):
    """Raised when specified template cannot be found."""

class AnalysisTimeoutError(ContractAnalysisError):
    """Raised when analysis exceeds timeout limits."""

# Use in services
def analyze_contract(contract_id: str, template_id: str) -> AnalysisResult:
    template = template_repository.find_by_id(template_id)
    if template is None:
        raise TemplateNotFoundError(f"Template {template_id} not found")
    
    # ... analysis logic
```

## Commit Guidelines

### Commit Message Format
- **Imperative voice**: "Add contract validation" not "Added contract validation"
- **Present tense**: "Fix analysis timeout" not "Fixed analysis timeout" 
- **Specific scope**: "Add template matching algorithm" not "Improve analysis"

### Good Commit Examples
- `Add semantic entity extraction service`
- `Fix template matching algorithm accuracy`
- `Refactor analysis result builder into separate service`
- `Update contract upload validation rules`
- `Remove deprecated analysis endpoint`

### Bad Commit Examples
- `Various fixes and improvements`
- `Working on analysis stuff`
- `Updated code`
- `Bug fixes`

## Code Review Checklist

Before submitting any PR, ensure:

### Architecture
- [ ] Single responsibility principle followed
- [ ] Business logic separated from HTTP concerns
- [ ] Dependencies point inward (no circular dependencies)
- [ ] New code follows established patterns

### Documentation
- [ ] Function docstrings include AI context
- [ ] README updated if public API changes
- [ ] Architecture docs updated for new modules
- [ ] TODO comments for unimplemented features

### Testing
- [ ] New functions have behavioral tests
- [ ] Tests follow naming conventions
- [ ] Critical paths have regression protection
- [ ] Tests pass locally

### Code Quality
- [ ] File size under 300 lines
- [ ] Function complexity reasonable (< 15 lines typically)
- [ ] Clear, descriptive naming throughout
- [ ] No hardcoded magic numbers or strings

## Extension Guidelines

### Adding New Features

1. **Start with domain modeling**: Define entities and domain services first
2. **Create use case**: Define application-layer coordination
3. **Add infrastructure**: Implement persistence/external integrations  
4. **Add API layer**: Create HTTP endpoints last
5. **Update documentation**: Keep architecture docs current

### Example: Adding Contract Comparison Feature

1. **Domain Layer**:
   ```python
   # app/domain/services/contract_comparison_service.py
   class ContractComparisonService:
       def compare_contracts(self, contract_a: Contract, contract_b: Contract) -> ComparisonResult:
   ```

2. **Application Layer**:
   ```python
   # app/application/use_cases/compare_contracts_use_case.py
   class CompareContractsUseCase:
       def execute(self, request: ComparisonRequest) -> ComparisonResult:
   ```

3. **API Layer**:
   ```python
   # app/api/routes/comparison.py
   @comparison_bp.route('/compare-contracts', methods=['POST'])
   def compare_contracts():
   ```

This structure ensures that both human developers and AI assistants can:
- Quickly locate relevant code
- Understand component boundaries
- Extend functionality without breaking existing patterns
- Debug issues by following clear dependency chains

## Questions or Issues?

If anything is unclear or you need guidance on applying these principles:

1. Check existing code examples that follow these patterns
2. Review the architecture documentation 
3. Ask in PR comments for specific guidance
4. Update this document if patterns are missing or unclear

Remember: The goal is code that works seamlessly for both human intuition and AI understanding.
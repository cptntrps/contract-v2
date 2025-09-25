# Contract Analyzer Architecture

This document provides a comprehensive overview of the Contract Analyzer application architecture. It's designed to help both human developers and AI assistants quickly understand how the system is organized and how to extend it.

## System Overview

The Contract Analyzer is an enterprise-grade application that compares contracts against templates using AI/LLM analysis and generates professional reports. It follows a three-layer architecture with clear separation of concerns.

## Current Architecture

### `/app/api/` - HTTP Endpoints Only
**Purpose**: Handle HTTP requests and responses, delegate business logic to application layer.

**Current Modules**:
- `routes/analysis.py` - Contract analysis endpoints (795 lines - NEEDS REFACTORING)
- `routes/contracts.py` - Contract management endpoints  
- `routes/templates.py` - Template management endpoints
- `routes/reports.py` - Report generation and download endpoints
- `async_routes.py` - Async task management endpoints
- `app.py` - Flask application factory and route registration

**Issues**: Currently contains business logic that should be moved to services layer.

### `/app/core/` - Core Business Logic
**Purpose**: Contains the main business logic and domain services.

**Current Modules**:
- `services/analyzer.py` - Main contract analysis orchestration (639 lines - NEEDS SPLITTING)
- `models/contract.py` - Contract entity definitions
- `models/template.py` - Template entity definitions  
- `models/analysis_result.py` - Analysis result data structures

**Issues**: Analyzer service is doing too many things and needs to be split into focused services.

### `/app/services/` - Supporting Services  
**Purpose**: Specialized services for specific business operations.

**Current Modules**:
- `nlp/semantic_analyzer.py` - NLP and semantic analysis (666 lines - NEEDS SPLITTING)
- `file_handler.py` - File upload and processing utilities
- `document_processor.py` - Document text extraction and preparation

**Issues**: Semantic analyzer tries to do everything and should be split into focused analyzers.

### `/app/utils/` - Utility Functions
**Purpose**: Reusable helper functions with no business logic dependencies.

**Current Modules**:
- `logging/setup.py` - Logging configuration
- `errors/exceptions.py` - Custom exception definitions  
- `errors/responses.py` - Error response formatting
- `validation.py` - Input validation helpers

### `/app/config/` - Configuration Management
**Purpose**: Application configuration and environment setup.

**Current Modules**:
- `settings.py` - Configuration classes and environment handling
- `llm_config.py` - LLM provider configuration

### `/app/async_processing/` - Background Task Management
**Purpose**: Handle long-running analysis tasks asynchronously.

**Current Modules**:
- `task_manager.py` - Celery task management and coordination
- `celery_config.py` - Celery application configuration

### `/app/database/` - Data Persistence
**Purpose**: Database models and repository patterns.

**Current Modules**:
- `models/` - SQLAlchemy model definitions
- `repositories/` - Data access layer implementations

### `/static/` and `/templates/` - Frontend Assets
**Purpose**: Web interface and client-side functionality.

**Current Structure**:
- `templates/dashboard.html` - Main dashboard template (671 lines)
- `static/js/modules/` - Modular JavaScript components
- `static/css/` - Styling and layout

**Issues**: JavaScript module loading timing issues causing dashboard display problems.

## Identified Architectural Problems

### 1. Mixed Concerns in Route Handlers
**Problem**: Route files contain complex business logic instead of delegating to services.

**Example**: Template matching algorithm (90+ lines) embedded directly in `analysis.py` route.

**Solution**: Extract to dedicated service classes:
```
app/domain/services/template_matching_service.py
app/application/use_cases/analyze_contract_use_case.py
```

### 2. Oversized Service Classes
**Problem**: Single classes trying to handle multiple responsibilities.

**Example**: `analyzer.py` (639 lines) handles orchestration, LLM management, document processing, and result building.

**Solution**: Split into focused services:
```
ContractAnalysisOrchestrator  - Workflow coordination
AnalysisResultBuilder        - Result construction  
RecommendationEngine         - Business rule application
```

### 3. Inconsistent Module Organization
**Problem**: Similar functionality scattered across different directories.

**Current Issues**:
- `app/core/models/` vs `app/database/models/` - duplicate model concepts
- `app/services/nlp/` vs `app/core/services/` - unclear hierarchy

**Solution**: Establish clear domain boundaries:
```
app/domain/          - Core business entities and rules
app/application/     - Use cases and application coordination  
app/infrastructure/  - External integrations and persistence
```

### 4. Frontend-Backend Integration Issues
**Problem**: JavaScript module loading and caching issues causing display problems.

**Recent Fixes**:
- Parameter name mismatch between frontend (`analysis_id`) and backend (`id`)
- Cache-busting timestamps for JavaScript modules
- Fallback refresh mechanisms when modules fail to load

## Target Architecture (Recommended)

### Domain-Driven Design Structure
```
app/
├── domain/                     # Core business logic
│   ├── entities/              # Business objects
│   │   ├── contract.py        # Contract aggregate root
│   │   ├── template.py        # Template entity
│   │   └── analysis.py        # Analysis aggregate
│   ├── services/              # Domain services  
│   │   ├── template_matching_service.py
│   │   ├── contract_analysis_service.py
│   │   └── recommendation_engine.py
│   └── repositories/          # Data access interfaces
│       ├── contract_repository.py (interface)
│       └── template_repository.py (interface)
├── application/               # Application coordination
│   ├── use_cases/            # Business workflows
│   │   ├── analyze_contract_use_case.py
│   │   ├── upload_contract_use_case.py
│   │   └── generate_report_use_case.py
│   ├── dto/                  # Data transfer objects
│   └── handlers/             # Command/query handlers
├── infrastructure/           # External concerns
│   ├── persistence/          # Database implementations
│   │   ├── sql_contract_repository.py
│   │   └── sql_template_repository.py  
│   ├── external/             # Third-party integrations
│   │   ├── openai_provider.py
│   │   └── ollama_provider.py
│   ├── web/                  # HTTP/API layer
│   │   ├── routes/           # Thin HTTP handlers
│   │   └── schemas/          # Request/response validation
│   └── storage/              # File system operations
└── utils/                    # Pure utility functions
    ├── validation/           # Input validation
    ├── formatting/           # Data formatting  
    └── logging/             # Logging setup
```

## How to Extend the System

### Adding a New Analysis Feature

**Example**: Adding contract risk assessment capability

1. **Start with Domain Layer**:
   ```python
   # app/domain/entities/risk_assessment.py
   class RiskAssessment:
       def __init__(self, contract_id: str, risk_level: RiskLevel):
           self.contract_id = contract_id
           self.risk_level = risk_level
           self.risk_factors = []
   
   # app/domain/services/risk_assessment_service.py  
   class RiskAssessmentService:
       def assess_contract_risk(self, contract: Contract) -> RiskAssessment:
           """Analyzes contract for potential risk factors."""
   ```

2. **Add Application Use Case**:
   ```python
   # app/application/use_cases/assess_contract_risk_use_case.py
   class AssessContractRiskUseCase:
       def __init__(self, risk_service: RiskAssessmentService):
           self.risk_service = risk_service
       
       def execute(self, request: RiskAssessmentRequest) -> RiskAssessmentResult:
           """Coordinates risk assessment workflow."""
   ```

3. **Implement Infrastructure**:
   ```python
   # app/infrastructure/persistence/sql_risk_repository.py
   class SqlRiskAssessmentRepository(RiskAssessmentRepository):
       def save(self, assessment: RiskAssessment) -> None:
           """Persist risk assessment to database."""
   ```

4. **Add HTTP Endpoint**:
   ```python
   # app/infrastructure/web/routes/risk_assessment.py
   @risk_bp.route('/assess-risk', methods=['POST'])
   def assess_contract_risk():
       """HTTP endpoint - delegates to use case."""
       request_data = RiskAssessmentSchema().load(request.json)
       use_case = AssessContractRiskUseCase()  # DI in real implementation
       result = use_case.execute(request_data)
       return jsonify(RiskAssessmentResponseSchema().dump(result))
   ```

### Adding a New Document Type

**Example**: Adding support for lease agreements

1. **Extend Domain Entities**:
   ```python
   # app/domain/entities/contract.py
   class ContractType(Enum):
       SERVICE_AGREEMENT = "service_agreement"
       LEASE_AGREEMENT = "lease_agreement"    # New type
       EMPLOYMENT_CONTRACT = "employment_contract"
   ```

2. **Add Specialized Service**:
   ```python
   # app/domain/services/lease_analysis_service.py
   class LeaseAnalysisService:
       def analyze_lease_terms(self, contract: Contract) -> LeaseAnalysisResult:
           """Specialized analysis for lease agreements."""
   ```

3. **Update Template Matching**:
   ```python
   # app/domain/services/template_matching_service.py
   class TemplateMatchingService:
       def find_best_template(self, contract: Contract) -> Optional[Template]:
           if contract.type == ContractType.LEASE_AGREEMENT:
               return self._match_lease_template(contract)
   ```

### Adding a New Report Format

**Example**: Adding PowerPoint presentation output

1. **Define Domain Contract**:
   ```python
   # app/domain/entities/report.py
   class ReportFormat(Enum):
       PDF = "pdf"
       EXCEL = "excel"  
       WORD = "word"
       POWERPOINT = "powerpoint"  # New format
   ```

2. **Implement Report Generator**:
   ```python
   # app/infrastructure/external/powerpoint_generator.py
   class PowerPointReportGenerator(ReportGenerator):
       def generate(self, analysis: AnalysisResult) -> Report:
           """Generate PowerPoint presentation from analysis."""
   ```

3. **Update Factory**:
   ```python
   # app/application/factories/report_generator_factory.py
   def create_report_generator(format: ReportFormat) -> ReportGenerator:
       if format == ReportFormat.POWERPOINT:
           return PowerPointReportGenerator()
   ```

### Adding External Integration

**Example**: Integrating with legal database API

1. **Define Domain Interface**:
   ```python
   # app/domain/repositories/legal_database_repository.py
   class LegalDatabaseRepository(ABC):
       @abstractmethod
       def find_similar_cases(self, contract_clauses: List[str]) -> List[LegalCase]:
           pass
   ```

2. **Implement Infrastructure**:
   ```python
   # app/infrastructure/external/westlaw_client.py
   class WestlawClient(LegalDatabaseRepository):
       def find_similar_cases(self, contract_clauses: List[str]) -> List[LegalCase]:
           """Query Westlaw API for similar legal cases."""
   ```

3. **Update Analysis Service**:
   ```python
   # app/domain/services/contract_analysis_service.py
   class ContractAnalysisService:
       def __init__(self, legal_db: LegalDatabaseRepository):
           self.legal_db = legal_db
       
       def analyze_with_legal_context(self, contract: Contract) -> AnalysisResult:
           similar_cases = self.legal_db.find_similar_cases(contract.key_clauses)
   ```

## Key Design Principles

### 1. Dependency Inversion
- High-level modules should not depend on low-level modules
- Both should depend on abstractions (interfaces)
- Database, HTTP, and external APIs are implementation details

### 2. Single Responsibility  
- Each class/module has one reason to change
- Separate business logic from infrastructure concerns
- Keep functions focused and testable

### 3. Open/Closed Principle
- Open for extension, closed for modification
- Use interfaces and dependency injection
- Add new features without changing existing code

### 4. Command/Query Separation
- Commands change state, don't return data
- Queries return data, don't change state
- Clear distinction between read and write operations

## Migration Strategy

### Phase 1: Extract Business Logic from Routes
1. Move template matching algorithm to dedicated service
2. Extract analysis orchestration from route handlers  
3. Create use case classes for major workflows

### Phase 2: Split Oversized Services
1. Break down analyzer.py into focused services
2. Split semantic_analyzer.py into specialized analyzers
3. Extract recommendation engine from main analyzer

### Phase 3: Establish Clear Boundaries
1. Implement repository interfaces
2. Create domain entity classes  
3. Separate infrastructure concerns

### Phase 4: Frontend Improvements
1. Fix JavaScript module loading issues
2. Implement proper error handling
3. Add loading states and retry mechanisms

## Testing Strategy

### Unit Tests
- Test business logic in isolation
- Mock external dependencies
- Focus on behavioral contracts

### Integration Tests  
- Test service interactions
- Verify database operations
- Test external API integrations

### End-to-End Tests
- Test complete workflows
- Verify HTTP API contracts
- Test UI interactions

## Monitoring and Observability

### Logging Strategy
- Structured logging with context
- Different log levels for different concerns
- Performance metrics and timing

### Health Checks
- Database connectivity
- External service availability
- Background task queue status

### Error Tracking
- Centralized error reporting
- Performance monitoring
- User behavior analytics

## Security Considerations

### Input Validation
- Validate all input at system boundaries
- Sanitize file uploads
- Check file types and sizes

### Authentication/Authorization
- JWT token-based authentication
- Role-based access control
- API rate limiting

### Data Protection
- Encrypt sensitive contract data
- Secure file storage
- Audit logging for compliance

---

This architecture documentation should be updated whenever new modules are added or existing ones are refactored. It serves as the single source of truth for understanding how the Contract Analyzer system is organized and how to extend it effectively.

For questions about this architecture or guidance on implementing new features, refer to the CONTRIBUTING.md guidelines or create an issue for discussion.
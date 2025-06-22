# Implementation Roadmap: High-Priority Enhancements

This document provides detailed implementation guidance for the top 3 priority enhancements identified from the `claude_code_instructions.md` analysis.

## 1. MCP Resources Implementation (PRIORITY: HIGH)

### Current State
- **Gap**: MCP server only exposes Tools, missing Resource interface for read operations
- **Impact**: CQRS pattern incomplete, forcing all operations through Tools
- **Location**: `src/mcp/server.py`, `src/mcp/resources.py`

### Implementation Strategy

#### Phase 1: Resource Interface Foundation
```python
# Add to src/mcp/resources.py
from mcp.server.models import Resource
from mcp.types import AnyUrl

@mcp.resource("qdrant://collections/{collection_name}")
async def get_collection_info(collection_name: str) -> str:
    """Query collection metadata and document count"""
    # Implementation: Read-only access to Qdrant collection info
    
@mcp.resource("qdrant://collections/{collection_name}/documents")
async def get_collection_documents(collection_name: str, limit: int = 10) -> str:
    """Retrieve documents from collection"""
    # Implementation: Read-only document retrieval
    
@mcp.resource("qdrant://search/{collection_name}")
async def search_collection(collection_name: str, query: str, top_k: int = 5) -> str:
    """Perform semantic search on collection"""
    # Implementation: Query-only search without result processing
```

#### Phase 2: CQRS Separation
```python
# Refactor existing tools to separate commands from queries
# KEEP: Tools for write operations (indexing, updating)
# MOVE: Search/retrieval operations to Resources

# Example separation:
# Tool: naive_retriever_tool() -> Command that processes and returns formatted results
# Resource: naive_search_resource() -> Query that returns raw search results
```

#### Phase 3: @ Mention Support
```python
# Enable Claude Desktop @ mention syntax
# @server:qdrant://collections/johnwick_baseline
# @server:qdrant://search/johnwick_semantic?query=action+scenes&top_k=3
```

### Implementation Prompts

**Prompt 1: Resource Interface Setup**
```bash
claude "Implement MCP Resources in src/mcp/resources.py that provide read-only access to Qdrant collections, following CQRS pattern where Resources handle queries and Tools handle commands"
```

**Prompt 2: CQRS Refactoring**
```bash
claude "Refactor existing MCP tools to separate query operations (move to Resources) from command operations (keep as Tools), ensuring no duplication of business logic from src/rag/"
```

**Prompt 3: Schema Integration**
```bash
claude "Update MCP server schema to expose both Tools and Resources, validate with tests/integration/verify_mcp.py, and ensure @ mention syntax works correctly"
```

### Success Criteria
- [ ] Resources accessible via `@server:qdrant://collections/johnwick_baseline`
- [ ] CQRS separation: queries use Resources, commands use Tools
- [ ] No duplication of RAG business logic
- [ ] Schema validation passes
- [ ] Performance improvement for read-only operations

---

## 2. Strategy Auto-Selection System (PRIORITY: HIGH)

### Current State
- **Gap**: Users must manually choose between 6 retrieval strategies
- **Impact**: Poor UX, suboptimal results when wrong strategy selected
- **Location**: `src/api/app.py`, `src/rag/retriever.py`

### Implementation Strategy

#### Phase 1: Query Analysis Engine
```python
# Add to src/rag/query_analyzer.py
class QueryAnalyzer:
    def analyze_query_type(self, query: str) -> dict:
        """Analyze query characteristics to recommend strategy"""
        return {
            "query_type": "factual|semantic|hybrid|specific",
            "complexity": "simple|medium|complex", 
            "domain_specificity": 0.0-1.0,
            "recommended_strategy": "naive|bm25|semantic|ensemble|...",
            "confidence": 0.0-1.0
        }
```

#### Phase 2: Strategy Router
```python
# Add to src/rag/strategy_router.py
class StrategyRouter:
    def __init__(self):
        self.strategies = {
            "naive": naive_retriever,
            "bm25": bm25_retriever,
            "semantic": semantic_retriever,
            "contextual_compression": contextual_compression_retriever,
            "multi_query": multi_query_retriever,
            "ensemble": ensemble_retriever
        }
        
    async def route_query(self, query: str) -> tuple[str, dict]:
        """Auto-select optimal strategy and execute"""
        analysis = QueryAnalyzer().analyze_query_type(query)
        strategy_name = analysis["recommended_strategy"]
        
        # Execute with fallback chain
        try:
            result = await self.strategies[strategy_name](query)
            return strategy_name, result
        except Exception:
            # Fallback to ensemble strategy
            return "ensemble", await self.strategies["ensemble"](query)
```

#### Phase 3: Performance Learning
```python
# Add Phoenix telemetry integration for strategy performance tracking
class StrategyPerformanceTracker:
    def track_strategy_performance(self, strategy: str, query: str, 
                                 response_time: float, quality_score: float):
        """Track strategy performance for continuous improvement"""
        # Implementation: Store performance metrics in Phoenix
        # Use for future strategy selection optimization
```

### Implementation Prompts

**Prompt 1: Query Analysis**
```bash
claude "Implement a QueryAnalyzer class that uses NLP techniques and heuristics to analyze query characteristics and recommend the optimal retrieval strategy from the 6 available options"
```

**Prompt 2: Strategy Router**
```bash
claude "Create a StrategyRouter that automatically selects and executes the best retrieval strategy based on query analysis, with fallback mechanisms and error handling"
```

**Prompt 3: Auto-Selection Endpoint**
```bash
claude "Add a new FastAPI endpoint /invoke/auto_retriever that uses strategy auto-selection, and ensure it's also available as an MCP tool with proper telemetry integration"
```

**Prompt 4: Performance Integration**
```bash
claude "Integrate Phoenix telemetry to track strategy selection accuracy and performance, enabling continuous improvement of auto-selection algorithms"
```

### Success Criteria
- [ ] New `/invoke/auto_retriever` endpoint working
- [ ] Query analysis accurately recommends strategies (>80% accuracy)
- [ ] Fallback mechanisms prevent failures
- [ ] Performance tracking via Phoenix telemetry
- [ ] MCP tool auto_retriever available

---

## 3. Security Framework Implementation (PRIORITY: HIGH)

### Current State
- **Gap**: Basic FastAPI security, no MCP-specific protections
- **Impact**: Production deployment risks, enterprise adoption blockers
- **Location**: `src/mcp/server.py`, `src/core/security.py` (new)

### Implementation Strategy

#### Phase 1: Input Validation Framework
```python
# Add to src/core/security.py
from pydantic import BaseModel, validator
import re

class SecureQueryValidator(BaseModel):
    query: str
    max_length: int = 1000
    
    @validator('query')
    def validate_query_safety(cls, v):
        """Prevent injection attacks and malicious queries"""
        # Block potentially dangerous patterns
        dangerous_patterns = [
            r'<script.*?>',  # XSS prevention
            r'javascript:',   # JavaScript injection
            r'sql.*?(drop|delete|update|insert)',  # SQL injection patterns
            r'exec\s*\(',    # Code execution attempts
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Query contains potentially dangerous content")
        
        if len(v) > cls.max_length:
            raise ValueError(f"Query exceeds maximum length of {cls.max_length}")
            
        return v
```

#### Phase 2: MCP Tool Security Wrapper
```python
# Add security decorators for MCP tools
def secure_mcp_tool(max_calls_per_minute: int = 60):
    """Security decorator for MCP tools with rate limiting and validation"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Rate limiting
            await rate_limiter.check_rate_limit(func.__name__)
            
            # Input validation
            validated_kwargs = {}
            for key, value in kwargs.items():
                if key == 'query':
                    validated_value = SecureQueryValidator(query=value).query
                    validated_kwargs[key] = validated_value
                else:
                    validated_kwargs[key] = value
            
            # Audit logging
            logger.info(f"MCP tool execution: {func.__name__}", extra={
                "tool_name": func.__name__,
                "args": args,
                "kwargs": validated_kwargs,
                "timestamp": datetime.utcnow()
            })
            
            return await func(*args, **validated_kwargs)
        return wrapper
    return decorator
```

#### Phase 3: Authentication & Authorization
```python
# Add to src/core/auth.py
class MCPAuthManager:
    def __init__(self):
        self.api_keys = set(os.getenv("MCP_API_KEYS", "").split(","))
        
    async def authenticate_request(self, api_key: str) -> bool:
        """Validate API key for MCP requests"""
        return api_key in self.api_keys
        
    async def authorize_tool_access(self, tool_name: str, user_context: dict) -> bool:
        """Check if user has permission to execute specific tool"""
        # Implementation: Role-based access control
        return True  # Placeholder
```

#### Phase 4: Audit Trail
```python
# Add comprehensive audit logging
class SecurityAuditLogger:
    def log_tool_execution(self, tool_name: str, user_id: str, 
                          inputs: dict, success: bool, error: str = None):
        """Log all tool executions for security audit"""
        audit_event = {
            "event_type": "mcp_tool_execution",
            "tool_name": tool_name,
            "user_id": user_id,
            "inputs": self._sanitize_inputs(inputs),
            "success": success,
            "error": error,
            "timestamp": datetime.utcnow(),
            "request_id": str(uuid.uuid4())
        }
        
        # Store in secure audit log
        security_logger.info(json.dumps(audit_event))
```

### Implementation Prompts

**Prompt 1: Input Validation**
```bash
claude "Implement comprehensive input validation for all MCP tools using Pydantic validators to prevent injection attacks, validate query lengths, and sanitize inputs"
```

**Prompt 2: Security Decorators**
```bash
claude "Create security decorator functions that wrap MCP tools with rate limiting, input validation, audit logging, and error handling"
```

**Prompt 3: Authentication System**
```bash
claude "Add API key authentication system for MCP server with role-based access control and audit trail logging for all tool executions"
```

**Prompt 4: Security Integration**
```bash
claude "Apply security framework to all existing MCP tools, update server configuration for production security, and add security health checks"
```

### Success Criteria
- [ ] All MCP tools protected with input validation
- [ ] Rate limiting prevents abuse (configurable limits)
- [ ] API key authentication working
- [ ] Comprehensive audit logging implemented
- [ ] Security health checks pass
- [ ] Production-ready security configuration

---

## Implementation Priority Order

### Week 1: MCP Resources (3-5 days)
**Rationale**: Architectural foundation improvement, enables true CQRS, relatively low risk

**Dependencies**: None
**Risk Level**: Low
**Impact**: High (doubles interface capabilities)

### Week 2: Security Framework (3-5 days)
**Rationale**: Production readiness requirement, enables enterprise adoption

**Dependencies**: None
**Risk Level**: Medium (requires thorough testing)
**Impact**: High (production deployment enabler)

### Week 3: Strategy Auto-Selection (5-7 days)
**Rationale**: User experience improvement, complex implementation

**Dependencies**: Phoenix telemetry working
**Risk Level**: Medium (affects core functionality)
**Impact**: High (eliminates user complexity)

## Validation & Testing Strategy

### For Each Implementation:
1. **Unit Tests**: Individual component testing
2. **Integration Tests**: End-to-end workflow testing
3. **Performance Tests**: Latency and throughput validation
4. **Security Tests**: Penetration testing and vulnerability assessment
5. **MCP Compliance**: Schema validation and protocol compliance

### Testing Commands:
```bash
# After each implementation
pytest tests/ -v -m "not requires_llm"  # Fast tests
python tests/integration/verify_mcp.py   # MCP validation
pytest tests/integration/ -v             # Full integration
python scripts/mcp/validate_mcp_schema.py # Schema compliance
```

---

*This roadmap provides concrete implementation guidance while respecting the existing architectural constraints and ensuring production readiness.*
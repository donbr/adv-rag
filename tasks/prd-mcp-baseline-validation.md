# PRD: MCP Ecosystem Baseline Validation & Developer Reference

## Problem Statement

**Direct Trigger**: Developers wasted 3+ hours building `semantic_retriever` variants that already existed in MCP tools.  
**Root Issue**: No discoverability led to duplicate work and debugging of existing capabilities.

## Goals

1. **Prevent duplicate MCP development** through comprehensive tool discovery
2. **Create quick reference for experienced developers** - no tutorials needed
3. **Validate existing tools work reliably** with thorough testing
4. **Deliver by Day 5** - fixed deadline for demo day

## Target Users

**Primary (80%): Experienced Developers**
- Need quick reference tables for tool selection  
- Require copy-paste code snippets  
- Zero tolerance for broken tools  

**Excluded**: PM overviews, junior tutorials (defer to Phase 2 if needed)

## User Stories

**As an experienced developer, I want to:**
- Quickly identify which MCP tool solves my specific use case
- Reference tools by ID (e.g., `MCP-RET-03`) in code reviews and standups
- Copy-paste working code examples without debugging
- Trust that documented tools actually work

**As an engineering team, we want to:**
- Eliminate duplicate MCP tool development
- Reference the tool catalog in all MCP-related tickets
- Have zero MCP redundancy tickets in Sprint 24

## Functional Requirements

### Phase 1: Test Existing Tools (Days 1-2)

#### 1. FastAPI MCP Tools Testing
**Scope**: 8 confirmed tools
- `naive_retriever`, `bm25_retriever`, `contextual_compression_retriever`  
- `multi_query_retriever`, `ensemble_retriever`, `semantic_retriever`
- `health_check_health_get`, `cache_stats_cache_stats_get`

**Testing Standard**: Thorough (not production-ready)
| Test Type | Scope |
|-----------|-------|
| Functional | 5+ realistic queries per tool |
| Edge Cases | Invalid inputs, timeout handling |
| **Excluded** | Load testing, benchmarks |

#### 2. External MCP Services Assessment
**Approach**: Test only if pre-configured
- Phoenix MCP tools (experiments, datasets, prompts)
- Qdrant MCP tools (code snippets, semantic memory)  
- Redis MCP tools (caching operations)
- Time/Brave Search/Fetch MCPs

**Documentation Format**: Accessibility status with ✅/❌ indicators
- Example: *"Phoenix MCPs: ❌ (endpoint unreachable)"*
- No new service setup required

#### 3. Schema Export/Validation Testing
- Run `export_mcp_schema.py` and `validate_mcp_schema.py`
- Verify MCP compliance of generated schemas
- Document any schema generation issues

### Phase 2: Create Developer Reference (Days 3-4)

#### 4. Quick Reference Tool Catalog
**Format**: Markdown tables optimized for experienced developers

```markdown
| Tool ID | Tool Name | Best For | Input Format | Example |
|---------|-----------|----------|--------------|---------|
| MCP-RET-01 | naive_retriever | Simple similarity search | `{"query": "text"}` | `{"query": "machine learning"}` |
| MCP-RET-02 | bm25_retriever | Keyword matching | `{"query": "text"}` | `{"query": "neural networks"}` |
```

**Requirements**:
- Tool IDs for easy reference in tickets/code reviews
- "Best For" column for quick tool selection
- Copy-paste ready examples
- No explanatory text - just facts

#### 5. Usage Guide for Integration
**Format**: Jupyter notebook with runnable examples

**Structure**:
```python
# MCP Tool Integration Patterns
# Tool: MCP-RET-01 (naive_retriever)
import requests

response = requests.post("http://localhost:8000/invoke/naive_retriever", 
                        json={"query": "your search term"})
result = response.json()
```

**Requirements**:
- Copy-paste code that works immediately
- Common integration patterns
- Error handling examples
- No tutorials - just working code

### Phase 3: Validation & Cleanup (Day 5)

#### 6. Final Validation
- Test all documented examples work
- Verify tool IDs are consistent
- Confirm accessibility status is accurate

#### 7. Integration with Development Process
- Link catalog in MCP-related ticket templates
- Add tool ID references to code review checklist
- Update development documentation

## Success Metrics

### Primary Success: Prevention
- **Target**: 0 duplicate MCP tool development tickets in Sprint 24
- **Verification**: Tool catalog referenced in all new MCP tickets

### Secondary Success: Adoption  
- Engineers reference tool IDs in standups and code reviews
- Copy-paste examples work without modification
- External MCP accessibility clearly documented

## Timeline (Fixed Deadline: Day 5)

```
Day 1-2: Tool Testing & Validation
├── FastAPI MCP tools (8 tools) - CRITICAL PATH
├── External MCP accessibility check
└── Schema validation

Day 3-4: Documentation Creation  
├── Quick reference catalog - CRITICAL PATH
├── Usage guide with examples
└── Integration patterns

Day 5: Demo Preparation
├── Final validation
├── Process integration
└── Demo delivery - HARD DEADLINE
```

**Flexibility**: External MCP testing depth can be reduced if blocking critical path.

## Deliverables

### Day 5 Demo Requirements
1. **Tool Catalog** (Markdown) - Quick reference with tool IDs
2. **Usage Guide** (Jupyter notebook) - Copy-paste examples  
3. **Accessibility Report** - External MCP status (✅/❌)
4. **Process Integration** - Updated ticket templates and checklists

### Success Validation
- Catalog prevents duplicate development (Sprint 24 metric)
- All examples work without debugging
- Tool IDs referenced in development process

## Risk Mitigation

**Risk**: External MCP services unavailable  
**Mitigation**: Document status as ❌, focus on FastAPI tools

**Risk**: Tool testing reveals broken functionality  
**Mitigation**: Document issues, fix only if critical path blocking

**Risk**: Day 5 deadline pressure  
**Mitigation**: Prioritize tool catalog over comprehensive examples

## Out of Scope

- New MCP tool development
- Junior developer tutorials  
- Performance benchmarking
- Production-ready testing
- External service configuration 
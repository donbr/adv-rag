# Product Requirements Document (PRD)
## Src/ Directory Reorganization for Educational Clarity

**Document Version:** 1.0  
**Created:** 2025-06-15  
**Status:** Draft  
**Target Implementation:** Q1 2025  

---

## 1. Problem Statement

### Current State
The existing `src/` directory structure mixes FastAPI endpoints, MCP server implementation, and RAG components without clear conceptual boundaries. This creates confusion for learners trying to understand:
- How RAG systems work independently
- How MCP servers are structured and implemented  
- How FastAPI applications are organized
- How these technologies integrate together

### Impact on Learning Experience
- **Cognitive Overload**: Students must parse multiple concepts simultaneously
- **Unclear Dependencies**: Hard to understand what belongs to which technology stack
- **Poor Instructional Flow**: No clear progression from individual concepts to integration
- **Maintenance Difficulty**: Changes to one concept affect understanding of others

## 2. Target User

**Primary:** Software engineering students and professionals learning RAG, MCP, and FastAPI integration

**Secondary:** Open source contributors and developers exploring the codebase

**Technical Level:** Intermediate developers with basic Python knowledge but new to RAG/MCP concepts

## 3. Core Functionality & Success Criteria

### Primary Goals
1. **Conceptual Clarity**: Each directory represents a distinct technical concept
2. **Learning Progression**: Clear path from individual concepts to integration
3. **Maintainability**: Easy to modify one concept without affecting others
4. **Industry Standards**: Follows established Python/FastAPI project structure patterns

### Success Metrics
- **Reduced Onboarding Time**: New developers can understand the structure in <10 minutes
- **Clear Dependencies**: Import statements clearly show cross-concept relationships
- **Modular Development**: Can work on RAG, MCP, or API components independently
- **Documentation Alignment**: Structure matches conceptual documentation flow

## 4. Proposed Solution

### New Directory Structure
Based on research from FastAPI best practices and MCP server patterns:

```
src/
├── __init__.py
├── main.py                 # Application entry point
├── core/                   # Shared infrastructure
│   ├── __init__.py
│   ├── settings.py         # Global configuration
│   ├── logging_config.py   # Logging setup
│   └── exceptions.py       # Global exceptions
├── api/                    # FastAPI implementation
│   ├── __init__.py
│   ├── main_api.py         # API routes and endpoints
│   ├── dependencies.py     # API-specific dependencies
│   └── middleware.py       # API middleware (if needed)
├── rag/                    # RAG system components
│   ├── __init__.py
│   ├── embeddings.py       # Embedding models
│   ├── vectorstore.py      # Vector store setup
│   ├── retriever.py        # Retrieval logic
│   ├── chain.py           # RAG chain implementation
│   └── data_loader.py     # Document processing
├── mcp/                    # MCP server implementation
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   ├── resources.py       # MCP resources
│   ├── tools.py           # MCP tools
│   └── transport.py       # Transport layer
└── integrations/          # External service integrations
    ├── __init__.py
    ├── redis_client.py    # Redis integration
    └── llm_models.py      # LLM model clients
```

### Migration Mapping

| Current File | New Location | Rationale |
|-------------|-------------|-----------|
| `main_api.py` | `api/main_api.py` | Clear API separation |
| `mcp_server/fastapi_wrapper.py` | `mcp/server.py` | MCP-focused organization |
| `mcp_server/resource_wrapper.py` | `mcp/resources.py` | Resource-specific functionality |
| `embeddings.py` | `rag/embeddings.py` | RAG component grouping |
| `vectorstore_setup.py` | `rag/vectorstore.py` | RAG infrastructure |
| `retriever_factory.py` | `rag/retriever.py` | Retrieval logic |
| `chain_factory.py` | `rag/chain.py` | Chain construction |
| `data_loader.py` | `rag/data_loader.py` | Data processing |
| `redis_client.py` | `integrations/redis_client.py` | External service |
| `llm_models.py` | `integrations/llm_models.py` | Model abstractions |
| `settings.py` | `core/settings.py` | Shared configuration |
| `logging_config.py` | `core/logging_config.py` | Shared infrastructure |

## 5. Non-Goals

- **Performance Optimization**: This is purely about structure, not performance
- **Feature Changes**: No modification to existing functionality
- **API Changes**: No changes to public interfaces
- **Dependency Updates**: No package version changes

## 6. Technical Requirements

### Must-Have Features
1. **Zero Breaking Changes**: All imports and functionality must work identically
2. **Clear Module Organization**: Each directory has a single responsibility
3. **Proper Python Packaging**: All directories are proper Python packages
4. **Import Path Updates**: All internal imports updated to new structure
5. **Documentation Updates**: README and docs reflect new structure

### Should-Have Features
1. **Educational Comments**: Each module has clear purpose documentation
2. **Dependency Visualization**: Clear import relationships between modules
3. **Example Usage**: Each module has usage examples in docstrings

### Could-Have Features
1. **Module-Level README**: Each directory has its own README explaining concepts
2. **Dependency Diagrams**: Visual representation of module relationships

## 7. Implementation Plan

### Phase 1: Infrastructure Setup (Week 1)
- Create new directory structure
- Set up proper `__init__.py` files
- Establish import patterns

### Phase 2: Core Components Migration (Week 1)
- Move shared infrastructure (`core/`)
- Update import statements
- Verify no breaking changes

### Phase 3: Domain-Specific Migration (Week 2)
- Migrate RAG components (`rag/`)
- Migrate MCP components (`mcp/`)
- Migrate API components (`api/`)
- Migrate integrations (`integrations/`)

### Phase 4: Testing & Validation (Week 2)
- Run all existing tests
- Verify MCP server functionality
- Test FastAPI endpoints
- Validate RAG pipeline

### Phase 5: Documentation Update (Week 3)
- Update import examples in README
- Update project structure documentation
- Add educational comments to modules

## 8. Risks & Mitigation

### High Risk
- **Import Conflicts**: Circular imports between modules
  - *Mitigation*: Careful dependency analysis and proper module boundaries

### Medium Risk  
- **Test Breakage**: Existing tests fail due to import changes
  - *Mitigation*: Comprehensive test run after each migration phase

### Low Risk
- **Documentation Lag**: Docs become outdated
  - *Mitigation*: Update docs as part of implementation, not afterward

## 9. Success Validation

### Automated Validation
- [ ] All existing tests pass
- [ ] MCP server starts without errors
- [ ] FastAPI application serves requests
- [ ] RAG pipeline processes queries
- [ ] Import statements work correctly

### Manual Validation
- [ ] New developer can understand structure in <10 minutes
- [ ] Each module's purpose is clear from its location
- [ ] Cross-module dependencies are obvious from imports
- [ ] Educational progression is logical (core → rag → mcp → api → integrations)

### Long-term Success Metrics
- Reduced time for new contributors to make their first PR
- Fewer questions about "where should this code go?"
- Easier maintenance and testing of individual components
- Better alignment with industry FastAPI/Python project standards

---

**Stakeholder Approval Required:**
- [ ] Project Maintainer
- [ ] Educational Content Reviewer
- [ ] Technical Architecture Review 
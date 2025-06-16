# Task List: Src/ Directory Reorganization

Generated from: `prd-src-reorganization.md`

## Relevant Files

- `src/core/__init__.py` - New package initialization for core shared components
- `src/core/settings.py` - Moved from `src/settings.py` - Global configuration management
- `src/core/logging_config.py` - Moved from `src/logging_config.py` - Shared logging setup
- `src/core/exceptions.py` - New file for global exceptions (if needed)
- `src/api/__init__.py` - New package initialization for FastAPI components
- `src/api/main_api.py` - Moved from `src/main_api.py` - FastAPI routes and endpoints
- `src/api/dependencies.py` - New file for API-specific dependencies (if needed)
- `src/rag/__init__.py` - New package initialization for RAG components
- `src/rag/embeddings.py` - Moved from `src/embeddings.py` - Embedding models
- `src/rag/vectorstore.py` - Moved from `src/vectorstore_setup.py` - Vector store setup
- `src/rag/retriever.py` - Moved from `src/retriever_factory.py` - Retrieval logic
- `src/rag/chain.py` - Moved from `src/chain_factory.py` - Chain construction
- `src/rag/data_loader.py` - Moved from `src/data_loader.py` - Document processing
- `src/mcp/__init__.py` - New package initialization for MCP components
- `src/mcp/server.py` - Moved from `src/mcp_server/fastapi_wrapper.py` - Main MCP server
- `src/mcp/resources.py` - Moved from `src/mcp_server/resource_wrapper.py` - MCP resources
- `src/mcp/tools.py` - New file for MCP tools (if needed)
- `src/mcp/transport.py` - New file for transport layer (if needed)
- `src/integrations/__init__.py` - New package initialization for external integrations
- `src/integrations/redis_client.py` - Moved from `src/redis_client.py` - Redis integration
- `src/integrations/llm_models.py` - Moved from `src/llm_models.py` - LLM model clients
- `src/main.py` - New or updated application entry point
- `run.py` - Updated to use new import paths
- `README.md` - Updated with new project structure documentation
- `docs/project-structure.md` - Updated with new organization

### Notes

- All `__init__.py` files should be created to make directories proper Python packages
- Import statements throughout the codebase will need to be updated to reflect new file locations
- Run all existing tests after each migration phase to ensure no breaking changes
- Use `pytest` to run tests: `pytest tests/` for all tests or `pytest tests/specific_test.py` for individual tests
- Keep backup of original structure until migration is fully validated
- Update any documentation that references old file paths
- Consider adding module-level docstrings explaining the purpose of each new directory

## Tasks

- [ ] 1.0 Create New Directory Structure and Infrastructure
  - [ ] 1.1 Create `src/core/` directory with `__init__.py`
  - [ ] 1.2 Create `src/api/` directory with `__init__.py`
  - [ ] 1.3 Create `src/rag/` directory with `__init__.py`
  - [ ] 1.4 Create `src/mcp/` directory with `__init__.py`
  - [ ] 1.5 Create `src/integrations/` directory with `__init__.py`
  - [ ] 1.6 Create or update `src/main.py` as application entry point
- [ ] 2.0 Migrate Core Shared Components
  - [ ] 2.1 Move `src/settings.py` to `src/core/settings.py`
  - [ ] 2.2 Move `src/logging_config.py` to `src/core/logging_config.py`
  - [ ] 2.3 Update imports in core components to use relative imports
  - [ ] 2.4 Create `src/core/exceptions.py` for global exceptions (if needed)
  - [ ] 2.5 Test core components can be imported from new locations
- [ ] 3.0 Migrate Domain-Specific Components (RAG, MCP, API, Integrations)
  - [ ] 3.1 Move `src/embeddings.py` to `src/rag/embeddings.py`
  - [ ] 3.2 Move `src/vectorstore_setup.py` to `src/rag/vectorstore.py`
  - [ ] 3.3 Move `src/retriever_factory.py` to `src/rag/retriever.py`
  - [ ] 3.4 Move `src/chain_factory.py` to `src/rag/chain.py`
  - [ ] 3.5 Move `src/data_loader.py` to `src/rag/data_loader.py`
  - [ ] 3.6 Move `src/main_api.py` to `src/api/main_api.py`
  - [ ] 3.7 Move `src/mcp_server/fastapi_wrapper.py` to `src/mcp/server.py`
  - [ ] 3.8 Move `src/mcp_server/resource_wrapper.py` to `src/mcp/resources.py`
  - [ ] 3.9 Move `src/redis_client.py` to `src/integrations/redis_client.py`
  - [ ] 3.10 Move `src/llm_models.py` to `src/integrations/llm_models.py`
  - [ ] 3.11 Remove old `src/mcp_server/` directory after migration
- [ ] 4.0 Update Import Statements and Dependencies
  - [ ] 4.1 Update all imports in RAG components to use new paths
  - [ ] 4.2 Update all imports in API components to use new paths
  - [ ] 4.3 Update all imports in MCP components to use new paths
  - [ ] 4.4 Update all imports in integration components to use new paths
  - [ ] 4.5 Update imports in `run.py` to use new structure
  - [ ] 4.6 Update imports in test files to use new paths
  - [ ] 4.7 Update any configuration files that reference old paths
- [ ] 5.0 Validate Migration and Update Documentation
  - [ ] 5.1 Run full test suite to ensure no breaking changes
  - [ ] 5.2 Test MCP server startup and functionality
  - [ ] 5.3 Test FastAPI application startup and endpoints
  - [ ] 5.4 Test RAG pipeline functionality
  - [ ] 5.5 Update `README.md` with new project structure
  - [ ] 5.6 Update `docs/project-structure.md` with new organization
  - [ ] 5.7 Add module-level docstrings explaining directory purposes
  - [ ] 5.8 Verify all imports work correctly in production environment 
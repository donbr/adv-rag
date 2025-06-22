# CLAUDE.md - MCP Usage Guide for Claude Code

**Target Audience**: Claude Code (CLI Tool)  
**Purpose**: Actionable guidance for effective MCP tool usage in Advanced RAG development

## Context: Two Different MCP Usage Patterns

### Claude (Web Interface) - Direct Function Access
- **Usage**: Direct function calls (e.g., `qdrant-code-snippets:qdrant-find`)
- **Permissions**: Automatic, no configuration needed
- **Context**: This is how I (Claude) access MCP tools in this conversation

### Claude Code (CLI) - Requires Configuration
- **Usage**: CLI commands with explicit permissions
- **Permissions**: Must use `--allowedTools` or configure settings
- **Context**: This is what YOU (Claude Code) need to use

## Quick Decision Matrix for Claude Code

| I Need To... | Use MCP Server | Command Pattern | Required Tools |
|--------------|----------------|-----------------|----------------|
| **Research FastMCP patterns** | `ai-docs-server` | Direct natural language query | None |
| **Find existing code examples** | `qdrant-code-snippets` | `--allowedTools "qdrant-find"` | qdrant-find |
| **Store new code patterns** | `qdrant-code-snippets` | `--allowedTools "qdrant-store"` | qdrant-store |
| **Remember project decisions** | `qdrant-semantic-memory` | `--allowedTools "qdrant-store"` | qdrant-store |
| **Recall past decisions** | `qdrant-semantic-memory` | `--allowedTools "qdrant-find"` | qdrant-find |
| **Get current time** | `mcp-server-time` | Check `/mcp` for available tools | Variable |
| **Web research** | `brave-search` | Check `/mcp` for available tools | Variable |

## Verified Working Commands for Claude Code

### Code Pattern Management (TESTED ✅)
```bash
# Store a new pattern - WORKING SYNTAX
claude -p --allowedTools "qdrant-store" "Store this FastMCP pattern in qdrant-code-snippets: mcp = FastMCP.from_fastapi(app=app)"

# Find existing patterns - WORKING SYNTAX
claude -p --allowedTools "qdrant-find" "Search qdrant-code-snippets for FastMCP conversion patterns"

# Verify storage worked - WORKING SYNTAX
claude -p --allowedTools "qdrant-find" "Find the FastMCP pattern I just stored"
```

### Project Context Management (TESTED ✅)
```bash
# Store architectural decision - WORKING SYNTAX
claude -p --allowedTools "qdrant-store" "Store in qdrant-semantic-memory: Decision - Use FastMCP.from_fastapi() for zero-duplication MCP conversion"

# Recall previous decisions - WORKING SYNTAX
claude -p --allowedTools "qdrant-find" "Search qdrant-semantic-memory for FastMCP decisions"

# Store development insights - WORKING SYNTAX  
claude -p --allowedTools "qdrant-store" "Remember in qdrant-semantic-memory: MCP resources provide faster access than full RAG pipeline"
```

### Documentation Research (TESTED ✅)
```bash
# ai-docs-server requires NO special permissions - just natural language
"Check ai-docs-server FastMCP documentation for resource registration patterns"
"Look up ai-docs-server MCP Protocol documentation for transport protocols"
"Reference ai-docs-server Anthropic documentation for Claude Code MCP configuration"
```

### Time Operations (TESTED ✅)
```bash
# Basic time query
"Get current time in Los Angeles timezone using mcp-server-time"

# For specific tool access, check what's available:
claude
> /mcp  # This shows all available tools from mcp-server-time
```

## Tested ai-docs-server Source Targeting

**VERIFIED**: These documentation sources are accessible and contain relevant content:

### FastMCP Development
- **Query**: `"Check ai-docs-server FastMCP documentation for [SPECIFIC_TOPIC]"`
- **Verified Content**: Server creation, resource registration, FastAPI conversion
- **Use For**: MCP server development, FastMCP.from_fastapi() patterns

### MCP Protocol Concepts  
- **Query**: `"Look up ai-docs-server MCP Protocol documentation for [SPECIFIC_CONCEPT]"`
- **Use For**: Protocol specifications, transport options, client-server architecture

### Claude Code Integration
- **Query**: `"Reference ai-docs-server Anthropic documentation for [SPECIFIC_FEATURE]"`
- **Use For**: CLI syntax, MCP configuration, permission settings

### LangChain RAG Development
- **Query**: `"Check ai-docs-server LangChain documentation for [SPECIFIC_NEED]"`
- **Use For**: LCEL patterns, retriever implementations, chain composition

## Verified Development Workflow

### Pattern: Research → Develop → Store → Validate (TESTED ✅)

#### 1. Research Phase
```bash
# ALWAYS start with existing knowledge
claude -p --allowedTools "qdrant-find" "Search qdrant-semantic-memory for previous work on [TOPIC]"

# Check specific documentation (NO permissions needed)
"Check ai-docs-server FastMCP documentation for [SPECIFIC_NEED]"

# Look for similar implementations
claude -p --allowedTools "qdrant-find" "Search qdrant-code-snippets for [RELATED_PATTERNS]"
```

#### 2. Development Phase
```bash
# Reference targeted documentation as needed (NO permissions needed)
"Look up ai-docs-server FastMCP documentation for resource registration patterns"

# Store insights during development
claude -p --allowedTools "qdrant-store" "Store in qdrant-semantic-memory: [LEARNING_OR_DECISION]"
```

#### 3. Storage Phase  
```bash
# Store successful patterns immediately
claude -p --allowedTools "qdrant-store" "Store this working pattern in qdrant-code-snippets: [PATTERN_WITH_CONTEXT]"
```

#### 4. Validation Phase (TESTED ✅)
```bash
# Verify pattern storage worked
claude -p --allowedTools "qdrant-find" "Find the [TOPIC] pattern I just stored"

# Check MCP server status
claude
> /mcp
```

## Permission Management for Claude Code

### Interactive Session (Recommended)
```bash
# Start interactive session
claude --verbose

# Grant permissions when prompted for each tool
> Search qdrant-code-snippets for FastMCP patterns
# Claude Code will ask: "Allow qdrant-find?" → Answer: Yes

> Store this pattern in qdrant-semantic-memory: [PATTERN]
# Claude Code will ask: "Allow qdrant-store?" → Answer: Yes
```

### Batch Operations (Testing)
```bash
# Skip permissions for testing only
claude -p --dangerously-skip-permissions "Search all MCP servers for FastMCP patterns"

# Pre-approve specific tools
claude -p --allowedTools "qdrant-find" "qdrant-store" "Search and store FastMCP patterns"
```

### Persistent Configuration (Production)
Add to `~/.claude/settings.json`:
```json
{
  "permissions": {
    "allow": [
      "qdrant-store",
      "qdrant-find"
    ]
  }
}
```

## Validation Checklist for Claude Code

### ✅ After Every MCP Operation:
```bash
# 1. Verify storage operations worked
claude -p --allowedTools "qdrant-find" "Find what I just stored about [TOPIC]"

# 2. Check MCP server status if issues arise
claude
> /mcp

# 3. Test with verbose mode if debugging needed
claude --verbose -p --allowedTools "qdrant-find" "test query"
```

## Internal MCP Architecture (Repository Develops)

### Two Distinct MCP Servers:

#### MCP Tools Server (`src/mcp/server.py`)
- **Purpose**: Expose RAG functionality as executable tools
- **Pattern**: `FastMCP.from_fastapi(app)` - automatic conversion  
- **Testing**: `python tests/integration/verify_mcp.py`

#### MCP Resources Server (`src/mcp/resources.py`)
- **Purpose**: CQRS read-only access to RAG data
- **Pattern**: Native FastMCP resources with URI patterns
- **Testing**: `python tests/integration/test_cqrs_resources.py`

### Development Commands:
```bash
# Test MCP conversion
python src/mcp/server.py

# Test resource server
python src/mcp/resources.py

# Use MCP Inspector
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/server.py
```

## Verified Success Metrics

**You're using MCP tools effectively when:**
- ✅ You can store and retrieve patterns without permission errors
- ✅ You find stored patterns from previous sessions
- ✅ You access ai-docs-server documentation without issues
- ✅ You use `/mcp` command to check server status when needed
- ✅ You build context across development sessions
- ✅ Your MCP operations complete successfully with proper permissions

---

**Key Principle**: Always query existing knowledge first, store new learnings immediately, and build context for future sessions. Use proper permission flags for Qdrant operations, but ai-docs-server works with direct queries.
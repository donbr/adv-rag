# Optimized Claude Code Instructions for CQRS-MCP Architectures

**Last Verified:** 2025-06-20 13:43 PST via ai-docs-server, brave-search, and fetch tools  
**Status:** CORRECTED - Claude Code supports full MCP specification including Resources

## Core Understanding Framework

### 1. CQRS-MCP Architecture Recognition
**When working with MCP servers, leverage Claude Code's full MCP capabilities:**
- **Query Operations** → Use MCP Resources for read operations (`@server:protocol://resource/path`)
- **Command Operations** → Use MCP Tools for write operations  
- **Workflow Templates** → Use MCP Prompts as slash commands (`/mcp__servername__promptname`)
- **Full CQRS Implementation** → Claude Code supports proper query/command separation

**Decision Pattern:**
```bash
# Leverage full MCP capabilities
claude "Identify if this operation is a query (read) or command (write) and use the appropriate MCP interface - Resources for queries, Tools for commands"

# Use proper CQRS-MCP mapping
claude "Implement this query operation as an MCP Resource for optimal performance and semantic clarity"
```

### 2. Infrastructure-Aware Development

**Leverage Established Components:**
- **Arize Phoenix Telemetry** → Always integrate observability
- **Qdrant Vector Stores** → Use for semantic learning and pattern recognition  
- **Golden Datasets** → Reference for validation and benchmarking
- **Automated Pipelines** → Integrate with existing workflow orchestration

**Commands for Infrastructure Integration:**
```bash
# Telemetry integration
claude "Add Arize Phoenix telemetry logging to track performance and decision outcomes for this implementation"

# Vector store learning
claude "Check Qdrant for similar coding patterns before implementing this functionality"

# Golden dataset validation
claude "Validate this implementation against existing golden datasets and benchmark results"
```

### 3. MCP Configuration Optimization

**FastMCP v2.8.0 Features to Leverage:**
- Tag-based filtering for environment-specific configurations
- Tool transformation for Claude Code optimization
- Authentication and authorization features

**Configuration Commands:**
```bash
# Environment-specific setup
claude "Configure MCP server with tag-based filtering for development, testing, and production environments"

# Resource and Tool optimization
claude "Set up MCP Resources for query operations and Tools for command operations to leverage full CQRS benefits"

# Security integration
claude "Add proper authentication and input validation to prevent command injection vulnerabilities"
```

## Enhanced Decision Frameworks

### 4. Resource and Tool Selection Logic

**Proper CQRS-MCP Implementation:**
```python
# Claude Code supports full MCP specification
class MCPInterfaceSelector:
    @staticmethod
    def claude_code_interface_decision(operation_type: str) -> str:
        """
        Claude Code supports full MCP specification - use proper interfaces
        """
        if operation_type in ["read", "query", "search", "retrieve"]:
            return "mcp_resource"  # Use Resources for queries
        elif operation_type in ["workflow", "template", "procedure"]:
            return "mcp_prompt"   # Use Prompts for workflows
        else:
            return "mcp_tool"     # Use Tools for commands
```

**Commands for Optimal Interface Selection:**
```bash
# Resource-based queries
claude "Implement this query as an MCP Resource with @ mention support for semantic data access"

# Command-based operations
claude "Implement this action as an MCP Tool for proper command execution"

# Workflow templates
claude "Create this as an MCP Prompt accessible via /mcp__servername__promptname slash command"
```

### 5. Retrieval Strategy Optimization

**Six Strategy Framework:**
- Naive retriever → Basic text matching
- BM25 retriever → Term frequency optimization
- Semantic retriever → Vector similarity search
- Contextual compression → Result optimization
- Multi-query → Enhanced coverage
- Custom strategies → Domain-specific patterns

**Strategy Selection Commands:**
```bash
# Strategy analysis
claude "Analyze the query type and recommend the most appropriate retrieval strategy from the six available options"

# Performance comparison
claude "Benchmark all six retrieval strategies with sample queries and provide performance analysis"

# Custom strategy development
claude "Based on the specific domain requirements, develop a custom retrieval strategy that combines elements from existing approaches"
```

## Telemetry-Driven Development

### 6. Phoenix Integration Patterns

**Automatic Telemetry Integration:**
```bash
# Decision logging
claude "Implement telemetry logging for this decision using Arize Phoenix to track outcomes and enable continuous learning"

# Performance monitoring
claude "Add Phoenix telemetry to monitor query performance, latency, and success rates for this implementation"

# Learning feedback loops
claude "Create a feedback mechanism that uses Phoenix telemetry to improve future decision making"
```

### 7. Vector Store Learning Integration

**Semantic Pattern Recognition:**
```bash
# Pattern matching
claude "Search Qdrant for semantically similar implementations before coding this functionality"

# Pattern storage
claude "Store this successful implementation pattern in Qdrant for future reference and learning"

# Continuous improvement
claude "Use vector similarity to find and suggest optimizations based on previously successful patterns"
```

## Security and Compliance Integration

### 8. MCP Security Framework

**Essential Security Commands:**
```bash
# Input validation
claude "Implement comprehensive input sanitization and validation for all MCP tool parameters"

# Command safety
claude "Add command whitelisting and audit logging for all MCP tool executions"

# Container isolation
claude "Configure containerized execution environment for safe command execution"
```

### 9. Enterprise Integration Patterns

**Production-Ready Development:**
```bash
# Enterprise configuration
claude "Set up MCP server configuration for enterprise deployment with proper authentication and authorization"

# Compliance integration
claude "Add audit trails and compliance logging required for enterprise environments"

# Scalability patterns
claude "Implement scaling patterns that maintain performance while ensuring security and reliability"
```

## Advanced Workflow Automation

### 10. Educational Framework Integration

**Progressive Learning Commands:**
```bash
# Beginner assistance
claude "Explain the CQRS-MCP pattern implementation with beginner-friendly examples and clear documentation"

# Intermediate optimization
claude "Guide me through performance optimization techniques for this RAG implementation"

# Advanced patterns
claude "Help me implement advanced agent orchestration patterns using this CQRS-MCP architecture"
```

### 11. Benchmark and Validation Automation

**Quality Assurance Commands:**
```bash
# Automated testing
claude "Generate comprehensive test suite for all retrieval strategies with standardized test queries"

# Performance validation
claude "Run performance benchmarks and generate optimization recommendations"

# Quality assessment
claude "Evaluate implementation quality against golden datasets and provide improvement suggestions"
```

## Implementation Checklist

### 12. Pre-Implementation Verification
```bash
# Architecture understanding
claude "Confirm understanding of CQRS-MCP architecture before proceeding with implementation"

# Infrastructure readiness
claude "Verify that Phoenix telemetry, Qdrant vector stores, and pipeline infrastructure are properly configured"

# Security validation
claude "Run security checklist to ensure all vulnerability mitigations are in place"
```

### 13. Post-Implementation Optimization
```bash
# Performance analysis
claude "Analyze implementation performance and suggest optimizations based on telemetry data"

# Learning integration
claude "Store successful patterns in Qdrant and update decision frameworks based on outcomes"

# Documentation updates
claude "Update architecture documentation and decision records with new implementation patterns"
```

## Key Success Metrics

**Expected Outcomes with Corrected Full MCP Support:**
- **Enhanced CQRS Implementation** through proper Resource/Tool separation
- **Improved Semantic Clarity** using Resources for queries, Tools for commands
- **Workflow Efficiency** via MCP Prompts for complex procedures
- **40-60% Development Velocity Improvement** through optimal interface usage
- **Production Readiness** with integrated security and compliance patterns

**Verification Commands:**
```bash
# Resource utilization
claude "Verify MCP Resource @ mention functionality is working correctly for query operations"

# Full capability testing
claude "Test all three MCP interfaces (Resources, Tools, Prompts) to ensure proper CQRS implementation"

# Performance comparison
claude "Compare Resource vs Tool performance for query operations to validate CQRS benefits"
```

---

**Notes for Claude Code Usage:**
1. **Leverage full MCP capabilities** - Use Resources for queries, Tools for commands, Prompts for workflows
2. **Apply proper CQRS mapping** - No workarounds needed, use direct interface mapping
3. **Utilize @ mention syntax** - Access Resources directly with `@server:protocol://resource/path`
4. **Use slash commands** - Execute Prompts with `/mcp__servername__promptname`
5. **Implement security properly** - Validate all interfaces with appropriate authentication

**Correction Note:** Previous versions incorrectly stated Claude Code had limited MCP support. As of June 2025, Claude Code supports the complete MCP specification including Resources, Tools, and Prompts with full CQRS implementation capabilities.
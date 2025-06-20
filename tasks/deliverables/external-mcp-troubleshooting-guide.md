# External MCP Services Troubleshooting Guide

## Overview

This guide provides systematic troubleshooting steps for resolving issues with external MCP services in the Advanced RAG system. It's based on real testing experience and common failure patterns identified during the MCP baseline validation process.

## Quick Diagnosis Table

| Symptom | Most Likely Cause | Quick Fix | Section |
|---------|-------------------|-----------|---------|
| "Connection closed" error | Service not running | Start the backend service | [Service Health](#service-health-checks) |
| "Invalid version request" | Incorrect package name | Verify MCP server package | [Package Issues](#package-installation-issues) |
| Tools hang during execution | Embedding model timeout | Check network/model access | [Execution Hangs](#tool-execution-hangs) |
| "No such tool" error | Tool discovery failure | Restart MCP server | [Tool Discovery](#tool-discovery-issues) |
| Cache miss every time | Redis connection failure | Verify Redis server | [Redis Specific](#redis-mcp-troubleshooting) |
| Empty dataset list | Phoenix not initialized | Check Phoenix server status | [Phoenix Specific](#phoenix-mcp-troubleshooting) |

---

## General Troubleshooting Workflow

### Step 1: Verify Backend Services
```bash
# Check if required services are running
docker-compose ps

# Expected output should show:
# - qdrant (healthy)
# - redis (healthy) 
# - phoenix (if configured)

# Or check individual services:
curl http://localhost:6333/health     # Qdrant
redis-cli ping                        # Redis (should return PONG)
curl http://localhost:6006/health     # Phoenix
```

### Step 2: Test MCP Server Installation
```bash
# Test each MCP server can be invoked
uvx @arize-ai/phoenix-mcp --help
uvx mcp-server-qdrant --help
uvx @modelcontextprotocol/server-redis --help

# If any fail, reinstall:
uvx install @arize-ai/phoenix-mcp
uvx install mcp-server-qdrant
uvx install @modelcontextprotocol/server-redis
```

### Step 3: Check Environment Variables
```bash
# Verify environment variables are set correctly
echo $REDIS_URL                    # Should be redis://localhost:6379
echo $COLLECTION_NAME              # Should be set for Qdrant
echo $FASTMCP_PORT                 # Should be unique for each Qdrant instance

# Check Cursor MCP configuration
cat ~/.cursor/mcp.json | jq '.mcpServers'
```

### Step 4: Test Individual Tool Operations
```bash
# Use our validated test scripts
python tests/integrations/test_redis_mcp.py
python tasks/temp-code/test_qdrant_semantic_memory_mcp.py
python tasks/temp-code/test_phoenix_mcp.py
```

---

## Service Health Checks

### Qdrant Health Check
```bash
# Check Qdrant server status
curl http://localhost:6333/health

# Expected response:
# {"status":"ok","version":"1.x.x"}

# Check collections
curl http://localhost:6333/collections

# Common issues:
# - Port 6333 not accessible → Start Qdrant server
# - Empty collections → Run ingestion pipeline
# - Permission denied → Check Docker user permissions
```

### Redis Health Check
```bash
# Test Redis connectivity
redis-cli ping
# Expected: PONG

redis-cli info server
# Check for any error messages

# Common issues:
# - Connection refused → Start Redis server
# - Permission denied → Check Redis authentication
# - Memory issues → Check Redis memory limits
```

### Phoenix Health Check
```bash
# Check Phoenix server
curl http://localhost:6006/health

# Check Phoenix UI accessibility
curl http://localhost:6006/

# Common issues:
# - Service not running → Start Phoenix server
# - Port conflicts → Check port 6006 availability
# - Database connection → Check Phoenix database configuration
```

---

## Package Installation Issues

### Invalid Version Request Errors
```bash
# Error: "Invalid version request: @modelcontextprotocol/server-redis"
# Solution: Update package manager and retry

# Clear uvx cache
uvx cache clear

# Reinstall with explicit version
uvx install @modelcontextprotocol/server-redis@latest

# Alternative: Use npx instead of uvx
npx @modelcontextprotocol/server-redis
```

### Package Not Found Errors
```bash
# If package installation fails:

# 1. Update package manager
pip install --upgrade uv

# 2. Check package name spelling
uvx search redis  # Search for available packages

# 3. Try alternative installation methods
npm install -g @modelcontextprotocol/server-redis
# Then use: npx @modelcontextprotocol/server-redis
```

### Dependency Conflicts
```bash
# If MCP server fails due to dependency issues:

# 1. Create isolated environment
uvx --isolated @arize-ai/phoenix-mcp

# 2. Check Python version compatibility
python --version  # MCP requires Python 3.8+

# 3. Clear Python cache
python -c "import sys; print(sys.path)"
# Remove any conflicting packages
```

---

## Tool Discovery Issues

### MCP Server Not Responding
```bash
# Test if MCP server starts correctly
timeout 10s uvx @arize-ai/phoenix-mcp

# If it hangs or times out:
# 1. Check if backend service is running
# 2. Verify environment variables
# 3. Try with debug logging

# Enable debug mode for more information
DEBUG=1 uvx @arize-ai/phoenix-mcp
```

### Tools List Empty or Incomplete
```python
# Test tool discovery programmatically
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def debug_tools():
    server_params = StdioServerParameters(
        command="uvx",
        args=["@arize-ai/phoenix-mcp"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                print(f"Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(debug_tools())
```

---

## Tool Execution Hangs

### Qdrant Code Snippets MCP Issue
**Known Issue**: Code Snippets MCP hangs during session initialization

**Root Cause**: Embedding model initialization timeout or configuration mismatch

**Troubleshooting Steps**:
```bash
# 1. Check embedding model access
python -c "
from sentence_transformers import SentenceTransformer
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print('✅ Embedding model accessible')
except Exception as e:
    print(f'❌ Embedding model error: {e}')
"

# 2. Test with increased timeout
TOKENIZERS_PARALLELISM=false uvx mcp-server-qdrant

# 3. Check network connectivity
curl -I https://huggingface.co/  # Should return 200 OK

# 4. Verify disk space for model downloads
df -h ~/.cache/  # Should have >1GB free
```

**Workaround**: Use Semantic Memory MCP instead, which works perfectly.

### General Execution Timeouts
```bash
# If tools execute but timeout:

# 1. Increase timeout in client code
# session = ClientSession(read, write, timeout=60.0)

# 2. Check resource usage
top -p $(pgrep -f "mcp-server")

# 3. Monitor network activity
netstat -an | grep :6333  # Qdrant
netstat -an | grep :6379  # Redis
```

---

## Redis MCP Troubleshooting

### Cache Miss Issues
```bash
# Check Redis connection in application
redis-cli monitor  # Watch real-time commands

# Test cache operations manually
redis-cli set test_key "test_value"
redis-cli get test_key
redis-cli del test_key

# Check cache key patterns
redis-cli keys "mcp_cache:*"
```

### Performance Issues
```bash
# Check Redis memory usage
redis-cli info memory

# Monitor slow queries
redis-cli config set slowlog-log-slower-than 1000
redis-cli slowlog get 10

# Check connection limits
redis-cli info clients
```

### Authentication Problems
```bash
# If Redis requires authentication:
redis-cli -a your_password ping

# Update REDIS_URL environment variable:
export REDIS_URL="redis://:password@localhost:6379"

# Test with updated URL
python tests/integrations/test_redis_mcp.py
```

---

## Phoenix MCP Troubleshooting

### Empty Dataset Issues
```bash
# Check if Phoenix has data
curl http://localhost:6006/v1/datasets

# If empty, check Phoenix data directory
ls -la ~/.phoenix/  # or your configured data dir

# Restart Phoenix with proper data directory
phoenix server --port 6006 --host 0.0.0.0
```

### Database Connection Errors
```bash
# Check Phoenix database configuration
python -c "
import phoenix as px
print('Phoenix config:', px.get_env())
"

# Test database connectivity
python -c "
import sqlite3
try:
    conn = sqlite3.connect(':memory:')
    print('✅ SQLite working')
    conn.close()
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

### Tool Permission Errors
```bash
# If Phoenix MCP tools fail with permissions:

# 1. Check Phoenix server logs
tail -f ~/.phoenix/logs/phoenix.log

# 2. Verify Phoenix API endpoints
curl http://localhost:6006/v1/experiments

# 3. Test with explicit authentication (if configured)
curl -H "Authorization: Bearer your_token" http://localhost:6006/v1/datasets
```

---

## Environment-Specific Issues

### Docker Container Issues
```bash
# If running in Docker containers:

# 1. Check container networking
docker network ls
docker network inspect adv-rag_default

# 2. Verify port mappings
docker port container_name

# 3. Check container logs
docker logs qdrant_container
docker logs redis_container

# 4. Test inter-container connectivity
docker exec -it app_container ping qdrant
docker exec -it app_container ping redis
```

### WSL2 Specific Issues
```bash
# If running on Windows WSL2:

# 1. Check WSL networking
cat /etc/resolv.conf

# 2. Verify localhost mapping
ping localhost
ping 127.0.0.1

# 3. Check Windows firewall
# Ensure ports 6333, 6379, 6006 are accessible

# 4. Restart WSL networking if needed
wsl --shutdown
# Then restart WSL
```

### Virtual Environment Issues
```bash
# Ensure virtual environment is activated
which python  # Should point to .venv/bin/python

# Verify MCP packages are installed
pip list | grep mcp

# Reinstall if needed
pip install --upgrade mcp

# Check Python path conflicts
python -c "import sys; print('\n'.join(sys.path))"
```

---

## Performance Troubleshooting

### Slow Response Times
```bash
# Monitor MCP tool performance
time python tasks/temp-code/test_redis_mcp.py

# Check system resources
htop
iostat 1 5
free -h

# Profile specific tools
python -m cProfile -o profile.out tasks/temp-code/test_phoenix_mcp.py
python -c "
import pstats
p = pstats.Stats('profile.out')
p.sort_stats('cumulative').print_stats(10)
"
```

### Memory Issues
```bash
# Check memory usage by service
docker stats  # If using Docker

# Monitor Python memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Check for memory leaks in long-running tests
# Run tests multiple times and monitor memory growth
```

---

## Advanced Debugging

### Enable Detailed Logging
```python
# Add to test scripts for detailed MCP logging
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("mcp").setLevel(logging.DEBUG)
logging.getLogger("fastmcp").setLevel(logging.DEBUG)
```

### Network Traffic Analysis
```bash
# Monitor MCP protocol traffic
tcpdump -i lo -A port 8002  # Qdrant Code Snippets
tcpdump -i lo -A port 8003  # Qdrant Semantic Memory

# Or use Wireshark for GUI analysis
```

### Protocol-Level Debugging
```python
# Test raw MCP protocol
import json
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def debug_protocol():
    server_params = StdioServerParameters(
        command="uvx",
        args=["@arize-ai/phoenix-mcp"]
    )
    
    async with stdio_client(server_params) as (read, write):
        # Send raw JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        write.write(json.dumps(request).encode() + b'\n')
        await write.drain()
        
        response = await read.readline()
        print("Raw response:", response.decode())

asyncio.run(debug_protocol())
```

---

## Recovery Procedures

### Complete Service Reset
```bash
# Nuclear option: reset everything
docker-compose down -v
docker system prune -f

# Clear MCP caches
uvx cache clear
rm -rf ~/.cache/uv/

# Restart all services
docker-compose up -d

# Verify all services
python tests/integrations/test_redis_mcp.py
python tasks/temp-code/test_qdrant_semantic_memory_mcp.py
python tasks/temp-code/test_phoenix_mcp.py
```

### Selective Service Restart
```bash
# Restart individual services
docker-compose restart qdrant
docker-compose restart redis

# Or if running directly:
pkill -f "redis-server"
redis-server &

pkill -f "qdrant"
docker run -d -p 6333:6333 qdrant/qdrant
```

---

## Prevention Best Practices

### Regular Health Monitoring
```bash
# Create health check script
cat > check_mcp_health.sh << 'EOF'
#!/bin/bash
echo "=== MCP Health Check ==="
echo "Qdrant: $(curl -s http://localhost:6333/health | jq -r .status)"
echo "Redis: $(redis-cli ping)"
echo "Phoenix: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:6006/health)"
echo "========================"
EOF

chmod +x check_mcp_health.sh
```

### Automated Testing
```bash
# Add to CI/CD pipeline or cron job
# Run every hour during development
0 * * * * /path/to/adv-rag/check_mcp_health.sh >> /var/log/mcp_health.log 2>&1
```

### Configuration Validation
```python
# Validate MCP configuration before running
import json
import os

def validate_mcp_config():
    config_path = os.path.expanduser("~/.cursor/mcp.json")
    if not os.path.exists(config_path):
        print("❌ MCP config not found")
        return False
    
    with open(config_path) as f:
        config = json.load(f)
    
    required_servers = ["phoenix", "qdrant-code-snippets", "qdrant-semantic-memory", "redis-mcp"]
    
    for server in required_servers:
        if server not in config.get("mcpServers", {}):
            print(f"❌ Missing MCP server: {server}")
            return False
    
    print("✅ MCP configuration valid")
    return True

if __name__ == "__main__":
    validate_mcp_config()
```

---

## Getting Help

### Community Resources
- **MCP Documentation**: https://modelcontextprotocol.io/docs
- **GitHub Issues**: 
  - Python SDK: https://github.com/modelcontextprotocol/python-sdk/issues
  - Servers: https://github.com/modelcontextprotocol/servers/issues
- **Discord Community**: Join the MCP Discord for real-time help

### Reporting Issues
When reporting MCP issues, include:
1. **Error messages** (full stack traces)
2. **Environment details** (OS, Python version, MCP SDK version)
3. **Configuration files** (sanitized)
4. **Reproduction steps** (minimal test case)
5. **Service logs** (Qdrant, Redis, Phoenix)

### Internal Project Support
- Check `tests/integrations/` for working examples
- Review `tasks/deliverables/external-mcp-services-documentation.md` for setup procedures
- Consult the task validation results in `tasks/tasks-prd-mcp-baseline-validation.md`

---

**Remember**: The MCP ecosystem is rapidly evolving. Always check for the latest versions and documentation when troubleshooting issues. 
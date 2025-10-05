# FastMCP Cloud Deployment Guide

> **Complete guide for deploying Advanced RAG MCP servers to FastMCP Cloud and self-hosted platforms**

## Table of Contents
- [Overview](#overview)
- [FastMCP Cloud Deployment](#fastmcp-cloud-deployment)
- [Self-Hosted Deployment Options](#self-hosted-deployment-options)
- [Local Testing with Cloud Transport](#local-testing-with-cloud-transport)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Advanced RAG system supports **three deployment modes**:

| Mode | Transport | Use Case | Performance |
|------|-----------|----------|-------------|
| **Local Development** | stdio | Claude Code CLI, MCP Inspector | Fastest (no network) |
| **FastMCP Cloud** | streamable-http | Managed cloud hosting | ~20-30s (tools), ~3-5s (resources) |
| **Self-Hosted Cloud** | streamable-http | Google Cloud Run, AWS Bedrock | Configurable |

### Architecture Highlights

- **Dual MCP Interface**: Tools (Command Pattern) + Resources (Query Pattern)
- **Zero Duplication**: `FastMCP.from_fastapi()` auto-converts endpoints to MCP tools
- **CQRS Pattern**: Separate servers for commands (full RAG) and queries (direct data)
- **6 Retrieval Strategies**: naive, bm25, semantic, compression, multiquery, ensemble

---

## FastMCP Cloud Deployment

### Prerequisites ✅

- Python 3.13+ ✅
- FastMCP 2.8.0+ ✅
- GitHub repository ✅
- `pyproject.toml` with dependencies ✅
- `fastmcp.json` configuration ✅

### Step 1: FastMCP Cloud Setup

1. **Visit FastMCP Cloud**
   ```bash
   open https://fastmcp.cloud
   ```

2. **Sign in with GitHub**
   - Authorize FastMCP Cloud to access your repositories
   - Select organization or personal account

3. **Create Project**
   - Click "New Project"
   - Select `adv-rag` repository
   - Project name: `advanced-rag` (or custom name)

### Step 2: Configure Project Settings

FastMCP Cloud reads configuration from `fastmcp.json` (already created):

```json
{
  "name": "adv-rag",
  "servers": [
    {
      "name": "adv-rag-tools",
      "entrypoint": "src/mcp/server.py:mcp",
      "transport": {
        "type": "auto",
        "streamable-http": { "port": 8001, "host": "0.0.0.0" }
      }
    },
    {
      "name": "adv-rag-resources",
      "entrypoint": "src/mcp/resources.py:mcp",
      "transport": {
        "type": "auto",
        "streamable-http": { "port": 8002, "host": "0.0.0.0" }
      }
    }
  ]
}
```

### Step 3: Configure Cloud Service Endpoints

**Required Services Setup (Free Tiers Available):**

#### 1. **Qdrant Cloud** (Free Tier: 1GB cluster)

```bash
# Sign up at https://cloud.qdrant.io
# Create a free cluster
# Get connection details:
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key
```

#### 2. **Phoenix Cloud** (Free Production Endpoint)

```bash
# Sign up at https://phoenix.arize.com
# Get your production endpoint:
PHOENIX_ENDPOINT=https://app.phoenix.arize.com
PHOENIX_API_KEY=your-phoenix-api-key
```

#### 3. **Redis Cloud Options** (Choose One)

**Option A: Upstash Redis** (Recommended - Serverless, ~Free for low traffic)
```bash
# Sign up at https://upstash.com
# Create serverless Redis database
# $0.20 per 100k requests, free tier available
REDIS_URL=rediss://default:your-password@your-endpoint.upstash.io:6379
```

**Option B: Render Redis** (Free Tier Available)
```bash
# Sign up at https://render.com
# Create Redis instance on free tier
REDIS_URL=redis://red-xxx:6379
```

**Option C: Railway Redis** (Usage-Based, ~$5/month for light usage)
```bash
# Sign up at https://railway.app
# Deploy Redis template
REDIS_URL=redis://default:password@host:port
```

**Note**: No widely-available free Redis cloud solution exists. Upstash offers best value for low-traffic applications with pay-as-you-go pricing. For development, consider disabling cache:

```env
CACHE_ENABLED=false  # Disable Redis dependency for testing
```

### Step 4: Configure Environment Variables in FastMCP Cloud

In FastMCP Cloud dashboard:

1. Navigate to **Project Settings** → **Environment Variables**
2. Add required variables:

   ```env
   # Required API Keys
   OPENAI_API_KEY=sk-...
   COHERE_API_KEY=...

   # Qdrant Cloud (Free Tier)
   QDRANT_URL=https://your-cluster.qdrant.io:6333
   QDRANT_API_KEY=your-qdrant-api-key

   # Phoenix Cloud (Free Production)
   PHOENIX_ENDPOINT=https://app.phoenix.arize.com
   PHOENIX_API_KEY=your-phoenix-api-key

   # Redis (Choose your provider or disable)
   REDIS_URL=rediss://default:password@your-endpoint.upstash.io:6379
   # OR disable caching:
   # CACHE_ENABLED=false
   ```

### Step 5: Deploy

**Automatic Deployment:**
```bash
# Push to main branch triggers automatic deployment
git add .
git commit -m "Configure FastMCP Cloud deployment"
git push origin main
```

**Branch Deployments:**
```bash
# Open PR triggers preview deployment
git checkout -b feature/new-retrieval-strategy
git push origin feature/new-retrieval-strategy
# Create PR → unique preview URL generated
```

### Step 5: Access Your Deployed Servers

FastMCP Cloud provides URLs for your servers:

```
Tools Server (Command Pattern):
https://adv-rag-tools-{your-org}.fastmcp.cloud

Resources Server (Query Pattern):
https://adv-rag-resources-{your-org}.fastmcp.cloud
```

### Step 6: Configure Claude Code to Use Cloud Servers

Update `.mcp.json` to point to cloud endpoints:

```json
{
  "mcpServers": {
    "adv-rag-tools-cloud": {
      "url": "https://adv-rag-tools-{your-org}.fastmcp.cloud",
      "transport": "streamable-http",
      "apiKey": "${FASTMCP_API_KEY}"
    },
    "adv-rag-resources-cloud": {
      "url": "https://adv-rag-resources-{your-org}.fastmcp.cloud",
      "transport": "streamable-http",
      "apiKey": "${FASTMCP_API_KEY}"
    }
  }
}
```

---

## Self-Hosted Deployment Options

### Option 1: Google Cloud Run

**Advantages:**
- Deploy in <10 minutes
- Auto-scaling (0 to N instances)
- Pay only for what you use
- Built-in HTTPS and authentication

**Deployment Steps:**

1. **Install Google Cloud SDK**
   ```bash
   # macOS
   brew install google-cloud-sdk

   # Linux
   curl https://sdk.cloud.google.com | bash
   ```

2. **Authenticate and Set Project**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Create Dockerfile** (if not exists)
   ```dockerfile
   FROM python:3.13-slim

   WORKDIR /app
   COPY . .

   RUN pip install uv && uv sync --no-dev

   # Tools Server
   CMD ["python", "src/mcp/server.py", "--transport", "streamable-http"]
   ```

4. **Deploy to Cloud Run**
   ```bash
   # Deploy Tools Server
   gcloud run deploy adv-rag-tools \
     --source . \
     --platform managed \
     --region us-central1 \
     --set-env-vars-file .env.cloud.local \
     --no-allow-unauthenticated \
     --port 8001

   # Deploy Resources Server
   gcloud run deploy adv-rag-resources \
     --source . \
     --platform managed \
     --region us-central1 \
     --set-env-vars-file .env.cloud.local \
     --no-allow-unauthenticated \
     --port 8002
   ```

5. **Get Service URLs**
   ```bash
   gcloud run services describe adv-rag-tools --region us-central1 --format 'value(status.url)'
   gcloud run services describe adv-rag-resources --region us-central1 --format 'value(status.url)'
   ```

### Option 2: AWS Bedrock AgentCore

**Advantages:**
- Native AWS integration
- Bedrock-optimized performance
- IAM-based authentication

**Deployment Steps:**

1. **Install AWS CLI**
   ```bash
   brew install awscli  # macOS
   pip install awscli   # Other platforms
   ```

2. **Configure AWS Credentials**
   ```bash
   aws configure
   ```

3. **Use Deployment Script** (from GitHub Gist)
   ```bash
   # Download deployment script
   curl -o deploy-aws.sh https://gist.githubusercontent.com/JayDoubleu/9b0b9d4d80f177ff70c9058d0ed45a93/raw/deploy-fastmcp-aws.sh

   chmod +x deploy-aws.sh
   ./deploy-aws.sh
   ```

4. **Verify Deployment**
   ```bash
   aws bedrock-agent-runtime list-agents
   ```

---

## Local Testing with Cloud Transport

Test streamable-http transport locally before deploying:

### Start Servers in Cloud Mode

**Terminal 1: Tools Server**
```bash
python src/mcp/server.py --transport streamable-http
# Server starts on http://0.0.0.0:8001
```

**Terminal 2: Resources Server**
```bash
python src/mcp/resources.py --transport streamable-http
# Server starts on http://0.0.0.0:8002
```

### Test with MCP Inspector

```bash
# Test Tools Server
npx @modelcontextprotocol/inspector http://localhost:8001

# Test Resources Server
npx @modelcontextprotocol/inspector http://localhost:8002
```

### Test with cURL

**Tools Server:**
```bash
# Call semantic_retriever tool
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "semantic_retriever",
      "arguments": {"question": "What makes John Wick popular?"}
    }
  }'
```

**Resources Server:**
```bash
# Read semantic_retriever resource
curl -X POST http://localhost:8002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "resources/read",
    "params": {
      "uri": "retriever://semantic_retriever/What makes John Wick popular?"
    }
  }'
```

---

## Troubleshooting

### Issue 1: Import Errors in Cloud Deployment

**Symptom**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Ensure `PYTHONPATH` includes project root
```python
# Already handled in server.py and resources.py
sys.path.insert(0, str(project_root))
```

### Issue 2: Environment Variables Not Loading

**Symptom**: `KeyError: 'OPENAI_API_KEY'`

**Solution**:
1. Verify `.env.cloud.local` exists with all required variables
2. For FastMCP Cloud: Set variables in dashboard
3. For Cloud Run: Use `--set-env-vars-file` flag
4. For AWS: Use Parameter Store or Secrets Manager

### Issue 3: Port Already in Use

**Symptom**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find and kill process using port 8001
lsof -ti:8001 | xargs kill -9

# Or use different ports
MCP_TOOLS_PORT=8003 MCP_RESOURCES_PORT=8004 python src/mcp/server.py --transport streamable-http
```

### Issue 4: Authentication Errors

**Symptom**: `401 Unauthorized` or `403 Forbidden`

**Solution**:
1. **FastMCP Cloud**: Ensure API key is set in client configuration
2. **Cloud Run**: Run with `--no-allow-unauthenticated` and configure IAM
3. **AWS**: Verify IAM roles have correct permissions

### Issue 5: Slow Response Times

**Symptom**: Queries taking >60 seconds

**Solution**:
1. Check `MCP_REQUEST_TIMEOUT` environment variable
2. Verify Qdrant and Redis connectivity
3. Review Phoenix telemetry for bottlenecks
4. Consider using Resources server (3-5x faster) instead of Tools

### Issue 6: FastMCP Cloud Build Failures

**Symptom**: Deployment fails during build

**Solution**:
1. Verify `pyproject.toml` has correct dependencies
2. Check Python version compatibility (>=3.13)
3. Review build logs in FastMCP Cloud dashboard
4. Ensure `fastmcp.json` syntax is valid

### Debug Commands

```bash
# Check server health
curl http://localhost:8001/health  # Tools server
curl http://localhost:8002/health  # Resources server

# View logs
tail -f logs/mcp_tools.log
tail -f logs/mcp_resources.log

# Test local vs cloud transport
python src/mcp/server.py  # stdio mode
python src/mcp/server.py --transport streamable-http  # cloud mode
```

---

## Performance Optimization

### 1. Enable Caching
```env
CACHE_ENABLED=true
REDIS_URL=redis://your-redis-instance:6379
```

### 2. Adjust Timeouts
```env
MCP_REQUEST_TIMEOUT=30  # seconds
MAX_SNIPPETS=10
```

### 3. Use Resources for Bulk Operations
- **Tools (Command)**: Full RAG with LLM synthesis (~20-30s)
- **Resources (Query)**: Direct data access (~3-5s)

### 4. Monitor with Phoenix
```env
PHOENIX_ENDPOINT=http://phoenix:6006
PHOENIX_AUTO_INSTRUMENT=true
```

---

## Next Steps

1. ✅ **Deploy to FastMCP Cloud** - Fastest way to get started
2. 📊 **Monitor with Phoenix** - View traces at http://localhost:6006
3. 🔧 **Customize Retrieval** - Add new strategies in `src/rag/`
4. 📈 **Scale Resources** - Adjust Cloud Run instances or AWS capacity
5. 🔐 **Secure Endpoints** - Enable authentication and rate limiting

---

## Additional Resources

- **FastMCP Documentation**: https://gofastmcp.com
- **FastMCP Cloud Dashboard**: https://fastmcp.cloud
- **MCP Protocol Spec**: https://modelcontextprotocol.io
- **Google Cloud Run Docs**: https://cloud.google.com/run/docs/host-mcp-servers
- **AWS Bedrock Docs**: https://docs.aws.amazon.com/bedrock/

---

**Questions or Issues?**
- Open an issue in the repository
- Check logs in `logs/mcp_*.log`
- Review Phoenix traces for detailed observability
- Consult FastMCP Cloud support (for managed deployments)

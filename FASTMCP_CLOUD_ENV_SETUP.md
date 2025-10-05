# FastMCP Cloud Environment Variables Setup

## ⚠️ Critical: Configure These Environment Variables

Your MCP servers are deployed but need environment variables configured in the FastMCP Cloud dashboard.

### Required Environment Variables

Navigate to **FastMCP Cloud Dashboard** → **Your Project** → **Settings** → **Environment Variables**

Add the following variables:

```env
# Core API Keys (REQUIRED for runtime)
OPENAI_API_KEY=sk-proj-...your-key-here...
COHERE_API_KEY=CVF8q8OOxXnblJgyxduI1LY5OFoBu8wTwgPhpR1a

# Qdrant Cloud (Free Tier)
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key

# Phoenix Cloud (Free Production Endpoint)
PHOENIX_ENDPOINT=https://app.phoenix.arize.com
PHOENIX_API_KEY=a1bf5cc43deb2c3d132:edaf3e5

# Upstash Redis (REST API)
UPSTASH_REDIS_REST_URL=https://supreme-dodo-19114.upstash.io
UPSTASH_REDIS_REST_TOKEN=AUqqAAIncDJjNTQ3ZTU1NDU4NTQ0ODBiOTk4NGJhZGEyZGE3MjExYnAyMTkxMTQ

# Optional: Traditional Redis URL (if your integration supports it)
# REDIS_URL=redis://default:token@supreme-dodo-19114.upstash.io:6379
```

### Environment Variables by Service

#### ✅ Already Configured (from your .env.cloud)
- `COHERE_API_KEY` - ✅ Have it
- `PHOENIX_API_KEY` - ✅ Have it (from your bashrc)
- `UPSTASH_REDIS_REST_URL` - ✅ Have it
- `UPSTASH_REDIS_REST_TOKEN` - ✅ Have it

#### ⚠️ Need to Add
- `OPENAI_API_KEY` - **REQUIRED** - Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- `QDRANT_URL` - Get from your Qdrant Cloud cluster dashboard
- `QDRANT_API_KEY` - Get from your Qdrant Cloud cluster settings

### Steps to Configure

1. **Visit FastMCP Cloud Dashboard**
   ```
   https://fastmcp.cloud/projects/your-project/settings
   ```

2. **Navigate to Environment Variables**
   - Click on your project (`adv-rag` or `still-blush-spoonbill`)
   - Go to "Settings" tab
   - Find "Environment Variables" section

3. **Add Variables One by One**
   - Click "Add Environment Variable"
   - Name: `OPENAI_API_KEY`
   - Value: `sk-proj-...` (your actual key)
   - Click "Save"
   - Repeat for all variables above

4. **Trigger Redeploy**
   - After adding all variables, trigger a redeploy
   - Either: Push a new commit to GitHub
   - Or: Use FastMCP Cloud's "Redeploy" button

### Verification

After deployment with environment variables:

```bash
# Test the deployed server
curl -X POST "https://objective-copper-narwhal.fastmcp.app/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "resources/list"
  }'
```

Expected response: List of available resources (not an error about missing API keys)

### Troubleshooting

**Error**: `The api_key client option must be set`
- **Solution**: Add `OPENAI_API_KEY` in FastMCP Cloud environment variables

**Error**: `[Errno 30] Read-only file system`
- **Solution**: ✅ Already fixed in latest commit (dd4a47f)

**Error**: Qdrant connection refused
- **Solution**: Verify `QDRANT_URL` and `QDRANT_API_KEY` are correct

### Cloud Service Setup Links

- **OpenAI API Keys**: https://platform.openai.com/api-keys
- **Qdrant Cloud**: https://cloud.qdrant.io
- **Phoenix Cloud**: https://phoenix.arize.com
- **Upstash Redis**: https://console.upstash.com

### Security Notes

⚠️ **Never commit API keys to GitHub**
- Environment variables in FastMCP Cloud are encrypted
- They're injected at runtime only
- Not visible in build logs

✅ **Best Practices**:
- Rotate API keys regularly
- Use separate keys for development vs production
- Monitor usage in respective service dashboards

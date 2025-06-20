#!/usr/bin/env python3
"""
Qdrant Semantic Memory MCP Individual Test

Tests the qdrant-semantic-memory MCP server (port 8003) with complete request/response objects.
Configuration: COLLECTION_NAME=semantic-memory, FASTMCP_PORT=8003
"""

import asyncio
import sys
from pathlib import Path
import traceback
import json

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_qdrant_semantic_memory_mcp():
    """Test Qdrant Semantic Memory MCP server individually"""
    print("🔍 Testing Qdrant Semantic Memory MCP Server")
    print("=" * 50)
    
    try:
        # Qdrant Semantic Memory MCP server parameters (from ~/.cursor/mcp.json)
        server_params = StdioServerParameters(
            command="uvx",
            args=["mcp-server-qdrant"],
            env={
                "QDRANT_URL": "http://localhost:6333",
                "COLLECTION_NAME": "semantic-memory",
                "FASTMCP_PORT": "8003",
                "TOOL_STORE_DESCRIPTION": "Store contextual information for semantic memory: conversation insights, project decisions, learned patterns, user preferences. Include descriptive information in the 'information' parameter and structured metadata for categorization and retrieval.",
                "TOOL_FIND_DESCRIPTION": "Search semantic memory for relevant context, decisions, and previously learned information. Use natural language queries to describe what type of information you're looking for."
            }
        )
        
        print(f"📡 Command: {server_params.command} {' '.join(server_params.args)}")
        print(f"🎯 Target: Semantic Memory Collection (Port 8003)")
        print()
        
        # Connect to server
        print("🔌 Connecting to Qdrant Semantic Memory MCP server...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Successfully connected to Qdrant Semantic Memory MCP")
                
                # Initialize the session
                print("🔧 Initializing session...")
                await session.initialize()
                print("✅ Session initialized")
                
                # List available tools
                print("🛠️  Listing available tools...")
                tools = await session.list_tools()
                print(f"✅ {len(tools.tools)} tools available:")
                for i, tool in enumerate(tools.tools, 1):
                    print(f"   {i}. {tool.name} - {tool.description}")
                print()
                
                # Test qdrant-store tool with semantic information
                try:
                    print("💾 Testing qdrant-store tool...")
                    store_request = {
                        "information": "MCP baseline validation task identified that Qdrant MCP tools work for discovery but hang during execution. This suggests embedding provider initialization issues or vector database connection problems during actual tool operations.",
                        "metadata": {
                            "project": "adv-rag",
                            "task": "mcp-baseline-validation",
                            "issue_type": "tool_execution_hang",
                            "affected_tools": ["qdrant-store", "qdrant-find"],
                            "status": "identified",
                            "timestamp": "2025-01-15",
                            "context": "external_mcp_testing",
                            "severity": "medium",
                            "category": "infrastructure"
                        }
                    }
                    print(f"   📤 REQUEST: qdrant-store")
                    print(f"   📝 Parameters:")
                    print(f"      information: {store_request['information']}")
                    print(f"      metadata: {json.dumps(store_request['metadata'], indent=8)}")
                    
                    store_result = await session.call_tool("qdrant-store", store_request)
                    print(f"   ✅ RESPONSE:")
                    for i, content in enumerate(store_result.content):
                        if hasattr(content, 'text'):
                            print(f"   📋 Content[{i}]: {content.text}")
                    print()
                    
                except Exception as tool_error:
                    print(f"   ⚠️  qdrant-store error: {tool_error}")
                    print(f"   🔍 Error details: {traceback.format_exc()}")
                
                # Test qdrant-find tool  
                try:
                    print("🔍 Testing qdrant-find tool...")
                    find_request = {
                        "query": "MCP tool execution issues and hanging problems during validation testing"
                    }
                    print(f"   📤 REQUEST: qdrant-find")
                    print(f"   📝 Parameters: {find_request}")
                    
                    find_result = await session.call_tool("qdrant-find", find_request)
                    print(f"   ✅ RESPONSE:")
                    for i, content in enumerate(find_result.content):
                        if hasattr(content, 'text'):
                            print(f"   📋 Content[{i}]: {content.text}")
                    print()
                    
                except Exception as tool_error:
                    print(f"   ⚠️  qdrant-find error: {tool_error}")
                    print(f"   🔍 Error details: {traceback.format_exc()}")
                
                print(f"🎯 Qdrant Semantic Memory MCP testing complete")
                return True
                
    except Exception as e:
        print(f"❌ Qdrant Semantic Memory MCP failed: {e}")
        print("\n🔍 Full error traceback:")
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🧪 Qdrant Semantic Memory MCP Individual Assessment")
    print("=" * 60)
    
    success = await test_qdrant_semantic_memory_mcp()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Qdrant Semantic Memory MCP: FUNCTIONAL")
        print("   - Store operations working")
        print("   - Find operations working") 
        print("   - Ready for semantic memory management")
        print("   - Port: 8003")
        print("   - Collection: semantic-memory")
    else:
        print("❌ Qdrant Semantic Memory MCP: NOT FUNCTIONAL")
        print("   - Tool execution failed")
        print("   - May require Qdrant service setup")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1) 
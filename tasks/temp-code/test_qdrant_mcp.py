#!/usr/bin/env python3
"""
Qdrant MCP Individual Test Script

Tests both Qdrant MCP servers individually:
1. Qdrant Code Snippets MCP (port 8002)
2. Qdrant Semantic Memory MCP (port 8003)
"""

import asyncio
import sys
from pathlib import Path
import traceback

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_qdrant_code_snippets():
    """Test Qdrant Code Snippets MCP server"""
    print("🔍 Testing Qdrant Code Snippets MCP Server")
    print("=" * 50)
    
    try:
        # Qdrant Code Snippets MCP server parameters (from Cursor config)
        server_params = StdioServerParameters(
            command="uvx",
            args=["mcp-server-qdrant"],
            env={
                "QDRANT_URL": "http://localhost:6333",
                "COLLECTION_NAME": "code-snippets",
                "FASTMCP_PORT": "8002"
            }
        )
        
        print(f"Command: {server_params.command} {' '.join(server_params.args)}")
        print("Environment: QDRANT_URL=http://localhost:6333")
        print()
        
        # Connect to server
        print("📡 Connecting to Qdrant Code Snippets MCP server...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Successfully connected to Qdrant Code Snippets MCP")
                
                # Initialize the session
                print("🔧 Initializing session...")
                await session.initialize()
                print("✅ Session initialized")
                
                # List available tools
                print("🛠️  Listing available tools...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                print(f"✅ Qdrant Code Snippets MCP: {len(tools)} tools available")
                for i, tool in enumerate(tools, 1):
                    print(f"   {i}. {tool.name} - {tool.description}")
                
                return True, len(tools)
                
    except Exception as e:
        print(f"❌ Qdrant Code Snippets MCP failed: {e}")
        print("\n🔍 Full error traceback:")
        traceback.print_exc()
        return False, 0

async def test_qdrant_semantic_memory():
    """Test Qdrant Semantic Memory MCP server"""
    print("\n🔍 Testing Qdrant Semantic Memory MCP Server")
    print("=" * 50)
    
    try:
        # Qdrant Semantic Memory MCP server parameters (from Cursor config)
        server_params = StdioServerParameters(
            command="uvx",
            args=["mcp-server-qdrant"],
            env={
                "QDRANT_URL": "http://localhost:6333",
                "COLLECTION_NAME": "semantic-memory",
                "FASTMCP_PORT": "8003"
            }
        )
        
        print(f"Command: {server_params.command} {' '.join(server_params.args)}")
        print("Environment: QDRANT_URL=http://localhost:6333")
        print()
        
        # Connect to server
        print("📡 Connecting to Qdrant Semantic Memory MCP server...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Successfully connected to Qdrant Semantic Memory MCP")
                
                # Initialize the session
                print("🔧 Initializing session...")
                await session.initialize()
                print("✅ Session initialized")
                
                # List available tools
                print("🛠️  Listing available tools...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                print(f"✅ Qdrant Semantic Memory MCP: {len(tools)} tools available")
                for i, tool in enumerate(tools, 1):
                    print(f"   {i}. {tool.name} - {tool.description}")
                
                return True, len(tools)
                
    except Exception as e:
        print(f"❌ Qdrant Semantic Memory MCP failed: {e}")
        print("\n🔍 Full error traceback:")
        traceback.print_exc()
        return False, 0

async def main():
    """Main test function"""
    print("🧪 Qdrant MCP Services Individual Assessment")
    print("=" * 60)
    
    # Test both Qdrant MCP services
    code_success, code_tools = await test_qdrant_code_snippets()
    memory_success, memory_tools = await test_qdrant_semantic_memory()
    
    print("\n" + "=" * 60)
    print("📊 QDRANT MCP ASSESSMENT RESULTS:")
    print()
    
    if code_success:
        print("✅ Qdrant Code Snippets MCP: ACCESSIBLE")
        print(f"   - {code_tools} tools available")
        print("   - Ready for code snippet storage/retrieval")
    else:
        print("❌ Qdrant Code Snippets MCP: NOT ACCESSIBLE")
        print("   - Connection failed")
        print("   - May require Qdrant service or proper configuration")
    
    print()
    
    if memory_success:
        print("✅ Qdrant Semantic Memory MCP: ACCESSIBLE")
        print(f"   - {memory_tools} tools available")
        print("   - Ready for semantic memory operations")
    else:
        print("❌ Qdrant Semantic Memory MCP: NOT ACCESSIBLE")
        print("   - Connection failed") 
        print("   - May require Qdrant service or proper configuration")
    
    print()
    overall_success = code_success or memory_success
    print(f"📋 Overall Qdrant MCP Status: {'✅ PARTIAL/FULL ACCESS' if overall_success else '❌ NO ACCESS'}")
    
    return overall_success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1) 
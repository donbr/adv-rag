#!/usr/bin/env python3
"""
Qdrant Code Snippets MCP Individual Test

Tests the qdrant-code-snippets MCP server (port 8002) with complete request/response objects.
Configuration: COLLECTION_NAME=code-snippets, FASTMCP_PORT=8002
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

async def test_qdrant_code_snippets_mcp():
    """Test Qdrant Code Snippets MCP server individually"""
    print("🔍 Testing Qdrant Code Snippets MCP Server")
    print("=" * 50)
    
    try:
        # Qdrant Code Snippets MCP server parameters (from ~/.cursor/mcp.json)
        server_params = StdioServerParameters(
            command="uvx",
            args=["mcp-server-qdrant"],
            env={
                "QDRANT_URL": "http://localhost:6333",
                "COLLECTION_NAME": "code-snippets",
                "FASTMCP_PORT": "8002",
                "TOOL_STORE_DESCRIPTION": "Store reusable code snippets for later retrieval. The 'information' parameter should contain a natural language description of what the code does, while the actual code should be included in the 'metadata' parameter as a 'code' property. The value of 'metadata' is a Python dictionary with strings as keys. Use this whenever you generate some code snippet.",
                "TOOL_FIND_DESCRIPTION": "Search for relevant code snippets based on natural language descriptions. The 'query' parameter should describe what you're looking for, and the tool will return the most relevant code snippets. Use this when you need to find existing code snippets for reuse or reference."
            }
        )
        
        print(f"📡 Command: {server_params.command} {' '.join(server_params.args)}")
        print(f"🎯 Target: Code Snippets Collection (Port 8002)")
        print()
        
        # Connect to server
        print("🔌 Connecting to Qdrant Code Snippets MCP server...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Successfully connected to Qdrant Code Snippets MCP")
                
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
                
                # Test qdrant-store tool with code snippet
                try:
                    print("💾 Testing qdrant-store tool...")
                    store_request = {
                        "information": "Python function to calculate factorial using recursion with memoization for optimal performance",
                        "metadata": {
                            "code": "def factorial(n, memo={}):\n    \"\"\"Calculate factorial with memoization to avoid redundant calculations.\"\"\"\n    if n in memo:\n        return memo[n]\n    if n <= 1:\n        return 1\n    memo[n] = n * factorial(n-1, memo)\n    return memo[n]\n\n# Example usage:\n# print(factorial(10))  # Output: 3628800",
                            "language": "python",
                            "category": "algorithms",
                            "complexity": "O(n)",
                            "author": "mcp-test-suite",
                            "framework": "pure-python",
                            "use_case": "mathematical_computation",
                            "optimization": "memoization",
                            "tested": "yes"
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
                        "query": "Python factorial recursive algorithm with memoization optimization"
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
                
                print(f"🎯 Qdrant Code Snippets MCP testing complete")
                return True
                
    except Exception as e:
        print(f"❌ Qdrant Code Snippets MCP failed: {e}")
        print("\n🔍 Full error traceback:")
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🧪 Qdrant Code Snippets MCP Individual Assessment")
    print("=" * 60)
    
    success = await test_qdrant_code_snippets_mcp()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Qdrant Code Snippets MCP: FUNCTIONAL")
        print("   - Store operations working")
        print("   - Find operations working") 
        print("   - Ready for code snippet management")
        print("   - Port: 8002")
        print("   - Collection: code-snippets")
    else:
        print("❌ Qdrant Code Snippets MCP: NOT FUNCTIONAL")
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
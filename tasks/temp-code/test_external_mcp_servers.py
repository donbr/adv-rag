#!/usr/bin/env python3
"""
External MCP Services Accessibility Assessment

Tests all external MCP servers configured in Cursor:
1. Phoenix MCP (@arizeai/phoenix-mcp)
2. Redis MCP (@modelcontextprotocol/server-redis)
3. Qdrant Code Snippets (mcp-server-qdrant)
4. Qdrant Semantic Memory (mcp-server-qdrant)
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any
import json

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class ExternalMCPTester:
    """Test external MCP servers for accessibility and functionality"""
    
    def __init__(self):
        self.results = {}
        
    async def test_phoenix_mcp(self) -> Dict[str, Any]:
        """Test Phoenix MCP Server (@arizeai/phoenix-mcp)"""
        print("\n🔍 Testing Phoenix MCP Server...")
        
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@arizeai/phoenix-mcp@latest", "--baseUrl", "http://localhost:6006/"],
            env={}
        )
        
        try:
            async with stdio_client(server_params) as (stdio, write):
                async with ClientSession(stdio, write) as session:
                    await session.initialize()
                    
                    # List tools
                    tools_result = await session.list_tools()
                    tools = [{"name": t.name, "description": t.description} for t in tools_result.tools]
                    
                    # List resources  
                    resources_result = await session.list_resources()
                    resources = [{"uri": r.uri, "name": r.name} for r in resources_result.resources]
                    
                    # Test a simple tool if available
                    test_result = None
                    if tools:
                        try:
                            # Try list-projects if available
                            for tool in tools_result.tools:
                                if "project" in tool.name.lower() and "list" in tool.name.lower():
                                    test_result = await session.call_tool(tool.name, {})
                                    break
                        except Exception as e:
                            test_result = f"Tool test failed: {e}"
                    
                    result = {
                        "status": "✅ SUCCESS",
                        "tools_count": len(tools),
                        "resources_count": len(resources),
                        "tools": tools[:5],  # First 5 tools
                        "resources": resources[:3],  # First 3 resources
                        "test_result": str(test_result) if test_result else "No test performed"
                    }
                    
                    print(f"✅ Phoenix MCP: {len(tools)} tools, {len(resources)} resources")
                    return result
                    
        except Exception as e:
            result = {
                "status": "❌ FAILED",
                "error": str(e),
                "tools_count": 0,
                "resources_count": 0
            }
            print(f"❌ Phoenix MCP failed: {e}")
            return result
    
    async def test_redis_mcp(self) -> Dict[str, Any]:
        """Test Redis MCP Server (@modelcontextprotocol/server-redis)"""
        print("\n🔍 Testing Redis MCP Server...")
        
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-redis"],
            env={"REDIS_URL": "redis://localhost:6379"}
        )
        
        try:
            async with stdio_client(server_params) as (stdio, write):
                async with ClientSession(stdio, write) as session:
                    await session.initialize()
                    
                    # List tools
                    tools_result = await session.list_tools()
                    tools = [{"name": t.name, "description": t.description} for t in tools_result.tools]
                    
                    # Test SET/GET if available
                    test_result = None
                    set_tool = None
                    get_tool = None
                    
                    for tool in tools_result.tools:
                        if tool.name.upper() == "SET":
                            set_tool = tool
                        elif tool.name.upper() == "GET":
                            get_tool = tool
                    
                    if set_tool and get_tool:
                        try:
                            # Test SET
                            await session.call_tool("SET", {"key": "mcp_test", "value": "test_value"})
                            # Test GET
                            get_result = await session.call_tool("GET", {"key": "mcp_test"})
                            test_result = f"SET/GET test successful: {get_result}"
                        except Exception as e:
                            test_result = f"SET/GET test failed: {e}"
                    
                    result = {
                        "status": "✅ SUCCESS",
                        "tools_count": len(tools),
                        "tools": tools[:5],
                        "test_result": str(test_result) if test_result else "No SET/GET tools found"
                    }
                    
                    print(f"✅ Redis MCP: {len(tools)} tools")
                    return result
                    
        except Exception as e:
            result = {
                "status": "❌ FAILED", 
                "error": str(e),
                "tools_count": 0
            }
            print(f"❌ Redis MCP failed: {e}")
            return result
    
    async def test_qdrant_code_snippets(self) -> Dict[str, Any]:
        """Test Qdrant Code Snippets MCP Server (mcp-server-qdrant)"""
        print("\n🔍 Testing Qdrant Code Snippets MCP Server...")
        
        server_params = StdioServerParameters(
            command="uvx",
            args=["mcp-server-qdrant"],
            env={
                "QDRANT_URL": "http://localhost:6333",
                "COLLECTION_NAME": "code-snippets",
                "FASTMCP_PORT": "8002"
            }
        )
        
        try:
            async with stdio_client(server_params) as (stdio, write):
                async with ClientSession(stdio, write) as session:
                    await session.initialize()
                    
                    # List tools
                    tools_result = await session.list_tools()
                    tools = [{"name": t.name, "description": t.description} for t in tools_result.tools]
                    
                    # Test store/find if available
                    test_result = None
                    store_tool = None
                    find_tool = None
                    
                    for tool in tools_result.tools:
                        if "store" in tool.name.lower():
                            store_tool = tool
                        elif "find" in tool.name.lower():
                            find_tool = tool
                    
                    if store_tool and find_tool:
                        try:
                            # Test store
                            await session.call_tool(store_tool.name, {
                                "information": "Simple Hello World function",
                                "metadata": {"code": "def hello(): return 'Hello World!'", "language": "python"}
                            })
                            # Test find
                            find_result = await session.call_tool(find_tool.name, {"query": "hello world function"})
                            test_result = f"Store/Find test successful: {len(str(find_result))} chars returned"
                        except Exception as e:
                            test_result = f"Store/Find test failed: {e}"
                    
                    result = {
                        "status": "✅ SUCCESS",
                        "tools_count": len(tools),
                        "tools": tools,
                        "test_result": str(test_result) if test_result else "No store/find tools found"
                    }
                    
                    print(f"✅ Qdrant Code Snippets: {len(tools)} tools")
                    return result
                    
        except Exception as e:
            result = {
                "status": "❌ FAILED",
                "error": str(e), 
                "tools_count": 0
            }
            print(f"❌ Qdrant Code Snippets failed: {e}")
            return result
    
    async def test_qdrant_semantic_memory(self) -> Dict[str, Any]:
        """Test Qdrant Semantic Memory MCP Server (mcp-server-qdrant)"""
        print("\n🔍 Testing Qdrant Semantic Memory MCP Server...")
        
        server_params = StdioServerParameters(
            command="uvx",
            args=["mcp-server-qdrant"],
            env={
                "QDRANT_URL": "http://localhost:6333",
                "COLLECTION_NAME": "semantic-memory",
                "FASTMCP_PORT": "8003"
            }
        )
        
        try:
            async with stdio_client(server_params) as (stdio, write):
                async with ClientSession(stdio, write) as session:
                    await session.initialize()
                    
                    # List tools
                    tools_result = await session.list_tools()
                    tools = [{"name": t.name, "description": t.description} for t in tools_result.tools]
                    
                    # Test store/find for semantic memory
                    test_result = None
                    store_tool = None
                    find_tool = None
                    
                    for tool in tools_result.tools:
                        if "store" in tool.name.lower():
                            store_tool = tool
                        elif "find" in tool.name.lower():
                            find_tool = tool
                    
                    if store_tool and find_tool:
                        try:
                            # Test store decision
                            await session.call_tool(store_tool.name, {
                                "information": "Decision to use FastAPI for MCP server implementation",
                                "metadata": {"category": "architecture", "project": "adv-rag", "date": "2025-06-17"}
                            })
                            # Test find decision
                            find_result = await session.call_tool(find_tool.name, {"query": "FastAPI architecture decisions"})
                            test_result = f"Store/Find semantic memory test successful: {len(str(find_result))} chars returned"
                        except Exception as e:
                            test_result = f"Store/Find semantic memory test failed: {e}"
                    
                    result = {
                        "status": "✅ SUCCESS",
                        "tools_count": len(tools),
                        "tools": tools,
                        "test_result": str(test_result) if test_result else "No store/find tools found"
                    }
                    
                    print(f"✅ Qdrant Semantic Memory: {len(tools)} tools")
                    return result
                    
        except Exception as e:
            result = {
                "status": "❌ FAILED",
                "error": str(e),
                "tools_count": 0
            }
            print(f"❌ Qdrant Semantic Memory failed: {e}")
            return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all external MCP server tests"""
        print("🧪 Starting External MCP Services Accessibility Assessment")
        print("=" * 60)
        
        self.results = {
            "timestamp": "2025-06-17T21:30:00Z",
            "infrastructure_dependencies": {
                "redis": "localhost:6379",
                "qdrant": "localhost:6333", 
                "phoenix": "localhost:6006"
            },
            "test_results": {}
        }
        
        # Test each external MCP server
        self.results["test_results"]["phoenix"] = await self.test_phoenix_mcp()
        self.results["test_results"]["redis"] = await self.test_redis_mcp()
        self.results["test_results"]["qdrant_code_snippets"] = await self.test_qdrant_code_snippets()
        self.results["test_results"]["qdrant_semantic_memory"] = await self.test_qdrant_semantic_memory()
        
        # Generate summary
        successful_tests = sum(1 for result in self.results["test_results"].values() if "SUCCESS" in result["status"])
        total_tests = len(self.results["test_results"])
        
        print("\n" + "=" * 60)
        print("🎯 EXTERNAL MCP SERVICES ASSESSMENT SUMMARY")
        print("=" * 60)
        print(f"✅ Successful: {successful_tests}/{total_tests}")
        print(f"❌ Failed: {total_tests - successful_tests}/{total_tests}")
        
        for service, result in self.results["test_results"].items():
            status_emoji = "✅" if "SUCCESS" in result["status"] else "❌"
            tools_count = result.get("tools_count", 0)
            print(f"{status_emoji} {service}: {tools_count} tools")
        
        self.results["summary"] = {
            "successful_tests": successful_tests,
            "total_tests": total_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%"
        }
        
        return self.results

async def main():
    """Main test runner"""
    tester = ExternalMCPTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    results_file = Path(__file__).parent / "external_mcp_test_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    # Return success code based on results
    success_rate = float(results["summary"]["success_rate"].rstrip("%"))
    return 0 if success_rate >= 50.0 else 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 
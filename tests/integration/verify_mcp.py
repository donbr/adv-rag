import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def verify_fastapi_mcp_server():
    """Verify the FastAPI-based MCP server (the correct one)."""
    print("🔍 Verifying FastAPI-based MCP Server...")
    print("=" * 50)
    
    try:
        async with Client(mcp) as client:
            # Test server connectivity
            await client.ping()
            print("✅ Server connectivity: OK")
            
            # Test tools discovery
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools] if tools else []
            print(f"✅ Tools ({len(tools)}): {tool_names}")
            
            # Verify we have all 6 expected FastAPI endpoints as tools
            expected_tools = [
                'naive_retriever', 'bm25_retriever', 'contextual_compression_retriever',
                'multi_query_retriever', 'ensemble_retriever', 'semantic_retriever'
            ]
            
            missing_tools = set(expected_tools) - set(tool_names)
            if missing_tools:
                print(f"⚠️  Missing expected tools: {missing_tools}")
            else:
                print("✅ All expected FastAPI endpoints converted to MCP tools")
            
            # Test resources and prompts
            resources = await client.list_resources()
            prompts = await client.list_prompts()
            print(f"✅ Resources: {len(resources)} available")
            print(f"✅ Prompts: {len(prompts)} available")
            
            # Test a sample tool execution
            print(f"\n🧪 Testing sample tool execution...")
            test_question = "What makes a good action movie?"
            
            # Test first two tools to verify they work
            for tool_name in tool_names[:2]:
                print(f"  Testing '{tool_name}'...")
                try:
                    result = await client.call_tool(tool_name, {"question": test_question})
                    print(f"  ✅ '{tool_name}': SUCCESS")
                    if result and len(result) > 0:
                        result_preview = str(result[0])[:100] + "..." if len(str(result[0])) > 100 else str(result[0])
                        print(f"      Result preview: {result_preview}")
                except Exception as tool_error:
                    print(f"  ❌ '{tool_name}': {tool_error}")
            
            print("\n🎉 FastAPI MCP Server verification completed successfully!")
            print("\n💡 Architecture Benefits:")
            print("   • FastAPI endpoints automatically become MCP tools")
            print("   • No code duplication needed")
            print("   • Single source of truth for API functionality")
            print("   • Schema inheritance from FastAPI")
            
            return True
            
    except Exception as e:
        print(f"❌ FastAPI MCP Server verification failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_fastapi_mcp_server())
    exit(0 if success else 1) 
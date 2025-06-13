"""
Test client for the native FastMCP implementation in src/mcp_server/main.py

This tests the native MCP server that doesn't use FastAPI wrapper approach.
Kept for comparison and alternative architecture validation.
"""
import asyncio
import json
from mcp.client.stdio import stdio_client, StdioServerParameters

async def test_native_rag_server():
    """Test the native RAG MCP server implementation."""
    
    # Configure server parameters
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "src.mcp_server.main"],
        env=None
    )
    
    print("🚀 Starting native RAG MCP client test...")
    
    try:
        # Connect to the server
        async with stdio_client(server_params) as (read, write):
            from mcp.client.session import ClientSession
            
            async with ClientSession(read, write) as session:
                print("✅ Connected to native RAG MCP server")
                
                # Initialize the session
                await session.initialize()
                print("✅ Session initialized")
                
                # Test 1: List available tools (should be 3 tools)
                print("\n📋 Testing list_tools...")
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                print(f"Available tools: {tool_names}")
                
                expected_native_tools = ["semantic_search", "document_query", "get_collection_stats"]
                missing_tools = [tool for tool in expected_native_tools if tool not in tool_names]
                if missing_tools:
                    print(f"❌ Missing expected tools: {missing_tools}")
                else:
                    print("✅ All expected native tools found")
                
                # Test 2: Call semantic_search with individual parameters
                print("\n🔍 Testing semantic_search tool...")
                try:
                    search_result = await session.call_tool(
                        "semantic_search",
                        arguments={
                            "query": "test search query about John Wick",
                            "top_k": 3,
                            "retrieval_type": "hybrid"
                        }
                    )
                    print(f"✅ semantic_search result: {search_result.content[0].text[:200]}...")
                except Exception as e:
                    print(f"❌ semantic_search failed: {e}")
                
                # Test 3: Call document_query
                print("\n❓ Testing document_query tool...")
                try:
                    query_result = await session.call_tool(
                        "document_query",
                        arguments={
                            "question": "What makes John Wick movies popular?"
                        }
                    )
                    print(f"✅ document_query result: {query_result.content[0].text[:200]}...")
                except Exception as e:
                    print(f"❌ document_query failed: {e}")
                
                # Test 4: Call get_collection_stats
                print("\n📊 Testing get_collection_stats tool...")
                try:
                    stats_result = await session.call_tool(
                        "get_collection_stats",
                        arguments={}
                    )
                    print(f"✅ get_collection_stats result: {stats_result.content[0].text}")
                except Exception as e:
                    print(f"❌ get_collection_stats failed: {e}")
                
                # Test 5: List resources
                print("\n📁 Testing list_resources...")
                try:
                    resources = await session.list_resources()
                    resource_uris = [resource.uri for resource in resources.resources]
                    print(f"Available resources: {resource_uris}")
                except Exception as e:
                    print(f"❌ list_resources failed: {e}")
                
                # Test 6: Read a resource
                print("\n📄 Testing read_resource...")
                try:
                    resource_result = await session.read_resource("rag://collections/johnwick_baseline")
                    print(f"✅ read_resource result: {resource_result.contents[0].text[:200]}...")
                except Exception as e:
                    print(f"⚠️ read_resource expected failure (collection name dependent): {e}")
                
                print("\n✅ Native implementation tests completed!")
                
                # Comparison note
                print("\n📝 COMPARISON NOTE:")
                print("   Native implementation provides 3 generic tools")
                print("   FastAPI wrapper provides 6 specific retrieval methods")
                print("   Both approaches have their merits for different use cases")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_native_rag_server()) 
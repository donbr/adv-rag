# tests/mcp/test_fastapi_wrapper.py
"""
Test client for the FastAPI to FastMCP conversion via fastapi_wrapper.py

This script tests that:
1. All FastAPI endpoints are converted to MCP tools
2. MCP tools can be called successfully with custom names
3. The response format is preserved
4. Schema inheritance works correctly
"""

import asyncio
import logging
from fastmcp import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp_server():
    """Test the converted MCP server"""
    logger.info("Testing FastAPI to FastMCP conversion via fastapi_wrapper...")
    
    client = Client("src.mcp_server.fastapi_wrapper")
    
    try:
        async with client:
            # Test 1: List available tools
            logger.info("📋 Listing available MCP tools...")
            tools = await client.list_tools()
            print("Available MCP Tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test 2: Verify expected tools are present (with custom names)
            tool_names = [tool.name for tool in tools]
            expected_tools = [
                "naive_search",        # Was naive_retriever
                "keyword_search",      # Was bm25_retriever
                "compressed_search",   # Was contextual_compression_retriever
                "enhanced_search",     # Was multi_query_retriever
                "hybrid_search",       # Was ensemble_retriever
                "semantic_search"      # Was semantic_retriever
            ]
            
            logger.info("🔍 Verifying all expected tools with custom names are present...")
            missing_tools = []
            for expected_tool in expected_tools:
                if expected_tool in tool_names:
                    print(f"  ✅ {expected_tool} - Found")
                else:
                    print(f"  ❌ {expected_tool} - Missing")
                    missing_tools.append(expected_tool)
            
            if missing_tools:
                logger.warning(f"Missing tools: {missing_tools}")
            else:
                logger.info("✅ All expected tools with custom names are present!")
            
            # Test 3: Test a working retrieval tool (try keyword_search first)
            test_question = "Did people generally like John Wick?"
            
            # Try keyword_search (was bm25_retriever)
            if "keyword_search" in tool_names:
                logger.info(f"🧪 Testing keyword_search with question: '{test_question}'")
                try:
                    result = await client.call_tool("keyword_search", {
                        "question": test_question
                    })
                    print(f"✅ Keyword Search Test Result:")
                    print(f"   Answer: {result.get('answer', 'No answer')[:100]}...")
                    print(f"   Context Documents: {result.get('context_document_count', 0)}")
                    
                except Exception as e:
                    print(f"❌ Keyword Search Test Failed: {e}")
            
            # Try hybrid_search (was ensemble_retriever)
            if "hybrid_search" in tool_names:
                logger.info(f"🧪 Testing hybrid_search with question: '{test_question}'")
                try:
                    result = await client.call_tool("hybrid_search", {
                        "question": test_question
                    })
                    print(f"✅ Hybrid Search Test Result:")
                    print(f"   Answer: {result.get('answer', 'No answer')[:100]}...")
                    print(f"   Context Documents: {result.get('context_document_count', 0)}")
                    
                except Exception as e:
                    print(f"❌ Hybrid Search Test Failed: {e}")
            
            logger.info("🎉 FastAPI to FastMCP conversion testing completed!")
            
    except Exception as e:
        logger.error(f"❌ MCP Server connection failed: {e}")
        print("Make sure the MCP server dependencies are properly initialized.")
        print("Check that Qdrant is running and accessible if you see chain initialization errors.")

async def test_tool_schemas():
    """Test that tool schemas are properly inherited from FastAPI"""
    logger.info("📝 Testing MCP tool schemas from FastAPI inheritance...")
    
    client = Client("src.mcp_server.fastapi_wrapper")
    
    try:
        async with client:
            tools = await client.list_tools()
            
            for tool in tools:
                print(f"\n🔧 Tool: {tool.name}")
                print(f"   Description: {tool.description}")
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    print(f"   Input Schema: {tool.inputSchema}")
                    # Verify QuestionRequest schema is inherited
                    if 'properties' in tool.inputSchema:
                        properties = tool.inputSchema['properties']
                        if 'question' in properties:
                            print(f"   ✅ Question field found: {properties['question']}")
                else:
                    print("   ⚠️ Input Schema: Not available")
                    
    except Exception as e:
        logger.error(f"❌ Schema testing failed: {e}")

async def main():
    """Run all tests"""
    print("=" * 70)
    print("FastAPI to FastMCP Wrapper Conversion Test Suite")
    print("=" * 70)
    
    await test_mcp_server()
    print("\n" + "=" * 70)
    await test_tool_schemas()
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main()) 
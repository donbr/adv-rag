#!/usr/bin/env python3
"""Simple MCP server test script that works from command line."""

import asyncio
import json
import sys
import os
import pytest

# Add the parent directory to Python path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

@pytest.mark.asyncio
async def test_semantic_search():
    """Test semantic search tool."""
    print("🔍 Testing Semantic Search Tool")
    print("-" * 40)
    
    try:
        from src.mcp_server.main import mcp
        from mcp.shared.memory import create_connected_server_and_client_session
        
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            await session.initialize()
            
            # Test semantic search
            query = "What is John Wick about?"
            print(f"Query: {query}")
            
            result = await session.call_tool(
                "semantic_search", 
                {
                    "query": query,
                    "top_k": 3
                }
            )
            
            if hasattr(result, 'content') and len(result.content) > 0:
                content = result.content[0].text
                print("✅ SUCCESS!")
                print("Response preview:")
                
                # Parse and display nicely
                try:
                    parsed = json.loads(content)
                    for i, doc in enumerate(parsed[:2]):  # Show first 2 results
                        print(f"\nResult {doc['rank']}:")
                        print(f"Content: {doc['content'][:100]}...")
                        print(f"Has metadata: {bool(doc.get('metadata'))}")
                except json.JSONDecodeError:
                    print(content[:200] + "...")
                    
                return True
            else:
                print("❌ ERROR: No content returned")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

@pytest.mark.asyncio
async def test_list_tools():
    """Test listing available tools."""
    print("\n🛠️  Testing Tools List")
    print("-" * 40)
    
    try:
        from src.mcp_server.main import mcp
        from mcp.shared.memory import create_connected_server_and_client_session
        
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            print("✅ SUCCESS!")
            print("Available tools:")
            for tool in tools.tools:
                print(f"  • {tool.name}: {tool.description}")
                
            return True
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

@pytest.mark.asyncio
async def test_collection_stats():
    """Test collection stats tool."""
    print("\n📊 Testing Collection Stats")
    print("-" * 40)
    
    try:
        from src.mcp_server.main import mcp
        from mcp.shared.memory import create_connected_server_and_client_session
        
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            await session.initialize()
            
            result = await session.call_tool("get_collection_stats", {})
            
            if hasattr(result, 'content') and len(result.content) > 0:
                content = result.content[0].text
                print("✅ SUCCESS!")
                print("Collection stats:")
                
                try:
                    parsed = json.loads(content)
                    for key, value in parsed.items():
                        print(f"  • {key}: {value}")
                except json.JSONDecodeError:
                    print(content)
                    
                return True
            else:
                print("❌ ERROR: No content returned")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

@pytest.mark.asyncio
async def test_resources():
    """Test MCP resources."""
    print("\n📁 Testing Resources")
    print("-" * 40)
    
    try:
        from src.mcp_server.main import mcp
        from mcp.shared.memory import create_connected_server_and_client_session
        
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            await session.initialize()
            
            # List resource templates
            templates = await session.list_resource_templates()
            print("✅ SUCCESS!")
            print("Available resource templates:")
            for template in templates.resourceTemplates:
                print(f"  • {template.uriTemplate}: {template.description}")
            
            # Test reading collection resource
            print("\nReading collection resource:")
            resource = await session.read_resource("rag://collections/johnwick_baseline")
            for content in resource.contents:
                print(f"  {content.text[:100]}...")
                
            return True
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 FastMCP Server Test Suite")
    print("=" * 50)
    
    tests = [
        ("List Tools", test_list_tools),
        ("Semantic Search", test_semantic_search),
        ("Collection Stats", test_collection_stats),
        ("Resources", test_resources),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! FastMCP server is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 
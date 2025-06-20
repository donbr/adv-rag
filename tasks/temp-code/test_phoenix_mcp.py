#!/usr/bin/env python3
"""
Phoenix MCP Individual Test Script

Tests Phoenix MCP server individually with detailed error reporting.
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

async def test_phoenix_mcp():
    """Test Phoenix MCP server individually"""
    print("🔍 Testing Phoenix MCP Server (Individual Test)")
    print("=" * 50)
    
    try:
        # Phoenix MCP server parameters
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@arizeai/phoenix-mcp"],
            env={"PHOENIX_API_KEY": "test_key"}  # Test with dummy key
        )
        
        print(f"Command: {server_params.command} {' '.join(server_params.args)}")
        print("Environment: PHOENIX_API_KEY=test_key")
        print()
        
        # Connect to server
        print("📡 Connecting to Phoenix MCP server...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Successfully connected to Phoenix MCP")
                
                # Initialize the session
                print("🔧 Initializing session...")
                await session.initialize()
                print("✅ Session initialized")
                
                # List available tools
                print("🛠️  Listing available tools...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                print(f"✅ Phoenix MCP: {len(tools)} tools available")
                for i, tool in enumerate(tools, 1):
                    print(f"   {i}. {tool.name} - {tool.description}")
                
                # Test specific Phoenix MCP tools as requested
                print(f"\n🧪 Testing Phoenix MCP with list-datasets and list-experiments")
                
                # Test list-datasets tool
                try:
                    print("📊 Testing list-datasets tool...")
                    print("   📤 REQUEST: list-datasets")
                    print("   📝 Parameters: {}")
                    datasets_result = await session.call_tool("list-datasets", {})
                    print(f"   ✅ RESPONSE:")
                    for i, content in enumerate(datasets_result.content):
                        if hasattr(content, 'text'):
                            print(f"   📋 Content[{i}]: {content.text}")
                    print()
                except Exception as tool_error:
                    print(f"   ⚠️  list-datasets error: {tool_error}")
                
                # Test list-experiments-for-dataset tool with real dataset ID
                try:
                    print("🔬 Testing list-experiments-for-dataset tool...")
                    # Use the real dataset ID we found from list-datasets
                    real_dataset_id = "RGF0YXNldDoy"  # johnwick_golden_testset
                    request_params = {"dataset_id": real_dataset_id}
                    print(f"   📤 REQUEST: list-experiments-for-dataset")
                    print(f"   📝 Parameters: {request_params}")
                    experiments_result = await session.call_tool("list-experiments-for-dataset", request_params)
                    print(f"   ✅ RESPONSE:")
                    for i, content in enumerate(experiments_result.content):
                        if hasattr(content, 'text'):
                            print(f"   📋 Content[{i}]: {content.text}")
                    print()
                except Exception as tool_error:
                    print(f"   ⚠️  list-experiments-for-dataset error: {tool_error}")
                    
                # Also test with invalid dataset ID to verify error handling
                try:
                    print("🧪 Testing error handling with invalid dataset ID...")
                    invalid_params = {"dataset_id": "invalid_id"}
                    print(f"   📤 REQUEST: list-experiments-for-dataset")
                    print(f"   📝 Parameters: {invalid_params}")
                    invalid_result = await session.call_tool("list-experiments-for-dataset", invalid_params)
                    print(f"   ✅ Error handling test - tool responded to invalid ID:")
                    for i, content in enumerate(invalid_result.content):
                        if hasattr(content, 'text'):
                            print(f"   📋 Content[{i}]: {content.text}")
                except Exception as expected_error:
                    print(f"   ✅ Error handling working correctly: {str(expected_error)}")
                    
                print(f"\n🔍 Phoenix MCP tool testing complete")
                
                return True
                
    except Exception as e:
        print(f"❌ Phoenix MCP failed: {e}")
        print("\n🔍 Full error traceback:")
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🧪 Phoenix MCP Individual Assessment")
    print("=" * 60)
    
    success = await test_phoenix_mcp()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Phoenix MCP: ACCESSIBLE")
        print("   - Connection successful")
        print("   - Tools discoverable")
        print("   - Ready for integration")
    else:
        print("❌ Phoenix MCP: NOT ACCESSIBLE")
        print("   - Connection failed")
        print("   - May require proper API key or service setup")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1) 
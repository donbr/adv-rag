#!/usr/bin/env python3
"""Simple command-line MCP tool verification"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastmcp import Client
from src.mcp.server import mcp

async def test_all_tools():
    """Test all 8 MCP tools via command-line"""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print(f"Found {len(tools)} MCP tools")
        
        test_question = "What makes a good action movie?"
        success_count = 0
        
        for tool in tools:
            try:
                # Use appropriate args based on tool type
                if 'health' in tool.name or 'cache' in tool.name:
                    args = {}
                else:
                    args = {'question': test_question}
                
                result = await client.call_tool(tool.name, args)
                print(f"✅ {tool.name}: SUCCESS")
                success_count += 1
                
            except Exception as e:
                print(f"❌ {tool.name}: FAILED - {str(e)[:50]}")
        
        print(f"\nSummary: {success_count}/{len(tools)} tools successful")
        return success_count == len(tools)

if __name__ == "__main__":
    success = asyncio.run(test_all_tools())
    sys.exit(0 if success else 1) 
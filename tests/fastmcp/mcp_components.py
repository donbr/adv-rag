# Quick verification script
import asyncio
import sys
import os
from pathlib import Path
from fastmcp import Client

# Add project root to Python path for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # Go up 3 levels: fastmcp -> tests -> project_root
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.mcp_server.fastapi_wrapper import mcp

async def verify_mcp_components():
    async with Client(mcp) as client:
        # Check tools
        tools = await client.list_tools()
        tool_list = tools if isinstance(tools, list) else (tools.tools if hasattr(tools, 'tools') else [])
        print(f"Tools found: {[t.name for t in tool_list]}")
        
        # Check resources  
        resources = await client.list_resources()
        resource_list = resources if isinstance(resources, list) else (resources.resources if hasattr(resources, 'resources') else [])
        print(f"Resources found: {len(resource_list)}")
        
        # Check prompts
        prompts = await client.list_prompts()
        prompt_list = prompts if isinstance(prompts, list) else (prompts.prompts if hasattr(prompts, 'prompts') else [])
        print(f"Prompts found: {len(prompt_list)}")

if __name__ == "__main__":
    asyncio.run(verify_mcp_components()) 
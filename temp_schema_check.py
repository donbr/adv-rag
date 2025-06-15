#!/usr/bin/env python3
"""Temporary script to check resource_wrapper.py schema"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastmcp import Client
from src.mcp_server.resource_wrapper import mcp

async def get_schema():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        
        print('=== RESOURCE_WRAPPER SCHEMA ===')
        print(f'Tools: {len(tools)}')
        for tool in tools:
            print(f'  - {tool.name}: {tool.description[:60]}...')
        
        print(f'Resources: {len(resources)}')
        for resource in resources:
            print(f'  - {resource.name}: {resource.uri}')
            print(f'    Description: {resource.description[:80]}...')
        
        print(f'Prompts: {len(prompts)}')
        for prompt in prompts:
            print(f'  - {prompt.name}: {prompt.description[:60]}...')

if __name__ == "__main__":
    asyncio.run(get_schema()) 
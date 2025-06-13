import asyncio
from fastmcp import Client
from src.mcp_server.fastapi_wrapper import mcp

async def verify():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print(f"✅ Tools: {[t.name for t in tools.tools]}")
        
        resources = await client.list_resources()
        print(f"✅ Resources: {len(resources.resources) if resources else 0}")
        
        prompts = await client.list_prompts()
        print(f"✅ Prompts: {len(prompts.prompts) if prompts else 0}")

asyncio.run(verify())

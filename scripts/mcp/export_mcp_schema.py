#!/usr/bin/env python3
"""
Export FastMCP server definitions to shareable JSON format.
"""
import json
import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # Go up from scripts/mcp/ to project root
sys.path.insert(0, str(project_root))

from fastmcp import Client
from src.mcp_server.fastapi_wrapper import mcp

async def export_mcp_definitions():
    """Export MCP server definitions as JSON."""
    
    async with Client(mcp) as client:
        # Get all definitions
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        
        # Build the standard schema format (legacy/community format)
        schema = {
            "server_info": {
                "name": "advanced-rag-fastapi",
                "description": "Advanced RAG with FastAPI → MCP Integration. Provides 6 retrieval strategies for semantic search across John Wick movie reviews.",
                "repo_url": "https://github.com/donbr/advanced-rag",
                "server_type": "FastAPI Integration",
                "server_category": ["RAG", "Search", "AI", "LangChain"],
                "server_version": "1.0.0"
            },
            "tools": [],
            "resources": [],
            "prompts": []
        }
        
        # Convert tools with clean descriptions (legacy format uses snake_case)
        for tool in tools:
            # Clean up the description - remove FastAPI response documentation
            clean_description = tool.description.split('\n\n\n**Responses:**')[0] if '\n\n\n**Responses:**' in tool.description else tool.description
            
            tool_def = {
                "name": tool.name,
                "description": clean_description,
                "input_schema": tool.inputSchema  # Legacy format uses snake_case
            }
            
            # Add response info as a note (not part of MCP spec, but useful for documentation)
            if hasattr(tool, 'annotations'):
                tool_def["annotations"] = tool.annotations
                
            schema["tools"].append(tool_def)
        
        # Convert resources  
        for resource in resources:
            schema["resources"].append({
                "name": resource.name,
                "description": resource.description,
                "uri": resource.uri
            })
            
        # Convert prompts
        for prompt in prompts:
            schema["prompts"].append({
                "name": prompt.name,
                "description": prompt.description,
                "template": getattr(prompt, 'template', None)
            })
        
        return schema

async def export_mcp_definitions_official():
    """Export MCP server definitions using official MCP protocol format."""
    
    async with Client(mcp) as client:
        # Get all definitions using the official MCP protocol
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        
        # Build official MCP server descriptor following the spec
        server_descriptor = {
            "$schema": "https://raw.githubusercontent.com/modelcontextprotocol/specification/main/schema/server.json",
            "$id": "https://github.com/donbr/advanced-rag/mcp-server.json",
            "name": "advanced-rag-fastapi",
            "version": "1.0.0",
            "description": "Advanced RAG with FastAPI → MCP Integration. Provides 6 retrieval strategies for semantic search across John Wick movie reviews.",
            "author": "Advanced RAG Team",
            "license": "MIT",
            "homepage": "https://github.com/donbr/advanced-rag",
            "repository": {
                "type": "git",
                "url": "https://github.com/donbr/advanced-rag.git"
            },
            "categories": ["RAG", "Search", "AI", "LangChain"],
            "keywords": ["rag", "retrieval", "langchain", "fastapi", "semantic-search", "bm25"],
            "capabilities": {
                "tools": {
                    "listChanged": False
                },
                "resources": {
                    "subscribe": False,
                    "listChanged": False
                },
                "prompts": {
                    "listChanged": False
                },
                "logging": {}
            },
            "protocolVersion": "2024-11-05",
            "tools": [],
            "resources": [],
            "prompts": []
        }
        
        # Convert tools to official format (using camelCase)
        for tool in tools:
            # Clean description - remove FastAPI response documentation
            clean_description = tool.description.split('\n\n\n**Responses:**')[0] if '\n\n\n**Responses:**' in tool.description else tool.description
            
            tool_def = {
                "name": tool.name,
                "description": clean_description,
                "inputSchema": tool.inputSchema  # camelCase as per spec
            }
            
            server_descriptor["tools"].append(tool_def)
        
        # Convert resources
        for resource in resources:
            server_descriptor["resources"].append({
                "name": resource.name,
                "description": resource.description,
                "uri": resource.uri,
                "mimeType": getattr(resource, 'mimeType', 'application/json')
            })
            
        # Convert prompts
        for prompt in prompts:
            prompt_def = {
                "name": prompt.name,
                "description": prompt.description
            }
            
            # Add arguments if available
            if hasattr(prompt, 'arguments') and prompt.arguments:
                prompt_def["arguments"] = prompt.arguments
                
            server_descriptor["prompts"].append(prompt_def)
        
        return server_descriptor

async def main():
    """Export and save MCP definitions."""
    print("🔄 Exporting MCP server definitions...")
    
    try:
        # Export community format
        community_schema = await export_mcp_definitions()
        
        # Export official MCP format
        official_schema = await export_mcp_definitions_official()
        
        # Save community format
        community_file = Path("mcp_server_schema.json")
        with open(community_file, 'w', encoding='utf-8') as f:
            json.dump(community_schema, f, indent=2, ensure_ascii=False)
        
        # Save official format
        official_file = Path("mcp_server_official.json")
        with open(official_file, 'w', encoding='utf-8') as f:
            json.dump(official_schema, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(official_schema['tools'])} tools, {len(official_schema['resources'])} resources, {len(official_schema['prompts'])} prompts")
        print(f"📄 Legacy/Community format: {community_file.absolute()}")
        print(f"📄 🎯 Official MCP format (RECOMMENDED): {official_file.absolute()}")
        
        # Print tool summary
        print(f"\n🛠️ Available Tools:")
        for tool in official_schema['tools']:
            print(f"  • {tool['name']}: {tool['description']}")
        
        # Validate that we have complete tool definitions using official format
        print(f"\n🔍 Official MCP Schema Validation:")
        for tool in official_schema['tools']:
            has_schema = tool.get('inputSchema') is not None  # Official format uses camelCase
            has_properties = bool(tool.get('inputSchema', {}).get('properties', {}))
            has_required = bool(tool.get('inputSchema', {}).get('required', []))
            print(f"  • {tool['name']}: Schema✅ Properties✅ Required✅" if has_schema and has_properties and has_required else f"  • {tool['name']}: Issues detected")
        
        # Schema compliance check
        print(f"\n🎯 Official MCP Schema Compliance:")
        print(f"  • $schema field: {'✅' if official_schema.get('$schema') else '❌'}")
        print(f"  • $id field: {'✅' if official_schema.get('$id') else '❌'}")
        print(f"  • camelCase inputSchema: {'✅' if all(tool.get('inputSchema') for tool in official_schema['tools']) else '❌'}")
        print(f"  • Capabilities defined: {'✅' if official_schema.get('capabilities') else '❌'}")
        print(f"  • Protocol version: {'✅' if official_schema.get('protocolVersion') else '❌'}")
        
        print(f"\n💡 MCP Specification Notes:")
        print(f"   • Official schema: https://raw.githubusercontent.com/modelcontextprotocol/specification/main/schema/server.json")
        print(f"   • Tool inputs use 'inputSchema' (camelCase), not 'input_schema'")
        print(f"   • Tool responses are defined by MCP protocol content types: text, image, audio, resource")
        print(f"   • Use the Official MCP format for production deployments")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 
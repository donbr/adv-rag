#!/usr/bin/env python3
"""
Export FastMCP server definitions using stdio transport.
This demonstrates the transport-agnostic nature of FastMCP Client.
"""
import json
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# Add project root to path for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fastmcp import Client
    # Import validation functions from the dedicated validation script
    from scripts.mcp.validate_mcp_schema import validate_with_json_schema
    # Import the MCP server directly
    from src.mcp.server import mcp
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Install with: pip install fastmcp")
    logger.error("Ensure you're running from the project root")
    sys.exit(1)

def validate_schema_structure(schema: dict) -> Tuple[bool, str]:
    """Validate basic schema structure and completeness."""
    try:
        # Check required top-level fields
        required_fields = ["info", "tools", "resources", "prompts"]
        for field in required_fields:
            if field not in schema:
                return False, f"Missing required field: {field}"
        
        # Validate info section
        info = schema.get("info", {})
        info_required = ["title", "version", "description"]
        for field in info_required:
            if field not in info:
                return False, f"Missing required info field: {field}"
        
        # Validate tools structure
        tools = schema.get("tools", [])
        for i, tool in enumerate(tools):
            tool_required = ["name", "description", "inputSchema"]
            for field in tool_required:
                if field not in tool:
                    return False, f"Tool {i} missing required field: {field}"
            
            # Validate inputSchema structure
            input_schema = tool.get("inputSchema", {})
            if not isinstance(input_schema, dict):
                return False, f"Tool {i} inputSchema must be an object"
            
            if "type" not in input_schema:
                return False, f"Tool {i} inputSchema missing 'type' field"
        
        # Validate resources structure
        resources = schema.get("resources", [])
        for i, resource in enumerate(resources):
            resource_required = ["name", "description", "uri"]
            for field in resource_required:
                if field not in resource:
                    return False, f"Resource {i} missing required field: {field}"
        
        # Validate prompts structure
        prompts = schema.get("prompts", [])
        for i, prompt in enumerate(prompts):
            prompt_required = ["name", "description"]
            for field in prompt_required:
                if field not in prompt:
                    return False, f"Prompt {i} missing required field: {field}"
        
        return True, "Schema structure validation passed"
        
    except Exception as e:
        return False, f"Schema validation error: {str(e)}"

async def export_stdio_schema() -> Optional[dict]:
    """Export complete MCP schema using stdio transport with FastMCP Client."""
    
    logger.info("🚀 Starting stdio MCP schema export...")
    
    try:
        # Connect to MCP server using stdio transport (direct connection)
        logger.info("🔍 Connecting to MCP server via stdio transport...")
        
        async with Client(mcp) as client:
            logger.info("✅ MCP server connection established via stdio")
            
            # Fetch schema components using FastMCP Client methods
            logger.info("🔍 Fetching schema via FastMCP Client methods...")
            
            tools = await client.list_tools()
            resources = await client.list_resources()
            prompts = await client.list_prompts()
            
            logger.info("✅ Stdio schema collection completed")
            
            # Build schema in standard format
            schema = {
                "info": {
                    "title": "Advanced RAG MCP Server (stdio)",
                    "version": "1.0.0",
                    "description": "FastMCP server exposing RAG retrieval tools via stdio transport"
                },
                "tools": [],
                "resources": [],
                "prompts": []
            }
            
            # Convert tools
            for tool in tools:
                # Clean description - remove FastAPI response documentation
                clean_description = tool.description.split('\n\n\n**Responses:**')[0] if '\n\n\n**Responses:**' in tool.description else tool.description
                
                tool_def = {
                    "name": tool.name,
                    "description": clean_description,
                    "inputSchema": tool.inputSchema
                }
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
                    "description": prompt.description
                })
            
            return schema
            
    except Exception as e:
        logger.error(f"❌ Failed to export schema via stdio: {e}")
        return None

async def main():
    """Export and save MCP definitions using stdio transport."""
    
    try:
        # Export schema using stdio transport
        schema = await export_stdio_schema()
        
        if not schema:
            logger.error("❌ Schema export failed")
            return False
        
        # Validate schema structure
        logger.info("🔍 Performing schema validation...")
        is_valid_structure, structure_message = validate_schema_structure(schema)
        if is_valid_structure:
            logger.info("✅ Schema structure validation passed")
        else:
            logger.error(f"❌ Schema structure validation failed: {structure_message}")
        
        # Optional official schema validation using imported function
        is_valid_official, official_message = validate_with_json_schema(schema)
        if is_valid_official:
            logger.info("✅ Official schema validation passed")
        else:
            logger.warning(f"⚠️ Official schema validation: {official_message}")
        
        # Save schema
        output_file = Path("mcp_server_stdio.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        # Print results
        print(f"\n🎯 FastMCP Client Schema Export Complete (stdio):")
        print(f"📄 File: {output_file.absolute()}")
        print(f"🛠️ Tools: {len(schema['tools'])}")
        print(f"📚 Resources: {len(schema['resources'])}")
        print(f"💬 Prompts: {len(schema['prompts'])}")
        print(f"🌐 Transport: stdio")
        print(f"📡 Server: Direct MCP instance connection")
        print(f"📋 Standard: FastMCP Client methods")
        
        print(f"\n🔍 Schema Validation Results:")
        print(f"  • Structure validation: {'✅ PASSED' if is_valid_structure else '❌ FAILED'}")
        print(f"  • Official schema validation: {'✅ PASSED' if is_valid_official else '⚠️ SKIPPED/FAILED'}")
        if not is_valid_official:
            print(f"  • Official validation note: {official_message}")
        
        print(f"\n💡 Benefits of FastMCP Client Approach (stdio):")
        print(f"  • Uses official FastMCP Client methods")
        print(f"  • Direct server connection (no HTTP overhead)")
        print(f"  • Transport-agnostic design validated")
        print(f"  • Perfect for Claude Desktop integration")
        print(f"  • Minimal latency and maximum performance")
        print(f"  • Same API as HTTP transport")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 
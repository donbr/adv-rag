#!/usr/bin/env python3
"""
Schema Comparison Script - FastAPI vs MCP Tools
Validates parameter schemas match between FastAPI and MCP
"""
import asyncio
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastmcp import Client
from src.mcp.server import mcp
from src.api.app import app

async def compare_schemas():
    """Compare FastAPI OpenAPI schemas with MCP tool schemas"""
    print("🔍 Comparing FastAPI and MCP parameter schemas...")
    print("=" * 60)
    
    # Get FastAPI OpenAPI schema
    openapi_schema = app.openapi()
    fastapi_endpoints = {}
    
    # Extract FastAPI endpoint schemas
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, details in methods.items():
            if method.upper() == "POST" and "/invoke/" in path:
                endpoint_name = path.split("/invoke/")[-1]
                operation_id = details.get("operationId", endpoint_name)
                
                # Get request schema and resolve $ref if needed
                request_schema = None
                if "requestBody" in details:
                    content = details["requestBody"].get("content", {})
                    if "application/json" in content:
                        schema = content["application/json"].get("schema", {})
                        
                        # Resolve $ref if present
                        if "$ref" in schema:
                            ref_path = schema["$ref"]
                            if ref_path.startswith("#/components/schemas/"):
                                schema_name = ref_path.split("/")[-1]
                                request_schema = openapi_schema.get("components", {}).get("schemas", {}).get(schema_name, {})
                            else:
                                request_schema = schema
                        else:
                            request_schema = schema
                
                fastapi_endpoints[operation_id] = {
                    "path": path,
                    "method": method.upper(),
                    "request_schema": request_schema
                }
    
    # Get MCP tool schemas
    async with Client(mcp) as client:
        tools = await client.list_tools()
        
        print(f"📊 Found {len(fastapi_endpoints)} FastAPI endpoints and {len(tools)} MCP tools")
        print()
        
        schema_matches = []
        schema_mismatches = []
        
        for tool in tools:
            tool_name = tool.name
            
            print(f"🔧 Analyzing tool: {tool_name}")
            print("-" * 40)
            
            # Find corresponding FastAPI endpoint
            fastapi_endpoint = fastapi_endpoints.get(tool_name)
            
            if not fastapi_endpoint:
                print(f"  ⚠️  No corresponding FastAPI endpoint found")
                schema_mismatches.append({
                    "tool": tool_name,
                    "issue": "No FastAPI endpoint match",
                    "mcp_schema": tool.inputSchema if hasattr(tool, 'inputSchema') else None
                })
                print()
                continue
            
            # Compare schemas
            fastapi_schema = fastapi_endpoint["request_schema"]
            mcp_schema = tool.inputSchema if hasattr(tool, 'inputSchema') else None
            
            print(f"  📝 FastAPI Schema: {json.dumps(fastapi_schema, indent=2) if fastapi_schema else 'None'}")
            print(f"  🔧 MCP Schema: {json.dumps(mcp_schema, indent=2) if mcp_schema else 'None'}")
            
            # Check for parameter compatibility
            if fastapi_schema and mcp_schema:
                fastapi_props = fastapi_schema.get("properties", {})
                mcp_props = mcp_schema.get("properties", {})
                
                # Check if parameter names match
                fastapi_params = set(fastapi_props.keys())
                mcp_params = set(mcp_props.keys())
                
                if fastapi_params == mcp_params:
                    print(f"  ✅ Parameter names match: {fastapi_params}")
                    schema_matches.append({
                        "tool": tool_name,
                        "status": "match",
                        "parameters": list(fastapi_params)
                    })
                else:
                    print(f"  ❌ Parameter mismatch!")
                    print(f"     FastAPI params: {fastapi_params}")
                    print(f"     MCP params: {mcp_params}")
                    
                    schema_mismatches.append({
                        "tool": tool_name,
                        "issue": "Parameter name mismatch",
                        "fastapi_params": list(fastapi_params),
                        "mcp_params": list(mcp_params),
                        "fastapi_schema": fastapi_schema,
                        "mcp_schema": mcp_schema
                    })
            else:
                print(f"  ⚠️  Missing schema data")
                schema_mismatches.append({
                    "tool": tool_name,
                    "issue": "Missing schema",
                    "fastapi_schema": fastapi_schema,
                    "mcp_schema": mcp_schema
                })
            
            print()
        
        # Summary
        print("=" * 60)
        print("📊 SCHEMA COMPARISON SUMMARY")
        print("=" * 60)
        print(f"✅ Schema matches: {len(schema_matches)}")
        print(f"❌ Schema mismatches: {len(schema_mismatches)}")
        
        if schema_mismatches:
            print("\n🚨 ISSUES FOUND:")
            for mismatch in schema_mismatches:
                print(f"  • {mismatch['tool']}: {mismatch['issue']}")
        
        if schema_matches:
            print(f"\n✅ WORKING TOOLS:")
            for match in schema_matches:
                print(f"  • {match['tool']}: {match['parameters']}")
        
        return len(schema_mismatches) == 0

if __name__ == "__main__":
    success = asyncio.run(compare_schemas())
    sys.exit(0 if success else 1) 
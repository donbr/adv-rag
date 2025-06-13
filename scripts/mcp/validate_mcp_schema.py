#!/usr/bin/env python3
"""
Validate MCP server schema against official specification.
"""
import json
import requests
from pathlib import Path
import sys

def validate_mcp_schema():
    """Validate our MCP schema against the official specification."""
    
    # Load our official schema
    schema_file = Path("mcp_server_official.json")
    if not schema_file.exists():
        print("❌ mcp_server_official.json not found. Run export_mcp_schema.py first.")
        return False
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        our_schema = json.load(f)
    
    print("🔍 Validating MCP Schema Compliance...")
    print(f"📄 Schema file: {schema_file.absolute()}")
    
    # Check required fields according to MCP spec
    required_fields = {
        "$schema": "JSON Schema reference",
        "$id": "Unique identifier",
        "name": "Server name",
        "version": "Server version",
        "description": "Server description",
        "capabilities": "MCP capabilities",
        "protocolVersion": "MCP protocol version",
        "tools": "Available tools",
        "resources": "Available resources", 
        "prompts": "Available prompts"
    }
    
    print("\n✅ Required Fields Check:")
    all_required_present = True
    for field, description in required_fields.items():
        present = field in our_schema
        print(f"  • {field}: {'✅' if present else '❌'} ({description})")
        if not present:
            all_required_present = False
    
    # Check field formats
    print("\n✅ Field Format Check:")
    format_checks = []
    
    # Check $schema URL
    schema_url = our_schema.get("$schema", "")
    schema_valid = "modelcontextprotocol" in schema_url and "server.json" in schema_url
    format_checks.append(("$schema URL", schema_valid, "Points to official MCP server schema"))
    
    # Check tools format
    tools = our_schema.get("tools", [])
    tools_valid = all(
        isinstance(tool, dict) and 
        "name" in tool and 
        "description" in tool and 
        "inputSchema" in tool  # Must be camelCase
        for tool in tools
    )
    format_checks.append(("Tools format", tools_valid, "All tools have name, description, inputSchema"))
    
    # Check inputSchema is camelCase (not input_schema)
    camelcase_valid = all(
        "inputSchema" in tool and "input_schema" not in tool 
        for tool in tools
    )
    format_checks.append(("camelCase inputSchema", camelcase_valid, "Uses 'inputSchema' not 'input_schema'"))
    
    # Check capabilities structure
    capabilities = our_schema.get("capabilities", {})
    cap_valid = (
        isinstance(capabilities, dict) and
        "tools" in capabilities and
        "resources" in capabilities and
        "prompts" in capabilities
    )
    format_checks.append(("Capabilities structure", cap_valid, "Has tools, resources, prompts capabilities"))
    
    for check_name, is_valid, description in format_checks:
        print(f"  • {check_name}: {'✅' if is_valid else '❌'} ({description})")
        if not is_valid:
            all_required_present = False
    
    # Tool-specific validation
    print(f"\n✅ Tool Validation ({len(tools)} tools):")
    for tool in tools:
        tool_name = tool.get("name", "Unknown")
        has_schema = "inputSchema" in tool
        has_properties = has_schema and "properties" in tool["inputSchema"]
        has_required = has_schema and "required" in tool["inputSchema"]
        
        tool_valid = has_schema and has_properties and has_required
        print(f"  • {tool_name}: {'✅' if tool_valid else '❌'}")
    
    # Summary
    print(f"\n📊 Validation Summary:")
    print(f"  • Schema compliance: {'✅ PASS' if all_required_present else '❌ FAIL'}")
    print(f"  • Total tools: {len(tools)}")
    print(f"  • Total resources: {len(our_schema.get('resources', []))}")
    print(f"  • Total prompts: {len(our_schema.get('prompts', []))}")
    
    if all_required_present:
        print(f"\n🎉 Schema is MCP-compliant!")
        print(f"   Ready for production deployment.")
    else:
        print(f"\n⚠️  Schema has compliance issues.")
        print(f"   Fix the issues above before production deployment.")
    
    # Optional: Try to fetch official schema for comparison
    print(f"\n🌐 Official Schema Check:")
    try:
        official_url = our_schema.get("$schema")
        if official_url:
            response = requests.get(official_url, timeout=10)
            if response.status_code == 200:
                print(f"  • Official schema accessible: ✅")
                official_schema = response.json()
                print(f"  • Official schema version: {official_schema.get('$id', 'Unknown')}")
            else:
                print(f"  • Official schema accessible: ❌ (HTTP {response.status_code})")
        else:
            print(f"  • No $schema URL provided: ❌")
    except Exception as e:
        print(f"  • Official schema check failed: ❌ ({e})")
    
    return all_required_present

if __name__ == "__main__":
    success = validate_mcp_schema()
    exit(0 if success else 1) 
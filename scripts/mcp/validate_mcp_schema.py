#!/usr/bin/env python3
"""
Validate MCP server schema against official specification.
"""
import json
import requests
from pathlib import Path
import sys

def validate_with_json_schema(our_schema):
    """Validate against official MCP JSON schema using jsonschema library."""
    try:
        import jsonschema
        
        # Get the official schema URL
        schema_url = our_schema.get("$schema")
        if not schema_url:
            return False, "No $schema URL found in document"
        
        print(f"🔍 Fetching official schema: {schema_url}")
        response = requests.get(schema_url, timeout=10)
        
        if response.status_code != 200:
            return False, f"Could not fetch official schema (HTTP {response.status_code})"
        
        official_schema = response.json()
        print(f"✅ Official schema fetched successfully")
        
        # Validate our schema against the official one
        jsonschema.validate(our_schema, official_schema)
        return True, "Schema validation passed"
        
    except ImportError:
        return False, "jsonschema library not installed. Run: pip install jsonschema"
    except jsonschema.ValidationError as e:
        return False, f"Schema validation failed: {e.message}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def validate_mcp_schema(schema_filename=None):
    """Validate our MCP schema against the official specification."""
    
    # Auto-detect schema file if not specified
    if schema_filename is None:
        candidates = ["mcp_server_official.json", "mcp_server_native.json", "mcp_server_schema.json"]
        schema_file = None
        for candidate in candidates:
            if Path(candidate).exists():
                schema_file = Path(candidate)
                break
        
        if schema_file is None:
            print("❌ No MCP schema file found. Tried: " + ", ".join(candidates))
            print("💡 Run export_mcp_schema.py or export_mcp_schema_native.py first.")
            return False
    else:
        schema_file = Path(schema_filename)
        if not schema_file.exists():
            print(f"❌ {schema_filename} not found.")
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
    schema_valid = "modelcontextprotocol" in schema_url and ("server.json" in schema_url or "schema.json" in schema_url)
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
    
    # NEW: JSON Schema Validation
    print(f"\n🔍 JSON Schema Validation:")
    schema_valid, validation_message = validate_with_json_schema(our_schema)
    print(f"  • Official schema validation: {'✅' if schema_valid else '❌'} ({validation_message})")
    if not schema_valid:
        all_required_present = False
    
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
    
    # Enhanced recommendations
    if schema_valid:
        print(f"\n💡 Enhancement Opportunities:")
        print(f"   • Add tool annotations for governance/security")
        print(f"   • Add tool examples for better LLM understanding") 
        print(f"   • Consider adding resource contentSchema fields")
        print(f"   • Update protocolVersion to latest MCP spec")
    
    return all_required_present

if __name__ == "__main__":
    import sys
    
    # Allow specifying schema file as command line argument
    schema_file = sys.argv[1] if len(sys.argv) > 1 else None
    success = validate_mcp_schema(schema_file)
    exit(0 if success else 1) 
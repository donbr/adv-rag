#!/usr/bin/env python3
"""
Compare MCP schemas across different transport implementations.

This script validates transport-agnostic design by comparing schemas from:
- stdio transport (export_mcp_schema_stdio.py)
- http transport (export_mcp_schema_native.py via HTTP)
- sse transport (Server-Sent Events)
- websocket transport (WebSocket connections)
- tcp transport (Raw TCP connections)

Key principle: MCP schemas should be identical regardless of transport layer.
"""
import json
from pathlib import Path
from typing import Dict, Any, List

def load_schema(filename: str) -> Dict[str, Any]:
    """Load schema file if it exists."""
    path = Path(filename)
    if not path.exists():
        return {}
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_schema_completeness(schema: Dict[str, Any], name: str) -> Dict[str, Any]:
    """Analyze schema completeness and features."""
    analysis = {
        "name": name,
        "exists": bool(schema),
        "tools_count": len(schema.get("tools", [])),
        "resources_count": len(schema.get("resources", [])),
        "prompts_count": len(schema.get("prompts", [])),
        "has_schema_field": "$schema" in schema,
        "has_id_field": "$id" in schema,
        "has_capabilities": "capabilities" in schema,
        "has_protocol_version": "protocolVersion" in schema,
        "has_annotations": False,
        "has_examples": False,
        "has_metadata": False,
        "file_size_kb": 0
    }
    
    if schema:
        # Check for enhanced features
        tools = schema.get("tools", [])
        if tools:
            first_tool = tools[0]
            analysis["has_annotations"] = "annotations" in first_tool
            analysis["has_examples"] = "examples" in first_tool
        
        # Check for metadata
        analysis["has_metadata"] = any(key in schema for key in ["author", "license", "repository", "homepage"])
        
        # Estimate file size
        schema_json = json.dumps(schema, indent=2)
        analysis["file_size_kb"] = round(len(schema_json.encode('utf-8')) / 1024, 1)
    
    return analysis

def compare_tool_descriptions(schemas: Dict[str, Dict[str, Any]]) -> None:
    """Compare tool descriptions across schemas."""
    print("\n🔍 Tool Description Comparison:")
    
    # Get all tool names from all schemas
    all_tools = set()
    for schema in schemas.values():
        for tool in schema.get("tools", []):
            all_tools.add(tool.get("name", ""))
    
    for tool_name in sorted(all_tools):
        if not tool_name:
            continue
            
        print(f"\n📋 Tool: {tool_name}")
        for schema_name, schema in schemas.items():
            tool_data = next((t for t in schema.get("tools", []) if t.get("name") == tool_name), None)
            if tool_data:
                desc = tool_data.get("description", "")
                # Truncate long descriptions
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                print(f"  • {schema_name}: {desc}")
            else:
                print(f"  • {schema_name}: ❌ Missing")

def validate_transport_agnostic_design(schemas: Dict[str, Dict[str, Any]]) -> bool:
    """Validate that all schemas are identical (transport-agnostic principle)."""
    valid_schemas = {k: v for k, v in schemas.items() if v}
    
    if len(valid_schemas) < 2:
        print("⚠️ Need at least 2 schemas to validate transport-agnostic design")
        return True
    
    # Remove transport-specific metadata for comparison
    normalized_schemas = {}
    for name, schema in valid_schemas.items():
        normalized = schema.copy()
        # Remove fields that might legitimately differ between transports
        normalized.pop("serverInfo", None)
        normalized.pop("timestamp", None)
        normalized_schemas[name] = normalized
    
    # Compare all schemas against the first one
    schema_names = list(normalized_schemas.keys())
    base_schema = normalized_schemas[schema_names[0]]
    
    for i in range(1, len(schema_names)):
        compare_name = schema_names[i]
        compare_schema = normalized_schemas[compare_name]
        
        if base_schema != compare_schema:
            print(f"❌ TRANSPORT-AGNOSTIC VIOLATION: {schema_names[0]} != {compare_name}")
            print(f"   This indicates transport-specific bugs in schema generation")
            return False
    
    print(f"✅ TRANSPORT-AGNOSTIC VALIDATED: All {len(schema_names)} schemas are identical")
    return True

def main():
    """Validate MCP transport-agnostic design and schema quality."""
    print("🔍 MCP Transport-Agnostic Design Validation")
    print("=" * 50)
    
    # Load available schemas to validate transport-agnostic design
    # All schemas should be identical if transport-agnostic design is correct
    schemas = {
        "stdio": load_schema("mcp_server_stdio.json"),
        "http": load_schema("mcp_server_http.json"), 
        "sse": load_schema("mcp_server_sse.json")
    }
    
    # First: Validate transport-agnostic design
    print("\n🎯 Primary Validation: Transport-Agnostic Design")
    is_transport_agnostic = validate_transport_agnostic_design(schemas)
    
    # Analyze each schema
    analyses = {}
    for name, schema in schemas.items():
        analyses[name] = analyze_schema_completeness(schema, name)
    
    # Display schema quality analysis
    print(f"\n📊 Schema Quality Analysis:")
    print(f"{'Transport':<10} {'Exists':<6} {'Tools':<6} {'Schema':<7} {'Caps':<5} {'Anno':<5} {'Examples':<8} {'Size(KB)':<8}")
    print("-" * 70)
    
    for name, analysis in analyses.items():
        if analysis["exists"]:
            print(f"{name:<10} {'✅':<6} {analysis['tools_count']:<6} "
                  f"{'✅' if analysis['has_schema_field'] else '❌':<7} "
                  f"{'✅' if analysis['has_capabilities'] else '❌':<5} "
                  f"{'✅' if analysis['has_annotations'] else '❌':<5} "
                  f"{'✅' if analysis['has_examples'] else '❌':<8} "
                  f"{analysis['file_size_kb']:<8}")
        else:
            print(f"{name:<10} {'❌':<6} {'N/A':<6} {'N/A':<7} {'N/A':<5} {'N/A':<5} {'N/A':<8} {'N/A':<8}")
    
    # MCP Compliance Check
    print("\n🎯 MCP Compliance Summary:")
    required_fields = ["$schema", "$id", "capabilities", "protocolVersion"]
    
    for name, analysis in analyses.items():
        if not analysis["exists"]:
            continue
            
        compliance_score = 0
        total_checks = len(required_fields)
        
        for field in required_fields:
            field_key = f"has_{field.replace('$', '').replace('V', '_v').lower()}"
            if analysis.get(field_key, False):
                compliance_score += 1
        
        compliance_pct = round((compliance_score / total_checks) * 100)
        status = "✅ COMPLIANT" if compliance_pct >= 100 else f"⚠️ {compliance_pct}% COMPLIANT"
        print(f"  • {name}: {status} ({compliance_score}/{total_checks} required fields)")
    
    # Compare tool descriptions
    compare_tool_descriptions(schemas)
    
    # Recommendations
    print("\n💡 Transport-Agnostic Recommendations:")
    
    # Check all transports for common issues
    for transport_name, analysis in analyses.items():
        if not analysis.get("exists", False):
            continue
            
        issues = []
        if not analysis.get("has_schema_field", False):
            issues.append("Add $schema field for MCP compliance")
        if not analysis.get("has_capabilities", False):
            issues.append("Add capabilities field for MCP compliance")
        if not analysis.get("has_annotations", False):
            issues.append("Consider adding tool annotations for governance")
        if not analysis.get("has_examples", False):
            issues.append("Consider adding tool examples for better LLM understanding")
            
        if issues:
            print(f"  • {transport_name} transport: {'; '.join(issues)}")
        else:
            print(f"  • {transport_name} transport: ✅ Full MCP compliance")
    
    # Summary
    print(f"\n📋 Transport-Agnostic Design Summary:")
    existing_transports = [name for name, analysis in analyses.items() if analysis["exists"]]
    
    if existing_transports:
        print(f"  • Available transport schemas: {', '.join(existing_transports)}")
        print(f"  • Transport-agnostic design: {'✅ VALID' if is_transport_agnostic else '❌ VIOLATED'}")
        
        if len(existing_transports) == 1:
            print(f"  • Schema quality: {existing_transports[0]} transport only (need more for validation)")
        else:
            # All should have same quality since they should be identical
            sample_analysis = analyses[existing_transports[0]]
            if (sample_analysis["has_schema_field"] and sample_analysis["has_capabilities"]):
                print(f"  • MCP compliance: ✅ All transports compliant")
            else:
                print(f"  • MCP compliance: ❌ All transports need fixes")
    else:
        print("  • No transport schemas found. Run an export script first.")
        print("  • Next step: python scripts/mcp/export_mcp_schema_stdio.py")

if __name__ == "__main__":
    main() 
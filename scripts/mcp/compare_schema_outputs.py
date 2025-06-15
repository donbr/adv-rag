#!/usr/bin/env python3
"""
Compare MCP schema outputs from different export methods.

This script provides meaningful comparisons between:
- Legacy export (export_mcp_schema.py)
- HTTP export (export_mcp_schema_http.py) 
- Native export (export_mcp_schema_native.py)
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

def main():
    """Compare schema outputs from different export methods."""
    print("🔍 MCP Schema Export Method Comparison")
    print("=" * 50)
    
    # Load all available schemas
    schemas = {
        "Legacy": load_schema("mcp_server_schema.json"),
        "HTTP": load_schema("mcp_server_http.json"), 
        "Native": load_schema("mcp_server_native.json"),
        "Official": load_schema("mcp_server_official.json")
    }
    
    # Analyze each schema
    analyses = {}
    for name, schema in schemas.items():
        analyses[name] = analyze_schema_completeness(schema, name)
    
    # Display comparison table
    print("\n📊 Feature Comparison:")
    print(f"{'Method':<10} {'Exists':<6} {'Tools':<6} {'Schema':<7} {'Caps':<5} {'Anno':<5} {'Examples':<8} {'Size(KB)':<8}")
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
    print("\n💡 Recommendations:")
    
    native_analysis = analyses.get("Native", {})
    if native_analysis.get("exists", False):
        if not native_analysis.get("has_schema_field", False):
            print("  • Native: Add $schema field for MCP compliance")
        if not native_analysis.get("has_capabilities", False):
            print("  • Native: Add capabilities field for MCP compliance")
        if not native_analysis.get("has_annotations", False):
            print("  • Native: Consider adding tool annotations for governance")
        if not native_analysis.get("has_examples", False):
            print("  • Native: Consider adding tool examples for better LLM understanding")
    
    # Summary
    print(f"\n📋 Summary:")
    existing_methods = [name for name, analysis in analyses.items() if analysis["exists"]]
    if existing_methods:
        print(f"  • Available exports: {', '.join(existing_methods)}")
        
        # Find most complete
        most_complete = max(existing_methods, 
                          key=lambda x: sum([
                              analyses[x]["has_schema_field"],
                              analyses[x]["has_capabilities"], 
                              analyses[x]["has_annotations"],
                              analyses[x]["has_examples"]
                          ]))
        print(f"  • Most feature-complete: {most_complete}")
        
        # Find most compliant
        compliant_methods = []
        for name in existing_methods:
            analysis = analyses[name]
            if (analysis["has_schema_field"] and 
                analysis["has_capabilities"]):
                compliant_methods.append(name)
        
        if compliant_methods:
            print(f"  • MCP compliant: {', '.join(compliant_methods)}")
        else:
            print(f"  • MCP compliant: None (all need compliance fixes)")
    else:
        print("  • No schema exports found. Run an export script first.")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Response Format Analyzer for MCP Tools

This script tests all MCP tools and documents their response formats and expected outputs.
Used for sub-task 1.4: Document response formats and expected outputs for each tool.
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to Python path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import Client
from src.mcp.server import mcp

async def test_tool_response_format(client: Client, tool_name: str, question: str) -> Dict[str, Any]:
    """Test a tool and capture its response format."""
    try:
        start_time = datetime.now()
        result = await client.call_tool(tool_name, {"question": question})
        end_time = datetime.now()
        
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Parse the response content
        if result.content and len(result.content) > 0:
            content = result.content[0]
            text_content = content.text if hasattr(content, 'text') else str(content)
            
            # Try to parse as JSON if possible
            parsed_data = None
            try:
                parsed_data = json.loads(text_content)
            except json.JSONDecodeError:
                parsed_data = {"raw_text": text_content}
            
            return {
                "status": "success",
                "response_time_ms": response_time_ms,
                "content_type": str(type(content).__name__),
                "content_structure": {
                    "type": getattr(content, 'type', 'unknown'),
                    "has_text": hasattr(content, 'text'),
                    "text_length": len(text_content) if text_content else 0,
                    "text_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content
                },
                "parsed_response": parsed_data,
                "response_schema": analyze_response_schema(parsed_data)
            }
        else:
            return {
                "status": "success",
                "response_time_ms": response_time_ms,
                "content_type": "empty",
                "content_structure": {},
                "parsed_response": None,
                "response_schema": {"type": "empty"}
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "response_time_ms": 0,
            "content_type": "error",
            "content_structure": {},
            "parsed_response": None,
            "response_schema": {"type": "error"}
        }

def analyze_response_schema(data: Any) -> Dict[str, Any]:
    """Analyze the schema structure of a response."""
    if data is None:
        return {"type": "null"}
    elif isinstance(data, dict):
        schema = {"type": "object", "properties": {}}
        for key, value in data.items():
            schema["properties"][key] = analyze_response_schema(value)
        return schema
    elif isinstance(data, list):
        if len(data) > 0:
            return {"type": "array", "items": analyze_response_schema(data[0])}
        else:
            return {"type": "array", "items": {"type": "unknown"}}
    elif isinstance(data, str):
        return {"type": "string", "max_length": len(data)}
    elif isinstance(data, int):
        return {"type": "integer"}
    elif isinstance(data, float):
        return {"type": "number"}
    elif isinstance(data, bool):
        return {"type": "boolean"}
    else:
        return {"type": "unknown", "python_type": str(type(data))}

async def test_utility_tool(client: Client, tool_name: str) -> Dict[str, Any]:
    """Test utility tools that don't require parameters."""
    try:
        start_time = datetime.now()
        result = await client.call_tool(tool_name, {})
        end_time = datetime.now()
        
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        if result.content and len(result.content) > 0:
            content = result.content[0]
            text_content = content.text if hasattr(content, 'text') else str(content)
            
            # Try to parse as JSON
            parsed_data = None
            try:
                parsed_data = json.loads(text_content)
            except json.JSONDecodeError:
                parsed_data = {"raw_text": text_content}
            
            return {
                "status": "success",
                "response_time_ms": response_time_ms,
                "content_type": str(type(content).__name__),
                "parsed_response": parsed_data,
                "response_schema": analyze_response_schema(parsed_data)
            }
        else:
            return {
                "status": "success",
                "response_time_ms": response_time_ms,
                "content_type": "empty",
                "parsed_response": None,
                "response_schema": {"type": "empty"}
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "response_time_ms": 0
        }

async def analyze_all_tool_responses():
    """Analyze response formats for all MCP tools."""
    print("🔍 Analyzing MCP Tool Response Formats")
    print("=" * 60)
    
    # Test questions for different scenarios
    test_questions = [
        "What makes a good action movie?",
        "Who is the main character in John Wick?",
        "What are the best action scenes?",
        "How does John Wick compare to other action movies?"
    ]
    
    # Expected retrieval tools
    retrieval_tools = [
        "naive_retriever",
        "bm25_retriever", 
        "contextual_compression_retriever",
        "multi_query_retriever",
        "ensemble_retriever",
        "semantic_retriever"
    ]
    
    # Expected utility tools
    utility_tools = [
        "health_check_health_get",
        "cache_stats_cache_stats_get"
    ]
    
    analysis_results = {}
    
    async with Client(mcp) as client:
        print(f"📋 Connected to MCP server")
        
        # Test retrieval tools
        print(f"\n🔧 Testing Retrieval Tools ({len(retrieval_tools)} tools)")
        print("-" * 40)
        
        for tool_name in retrieval_tools:
            print(f"  Testing {tool_name}...")
            # Test with first question
            result = await test_tool_response_format(client, tool_name, test_questions[0])
            analysis_results[tool_name] = {
                "tool_type": "retrieval",
                "input_schema": {"question": "string"},
                "test_question": test_questions[0],
                "response_analysis": result
            }
            
            if result["status"] == "success":
                print(f"    ✅ SUCCESS (⏱️ {result['response_time_ms']}ms)")
                if result.get("parsed_response") and isinstance(result["parsed_response"], dict):
                    answer_key = None
                    for key in ["answer", "response", "result", "text"]:
                        if key in result["parsed_response"]:
                            answer_key = key
                            break
                    if answer_key:
                        answer_preview = str(result["parsed_response"][answer_key])[:100]
                        print(f"    📄 Response: {answer_preview}...")
            else:
                print(f"    ❌ ERROR: {result.get('error_message', 'Unknown error')}")
        
        # Test utility tools
        print(f"\n🛠️ Testing Utility Tools ({len(utility_tools)} tools)")
        print("-" * 40)
        
        for tool_name in utility_tools:
            print(f"  Testing {tool_name}...")
            result = await test_utility_tool(client, tool_name)
            analysis_results[tool_name] = {
                "tool_type": "utility",
                "input_schema": {},
                "response_analysis": result
            }
            
            if result["status"] == "success":
                print(f"    ✅ SUCCESS (⏱️ {result['response_time_ms']}ms)")
                if result.get("parsed_response"):
                    print(f"    📊 Data: {str(result['parsed_response'])[:100]}...")
            else:
                print(f"    ❌ ERROR: {result.get('error_message', 'Unknown error')}")
    
    return analysis_results

def generate_response_format_documentation(analysis_results: Dict[str, Any]) -> str:
    """Generate markdown documentation for response formats."""
    doc = "# MCP Tools Response Format Documentation\n\n"
    doc += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    doc += "This document provides detailed response format specifications for all MCP tools.\n\n"
    
    # Retrieval Tools Section
    doc += "## Retrieval Tools\n\n"
    doc += "All retrieval tools accept a `question` parameter (string) and return structured responses.\n\n"
    
    retrieval_tools = {k: v for k, v in analysis_results.items() if v.get("tool_type") == "retrieval"}
    
    for tool_name, data in retrieval_tools.items():
        doc += f"### {tool_name}\n\n"
        
        response_analysis = data["response_analysis"]
        
        if response_analysis["status"] == "success":
            doc += f"**Response Time:** ~{response_analysis['response_time_ms']}ms\n\n"
            
            # Input schema
            doc += "**Input Schema:**\n```json\n"
            doc += json.dumps(data["input_schema"], indent=2)
            doc += "\n```\n\n"
            
            # Response schema
            if response_analysis.get("response_schema"):
                doc += "**Response Schema:**\n```json\n"
                doc += json.dumps(response_analysis["response_schema"], indent=2)
                doc += "\n```\n\n"
            
            # Example response
            if response_analysis.get("parsed_response"):
                doc += "**Example Response:**\n```json\n"
                example_response = response_analysis["parsed_response"]
                # Truncate long text for documentation
                if isinstance(example_response, dict):
                    truncated_response = {}
                    for key, value in example_response.items():
                        if isinstance(value, str) and len(value) > 200:
                            truncated_response[key] = value[:200] + "... [truncated]"
                        else:
                            truncated_response[key] = value
                    doc += json.dumps(truncated_response, indent=2)
                else:
                    doc += json.dumps(example_response, indent=2)
                doc += "\n```\n\n"
        else:
            doc += f"**Status:** ❌ ERROR - {response_analysis.get('error_message', 'Unknown error')}\n\n"
    
    # Utility Tools Section
    doc += "## Utility Tools\n\n"
    doc += "Utility tools provide system information and don't require question parameters.\n\n"
    
    utility_tools = {k: v for k, v in analysis_results.items() if v.get("tool_type") == "utility"}
    
    for tool_name, data in utility_tools.items():
        doc += f"### {tool_name}\n\n"
        
        response_analysis = data["response_analysis"]
        
        if response_analysis["status"] == "success":
            doc += f"**Response Time:** ~{response_analysis['response_time_ms']}ms\n\n"
            
            # Response schema
            if response_analysis.get("response_schema"):
                doc += "**Response Schema:**\n```json\n"
                doc += json.dumps(response_analysis["response_schema"], indent=2)
                doc += "\n```\n\n"
            
            # Example response
            if response_analysis.get("parsed_response"):
                doc += "**Example Response:**\n```json\n"
                doc += json.dumps(response_analysis["parsed_response"], indent=2)
                doc += "\n```\n\n"
        else:
            doc += f"**Status:** ❌ ERROR - {response_analysis.get('error_message', 'Unknown error')}\n\n"
    
    # Summary section
    doc += "## Summary\n\n"
    successful_tools = [k for k, v in analysis_results.items() if v["response_analysis"]["status"] == "success"]
    failed_tools = [k for k, v in analysis_results.items() if v["response_analysis"]["status"] == "error"]
    
    doc += f"- **Total Tools:** {len(analysis_results)}\n"
    doc += f"- **Successful:** {len(successful_tools)}\n"
    doc += f"- **Failed:** {len(failed_tools)}\n\n"
    
    if failed_tools:
        doc += f"**Failed Tools:** {', '.join(failed_tools)}\n\n"
    
    # Performance summary
    response_times = [v["response_analysis"]["response_time_ms"] for v in analysis_results.values() 
                     if v["response_analysis"]["status"] == "success"]
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        doc += f"**Average Response Time:** {avg_response_time:.1f}ms\n"
        doc += f"**Min Response Time:** {min(response_times)}ms\n"
        doc += f"**Max Response Time:** {max(response_times)}ms\n\n"
    
    return doc

async def main():
    """Main execution function."""
    try:
        # Analyze all tools
        analysis_results = await analyze_all_tool_responses()
        
        # Generate documentation
        print(f"\n📝 Generating response format documentation...")
        documentation = generate_response_format_documentation(analysis_results)
        
        # Save to deliverables
        deliverables_dir = Path("tasks/deliverables")
        deliverables_dir.mkdir(exist_ok=True)
        
        doc_file = deliverables_dir / "mcp-tool-response-formats.md"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        # Also save raw analysis data
        analysis_file = deliverables_dir / "mcp-tool-response-analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2)
        
        print(f"✅ Documentation saved to:")
        print(f"   📄 {doc_file}")
        print(f"   📊 {analysis_file}")
        
        # Print summary
        print(f"\n📊 Analysis Summary:")
        successful_tools = [k for k, v in analysis_results.items() if v["response_analysis"]["status"] == "success"]
        failed_tools = [k for k, v in analysis_results.items() if v["response_analysis"]["status"] == "error"]
        print(f"   ✅ Successful tools: {len(successful_tools)}")
        print(f"   ❌ Failed tools: {len(failed_tools)}")
        
        if failed_tools:
            print(f"   🚨 Failed: {', '.join(failed_tools)}")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 
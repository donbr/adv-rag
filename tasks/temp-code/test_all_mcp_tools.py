#!/usr/bin/env python3
"""
Comprehensive MCP Tools Test Runner

This script uses the test data samples to systematically validate all 8 MCP tools
and generate detailed validation reports.

Usage: python test_all_mcp_tools.py [--quick] [--tool TOOL_NAME]
"""

import asyncio
import json
import time
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import test data samples
sys.path.append(str(current_file.parent))
from test_data_samples import (
    MCPTestDataSamples, 
    TestCase, 
    create_test_suite_for_tool,
    generate_test_report_template
)

# Import MCP client
from fastmcp import Client

class MCPToolValidator:
    """Comprehensive validator for all MCP tools"""
    
    RETRIEVAL_TOOLS = [
        "naive_retriever",
        "bm25_retriever", 
        "contextual_compression_retriever",
        "multi_query_retriever",
        "ensemble_retriever",
        "semantic_retriever"
    ]
    
    UTILITY_TOOLS = [
        "health_check_health_get",
        "cache_stats_cache_stats_get"
    ]
    
    ALL_TOOLS = RETRIEVAL_TOOLS + UTILITY_TOOLS
    
    def __init__(self, mcp_server_module: str = "src.mcp.server"):
        """Initialize the validator with MCP server reference"""
        self.mcp_server_module = mcp_server_module
        self.test_results = {}
        self.start_time = None
        
    async def run_comprehensive_validation(self, 
                                         quick_mode: bool = False,
                                         specific_tool: Optional[str] = None) -> Dict[str, Any]:
        """
        Run comprehensive validation of all MCP tools
        
        Args:
            quick_mode: If True, run only core tests
            specific_tool: If provided, test only this tool
            
        Returns:
            Complete validation report
        """
        self.start_time = datetime.now()
        
        print("🧪 Starting MCP Tools Comprehensive Validation")
    print("=" * 60)
        print(f"Timestamp: {self.start_time}")
        print(f"Quick mode: {quick_mode}")
        print(f"Specific tool: {specific_tool or 'All tools'}")
        print()
        
        # Import and create MCP server
        try:
            from src.mcp.server import mcp
            print("✅ MCP server imported successfully")
        except Exception as e:
            print(f"❌ Failed to import MCP server: {e}")
            return {"error": f"Failed to import MCP server: {e}"}
        
        # Determine which tools to test
        tools_to_test = [specific_tool] if specific_tool else self.ALL_TOOLS
        
        # Validate each tool
        async with Client(mcp) as client:
            for tool_name in tools_to_test:
                print(f"\n🔍 Testing tool: {tool_name}")
                print("-" * 40)
                
                if tool_name in self.RETRIEVAL_TOOLS:
                    result = await self._test_retrieval_tool(client, tool_name, quick_mode)
                elif tool_name in self.UTILITY_TOOLS:
                    result = await self._test_utility_tool(client, tool_name)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                self.test_results[tool_name] = result
                self._print_tool_summary(tool_name, result)
        
        # Generate final report
        final_report = self._generate_final_report()
        return final_report
    
    async def _test_retrieval_tool(self, client: Client, tool_name: str, quick_mode: bool) -> Dict[str, Any]:
        """Test a retrieval tool with comprehensive test cases"""
        tool_result = generate_test_report_template()
        tool_result["tool_name"] = tool_name
        tool_result["execution_timestamp"] = datetime.now().isoformat()
        
        # Get test cases based on mode
        if quick_mode:
            test_cases = MCPTestDataSamples.get_core_tests()
            print(f"  Running {len(test_cases)} core tests")
        else:
            test_cases = MCPTestDataSamples.get_all_retrieval_tests()
            print(f"  Running {len(test_cases)} comprehensive tests")
        
        # Track performance metrics
        response_times = []
        answer_lengths = []
        cache_hits = 0
        
        # Execute test cases
        for i, test_case in enumerate(test_cases, 1):
            print(f"    [{i}/{len(test_cases)}] {test_case.name}...", end=" ")
            
            try:
                # Measure response time
                start_time = time.time()
                result = await client.call_tool(tool_name, test_case.parameters)
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                # Validate response
                validation = MCPTestDataSamples.validate_response(result, test_case)
                
                # Track metrics
                if validation.get("metrics", {}).get("answer_length"):
                    answer_lengths.append(validation["metrics"]["answer_length"])
                
                # Check for cache hit (rough heuristic - very fast response)
                if response_time < 0.2:
                    cache_hits += 1
                
                # Store result
                validation["response_time"] = response_time
                
                if test_case.name in ["action_movie_quality", "john_wick_specific", "character_development"]:
                    tool_result["test_results"]["core_tests"].append(validation)
                elif test_case.name in ["very_short_query", "very_long_query", "special_characters", "numeric_query", "empty_query"]:
                    tool_result["test_results"]["edge_cases"].append(validation)
                else:
                    tool_result["test_results"]["comparison_tests"].append(validation)
                
                # Print result
                if validation["passed"]:
                    warnings = len(validation["warnings"])
                    if warnings > 0:
                        print(f"⚠️  PASS ({warnings} warnings)")
                    else:
                        print("✅ PASS")
                else:
                    print(f"❌ FAIL ({len(validation['errors'])} errors)")
                    
            except Exception as e:
                print(f"💥 ERROR: {e}")
                tool_result["test_results"]["core_tests"].append({
                    "test_name": test_case.name,
                    "passed": False,
                    "errors": [f"Exception: {e}"],
                    "warnings": [],
                    "metrics": {}
                })
        
        # Test parameter validation
        print(f"    Testing parameter validation...")
        invalid_tests = MCPTestDataSamples.get_invalid_parameter_tests()
        for invalid_test in invalid_tests:
            try:
                if "expected_error" in invalid_test:
                    # Should fail
                    try:
                        await client.call_tool(tool_name, invalid_test["parameters"])
                        # If we get here, it didn't fail as expected
                        tool_result["test_results"]["parameter_validation"].append({
                            "test_name": invalid_test["name"],
                            "passed": False,
                            "errors": ["Expected error but got success"],
                            "warnings": []
                        })
                    except Exception:
                        # Expected failure
                        tool_result["test_results"]["parameter_validation"].append({
                            "test_name": invalid_test["name"],
                            "passed": True,
                            "errors": [],
                            "warnings": []
                        })
                        else:
                    # Should succeed (extra parameters test)
                    result = await client.call_tool(tool_name, invalid_test["parameters"])
                    validation = MCPTestDataSamples.validate_response(
                        result, 
                        TestCase(
                            name=invalid_test["name"],
                            description=invalid_test["description"],
                            parameters=invalid_test["parameters"],
                            expected_response_keys=invalid_test["expected_response_keys"]
                        )
                    )
                    tool_result["test_results"]["parameter_validation"].append(validation)
                    
            except Exception as e:
                tool_result["test_results"]["parameter_validation"].append({
                    "test_name": invalid_test["name"],
                    "passed": False,
                    "errors": [f"Unexpected exception: {e}"],
                    "warnings": []
                })
        
        # Calculate summary statistics
        all_results = (tool_result["test_results"]["core_tests"] + 
                      tool_result["test_results"]["edge_cases"] +
                      tool_result["test_results"]["comparison_tests"] +
                      tool_result["test_results"]["parameter_validation"])
        
        tool_result["summary"]["total_tests"] = len(all_results)
        tool_result["summary"]["passed"] = sum(1 for r in all_results if r["passed"])
        tool_result["summary"]["failed"] = tool_result["summary"]["total_tests"] - tool_result["summary"]["passed"]
        tool_result["summary"]["warnings"] = sum(len(r.get("warnings", [])) for r in all_results)
        
        if tool_result["summary"]["total_tests"] > 0:
            tool_result["summary"]["success_rate"] = tool_result["summary"]["passed"] / tool_result["summary"]["total_tests"]
        
        # Performance metrics
        if response_times:
            tool_result["performance_metrics"]["average_response_time"] = sum(response_times) / len(response_times)
        if answer_lengths:
            tool_result["performance_metrics"]["average_answer_length"] = sum(answer_lengths) / len(answer_lengths)
        if len(test_cases) > 0:
            tool_result["performance_metrics"]["cache_hit_rate"] = cache_hits / len(test_cases)
        
        return tool_result
    
    async def _test_utility_tool(self, client: Client, tool_name: str) -> Dict[str, Any]:
        """Test a utility tool (health check, cache stats)"""
        tool_result = generate_test_report_template()
        tool_result["tool_name"] = tool_name
        tool_result["execution_timestamp"] = datetime.now().isoformat()
        
        print(f"  Testing utility tool (no parameters required)")
        
        try:
            start_time = time.time()
            result = await client.call_tool(tool_name, {})
            response_time = time.time() - start_time
            
            # Basic validation for utility tools
            validation_result = {
                "test_name": f"{tool_name}_basic_test",
                "passed": True,
                "errors": [],
                "warnings": [],
                "metrics": {"response_time": response_time}
            }
            
            # Check response structure
            if not isinstance(result, list) or len(result) != 1:
                validation_result["passed"] = False
                validation_result["errors"].append("Invalid response structure")
                            else:
                try:
                    if hasattr(result[0], 'text'):
                        parsed = json.loads(result[0].text)
                        validation_result["metrics"]["response_content"] = parsed
                        else:
                        validation_result["warnings"].append("Response doesn't have text attribute")
                except json.JSONDecodeError:
                    validation_result["warnings"].append("Response is not valid JSON")
            
            tool_result["test_results"]["core_tests"].append(validation_result)
            
            # Summary
            tool_result["summary"]["total_tests"] = 1
            tool_result["summary"]["passed"] = 1 if validation_result["passed"] else 0
            tool_result["summary"]["failed"] = 0 if validation_result["passed"] else 1
            tool_result["summary"]["warnings"] = len(validation_result["warnings"])
            tool_result["summary"]["success_rate"] = 1.0 if validation_result["passed"] else 0.0
            
            # Performance
            tool_result["performance_metrics"]["average_response_time"] = response_time
            
            print(f"    ✅ PASS" if validation_result["passed"] else f"    ❌ FAIL")
                        
                    except Exception as e:
            print(f"    💥 ERROR: {e}")
            validation_result = {
                "test_name": f"{tool_name}_basic_test",
                "passed": False,
                "errors": [f"Exception: {e}"],
                "warnings": [],
                "metrics": {}
            }
            tool_result["test_results"]["core_tests"].append(validation_result)
            tool_result["summary"]["total_tests"] = 1
            tool_result["summary"]["failed"] = 1
        
        return tool_result
    
    def _print_tool_summary(self, tool_name: str, result: Dict[str, Any]):
        """Print a summary for a single tool's test results"""
        if "error" in result:
            print(f"  ❌ TOOL FAILED: {result['error']}")
            return
        
        summary = result["summary"]
        performance = result["performance_metrics"]
        
        print(f"  📊 SUMMARY:")
        print(f"    Tests: {summary['passed']}/{summary['total_tests']} passed ({summary['success_rate']:.1%})")
        if summary["warnings"] > 0:
            print(f"    Warnings: {summary['warnings']}")
        if performance.get("average_response_time"):
            print(f"    Avg Response Time: {performance['average_response_time']:.3f}s")
        if performance.get("cache_hit_rate"):
            print(f"    Cache Hit Rate: {performance['cache_hit_rate']:.1%}")
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        end_time = datetime.now()
        execution_duration = end_time - self.start_time
        
        # Aggregate statistics
        total_tests = sum(r.get("summary", {}).get("total_tests", 0) for r in self.test_results.values() if "error" not in r)
        total_passed = sum(r.get("summary", {}).get("passed", 0) for r in self.test_results.values() if "error" not in r)
        total_failed = sum(r.get("summary", {}).get("failed", 0) for r in self.test_results.values() if "error" not in r)
        total_warnings = sum(r.get("summary", {}).get("warnings", 0) for r in self.test_results.values() if "error" not in r)
        
        # Tool status summary
        successful_tools = [name for name, result in self.test_results.items() 
                          if "error" not in result and result.get("summary", {}).get("success_rate", 0) == 1.0]
        failed_tools = [name for name, result in self.test_results.items() 
                       if "error" in result or result.get("summary", {}).get("success_rate", 0) < 1.0]
        
        final_report = {
            "execution_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": execution_duration.total_seconds(),
                "tools_tested": list(self.test_results.keys())
            },
            "aggregate_summary": {
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_warnings": total_warnings,
                "overall_success_rate": total_passed / total_tests if total_tests > 0 else 0.0
            },
            "tool_status": {
                "successful_tools": successful_tools,
                "failed_tools": failed_tools,
                "tools_with_warnings": [name for name, result in self.test_results.items() 
                                      if "error" not in result and result.get("summary", {}).get("warnings", 0) > 0]
            },
            "detailed_results": self.test_results
        }
        
        return final_report

async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Comprehensive MCP Tools Validator")
    parser.add_argument("--quick", action="store_true", help="Run only core tests (faster)")
    parser.add_argument("--tool", type=str, help="Test only specific tool")
    parser.add_argument("--output", type=str, help="Output file for detailed report (JSON)")
    args = parser.parse_args()
    
    # Validate tool name if provided
    if args.tool and args.tool not in MCPToolValidator.ALL_TOOLS:
        print(f"❌ Unknown tool: {args.tool}")
        print(f"Available tools: {', '.join(MCPToolValidator.ALL_TOOLS)}")
        return 1
    
    # Run validation
    validator = MCPToolValidator()
    final_report = await validator.run_comprehensive_validation(
        quick_mode=args.quick,
        specific_tool=args.tool
    )
    
    # Print final summary
    print("\n" + "=" * 60)
    print("🎯 FINAL VALIDATION REPORT")
    print("=" * 60)
    
    if "error" in final_report:
        print(f"❌ Validation failed: {final_report['error']}")
        return 1
    
    aggregate = final_report["aggregate_summary"]
    tool_status = final_report["tool_status"]
    
    print(f"⏱️  Duration: {final_report['execution_info']['duration_seconds']:.1f} seconds")
    print(f"📊 Overall: {aggregate['total_passed']}/{aggregate['total_tests']} tests passed ({aggregate['overall_success_rate']:.1%})")
    print(f"⚠️  Warnings: {aggregate['total_warnings']}")
    print()
    
    print(f"✅ Successful tools ({len(tool_status['successful_tools'])}): {', '.join(tool_status['successful_tools'])}")
    if tool_status['failed_tools']:
        print(f"❌ Failed tools ({len(tool_status['failed_tools'])}): {', '.join(tool_status['failed_tools'])}")
    if tool_status['tools_with_warnings']:
        print(f"⚠️  Tools with warnings: {', '.join(tool_status['tools_with_warnings'])}")
    
    # Save detailed report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(final_report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {args.output}")
    
    # Return exit code
    return 0 if aggregate['overall_success_rate'] == 1.0 else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 
#!/usr/bin/env python3
"""
MCP Milestone Test Runner

Executes all MCP milestone tests in sequence and provides comprehensive reporting.
This consolidates the milestone-based testing approach with automated validation.
"""
import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

class MCPMilestoneRunner:
    """Runs all MCP milestone tests and provides comprehensive reporting."""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "execution_times": {},
            "milestone_results": {}
        }
    
    def get_milestone_tests(self) -> List[Tuple[str, Path, str]]:
        """Get list of milestone tests to run."""
        tests = [
            ("Milestone 1: Initialization", 
             self.script_dir / "01-initialization" / "test-initialize.py",
             "MCP server initialization and capability negotiation"),
            
            ("Milestone 2: Tool Discovery", 
             self.script_dir / "02-tools" / "test-tools-discovery.py",
             "Tool listing and schema validation"),
            
            ("Milestone 3: Tool Execution (Semantic Search)", 
             self.script_dir / "03-tool-execution" / "semantic-search" / "test.py",
             "Semantic search tool execution and response validation"),
            
            ("Simple MCP Client Test", 
             self.script_dir / "simple_mcp_test.py",
             "Basic connectivity and smoke testing"),
            
            ("MCP Endpoints Bash Test", 
             self.script_dir / "test_mcp_endpoints.sh",
             "System-level process validation and log analysis")
        ]
        
        return tests
    
    async def run_python_test(self, test_path: Path) -> Tuple[bool, str, float]:
        """Run a Python test and return success, output, and execution time."""
        start_time = time.time()
        
        try:
            # Run the test using uv
            process = await asyncio.create_subprocess_exec(
                "uv", "run", "python", str(test_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.script_dir.parent.parent  # Go back to project root
            )
            
            stdout, _ = await process.communicate()
            execution_time = time.time() - start_time
            
            output = stdout.decode('utf-8') if stdout else ""
            success = process.returncode == 0
            
            return success, output, execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            return False, f"Test execution failed: {e}", execution_time
    
    async def run_bash_test(self, test_path: Path) -> Tuple[bool, str, float]:
        """Run a bash test and return success, output, and execution time."""
        start_time = time.time()
        
        try:
            # Make sure the script is executable
            test_path.chmod(0o755)
            
            # Run the bash test
            process = await asyncio.create_subprocess_exec(
                "bash", str(test_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.script_dir.parent.parent  # Go back to project root
            )
            
            stdout, _ = await process.communicate()
            execution_time = time.time() - start_time
            
            output = stdout.decode('utf-8') if stdout else ""
            success = process.returncode == 0
            
            return success, output, execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            return False, f"Bash test execution failed: {e}", execution_time
    
    async def run_single_test(self, name: str, test_path: Path, description: str) -> bool:
        """Run a single test and update results."""
        print(f"\n{'='*80}")
        print(f"🧪 Running: {name}")
        print(f"📝 Description: {description}")
        print(f"📁 Path: {test_path}")
        print(f"{'='*80}")
        
        if not test_path.exists():
            error_msg = f"❌ Test file not found: {test_path}"
            print(error_msg)
            self.test_results["errors"].append(error_msg)
            self.test_results["failed"] += 1
            self.test_results["milestone_results"][name] = {
                "success": False,
                "output": error_msg,
                "execution_time": 0.0
            }
            return False
        
        # Determine test type and run accordingly
        if test_path.suffix == ".py":
            success, output, exec_time = await self.run_python_test(test_path)
        elif test_path.suffix == ".sh":
            success, output, exec_time = await self.run_bash_test(test_path)
        else:
            error_msg = f"❌ Unsupported test type: {test_path.suffix}"
            print(error_msg)
            self.test_results["errors"].append(error_msg)
            self.test_results["failed"] += 1
            return False
        
        # Store results
        self.test_results["execution_times"][name] = exec_time
        self.test_results["milestone_results"][name] = {
            "success": success,
            "output": output,
            "execution_time": exec_time
        }
        
        # Update counters
        if success:
            self.test_results["passed"] += 1
            print(f"✅ {name}: PASSED ({exec_time:.2f}s)")
        else:
            self.test_results["failed"] += 1
            print(f"❌ {name}: FAILED ({exec_time:.2f}s)")
            
            # Show last few lines of output for debugging
            output_lines = output.strip().split('\n')
            if len(output_lines) > 5:
                print("📋 Last 5 lines of output:")
                for line in output_lines[-5:]:
                    print(f"   {line}")
            else:
                print("📋 Full output:")
                for line in output_lines:
                    print(f"   {line}")
        
        return success
    
    async def run_all_tests(self) -> bool:
        """Run all milestone tests."""
        print("🚀 MCP Milestone Test Runner")
        print("=" * 80)
        print("Running comprehensive MCP server validation tests...")
        
        milestone_tests = self.get_milestone_tests()
        self.test_results["total_tests"] = len(milestone_tests)
        
        overall_success = True
        
        for name, test_path, description in milestone_tests:
            test_success = await self.run_single_test(name, test_path, description)
            if not test_success:
                overall_success = False
        
        return overall_success
    
    def print_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 80)
        print("📊 MCP MILESTONE TEST SUMMARY")
        print("=" * 80)
        
        # Overall stats
        total = self.test_results["total_tests"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 Overall Results:")
        print(f"   Total Tests: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Success Rate: {success_rate:.1f}%")
        
        # Execution times
        if self.test_results["execution_times"]:
            total_time = sum(self.test_results["execution_times"].values())
            print(f"\n⏱️  Execution Times:")
            print(f"   Total Time: {total_time:.2f}s")
            
            for test_name, exec_time in self.test_results["execution_times"].items():
                status = "✅" if self.test_results["milestone_results"][test_name]["success"] else "❌"
                print(f"   {status} {test_name}: {exec_time:.2f}s")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for test_name, result in self.test_results["milestone_results"].items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"   {status}: {test_name}")
        
        # Errors
        if self.test_results["errors"]:
            print(f"\n🚨 Errors ({len(self.test_results['errors'])}):")
            for error in self.test_results["errors"]:
                print(f"   - {error}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if failed == 0:
            print("   🎉 All tests passed! MCP server is ready for production.")
        elif failed <= 2:
            print("   ⚠️  Minor issues detected. Review failed tests and fix.")
        else:
            print("   🚨 Major issues detected. Comprehensive review needed.")
        
        print("=" * 80)

async def main():
    """Main entry point."""
    runner = MCPMilestoneRunner()
    
    try:
        overall_success = await runner.run_all_tests()
        runner.print_summary()
        
        return 0 if overall_success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Test execution interrupted by user")
        runner.print_summary()
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        runner.print_summary()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 
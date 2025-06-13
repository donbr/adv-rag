#!/usr/bin/env python3
"""
Milestone 2: Tool Discovery & Validation Test

Validates that the MCP server properly lists tools and returns correct schemas
as defined in JSON-RPC samples.
"""
import asyncio
import json
import os
from pathlib import Path
from mcp.client.stdio import stdio_client, StdioServerParameters

# Test configuration
SCRIPT_DIR = Path(__file__).parent
REQUEST_FILE = SCRIPT_DIR / "request-list-tools.json"
EXPECTED_RESPONSE_FILE = SCRIPT_DIR / "response-list-tools.json"
SERVER_COMMAND = ["uv", "run", "python", "-m", "src.mcp_server.main"]

class ToolsDiscoveryTest:
    """Test tool discovery against JSON-RPC samples."""
    
    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    async def load_json_sample(self, file_path: Path) -> dict:
        """Load JSON sample file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load {file_path}: {e}")
    
    def validate_tools_response(self, actual: dict, expected: dict) -> bool:
        """Validate tools response against expected sample."""
        validations = []
        
        # Check JSON-RPC structure
        validations.append(
            self.check_field(actual, expected, "jsonrpc", "JSON-RPC version")
        )
        validations.append(
            self.check_field(actual, expected, "id", "Request ID")
        )
        
        # Check result structure
        if "result" in expected and "result" in actual:
            expected_tools = expected["result"]["tools"]
            actual_tools = actual["result"]["tools"]
            
            # Check tool count
            if len(actual_tools) == len(expected_tools):
                print(f"✅ Tool count: PASS ({len(actual_tools)} tools)")
                validations.append(True)
            else:
                error = f"❌ Tool count: FAIL - Expected {len(expected_tools)}, got {len(actual_tools)}"
                print(error)
                self.test_results["errors"].append(error)
                validations.append(False)
            
            # Check each tool
            expected_tool_names = {tool["name"] for tool in expected_tools}
            actual_tool_names = {tool["name"] for tool in actual_tools}
            
            if expected_tool_names == actual_tool_names:
                print(f"✅ Tool names: PASS ({', '.join(sorted(actual_tool_names))})")
                validations.append(True)
            else:
                missing = expected_tool_names - actual_tool_names
                extra = actual_tool_names - expected_tool_names
                error = f"❌ Tool names: FAIL - Missing: {missing}, Extra: {extra}"
                print(error)
                self.test_results["errors"].append(error)
                validations.append(False)
            
            # Check tool schemas
            for expected_tool in expected_tools:
                actual_tool = next((t for t in actual_tools if t["name"] == expected_tool["name"]), None)
                if actual_tool:
                    validations.append(
                        self.validate_tool_schema(actual_tool, expected_tool)
                    )
        
        return all(validations)
    
    def validate_tool_schema(self, actual_tool: dict, expected_tool: dict) -> bool:
        """Validate individual tool schema."""
        tool_name = actual_tool["name"]
        
        # Check required fields
        required_fields = ["name", "description", "inputSchema"]
        for field in required_fields:
            if field not in actual_tool:
                error = f"❌ Tool {tool_name}: Missing field '{field}'"
                print(error)
                self.test_results["errors"].append(error)
                return False
        
        # Check input schema structure
        input_schema = actual_tool["inputSchema"]
        if "type" not in input_schema or input_schema["type"] != "object":
            error = f"❌ Tool {tool_name}: Invalid input schema type"
            print(error)
            self.test_results["errors"].append(error)
            return False
        
        if "properties" not in input_schema:
            error = f"❌ Tool {tool_name}: Missing properties in input schema"
            print(error)
            self.test_results["errors"].append(error)
            return False
        
        print(f"✅ Tool {tool_name}: Schema valid")
        return True
    
    def check_field(self, actual: dict, expected: dict, field_path: str, description: str) -> bool:
        """Check if a nested field matches expected value."""
        try:
            actual_val = self.get_nested_field(actual, field_path)
            expected_val = self.get_nested_field(expected, field_path)
            
            if actual_val == expected_val:
                print(f"✅ {description}: PASS")
                return True
            else:
                error = f"❌ {description}: FAIL - Expected '{expected_val}', got '{actual_val}'"
                print(error)
                self.test_results["errors"].append(error)
                return False
                
        except Exception as e:
            error = f"❌ {description}: ERROR - {e}"
            print(error)
            self.test_results["errors"].append(error)
            return False
    
    def get_nested_field(self, data: dict, field_path: str):
        """Get nested field value using dot notation."""
        fields = field_path.split('.')
        current = data
        for field in fields:
            current = current[field]
        return current
    
    async def run_test(self) -> bool:
        """Run the tools discovery test."""
        print("🔧 Milestone 2: Tool Discovery & Validation")
        print("=" * 60)
        
        try:
            # Load test samples
            request_sample = await self.load_json_sample(REQUEST_FILE)
            expected_response = await self.load_json_sample(EXPECTED_RESPONSE_FILE)
            
            print(f"📋 Loaded request sample: {REQUEST_FILE.name}")
            print(f"📋 Loaded expected response: {EXPECTED_RESPONSE_FILE.name}")
            
            # Configure server connection
            server_params = StdioServerParameters(
                command=SERVER_COMMAND[0],
                args=SERVER_COMMAND[1:],
                env=None
            )
            
            print(f"🔧 Connecting to server: {' '.join(SERVER_COMMAND)}")
            
            # Test server tools discovery
            async with stdio_client(server_params) as (read, write):
                from mcp.client.session import ClientSession
                
                async with ClientSession(read, write) as session:
                    print("✅ Connected to MCP server")
                    
                    # Initialize session first
                    await session.initialize()
                    
                    # List tools
                    tools_result = await session.list_tools()
                    
                    # Convert result to JSON-RPC format for comparison
                    actual_response = {
                        "jsonrpc": "2.0",
                        "id": request_sample["id"],
                        "result": {
                            "tools": [tool.model_dump() for tool in tools_result.tools]
                        }
                    }
                    
                    print("\n🔍 Validating tools response...")
                    success = self.validate_tools_response(actual_response, expected_response)
                    
                    if success:
                        self.test_results["passed"] += 1
                        print(f"\n🎉 Milestone 2: PASSED")
                        return True
                    else:
                        self.test_results["failed"] += 1
                        print(f"\n❌ Milestone 2: FAILED")
                        return False
                        
        except Exception as e:
            error = f"Test execution failed: {e}"
            print(f"💥 {error}")
            self.test_results["errors"].append(error)
            self.test_results["failed"] += 1
            return False
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results["errors"]:
            print(f"\n🚨 Errors ({len(self.test_results['errors'])}):")
            for error in self.test_results["errors"]:
                print(f"  - {error}")

async def main():
    """Run tools discovery test."""
    test = ToolsDiscoveryTest()
    success = await test.run_test()
    test.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 
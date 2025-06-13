#!/usr/bin/env python3
"""
Milestone 1: Server Initialization & Capability Negotiation Test

Validates that the MCP server properly responds to initialization requests
and returns expected capabilities as defined in JSON-RPC samples.
"""
import asyncio
import json
import os
from pathlib import Path
from mcp.client.stdio import stdio_client, StdioServerParameters

# Test configuration
SCRIPT_DIR = Path(__file__).parent
REQUEST_FILE = SCRIPT_DIR / "request-initialize.json"
EXPECTED_RESPONSE_FILE = SCRIPT_DIR / "response-initialize.json"
SERVER_COMMAND = ["uv", "run", "python", "test_rag_server.py"]

class InitializationTest:
    """Test server initialization against JSON-RPC samples."""
    
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
    
    def validate_initialization_response(self, actual: dict, expected: dict) -> bool:
        """Validate initialization response against expected sample."""
        validations = []
        
        # Check JSON-RPC structure
        validations.append(
            self.check_field(actual, expected, "jsonrpc", "JSON-RPC version")
        )
        validations.append(
            self.check_field(actual, expected, "id", "Request ID")
        )
        
        # Check result structure
        if "result" in expected:
            validations.append(
                self.check_field(actual, expected, "result.protocolVersion", "Protocol version")
            )
            validations.append(
                self.check_field(actual, expected, "result.serverInfo.name", "Server name") 
            )
            validations.append(
                self.check_nested_field(actual, "result.capabilities.tools", "Tools capability")
            )
            validations.append(
                self.check_nested_field(actual, "result.capabilities.resources", "Resources capability")
            )
        
        return all(validations)
    
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
    
    def check_nested_field(self, actual: dict, field_path: str, description: str) -> bool:
        """Check if a nested field exists."""
        try:
            self.get_nested_field(actual, field_path)
            print(f"✅ {description}: EXISTS")
            return True
        except:
            error = f"❌ {description}: MISSING"
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
        """Run the initialization test."""
        print("🚀 Milestone 1: Server Initialization & Capability Negotiation")
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
            
            # Test server initialization
            async with stdio_client(server_params) as (read, write):
                from mcp.client.session import ClientSession
                
                async with ClientSession(read, write) as session:
                    print("✅ Connected to MCP server")
                    
                    # Send initialization request
                    result = await session.initialize()
                    
                    # Convert result to JSON-RPC format for comparison
                    actual_response = {
                        "jsonrpc": "2.0",
                        "id": request_sample["id"],
                        "result": {
                            "protocolVersion": result.protocolVersion,
                            "capabilities": result.capabilities.model_dump(),
                            "serverInfo": result.serverInfo.model_dump(),
                            "instructions": result.instructions
                        }
                    }
                    
                    print("\n🔍 Validating server response...")
                    success = self.validate_initialization_response(actual_response, expected_response)
                    
                    if success:
                        self.test_results["passed"] += 1
                        print(f"\n🎉 Milestone 1: PASSED")
                        return True
                    else:
                        self.test_results["failed"] += 1
                        print(f"\n❌ Milestone 1: FAILED")
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
    """Run initialization test."""
    test = InitializationTest()
    success = await test.run_test()
    test.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 
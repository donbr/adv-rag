#!/usr/bin/env python3
"""
Milestone 3: Semantic Search Tool Execution Test

Validates that the semantic_search tool executes correctly with sample inputs
and returns expected outputs as defined in JSON-RPC samples.
"""
import asyncio
import json
import os
from pathlib import Path
from mcp.client.stdio import stdio_client, StdioServerParameters

# Test configuration
SCRIPT_DIR = Path(__file__).parent
REQUEST_FILE = SCRIPT_DIR / "request.json"
EXPECTED_RESPONSE_FILE = SCRIPT_DIR / "response.json"
SERVER_COMMAND = ["uv", "run", "python", "-m", "src.mcp_server.main"]

class SemanticSearchTest:
    """Test semantic search tool execution against JSON-RPC samples."""
    
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
    
    def validate_tool_response(self, actual: dict, expected: dict) -> bool:
        """Validate tool response against expected sample."""
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
            # Check that result has content
            if "content" in actual["result"]:
                content = actual["result"]["content"]
                if len(content) > 0 and content[0].get("type") == "text":
                    print("✅ Response has text content")
                    validations.append(True)
                    
                    # Try to parse the text content as JSON (search results)
                    try:
                        text_content = content[0]["text"]
                        search_results = json.loads(text_content)
                        
                        if isinstance(search_results, list) and len(search_results) > 0:
                            print(f"✅ Search results: {len(search_results)} documents returned")
                            validations.append(True)
                            
                            # Check result structure
                            for i, result in enumerate(search_results):
                                if all(key in result for key in ["rank", "content", "metadata", "relevance_score"]):
                                    print(f"✅ Result {i+1}: Valid structure")
                                    validations.append(True)
                                else:
                                    error = f"❌ Result {i+1}: Missing required fields"
                                    print(error)
                                    self.test_results["errors"].append(error)
                                    validations.append(False)
                        else:
                            error = "❌ Search results: Empty or invalid format"
                            print(error)
                            self.test_results["errors"].append(error)
                            validations.append(False)
                            
                    except json.JSONDecodeError as e:
                        error = f"❌ Search results: Invalid JSON format - {e}"
                        print(error)
                        self.test_results["errors"].append(error)
                        validations.append(False)
                else:
                    error = "❌ Response: No text content found"
                    print(error)
                    self.test_results["errors"].append(error)
                    validations.append(False)
            else:
                error = "❌ Response: No content field found"
                print(error)
                self.test_results["errors"].append(error)
                validations.append(False)
            
            # Check isError field
            if "isError" in actual["result"]:
                if not actual["result"]["isError"]:
                    print("✅ Tool execution: No errors reported")
                    validations.append(True)
                else:
                    error = "❌ Tool execution: Error reported"
                    print(error)
                    self.test_results["errors"].append(error)
                    validations.append(False)
        
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
    
    def get_nested_field(self, data: dict, field_path: str):
        """Get nested field value using dot notation."""
        fields = field_path.split('.')
        current = data
        for field in fields:
            current = current[field]
        return current
    
    async def run_test(self) -> bool:
        """Run the semantic search tool test."""
        print("🔍 Milestone 3: Semantic Search Tool Execution")
        print("=" * 60)
        
        try:
            # Load test samples
            request_sample = await self.load_json_sample(REQUEST_FILE)
            expected_response = await self.load_json_sample(EXPECTED_RESPONSE_FILE)
            
            print(f"📋 Loaded request sample: {REQUEST_FILE.name}")
            print(f"📋 Loaded expected response: {EXPECTED_RESPONSE_FILE.name}")
            
            # Extract tool parameters from request
            tool_params = request_sample["params"]["arguments"]
            print(f"🔧 Tool parameters: {tool_params}")
            
            # Configure server connection
            server_params = StdioServerParameters(
                command=SERVER_COMMAND[0],
                args=SERVER_COMMAND[1:],
                env=None
            )
            
            print(f"🔧 Connecting to server: {' '.join(SERVER_COMMAND)}")
            
            # Test semantic search tool execution
            async with stdio_client(server_params) as (read, write):
                from mcp.client.session import ClientSession
                
                async with ClientSession(read, write) as session:
                    print("✅ Connected to MCP server")
                    
                    # Initialize session first
                    await session.initialize()
                    
                    # Execute semantic search tool
                    tool_result = await session.call_tool("semantic_search", tool_params)
                    
                    # Convert result to JSON-RPC format for comparison
                    actual_response = {
                        "jsonrpc": "2.0",
                        "id": request_sample["id"],
                        "result": {
                            "content": [{"type": "text", "text": content.text} for content in tool_result.content],
                            "isError": tool_result.isError
                        }
                    }
                    
                    print("\n🔍 Validating tool response...")
                    success = self.validate_tool_response(actual_response, expected_response)
                    
                    if success:
                        self.test_results["passed"] += 1
                        print(f"\n🎉 Milestone 3 (Semantic Search): PASSED")
                        return True
                    else:
                        self.test_results["failed"] += 1
                        print(f"\n❌ Milestone 3 (Semantic Search): FAILED")
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
    """Run semantic search tool test."""
    test = SemanticSearchTest()
    success = await test.run_test()
    test.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 
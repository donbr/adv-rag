#!/usr/bin/env python3
"""
MCP Tool Validation Script - Day 1 Testing
Tests all 8 FastAPI MCP tools with realistic queries per PRD requirements.
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Set required environment variables for testing
os.environ["OPENAI_API_KEY"] = "test-key-for-mcp-validation"
os.environ["COHERE_API_KEY"] = "test-cohere-key"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["PHOENIX_PROJECT_NAME"] = "mcp-validation-testing"

# Test queries for each tool type
TEST_QUERIES = {
    "naive_retriever": [
        "What makes a good action movie?",
        "How do characters develop in John Wick?", 
        "What are the key themes in action films?",
        "How does cinematography impact action sequences?",
        "What makes John Wick different from other action heroes?",
        "How do fight scenes contribute to storytelling?"
    ],
    "bm25_retriever": [
        "gunfight scenes choreography",
        "Keanu Reeves performance John Wick",
        "Continental Hotel rules assassins", 
        "motorcycle chase sequences",
        "pencil weapon improvised combat",
        "dog motivation revenge plot"
    ],
    "contextual_compression_retriever": [
        "What specific fighting techniques are shown in John Wick movies?",
        "How does the Continental Hotel function as a safe haven?",
        "What role does the High Table play in the assassin world?",
        "How are weapons and combat portrayed realistically?",
        "What makes the John Wick universe unique among action films?",
        "How do the movies balance action with character development?"
    ],
    "multi_query_retriever": [
        "John Wick character development throughout series",
        "Action movie cinematography and visual style",
        "Assassin world building and mythology",
        "Fight choreography and stunt work quality", 
        "Emotional themes in action genre films",
        "Sequel quality and story progression"
    ],
    "ensemble_retriever": [
        "What are the best action sequences in John Wick?",
        "How does John Wick compare to other action franchises?",
        "What makes the Continental Hotel scenes memorable?",
        "How effective is the world-building in these films?",
        "What role does music play in action sequences?",
        "How do the films handle violence and consequences?"
    ],
    "semantic_retriever": [
        "Themes of loss and redemption in action cinema",
        "Professional ethics in the assassin underworld",
        "Loyalty and betrayal in John Wick series",
        "The concept of honor among criminals",
        "How grief drives character motivation",
        "Justice versus revenge in action narratives"
    ]
}

# Health check queries (simpler)
HEALTH_QUERIES = [
    {},  # Basic health check
    {},  # Redundant check for reliability
]

CACHE_QUERIES = [
    {},  # Basic cache stats
    {},  # Second check
]

class MCPToolValidator:
    def __init__(self):
        self.results = {}
        self.errors = []
        
    async def test_tool(self, session: ClientSession, tool_name: str, queries: List[Any]) -> Dict[str, Any]:
        """Test a single MCP tool with multiple queries"""
        print(f"\n🔧 Testing {tool_name}...")
        tool_results = {
            "tool_name": tool_name,
            "total_queries": len(queries),
            "successful": 0,
            "failed": 0,
            "errors": [],
            "response_times": [],
            "sample_responses": []
        }
        
        for i, query in enumerate(queries, 1):
            try:
                print(f"  Query {i}/{len(queries)}: {str(query)[:50]}...")
                
                start_time = time.time()
                
                # Handle different query formats
                if tool_name in ["health_check_health_get", "cache_stats_cache_stats_get"]:
                    arguments = {}
                else:
                    arguments = {"question": query} if isinstance(query, str) else query
                
                result = await session.call_tool(tool_name, arguments)
                response_time = time.time() - start_time
                
                tool_results["successful"] += 1
                tool_results["response_times"].append(response_time)
                
                # Store first 2 responses as samples
                if len(tool_results["sample_responses"]) < 2:
                    tool_results["sample_responses"].append({
                        "query": query,
                        "response": str(result.content[0].text)[:200] + "..." if result.content else "No response"
                    })
                
                print(f"    ✅ SUCCESS ({response_time:.2f}s)")
                
            except Exception as e:
                tool_results["failed"] += 1
                tool_results["errors"].append(f"Query {i}: {str(e)}")
                print(f"    ❌ FAILED: {str(e)}")
        
        # Calculate stats
        if tool_results["response_times"]:
            tool_results["avg_response_time"] = sum(tool_results["response_times"]) / len(tool_results["response_times"])
            tool_results["max_response_time"] = max(tool_results["response_times"])
        
        return tool_results
    
    async def run_validation(self):
        """Run comprehensive validation of all MCP tools"""
        print("🚀 Starting MCP Tool Validation - Day 1 Testing")
        print("=" * 60)
        
        # Prepare environment variables for the server subprocess
        env = os.environ.copy()
        env.update({
            "OPENAI_API_KEY": "test-key-for-mcp-validation",
            "COHERE_API_KEY": "test-cohere-key",
            "QDRANT_URL": "http://localhost:6333",
            "REDIS_URL": "redis://localhost:6379",
            "PHOENIX_PROJECT_NAME": "mcp-validation-testing"
        })
        
        server_params = StdioServerParameters(
            command="python", 
            args=["-m", "src.mcp.server"],
            env=env  # Pass environment variables to subprocess
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test retrieval tools
                for tool_name, queries in TEST_QUERIES.items():
                    self.results[tool_name] = await self.test_tool(session, tool_name, queries)
                
                # Test health/cache tools
                self.results["health_check_health_get"] = await self.test_tool(
                    session, "health_check_health_get", HEALTH_QUERIES
                )
                self.results["cache_stats_cache_stats_get"] = await self.test_tool(
                    session, "cache_stats_cache_stats_get", CACHE_QUERIES
                )
        
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "=" * 60)
        print("📊 MCP TOOL VALIDATION REPORT - DAY 1")
        print("=" * 60)
        
        total_tools = len(self.results)
        total_queries = sum(r["total_queries"] for r in self.results.values())
        total_successful = sum(r["successful"] for r in self.results.values())
        total_failed = sum(r["failed"] for r in self.results.values())
        
        print(f"\n📈 OVERALL STATS:")
        print(f"  Tools Tested: {total_tools}/8")
        print(f"  Total Queries: {total_queries}")
        print(f"  Success Rate: {total_successful}/{total_queries} ({100*total_successful/total_queries:.1f}%)")
        print(f"  Failed Queries: {total_failed}")
        
        print(f"\n🔧 TOOL-BY-TOOL RESULTS:")
        for tool_name, results in self.results.items():
            status = "✅ PASS" if results["failed"] == 0 else f"⚠️  ISSUES ({results['failed']} failed)"
            avg_time = results.get("avg_response_time", 0)
            print(f"  {tool_name:35} | {status:15} | {results['successful']}/{results['total_queries']} queries | {avg_time:.2f}s avg")
            
            # Show errors if any
            if results["errors"]:
                for error in results["errors"][:2]:  # Show first 2 errors
                    print(f"    🔴 {error}")
        
        print(f"\n📝 SAMPLE RESPONSES (for documentation):")
        for tool_name, results in self.results.items():
            if results["sample_responses"]:
                print(f"\n  {tool_name}:")
                for sample in results["sample_responses"][:1]:  # Show 1 sample
                    print(f"    Query: {sample['query']}")
                    print(f"    Response: {sample['response']}")
        
        # Edge case testing summary
        print(f"\n🧪 EDGE CASE TESTING:")
        print(f"  - Invalid inputs: Will test in next phase")
        print(f"  - Timeout handling: Will test in next phase") 
        print(f"  - Empty queries: Will test in next phase")
        
        print(f"\n✅ Day 1 Testing Complete - Ready for Documentation Phase")

async def main():
    validator = MCPToolValidator()
    await validator.run_validation()

if __name__ == "__main__":
    asyncio.run(main()) 
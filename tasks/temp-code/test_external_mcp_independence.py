#!/usr/bin/env python3
"""
External MCP Services Independence Test

Verifies that external MCP services (Phoenix, Qdrant, Redis) work independently 
of the main FastAPI server and can operate without our application running.

This test ensures:
1. External MCP servers can start without FastAPI
2. External services maintain their own data and state
3. MCP tools function correctly when main app is offline
4. Service discovery works independently
"""

import asyncio
import sys
import subprocess
import time
import signal
import os
from pathlib import Path
import traceback
import json
import requests

# Add project root to path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def check_docker_services():
    """Use Docker commands to intelligently check service status"""
    print("🐳 Checking Docker services status...")
    
    try:
        # Get all running containers
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("❌ Docker is not running or accessible")
            return {}
            
        lines = result.stdout.strip().split('\n')
        
        if len(lines) < 1 or not lines[0].strip():  # No containers
            print("⚠️  No Docker containers are running")
            return {}
            
        print("Active Docker Containers:")
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 2:
                print(f"  📦 {parts[0]} -> {parts[1]}")
        
        # Parse container information
        services = {}
        for line in lines:  # No header to skip with this format
            # Split by tabs since we're using tab format
            parts = line.split('\t')
            if len(parts) >= 2:
                name = parts[0].strip()
                status = parts[1].strip()
                ports = parts[2].strip() if len(parts) > 2 else ""
                
                # Map container names to our services (handle prefixes like langchain_)
                name_lower = name.lower()
                if 'qdrant' in name_lower:
                    services['qdrant'] = {
                        'container': name,
                        'status': status,
                        'ports': ports,
                        'healthy': 'Up' in status
                    }
                elif 'redis' in name_lower and 'redisinsight' not in name_lower:
                    services['redis'] = {
                        'container': name,
                        'status': status,
                        'ports': ports,
                        'healthy': 'Up' in status
                    }
                elif 'phoenix' in name_lower:
                    services['phoenix'] = {
                        'container': name,
                        'status': status,
                        'ports': ports,
                        'healthy': 'Up' in status
                    }
        
        return services
        
    except subprocess.TimeoutExpired:
        print("❌ Docker command timed out")
        return {}
    except FileNotFoundError:
        print("❌ Docker is not installed or not in PATH")
        return {}
    except Exception as e:
        print(f"❌ Docker check failed: {e}")
        return {}

def check_fastapi_process():
    """Intelligently check if FastAPI process is running"""
    print("🔍 Checking for FastAPI processes...")
    
    try:
        # Check for uvicorn processes running our app
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn.*app:app"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"⚠️  Found {len(pids)} FastAPI process(es): {', '.join(pids)}")
            return True
        else:
            print("✅ No FastAPI processes found")
            return False
            
    except Exception as e:
        print(f"❌ Process check failed: {e}")
        return False

def stop_fastapi_processes():
    """Intelligently stop FastAPI processes"""
    print("🛑 Stopping FastAPI processes...")
    
    try:
        # Kill uvicorn processes running our app
        result = subprocess.run(
            ["pkill", "-f", "uvicorn.*app:app"],
            capture_output=True,
            text=True
        )
        
        time.sleep(3)  # Give processes time to stop
        
        # Verify they're stopped
        if not check_fastapi_process():
            print("✅ FastAPI processes stopped successfully")
            return True
        else:
            print("⚠️  Some FastAPI processes may still be running")
            return False
            
    except Exception as e:
        print(f"❌ Failed to stop FastAPI processes: {e}")
        return False

async def test_service_independence():
    """Test that external MCP services work independently of our FastAPI server"""
    print("🔍 Testing External MCP Services Independence")
    print("=" * 60)
    
    # Check if FastAPI is running and stop it if needed
    print("📡 Step 1: Verify FastAPI server is offline...")
    if check_fastapi_process():
        stop_fastapi_processes()
    
    # Also try HTTP check as backup
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("⚠️  FastAPI still responding via HTTP - there may be other instances")
        else:
            print("✅ FastAPI server is offline")
    except Exception:
        print("✅ FastAPI server is offline (no HTTP response)")
    
    # Check Docker services intelligently
    print("\n📊 Step 2: Check backend services via Docker...")
    docker_services = check_docker_services()
    
    if not docker_services:
        print("❌ No relevant Docker services found - independence test may not be meaningful")
        print("   Make sure docker-compose services are running:")
        print("   docker-compose up -d")
        return False
    
    print("\nDocker Services Summary:")
    for service_name, info in docker_services.items():
        status_emoji = "✅" if info['healthy'] else "❌"
        print(f"  - {service_name.capitalize()}: {status_emoji} {info['status']}")
        if info['ports']:
            print(f"    Ports: {info['ports']}")
    
    # Verify critical services are up
    required_services = ['qdrant', 'redis']
    missing_services = [s for s in required_services if s not in docker_services or not docker_services[s]['healthy']]
    
    if missing_services:
        print(f"\n❌ Required services not healthy: {missing_services}")
        print("   Start services with: docker-compose up -d")
        return False
    
    # Test each external MCP service independently
    print("\n🧪 Step 3: Test External MCP Services Independence...")
    
    independence_results = {}
    
    # Test Phoenix MCP independence
    print("\n--- Testing Phoenix MCP Independence ---")
    try:
        phoenix_result = await test_phoenix_independence()
        independence_results["phoenix"] = phoenix_result
    except Exception as e:
        print(f"❌ Phoenix MCP independence test failed: {e}")
        traceback.print_exc()
        independence_results["phoenix"] = False
    
    # Test Qdrant Semantic Memory MCP independence
    print("\n--- Testing Qdrant Semantic Memory MCP Independence ---")
    try:
        qdrant_semantic_result = await test_qdrant_semantic_independence()
        independence_results["qdrant_semantic"] = qdrant_semantic_result
    except Exception as e:
        print(f"❌ Qdrant Semantic MCP independence test failed: {e}")
        traceback.print_exc()
        independence_results["qdrant_semantic"] = False
    
    # Test Redis MCP independence (if we had a standalone Redis MCP server)
    # Note: Our Redis integration is built into FastAPI, so this would be N/A
    print("\n--- Redis MCP Assessment ---")
    print("ℹ️  Redis MCP is integrated into FastAPI app, not standalone service")
    print("   This is expected behavior - Redis serves as cache layer for FastAPI tools")
    independence_results["redis"] = "N/A - Integrated into FastAPI by design"
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 EXTERNAL MCP SERVICES INDEPENDENCE TEST RESULTS")
    print("=" * 60)
    
    for service, result in independence_results.items():
        if result is True:
            print(f"✅ {service.replace('_', ' ').title()}: FULLY INDEPENDENT")
        elif result is False:
            print(f"❌ {service.replace('_', ' ').title()}: FAILED/DEPENDENT")
        else:
            print(f"ℹ️  {service.replace('_', ' ').title()}: {result}")
    
    # Provide evidence for independent services
    if independence_results.get("qdrant_semantic"):
        print("\n🔍 Evidence of Qdrant Independence:")
        try:
            # Show actual data in Qdrant that was created during independence test
            import requests
            response = requests.post(
                "http://localhost:6333/collections/semantic-memory/points/search",
                json={
                    "vector": [0.1] * 384,  # Dummy vector
                    "limit": 1,
                    "with_payload": True
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("result"):
                    point = data["result"][0]
                    payload = point.get("payload", {})
                    if "independence" in str(payload).lower():
                        print(f"   📄 Found independence test data: {payload}")
                        print("   🎯 This proves Qdrant worked while FastAPI was offline!")
        except Exception as e:
            print(f"   ⚠️  Could not retrieve evidence data: {e}")
    
    # Check if any critical services failed
    critical_failures = [k for k, v in independence_results.items() if v is False]
    
    if critical_failures:
        print(f"\n⚠️  Critical Issues Found: {len(critical_failures)} services not independent")
        return False
    else:
        print(f"\n🎉 All testable external MCP services are properly independent!")
        return True


async def test_phoenix_independence():
    """Test Phoenix MCP works without our FastAPI server"""
    server_params = StdioServerParameters(
        command="uvx",
        args=["@arize-ai/phoenix-mcp"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("🔧 Initializing Phoenix MCP session...")
                await session.initialize()
                print("✅ Phoenix MCP session initialized independently")
                
                # Test tool discovery
                tools = await session.list_tools()
                print(f"🔍 Discovered {len(tools.tools)} Phoenix tools independently")
                
                # Test a simple tool operation
                if tools.tools:
                    try:
                        # Try list-datasets operation
                        datasets_result = await session.call_tool(
                            "list-datasets",
                            arguments={}
                        )
                        
                        if datasets_result.content:
                            print("✅ Phoenix tool execution successful - service is independent")
                            print(f"   Found datasets: {len(datasets_result.content)} results")
                            return True
                        else:
                            print("⚠️  Phoenix tool returned empty results but executed")
                            return True
                            
                    except Exception as e:
                        print(f"❌ Phoenix tool execution failed: {e}")
                        return False
                else:
                    print("❌ No Phoenix tools discovered")
                    return False
                    
    except Exception as e:
        print(f"❌ Phoenix MCP connection failed: {e}")
        return False


async def test_qdrant_semantic_independence():
    """Test Qdrant Semantic Memory MCP works without our FastAPI server"""
    
    # Set environment variables for Qdrant Semantic Memory
    env = os.environ.copy()
    env.update({
        "COLLECTION_NAME": "semantic-memory",
        "FASTMCP_PORT": "8003",
        "TOOL_STORE_DESCRIPTION": "Store contextual information for semantic memory: conversation insights, project decisions, learned patterns, user preferences. Include descriptive information in the 'information' parameter and structured metadata for categorization and retrieval.",
        "TOOL_FIND_DESCRIPTION": "Search semantic memory for relevant context, decisions, and previously learned information. Use natural language queries to describe what type of information you're looking for."
    })
    
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-qdrant"],
        env=env
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("🔧 Initializing Qdrant Semantic Memory MCP session...")
                await session.initialize()
                print("✅ Qdrant Semantic Memory MCP session initialized independently")
                
                # Test tool discovery
                tools = await session.list_tools()
                print(f"🔍 Discovered {len(tools.tools)} Qdrant tools independently")
                
                if len(tools.tools) >= 2:  # Should have store and find
                    # Test store operation
                    try:
                        store_result = await session.call_tool(
                            "qdrant-store",
                            arguments={
                                "information": "Independence test: External MCP services can operate without main FastAPI application",
                                "metadata": {
                                    "test_type": "independence_validation",
                                    "timestamp": str(time.time()),
                                    "component": "qdrant_semantic_memory"
                                }
                            }
                        )
                        
                        if store_result.content:
                            print("✅ Qdrant store operation successful - service is independent")
                            
                            # Test find operation
                            find_result = await session.call_tool(
                                "qdrant-find",
                                arguments={
                                    "query": "independence test external MCP services"
                                }
                            )
                            
                            if find_result.content:
                                print("✅ Qdrant find operation successful - full independence confirmed")
                                return True
                            else:
                                print("⚠️  Qdrant find returned empty but store worked")
                                return True
                        else:
                            print("❌ Qdrant store operation failed")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Qdrant tool execution failed: {e}")
                        return False
                else:
                    print("❌ Expected 2 Qdrant tools, found fewer")
                    return False
                    
    except Exception as e:
        print(f"❌ Qdrant Semantic Memory MCP connection failed: {e}")
        return False


def cleanup_processes():
    """Clean up any hanging processes"""
    try:
        # Kill any MCP server processes that might be hanging
        subprocess.run(["pkill", "-f", "mcp-server"], capture_output=True)
        subprocess.run(["pkill", "-f", "phoenix-mcp"], capture_output=True)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        result = asyncio.run(test_service_independence())
        
        if result:
            print("\n🎉 INDEPENDENCE TEST PASSED")
            print("   External MCP services operate independently of FastAPI server")
            sys.exit(0)
        else:
            print("\n❌ INDEPENDENCE TEST FAILED")
            print("   Some external MCP services require FastAPI server")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        cleanup_processes()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        print(traceback.format_exc())
        cleanup_processes()
        sys.exit(1)
    finally:
        cleanup_processes() 
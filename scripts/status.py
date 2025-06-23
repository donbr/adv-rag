#!/usr/bin/env python
"""
Application Tier Status Detection

Checks the current state of all application tiers and provides comprehensive status information.
"""

import os
import sys
import subprocess
import json
import socket
import psutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.settings import get_settings
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False


class Colors:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class TierStatus:
    """Check status of all application tiers"""
    
    def __init__(self):
        self.status = {
            "tier1_environment": {},
            "tier2_infrastructure": {},
            "tier3_application": {},
            "tier4_mcp_interface": {},
            "tier5_data": {},
            "timestamp": datetime.now().isoformat()
        }
    
    def check_all(self, verbose: bool = False) -> Dict:
        """Run all status checks"""
        print(f"{Colors.BOLD}🔍 Advanced RAG System Status Check{Colors.RESET}")
        print("=" * 60)
        
        self._check_tier1_environment()
        self._check_tier2_infrastructure()
        self._check_tier3_application()
        self._check_tier4_mcp_interface()
        self._check_tier5_data()
        
        self._print_summary(verbose)
        return self.status
    
    def _check_tier1_environment(self):
        """Check Tier 1: Environment & Dependencies"""
        print(f"\n{Colors.BLUE}Tier 1: Environment & Dependencies{Colors.RESET}")
        
        # Virtual environment
        venv_active = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        venv_path = os.environ.get('VIRTUAL_ENV', 'Not detected')
        
        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        python_ok = sys.version_info >= (3, 13)
        
        # Dependencies (check if uv is available)
        uv_available = True
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True)
            uv_available = result.returncode == 0
        except:
            uv_available = False
        
        # API Keys and Model Pinning Validation
        api_keys = {}
        model_pinning = {}
        if SETTINGS_AVAILABLE:
            try:
                settings = get_settings()
                api_keys = {
                    "OPENAI_API_KEY": bool(settings.openai_api_key),
                    "COHERE_API_KEY": bool(settings.cohere_api_key),
                }
                # Validate model pinning (IMMUTABLE requirement)
                model_pinning = {
                    "openai_model": settings.openai_model_name == "gpt-4.1-mini",
                    "embedding_model": settings.embedding_model_name == "text-embedding-3-small",
                    "expected_openai": "gpt-4.1-mini",
                    "actual_openai": settings.openai_model_name,
                    "expected_embedding": "text-embedding-3-small", 
                    "actual_embedding": settings.embedding_model_name
                }
            except:
                api_keys = {"error": "Could not load settings"}
                model_pinning = {"error": "Could not validate model pinning"}
        else:
            api_keys = {
                "OPENAI_API_KEY": bool(os.environ.get('OPENAI_API_KEY')),
                "COHERE_API_KEY": bool(os.environ.get('COHERE_API_KEY')),
            }
            model_pinning = {"error": "Settings module not available"}
        
        self.status["tier1_environment"] = {
            "virtual_env_active": venv_active,
            "virtual_env_path": venv_path,
            "python_version": python_version,
            "python_version_ok": python_ok,
            "uv_available": uv_available,
            "api_keys": api_keys,
            "model_pinning": model_pinning
        }
        
        # Print results
        status_icon = "✅" if venv_active else "❌"
        print(f"  {status_icon} Virtual Environment: {'Active' if venv_active else 'Not Active'}")
        if venv_active:
            print(f"     Path: {venv_path}")
        
        status_icon = "✅" if python_ok else "❌"
        print(f"  {status_icon} Python Version: {python_version} {'(OK)' if python_ok else '(Need >= 3.13)'}")
        
        status_icon = "✅" if uv_available else "❌"
        print(f"  {status_icon} Package Manager (uv): {'Available' if uv_available else 'Not Found'}")
        
        print(f"  🔑 API Keys:")
        for key, present in api_keys.items():
            if key != "error":
                status_icon = "✅" if present else "❌"
                print(f"     {status_icon} {key}: {'Configured' if present else 'Missing'}")
        
        print(f"  🔒 Model Pinning (IMMUTABLE):")
        if "error" not in model_pinning:
            for model_type in ["openai_model", "embedding_model"]:
                if model_type in model_pinning:
                    is_correct = model_pinning[model_type]
                    status_icon = "✅" if is_correct else "❌"
                    model_name = "OpenAI LLM" if model_type == "openai_model" else "Embedding"
                    print(f"     {status_icon} {model_name}: {'Correct' if is_correct else 'WRONG'}")
                    if not is_correct:
                        expected_key = f"expected_{'openai' if model_type == 'openai_model' else 'embedding'}"
                        actual_key = f"actual_{'openai' if model_type == 'openai_model' else 'embedding'}"
                        print(f"        Expected: {model_pinning.get(expected_key, 'unknown')}")
                        print(f"        Actual: {model_pinning.get(actual_key, 'unknown')}")
        else:
            print(f"     ❌ Could not validate model pinning")
    
    def _check_tier2_infrastructure(self):
        """Check Tier 2: Infrastructure Services"""
        print(f"\n{Colors.BLUE}Tier 2: Infrastructure Services{Colors.RESET}")
        
        services = {
            "qdrant": {"port": 6333, "health_endpoint": "/"},
            "phoenix": {"port": 6006, "health_endpoint": "/"},
            "redis": {"port": 6379, "health_endpoint": None},
            "redisinsight": {"port": 5540, "health_endpoint": "/"}
        }
        
        # Check Docker
        docker_running = self._check_docker_running()
        print(f"  {'✅' if docker_running else '❌'} Docker: {'Running' if docker_running else 'Not Running'}")
        
        # Check each service
        for service, config in services.items():
            status = self._check_service_health(service, config["port"], config["health_endpoint"])
            self.status["tier2_infrastructure"][service] = status
            
            status_icon = "✅" if status["healthy"] else "❌"
            print(f"  {status_icon} {service.capitalize()}: {status['status']}")
            if status.get("docker_status") and not status["healthy"]:
                print(f"     Docker: {status['docker_status']}")
    
    def _check_tier3_application(self):
        """Check Tier 3: Core RAG Application"""
        print(f"\n{Colors.BLUE}Tier 3: Core RAG Application{Colors.RESET}")
        
        # Check FastAPI server
        apps = {
            "fastapi": {"port": 8000, "process_pattern": ["run.py", "uvicorn", "src.api.app"]}
        }
        
        for app, config in apps.items():
            port_status = self._check_port(config["port"])
            # Check for our specific process first
            process_info = self._find_process_by_pattern(config["process_pattern"])
            
            # If we find our process, it's running regardless of port
            if process_info:
                status = {
                    "running": True,
                    "port": config["port"],
                    "port_in_use": port_status,
                    "process": process_info
                }
            else:
                # If port is in use but not by our process, check health endpoint
                if port_status:
                    # Try health check to see if it's our service
                    health_ok = self._check_fastapi_health(config["port"])
                    status = {
                        "running": health_ok,
                        "port": config["port"],
                        "port_in_use": True,
                        "process": None,
                        "health_check": health_ok
                    }
                else:
                    status = {
                        "running": False,
                        "port": config["port"],
                        "port_in_use": False,
                        "process": None
                    }
            
            self.status["tier3_application"][app] = status
            
            status_icon = "✅" if status["running"] else "❌"
            status_text = "Running" if status["running"] else "Not Running"
            
            print(f"  {status_icon} {app.replace('_', ' ').title()}: {status_text}")
            if process_info:
                print(f"     PID: {process_info['pid']}, Command: {' '.join(process_info['cmdline'][:3])}")
            elif status.get("health_check"):
                print(f"     Health check passed on port {config['port']}")
            elif port_status and not status["running"]:
                print(f"     Note: Port {config['port']} in use by different service")
    
    def _check_tier4_mcp_interface(self):
        """Check Tier 4: MCP Interface Layer"""
        print(f"\n{Colors.BLUE}Tier 4: MCP Interface Layer{Colors.RESET}")
        
        # Check MCP servers (no fixed ports - they run via stdio)
        mcp_apps = {
            "mcp_tools": {"port": None, "process_pattern": ["src/mcp/server.py"]},
            "mcp_resources": {"port": None, "process_pattern": ["src/mcp/resources.py"]}
        }
        
        for app, config in mcp_apps.items():
            process_info = self._find_process_by_pattern(config["process_pattern"])
            
            status = {
                "running": bool(process_info),
                "process": process_info
            }
            
            self.status["tier4_mcp_interface"][app] = status
            
            status_icon = "✅" if status["running"] else "❌"
            status_text = "Running" if status["running"] else "Not Running"
            
            print(f"  {status_icon} {app.replace('_', ' ').title()}: {status_text}")
            if process_info:
                print(f"     PID: {process_info['pid']}, Command: {' '.join(process_info['cmdline'][:3])}")
        
        # Note about setup
        if not any(self.status["tier4_mcp_interface"][app]["running"] for app in mcp_apps.keys()):
            print(f"     Note: See docs/SETUP.md for MCP server startup instructions")
    
    def _check_tier5_data(self):
        """Check Tier 5: Data & Validation"""
        print(f"\n{Colors.BLUE}Tier 5: Data & Validation{Colors.RESET}")
        
        # Check Qdrant collections
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:6333/collections"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                collections = data.get("result", {}).get("collections", [])
                
                johnwick_collections = [c for c in collections if "johnwick" in c.get("name", "")]
                
                self.status["tier5_data"]["collections"] = {
                    "total": len(collections),
                    "johnwick_collections": len(johnwick_collections),
                    "names": [c.get("name") for c in johnwick_collections]
                }
                
                status_icon = "✅" if johnwick_collections else "❌"
                print(f"  {status_icon} Qdrant Collections: {len(johnwick_collections)} John Wick collections")
                for name in self.status["tier5_data"]["collections"]["names"]:
                    print(f"     - {name}")
            else:
                self.status["tier5_data"]["collections"] = {"error": "Could not connect to Qdrant"}
                print(f"  ❌ Qdrant Collections: Could not connect")
        except Exception as e:
            self.status["tier5_data"]["collections"] = {"error": str(e)}
            print(f"  ❌ Qdrant Collections: Error - {str(e)}")
        
        # Note about data pipeline
        johnwick_collections = self.status["tier5_data"].get("collections", {}).get("johnwick_collections", 0)
        if not johnwick_collections:
            print(f"     Note: See docs/SETUP.md for data ingestion instructions")
    
    def _check_docker_running(self) -> bool:
        """Check if Docker is running"""
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _check_fastapi_health(self, port: int) -> bool:
        """Check if our FastAPI app is running on the port by testing health endpoint"""
        try:
            result = subprocess.run(
                ["curl", "-s", "-f", f"http://localhost:{port}/health"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Check if response contains our expected health response
                try:
                    import json
                    response = json.loads(result.stdout)
                    return response.get("status") == "healthy"
                except:
                    return False
            return False
        except:
            return False
    
    def _check_service_health(self, service: str, port: int, health_endpoint: Optional[str]) -> Dict:
        """Check health of a service"""
        # First check if port is open
        port_open = self._check_port(port)
        
        # Check Docker status
        docker_status = self._check_docker_service(service)
        
        # Try health endpoint if available
        health_ok = False
        if port_open and health_endpoint:
            try:
                if service == "redis":
                    # Special handling for Redis
                    result = subprocess.run(
                        ["redis-cli", "-p", str(port), "ping"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    health_ok = result.returncode == 0 and "PONG" in result.stdout
                else:
                    # HTTP health check
                    url = f"http://localhost:{port}{health_endpoint}"
                    result = subprocess.run(
                        ["curl", "-s", "-f", url],
                        capture_output=True,
                        timeout=2
                    )
                    health_ok = result.returncode == 0
            except:
                health_ok = False
        elif port_open and service == "redis":
            health_ok = True  # If Redis port is open, assume it's healthy
        
        return {
            "port_open": port_open,
            "healthy": health_ok,
            "docker_status": docker_status,
            "status": "Healthy" if health_ok else ("Port Open" if port_open else "Not Running")
        }
    
    def _check_docker_service(self, service: str) -> str:
        """Check Docker container status"""
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        container = json.loads(line)
                        if service in container.get("Service", "").lower():
                            return container.get("State", "unknown")
            return "not found"
        except:
            return "docker error"
    
    def _check_port(self, port: int) -> bool:
        """Check if a port is in use"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    
    def _find_process_on_port(self, port: int) -> Optional[Dict]:
        """Find process using a specific port"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                for conn in proc.net_connections():
                    if conn.laddr.port == port:
                        return {
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "cmdline": proc.info['cmdline'] or []
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def _find_process_by_pattern(self, patterns: List[str]) -> Optional[Dict]:
        """Find process by command line pattern"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(pattern in cmdline for pattern in patterns):
                    return {
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cmdline": proc.info['cmdline'] or []
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def _print_summary(self, verbose: bool):
        """Print status summary"""
        print(f"\n{Colors.BOLD}Summary{Colors.RESET}")
        print("=" * 60)
        
        # Tier 1 Summary
        api_keys_ok = all(v for k, v in self.status["tier1_environment"]["api_keys"].items() if k != "error")
        model_pinning_ok = True
        if "error" not in self.status["tier1_environment"]["model_pinning"]:
            model_pinning_ok = all(
                self.status["tier1_environment"]["model_pinning"].get(k, False) 
                for k in ["openai_model", "embedding_model"]
                if k in self.status["tier1_environment"]["model_pinning"]
            )
        
        tier1_ok = (
            self.status["tier1_environment"]["virtual_env_active"] and
            self.status["tier1_environment"]["python_version_ok"] and
            api_keys_ok and
            model_pinning_ok
        )
        
        # Tier 2 Summary
        tier2_services = ["qdrant", "phoenix", "redis"]
        tier2_ok = all(
            self.status["tier2_infrastructure"].get(s, {}).get("healthy", False)
            for s in tier2_services
        )
        
        # Tier 3 Summary
        fastapi_running = self.status["tier3_application"].get("fastapi", {}).get("running", False)
        
        # Tier 4 Summary
        mcp_apps = ["mcp_tools", "mcp_resources"]
        tier4_ok = any(
            self.status["tier4_mcp_interface"].get(app, {}).get("running", False)
            for app in mcp_apps
        )
        
        # Tier 5 Summary
        data_ok = self.status["tier5_data"].get("collections", {}).get("johnwick_collections", 0) > 0
        
        print(f"  Tier 1 (Environment): {'✅ Ready' if tier1_ok else '❌ Issues Found'}")
        print(f"  Tier 2 (Infrastructure): {'✅ All Services Running' if tier2_ok else '❌ Some Services Down'}")
        print(f"  Tier 3 (Application): {'✅ FastAPI Running' if fastapi_running else '❌ FastAPI Not Running'}")
        print(f"  Tier 4 (MCP Interface): {'✅ MCP Servers Available' if tier4_ok else '❌ No MCP Servers'}")
        print(f"  Tier 5 (Data): {'✅ Collections Loaded' if data_ok else '❌ No Data'}")
        
        # Overall status
        all_ok = tier1_ok and tier2_ok and fastapi_running and data_ok
        print(f"\n  Overall: {'✅ System Ready' if all_ok else '⚠️  Issues Detected'}")
        
        if not all_ok:
            print(f"\n{Colors.YELLOW}For setup instructions, see docs/SETUP.md{Colors.RESET}")
            if not tier4_ok:
                print(f"     Note: MCP servers are optional - see docs/SETUP.md Section 4 for MCP integration")
        
        if verbose:
            print(f"\n{Colors.BLUE}Full Status JSON:{Colors.RESET}")
            print(json.dumps(self.status, indent=2))


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check Advanced RAG system status")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()
    
    checker = TierStatus()
    status = checker.check_all(verbose=args.verbose)
    
    if args.json:
        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
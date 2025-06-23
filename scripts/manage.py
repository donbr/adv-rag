#!/usr/bin/env python
"""
Application Tier Management

Provides commands to manage all application tiers: start, stop, restart, and clean operations.
"""

import os
import sys
import subprocess
import signal
import time
import psutil
import argparse
from pathlib import Path
from typing import List, Optional, Dict
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.status import TierStatus, Colors


class TierManager:
    """Manage application tiers"""
    
    def __init__(self):
        self.project_root = project_root
        self.status_checker = TierStatus()
    
    def status(self, tier: Optional[int] = None) -> Dict:
        """Check status of all tiers or specific tier"""
        full_status = self.status_checker.check_all()
        
        if tier:
            tier_map = {
                1: "tier1_environment",
                3: "tier3_infrastructure", 
                4: "tier4_application"
            }
            if tier in tier_map:
                return {tier_map[tier]: full_status.get(tier_map[tier], {})}
        
        return full_status
    
    def start(self, tier: Optional[int] = None):
        """Start services for specified tier or all tiers"""
        print(f"{Colors.BOLD}🚀 Starting Advanced RAG System{Colors.RESET}")
        
        if tier is None:
            # Start all tiers in order
            self._start_tier3()
            time.sleep(5)  # Wait for infrastructure
            self._check_data()
            self._start_tier4()
        elif tier == 3:
            self._start_tier3()
        elif tier == 4:
            self._start_tier4()
        else:
            print(f"{Colors.RED}Invalid tier: {tier}{Colors.RESET}")
    
    def stop(self, tier: Optional[int] = None):
        """Stop services for specified tier or all tiers"""
        print(f"{Colors.BOLD}🛑 Stopping Advanced RAG System{Colors.RESET}")
        
        if tier is None:
            # Stop all tiers in reverse order
            self._stop_tier4()
            self._stop_tier3()
        elif tier == 3:
            self._stop_tier3()
        elif tier == 4:
            self._stop_tier4()
        else:
            print(f"{Colors.RED}Invalid tier: {tier}{Colors.RESET}")
    
    def restart(self, tier: Optional[int] = None):
        """Restart services for specified tier or all tiers"""
        print(f"{Colors.BOLD}🔄 Restarting Advanced RAG System{Colors.RESET}")
        self.stop(tier)
        time.sleep(2)
        self.start(tier)
    
    def clean(self):
        """Clean up orphaned processes and restart everything"""
        print(f"{Colors.BOLD}🧹 Cleaning up system{Colors.RESET}")
        
        # Kill orphaned processes
        self._kill_orphaned_processes()
        
        # Stop all services
        self.stop()
        
        # Clean Docker volumes if requested
        response = input("\nClean Docker volumes? (y/N): ")
        if response.lower() == 'y':
            print("Cleaning Docker volumes...")
            subprocess.run(
                ["docker-compose", "down", "-v"],
                cwd=self.project_root
            )
        
        print(f"\n{Colors.GREEN}System cleaned. Run 'python scripts/manage.py start' to restart.{Colors.RESET}")
    
    def _start_tier3(self):
        """Start Tier 3 infrastructure services"""
        print(f"\n{Colors.BLUE}Starting Tier 3: Infrastructure{Colors.RESET}")
        
        # Check if Docker is running
        try:
            subprocess.run(["docker", "info"], capture_output=True, check=True)
        except:
            print(f"{Colors.RED}Docker is not running. Please start Docker first.{Colors.RESET}")
            return
        
        # Start Docker services
        print("Starting Docker services...")
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=self.project_root
        )
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ Infrastructure services started{Colors.RESET}")
            
            # Wait for services to be ready
            print("Waiting for services to be ready...")
            time.sleep(5)
            
            # Check health
            services_healthy = self._check_services_health()
            if services_healthy:
                print(f"{Colors.GREEN}✅ All services healthy{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}⚠️  Some services may not be ready yet{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ Failed to start infrastructure{Colors.RESET}")
    
    def _start_tier4(self):
        """Start Tier 4 application servers"""
        print(f"\n{Colors.BLUE}Starting Tier 4: Application Servers{Colors.RESET}")
        
        # Check if virtual environment is active
        if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
            print(f"{Colors.RED}❌ Virtual environment not active!{Colors.RESET}")
            print("Please activate with: source .venv/bin/activate")
            return
        
        # Check if FastAPI is already running
        if self._check_port_in_use(8000):
            print(f"{Colors.YELLOW}FastAPI already running on port 8000{Colors.RESET}")
            response = input("Kill existing process and restart? (y/N): ")
            if response.lower() == 'y':
                self._kill_process_on_port(8000)
                time.sleep(1)
            else:
                print("Skipping FastAPI start")
                return
        
        # Start FastAPI server
        print("Starting FastAPI server...")
        fastapi_process = subprocess.Popen(
            [sys.executable, "run.py"],
            cwd=self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(3)  # Wait for startup
        
        if fastapi_process.poll() is None:
            print(f"{Colors.GREEN}✅ FastAPI server started (PID: {fastapi_process.pid}){Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ FastAPI server failed to start{Colors.RESET}")
            stderr = fastapi_process.stderr.read().decode() if fastapi_process.stderr else ""
            if stderr:
                print(f"Error: {stderr}")
        
        # Optionally start MCP servers
        response = input("\nStart MCP servers? (y/N): ")
        if response.lower() == 'y':
            self._start_mcp_servers()
    
    def _stop_tier3(self):
        """Stop Tier 3 infrastructure services"""
        print(f"\n{Colors.BLUE}Stopping Tier 3: Infrastructure{Colors.RESET}")
        
        result = subprocess.run(
            ["docker-compose", "stop"],
            cwd=self.project_root
        )
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ Infrastructure services stopped{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ Failed to stop infrastructure{Colors.RESET}")
    
    def _stop_tier4(self):
        """Stop Tier 4 application servers"""
        print(f"\n{Colors.BLUE}Stopping Tier 4: Application Servers{Colors.RESET}")
        
        # Stop processes by pattern
        patterns = [
            ("FastAPI", ["run.py", "uvicorn", "src.api.app"]),
            ("MCP Tools", ["src/mcp/server.py"]),
            ("MCP Resources", ["src/mcp/resources.py"])
        ]
        
        for name, pattern_list in patterns:
            processes = self._find_processes_by_pattern(pattern_list)
            if processes:
                print(f"Stopping {name}...")
                for proc in processes:
                    try:
                        psutil.Process(proc['pid']).terminate()
                        print(f"  Terminated PID {proc['pid']}")
                    except:
                        pass
        
        print(f"{Colors.GREEN}✅ Application servers stopped{Colors.RESET}")
    
    def _check_data(self):
        """Check if data is ingested"""
        print(f"\n{Colors.BLUE}Checking Data Status{Colors.RESET}")
        
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
                
                if not johnwick_collections:
                    print(f"{Colors.YELLOW}No data collections found{Colors.RESET}")
                    response = input("Run data ingestion? (y/N): ")
                    if response.lower() == 'y':
                        print("Running data ingestion...")
                        result = subprocess.run(
                            [sys.executable, "scripts/ingestion/csv_ingestion_pipeline.py"],
                            cwd=self.project_root
                        )
                        if result.returncode == 0:
                            print(f"{Colors.GREEN}✅ Data ingestion complete{Colors.RESET}")
                        else:
                            print(f"{Colors.RED}❌ Data ingestion failed{Colors.RESET}")
                else:
                    print(f"{Colors.GREEN}✅ Data collections found: {', '.join(c['name'] for c in johnwick_collections)}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Could not check data status: {e}{Colors.RESET}")
    
    def _check_services_health(self) -> bool:
        """Check if all infrastructure services are healthy"""
        services = [
            ("Qdrant", 6333, "http://localhost:6333/health"),
            ("Phoenix", 6006, "http://localhost:6006"),
            ("Redis", 6379, None)
        ]
        
        all_healthy = True
        for name, port, health_url in services:
            if self._check_port_in_use(port):
                print(f"  ✅ {name} is running on port {port}")
            else:
                print(f"  ❌ {name} is not running on port {port}")
                all_healthy = False
        
        return all_healthy
    
    def _check_port_in_use(self, port: int) -> bool:
        """Check if a port is in use"""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    
    def _kill_process_on_port(self, port: int):
        """Kill process using a specific port"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.connections():
                    if conn.laddr.port == port:
                        print(f"Killing process {proc.info['name']} (PID: {proc.info['pid']}) on port {port}")
                        proc.terminate()
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    def _find_processes_by_pattern(self, patterns: List[str]) -> List[Dict]:
        """Find processes matching command line patterns"""
        matching_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(pattern in cmdline for pattern in patterns):
                    matching_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': proc.info['cmdline']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return matching_processes
    
    def _kill_orphaned_processes(self):
        """Kill orphaned Python processes related to the project"""
        print("Looking for orphaned processes...")
        
        patterns = [
            ["run.py"],
            ["uvicorn", "src.api.app"],
            ["src/mcp/server.py"],
            ["src/mcp/resources.py"]
        ]
        
        killed_count = 0
        for pattern in patterns:
            processes = self._find_processes_by_pattern(pattern)
            for proc in processes:
                try:
                    print(f"  Killing orphaned process: PID {proc['pid']} - {' '.join(proc['cmdline'][:3])}")
                    psutil.Process(proc['pid']).terminate()
                    killed_count += 1
                except:
                    pass
        
        if killed_count > 0:
            print(f"  Killed {killed_count} orphaned processes")
        else:
            print("  No orphaned processes found")
    
    def _start_mcp_servers(self):
        """Start MCP servers"""
        print("\nStarting MCP servers...")
        
        # Start MCP Tools server
        mcp_tools_process = subprocess.Popen(
            [sys.executable, "src/mcp/server.py"],
            cwd=self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Start MCP Resources server
        mcp_resources_process = subprocess.Popen(
            [sys.executable, "src/mcp/resources.py"],
            cwd=self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(2)
        
        if mcp_tools_process.poll() is None:
            print(f"{Colors.GREEN}✅ MCP Tools server started (PID: {mcp_tools_process.pid}){Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ MCP Tools server failed to start{Colors.RESET}")
        
        if mcp_resources_process.poll() is None:
            print(f"{Colors.GREEN}✅ MCP Resources server started (PID: {mcp_resources_process.pid}){Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ MCP Resources server failed to start{Colors.RESET}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Manage Advanced RAG system tiers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/manage.py status              # Check all tiers
  python scripts/manage.py start               # Start all services
  python scripts/manage.py stop --tier 4       # Stop only application servers
  python scripts/manage.py restart             # Restart everything
  python scripts/manage.py clean               # Clean up and reset
        """
    )
    
    parser.add_argument(
        "command",
        choices=["status", "start", "stop", "restart", "clean"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--tier",
        type=int,
        choices=[1, 3, 4],
        help="Specific tier to manage (1=Environment, 3=Infrastructure, 4=Application)"
    )
    
    args = parser.parse_args()
    
    manager = TierManager()
    
    if args.command == "status":
        manager.status(args.tier)
    elif args.command == "start":
        manager.start(args.tier)
    elif args.command == "stop":
        manager.stop(args.tier)
    elif args.command == "restart":
        manager.restart(args.tier)
    elif args.command == "clean":
        manager.clean()


if __name__ == "__main__":
    main()
#!/usr/bin/env python
"""
Advanced RAG System Health Check

Purpose: Comprehensive validation of all system tiers using established logging patterns.
This replaces the bash script with proper Python logging integration.

Usage: python scripts/validation/system_health_check.py
Logs: Output goes to console and logs/app.log (existing logging infrastructure)
"""

import sys
import os
import subprocess
import requests
import json
import logging
from pathlib import Path
from datetime import datetime
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Use established logging pattern
from src.core.logging_config import setup_logging

# Initialize logging using established pattern
setup_logging()
logger = logging.getLogger("validation")


class HealthChecker:
    """System health checker using established logging patterns"""
    
    def __init__(self):
        self.total_tests = 10
        self.passed_tests = 0
        self.failed_tests = 0
        
    def run_command(self, command: list, description: str) -> bool:
        """Run a command and return success status"""
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=300
            )
            if result.returncode == 0:
                logger.info(f"✅ {description}: OK")
                return True
            else:
                logger.warning(f"❌ {description}: FAILED - {result.stderr.strip()}")
                return False
        except subprocess.TimeoutExpired:
            logger.warning(f"⚠️ {description}: TIMEOUT")
            return False
        except Exception as e:
            logger.warning(f"❌ {description}: ERROR - {str(e)}")
            return False
    
    def check_http_endpoint(self, url: str, description: str) -> bool:
        """Check HTTP endpoint health"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ {description}: OK")
                return True
            else:
                logger.warning(f"❌ {description}: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"❌ {description}: ERROR - {str(e)}")
            return False
    
    def log_result(self, test_name: str, passed: bool):
        """Log test result and update counters"""
        if passed:
            self.passed_tests += 1
            logger.info(f"✅ {test_name}: PASSED")
        else:
            self.failed_tests += 1
            logger.warning(f"❌ {test_name}: FAILED")
    
    def test_system_status(self) -> bool:
        """Test 1: System Status Check"""
        logger.info("1/10: System Status Check...")
        return self.run_command(
            ["python", "scripts/status.py", "--verbose"], 
            "System Status"
        )
    
    def test_api_endpoints(self) -> bool:
        """Test 2: API Endpoints Testing"""
        logger.info("2/10: API Endpoints Testing...")
        return self.run_command(
            ["bash", "tests/integration/test_api_endpoints.sh"], 
            "API Endpoints"
        )
    
    def test_mcp_tools(self) -> bool:
        """Test 3: MCP Tools Validation"""
        logger.info("3/10: MCP Tools Validation...")
        return self.run_command(
            ["python", "tests/integration/verify_mcp.py"], 
            "MCP Tools"
        )
    
    def test_cqrs_resources(self) -> bool:
        """Test 4: CQRS Resources Testing"""
        logger.info("4/10: CQRS Resources Testing...")
        return self.run_command(
            ["python", "tests/integration/test_cqrs_resources.py"], 
            "CQRS Resources"
        )
    
    def test_structure_validation(self) -> bool:
        """Test 5: Structure Validation"""
        logger.info("5/10: Structure Validation...")
        return self.run_command(
            ["python", "tests/integration/test_cqrs_structure_validation.py"], 
            "Structure Validation"
        )
    
    def test_performance_comparison(self) -> bool:
        """Test 6: Performance Comparison"""
        logger.info("6/10: Performance Comparison...")
        return self.run_command(
            ["python", "scripts/evaluation/retrieval_method_comparison.py"], 
            "Performance Comparison"
        )
    
    def test_infrastructure_health(self) -> bool:
        """Test 7: Infrastructure Health Checks"""
        logger.info("7/10: Infrastructure Health Checks...")
        
        qdrant_ok = self.check_http_endpoint("http://localhost:6333/", "Qdrant")
        fastapi_ok = self.check_http_endpoint("http://localhost:8000/health", "FastAPI")
        redis_ok = self.run_command(["redis-cli", "ping"], "Redis")
        
        all_ok = qdrant_ok and fastapi_ok and redis_ok
        return all_ok
    
    def test_collections_verification(self) -> bool:
        """Test 8: Collections Verification"""
        logger.info("8/10: Collections Verification...")
        return self.check_http_endpoint("http://localhost:6333/collections", "Collections")
    
    def test_architecture_benchmark(self) -> bool:
        """Test 9: Architecture Benchmark"""
        logger.info("9/10: Architecture Benchmark...")
        return self.run_command(
            ["python", "scripts/evaluation/semantic_architecture_benchmark.py"], 
            "Architecture Benchmark"
        )
    
    def test_phoenix_dashboard(self) -> bool:
        """Test 10: Phoenix Dashboard Check"""
        logger.info("10/10: Phoenix Dashboard Check...")
        return self.check_http_endpoint("http://localhost:6006", "Phoenix Dashboard")
    
    def run_all_tests(self):
        """Run all health checks and log summary"""
        logger.info("=== Advanced RAG System Health Check ===")
        logger.info(f"Timestamp: {datetime.now()}")
        
        # Run all tests
        tests = [
            ("System Status", self.test_system_status),
            ("API Endpoints", self.test_api_endpoints),
            ("MCP Tools", self.test_mcp_tools),
            ("CQRS Resources", self.test_cqrs_resources),
            ("Structure Validation", self.test_structure_validation),
            ("Performance Comparison", self.test_performance_comparison),
            ("Infrastructure Health", self.test_infrastructure_health),
            ("Collections Verification", self.test_collections_verification),
            ("Architecture Benchmark", self.test_architecture_benchmark),
            ("Phoenix Dashboard", self.test_phoenix_dashboard),
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                self.log_result(test_name, result)
            except Exception as e:
                logger.error(f"❌ {test_name}: EXCEPTION - {str(e)}")
                self.failed_tests += 1
        
        # Log summary
        success_rate = (self.passed_tests * 100) // self.total_tests
        logger.info("=== HEALTH CHECK SUMMARY ===")
        logger.info(f"Total Tests: {self.total_tests}")
        logger.info(f"✅ Passed: {self.passed_tests}")
        logger.info(f"❌ Failed: {self.failed_tests}")
        logger.info(f"Success Rate: {success_rate}%")
        
        if self.failed_tests == 0:
            logger.info("🎉 All systems operational!")
        else:
            logger.warning("⚠️ Some tests failed. Check logs for details.")
        
        logger.info("=== VALIDATION COMPLETE ===")
        logger.info("Results logged to console and logs/app.log")
        
        # Return appropriate exit code
        return self.failed_tests == 0


def main():
    """Main entry point"""
    checker = HealthChecker()
    success = checker.run_all_tests()
    
    # Exit with appropriate code for CI/CD
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
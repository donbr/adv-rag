#!/usr/bin/env python3
"""
Test script to verify all imports work correctly after Redis MCP integration fixes
"""

import sys
import traceback

def test_import(module_name, description):
    """Test importing a module and report results"""
    try:
        __import__(module_name)
        print(f"✅ {description}: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ {description}: FAILED - {e}")
        traceback.print_exc()
        return False

def main():
    """Test all critical imports"""
    print("🧪 Testing Critical Imports After Redis MCP Integration")
    print("=" * 60)
    
    tests = [
        ("pydantic_settings", "Pydantic Settings (BaseSettings)"),
        ("redis.asyncio", "Redis Async Client"),
        ("langchain_redis", "LangChain Redis Integration"),
        ("src.settings", "Application Settings"),
        ("src.redis_client", "Redis Client Module"),
        ("src.llm_models", "LLM Models Module"),
        ("src.main_api", "FastAPI Main Application"),
    ]
    
    results = []
    for module, description in tests:
        results.append(test_import(module, description))
    
    print("\n" + "=" * 60)
    print("📊 IMPORT TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 ALL IMPORTS SUCCESSFUL! Application should start correctly.")
        
        # Test settings instantiation
        try:
            from src.settings import get_settings
            settings = get_settings()
            print(f"✅ Settings loaded: Redis URL = {settings.redis_url}")
        except Exception as e:
            print(f"⚠️ Settings instantiation failed: {e}")
            
    else:
        print("⚠️ Some imports failed. Please install missing dependencies:")
        print("   uv sync  # or pip install -e .")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
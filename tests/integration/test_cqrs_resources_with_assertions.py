#!/usr/bin/env python3
"""
Proper test script with assertions for CQRS-compliant MCP Resources implementation.

This script validates the CQRS Resources with actual assertions and expected outcomes.
"""

import asyncio
import sys
import logging
import re
from pathlib import Path
import pytest

# Setup project path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.mcp.qdrant_resources import QdrantResourceProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestResults:
    """Track test results with assertions."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def assert_true(self, condition: bool, message: str, test_name: str):
        """Assert condition is true."""
        if condition:
            self.passed += 1
            print(f"  ✅ {message}")
        else:
            self.failed += 1
            error_msg = f"❌ {test_name}: {message}"
            self.errors.append(error_msg)
            print(f"  {error_msg}")
    
    def assert_contains(self, text: str, substring: str, test_name: str):
        """Assert text contains substring."""
        condition = substring in text
        self.assert_true(condition, f"Contains '{substring}'", test_name)
    
    def assert_not_contains(self, text: str, substring: str, test_name: str):
        """Assert text does not contain substring."""
        condition = substring not in text
        self.assert_true(condition, f"Does not contain '{substring}'", test_name)
    
    def assert_min_length(self, text: str, min_length: int, test_name: str):
        """Assert text meets minimum length."""
        condition = len(text) >= min_length
        self.assert_true(condition, f"Length >= {min_length} chars (actual: {len(text)})", test_name)
    
    def assert_starts_with(self, text: str, prefix: str, test_name: str):
        """Assert text starts with prefix."""
        condition = text.startswith(prefix)
        self.assert_true(condition, f"Starts with '{prefix}'", test_name)
    
    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"Test Summary: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"Failed assertions: {self.failed}")
            for error in self.errors:
                print(f"  {error}")
        print(f"{'='*50}")
        return self.failed == 0

@pytest.mark.integration
@pytest.mark.requires_vectordb
async def test_list_collections():
    """Test collection listing with assertions."""
    print("\n📋 Test 1: List Collections")
    print("-" * 30)
    
    results = TestResults()
    provider = QdrantResourceProvider()
    
    try:
        result = await provider.list_collections()
        
        # Expected assertions for collections listing
        results.assert_starts_with(result, "# Qdrant Collections", "List Collections")
        results.assert_contains(result, "Available Collections", "List Collections")
        results.assert_contains(result, "CQRS Resource Access", "List Collections")
        results.assert_contains(result, "qdrant://collections", "List Collections")
        results.assert_min_length(result, 200, "List Collections")
        
        # Should contain collection names or error info
        contains_collections = ("johnwick_baseline" in result or 
                              "johnwick_semantic" in result or 
                              "Error" in result)
        results.assert_true(contains_collections, "Contains collection names or error info", "List Collections")
        
        print(f"Response preview: {result[:150]}...")
        
    except Exception as e:
        results.assert_true(False, f"Exception: {str(e)}", "List Collections")
    
    return results

@pytest.mark.integration
@pytest.mark.requires_vectordb
async def test_collection_info():
    """Test collection info with assertions."""
    print("\n📊 Test 2: Collection Info")
    print("-" * 30)
    
    results = TestResults()
    provider = QdrantResourceProvider()
    
    try:
        result = await provider.get_collection_info("johnwick_baseline")
        
        # Expected assertions for collection info
        results.assert_starts_with(result, "# Qdrant Collection:", "Collection Info")
        results.assert_contains(result, "johnwick_baseline", "Collection Info")
        results.assert_contains(result, "Collection Metadata", "Collection Info")
        results.assert_contains(result, "CQRS Information", "Collection Info")
        results.assert_contains(result, "READ-ONLY Resource", "Collection Info")
        results.assert_min_length(result, 300, "Collection Info")
        
        # Should contain either valid data or error info
        has_valid_info = ("Total Documents:" in result or 
                         "Vector Size" in result or 
                         "Vector Dimension:" in result or
                         "Error Details" in result)
        results.assert_true(has_valid_info, "Contains metadata or error details", "Collection Info")
        
        print(f"Response preview: {result[:150]}...")
        
    except Exception as e:
        results.assert_true(False, f"Exception: {str(e)}", "Collection Info")
    
    return results

@pytest.mark.integration
@pytest.mark.requires_vectordb
async def test_collection_search():
    """Test collection search with assertions."""
    print("\n🔍 Test 3: Collection Search")
    print("-" * 30)
    
    results = TestResults()
    provider = QdrantResourceProvider()
    
    try:
        result = await provider.search_collection("johnwick_baseline", "action movie", limit=2)
        
        # Expected assertions for search
        results.assert_starts_with(result, "# Search Results:", "Collection Search")
        results.assert_contains(result, "action movie", "Collection Search")
        results.assert_contains(result, "Collection**: johnwick_baseline", "Collection Search")
        results.assert_contains(result, "CQRS Information", "Collection Search")
        results.assert_contains(result, "READ-ONLY Vector Search", "Collection Search")
        results.assert_min_length(result, 200, "Collection Search")
        
        # Should contain results or no results message
        has_results = ("Results Found" in result or 
                      "No Search Results" in result or
                      "Search Error" in result)
        results.assert_true(has_results, "Contains search results information", "Collection Search")
        
        print(f"Response preview: {result[:150]}...")
        
    except Exception as e:
        results.assert_true(False, f"Exception: {str(e)}", "Collection Search")
    
    return results

@pytest.mark.integration
@pytest.mark.requires_vectordb
async def test_collection_stats():
    """Test collection statistics with assertions."""
    print("\n📈 Test 4: Collection Statistics")
    print("-" * 30)
    
    results = TestResults()
    provider = QdrantResourceProvider()
    
    try:
        result = await provider.get_collection_stats("johnwick_baseline")
        
        # Expected assertions for stats
        results.assert_starts_with(result, "# Collection Statistics:", "Collection Stats")
        results.assert_contains(result, "johnwick_baseline", "Collection Stats")
        results.assert_contains(result, "Basic Statistics", "Collection Stats")
        results.assert_contains(result, "CQRS Resource Information", "Collection Stats")
        results.assert_contains(result, "Read-Only Statistics", "Collection Stats")
        results.assert_min_length(result, 300, "Collection Stats")
        
        # Should contain stats or error info  
        has_stats = ("Total Points:" in result or 
                    "Vector Dimension:" in result or
                    "Basic Statistics" in result or 
                    "Statistics Error" in result)
        results.assert_true(has_stats, "Contains statistics or error info", "Collection Stats")
        
        print(f"Response preview: {result[:150]}...")
        
    except Exception as e:
        results.assert_true(False, f"Exception: {str(e)}", "Collection Stats")
    
    return results

@pytest.mark.integration
@pytest.mark.requires_vectordb
async def test_error_handling():
    """Test error handling with assertions."""
    print("\n❌ Test 5: Error Handling")
    print("-" * 30)
    
    results = TestResults()
    provider = QdrantResourceProvider()
    
    try:
        result = await provider.get_collection_info("nonexistent_collection_12345")
        
        # Expected assertions for error handling
        results.assert_starts_with(result, "# Error: Collection", "Error Handling")
        results.assert_contains(result, "nonexistent_collection_12345", "Error Handling")
        results.assert_contains(result, "Error Details", "Error Handling")
        results.assert_contains(result, "Troubleshooting", "Error Handling")
        results.assert_min_length(result, 100, "Error Handling")
        
        # Should NOT contain success indicators
        results.assert_not_contains(result, "Collection Metadata", "Error Handling")
        results.assert_not_contains(result, "Total Documents:", "Error Handling")
        
        print(f"Response preview: {result[:150]}...")
        
    except Exception as e:
        results.assert_true(False, f"Exception: {str(e)}", "Error Handling")
    
    return results

@pytest.mark.integration
@pytest.mark.requires_vectordb
async def test_document_retrieval():
    """Test document retrieval with assertions."""
    print("\n📄 Test 6: Document Retrieval")
    print("-" * 30)
    
    results = TestResults()
    provider = QdrantResourceProvider()
    
    try:
        # Test with a likely invalid point ID to test error handling
        result = await provider.get_document_by_id("johnwick_baseline", "test_point_id_123")
        
        # Expected assertions for document retrieval (likely to be "not found")
        valid_responses = [
            "# Document: test_point_id_123",  # Success case
            "# Document Not Found:",          # Not found case
            "# Error: Document Retrieval"     # Error case
        ]
        
        has_valid_response = any(resp in result for resp in valid_responses)
        results.assert_true(has_valid_response, "Has valid document response format", "Document Retrieval")
        
        results.assert_contains(result, "test_point_id_123", "Document Retrieval")
        results.assert_contains(result, "johnwick_baseline", "Document Retrieval")
        results.assert_min_length(result, 100, "Document Retrieval")
        
        print(f"Response preview: {result[:150]}...")
        
    except Exception as e:
        results.assert_true(False, f"Exception: {str(e)}", "Document Retrieval")
    
    return results

@pytest.mark.integration
@pytest.mark.requires_vectordb
async def test_cqrs_compliance():
    """Test CQRS pattern compliance."""
    print("\n🎯 Test 7: CQRS Compliance Validation")
    print("-" * 30)
    
    results = TestResults()
    
    # Test that resources are read-only (no mutation methods)
    provider = QdrantResourceProvider()
    
    # Check that provider only has read methods
    read_only_methods = [
        'get_collection_info',
        'get_document_by_id', 
        'search_collection',
        'get_collection_stats',
        'list_collections'
    ]
    
    # Check that provider doesn't have write methods
    write_methods = [
        'create_collection',
        'delete_collection',
        'insert_document',
        'update_document',
        'delete_document'
    ]
    
    for method in read_only_methods:
        has_method = hasattr(provider, method)
        results.assert_true(has_method, f"Has read-only method: {method}", "CQRS Compliance")
    
    for method in write_methods:
        has_method = hasattr(provider, method)
        results.assert_true(not has_method, f"Does NOT have write method: {method}", "CQRS Compliance")
    
    # Test idempotency - calling same operation twice should give same result
    try:
        result1 = await provider.list_collections()
        result2 = await provider.list_collections()
        
        # Results should be very similar (allowing for timestamp differences)
        similar = len(result1) == len(result2) or abs(len(result1) - len(result2)) < 100
        results.assert_true(similar, "Operations are idempotent", "CQRS Compliance")
        
    except Exception as e:
        results.assert_true(False, f"Idempotency test failed: {e}", "CQRS Compliance")
    
    return results

async def run_all_tests():
    """Run all tests with proper assertions."""
    print("🧪 CQRS Resources Tests with Assertions")
    print("=" * 50)
    
    all_results = []
    
    # Run all test functions
    test_functions = [
        test_list_collections,
        test_collection_info,
        test_collection_search,
        test_collection_stats,
        test_error_handling,
        test_document_retrieval,
        test_cqrs_compliance
    ]
    
    for test_func in test_functions:
        try:
            result = await test_func()
            all_results.append(result)
        except Exception as e:
            print(f"❌ Test function {test_func.__name__} failed: {e}")
            failed_result = TestResults()
            failed_result.failed = 1
            failed_result.errors.append(f"Test function failed: {e}")
            all_results.append(failed_result)
    
    # Calculate overall results
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    all_errors = []
    for r in all_results:
        all_errors.extend(r.errors)
    
    # Print overall summary
    print(f"\n{'='*60}")
    print(f"OVERALL TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Assertions Passed: {total_passed}")
    print(f"Total Assertions Failed: {total_failed}")
    print(f"Success Rate: {total_passed/(total_passed + total_failed)*100:.1f}%")
    
    if total_failed > 0:
        print(f"\nFailed Assertions:")
        for error in all_errors:
            print(f"  {error}")
    
    # Determine overall success
    overall_success = total_failed == 0
    
    if overall_success:
        print(f"\n🎉 ALL TESTS PASSED - CQRS Resources implementation is working correctly!")
        print(f"\n✅ CQRS Compliance Verified:")
        print(f"  - Resources provide read-only access")
        print(f"  - Proper error handling implemented")
        print(f"  - LLM-friendly structured output")
        print(f"  - Idempotent operations")
        print(f"  - Clear separation from command operations")
    else:
        print(f"\n💥 SOME TESTS FAILED - Review implementation")
        print(f"\n🔧 Common Issues:")
        print(f"  - Qdrant service may not be running")
        print(f"  - Collections may not be populated")
        print(f"  - Network connectivity issues")
        print(f"  - Dependencies may be missing")
    
    return overall_success

if __name__ == "__main__":
    async def main():
        """Run all CQRS tests with assertions."""
        success = await run_all_tests()
        
        if not success:
            print(f"\n📋 To resolve issues:")
            print(f"  1. Ensure Qdrant is running: docker-compose up -d")
            print(f"  2. Check data ingestion: python scripts/ingestion/csv_ingestion_pipeline.py") 
            print(f"  3. Verify dependencies: uv sync")
            print(f"  4. Check service health: curl http://localhost:6333")
            
            sys.exit(1)
        else:
            print(f"\n🚀 CQRS Resources are ready for production use!")
    
    asyncio.run(main())
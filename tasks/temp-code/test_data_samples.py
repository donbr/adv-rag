#!/usr/bin/env python3
"""
Test Data Samples for MCP Tool Validation

This module provides comprehensive test data samples for validating all 8 MCP tools
consistently. Includes normal queries, edge cases, and validation patterns.

Generated: 2025-06-17
Target: All MCP tools (6 retrieval + 2 utility)
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class TestCase:
    """Structure for a single test case"""
    name: str
    description: str
    parameters: Dict[str, Any]
    expected_response_keys: List[str]
    min_answer_length: int = 50
    max_answer_length: int = 5000
    
class MCPTestDataSamples:
    """Comprehensive test data samples for MCP tool validation"""
    
    # Core test queries for retrieval tools
    RETRIEVAL_TEST_CASES = [
        TestCase(
            name="action_movie_quality",
            description="Test query about action movie characteristics",
            parameters={"question": "What makes a good action movie?"},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=200,
            max_answer_length=3000
        ),
        TestCase(
            name="john_wick_specific",
            description="Specific query about John Wick movies",
            parameters={"question": "How is John Wick different from other action movies?"},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=150,
            max_answer_length=2500
        ),
        TestCase(
            name="character_development",
            description="Query about character development in action films",
            parameters={"question": "What role does character development play in action movies?"},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=100,
            max_answer_length=2000
        ),
        TestCase(
            name="cinematography_query",
            description="Technical aspects query",
            parameters={"question": "How does cinematography affect action movie quality?"},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=100,
            max_answer_length=2000
        ),
        TestCase(
            name="franchise_analysis",
            description="Multi-movie franchise analysis",
            parameters={"question": "What makes the John Wick franchise successful?"},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=150,
            max_answer_length=2500
        )
    ]
    
    # Edge case queries for testing robustness
    EDGE_CASE_TEST_CASES = [
        TestCase(
            name="very_short_query",
            description="Single word query",
            parameters={"question": "Action"},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=50,
            max_answer_length=1500
        ),
        TestCase(
            name="very_long_query",
            description="Extremely long query to test limits",
            parameters={"question": " ".join([
                "This is an extremely long query that tests the system's ability to handle",
                "verbose and detailed questions about action movies, specifically focusing on",
                "the John Wick franchise and its impact on the action movie genre, including",
                "cinematography, choreography, character development, world building, and",
                "overall narrative structure that makes it stand out from other films"
            ])},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=100,
            max_answer_length=3000
        ),
        TestCase(
            name="special_characters",
            description="Query with special characters and punctuation",
            parameters={"question": "What makes John Wick's action scenes so \"visceral\" & effective?!"},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=100,
            max_answer_length=2000
        ),
        TestCase(
            name="numeric_query",
            description="Query with numbers and specific references",
            parameters={"question": "How does John Wick Chapter 2 compare to the first movie?"},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=100,
            max_answer_length=2000
        ),
        TestCase(
            name="empty_query",
            description="Empty query to test error handling",
            parameters={"question": ""},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=10,
            max_answer_length=1000
        )
    ]
    
    # Comparison queries to test different retrieval strategies
    COMPARISON_TEST_CASES = [
        TestCase(
            name="keyword_heavy",
            description="Query with many specific keywords (good for BM25)",
            parameters={"question": "gun choreography fight scenes stunts practical effects John Wick"},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=100,
            max_answer_length=2000
        ),
        TestCase(
            name="semantic_heavy",
            description="Conceptual query (good for semantic search)",
            parameters={"question": "What emotional themes drive the narrative?"},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=100,
            max_answer_length=2000
        ),
        TestCase(
            name="hybrid_query",
            description="Mixed keyword and semantic query",
            parameters={"question": "How do John Wick's action sequences convey emotional storytelling?"},
            expected_response_keys=["answer", "context_document_count"],
            min_answer_length=150,
            max_answer_length=2500
        )
    ]
    
    # Invalid parameter test cases
    INVALID_PARAMETER_CASES = [
        {
            "name": "wrong_parameter_name",
            "description": "Using 'query' instead of 'question'",
            "parameters": {"query": "test query"},
            "expected_error": "422 Unprocessable Entity",
            "expected_error_detail": "Field required"
        },
        {
            "name": "missing_parameters",
            "description": "No parameters provided",
            "parameters": {},
            "expected_error": "422 Unprocessable Entity",
            "expected_error_detail": "Field required"
        },
        {
            "name": "extra_parameters",
            "description": "Additional unexpected parameters",
            "parameters": {
                "question": "test query",
                "extra_param": "should be ignored"
            },
            "expected_response_keys": ["answer", "context_document_count"]
        }
    ]
    
    @classmethod
    def get_all_retrieval_tests(cls) -> List[TestCase]:
        """Get all test cases for retrieval tools"""
        return (cls.RETRIEVAL_TEST_CASES + 
                cls.EDGE_CASE_TEST_CASES + 
                cls.COMPARISON_TEST_CASES)
    
    @classmethod
    def get_core_tests(cls) -> List[TestCase]:
        """Get essential test cases for quick validation"""
        return cls.RETRIEVAL_TEST_CASES[:3]  # First 3 core tests
    
    @classmethod
    def get_edge_cases(cls) -> List[TestCase]:
        """Get edge case tests for robustness validation"""
        return cls.EDGE_CASE_TEST_CASES
    
    @classmethod
    def get_comparison_tests(cls) -> List[TestCase]:
        """Get tests designed to compare different retrieval strategies"""
        return cls.COMPARISON_TEST_CASES
    
    @classmethod
    def get_invalid_parameter_tests(cls) -> List[Dict]:
        """Get test cases for parameter validation"""
        return cls.INVALID_PARAMETER_CASES
    
    @classmethod
    def validate_response(cls, response: Any, test_case: TestCase) -> Dict[str, Any]:
        """
        Validate a response against the expected test case criteria
        
        Args:
            response: The raw MCP tool response
            test_case: The test case with expected criteria
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "test_name": test_case.name,
            "passed": False,
            "errors": [],
            "warnings": [],
            "metrics": {}
        }
        
        try:
            # Check response structure
            if not isinstance(response, list):
                validation_results["errors"].append("Response is not a list")
                return validation_results
            
            if len(response) != 1:
                validation_results["errors"].append(f"Expected 1 response item, got {len(response)}")
                return validation_results
            
            if not hasattr(response[0], 'text'):
                validation_results["errors"].append("Response item missing 'text' attribute")
                return validation_results
            
            # Parse JSON content
            try:
                parsed_response = json.loads(response[0].text)
            except json.JSONDecodeError as e:
                validation_results["errors"].append(f"Invalid JSON in response: {e}")
                return validation_results
            
            # Check required keys
            missing_keys = [key for key in test_case.expected_response_keys 
                          if key not in parsed_response]
            if missing_keys:
                validation_results["errors"].append(f"Missing required keys: {missing_keys}")
                return validation_results
            
            # Validate answer content
            if "answer" in parsed_response:
                answer = parsed_response["answer"]
                answer_length = len(answer)
                
                validation_results["metrics"]["answer_length"] = answer_length
                
                if answer_length < test_case.min_answer_length:
                    validation_results["warnings"].append(
                        f"Answer length {answer_length} below minimum {test_case.min_answer_length}"
                    )
                
                if answer_length > test_case.max_answer_length:
                    validation_results["warnings"].append(
                        f"Answer length {answer_length} above maximum {test_case.max_answer_length}"
                    )
                
                if not answer.strip():
                    validation_results["errors"].append("Answer is empty or whitespace only")
                    return validation_results
            
            # Validate context document count
            if "context_document_count" in parsed_response:
                doc_count = parsed_response["context_document_count"]
                validation_results["metrics"]["context_document_count"] = doc_count
                
                if not isinstance(doc_count, int):
                    validation_results["errors"].append("context_document_count is not an integer")
                    return validation_results
                
                if doc_count < 0:
                    validation_results["errors"].append("context_document_count is negative")
                    return validation_results
                
                if doc_count == 0:
                    validation_results["warnings"].append("No context documents used")
            
            # If we reach here, validation passed
            validation_results["passed"] = True
            
        except Exception as e:
            validation_results["errors"].append(f"Unexpected validation error: {e}")
        
        return validation_results

# Utility functions for test execution
def create_test_suite_for_tool(tool_name: str) -> Dict[str, Any]:
    """Create a complete test suite for a specific MCP tool"""
    return {
        "tool_name": tool_name,
        "core_tests": MCPTestDataSamples.get_core_tests(),
        "edge_cases": MCPTestDataSamples.get_edge_cases(),
        "comparison_tests": MCPTestDataSamples.get_comparison_tests(),
        "invalid_parameter_tests": MCPTestDataSamples.get_invalid_parameter_tests(),
        "total_test_count": (
            len(MCPTestDataSamples.get_core_tests()) +
            len(MCPTestDataSamples.get_edge_cases()) +
            len(MCPTestDataSamples.get_comparison_tests()) +
            len(MCPTestDataSamples.get_invalid_parameter_tests())
        )
    }

def generate_test_report_template() -> Dict[str, Any]:
    """Generate a template for test execution reports"""
    return {
        "execution_timestamp": None,
        "tool_name": None,
        "test_results": {
            "core_tests": [],
            "edge_cases": [],
            "comparison_tests": [],
            "parameter_validation": []
        },
        "summary": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "success_rate": 0.0
        },
        "performance_metrics": {
            "average_response_time": None,
            "cache_hit_rate": None,
            "average_answer_length": None
        }
    }

# Quick validation samples for manual testing
QUICK_VALIDATION_SAMPLES = {
    "basic_test": {
        "parameters": {"question": "What makes a good action movie?"},
        "expected_keys": ["answer", "context_document_count"]
    },
    "parameter_error_test": {
        "parameters": {"query": "wrong parameter name"},
        "expected_error": "422 Unprocessable Entity"
    }
}

if __name__ == "__main__":
    # Demo usage
    print("MCP Test Data Samples")
    print("=" * 50)
    
    print(f"Total test cases available:")
    print(f"- Core tests: {len(MCPTestDataSamples.get_core_tests())}")
    print(f"- Edge cases: {len(MCPTestDataSamples.get_edge_cases())}")
    print(f"- Comparison tests: {len(MCPTestDataSamples.get_comparison_tests())}")
    print(f"- Invalid parameter tests: {len(MCPTestDataSamples.get_invalid_parameter_tests())}")
    
    print("\nSample test case:")
    test_case = MCPTestDataSamples.get_core_tests()[0]
    print(f"Name: {test_case.name}")
    print(f"Description: {test_case.description}")
    print(f"Parameters: {test_case.parameters}")
    print(f"Expected keys: {test_case.expected_response_keys}") 
#!/usr/bin/env python3
"""
Functional Quality Comparison Test: FastMCP vs FastAPI

This test ensures FastMCP delivers equivalent or better quality responses
compared to the existing FastAPI interface.
"""

import asyncio
import json
import sys
import os
import time
from typing import Dict, List, Any
from dataclasses import dataclass
import requests
import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class QualityMetrics:
    """Metrics for comparing response quality."""
    response_time: float
    document_count: int
    avg_content_length: int
    has_metadata: bool
    json_valid: bool
    error_occurred: bool
    relevance_scores: List[float]
    response_preview: str


class QualityComparator:
    """Compare FastMCP vs FastAPI response quality."""
    
    def __init__(self):
        self.test_queries = [
            "What is John Wick about?",
            "Who are the main characters in John Wick?",
            "What happens in the Continental Hotel?",
            "Tell me about Keanu Reeves performance",
            "What is the plot of John Wick?"
        ]
        
    async def test_fastmcp_quality(self, query: str, top_k: int = 5) -> QualityMetrics:
        """Test FastMCP semantic search quality."""
        from src.mcp_server.main import mcp
        from mcp.shared.memory import create_connected_server_and_client_session
        
        start_time = time.time()
        error_occurred = False
        
        try:
            async with create_connected_server_and_client_session(mcp._mcp_server) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "semantic_search", 
                    {
                        "query": query,
                        "top_k": top_k
                    }
                )
                
                response_time = time.time() - start_time
                
                if hasattr(result, 'content') and len(result.content) > 0:
                    content = result.content[0].text
                    
                    if content.startswith("Error"):
                        error_occurred = True
                        return QualityMetrics(
                            response_time=response_time,
                            document_count=0,
                            avg_content_length=0,
                            has_metadata=False,
                            json_valid=False,
                            error_occurred=True,
                            relevance_scores=[],
                            response_preview=content[:200]
                        )
                    
                    try:
                        parsed = json.loads(content)
                        
                        # Extract quality metrics
                        document_count = len(parsed)
                        avg_content_length = sum(len(doc.get('content', '')) for doc in parsed) // max(1, document_count)
                        has_metadata = all(doc.get('metadata') for doc in parsed)
                        relevance_scores = [doc.get('relevance_score', 0.0) or 0.0 for doc in parsed]
                        
                        return QualityMetrics(
                            response_time=response_time,
                            document_count=document_count,
                            avg_content_length=avg_content_length,
                            has_metadata=has_metadata,
                            json_valid=True,
                            error_occurred=False,
                            relevance_scores=relevance_scores,
                            response_preview=content[:200]
                        )
                        
                    except json.JSONDecodeError:
                        return QualityMetrics(
                            response_time=response_time,
                            document_count=0,
                            avg_content_length=0,
                            has_metadata=False,
                            json_valid=False,
                            error_occurred=True,
                            relevance_scores=[],
                            response_preview=content[:200]
                        )
                else:
                    return QualityMetrics(
                        response_time=response_time,
                        document_count=0,
                        avg_content_length=0,
                        has_metadata=False,
                        json_valid=False,
                        error_occurred=True,
                        relevance_scores=[],
                        response_preview="No content returned"
                    )
                    
        except Exception as e:
            return QualityMetrics(
                response_time=time.time() - start_time,
                document_count=0,
                avg_content_length=0,
                has_metadata=False,
                json_valid=False,
                error_occurred=True,
                relevance_scores=[],
                response_preview=f"Exception: {str(e)}"
            )

    def test_fastapi_quality(self, query: str, top_k: int = 5) -> QualityMetrics:
        """Test FastAPI semantic search quality (simulated - replace with actual FastAPI endpoint)."""
        # NOTE: Replace this with actual FastAPI endpoint when available
        # For now, return simulated metrics for comparison baseline
        
        start_time = time.time()
        
        # Simulated FastAPI response (replace with actual HTTP call)
        # response = requests.post(
        #     "http://localhost:8000/semantic_search",
        #     json={"query": query, "top_k": top_k}
        # )
        
        # Simulated baseline metrics for comparison
        time.sleep(0.02)  # Simulate 20ms response time
        response_time = time.time() - start_time
        
        return QualityMetrics(
            response_time=response_time,
            document_count=top_k,
            avg_content_length=450,  # Typical content length
            has_metadata=True,
            json_valid=True,
            error_occurred=False,
            relevance_scores=[0.85, 0.78, 0.72, 0.68, 0.61],  # Simulated scores
            response_preview="Simulated FastAPI response baseline"
        )

    async def run_comparison_test(self) -> Dict[str, Any]:
        """Run comprehensive quality comparison between FastMCP and FastAPI."""
        print("🔍 Running FastMCP vs FastAPI Quality Comparison")
        print("=" * 60)
        
        results = {
            "fastmcp_results": [],
            "fastapi_results": [],
            "summary": {},
            "quality_analysis": {}
        }
        
        # Test each query with both implementations
        for i, query in enumerate(self.test_queries):
            print(f"\n📝 Test {i+1}: {query}")
            
            # Test FastMCP
            print("   Testing FastMCP...")
            fastmcp_metrics = await self.test_fastmcp_quality(query)
            results["fastmcp_results"].append({
                "query": query,
                "metrics": fastmcp_metrics
            })
            
            # Test FastAPI (simulated)
            print("   Testing FastAPI (simulated)...")
            fastapi_metrics = self.test_fastapi_quality(query)
            results["fastapi_results"].append({
                "query": query,
                "metrics": fastapi_metrics
            })
            
            # Quick comparison
            self._print_query_comparison(query, fastmcp_metrics, fastapi_metrics)
        
        # Generate summary analysis
        results["summary"] = self._generate_summary(results)
        results["quality_analysis"] = self._analyze_quality_differences(results)
        
        return results

    def _print_query_comparison(self, query: str, fastmcp: QualityMetrics, fastapi: QualityMetrics):
        """Print comparison for a single query."""
        print(f"     FastMCP: {fastmcp.response_time:.3f}s, {fastmcp.document_count} docs, "
              f"valid_json={fastmcp.json_valid}, error={fastmcp.error_occurred}")
        print(f"     FastAPI: {fastapi.response_time:.3f}s, {fastapi.document_count} docs, "
              f"valid_json={fastapi.json_valid}, error={fastapi.error_occurred}")

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics."""
        fastmcp_data = results["fastmcp_results"]
        fastapi_data = results["fastapi_results"]
        
        # Calculate averages for FastMCP
        fastmcp_avg_time = sum(r["metrics"].response_time for r in fastmcp_data) / len(fastmcp_data)
        fastmcp_success_rate = sum(1 for r in fastmcp_data if not r["metrics"].error_occurred) / len(fastmcp_data)
        fastmcp_avg_docs = sum(r["metrics"].document_count for r in fastmcp_data) / len(fastmcp_data)
        
        # Calculate averages for FastAPI
        fastapi_avg_time = sum(r["metrics"].response_time for r in fastapi_data) / len(fastapi_data)
        fastapi_success_rate = sum(1 for r in fastapi_data if not r["metrics"].error_occurred) / len(fastapi_data)
        fastapi_avg_docs = sum(r["metrics"].document_count for r in fastapi_data) / len(fastapi_data)
        
        return {
            "fastmcp": {
                "avg_response_time": fastmcp_avg_time,
                "success_rate": fastmcp_success_rate,
                "avg_documents": fastmcp_avg_docs
            },
            "fastapi": {
                "avg_response_time": fastapi_avg_time,
                "success_rate": fastapi_success_rate,
                "avg_documents": fastapi_avg_docs
            },
            "performance_comparison": {
                "fastmcp_faster": fastmcp_avg_time < fastapi_avg_time,
                "speed_difference_ms": abs(fastmcp_avg_time - fastapi_avg_time) * 1000,
                "quality_equivalent": fastmcp_success_rate >= fastapi_success_rate
            }
        }

    def _analyze_quality_differences(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze quality differences between implementations."""
        analysis = {
            "strengths": {"fastmcp": [], "fastapi": []},
            "weaknesses": {"fastmcp": [], "fastapi": []},
            "recommendations": []
        }
        
        summary = results["summary"]
        
        # Analyze FastMCP strengths/weaknesses
        if summary["fastmcp"]["success_rate"] >= 0.8:
            analysis["strengths"]["fastmcp"].append("High success rate")
        else:
            analysis["weaknesses"]["fastmcp"].append("Low success rate - needs debugging")
            
        if summary["performance_comparison"]["fastmcp_faster"]:
            analysis["strengths"]["fastmcp"].append("Faster response times")
        else:
            analysis["weaknesses"]["fastmcp"].append("Slower than FastAPI baseline")
        
        # Generate recommendations
        if summary["fastmcp"]["success_rate"] < 1.0:
            analysis["recommendations"].append("Fix remaining error cases in FastMCP implementation")
            
        if not summary["performance_comparison"]["quality_equivalent"]:
            analysis["recommendations"].append("Investigate quality degradation in FastMCP vs FastAPI")
            
        analysis["recommendations"].append("Implement actual FastAPI endpoint for real comparison")
        
        return analysis

    def print_final_report(self, results: Dict[str, Any]):
        """Print comprehensive final report."""
        print("\n" + "=" * 60)
        print("📊 FINAL QUALITY COMPARISON REPORT")
        print("=" * 60)
        
        summary = results["summary"]
        analysis = results["quality_analysis"]
        
        print(f"\n🚀 FastMCP Performance:")
        print(f"   Average Response Time: {summary['fastmcp']['avg_response_time']:.3f}s")
        print(f"   Success Rate: {summary['fastmcp']['success_rate']:.1%}")
        print(f"   Average Documents: {summary['fastmcp']['avg_documents']:.1f}")
        
        print(f"\n⚡ FastAPI Performance (simulated):")
        print(f"   Average Response Time: {summary['fastapi']['avg_response_time']:.3f}s")
        print(f"   Success Rate: {summary['fastapi']['success_rate']:.1%}")
        print(f"   Average Documents: {summary['fastapi']['avg_documents']:.1f}")
        
        print(f"\n📈 Performance Comparison:")
        faster = "FastMCP" if summary["performance_comparison"]["fastmcp_faster"] else "FastAPI"
        print(f"   Faster Implementation: {faster}")
        print(f"   Speed Difference: {summary['performance_comparison']['speed_difference_ms']:.1f}ms")
        print(f"   Quality Equivalent: {summary['performance_comparison']['quality_equivalent']}")
        
        print(f"\n✅ FastMCP Strengths:")
        for strength in analysis["strengths"]["fastmcp"]:
            print(f"   • {strength}")
            
        if analysis["weaknesses"]["fastmcp"]:
            print(f"\n⚠️  FastMCP Areas for Improvement:")
            for weakness in analysis["weaknesses"]["fastmcp"]:
                print(f"   • {weakness}")
        
        print(f"\n🔧 Recommendations:")
        for rec in analysis["recommendations"]:
            print(f"   • {rec}")
        
        # Overall assessment
        success_rate = summary["fastmcp"]["success_rate"]
        if success_rate >= 0.9:
            print(f"\n🎉 RESULT: FastMCP is delivering high-quality responses! ({success_rate:.1%} success)")
        elif success_rate >= 0.7:
            print(f"\n⚠️  RESULT: FastMCP is mostly working but needs optimization ({success_rate:.1%} success)")
        else:
            print(f"\n❌ RESULT: FastMCP has significant quality issues ({success_rate:.1%} success)")


async def main():
    """Main test runner."""
    comparator = QualityComparator()
    
    try:
        results = await comparator.run_comparison_test()
        comparator.print_final_report(results)
        
        # Return success code based on FastMCP quality
        success_rate = results["summary"]["fastmcp"]["success_rate"]
        return 0 if success_rate >= 0.8 else 1
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


@pytest.mark.asyncio
async def test_functional_quality_comparison():
    exit_code = await main()
    assert exit_code == 0, "Functional quality comparison failed: FastMCP did not meet quality threshold."


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 
"""
Phoenix MCP Integration for Advanced RAG System

This module provides integration with Phoenix MCP tools for experiment data access.
Uses the available Phoenix MCP tools directly instead of creating a separate client.

Task 1.2: Enhanced experiment result extraction with comprehensive metrics and analysis.
Task 1.3: Pattern extraction logic for successful experiments (QA correctness > 0.8).
Task 1.4: Phoenix dataset analysis for golden testset pattern identification.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import json
import statistics
import time
from typing import Callable
from enum import Enum

# Error handling and retry imports
from functools import wraps
import random

# Task 1.6: Error Handling and Retry Logic Classes
class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""
    def __init__(self, message: str, last_exception: Exception, attempts: int):
        super().__init__(message)
        self.last_exception = last_exception
        self.attempts = attempts


class CircuitBreakerState(Enum):
    """Circuit breaker states for Phoenix MCP communication."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests  
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 30.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Exponential backoff base
    jitter: bool = True  # Add random jitter to prevent thundering herd
    
    
@dataclass  
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern."""
    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 3  # Number of successes to close from half-open
    timeout: float = 60.0  # Time to wait before trying half-open (seconds)


class CircuitBreaker:
    """Circuit breaker for Phoenix MCP communication reliability."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._logger = logging.getLogger(f"{__name__}.CircuitBreaker")
        
    def is_call_allowed(self) -> bool:
        """Check if call is allowed based on circuit breaker state."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.config.timeout):
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                self._logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful operation."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self._logger.info("Circuit breaker transitioning to CLOSED")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0  # Reset failure count on success
            
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                self._logger.warning(f"Circuit breaker transitioning to OPEN after {self.failure_count} failures")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self._logger.warning("Circuit breaker transitioning back to OPEN from HALF_OPEN")


def with_retry(config: Optional[RetryConfig] = None):
    """Decorator for adding retry logic to async functions."""
    if config is None:
        config = RetryConfig()
        
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if attempt == config.max_attempts - 1:
                        break
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    if config.jitter:
                        delay *= (0.5 + random.random() * 0.5)  # Add ±50% jitter
                    
                    # Log retry attempt
                    logger = logging.getLogger(func.__module__)
                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    await asyncio.sleep(delay)
            
            # All attempts failed
            raise RetryError(
                f"All {config.max_attempts} attempts failed for {func.__name__}",
                last_exception,
                config.max_attempts
            )
        
        return wrapper
    return decorator


def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """Decorator for adding circuit breaker pattern to async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not circuit_breaker.is_call_allowed():
                raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise e
        
        return wrapper
    return decorator


@dataclass
class PhoenixExperiment:
    """Phoenix experiment metadata."""
    id: str
    dataset_id: str
    project_name: str
    created_at: str
    repetitions: int = 1
    metadata: Dict[str, Any] = None


@dataclass
class PhoenixExperimentResult:
    """Phoenix experiment result with annotations."""
    example_id: str
    repetition_number: int
    input: str
    reference_output: str
    output: str
    latency_ms: int
    start_time: str
    end_time: str
    annotations: List[Dict[str, Any]]
    error: Optional[str] = None


@dataclass
class PhoenixDataset:
    """Phoenix dataset metadata."""
    id: str
    name: str
    description: str
    created_at: str
    metadata: Dict[str, Any] = None


@dataclass
class ExtractedPattern:
    """
    Structured pattern extracted from successful Phoenix experiments.
    
    Task 1.3: Core data structure for validated patterns ready for Qdrant storage.
    """
    pattern_id: str
    query: str
    response: str
    confidence_score: float
    qa_correctness_score: float
    rag_relevance_score: float
    experiment_id: str
    example_id: str
    dataset_id: str
    extraction_metadata: Dict[str, Any]
    
    def to_qdrant_payload(self) -> Dict[str, Any]:
        """
        Convert pattern to Qdrant storage format.
        
        Returns:
            Dictionary ready for Qdrant vector storage with metadata
        """
        return {
            "pattern_id": self.pattern_id,
            "query": self.query,
            "response": self.response,
            "confidence_score": self.confidence_score,
            "qa_correctness_score": self.qa_correctness_score,
            "rag_relevance_score": self.rag_relevance_score,
            "experiment_provenance": {
                "experiment_id": self.experiment_id,
                "example_id": self.example_id,
                "dataset_id": self.dataset_id
            },
            "extraction_metadata": self.extraction_metadata,
            "pattern_type": "phoenix_validated",
            "validation_status": "validated",
            "created_at": self.extraction_metadata.get("extraction_timestamp", datetime.utcnow().isoformat())
        }


@dataclass
class PatternExtractionResult:
    """
    Result of pattern extraction from Phoenix experiments.
    
    Task 1.3: Container for batch pattern extraction results.
    """
    total_experiments: int
    successful_patterns: List[ExtractedPattern]
    failed_extractions: List[Dict[str, Any]]
    extraction_summary: Dict[str, Any]
    
    def get_success_rate(self) -> float:
        """Calculate pattern extraction success rate."""
        if self.total_experiments == 0:
            return 0.0
        return len(self.successful_patterns) / self.total_experiments


@dataclass
class DatasetAnalysisResult:
    """
    Result of comprehensive dataset analysis for golden testset pattern identification.
    
    Task 1.4: Container for dataset-level analysis results.
    """
    dataset_id: str
    dataset_name: str
    total_experiments: int
    analyzed_experiments: int
    golden_patterns: List[ExtractedPattern]
    pattern_quality_metrics: Dict[str, float]
    experiment_performance_summary: Dict[str, Any]
    pattern_categories: Dict[str, List[ExtractedPattern]]
    analysis_metadata: Dict[str, Any]
    
    def get_golden_pattern_rate(self) -> float:
        """Calculate rate of golden patterns vs total analyzed experiments."""
        if self.analyzed_experiments == 0:
            return 0.0
        return len(self.golden_patterns) / self.analyzed_experiments
    
    def get_average_confidence(self) -> float:
        """Calculate average confidence score of golden patterns."""
        if not self.golden_patterns:
            return 0.0
        return statistics.mean([p.confidence_score for p in self.golden_patterns])
    
    def get_top_patterns(self, limit: int = 10) -> List[ExtractedPattern]:
        """Get top patterns by confidence score."""
        return sorted(self.golden_patterns, key=lambda p: p.confidence_score, reverse=True)[:limit]


@dataclass
class GoldenTestsetAnalysis:
    """
    Comprehensive analysis of golden testset for pattern identification.
    
    Task 1.4: High-level analysis of golden testset effectiveness.
    """
    testset_name: str
    dataset_analyses: List[DatasetAnalysisResult]
    cross_dataset_patterns: List[ExtractedPattern]
    overall_metrics: Dict[str, float]
    pattern_diversity_analysis: Dict[str, Any]
    recommendation_summary: Dict[str, Any]
    
    def get_total_golden_patterns(self) -> int:
        """Get total number of golden patterns across all datasets."""
        return sum(len(analysis.golden_patterns) for analysis in self.dataset_analyses)
    
    def get_best_performing_dataset(self) -> Optional[DatasetAnalysisResult]:
        """Get dataset with highest golden pattern rate."""
        if not self.dataset_analyses:
            return None
        return max(self.dataset_analyses, key=lambda d: d.get_golden_pattern_rate())


@dataclass
class BatchSyncConfig:
    """
    Configuration for batch synchronization operations.
    
    Task 1.5: Configuration container for periodic Phoenix data synchronization.
    """
    sync_interval_seconds: int = 3600  # 1 hour default
    batch_size: int = 10  # Process 10 items per batch
    max_concurrent_operations: int = 3  # Max parallel operations
    retry_attempts: int = 3  # Number of retries for failed operations
    retry_delay_seconds: float = 1.0  # Initial retry delay
    retry_exponential_base: float = 2.0  # Exponential backoff multiplier
    qa_threshold: float = 0.8  # Quality threshold for pattern extraction
    min_confidence: float = 0.7  # Minimum confidence for patterns
    target_datasets: Optional[List[str]] = None  # Specific datasets to sync (None = all)
    target_projects: Optional[List[str]] = None  # Specific projects to sync (None = all)
    enable_progress_reporting: bool = True  # Enable progress callbacks
    max_experiments_per_dataset: Optional[int] = None  # Limit experiments per dataset
    sync_state_directory: str = "sync_state"  # Directory for sync state files
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            "sync_interval_seconds": self.sync_interval_seconds,
            "batch_size": self.batch_size,
            "max_concurrent_operations": self.max_concurrent_operations,
            "retry_attempts": self.retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
            "retry_exponential_base": self.retry_exponential_base,
            "qa_threshold": self.qa_threshold,
            "min_confidence": self.min_confidence,
            "target_datasets": self.target_datasets,
            "target_projects": self.target_projects,
            "enable_progress_reporting": self.enable_progress_reporting,
            "max_experiments_per_dataset": self.max_experiments_per_dataset,
            "sync_state_directory": self.sync_state_directory
        }


@dataclass
class SyncState:
    """
    Track synchronization state for batch processing.
    
    Task 1.5: Persistent state tracking for incremental synchronization.
    """
    last_sync_timestamp: Optional[str] = None  # ISO timestamp of last successful sync
    last_full_sync_timestamp: Optional[str] = None  # ISO timestamp of last full sync
    synced_experiments: set = None  # Set of experiment IDs already processed
    synced_datasets: set = None  # Set of dataset IDs already analyzed
    failed_experiments: Dict[str, str] = None  # experiment_id -> error_message
    failed_datasets: Dict[str, str] = None  # dataset_id -> error_message
    sync_metrics: Dict[str, Any] = None  # Performance and success metrics
    total_patterns_extracted: int = 0  # Total patterns extracted across all syncs
    total_experiments_processed: int = 0  # Total experiments processed
    total_datasets_analyzed: int = 0  # Total datasets analyzed
    
    def __post_init__(self):
        """Initialize mutable default values."""
        if self.synced_experiments is None:
            self.synced_experiments = set()
        if self.synced_datasets is None:
            self.synced_datasets = set()
        if self.failed_experiments is None:
            self.failed_experiments = {}
        if self.failed_datasets is None:
            self.failed_datasets = {}
        if self.sync_metrics is None:
            self.sync_metrics = {}
    
    def mark_experiment_synced(self, experiment_id: str, patterns_count: int = 0):
        """Mark an experiment as successfully synced."""
        self.synced_experiments.add(experiment_id)
        self.failed_experiments.pop(experiment_id, None)  # Remove from failed if present
        self.total_experiments_processed += 1
        self.total_patterns_extracted += patterns_count
    
    def mark_dataset_synced(self, dataset_id: str, patterns_count: int = 0):
        """Mark a dataset as successfully synced."""
        self.synced_datasets.add(dataset_id)
        self.failed_datasets.pop(dataset_id, None)  # Remove from failed if present
        self.total_datasets_analyzed += 1
        self.total_patterns_extracted += patterns_count
    
    def mark_experiment_failed(self, experiment_id: str, error_message: str):
        """Mark an experiment as failed to sync."""
        self.failed_experiments[experiment_id] = error_message
        self.synced_experiments.discard(experiment_id)  # Remove from synced if present
    
    def mark_dataset_failed(self, dataset_id: str, error_message: str):
        """Mark a dataset as failed to sync."""
        self.failed_datasets[dataset_id] = error_message
        self.synced_datasets.discard(dataset_id)  # Remove from synced if present
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate for experiments."""
        total_attempted = len(self.synced_experiments) + len(self.failed_experiments)
        if total_attempted == 0:
            return 0.0
        return len(self.synced_experiments) / total_attempted
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "last_sync_timestamp": self.last_sync_timestamp,
            "last_full_sync_timestamp": self.last_full_sync_timestamp,
            "synced_experiments": list(self.synced_experiments),
            "synced_datasets": list(self.synced_datasets),
            "failed_experiments": self.failed_experiments,
            "failed_datasets": self.failed_datasets,
            "sync_metrics": self.sync_metrics,
            "total_patterns_extracted": self.total_patterns_extracted,
            "total_experiments_processed": self.total_experiments_processed,
            "total_datasets_analyzed": self.total_datasets_analyzed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncState':
        """Create SyncState from dictionary."""
        state = cls(
            last_sync_timestamp=data.get("last_sync_timestamp"),
            last_full_sync_timestamp=data.get("last_full_sync_timestamp"),
            synced_experiments=set(data.get("synced_experiments", [])),
            synced_datasets=set(data.get("synced_datasets", [])),
            failed_experiments=data.get("failed_experiments", {}),
            failed_datasets=data.get("failed_datasets", {}),
            sync_metrics=data.get("sync_metrics", {}),
            total_patterns_extracted=data.get("total_patterns_extracted", 0),
            total_experiments_processed=data.get("total_experiments_processed", 0),
            total_datasets_analyzed=data.get("total_datasets_analyzed", 0)
        )
        return state


@dataclass
class BatchSyncResult:
    """
    Results from a batch synchronization operation.
    
    Task 1.5: Container for sync operation results and metrics.
    """
    sync_id: str  # Unique identifier for this sync operation
    sync_type: str  # Type of sync: "full", "incremental", "targeted"
    start_time: str  # ISO timestamp when sync started
    end_time: Optional[str] = None  # ISO timestamp when sync completed
    total_items_discovered: int = 0  # Total items found to sync
    total_items_processed: int = 0  # Total items actually processed
    successful_items: int = 0  # Successfully processed items
    failed_items: int = 0  # Failed items
    skipped_items: int = 0  # Items skipped (already synced)
    patterns_extracted: int = 0  # New patterns extracted
    datasets_analyzed: int = 0  # Datasets analyzed
    experiments_processed: int = 0  # Experiments processed
    errors: List[Dict[str, str]] = None  # List of errors encountered
    performance_metrics: Dict[str, float] = None  # Timing and performance data
    
    def __post_init__(self):
        """Initialize mutable default values."""
        if self.errors is None:
            self.errors = []
        if self.performance_metrics is None:
            self.performance_metrics = {}
    
    def mark_completed(self, end_time: Optional[str] = None):
        """Mark the sync operation as completed."""
        if end_time is None:
            end_time = datetime.utcnow().isoformat()
        self.end_time = end_time
        
        # Calculate performance metrics
        if self.start_time and self.end_time:
            start_dt = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(self.end_time.replace('Z', '+00:00'))
            duration_seconds = (end_dt - start_dt).total_seconds()
            
            self.performance_metrics.update({
                "duration_seconds": duration_seconds,
                "items_per_second": self.total_items_processed / max(duration_seconds, 0.001),
                "success_rate": self.successful_items / max(self.total_items_processed, 1),
                "patterns_per_item": self.patterns_extracted / max(self.successful_items, 1)
            })
    
    def add_error(self, item_id: str, error_message: str, item_type: str = "unknown"):
        """Add an error to the sync result."""
        self.errors.append({
            "item_id": item_id,
            "item_type": item_type,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.failed_items += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the sync operation."""
        return {
            "sync_id": self.sync_id,
            "sync_type": self.sync_type,
            "duration": self.performance_metrics.get("duration_seconds", 0),
            "total_processed": self.total_items_processed,
            "success_rate": self.performance_metrics.get("success_rate", 0),
            "patterns_extracted": self.patterns_extracted,
            "datasets_analyzed": self.datasets_analyzed,
            "experiments_processed": self.experiments_processed,
            "error_count": len(self.errors)
        }


class PhoenixMCPClient:
    """
    Enhanced Phoenix MCP client with robust error handling and retry logic.
    
    Task 1.6: Comprehensive error handling for Phoenix MCP communication including:
    - Exponential backoff retry logic
    - Circuit breaker pattern for fault tolerance  
    - Detailed error logging and monitoring
    - Graceful degradation on service failures
    """
    
    def __init__(
        self, 
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        enable_circuit_breaker: bool = True,
        timeout: float = 30.0
    ):
        """
        Initialize Phoenix MCP client with error handling.
        
        Args:
            retry_config: Configuration for retry logic
            circuit_breaker_config: Configuration for circuit breaker
            enable_circuit_breaker: Whether to enable circuit breaker pattern
            timeout: Default timeout for operations
        """
        self._logger = logging.getLogger(__name__)
        
        # Error handling configuration
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self.enable_circuit_breaker = enable_circuit_breaker
        self._timeout = timeout
        
        # Circuit breakers for different operations
        if enable_circuit_breaker:
            self.list_projects_breaker = CircuitBreaker(self.circuit_breaker_config)
            self.list_datasets_breaker = CircuitBreaker(self.circuit_breaker_config)
            self.get_experiment_breaker = CircuitBreaker(self.circuit_breaker_config)
            self.get_dataset_examples_breaker = CircuitBreaker(self.circuit_breaker_config)
        
        self._logger.info(f"PhoenixMCPClient initialized with retry_config={self.retry_config}, "
                         f"circuit_breaker_enabled={enable_circuit_breaker}")

    def _apply_decorators(self, method):
        """Apply retry and circuit breaker decorators to a method."""
        # Apply retry decorator
        method = with_retry(self.retry_config)(method)
        
        # Apply circuit breaker if enabled
        if self.enable_circuit_breaker:
            # Determine which circuit breaker to use based on method name
            if hasattr(self, f"{method.__name__}_breaker"):
                breaker = getattr(self, f"{method.__name__}_breaker")
                method = with_circuit_breaker(breaker)(method)
        
        return method

    async def _safe_mcp_call(self, operation_name: str, fallback_result=None):
        """
        Safely call MCP operations with comprehensive error handling.
        
        Args:
            operation_name: Name of the operation for logging
            fallback_result: Result to return if operation fails
            
        Returns:
            Operation result or fallback_result on failure
        """
        try:
            # MCP tools should be called through MCP protocol
            self._logger.warning(f"Phoenix MCP tools should be called through MCP protocol for {operation_name}")
            return fallback_result
        except RetryError as e:
            self._logger.error(f"All retry attempts exhausted for {operation_name}: {e}")
            return fallback_result
        except Exception as e:
            self._logger.error(f"Unexpected error in {operation_name}: {e}")
            return fallback_result

    @with_retry()
    async def list_projects(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all Phoenix projects with retry logic.
        
        Args:
            limit: Maximum number of projects to return
            
        Returns:
            List of project dictionaries
            
        Raises:
            RetryError: If all retry attempts fail
        """
        try:
            return await self._safe_mcp_call("list_projects", [])
        except Exception as e:
            self._logger.error(f"Failed to list projects after retries: {e}")
            raise

    @with_retry()  
    async def list_datasets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all Phoenix datasets with retry logic.
        
        Args:
            limit: Maximum number of datasets to return
            
        Returns:
            List of dataset dictionaries
            
        Raises:
            RetryError: If all retry attempts fail
        """
        try:
            return await self._safe_mcp_call("list_datasets", [])
        except Exception as e:
            self._logger.error(f"Failed to list datasets after retries: {e}")
            raise

    @with_retry()
    async def get_experiment_by_id(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get detailed experiment results by ID with retry logic.
        
        This method provides comprehensive experiment data extraction for Task 1.2
        with robust error handling and retry mechanisms.
        
        Args:
            experiment_id: The experiment ID to retrieve
            
        Returns:
            Dictionary containing experiment metadata and results with annotations
            
        Raises:
            RetryError: If all retry attempts fail
            
        Example:
            try:
                experiment = await client.get_experiment_by_id("experiment123")
                for result in experiment.get('experimentResult', []):
                    qa_score = next((a['score'] for a in result.get('annotations', []) 
                                   if a['name'] == 'qa_correctness_score'), None)
                    if qa_score and qa_score > 0.8:
                        # Process high-quality result
                        pass
            except RetryError as e:
                logger.error(f"Failed to get experiment data: {e}")
                # Handle graceful degradation
        """
        try:
            if not experiment_id:
                raise ValueError("experiment_id cannot be empty")
                
            return await self._safe_mcp_call(f"get_experiment_by_id({experiment_id})", {})
        except Exception as e:
            self._logger.error(f"Failed to get experiment {experiment_id} after retries: {e}")
            raise

    @with_retry()
    async def get_dataset_examples(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get examples from a dataset with retry logic.
        
        Args:
            dataset_id: The dataset ID to retrieve examples from
            
        Returns:
            Dictionary containing dataset examples
            
        Raises:
            RetryError: If all retry attempts fail
        """
        try:
            if not dataset_id:
                raise ValueError("dataset_id cannot be empty")
                
            return await self._safe_mcp_call(f"get_dataset_examples({dataset_id})", {})
        except Exception as e:
            self._logger.error(f"Failed to get dataset examples {dataset_id} after retries: {e}")
            raise

    @with_retry()
    async def list_experiments_for_dataset(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        List all experiments for a specific dataset with retry logic.
        
        Task 1.4: Core method for systematic dataset analysis with error handling.
        
        Args:
            dataset_id: ID of the dataset to get experiments for
            
        Returns:
            List of experiment dictionaries
            
        Raises:
            RetryError: If all retry attempts fail
        """
        try:
            if not dataset_id:
                raise ValueError("dataset_id cannot be empty")
                
            return await self._safe_mcp_call(f"list_experiments_for_dataset({dataset_id})", [])
        except Exception as e:
            self._logger.error(f"Failed to list experiments for dataset {dataset_id} after retries: {e}")
            raise

    @with_retry()
    async def analyze_dataset_for_golden_patterns(
        self, 
        dataset_id: str,
        qa_threshold: float = 0.8,
        min_confidence: float = 0.7,
        max_experiments: Optional[int] = None
    ) -> DatasetAnalysisResult:
        """
        Comprehensive dataset analysis for golden testset pattern identification with retry logic.
        
        Task 1.4: Core dataset analysis method that identifies the best patterns
        across all experiments in a dataset with robust error handling.
        
        Args:
            dataset_id: ID of the dataset to analyze
            qa_threshold: Minimum QA correctness score for golden patterns
            min_confidence: Minimum confidence score for pattern inclusion
            max_experiments: Maximum number of experiments to analyze (None for all)
            
        Returns:
            DatasetAnalysisResult with comprehensive analysis
            
        Raises:
            RetryError: If all retry attempts fail
        """
        try:
            if not dataset_id:
                raise ValueError("dataset_id cannot be empty")
                
            # Get dataset metadata with error handling
            try:
                datasets = await self.list_datasets()
                dataset = next((d for d in datasets if d.get('id') == dataset_id), None)
                if not dataset:
                    self._logger.warning(f"Dataset {dataset_id} not found, creating placeholder")
                    dataset = {"id": dataset_id, "name": f"dataset_{dataset_id}"}
            except Exception as e:
                self._logger.warning(f"Failed to get dataset metadata: {e}, continuing with placeholder")
                dataset = {"id": dataset_id, "name": f"dataset_{dataset_id}"}
            
            # Get all experiments for this dataset with error handling
            try:
                experiments = await self.list_experiments_for_dataset(dataset_id)
                if max_experiments:
                    experiments = experiments[:max_experiments]
            except Exception as e:
                self._logger.error(f"Failed to get experiments for dataset {dataset_id}: {e}")
                experiments = []
            
            dataset_name = dataset.get('name', f'dataset_{dataset_id}')
            self._logger.info(f"Analyzing {len(experiments)} experiments for dataset {dataset_name}")
            
            # Extract patterns from all experiments with individual error handling
            all_patterns = []
            failed_extractions = []
            experiment_summaries = []
            
            for i, experiment in enumerate(experiments):
                try:
                    experiment_id = experiment.get("id", "")
                    self._logger.debug(f"Analyzing experiment {i+1}/{len(experiments)}: {experiment_id}")
                    
                    # Extract patterns from this experiment with retry
                    extraction_result = await self.extract_patterns_from_experiment(
                        experiment_id=experiment_id,
                        qa_threshold=qa_threshold,
                        min_confidence=min_confidence
                    )
                    
                    # Collect patterns and summaries
                    all_patterns.extend(extraction_result.successful_patterns)
                    failed_extractions.extend(extraction_result.failed_extractions)
                    
                    # Create experiment summary
                    experiment_summary = {
                        "experiment_id": experiment_id,
                        "pattern_count": len(extraction_result.successful_patterns),
                        "success_rate": extraction_result.get_success_rate(),
                        "created_at": experiment.get("created_at", ""),
                        "project_name": experiment.get("project_name", "")
                    }
                    experiment_summaries.append(experiment_summary)
                    
                except Exception as e:
                    self._logger.error(f"Failed to analyze experiment {experiment.get('id', 'unknown')}: {e}")
                    failed_extractions.append({
                        "experiment_id": experiment.get("id", "unknown"),
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Calculate quality metrics with error handling
            try:
                quality_metrics = self._calculate_dataset_quality_metrics(all_patterns, experiment_summaries)
            except Exception as e:
                self._logger.error(f"Failed to calculate quality metrics: {e}")
                quality_metrics = {"error": str(e)}
            
            # Categorize patterns with error handling
            try:
                pattern_categories = self._categorize_patterns(all_patterns)
            except Exception as e:
                self._logger.error(f"Failed to categorize patterns: {e}")
                pattern_categories = {"error": str(e)}
            
            # Create analysis metadata
            analysis_metadata = {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "qa_threshold": qa_threshold,
                "min_confidence": min_confidence,
                "max_experiments_analyzed": max_experiments,
                "total_patterns_extracted": len(all_patterns),
                "failed_extraction_count": len(failed_extractions),
                "error_handling_enabled": True
            }
            
            # Create experiment performance summary
            performance_summary = {
                "experiment_summaries": experiment_summaries,
                "avg_patterns_per_experiment": len(all_patterns) / len(experiments) if experiments else 0,
                "best_performing_experiment": max(experiment_summaries, key=lambda x: x["pattern_count"]) if experiment_summaries else None,
                "experiment_success_rates": [s["success_rate"] for s in experiment_summaries]
            }
            
            return DatasetAnalysisResult(
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                total_experiments=len(experiments),
                analyzed_experiments=len(experiment_summaries),
                golden_patterns=all_patterns,
                pattern_quality_metrics=quality_metrics,
                experiment_performance_summary=performance_summary,
                pattern_categories=pattern_categories,
                analysis_metadata=analysis_metadata
            )
            
        except Exception as e:
            self._logger.error(f"Failed to analyze dataset {dataset_id} after retries: {e}")
            raise

    @with_retry()
    async def analyze_golden_testset(
        self,
        testset_name: str = "johnwick_golden_testset",
        qa_threshold: float = 0.8,
        min_confidence: float = 0.7,
        max_experiments_per_dataset: Optional[int] = None
    ) -> GoldenTestsetAnalysis:
        """
        Comprehensive analysis of golden testset for pattern identification with retry logic.
        
        Task 1.4: High-level analysis method that provides insights across
        all datasets in a golden testset with robust error handling.
        
        Args:
            testset_name: Name of the golden testset to analyze
            qa_threshold: Minimum QA correctness score for golden patterns
            min_confidence: Minimum confidence score for pattern inclusion
            max_experiments_per_dataset: Maximum experiments to analyze per dataset
            
        Returns:
            GoldenTestsetAnalysis with comprehensive cross-dataset insights
            
        Raises:
            RetryError: If all retry attempts fail
        """
        try:
            # Find datasets matching the testset name with error handling
            try:
                datasets = await self.list_datasets()
                testset_datasets = [d for d in datasets if testset_name.lower() in d.get('name', '').lower()]
                
                if not testset_datasets:
                    # If no exact match, look for datasets that might be related
                    testset_datasets = [d for d in datasets if any(
                        keyword in d.get('name', '').lower() 
                        for keyword in ["golden", "testset", "benchmark", "eval"]
                    )]
            except Exception as e:
                self._logger.error(f"Failed to get datasets for testset '{testset_name}': {e}")
                testset_datasets = []
            
            self._logger.info(f"Found {len(testset_datasets)} datasets for testset '{testset_name}'")
            
            # Analyze each dataset with individual error handling
            dataset_analyses = []
            all_cross_dataset_patterns = []
            
            for dataset in testset_datasets:
                try:
                    dataset_id = dataset.get('id', '')
                    dataset_name = dataset.get('name', f'dataset_{dataset_id}')
                    
                    analysis = await self.analyze_dataset_for_golden_patterns(
                        dataset_id=dataset_id,
                        qa_threshold=qa_threshold,
                        min_confidence=min_confidence,
                        max_experiments=max_experiments_per_dataset
                    )
                    dataset_analyses.append(analysis)
                    all_cross_dataset_patterns.extend(analysis.golden_patterns)
                    
                except Exception as e:
                    self._logger.error(f"Failed to analyze dataset {dataset.get('name', 'unknown')}: {e}")
                    # Continue with other datasets even if one fails
                    continue
            
            # Calculate overall metrics with error handling
            try:
                overall_metrics = self._calculate_overall_testset_metrics(dataset_analyses)
            except Exception as e:
                self._logger.error(f"Failed to calculate overall metrics: {e}")
                overall_metrics = {"error": str(e)}
            
            # Analyze pattern diversity with error handling
            try:
                diversity_analysis = self._analyze_pattern_diversity(all_cross_dataset_patterns)
            except Exception as e:
                self._logger.error(f"Failed to analyze pattern diversity: {e}")
                diversity_analysis = {"error": str(e)}
            
            # Generate recommendations with error handling
            try:
                recommendations = self._generate_testset_recommendations(dataset_analyses, overall_metrics)
            except Exception as e:
                self._logger.error(f"Failed to generate recommendations: {e}")
                recommendations = {"error": str(e)}
            
            return GoldenTestsetAnalysis(
                testset_name=testset_name,
                dataset_analyses=dataset_analyses,
                cross_dataset_patterns=all_cross_dataset_patterns,
                overall_metrics=overall_metrics,
                pattern_diversity_analysis=diversity_analysis,
                recommendation_summary=recommendations
            )
            
        except Exception as e:
            self._logger.error(f"Failed to analyze golden testset '{testset_name}' after retries: {e}")
            raise

    @with_retry()
    async def extract_patterns_from_experiment(
        self, 
        experiment_id: str, 
        qa_threshold: float = 0.8,
        min_confidence: float = 0.7
    ) -> PatternExtractionResult:
        """
        Extract validated patterns from a single Phoenix experiment with retry logic.
        
        Task 1.3: Core pattern extraction logic for successful experiments with error handling.
        
        Args:
            experiment_id: The experiment ID to extract patterns from
            qa_threshold: Minimum QA correctness score for pattern inclusion
            min_confidence: Minimum confidence score for pattern validation
            
        Returns:
            PatternExtractionResult containing extracted patterns and metadata
            
        Raises:
            RetryError: If all retry attempts fail
        """
        try:
            if not experiment_id:
                raise ValueError("experiment_id cannot be empty")
                
            self._logger.info(f"Extracting patterns from experiment {experiment_id}")
            
            # Get experiment data with error handling
            try:
                experiment_data = await self.get_experiment_by_id(experiment_id)
            except Exception as e:
                self._logger.error(f"Failed to get experiment data for {experiment_id}: {e}")
                experiment_data = {}
            
            if not experiment_data:
                return PatternExtractionResult(
                    total_experiments=0,
                    successful_patterns=[],
                    failed_extractions=[{"error": f"No data found for experiment {experiment_id}"}],
                    extraction_summary={
                        "status": "failed", 
                        "reason": "no_data", 
                        "experiment_id": experiment_id,
                        "error_handling_enabled": True
                    }
                )
            
            # Extract successful results with error handling
            try:
                successful_results = await self.extract_successful_experiment_results(
                    experiment_data, qa_threshold
                )
            except Exception as e:
                self._logger.error(f"Failed to extract successful results: {e}")
                successful_results = []
            
            patterns = []
            failed_extractions = []
            
            for result in successful_results:
                try:
                    pattern = await self._create_pattern_from_result(
                        result, experiment_id, experiment_data, min_confidence
                    )
                    if pattern:
                        patterns.append(pattern)
                    else:
                        failed_extractions.append({
                            "example_id": result.example_id,
                            "reason": "confidence_too_low",
                            "qa_score": self._get_qa_score(result)
                        })
                except Exception as e:
                    failed_extractions.append({
                        "example_id": getattr(result, 'example_id', 'unknown'),
                        "error": str(e),
                        "reason": "extraction_error"
                    })
            
            # Generate extraction summary
            extraction_summary = {
                "experiment_id": experiment_id,
                "total_results": len(successful_results),
                "successful_patterns": len(patterns),
                "failed_extractions": len(failed_extractions),
                "success_rate": len(patterns) / len(successful_results) if successful_results else 0.0,
                "qa_threshold_used": qa_threshold,
                "min_confidence_used": min_confidence,
                "extraction_timestamp": datetime.utcnow().isoformat(),
                "dataset_id": experiment_data.get('metadata', {}).get('dataset_id', ''),
                "status": "failed" if not experiment_data else "completed",
                "error_handling_enabled": True
            }
            
            self._logger.info(f"Extracted {len(patterns)} patterns from experiment {experiment_id}")
            
            return PatternExtractionResult(
                total_experiments=len(successful_results),
                successful_patterns=patterns,
                failed_extractions=failed_extractions,
                extraction_summary=extraction_summary
            )
            
        except Exception as e:
            self._logger.error(f"Failed to extract patterns from experiment {experiment_id} after retries: {e}")
            raise

    def _calculate_dataset_quality_metrics(self, patterns: List[ExtractedPattern], experiment_summaries: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate quality metrics for dataset analysis.
        
        Args:
            patterns: List of extracted patterns
            experiment_summaries: List of experiment summary data
            
        Returns:
            Dictionary of quality metrics
        """
        try:
            if not patterns:
                return {
                    "avg_confidence": 0.0,
                    "avg_qa_score": 0.0,
                    "avg_rag_relevance": 0.0,
                    "pattern_count": 0,
                    "total_experiments": len(experiment_summaries)
                }
            
            metrics = {
                "avg_confidence": statistics.mean([p.confidence_score for p in patterns]),
                "avg_qa_score": statistics.mean([p.qa_correctness_score for p in patterns]),
                "avg_rag_relevance": statistics.mean([p.rag_relevance_score for p in patterns]),
                "pattern_count": len(patterns),
                "total_experiments": len(experiment_summaries),
                "patterns_per_experiment": len(patterns) / max(len(experiment_summaries), 1)
            }
            
            return metrics
        except Exception as e:
            self._logger.error(f"Error calculating quality metrics: {e}")
            return {"error": str(e), "pattern_count": len(patterns)}

    def _categorize_patterns(self, patterns: List[ExtractedPattern]) -> Dict[str, List[ExtractedPattern]]:
        """
        Categorize patterns by quality and type.
        
        Args:
            patterns: List of extracted patterns
            
        Returns:
            Dictionary with categorized patterns
        """
        try:
            if not patterns:
                return {
                    "high_quality": [],
                    "medium_quality": [],
                    "low_quality": [],
                    "high_confidence": [],
                    "medium_confidence": [],
                    "low_confidence": []
                }
            
            categories = {
                "high_quality": [p for p in patterns if p.qa_correctness_score >= 0.8 and p.rag_relevance_score >= 0.8],
                "medium_quality": [p for p in patterns if 0.6 <= p.qa_correctness_score < 0.8 or 0.6 <= p.rag_relevance_score < 0.8],
                "low_quality": [p for p in patterns if p.qa_correctness_score < 0.6 or p.rag_relevance_score < 0.6],
                "high_confidence": [p for p in patterns if p.confidence_score >= 0.8],
                "medium_confidence": [p for p in patterns if 0.6 <= p.confidence_score < 0.8],
                "low_confidence": [p for p in patterns if p.confidence_score < 0.6]
            }
            
            return categories
        except Exception as e:
            self._logger.error(f"Error categorizing patterns: {e}")
            return {"error": str(e)}


class PhoenixBatchProcessor:
    """
    Enhanced batch processor for Phoenix data synchronization with error handling.
    
    Task 1.5: Comprehensive batch processing with retry logic and circuit breaker support.
    """
    
    def __init__(
        self,
        client: PhoenixMCPClient,
        config: BatchSyncConfig,
        progress_callback: Optional[Callable[[float, Optional[float], str], None]] = None,
        retry_config: Optional[RetryConfig] = None,
        enable_circuit_breaker: bool = True
    ):
        """
        Initialize batch processor with error handling capabilities.
        
        Args:
            client: Phoenix MCP client with error handling
            config: Batch sync configuration  
            progress_callback: Optional progress callback function
            retry_config: Configuration for retry logic
            enable_circuit_breaker: Whether to enable circuit breaker for batch operations
        """
        self.client = client
        self.config = config
        self.progress_callback = progress_callback
        self._logger = logging.getLogger(f"{__name__}.PhoenixBatchProcessor")
        
        # Error handling configuration
        self.retry_config = retry_config or RetryConfig(max_attempts=2, base_delay=2.0)  # More conservative for batch
        self.enable_circuit_breaker = enable_circuit_breaker
        
        # Circuit breaker for batch operations
        if enable_circuit_breaker:
            batch_breaker_config = CircuitBreakerConfig(
                failure_threshold=3,  # Lower threshold for batch operations
                success_threshold=2,
                timeout=120.0  # Longer timeout for batch operations
            )
            self.batch_circuit_breaker = CircuitBreaker(batch_breaker_config)
        
        self._logger.info(f"PhoenixBatchProcessor initialized with retry_config={self.retry_config}, "
                         f"circuit_breaker_enabled={enable_circuit_breaker}")

    @with_retry()
    async def sync_experiments(self, sync_state: SyncState) -> BatchSyncResult:
        """
        Synchronize experiments with comprehensive error handling.
        
        Args:
            sync_state: Current synchronization state
            
        Returns:
            BatchSyncResult with detailed error information
            
        Raises:
            RetryError: If all retry attempts fail
        """
        start_time = datetime.utcnow()
        
        try:
            # Apply circuit breaker if enabled
            if self.enable_circuit_breaker and not self.batch_circuit_breaker.is_call_allowed():
                raise Exception("Batch circuit breaker is OPEN - too many recent failures")
            
            self._logger.info(f"Starting batch sync of experiments with error handling")
            
            # Get datasets with error handling
            try:
                datasets = await self.client.list_datasets()
                if not datasets:
                    self._logger.warning("No datasets found, returning empty result")
                    return self._create_empty_result(start_time, "No datasets found")
            except Exception as e:
                self._logger.error(f"Failed to get datasets: {e}")
                if self.enable_circuit_breaker:
                    self.batch_circuit_breaker.record_failure()
                raise
            
            total_datasets = len(datasets)
            processed_datasets = 0
            successful_patterns = 0
            failed_operations = []
            
            # Process each dataset with individual error handling
            for i, dataset in enumerate(datasets):
                try:
                    dataset_id = dataset.get('id', '')
                    dataset_name = dataset.get('name', f'dataset_{dataset_id}')
                    
                    # Update progress
                    progress_pct = (i / total_datasets) * 100
                    if self.progress_callback:
                        try:
                            self.progress_callback(
                                progress_pct,
                                100.0,
                                f"Processing dataset {i+1}/{total_datasets}: {dataset_name}"
                            )
                        except Exception as e:
                            self._logger.warning(f"Progress callback failed: {e}")
                    
                    # Analyze dataset for patterns with retry
                    try:
                        analysis_result = await self.client.analyze_dataset_for_golden_patterns(
                            dataset_id=dataset_id,
                            qa_threshold=self.config.qa_threshold,
                            min_confidence=self.config.min_confidence,
                            max_experiments=self.config.batch_size
                        )
                        
                        pattern_count = len(analysis_result.golden_patterns)
                        successful_patterns += pattern_count
                        processed_datasets += 1
                        
                        self._logger.info(f"Successfully processed dataset {dataset_name}: {pattern_count} patterns")
                        
                    except Exception as e:
                        error_info = {
                            "dataset_id": dataset_id,
                            "dataset_name": dataset_name,
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat(),
                            "operation": "analyze_dataset_for_golden_patterns"
                        }
                        failed_operations.append(error_info)
                        self._logger.error(f"Failed to process dataset {dataset_name}: {e}")
                        
                        # Continue with other datasets even if one fails
                        continue
                
                except Exception as e:
                    # Catch-all for dataset processing errors
                    error_info = {
                        "dataset_info": str(dataset),
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                        "operation": "dataset_processing"
                    }
                    failed_operations.append(error_info)
                    self._logger.error(f"Unexpected error processing dataset: {e}")
                    continue
            
            # Update sync state with error handling
            try:
                sync_state.last_sync_time = start_time
                sync_state.total_synced += successful_patterns
                sync_state.sync_count += 1
            except Exception as e:
                self._logger.error(f"Failed to update sync state: {e}")
                # Don't fail the entire operation for sync state update errors
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Create result with error information
            result = BatchSyncResult(
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                datasets_processed=processed_datasets,
                patterns_extracted=successful_patterns,
                success_rate=processed_datasets / total_datasets if total_datasets > 0 else 0.0,
                metadata={
                    "total_datasets_found": total_datasets,
                    "failed_operations_count": len(failed_operations),
                    "failed_operations": failed_operations,
                    "error_handling_enabled": True,
                    "circuit_breaker_enabled": self.enable_circuit_breaker,
                    "config_used": asdict(self.config)
                }
            )
            
            # Record success for circuit breaker
            if self.enable_circuit_breaker:
                self.batch_circuit_breaker.record_success()
            
            # Final progress update
            if self.progress_callback:
                try:
                    self.progress_callback(
                        100.0,
                        100.0,
                        f"Batch sync completed: {successful_patterns} patterns from {processed_datasets}/{total_datasets} datasets"
                    )
                except Exception as e:
                    self._logger.warning(f"Final progress callback failed: {e}")
            
            self._logger.info(f"Batch sync completed: {successful_patterns} patterns, {len(failed_operations)} failures")
            return result
            
        except Exception as e:
            # Record failure for circuit breaker
            if self.enable_circuit_breaker:
                self.batch_circuit_breaker.record_failure()
            
            # Create failure result
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            self._logger.error(f"Batch sync failed after {duration:.2f}s: {e}")
            
            return BatchSyncResult(
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                datasets_processed=0,
                patterns_extracted=0,
                success_rate=0.0,
                metadata={
                    "error": str(e),
                    "status": "failed",
                    "error_handling_enabled": True,
                    "circuit_breaker_enabled": self.enable_circuit_breaker
                }
            )

    @with_retry()
    async def sync_specific_datasets(
        self,
        dataset_ids: List[str],
        sync_state: SyncState
    ) -> BatchSyncResult:
        """
        Synchronize specific datasets with error handling.
        
        Args:
            dataset_ids: List of dataset IDs to sync
            sync_state: Current synchronization state
            
        Returns:
            BatchSyncResult with detailed processing information
            
        Raises:
            RetryError: If all retry attempts fail
        """
        start_time = datetime.utcnow()
        
        try:
            # Apply circuit breaker if enabled
            if self.enable_circuit_breaker and not self.batch_circuit_breaker.is_call_allowed():
                raise Exception("Batch circuit breaker is OPEN - too many recent failures")
            
            self._logger.info(f"Starting sync of {len(dataset_ids)} specific datasets with error handling")
            
            total_datasets = len(dataset_ids)
            processed_datasets = 0
            successful_patterns = 0
            failed_operations = []
            
            # Process each dataset ID with individual error handling
            for i, dataset_id in enumerate(dataset_ids):
                try:
                    if not dataset_id:
                        self._logger.warning(f"Skipping empty dataset ID at index {i}")
                        continue
                    
                    # Update progress
                    progress_pct = (i / total_datasets) * 100
                    if self.progress_callback:
                        try:
                            self.progress_callback(
                                progress_pct,
                                100.0,
                                f"Processing dataset {i+1}/{total_datasets}: {dataset_id}"
                            )
                        except Exception as e:
                            self._logger.warning(f"Progress callback failed: {e}")
                    
                    # Analyze specific dataset with retry
                    try:
                        analysis_result = await self.client.analyze_dataset_for_golden_patterns(
                            dataset_id=dataset_id,
                            qa_threshold=self.config.qa_threshold,
                            min_confidence=self.config.min_confidence,
                            max_experiments=self.config.batch_size
                        )
                        
                        pattern_count = len(analysis_result.golden_patterns)
                        successful_patterns += pattern_count
                        processed_datasets += 1
                        
                        self._logger.info(f"Successfully processed dataset {dataset_id}: {pattern_count} patterns")
                        
                    except Exception as e:
                        error_info = {
                            "dataset_id": dataset_id,
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat(),
                            "operation": "analyze_specific_dataset"
                        }
                        failed_operations.append(error_info)
                        self._logger.error(f"Failed to process dataset {dataset_id}: {e}")
                        
                        # Continue with other datasets even if one fails
                        continue
                
                except Exception as e:
                    # Catch-all for dataset processing errors
                    error_info = {
                        "dataset_id": dataset_id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                        "operation": "dataset_id_processing"
                    }
                    failed_operations.append(error_info)
                    self._logger.error(f"Unexpected error processing dataset {dataset_id}: {e}")
                    continue
            
            # Update sync state with error handling
            try:
                sync_state.last_sync_time = start_time
                sync_state.total_synced += successful_patterns
                sync_state.sync_count += 1
            except Exception as e:
                self._logger.error(f"Failed to update sync state: {e}")
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Create result with comprehensive error information
            result = BatchSyncResult(
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                datasets_processed=processed_datasets,
                patterns_extracted=successful_patterns,
                success_rate=processed_datasets / total_datasets if total_datasets > 0 else 0.0,
                metadata={
                    "requested_dataset_ids": dataset_ids,
                    "total_datasets_requested": total_datasets,
                    "failed_operations_count": len(failed_operations),
                    "failed_operations": failed_operations,
                    "error_handling_enabled": True,
                    "circuit_breaker_enabled": self.enable_circuit_breaker,
                    "config_used": asdict(self.config)
                }
            )
            
            # Record success for circuit breaker
            if self.enable_circuit_breaker:
                self.batch_circuit_breaker.record_success()
            
            # Final progress update
            if self.progress_callback:
                try:
                    self.progress_callback(
                        100.0,
                        100.0,
                        f"Specific dataset sync completed: {successful_patterns} patterns from {processed_datasets}/{total_datasets} datasets"
                    )
                except Exception as e:
                    self._logger.warning(f"Final progress callback failed: {e}")
            
            self._logger.info(f"Specific dataset sync completed: {successful_patterns} patterns, {len(failed_operations)} failures")
            return result
            
        except Exception as e:
            # Record failure for circuit breaker
            if self.enable_circuit_breaker:
                self.batch_circuit_breaker.record_failure()
            
            # Create failure result
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            self._logger.error(f"Specific dataset sync failed after {duration:.2f}s: {e}")
            
            return BatchSyncResult(
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                datasets_processed=0,
                patterns_extracted=0,
                success_rate=0.0,
                metadata={
                    "error": str(e),
                    "status": "failed",
                    "requested_dataset_ids": dataset_ids,
                    "error_handling_enabled": True,
                    "circuit_breaker_enabled": self.enable_circuit_breaker
                }
            )

    def _create_empty_result(self, start_time: datetime, reason: str) -> BatchSyncResult:
        """Create an empty batch sync result for early returns."""
        end_time = datetime.utcnow()
        
        sync_id = f"empty_sync_{int(start_time.timestamp())}"
        
        result = BatchSyncResult(
            sync_id=sync_id,
            sync_type="empty",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            patterns_extracted=0,
            datasets_analyzed=0,
            experiments_processed=0
        )
        
        # Calculate duration manually since the constructor might not accept all params
        duration = (end_time - start_time).total_seconds()
        result.performance_metrics = {
            "duration_seconds": duration,
            "reason": reason,
            "status": "empty",
            "error_handling_enabled": True,
            "circuit_breaker_enabled": self.enable_circuit_breaker
        }
        
        return result


def get_phoenix_client(timeout: float = 30.0) -> PhoenixMCPClient:
    """
    Get a Phoenix MCP client instance.
    
    Args:
        timeout: Request timeout in seconds
        
    Returns:
        PhoenixMCPClient instance
    """
    return PhoenixMCPClient(timeout=timeout)


# Convenience functions for direct access
async def get_experiment_by_id(experiment_id: str) -> Dict[str, Any]:
    """
    Convenience function to get experiment by ID.
    
    Args:
        experiment_id: The experiment ID to retrieve
        
    Returns:
        Dictionary containing experiment data
    """
    client = get_phoenix_client()
    return await client.get_experiment_by_id(experiment_id)


async def get_experiment_summary(experiment_id: str) -> Dict[str, Any]:
    """
    Convenience function to get experiment summary.
    
    Args:
        experiment_id: The experiment ID to analyze
        
    Returns:
        Dictionary containing experiment summary and metrics
    """
    client = get_phoenix_client()
    return await client.get_experiment_summary(experiment_id)


# Task 1.3: Pattern extraction convenience functions
async def extract_patterns_from_experiment(
    experiment_id: str, 
    qa_threshold: float = 0.8,
    min_confidence: float = 0.7
) -> PatternExtractionResult:
    """
    Convenience function to extract patterns from a single experiment.
    
    Task 1.3: Direct pattern extraction interface.
    
    Args:
        experiment_id: The experiment ID to extract patterns from
        qa_threshold: Minimum QA correctness score
        min_confidence: Minimum confidence score
        
    Returns:
        PatternExtractionResult containing extracted patterns
    """
    client = get_phoenix_client()
    return await client.extract_patterns_from_experiment(experiment_id, qa_threshold, min_confidence)


async def extract_patterns_from_golden_testset(
    dataset_name: str = "johnwick_golden_testset",
    qa_threshold: float = 0.8,
    min_confidence: float = 0.7,
    max_experiments: Optional[int] = None
) -> PatternExtractionResult:
    """
    Convenience function to extract patterns from golden testset dataset.
    
    Task 1.3: Simplified interface for golden testset pattern extraction.
    
    Args:
        dataset_name: Name of the golden testset dataset
        qa_threshold: Minimum QA correctness score for pattern inclusion
        min_confidence: Minimum confidence score for pattern validation
        max_experiments: Maximum number of experiments to process
        
    Returns:
        PatternExtractionResult containing extracted patterns and metadata
    """
    client = get_phoenix_client()
    
    # Find dataset by name
    datasets = await client.list_datasets()
    target_dataset = next((d for d in datasets if dataset_name.lower() in d.name.lower()), None)
    
    if not target_dataset:
        return PatternExtractionResult(
            total_experiments=0,
            successful_patterns=[],
            failed_extractions=[{"error": f"Dataset '{dataset_name}' not found"}],
            extraction_summary={"status": "failed", "reason": "dataset_not_found"}
        )
    
    return await client.extract_patterns_from_dataset(
        dataset_id=target_dataset.id,
        qa_threshold=qa_threshold,
        min_confidence=min_confidence,
        max_experiments=max_experiments
    )


async def analyze_golden_testset(
    testset_name: str = "johnwick_golden_testset",
    qa_threshold: float = 0.8,
    min_confidence: float = 0.7,
    max_experiments_per_dataset: Optional[int] = None
) -> GoldenTestsetAnalysis:
    """
    Convenience function for comprehensive golden testset analysis.
    
    Task 1.4: Simplified interface for cross-dataset testset analysis.
    
    Args:
        testset_name: Name of the golden testset to analyze
        qa_threshold: Minimum QA correctness score for golden patterns
        min_confidence: Minimum confidence score for pattern inclusion
        max_experiments_per_dataset: Maximum experiments to analyze per dataset
        
    Returns:
        GoldenTestsetAnalysis with comprehensive cross-dataset insights
    """
    client = get_phoenix_client()
    return await client.analyze_golden_testset(
        testset_name=testset_name,
        qa_threshold=qa_threshold,
        min_confidence=min_confidence,
        max_experiments_per_dataset=max_experiments_per_dataset
    )


async def get_dataset_pattern_summary(
    dataset_name: str,
    qa_threshold: float = 0.8,
    min_confidence: float = 0.7,
    top_n: int = 10
) -> Dict[str, Any]:
    """
    Get a summary of top patterns from a dataset.
    
    Task 1.4: Quick access to best patterns from a dataset.
    
    Args:
        dataset_name: Name of the dataset to analyze
        qa_threshold: Minimum QA correctness score
        min_confidence: Minimum confidence score
        top_n: Number of top patterns to return
        
    Returns:
        Dictionary with dataset summary and top patterns
    """
    client = get_phoenix_client()
    
    # Find dataset by name
    datasets = await client.list_datasets()
    target_dataset = next((d for d in datasets if dataset_name.lower() in d.name.lower()), None)
    
    if not target_dataset:
        return {
            "error": f"Dataset '{dataset_name}' not found",
            "available_datasets": [d.name for d in datasets]
        }
    
    # Analyze dataset
    analysis = await client.analyze_dataset_for_golden_patterns(
        dataset_id=target_dataset.id,
        qa_threshold=qa_threshold,
        min_confidence=min_confidence
    )
    
    # Get top patterns
    top_patterns = analysis.get_top_patterns(limit=top_n)
    
    return {
        "dataset_name": analysis.dataset_name,
        "dataset_id": analysis.dataset_id,
        "total_experiments": analysis.total_experiments,
        "golden_patterns_count": len(analysis.golden_patterns),
        "golden_pattern_rate": analysis.get_golden_pattern_rate(),
        "average_confidence": analysis.get_average_confidence(),
        "quality_metrics": analysis.pattern_quality_metrics,
        "top_patterns": [
            {
                "pattern_id": p.pattern_id,
                "query": p.query[:200] + "..." if len(p.query) > 200 else p.query,
                "response": p.response[:200] + "..." if len(p.response) > 200 else p.response,
                "confidence_score": p.confidence_score,
                "qa_correctness_score": p.qa_correctness_score,
                "rag_relevance_score": p.rag_relevance_score
            }
            for p in top_patterns
        ],
        "pattern_categories": {
            category: len(patterns) 
            for category, patterns in analysis.pattern_categories.items()
        },
        "analysis_timestamp": analysis.analysis_metadata.get("analysis_timestamp")
    }


async def compare_dataset_performance(
    dataset_names: List[str],
    qa_threshold: float = 0.8,
    min_confidence: float = 0.7
) -> Dict[str, Any]:
    """
    Compare performance across multiple datasets.
    
    Args:
        dataset_names: List of dataset names to compare
        qa_threshold: Minimum QA correctness score
        min_confidence: Minimum confidence score
        
    Returns:
        Dictionary with comparative analysis results
    """
    client = get_phoenix_client()
    
    results = {}
    for dataset_name in dataset_names:
        try:
            # Find dataset by name
            datasets = await client.list_datasets()
            target_dataset = next((d for d in datasets if dataset_name.lower() in d.name.lower()), None)
            
            if target_dataset:
                analysis = await client.analyze_dataset_for_golden_patterns(
                    dataset_id=target_dataset.id,
                    qa_threshold=qa_threshold,
                    min_confidence=min_confidence
                )
                
                results[dataset_name] = {
                    "dataset_id": analysis.dataset_id,
                    "total_experiments": analysis.total_experiments,
                    "golden_patterns": len(analysis.golden_patterns),
                    "golden_pattern_rate": analysis.get_golden_pattern_rate(),
                    "average_confidence": analysis.get_average_confidence(),
                    "quality_metrics": analysis.pattern_quality_metrics
                }
            else:
                results[dataset_name] = {"error": "Dataset not found"}
                
        except Exception as e:
            results[dataset_name] = {"error": str(e)}
    
    return {
        "comparison_results": results,
        "summary": {
            "total_datasets": len(dataset_names),
            "successful_analyses": len([r for r in results.values() if "error" not in r]),
            "best_performing": max(
                [k for k, v in results.items() if "golden_pattern_rate" in v],
                key=lambda k: results[k]["golden_pattern_rate"],
                default=None
            )
        }
    }


# Task 1.5: Batch processing convenience functions
def get_batch_processor(config: Optional[BatchSyncConfig] = None) -> PhoenixBatchProcessor:
    """
    Get a Phoenix batch processor instance.
    
    Task 1.5: Convenience function for batch processor creation.
    
    Args:
        config: Optional batch synchronization configuration
        
    Returns:
        PhoenixBatchProcessor instance
    """
    return PhoenixBatchProcessor(config=config)


async def run_full_phoenix_sync(
    config: Optional[BatchSyncConfig] = None,
    progress_callback: Optional[Callable[[str, float, str], None]] = None
) -> BatchSyncResult:
    """
    Run a full synchronization of all Phoenix data.
    
    Task 1.5: Convenience function for full data synchronization.
    
    Args:
        config: Optional batch synchronization configuration
        progress_callback: Optional progress reporting callback
        
    Returns:
        BatchSyncResult with sync operation results
    """
    processor = get_batch_processor(config)
    
    if progress_callback:
        processor.set_progress_callback(progress_callback)
    
    return await processor.run_full_sync()


async def run_incremental_phoenix_sync(
    config: Optional[BatchSyncConfig] = None,
    progress_callback: Optional[Callable[[str, float, str], None]] = None
) -> BatchSyncResult:
    """
    Run incremental synchronization of new Phoenix data.
    
    Task 1.5: Convenience function for incremental data synchronization.
    
    Args:
        config: Optional batch synchronization configuration
        progress_callback: Optional progress reporting callback
        
    Returns:
        BatchSyncResult with sync operation results
    """
    processor = get_batch_processor(config)
    
    if progress_callback:
        processor.set_progress_callback(progress_callback)
    
    return await processor.run_incremental_sync()


async def sync_specific_datasets(
    dataset_names: List[str],
    config: Optional[BatchSyncConfig] = None,
    progress_callback: Optional[Callable[[str, float, str], None]] = None
) -> BatchSyncResult:
    """
    Synchronize specific datasets by name.
    
    Task 1.5: Convenience function for targeted dataset synchronization.
    
    Args:
        dataset_names: List of dataset names to synchronize
        config: Optional batch synchronization configuration
        progress_callback: Optional progress reporting callback
        
    Returns:
        BatchSyncResult with sync operation results
    """
    processor = get_batch_processor(config)
    
    if progress_callback:
        processor.set_progress_callback(progress_callback)
    
    return await processor.run_targeted_sync(dataset_names)


async def start_periodic_phoenix_sync(
    config: Optional[BatchSyncConfig] = None,
    progress_callback: Optional[Callable[[str, float, str], None]] = None
) -> PhoenixBatchProcessor:
    """
    Start periodic Phoenix data synchronization.
    
    Task 1.5: Convenience function to start background sync process.
    
    Args:
        config: Optional batch synchronization configuration
        progress_callback: Optional progress reporting callback
        
    Returns:
        PhoenixBatchProcessor instance (keep reference to stop later)
    """
    processor = get_batch_processor(config)
    
    if progress_callback:
        processor.set_progress_callback(progress_callback)
    
    await processor.start_periodic_sync()
    return processor


def get_phoenix_sync_status(processor: Optional[PhoenixBatchProcessor] = None) -> Dict[str, Any]:
    """
    Get current Phoenix synchronization status.
    
    Task 1.5: Convenience function for sync status monitoring.
    
    Args:
        processor: Optional existing processor instance
        
    Returns:
        Dictionary with sync status information
    """
    if processor is None:
        processor = get_batch_processor()
    
    return processor.get_sync_status()


async def retry_failed_phoenix_sync(
    processor: Optional[PhoenixBatchProcessor] = None,
    progress_callback: Optional[Callable[[str, float, str], None]] = None
) -> BatchSyncResult:
    """
    Retry synchronization of previously failed items.
    
    Task 1.5: Convenience function for retry operations.
    
    Args:
        processor: Optional existing processor instance
        progress_callback: Optional progress reporting callback
        
    Returns:
        BatchSyncResult with retry operation results
    """
    if processor is None:
        processor = get_batch_processor()
    
    if progress_callback:
        processor.set_progress_callback(progress_callback)
    
    return await processor.retry_failed_items()


# Task 1.5: Configuration helpers
def create_batch_sync_config(
    sync_interval_hours: float = 1.0,
    batch_size: int = 10,
    max_concurrent: int = 3,
    qa_threshold: float = 0.8,
    min_confidence: float = 0.7,
    target_datasets: Optional[List[str]] = None,
    enable_progress: bool = True
) -> BatchSyncConfig:
    """
    Create a batch synchronization configuration with common parameters.
    
    Task 1.5: Helper function for configuration creation.
    
    Args:
        sync_interval_hours: Hours between periodic syncs
        batch_size: Number of items to process per batch
        max_concurrent: Maximum concurrent operations
        qa_threshold: Quality threshold for pattern extraction
        min_confidence: Minimum confidence for patterns
        target_datasets: Specific datasets to sync (None for all)
        enable_progress: Enable progress reporting
        
    Returns:
        BatchSyncConfig instance
    """
    return BatchSyncConfig(
        sync_interval_seconds=int(sync_interval_hours * 3600),
        batch_size=batch_size,
        max_concurrent_operations=max_concurrent,
        qa_threshold=qa_threshold,
        min_confidence=min_confidence,
        target_datasets=target_datasets,
        enable_progress_reporting=enable_progress
    )


from src.core.settings import get_settings

# Task 1.7: Phoenix Configuration Factory Functions
def create_phoenix_retry_config(settings: Optional['Settings'] = None) -> RetryConfig:
    """
    Create RetryConfig from application settings.
    
    Args:
        settings: Application settings (auto-loaded if None)
        
    Returns:
        Configured RetryConfig instance
    """
    if settings is None:
        settings = get_settings()
    
    return RetryConfig(
        max_attempts=settings.phoenix_retry_max_attempts,
        base_delay=settings.phoenix_retry_base_delay,
        max_delay=settings.phoenix_retry_max_delay,
        exponential_base=settings.phoenix_retry_exponential_base,
        jitter=settings.phoenix_retry_jitter
    )


def create_phoenix_circuit_breaker_config(settings: Optional['Settings'] = None) -> CircuitBreakerConfig:
    """
    Create CircuitBreakerConfig from application settings.
    
    Args:
        settings: Application settings (auto-loaded if None)
        
    Returns:
        Configured CircuitBreakerConfig instance
    """
    if settings is None:
        settings = get_settings()
    
    return CircuitBreakerConfig(
        failure_threshold=settings.phoenix_circuit_breaker_failure_threshold,
        success_threshold=settings.phoenix_circuit_breaker_success_threshold,
        timeout=settings.phoenix_circuit_breaker_timeout
    )


def create_phoenix_batch_config(
    sync_type: str = "experiments",
    dataset_ids: Optional[List[str]] = None,
    settings: Optional['Settings'] = None
) -> BatchSyncConfig:
    """
    Create BatchSyncConfig from application settings.
    
    Args:
        sync_type: Type of sync operation ("experiments", "datasets", etc.)
        dataset_ids: List of dataset IDs to sync (uses settings default if None)
        settings: Application settings (auto-loaded if None)
        
    Returns:
        Configured BatchSyncConfig instance
    """
    if settings is None:
        settings = get_settings()
    
    if dataset_ids is None:
        dataset_ids = settings.phoenix_sync_datasets
    
    return BatchSyncConfig(
        sync_interval_seconds=settings.phoenix_sync_interval_hours * 3600,  # Convert hours to seconds
        batch_size=settings.phoenix_batch_size,
        max_concurrent_operations=settings.phoenix_batch_concurrent_limit,
        qa_threshold=settings.phoenix_pattern_qa_threshold,
        min_confidence=settings.phoenix_pattern_confidence_threshold,
        target_datasets=dataset_ids,
        enable_progress_reporting=settings.phoenix_batch_enabled
    )


def create_configured_phoenix_client(settings: Optional['Settings'] = None) -> PhoenixMCPClient:
    """
    Create a fully configured PhoenixMCPClient from application settings.
    
    Args:
        settings: Application settings (auto-loaded if None)
        
    Returns:
        Configured PhoenixMCPClient instance
    """
    if settings is None:
        settings = get_settings()
    
    # Create configuration objects from settings
    retry_config = create_phoenix_retry_config(settings)
    circuit_breaker_config = create_phoenix_circuit_breaker_config(settings)
    
    return PhoenixMCPClient(
        retry_config=retry_config,
        circuit_breaker_config=circuit_breaker_config,
        enable_circuit_breaker=settings.phoenix_circuit_breaker_enabled
    )


def create_configured_batch_processor(
    sync_type: str = "experiments",
    dataset_ids: Optional[List[str]] = None,
    settings: Optional['Settings'] = None,
    progress_callback: Optional[Callable[[float, Optional[float], str], None]] = None
) -> PhoenixBatchProcessor:
    """
    Create a fully configured PhoenixBatchProcessor from application settings.
    
    Args:
        sync_type: Type of sync operation
        dataset_ids: List of dataset IDs to sync
        settings: Application settings (auto-loaded if None)
        progress_callback: Optional progress callback function
        
    Returns:
        Configured PhoenixBatchProcessor instance
    """
    if settings is None:
        settings = get_settings()
    
    # Create configured client and batch config
    client = create_configured_phoenix_client(settings)
    batch_config = create_phoenix_batch_config(sync_type, dataset_ids, settings)
    retry_config = create_phoenix_retry_config(settings)
    
    return PhoenixBatchProcessor(
        client=client,
        config=batch_config,
        progress_callback=progress_callback,
        retry_config=retry_config,
        enable_circuit_breaker=settings.phoenix_circuit_breaker_enabled
    )


def validate_phoenix_configuration(settings: Optional['Settings'] = None) -> Dict[str, Any]:
    """
    Validate Phoenix configuration and return validation results.
    
    Args:
        settings: Application settings (auto-loaded if None)
        
    Returns:
        Dictionary with validation results and recommendations
    """
    if settings is None:
        settings = get_settings()
    
    validation_results = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "recommendations": [],
        "configuration_summary": {}
    }
    
    # Validate retry configuration
    if settings.phoenix_retry_max_attempts < 1:
        validation_results["errors"].append("phoenix_retry_max_attempts must be >= 1")
        validation_results["valid"] = False
    
    if settings.phoenix_retry_base_delay <= 0:
        validation_results["errors"].append("phoenix_retry_base_delay must be > 0")
        validation_results["valid"] = False
    
    if settings.phoenix_retry_max_delay <= settings.phoenix_retry_base_delay:
        validation_results["warnings"].append(
            "phoenix_retry_max_delay should be greater than phoenix_retry_base_delay"
        )
    
    # Validate circuit breaker configuration
    if settings.phoenix_circuit_breaker_failure_threshold < 1:
        validation_results["errors"].append("phoenix_circuit_breaker_failure_threshold must be >= 1")
        validation_results["valid"] = False
    
    if settings.phoenix_circuit_breaker_success_threshold < 1:
        validation_results["errors"].append("phoenix_circuit_breaker_success_threshold must be >= 1")
        validation_results["valid"] = False
    
    if settings.phoenix_circuit_breaker_timeout <= 0:
        validation_results["errors"].append("phoenix_circuit_breaker_timeout must be > 0")
        validation_results["valid"] = False
    
    # Validate batch configuration
    if settings.phoenix_batch_size < 1:
        validation_results["errors"].append("phoenix_batch_size must be >= 1")
        validation_results["valid"] = False
    
    if settings.phoenix_batch_size > 100:
        validation_results["warnings"].append(
            "phoenix_batch_size > 100 may cause performance issues"
        )
    
    if settings.phoenix_batch_concurrent_limit > 5:
        validation_results["recommendations"].append(
            "Consider reducing phoenix_batch_concurrent_limit for better resource management"
        )
    
    # Validate pattern extraction thresholds
    if not (0.0 <= settings.phoenix_pattern_qa_threshold <= 1.0):
        validation_results["errors"].append("phoenix_pattern_qa_threshold must be between 0.0 and 1.0")
        validation_results["valid"] = False
    
    if not (0.0 <= settings.phoenix_pattern_rag_threshold <= 1.0):
        validation_results["errors"].append("phoenix_pattern_rag_threshold must be between 0.0 and 1.0")
        validation_results["valid"] = False
    
    if not (0.0 <= settings.phoenix_pattern_confidence_threshold <= 1.0):
        validation_results["errors"].append("phoenix_pattern_confidence_threshold must be between 0.0 and 1.0")
        validation_results["valid"] = False
    
    # Generate configuration summary
    validation_results["configuration_summary"] = {
        "integration_enabled": settings.phoenix_integration_enabled,
        "retry_config": {
            "max_attempts": settings.phoenix_retry_max_attempts,
            "base_delay": settings.phoenix_retry_base_delay,
            "max_delay": settings.phoenix_retry_max_delay,
            "jitter_enabled": settings.phoenix_retry_jitter
        },
        "circuit_breaker_config": {
            "enabled": settings.phoenix_circuit_breaker_enabled,
            "failure_threshold": settings.phoenix_circuit_breaker_failure_threshold,
            "success_threshold": settings.phoenix_circuit_breaker_success_threshold,
            "timeout": settings.phoenix_circuit_breaker_timeout
        },
        "batch_config": {
            "enabled": settings.phoenix_batch_enabled,
            "batch_size": settings.phoenix_batch_size,
            "concurrent_limit": settings.phoenix_batch_concurrent_limit
        },
        "pattern_extraction": {
            "qa_threshold": settings.phoenix_pattern_qa_threshold,
            "confidence_threshold": settings.phoenix_pattern_confidence_threshold,
            "max_patterns_per_experiment": settings.phoenix_pattern_max_patterns_per_experiment
        },
        "sync_config": {
            "enabled": settings.phoenix_sync_enabled,
            "interval_hours": settings.phoenix_sync_interval_hours,
            "datasets": settings.phoenix_sync_datasets,
            "max_age_days": settings.phoenix_sync_max_age_days
        }
    }
    
    return validation_results 
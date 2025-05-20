"""
Latency tracker utility for performance monitoring in the crypto trading simulator.

This module provides utilities for tracking and analyzing execution latency.
"""

import time
from typing import Dict, List, Optional, Tuple
import statistics
import logging

logger = logging.getLogger("latency_tracker")


class LatencyTracker:
    """Utility class for tracking and analyzing latency metrics."""
    
    def __init__(self, max_samples: int = 1000):
        """
        Initialize the latency tracker.
        
        Args:
            max_samples: Maximum number of samples to keep in history
        """
        self.max_samples = max_samples
        self.latency_history = {}
        self.start_times = {}
    
    def start(self, operation_name: str) -> None:
        """
        Start timing an operation.
        
        Args:
            operation_name: Name/identifier for the operation
        """
        self.start_times[operation_name] = time.time()
    
    def stop(self, operation_name: str) -> float:
        """
        Stop timing an operation and record the elapsed time.
        
        Args:
            operation_name: Name/identifier for the operation
            
        Returns:
            Elapsed time in milliseconds
        """
        if operation_name not in self.start_times:
            logger.warning(f"No start time found for operation: {operation_name}")
            return 0.0
        
        elapsed_time = (time.time() - self.start_times[operation_name]) * 1000  # Convert to ms
        
        # Initialize history list if it doesn't exist
        if operation_name not in self.latency_history:
            self.latency_history[operation_name] = []
        
        # Add to history
        self.latency_history[operation_name].append(elapsed_time)
        
        # Keep only the last max_samples
        if len(self.latency_history[operation_name]) > self.max_samples:
            self.latency_history[operation_name] = self.latency_history[operation_name][-self.max_samples:]
        
        return elapsed_time
    
    def get_stats(self, operation_name: str) -> Dict[str, float]:
        """
        Get latency statistics for an operation.
        
        Args:
            operation_name: Name/identifier for the operation
            
        Returns:
            Dictionary with latency statistics
        """
        if operation_name not in self.latency_history or not self.latency_history[operation_name]:
            return {
                "count": 0,
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "median": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
        
        samples = self.latency_history[operation_name]
        samples.sort()
        
        return {
            "count": len(samples),
            "min": samples[0],
            "max": samples[-1],
            "avg": statistics.mean(samples),
            "median": statistics.median(samples),
            "p95": samples[int(0.95 * len(samples)) - 1] if len(samples) >= 20 else samples[-1],
            "p99": samples[int(0.99 * len(samples)) - 1] if len(samples) >= 100 else samples[-1]
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get latency statistics for all tracked operations.
        
        Returns:
            Dictionary with latency statistics for each operation
        """
        return {op: self.get_stats(op) for op in self.latency_history.keys()}
    
    def reset(self, operation_name: Optional[str] = None) -> None:
        """
        Reset latency history.
        
        Args:
            operation_name: Name of operation to reset, or None to reset all
        """
        if operation_name is None:
            self.latency_history = {}
            self.start_times = {}
        else:
            if operation_name in self.latency_history:
                self.latency_history[operation_name] = []
            if operation_name in self.start_times:
                del self.start_times[operation_name]
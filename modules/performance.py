# modules/performance.py
"""
Performance Optimization Module for AURA

Provides performance enhancements including:
- Connection pooling for API calls
- Image compression and caching
- Parallel processing utilities
- Performance monitoring and metrics collection
"""

import logging
import time
import threading
import asyncio
import concurrent.futures
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import hashlib
import io
import base64
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image
import numpy as np
from collections import defaultdict, deque
import psutil
import gc

from config import (
    VISION_API_BASE,
    REASONING_API_BASE,
    VISION_API_TIMEOUT,
    REASONING_API_TIMEOUT,
    SCREENSHOT_QUALITY,
    MAX_SCREENSHOT_SIZE
)

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    timestamp: float = field(default_factory=time.time)
    operation: str = ""
    duration: float = 0.0
    success: bool = True
    error_message: str = ""
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    cache_hit: bool = False
    parallel_execution: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HybridPerformanceMetrics:
    """Performance metrics for hybrid execution paths."""
    timestamp: float = field(default_factory=time.time)
    command: str = ""
    path_used: str = ""  # 'fast' or 'slow'
    total_execution_time: float = 0.0
    element_detection_time: float = 0.0
    action_execution_time: float = 0.0
    success: bool = True
    fallback_triggered: bool = False
    app_name: Optional[str] = None
    element_found: bool = False
    error_message: str = ""
    accessibility_api_available: bool = True
    vision_model_used: bool = False
    reasoning_model_used: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheEntry:
    """Cache entry with expiration and metadata."""
    data: Any
    timestamp: float
    expiry_time: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    size_bytes: int = 0


class ConnectionPool:
    """HTTP connection pool with retry logic and session management."""
    
    def __init__(self, max_connections: int = 10, max_retries: int = 3):
        """
        Initialize connection pool.
        
        Args:
            max_connections: Maximum number of connections per host
            max_retries: Maximum number of retry attempts
        """
        self.max_connections = max_connections
        self.max_retries = max_retries
        self.sessions = {}
        self.session_lock = threading.Lock()
        
        # Configure retry strategy
        self.retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        logger.info(f"Connection pool initialized with {max_connections} max connections")
    
    def get_session(self, base_url: str) -> requests.Session:
        """
        Get or create a session for the given base URL.
        
        Args:
            base_url: Base URL for the session
            
        Returns:
            Configured requests session
        """
        with self.session_lock:
            if base_url not in self.sessions:
                session = requests.Session()
                
                # Configure adapter with connection pooling
                adapter = HTTPAdapter(
                    pool_connections=self.max_connections,
                    pool_maxsize=self.max_connections,
                    max_retries=self.retry_strategy
                )
                
                session.mount("http://", adapter)
                session.mount("https://", adapter)
                
                # Set default headers
                session.headers.update({
                    'User-Agent': 'AURA/1.0.0',
                    'Connection': 'keep-alive'
                })
                
                self.sessions[base_url] = session
                logger.debug(f"Created new session for {base_url}")
            
            return self.sessions[base_url]
    
    def close_all_sessions(self) -> None:
        """Close all active sessions."""
        with self.session_lock:
            for base_url, session in self.sessions.items():
                try:
                    session.close()
                    logger.debug(f"Closed session for {base_url}")
                except Exception as e:
                    logger.warning(f"Error closing session for {base_url}: {e}")
            
            self.sessions.clear()
            logger.info("All sessions closed")


class ImageCache:
    """Intelligent image caching with compression and deduplication."""
    
    def __init__(self, max_size_mb: int = 100, max_entries: int = 50):
        """
        Initialize image cache.
        
        Args:
            max_size_mb: Maximum cache size in megabytes
            max_entries: Maximum number of cache entries
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.current_size_bytes = 0
        self.hit_count = 0
        self.miss_count = 0
        
        logger.info(f"Image cache initialized: {max_size_mb}MB, {max_entries} entries")
    
    def _generate_cache_key(self, image_data: bytes, quality: int = None) -> str:
        """Generate cache key from image data."""
        hasher = hashlib.md5()
        hasher.update(image_data)
        if quality:
            hasher.update(str(quality).encode())
        return hasher.hexdigest()
    
    def _evict_lru_entries(self, required_space: int) -> None:
        """Evict least recently used entries to make space."""
        if not self.cache:
            return
        
        # Sort by last access time (oldest first)
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].last_access
        )
        
        freed_space = 0
        entries_removed = 0
        
        for key, entry in sorted_entries:
            if freed_space >= required_space and len(self.cache) <= self.max_entries:
                break
            
            self.current_size_bytes -= entry.size_bytes
            del self.cache[key]
            freed_space += entry.size_bytes
            entries_removed += 1
        
        logger.debug(f"Evicted {entries_removed} cache entries, freed {freed_space} bytes")
    
    def get_compressed_image(self, image_data: bytes, quality: int = SCREENSHOT_QUALITY) -> Optional[str]:
        """
        Get compressed image from cache or compress and cache it.
        
        Args:
            image_data: Raw image data
            quality: JPEG compression quality (1-100)
            
        Returns:
            Base64 encoded compressed image or None if error
        """
        cache_key = self._generate_cache_key(image_data, quality)
        
        with self.cache_lock:
            # Check cache first
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                
                # Check if entry is still valid (not expired)
                if time.time() < entry.expiry_time:
                    entry.access_count += 1
                    entry.last_access = time.time()
                    self.hit_count += 1
                    logger.debug(f"Cache hit for image key {cache_key[:8]}...")
                    return entry.data
                else:
                    # Remove expired entry
                    self.current_size_bytes -= entry.size_bytes
                    del self.cache[cache_key]
            
            self.miss_count += 1
        
        # Compress image
        try:
            compressed_data = self._compress_image(image_data, quality)
            if not compressed_data:
                return None
            
            # Calculate size and check if we need to evict entries
            entry_size = len(compressed_data)
            
            with self.cache_lock:
                # Evict entries if necessary
                if (self.current_size_bytes + entry_size > self.max_size_bytes or 
                    len(self.cache) >= self.max_entries):
                    self._evict_lru_entries(entry_size)
                
                # Add to cache
                cache_entry = CacheEntry(
                    data=compressed_data,
                    timestamp=time.time(),
                    expiry_time=time.time() + 300,  # 5 minute expiry
                    size_bytes=entry_size
                )
                
                self.cache[cache_key] = cache_entry
                self.current_size_bytes += entry_size
                
                logger.debug(f"Cached compressed image: {entry_size} bytes, key {cache_key[:8]}...")
            
            return compressed_data
            
        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            return None
    
    def _compress_image(self, image_data: bytes, quality: int) -> Optional[str]:
        """
        Compress image data to base64 JPEG.
        
        Args:
            image_data: Raw image data
            quality: JPEG compression quality
            
        Returns:
            Base64 encoded compressed image
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            if image.width > MAX_SCREENSHOT_SIZE or image.height > MAX_SCREENSHOT_SIZE:
                ratio = min(MAX_SCREENSHOT_SIZE / image.width, MAX_SCREENSHOT_SIZE / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Compress to JPEG
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            compressed_bytes = buffer.getvalue()
            
            # Encode to base64
            base64_string = base64.b64encode(compressed_bytes).decode('utf-8')
            
            return base64_string
            
        except Exception as e:
            logger.error(f"Image compression error: {e}")
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.cache_lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'entries': len(self.cache),
                'size_mb': self.current_size_bytes / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate_percent': hit_rate,
                'total_requests': total_requests
            }
    
    def clear_cache(self) -> None:
        """Clear all cache entries."""
        with self.cache_lock:
            self.cache.clear()
            self.current_size_bytes = 0
            logger.info("Image cache cleared")


class ParallelProcessor:
    """Parallel processing utilities for AURA operations."""
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize parallel processor.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.max_workers = max_workers
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
        self.active_tasks = {}
        self.task_lock = threading.Lock()
        
        logger.info(f"Parallel processor initialized with {max_workers} workers")
    
    def execute_parallel_io(self, tasks: List[Tuple[Callable, tuple, dict]]) -> List[Any]:
        """
        Execute I/O bound tasks in parallel.
        
        Args:
            tasks: List of (function, args, kwargs) tuples
            
        Returns:
            List of results in the same order as tasks
        """
        if not tasks:
            return []
        
        start_time = time.time()
        
        try:
            # Submit all tasks
            future_to_index = {}
            for i, (func, args, kwargs) in enumerate(tasks):
                future = self.thread_pool.submit(func, *args, **kwargs)
                future_to_index[future] = i
            
            # Collect results
            results = [None] * len(tasks)
            completed = 0
            
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                    completed += 1
                except Exception as e:
                    logger.error(f"Parallel task {index} failed: {e}")
                    results[index] = None
            
            duration = time.time() - start_time
            logger.debug(f"Parallel I/O execution completed: {completed}/{len(tasks)} tasks in {duration:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Parallel I/O execution failed: {e}")
            return [None] * len(tasks)
    
    def execute_parallel_cpu(self, tasks: List[Tuple[Callable, tuple, dict]]) -> List[Any]:
        """
        Execute CPU bound tasks in parallel using process pool.
        
        Args:
            tasks: List of (function, args, kwargs) tuples
            
        Returns:
            List of results in the same order as tasks
        """
        if not tasks:
            return []
        
        start_time = time.time()
        
        try:
            # Submit all tasks
            future_to_index = {}
            for i, (func, args, kwargs) in enumerate(tasks):
                future = self.process_pool.submit(func, *args, **kwargs)
                future_to_index[future] = i
            
            # Collect results
            results = [None] * len(tasks)
            completed = 0
            
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                    completed += 1
                except Exception as e:
                    logger.error(f"Parallel CPU task {index} failed: {e}")
                    results[index] = None
            
            duration = time.time() - start_time
            logger.debug(f"Parallel CPU execution completed: {completed}/{len(tasks)} tasks in {duration:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Parallel CPU execution failed: {e}")
            return [None] * len(tasks)
    
    def shutdown(self) -> None:
        """Shutdown all thread and process pools."""
        try:
            self.thread_pool.shutdown(wait=True)
            self.process_pool.shutdown(wait=True)
            logger.info("Parallel processor shutdown completed")
        except Exception as e:
            logger.error(f"Error shutting down parallel processor: {e}")


class HybridPerformanceMonitor:
    """Performance monitoring specifically for hybrid execution paths."""
    
    def __init__(self, max_metrics: int = 500):
        """
        Initialize hybrid performance monitor.
        
        Args:
            max_metrics: Maximum number of hybrid metrics to keep in memory
        """
        self.max_metrics = max_metrics
        self.hybrid_metrics = deque(maxlen=max_metrics)
        self.hybrid_lock = threading.Lock()
        
        # Path-specific statistics
        self.path_stats = {
            'fast': {
                'count': 0,
                'success_count': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0,
                'min_duration': float('inf'),
                'max_duration': 0.0,
                'fallback_count': 0
            },
            'slow': {
                'count': 0,
                'success_count': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0,
                'min_duration': float('inf'),
                'max_duration': 0.0,
                'fallback_count': 0
            }
        }
        
        # Application-specific statistics
        self.app_stats = defaultdict(lambda: {
            'fast_path_success_rate': 0.0,
            'fast_path_attempts': 0,
            'fast_path_successes': 0,
            'avg_fast_duration': 0.0,
            'avg_slow_duration': 0.0
        })
        
        logger.info(f"Hybrid performance monitor initialized with {max_metrics} max metrics")
    
    def record_hybrid_metric(self, metric: HybridPerformanceMetrics) -> None:
        """
        Record a hybrid performance metric.
        
        Args:
            metric: Hybrid performance metric to record
        """
        with self.hybrid_lock:
            self.hybrid_metrics.append(metric)
            
            # Update path statistics
            path = metric.path_used
            if path in self.path_stats:
                stats = self.path_stats[path]
                stats['count'] += 1
                stats['total_duration'] += metric.total_execution_time
                
                if metric.success:
                    stats['success_count'] += 1
                
                if metric.fallback_triggered:
                    stats['fallback_count'] += 1
                
                # Update duration statistics
                stats['avg_duration'] = stats['total_duration'] / stats['count']
                stats['min_duration'] = min(stats['min_duration'], metric.total_execution_time)
                stats['max_duration'] = max(stats['max_duration'], metric.total_execution_time)
            
            # Update application statistics
            if metric.app_name:
                app_stats = self.app_stats[metric.app_name]
                
                if metric.path_used == 'fast':
                    app_stats['fast_path_attempts'] += 1
                    if metric.success and not metric.fallback_triggered:
                        app_stats['fast_path_successes'] += 1
                    
                    # Update success rate
                    app_stats['fast_path_success_rate'] = (
                        app_stats['fast_path_successes'] / app_stats['fast_path_attempts'] * 100
                    )
                    
                    # Update average durations
                    fast_metrics = [m for m in self.hybrid_metrics 
                                  if m.app_name == metric.app_name and m.path_used == 'fast']
                    if fast_metrics:
                        app_stats['avg_fast_duration'] = sum(m.total_execution_time for m in fast_metrics) / len(fast_metrics)
                
                elif metric.path_used == 'slow':
                    slow_metrics = [m for m in self.hybrid_metrics 
                                  if m.app_name == metric.app_name and m.path_used == 'slow']
                    if slow_metrics:
                        app_stats['avg_slow_duration'] = sum(m.total_execution_time for m in slow_metrics) / len(slow_metrics)
    
    def get_hybrid_stats(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get hybrid performance statistics for the specified time window.
        
        Args:
            time_window_minutes: Time window in minutes
            
        Returns:
            Hybrid performance statistics dictionary
        """
        cutoff_time = time.time() - (time_window_minutes * 60)
        
        with self.hybrid_lock:
            # Filter metrics within time window
            recent_metrics = [m for m in self.hybrid_metrics if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return {
                    'time_window_minutes': time_window_minutes,
                    'total_commands': 0,
                    'fast_path_usage': 0.0,
                    'slow_path_usage': 0.0,
                    'overall_success_rate': 0.0,
                    'fallback_rate': 0.0,
                    'avg_fast_duration': 0.0,
                    'avg_slow_duration': 0.0,
                    'path_stats': self.path_stats.copy(),
                    'app_stats': dict(self.app_stats)
                }
            
            # Calculate statistics
            total_commands = len(recent_metrics)
            fast_path_commands = [m for m in recent_metrics if m.path_used == 'fast']
            slow_path_commands = [m for m in recent_metrics if m.path_used == 'slow']
            successful_commands = [m for m in recent_metrics if m.success]
            fallback_commands = [m for m in recent_metrics if m.fallback_triggered]
            
            fast_path_usage = (len(fast_path_commands) / total_commands * 100) if total_commands > 0 else 0
            slow_path_usage = (len(slow_path_commands) / total_commands * 100) if total_commands > 0 else 0
            overall_success_rate = (len(successful_commands) / total_commands * 100) if total_commands > 0 else 0
            fallback_rate = (len(fallback_commands) / total_commands * 100) if total_commands > 0 else 0
            
            avg_fast_duration = (sum(m.total_execution_time for m in fast_path_commands) / 
                               len(fast_path_commands)) if fast_path_commands else 0
            avg_slow_duration = (sum(m.total_execution_time for m in slow_path_commands) / 
                               len(slow_path_commands)) if slow_path_commands else 0
            
            return {
                'time_window_minutes': time_window_minutes,
                'total_commands': total_commands,
                'fast_path_usage_percent': fast_path_usage,
                'slow_path_usage_percent': slow_path_usage,
                'overall_success_rate_percent': overall_success_rate,
                'fallback_rate_percent': fallback_rate,
                'avg_fast_duration_seconds': avg_fast_duration,
                'avg_slow_duration_seconds': avg_slow_duration,
                'performance_improvement': ((avg_slow_duration - avg_fast_duration) / avg_slow_duration * 100) 
                                         if avg_slow_duration > 0 else 0,
                'path_stats': self.path_stats.copy(),
                'app_stats': dict(self.app_stats)
            }


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self, max_metrics: int = 1000):
        """
        Initialize performance monitor.
        
        Args:
            max_metrics: Maximum number of metrics to keep in memory
        """
        self.max_metrics = max_metrics
        self.metrics = deque(maxlen=max_metrics)
        self.metrics_lock = threading.Lock()
        self.operation_stats = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0.0,
            'success_count': 0,
            'error_count': 0,
            'avg_duration': 0.0,
            'min_duration': float('inf'),
            'max_duration': 0.0
        })
        
        # System monitoring
        self.system_metrics = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_mb': 0.0,
            'disk_usage_percent': 0.0,
            'network_io': {'bytes_sent': 0, 'bytes_recv': 0},
            'last_update': time.time()
        }
        
        # Start system monitoring thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._system_monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Performance monitor initialized with {max_metrics} max metrics")
    
    def record_metric(self, metric: PerformanceMetrics) -> None:
        """
        Record a performance metric.
        
        Args:
            metric: Performance metric to record
        """
        with self.metrics_lock:
            self.metrics.append(metric)
            
            # Update operation statistics
            stats = self.operation_stats[metric.operation]
            stats['count'] += 1
            stats['total_duration'] += metric.duration
            
            if metric.success:
                stats['success_count'] += 1
            else:
                stats['error_count'] += 1
            
            # Update duration statistics
            stats['avg_duration'] = stats['total_duration'] / stats['count']
            stats['min_duration'] = min(stats['min_duration'], metric.duration)
            stats['max_duration'] = max(stats['max_duration'], metric.duration)
    
    def _system_monitoring_loop(self) -> None:
        """System monitoring loop that runs in background."""
        while self.monitoring_active:
            try:
                # Update system metrics every 30 seconds
                time.sleep(30.0)
                
                if not self.monitoring_active:
                    break
                
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('.')
                network = psutil.net_io_counters()
                
                self.system_metrics.update({
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_mb': memory.used / (1024 * 1024),
                    'disk_usage_percent': disk.percent,
                    'network_io': {
                        'bytes_sent': network.bytes_sent,
                        'bytes_recv': network.bytes_recv
                    },
                    'last_update': time.time()
                })
                
                # Trigger garbage collection periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    collected = gc.collect()
                    logger.debug(f"Garbage collection: {collected} objects collected")
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(10.0)  # Brief pause before retrying
    
    def get_operation_stats(self, operation: str = None) -> Dict[str, Any]:
        """
        Get statistics for operations.
        
        Args:
            operation: Specific operation to get stats for (None for all)
            
        Returns:
            Dictionary of operation statistics
        """
        with self.metrics_lock:
            if operation:
                return dict(self.operation_stats.get(operation, {}))
            else:
                return {op: dict(stats) for op, stats in self.operation_stats.items()}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return self.system_metrics.copy()
    
    def get_performance_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get performance summary for the specified time window.
        
        Args:
            time_window_minutes: Time window in minutes
            
        Returns:
            Performance summary dictionary
        """
        cutoff_time = time.time() - (time_window_minutes * 60)
        
        with self.metrics_lock:
            # Filter metrics within time window
            recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return {
                    'time_window_minutes': time_window_minutes,
                    'total_operations': 0,
                    'success_rate': 0.0,
                    'avg_duration': 0.0,
                    'cache_hit_rate': 0.0,
                    'parallel_execution_rate': 0.0,
                    'system_metrics': self.get_system_metrics()
                }
            
            # Calculate summary statistics
            total_ops = len(recent_metrics)
            successful_ops = sum(1 for m in recent_metrics if m.success)
            cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
            parallel_ops = sum(1 for m in recent_metrics if m.parallel_execution)
            
            avg_duration = sum(m.duration for m in recent_metrics) / total_ops
            success_rate = (successful_ops / total_ops) * 100
            cache_hit_rate = (cache_hits / total_ops) * 100 if total_ops > 0 else 0
            parallel_rate = (parallel_ops / total_ops) * 100 if total_ops > 0 else 0
            
            # Group by operation type
            operation_breakdown = defaultdict(int)
            for metric in recent_metrics:
                operation_breakdown[metric.operation] += 1
            
            return {
                'time_window_minutes': time_window_minutes,
                'total_operations': total_ops,
                'successful_operations': successful_ops,
                'success_rate_percent': success_rate,
                'avg_duration_seconds': avg_duration,
                'cache_hit_rate_percent': cache_hit_rate,
                'parallel_execution_rate_percent': parallel_rate,
                'operation_breakdown': dict(operation_breakdown),
                'system_metrics': self.get_system_metrics()
            }
    
    def stop_monitoring(self) -> None:
        """Stop system monitoring."""
        self.monitoring_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        logger.info("Performance monitoring stopped")


# Global instances
connection_pool = ConnectionPool()
image_cache = ImageCache()
parallel_processor = ParallelProcessor()
performance_monitor = PerformanceMonitor()
hybrid_performance_monitor = HybridPerformanceMonitor()


def measure_performance(operation: str, include_system_metrics: bool = False):
    """
    Decorator to measure performance of functions.
    
    Args:
        operation: Name of the operation being measured
        include_system_metrics: Whether to include system metrics
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = 0
            start_cpu = 0
            
            if include_system_metrics:
                try:
                    process = psutil.Process()
                    start_memory = process.memory_info().rss / (1024 * 1024)
                    start_cpu = process.cpu_percent()
                except:
                    pass
            
            success = True
            error_message = ""
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration = time.time() - start_time
                
                # Calculate system metrics if requested
                memory_usage = 0
                cpu_percent = 0
                if include_system_metrics:
                    try:
                        process = psutil.Process()
                        memory_usage = process.memory_info().rss / (1024 * 1024)
                        cpu_percent = process.cpu_percent()
                    except:
                        pass
                
                # Create and record metric
                metric = PerformanceMetrics(
                    operation=operation,
                    duration=duration,
                    success=success,
                    error_message=error_message,
                    memory_usage_mb=memory_usage,
                    cpu_percent=cpu_percent,
                    metadata={
                        'function_name': func.__name__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )
                
                performance_monitor.record_metric(metric)
        
        return wrapper
    return decorator


def measure_fast_path_performance(command: str = "", app_name: str = None):
    """
    Decorator to measure performance of fast path operations.
    
    Args:
        command: User command being executed
        app_name: Name of the target application
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            element_detection_start = start_time
            
            success = True
            error_message = ""
            element_found = False
            fallback_triggered = False
            result = None
            
            try:
                result = func(*args, **kwargs)
                
                # Check if result indicates element was found
                if isinstance(result, dict):
                    element_found = result.get('element_found', False)
                    fallback_triggered = result.get('fallback_required', False)
                elif result is not None:
                    element_found = True
                
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                fallback_triggered = True
                raise
            finally:
                total_duration = time.time() - start_time
                
                # For fast path, element detection and action execution happen together
                element_detection_time = total_duration
                action_execution_time = 0.0
                
                # Create and record hybrid metric
                hybrid_metric = HybridPerformanceMetrics(
                    command=command or func.__name__,
                    path_used='fast',
                    total_execution_time=total_duration,
                    element_detection_time=element_detection_time,
                    action_execution_time=action_execution_time,
                    success=success,
                    fallback_triggered=fallback_triggered,
                    app_name=app_name,
                    element_found=element_found,
                    error_message=error_message,
                    accessibility_api_available=True,
                    vision_model_used=False,
                    reasoning_model_used=False,
                    metadata={
                        'function_name': func.__name__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )
                
                hybrid_performance_monitor.record_hybrid_metric(hybrid_metric)
        
        return wrapper
    return decorator


def measure_slow_path_performance(command: str = "", app_name: str = None):
    """
    Decorator to measure performance of slow path (vision-based) operations.
    
    Args:
        command: User command being executed
        app_name: Name of the target application
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            success = True
            error_message = ""
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                total_duration = time.time() - start_time
                
                # For slow path, we don't separate detection and execution times
                # as they're interleaved in the vision-reasoning workflow
                element_detection_time = total_duration * 0.7  # Estimate
                action_execution_time = total_duration * 0.3   # Estimate
                
                # Create and record hybrid metric
                hybrid_metric = HybridPerformanceMetrics(
                    command=command or func.__name__,
                    path_used='slow',
                    total_execution_time=total_duration,
                    element_detection_time=element_detection_time,
                    action_execution_time=action_execution_time,
                    success=success,
                    fallback_triggered=False,  # Slow path is the fallback
                    app_name=app_name,
                    element_found=success,  # If slow path succeeds, element was found
                    error_message=error_message,
                    accessibility_api_available=False,  # Slow path used when accessibility fails
                    vision_model_used=True,
                    reasoning_model_used=True,
                    metadata={
                        'function_name': func.__name__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )
                
                hybrid_performance_monitor.record_hybrid_metric(hybrid_metric)
        
        return wrapper
    return decorator


def cleanup_performance_resources():
    """Clean up all performance-related resources."""
    try:
        connection_pool.close_all_sessions()
        image_cache.clear_cache()
        parallel_processor.shutdown()
        performance_monitor.stop_monitoring()
        # Hybrid performance monitor doesn't need explicit cleanup as it's just data storage
        logger.info("Performance resources cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up performance resources: {e}")
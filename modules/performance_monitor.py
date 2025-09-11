"""
Performance Monitor Module for AURA

This module provides comprehensive performance monitoring, metrics tracking,
and optimization for the explain selected text feature and other AURA operations.
It includes caching strategies, performance alerting, and detailed analytics.
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import contextmanager
import json
import statistics
from datetime import datetime, timedelta


@dataclass
class PerformanceMetric:
    """Individual performance metric record."""
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def finish(self, success: bool = True, error_message: Optional[str] = None):
        """Mark the metric as finished and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and analysis."""
        return {
            'operation': self.operation,
            'duration_ms': self.duration_ms,
            'success': self.success,
            'error_message': self.error_message,
            'timestamp': self.start_time,
            'metadata': self.metadata
        }


@dataclass
class CacheEntry:
    """Cache entry with TTL and metadata."""
    key: str
    value: Any
    created_at: float
    ttl_seconds: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds
    
    def access(self) -> Any:
        """Access the cached value and update statistics."""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value


@dataclass
class PerformanceAlert:
    """Performance alert for threshold violations."""
    alert_type: str
    operation: str
    threshold_ms: float
    actual_ms: float
    timestamp: float
    severity: str  # 'warning', 'critical'
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'alert_type': self.alert_type,
            'operation': self.operation,
            'threshold_ms': self.threshold_ms,
            'actual_ms': self.actual_ms,
            'timestamp': self.timestamp,
            'severity': self.severity,
            'metadata': self.metadata
        }


class PerformanceCache:
    """High-performance cache with TTL and LRU eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0):
        """
        Initialize performance cache.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats['misses'] += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return None
            
            self._stats['hits'] += 1
            return entry.access()
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put value in cache."""
        with self._lock:
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            ttl = ttl or self.default_ttl
            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl_seconds=ttl
            )
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        lru_key = min(self._cache.keys(), 
                     key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_key]
        self._stats['evictions'] += 1
    
    def clear_expired(self) -> int:
        """Clear expired entries and return count."""
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
            self._stats['expirations'] += len(expired_keys)
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            hit_rate = self._stats['hits'] / max(1, self._stats['hits'] + self._stats['misses'])
            return {
                **self._stats,
                'size': len(self._cache),
                'hit_rate': hit_rate,
                'max_size': self.max_size
            }


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for AURA operations.
    
    Provides metrics tracking, caching strategies, performance alerting,
    and optimization recommendations for the explain selected text feature.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize performance monitor.
        
        Args:
            config: Configuration dictionary with monitoring settings
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration with defaults
        config = config or {}
        self.enabled = config.get('enabled', True)
        self.warning_threshold_ms = config.get('warning_threshold_ms', 1500)
        self.critical_threshold_ms = config.get('critical_threshold_ms', 3000)
        self.history_size = config.get('history_size', 100)
        self.cache_enabled = config.get('cache_enabled', True)
        self.alerting_enabled = config.get('alerting_enabled', True)
        
        # Performance metrics storage
        self._metrics: deque = deque(maxlen=self.history_size)
        self._metrics_lock = threading.RLock()
        
        # Operation-specific statistics
        self._operation_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'success_count': 0,
            'total_duration_ms': 0.0,
            'min_duration_ms': float('inf'),
            'max_duration_ms': 0.0,
            'recent_durations': deque(maxlen=20)
        })
        
        # Performance caches
        self.text_capture_cache = PerformanceCache(max_size=500, default_ttl=60.0)
        self.explanation_cache = PerformanceCache(max_size=200, default_ttl=300.0)
        self.accessibility_cache = PerformanceCache(max_size=1000, default_ttl=30.0)
        
        # Alert tracking
        self._alerts: deque = deque(maxlen=50)
        self._alert_callbacks: List[callable] = []
        
        # Background cleanup thread
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        
        if self.enabled:
            self._start_cleanup_thread()
            self.logger.info("Performance monitor initialized")
    
    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread."""
        def cleanup_worker():
            while not self._stop_cleanup.wait(60):  # Run every minute
                try:
                    self._cleanup_expired_cache_entries()
                except Exception as e:
                    self.logger.warning(f"Cache cleanup error: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_expired_cache_entries(self) -> None:
        """Clean up expired cache entries."""
        total_expired = 0
        total_expired += self.text_capture_cache.clear_expired()
        total_expired += self.explanation_cache.clear_expired()
        total_expired += self.accessibility_cache.clear_expired()
        
        if total_expired > 0:
            self.logger.debug(f"Cleaned up {total_expired} expired cache entries")
    
    @contextmanager
    def track_operation(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for tracking operation performance.
        
        Args:
            operation: Operation name
            metadata: Additional metadata to track
            
        Usage:
            with monitor.track_operation('text_capture') as metric:
                # perform operation
                pass
        """
        if not self.enabled:
            yield None
            return
        
        metric = PerformanceMetric(
            operation=operation,
            start_time=time.time(),
            metadata=metadata or {}
        )
        
        try:
            yield metric
            metric.finish(success=True)
        except Exception as e:
            metric.finish(success=False, error_message=str(e))
            raise
        finally:
            self._record_metric(metric)
    
    def _record_metric(self, metric: PerformanceMetric) -> None:
        """Record a performance metric."""
        with self._metrics_lock:
            self._metrics.append(metric)
            
            # Update operation statistics
            stats = self._operation_stats[metric.operation]
            stats['count'] += 1
            if metric.success:
                stats['success_count'] += 1
            
            if metric.duration_ms is not None:
                stats['total_duration_ms'] += metric.duration_ms
                stats['min_duration_ms'] = min(stats['min_duration_ms'], metric.duration_ms)
                stats['max_duration_ms'] = max(stats['max_duration_ms'], metric.duration_ms)
                stats['recent_durations'].append(metric.duration_ms)
                
                # Check for performance alerts
                self._check_performance_alerts(metric)
        
        # Log performance information
        if metric.duration_ms is not None:
            if metric.success:
                self.logger.debug(f"Operation '{metric.operation}' completed in {metric.duration_ms:.1f}ms")
            else:
                self.logger.warning(f"Operation '{metric.operation}' failed after {metric.duration_ms:.1f}ms: {metric.error_message}")
    
    def _check_performance_alerts(self, metric: PerformanceMetric) -> None:
        """Check if metric triggers performance alerts."""
        if not self.alerting_enabled or metric.duration_ms is None:
            return
        
        alert = None
        
        if metric.duration_ms > self.critical_threshold_ms:
            alert = PerformanceAlert(
                alert_type='duration_critical',
                operation=metric.operation,
                threshold_ms=self.critical_threshold_ms,
                actual_ms=metric.duration_ms,
                timestamp=time.time(),
                severity='critical',
                metadata=metric.metadata
            )
        elif metric.duration_ms > self.warning_threshold_ms:
            alert = PerformanceAlert(
                alert_type='duration_warning',
                operation=metric.operation,
                threshold_ms=self.warning_threshold_ms,
                actual_ms=metric.duration_ms,
                timestamp=time.time(),
                severity='warning',
                metadata=metric.metadata
            )
        
        if alert:
            self._alerts.append(alert)
            self._trigger_alert_callbacks(alert)
            
            # Log alert
            self.logger.warning(f"Performance alert: {alert.operation} took {alert.actual_ms:.1f}ms "
                              f"(threshold: {alert.threshold_ms:.1f}ms)")
    
    def _trigger_alert_callbacks(self, alert: PerformanceAlert) -> None:
        """Trigger registered alert callbacks."""
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def add_alert_callback(self, callback: callable) -> None:
        """Add callback for performance alerts."""
        self._alert_callbacks.append(callback)
    
    def get_operation_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance statistics for operations.
        
        Args:
            operation: Specific operation name, or None for all operations
            
        Returns:
            Dictionary with performance statistics
        """
        with self._metrics_lock:
            if operation:
                if operation not in self._operation_stats:
                    return {}
                
                stats = self._operation_stats[operation].copy()
                if stats['count'] > 0:
                    stats['success_rate'] = stats['success_count'] / stats['count']
                    stats['avg_duration_ms'] = stats['total_duration_ms'] / stats['count']
                    
                    if stats['recent_durations']:
                        stats['recent_avg_ms'] = statistics.mean(stats['recent_durations'])
                        stats['recent_median_ms'] = statistics.median(stats['recent_durations'])
                
                return stats
            else:
                # Return all operation statistics
                result = {}
                for op_name, stats in self._operation_stats.items():
                    result[op_name] = self.get_operation_stats(op_name)
                return result
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        return {
            'text_capture': self.text_capture_cache.get_stats(),
            'explanation': self.explanation_cache.get_stats(),
            'accessibility': self.accessibility_cache.get_stats()
        }
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent performance alerts."""
        return [alert.to_dict() for alert in list(self._alerts)[-limit:]]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._metrics_lock:
            total_operations = len(self._metrics)
            successful_operations = sum(1 for m in self._metrics if m.success)
            
            if total_operations > 0:
                success_rate = successful_operations / total_operations
                durations = [m.duration_ms for m in self._metrics if m.duration_ms is not None]
                
                if durations:
                    avg_duration = statistics.mean(durations)
                    median_duration = statistics.median(durations)
                    p95_duration = statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations)
                else:
                    avg_duration = median_duration = p95_duration = 0.0
            else:
                success_rate = avg_duration = median_duration = p95_duration = 0.0
            
            return {
                'total_operations': total_operations,
                'success_rate': success_rate,
                'avg_duration_ms': avg_duration,
                'median_duration_ms': median_duration,
                'p95_duration_ms': p95_duration,
                'recent_alerts': len(self._alerts),
                'cache_stats': self.get_cache_stats(),
                'operation_stats': self.get_operation_stats()
            }
    
    def optimize_text_capture_performance(self) -> Dict[str, Any]:
        """
        Analyze and provide optimization recommendations for text capture.
        
        Returns:
            Dictionary with optimization recommendations
        """
        stats = self.get_operation_stats('text_capture')
        recommendations = []
        
        if not stats:
            return {'recommendations': ['No text capture performance data available']}
        
        # Analyze success rate
        success_rate = stats.get('success_rate', 0.0)
        if success_rate < 0.9:
            recommendations.append(f"Text capture success rate is low ({success_rate:.1%}). "
                                 "Consider improving fallback mechanisms.")
        
        # Analyze performance
        avg_duration = stats.get('avg_duration_ms', 0.0)
        if avg_duration > 1000:
            recommendations.append(f"Text capture is slow (avg: {avg_duration:.0f}ms). "
                                 "Consider caching accessibility API connections.")
        
        # Analyze recent performance trends
        recent_durations = stats.get('recent_durations', [])
        if len(recent_durations) >= 5:
            recent_avg = statistics.mean(recent_durations)
            if recent_avg > avg_duration * 1.2:
                recommendations.append("Recent text capture performance has degraded. "
                                     "Check for system resource issues.")
        
        # Cache effectiveness
        cache_stats = self.text_capture_cache.get_stats()
        hit_rate = cache_stats.get('hit_rate', 0.0)
        if hit_rate < 0.3:
            recommendations.append(f"Text capture cache hit rate is low ({hit_rate:.1%}). "
                                 "Consider adjusting cache TTL or improving cache keys.")
        
        return {
            'current_performance': stats,
            'cache_performance': cache_stats,
            'recommendations': recommendations or ['Text capture performance is optimal']
        }
    
    def optimize_explanation_performance(self) -> Dict[str, Any]:
        """
        Analyze and provide optimization recommendations for explanation generation.
        
        Returns:
            Dictionary with optimization recommendations
        """
        stats = self.get_operation_stats('explanation_generation')
        recommendations = []
        
        if not stats:
            return {'recommendations': ['No explanation generation performance data available']}
        
        # Analyze success rate
        success_rate = stats.get('success_rate', 0.0)
        if success_rate < 0.95:
            recommendations.append(f"Explanation generation success rate is low ({success_rate:.1%}). "
                                 "Review error handling and API reliability.")
        
        # Analyze performance
        avg_duration = stats.get('avg_duration_ms', 0.0)
        if avg_duration > 5000:
            recommendations.append(f"Explanation generation is slow (avg: {avg_duration:.0f}ms). "
                                 "Consider optimizing prompts or using faster models.")
        
        # Cache effectiveness
        cache_stats = self.explanation_cache.get_stats()
        hit_rate = cache_stats.get('hit_rate', 0.0)
        if hit_rate < 0.2:
            recommendations.append(f"Explanation cache hit rate is low ({hit_rate:.1%}). "
                                 "Consider caching similar explanations or improving cache keys.")
        
        return {
            'current_performance': stats,
            'cache_performance': cache_stats,
            'recommendations': recommendations or ['Explanation generation performance is optimal']
        }
    
    def shutdown(self) -> None:
        """Shutdown performance monitor and cleanup resources."""
        if self._cleanup_thread:
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)
        
        self.logger.info("Performance monitor shutdown complete")


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance."""
    global _performance_monitor
    
    if _performance_monitor is None:
        # Load configuration from config module
        try:
            from config import (
                PERFORMANCE_MONITORING_ENABLED,
                PERFORMANCE_WARNING_THRESHOLD,
                PERFORMANCE_HISTORY_SIZE
            )
            config = {
                'enabled': PERFORMANCE_MONITORING_ENABLED,
                'warning_threshold_ms': PERFORMANCE_WARNING_THRESHOLD,
                'history_size': PERFORMANCE_HISTORY_SIZE,
                'cache_enabled': True,
                'alerting_enabled': True
            }
        except ImportError:
            # Fallback configuration
            config = {
                'enabled': True,
                'warning_threshold_ms': 1500,
                'history_size': 100,
                'cache_enabled': True,
                'alerting_enabled': True
            }
        
        _performance_monitor = PerformanceMonitor(config)
    
    return _performance_monitor
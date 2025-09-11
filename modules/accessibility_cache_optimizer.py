"""
Accessibility Cache Optimizer for AURA

This module provides advanced caching strategies and optimizations for
accessibility API calls to improve performance of the explain selected text
feature and other accessibility operations.
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
import hashlib
import weakref


@dataclass
class AccessibilityConnection:
    """Cached accessibility API connection."""
    app_name: str
    app_pid: int
    connection: Any
    created_at: float
    last_used: float
    use_count: int = 0
    
    def is_stale(self, max_age: float = 300.0) -> bool:
        """Check if connection is stale."""
        return time.time() - self.last_used > max_age
    
    def use(self) -> Any:
        """Use the connection and update statistics."""
        self.last_used = time.time()
        self.use_count += 1
        return self.connection


@dataclass
class ElementCache:
    """Cached accessibility element data."""
    element_id: str
    element_data: Dict[str, Any]
    app_name: str
    cached_at: float
    ttl: float
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.cached_at > self.ttl
    
    def access(self) -> Dict[str, Any]:
        """Access cached data and update statistics."""
        self.access_count += 1
        return self.element_data


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class AccessibilityCacheOptimizer:
    """
    Advanced caching system for accessibility API operations.
    
    Provides connection pooling, element caching, and predictive prefetching
    to optimize performance of accessibility operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize accessibility cache optimizer.
        
        Args:
            config: Configuration dictionary with caching settings
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration with defaults
        config = config or {}
        self.enabled = config.get('enabled', True)
        self.connection_pool_size = config.get('connection_pool_size', 10)
        self.element_cache_size = config.get('element_cache_size', 1000)
        self.connection_ttl = config.get('connection_ttl', 300.0)  # 5 minutes
        self.element_ttl = config.get('element_ttl', 30.0)  # 30 seconds
        self.prefetch_enabled = config.get('prefetch_enabled', True)
        
        # Connection pool
        self._connections: Dict[str, AccessibilityConnection] = {}
        self._connection_lock = threading.RLock()
        
        # Element cache
        self._element_cache: Dict[str, ElementCache] = {}
        self._element_cache_lock = threading.RLock()
        
        # Cache statistics
        self._connection_stats = CacheStats()
        self._element_stats = CacheStats()
        
        # Prefetch queue and worker
        self._prefetch_queue: deque = deque()
        self._prefetch_worker = None
        self._stop_prefetch = threading.Event()
        
        # Cleanup thread
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        
        # Performance tracking
        self._performance_history: deque = deque(maxlen=100)
        
        if self.enabled:
            self._start_background_workers()
            self.logger.info("Accessibility cache optimizer initialized")
    
    def _start_background_workers(self) -> None:
        """Start background worker threads."""
        # Start prefetch worker
        if self.prefetch_enabled:
            def prefetch_worker():
                while not self._stop_prefetch.wait(1.0):
                    try:
                        self._process_prefetch_queue()
                    except Exception as e:
                        self.logger.warning(f"Prefetch worker error: {e}")
            
            self._prefetch_worker = threading.Thread(target=prefetch_worker, daemon=True)
            self._prefetch_worker.start()
        
        # Start cleanup worker
        def cleanup_worker():
            while not self._stop_cleanup.wait(60.0):  # Run every minute
                try:
                    self._cleanup_expired_entries()
                except Exception as e:
                    self.logger.warning(f"Cleanup worker error: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def get_accessibility_connection(self, app_name: str, app_pid: int) -> Optional[Any]:
        """
        Get cached accessibility connection for an application.
        
        Args:
            app_name: Application name
            app_pid: Application process ID
            
        Returns:
            Cached connection if available, None otherwise
        """
        if not self.enabled:
            return None
        
        connection_key = f"{app_name}_{app_pid}"
        
        with self._connection_lock:
            connection_entry = self._connections.get(connection_key)
            
            if connection_entry:
                if not connection_entry.is_stale(self.connection_ttl):
                    self._connection_stats.hits += 1
                    return connection_entry.use()
                else:
                    # Remove stale connection
                    del self._connections[connection_key]
                    self._connection_stats.expirations += 1
            
            self._connection_stats.misses += 1
            return None
    
    def cache_accessibility_connection(self, app_name: str, app_pid: int, connection: Any) -> None:
        """
        Cache an accessibility connection.
        
        Args:
            app_name: Application name
            app_pid: Application process ID
            connection: Accessibility connection to cache
        """
        if not self.enabled or not connection:
            return
        
        connection_key = f"{app_name}_{app_pid}"
        
        with self._connection_lock:
            # Evict oldest connection if pool is full
            if len(self._connections) >= self.connection_pool_size:
                self._evict_oldest_connection()
            
            # Cache new connection
            self._connections[connection_key] = AccessibilityConnection(
                app_name=app_name,
                app_pid=app_pid,
                connection=connection,
                created_at=time.time(),
                last_used=time.time()
            )
            
            self.logger.debug(f"Cached accessibility connection for {app_name} (PID: {app_pid})")
    
    def _evict_oldest_connection(self) -> None:
        """Evict the oldest connection from the pool."""
        if not self._connections:
            return
        
        oldest_key = min(self._connections.keys(), 
                        key=lambda k: self._connections[k].last_used)
        del self._connections[oldest_key]
        self._connection_stats.evictions += 1
    
    def get_cached_element(self, element_id: str, app_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached element data.
        
        Args:
            element_id: Unique element identifier
            app_name: Application name
            
        Returns:
            Cached element data if available, None otherwise
        """
        if not self.enabled:
            return None
        
        cache_key = f"{app_name}_{element_id}"
        
        with self._element_cache_lock:
            cache_entry = self._element_cache.get(cache_key)
            
            if cache_entry:
                if not cache_entry.is_expired():
                    self._element_stats.hits += 1
                    return cache_entry.access()
                else:
                    # Remove expired entry
                    del self._element_cache[cache_key]
                    self._element_stats.expirations += 1
            
            self._element_stats.misses += 1
            return None
    
    def cache_element(self, element_id: str, app_name: str, element_data: Dict[str, Any], 
                     ttl: Optional[float] = None) -> None:
        """
        Cache element data.
        
        Args:
            element_id: Unique element identifier
            app_name: Application name
            element_data: Element data to cache
            ttl: Time-to-live override
        """
        if not self.enabled or not element_data:
            return
        
        cache_key = f"{app_name}_{element_id}"
        ttl = ttl or self.element_ttl
        
        with self._element_cache_lock:
            # Evict oldest element if cache is full
            if len(self._element_cache) >= self.element_cache_size:
                self._evict_oldest_element()
            
            # Cache new element
            self._element_cache[cache_key] = ElementCache(
                element_id=element_id,
                element_data=element_data,
                app_name=app_name,
                cached_at=time.time(),
                ttl=ttl
            )
            
            self.logger.debug(f"Cached element {element_id} for {app_name}")
    
    def _evict_oldest_element(self) -> None:
        """Evict the oldest element from the cache."""
        if not self._element_cache:
            return
        
        oldest_key = min(self._element_cache.keys(),
                        key=lambda k: self._element_cache[k].cached_at)
        del self._element_cache[oldest_key]
        self._element_stats.evictions += 1
    
    def prefetch_common_elements(self, app_name: str, element_patterns: List[str]) -> None:
        """
        Queue common elements for prefetching.
        
        Args:
            app_name: Application name
            element_patterns: List of element patterns to prefetch
        """
        if not self.enabled or not self.prefetch_enabled:
            return
        
        for pattern in element_patterns:
            prefetch_task = {
                'type': 'element_prefetch',
                'app_name': app_name,
                'pattern': pattern,
                'queued_at': time.time()
            }
            self._prefetch_queue.append(prefetch_task)
        
        self.logger.debug(f"Queued {len(element_patterns)} elements for prefetch in {app_name}")
    
    def _process_prefetch_queue(self) -> None:
        """Process prefetch queue."""
        if not self._prefetch_queue:
            return
        
        # Process up to 5 items per cycle to avoid blocking
        for _ in range(min(5, len(self._prefetch_queue))):
            try:
                task = self._prefetch_queue.popleft()
                self._execute_prefetch_task(task)
            except IndexError:
                break
            except Exception as e:
                self.logger.warning(f"Prefetch task error: {e}")
    
    def _execute_prefetch_task(self, task: Dict[str, Any]) -> None:
        """Execute a prefetch task."""
        task_type = task.get('type')
        
        if task_type == 'element_prefetch':
            # This would integrate with the actual accessibility module
            # to prefetch elements based on patterns
            app_name = task['app_name']
            pattern = task['pattern']
            
            # Placeholder for actual prefetch logic
            self.logger.debug(f"Prefetching elements matching '{pattern}' in {app_name}")
    
    def _cleanup_expired_entries(self) -> None:
        """Clean up expired cache entries."""
        current_time = time.time()
        
        # Clean up connections
        with self._connection_lock:
            expired_connections = [
                key for key, conn in self._connections.items()
                if conn.is_stale(self.connection_ttl)
            ]
            for key in expired_connections:
                del self._connections[key]
                self._connection_stats.expirations += 1
        
        # Clean up elements
        with self._element_cache_lock:
            expired_elements = [
                key for key, elem in self._element_cache.items()
                if elem.is_expired()
            ]
            for key in expired_elements:
                del self._element_cache[key]
                self._element_stats.expirations += 1
        
        if expired_connections or expired_elements:
            self.logger.debug(f"Cleaned up {len(expired_connections)} connections "
                            f"and {len(expired_elements)} elements")
    
    def optimize_for_text_capture(self) -> None:
        """Optimize cache for text capture operations."""
        if not self.enabled:
            return
        
        # Prefetch common text capture elements
        common_patterns = [
            'AXSelectedText',
            'AXFocusedUIElement',
            'AXTextField',
            'AXTextArea'
        ]
        
        # Get currently active applications
        active_apps = self._get_active_applications()
        
        for app_name in active_apps:
            self.prefetch_common_elements(app_name, common_patterns)
    
    def _get_active_applications(self) -> List[str]:
        """Get list of currently active applications."""
        # This would integrate with the accessibility module
        # to get the list of active applications
        return ['Safari', 'Chrome', 'TextEdit', 'VS Code']  # Placeholder
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._connection_lock, self._element_cache_lock:
            return {
                'connections': {
                    'pool_size': len(self._connections),
                    'max_pool_size': self.connection_pool_size,
                    'hits': self._connection_stats.hits,
                    'misses': self._connection_stats.misses,
                    'hit_rate': self._connection_stats.hit_rate,
                    'evictions': self._connection_stats.evictions,
                    'expirations': self._connection_stats.expirations
                },
                'elements': {
                    'cache_size': len(self._element_cache),
                    'max_cache_size': self.element_cache_size,
                    'hits': self._element_stats.hits,
                    'misses': self._element_stats.misses,
                    'hit_rate': self._element_stats.hit_rate,
                    'evictions': self._element_stats.evictions,
                    'expirations': self._element_stats.expirations
                },
                'prefetch': {
                    'queue_size': len(self._prefetch_queue),
                    'enabled': self.prefetch_enabled
                }
            }
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get cache optimization recommendations."""
        recommendations = []
        stats = self.get_cache_statistics()
        
        # Connection pool recommendations
        conn_hit_rate = stats['connections']['hit_rate']
        if conn_hit_rate < 0.5:
            recommendations.append({
                'category': 'connection_pool',
                'priority': 'medium',
                'title': 'Increase Connection Pool Size',
                'description': f'Connection hit rate is low ({conn_hit_rate:.1%}). '
                             f'Consider increasing pool size from {self.connection_pool_size}.',
                'suggested_action': f'Increase connection_pool_size to {self.connection_pool_size * 2}'
            })
        
        # Element cache recommendations
        elem_hit_rate = stats['elements']['hit_rate']
        if elem_hit_rate < 0.3:
            recommendations.append({
                'category': 'element_cache',
                'priority': 'high',
                'title': 'Optimize Element Caching',
                'description': f'Element cache hit rate is low ({elem_hit_rate:.1%}). '
                             f'Consider adjusting TTL or cache size.',
                'suggested_action': f'Increase element_cache_size to {self.element_cache_size * 2} '
                                  f'or adjust element_ttl to {self.element_ttl * 2:.0f}s'
            })
        
        # Prefetch recommendations
        if not self.prefetch_enabled and elem_hit_rate < 0.4:
            recommendations.append({
                'category': 'prefetch',
                'priority': 'medium',
                'title': 'Enable Prefetching',
                'description': 'Prefetching is disabled but could improve cache hit rates.',
                'suggested_action': 'Enable prefetch_enabled in configuration'
            })
        
        return recommendations
    
    def clear_cache(self, app_name: Optional[str] = None) -> None:
        """
        Clear cache entries.
        
        Args:
            app_name: Clear cache for specific app, or None for all
        """
        with self._connection_lock, self._element_cache_lock:
            if app_name:
                # Clear specific app
                conn_keys_to_remove = [k for k in self._connections.keys() if k.startswith(app_name)]
                elem_keys_to_remove = [k for k in self._element_cache.keys() if k.startswith(app_name)]
                
                for key in conn_keys_to_remove:
                    del self._connections[key]
                for key in elem_keys_to_remove:
                    del self._element_cache[key]
                
                self.logger.info(f"Cleared cache for {app_name}: "
                               f"{len(conn_keys_to_remove)} connections, "
                               f"{len(elem_keys_to_remove)} elements")
            else:
                # Clear all
                conn_count = len(self._connections)
                elem_count = len(self._element_cache)
                
                self._connections.clear()
                self._element_cache.clear()
                
                self.logger.info(f"Cleared all cache: {conn_count} connections, {elem_count} elements")
    
    def shutdown(self) -> None:
        """Shutdown cache optimizer and cleanup resources."""
        if self._prefetch_worker:
            self._stop_prefetch.set()
            self._prefetch_worker.join(timeout=5)
        
        if self._cleanup_thread:
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)
        
        self.clear_cache()
        self.logger.info("Accessibility cache optimizer shutdown complete")


# Global cache optimizer instance
_cache_optimizer: Optional[AccessibilityCacheOptimizer] = None


def get_cache_optimizer() -> AccessibilityCacheOptimizer:
    """Get or create global cache optimizer instance."""
    global _cache_optimizer
    
    if _cache_optimizer is None:
        # Load configuration
        config = {
            'enabled': True,
            'connection_pool_size': 10,
            'element_cache_size': 1000,
            'connection_ttl': 300.0,
            'element_ttl': 30.0,
            'prefetch_enabled': True
        }
        
        _cache_optimizer = AccessibilityCacheOptimizer(config)
    
    return _cache_optimizer
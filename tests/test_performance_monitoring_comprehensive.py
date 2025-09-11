"""
Comprehensive Test Suite for Performance Monitoring System

Tests the performance monitor, dashboard, and cache optimizer components
for the explain selected text feature optimization.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

# Import modules to test
from modules.performance_monitor import (
    PerformanceMonitor, PerformanceMetric, CacheEntry, PerformanceAlert,
    PerformanceCache, get_performance_monitor
)
from modules.performance_dashboard import (
    PerformanceDashboard, PerformanceTrend, OptimizationRecommendation,
    create_performance_dashboard
)
from modules.accessibility_cache_optimizer import (
    AccessibilityCacheOptimizer, AccessibilityConnection, ElementCache,
    get_cache_optimizer
)


class TestPerformanceMonitor:
    """Test suite for PerformanceMonitor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'enabled': True,
            'warning_threshold_ms': 1000,
            'critical_threshold_ms': 2000,
            'history_size': 50,
            'cache_enabled': True,
            'alerting_enabled': True
        }
        self.monitor = PerformanceMonitor(self.config)
    
    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self, 'monitor'):
            self.monitor.shutdown()
    
    def test_monitor_initialization(self):
        """Test performance monitor initialization."""
        assert self.monitor.enabled is True
        assert self.monitor.warning_threshold_ms == 1000
        assert self.monitor.critical_threshold_ms == 2000
        assert self.monitor.history_size == 50
        assert len(self.monitor._metrics) == 0
        assert len(self.monitor._operation_stats) == 0
    
    def test_track_operation_success(self):
        """Test successful operation tracking."""
        with self.monitor.track_operation('test_operation', {'test': 'data'}) as metric:
            time.sleep(0.1)  # Simulate work
            assert metric is not None
            assert metric.operation == 'test_operation'
            assert metric.metadata['test'] == 'data'
        
        # Check that metric was recorded
        assert len(self.monitor._metrics) == 1
        recorded_metric = self.monitor._metrics[0]
        assert recorded_metric.success is True
        assert recorded_metric.duration_ms is not None
        assert recorded_metric.duration_ms > 90  # Should be around 100ms
    
    def test_track_operation_failure(self):
        """Test failed operation tracking."""
        with pytest.raises(ValueError):
            with self.monitor.track_operation('test_operation') as metric:
                raise ValueError("Test error")
        
        # Check that failed metric was recorded
        assert len(self.monitor._metrics) == 1
        recorded_metric = self.monitor._metrics[0]
        assert recorded_metric.success is False
        assert recorded_metric.error_message == "Test error"
    
    def test_operation_statistics(self):
        """Test operation statistics calculation."""
        # Record multiple operations
        for i in range(5):
            with self.monitor.track_operation('test_op') as metric:
                time.sleep(0.05)  # 50ms each
        
        # Record one failure
        try:
            with self.monitor.track_operation('test_op') as metric:
                raise Exception("Test failure")
        except:
            pass
        
        stats = self.monitor.get_operation_stats('test_op')
        assert stats['count'] == 6
        assert stats['success_count'] == 5
        assert stats['success_rate'] == 5/6
        assert stats['avg_duration_ms'] > 0
        assert len(stats['recent_durations']) == 6
    
    def test_performance_alerts(self):
        """Test performance alerting system."""
        alerts_triggered = []
        
        def alert_callback(alert):
            alerts_triggered.append(alert)
        
        self.monitor.add_alert_callback(alert_callback)
        
        # Trigger warning alert
        with self.monitor.track_operation('slow_operation') as metric:
            time.sleep(1.1)  # Exceed warning threshold
        
        assert len(alerts_triggered) == 1
        alert = alerts_triggered[0]
        assert alert.alert_type == 'duration_warning'
        assert alert.severity == 'warning'
        assert alert.actual_ms > 1000
    
    def test_cache_functionality(self):
        """Test performance cache functionality."""
        cache = self.monitor.text_capture_cache
        
        # Test cache miss
        result = cache.get('test_key')
        assert result is None
        
        # Test cache put and hit
        cache.put('test_key', 'test_value', ttl=1.0)
        result = cache.get('test_key')
        assert result == 'test_value'
        
        # Test cache expiration
        time.sleep(1.1)
        result = cache.get('test_key')
        assert result is None
        
        # Check cache statistics
        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 2
        assert stats['expirations'] == 1
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        # Record some operations
        for i in range(3):
            with self.monitor.track_operation('test_op'):
                time.sleep(0.05)
        
        summary = self.monitor.get_performance_summary()
        assert summary['total_operations'] == 3
        assert summary['success_rate'] == 1.0
        assert summary['avg_duration_ms'] > 0
        assert 'cache_stats' in summary
        assert 'operation_stats' in summary
    
    def test_optimization_recommendations(self):
        """Test optimization recommendation generation."""
        # Simulate poor text capture performance
        for i in range(5):
            try:
                with self.monitor.track_operation('text_capture'):
                    if i < 2:  # 2 failures out of 5
                        raise Exception("Capture failed")
                    time.sleep(0.5)  # Slow operations
            except:
                pass
        
        recommendations = self.monitor.optimize_text_capture_performance()
        assert 'recommendations' in recommendations
        assert len(recommendations['recommendations']) > 0
        
        # Should recommend improving success rate and performance
        rec_text = ' '.join(recommendations['recommendations'])
        assert 'success rate' in rec_text.lower() or 'performance' in rec_text.lower()


class TestPerformanceCache:
    """Test suite for PerformanceCache class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache = PerformanceCache(max_size=3, default_ttl=1.0)
    
    def test_cache_basic_operations(self):
        """Test basic cache operations."""
        # Test miss
        assert self.cache.get('key1') is None
        
        # Test put and hit
        self.cache.put('key1', 'value1')
        assert self.cache.get('key1') == 'value1'
        
        # Test TTL expiration
        time.sleep(1.1)
        assert self.cache.get('key1') is None
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        # Fill cache to capacity
        self.cache.put('key1', 'value1')
        self.cache.put('key2', 'value2')
        self.cache.put('key3', 'value3')
        
        # Access key1 to make it recently used
        self.cache.get('key1')
        
        # Add another item, should evict key2 (least recently used)
        self.cache.put('key4', 'value4')
        
        assert self.cache.get('key1') == 'value1'  # Still there
        assert self.cache.get('key2') is None      # Evicted
        assert self.cache.get('key3') == 'value3'  # Still there
        assert self.cache.get('key4') == 'value4'  # New item
    
    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        # Generate some cache activity
        self.cache.put('key1', 'value1')
        self.cache.get('key1')  # Hit
        self.cache.get('key2')  # Miss
        
        stats = self.cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5
        assert stats['size'] == 1


class TestPerformanceDashboard:
    """Test suite for PerformanceDashboard class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = Mock()
        self.monitor.enabled = True
        self.monitor.get_performance_summary.return_value = {
            'total_operations': 100,
            'success_rate': 0.95,
            'avg_duration_ms': 500.0,
            'median_duration_ms': 400.0,
            'p95_duration_ms': 800.0
        }
        self.monitor.get_operation_stats.return_value = {
            'count': 50,
            'success_count': 48,
            'success_rate': 0.96,
            'avg_duration_ms': 300.0
        }
        self.monitor.get_cache_stats.return_value = {
            'text_capture': {'hit_rate': 0.7, 'size': 10},
            'explanation': {'hit_rate': 0.4, 'size': 5}
        }
        self.monitor.get_recent_alerts.return_value = []
        
        self.dashboard = PerformanceDashboard(self.monitor)
    
    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self, 'dashboard'):
            self.dashboard.shutdown()
    
    def test_dashboard_initialization(self):
        """Test dashboard initialization."""
        assert self.dashboard.monitor == self.monitor
        assert self.dashboard.update_interval == 30.0
        assert self.dashboard._update_thread is not None
    
    def test_health_score_calculation(self):
        """Test health score calculation."""
        summary = {
            'success_rate': 0.95,
            'avg_duration_ms': 1000.0
        }
        text_stats = {'success_rate': 0.9}
        explanation_stats = {'success_rate': 0.95}
        
        score = self.dashboard._calculate_health_score(summary, text_stats, explanation_stats)
        assert 0 <= score <= 100
        assert score > 50  # Should be decent with these stats
    
    def test_dashboard_data_update(self):
        """Test dashboard data update."""
        self.dashboard._update_dashboard_data()
        
        data = self.dashboard.get_dashboard_data()
        assert 'timestamp' in data
        assert 'overall_health_score' in data
        assert 'summary' in data
        assert 'optimization_recommendations' in data
    
    def test_optimization_recommendations(self):
        """Test optimization recommendation generation."""
        # Mock poor performance stats
        def mock_get_operation_stats(op):
            if op == 'text_capture':
                return {'success_rate': 0.8, 'avg_duration_ms': 1500.0}
            elif op == 'explanation_generation':
                return {'success_rate': 0.9, 'avg_duration_ms': 6000.0}
            else:
                return {}
        
        self.monitor.get_operation_stats.side_effect = mock_get_operation_stats
        
        # Update dashboard data to include the mocked stats
        self.dashboard._dashboard_data = {
            'text_capture': {'success_rate': 0.8, 'avg_duration_ms': 1500.0},
            'explanation_generation': {'success_rate': 0.9, 'avg_duration_ms': 6000.0},
            'cache_performance': {
                'text_capture': {'hit_rate': 0.1},
                'explanation': {'hit_rate': 0.1}
            }
        }
        
        recommendations = self.dashboard._generate_optimization_recommendations()
        assert len(recommendations) > 0
        
        # Should have recommendations for both text capture and explanation
        categories = [rec.category for rec in recommendations]
        assert 'text_capture' in categories or 'explanation_generation' in categories or 'caching' in categories
    
    def test_performance_report(self):
        """Test performance report generation."""
        report = self.dashboard.get_performance_report()
        
        assert 'report_timestamp' in report
        assert 'health_score' in report
        assert 'summary' in report
        assert 'recommendations' in report
        assert isinstance(report['recommendations'], list)


class TestAccessibilityCacheOptimizer:
    """Test suite for AccessibilityCacheOptimizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'enabled': True,
            'connection_pool_size': 5,
            'element_cache_size': 10,
            'connection_ttl': 1.0,
            'element_ttl': 1.0,
            'prefetch_enabled': True
        }
        self.optimizer = AccessibilityCacheOptimizer(self.config)
    
    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self, 'optimizer'):
            self.optimizer.shutdown()
    
    def test_optimizer_initialization(self):
        """Test cache optimizer initialization."""
        assert self.optimizer.enabled is True
        assert self.optimizer.connection_pool_size == 5
        assert self.optimizer.element_cache_size == 10
        assert len(self.optimizer._connections) == 0
        assert len(self.optimizer._element_cache) == 0
    
    def test_connection_caching(self):
        """Test accessibility connection caching."""
        mock_connection = Mock()
        
        # Test cache miss
        result = self.optimizer.get_accessibility_connection('TestApp', 1234)
        assert result is None
        
        # Cache connection
        self.optimizer.cache_accessibility_connection('TestApp', 1234, mock_connection)
        
        # Test cache hit
        result = self.optimizer.get_accessibility_connection('TestApp', 1234)
        assert result == mock_connection
        
        # Test expiration
        time.sleep(1.1)
        result = self.optimizer.get_accessibility_connection('TestApp', 1234)
        assert result is None
    
    def test_element_caching(self):
        """Test element data caching."""
        element_data = {'role': 'AXButton', 'title': 'Test Button'}
        
        # Test cache miss
        result = self.optimizer.get_cached_element('elem1', 'TestApp')
        assert result is None
        
        # Cache element
        self.optimizer.cache_element('elem1', 'TestApp', element_data)
        
        # Test cache hit
        result = self.optimizer.get_cached_element('elem1', 'TestApp')
        assert result == element_data
        
        # Test expiration
        time.sleep(1.1)
        result = self.optimizer.get_cached_element('elem1', 'TestApp')
        assert result is None
    
    def test_connection_pool_eviction(self):
        """Test connection pool LRU eviction."""
        # Fill pool to capacity
        for i in range(self.optimizer.connection_pool_size):
            mock_conn = Mock()
            self.optimizer.cache_accessibility_connection(f'App{i}', i, mock_conn)
        
        # Access first connection to make it recently used
        self.optimizer.get_accessibility_connection('App0', 0)
        
        # Add another connection, should evict least recently used
        new_mock = Mock()
        self.optimizer.cache_accessibility_connection('NewApp', 999, new_mock)
        
        # First connection should still be there
        assert self.optimizer.get_accessibility_connection('App0', 0) is not None
        # New connection should be there
        assert self.optimizer.get_accessibility_connection('NewApp', 999) is not None
        # Pool should be at capacity
        assert len(self.optimizer._connections) == self.optimizer.connection_pool_size
    
    def test_prefetch_functionality(self):
        """Test element prefetching."""
        patterns = ['AXButton', 'AXTextField', 'AXLink']
        
        # Queue prefetch tasks
        self.optimizer.prefetch_common_elements('TestApp', patterns)
        
        # Check that tasks were queued
        assert len(self.optimizer._prefetch_queue) == len(patterns)
        
        # Process queue
        self.optimizer._process_prefetch_queue()
        
        # Queue should be processed (empty or reduced)
        assert len(self.optimizer._prefetch_queue) <= len(patterns)
    
    def test_cache_statistics(self):
        """Test cache statistics reporting."""
        # Generate some cache activity
        mock_conn = Mock()
        self.optimizer.cache_accessibility_connection('App1', 1, mock_conn)
        self.optimizer.get_accessibility_connection('App1', 1)  # Hit
        self.optimizer.get_accessibility_connection('App2', 2)  # Miss
        
        element_data = {'role': 'AXButton'}
        self.optimizer.cache_element('elem1', 'App1', element_data)
        self.optimizer.get_cached_element('elem1', 'App1')  # Hit
        self.optimizer.get_cached_element('elem2', 'App1')  # Miss
        
        stats = self.optimizer.get_cache_statistics()
        
        assert 'connections' in stats
        assert 'elements' in stats
        assert stats['connections']['hits'] == 1
        assert stats['connections']['misses'] == 1
        assert stats['elements']['hits'] == 1
        assert stats['elements']['misses'] == 1
    
    def test_optimization_recommendations(self):
        """Test optimization recommendations."""
        # Generate poor cache performance
        for i in range(10):
            self.optimizer.get_accessibility_connection(f'App{i}', i)  # All misses
            self.optimizer.get_cached_element(f'elem{i}', f'App{i}')   # All misses
        
        recommendations = self.optimizer.get_optimization_recommendations()
        assert len(recommendations) > 0
        
        # Should recommend improvements for low hit rates
        categories = [rec['category'] for rec in recommendations]
        assert 'connection_pool' in categories or 'element_cache' in categories
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        # Add some cached data
        mock_conn = Mock()
        self.optimizer.cache_accessibility_connection('App1', 1, mock_conn)
        self.optimizer.cache_element('elem1', 'App1', {'role': 'AXButton'})
        
        # Clear specific app
        self.optimizer.clear_cache('App1')
        
        # Should be cleared
        assert self.optimizer.get_accessibility_connection('App1', 1) is None
        assert self.optimizer.get_cached_element('elem1', 'App1') is None
    
    def test_text_capture_optimization(self):
        """Test optimization for text capture operations."""
        # This should queue prefetch tasks for text capture elements
        self.optimizer.optimize_for_text_capture()
        
        # Should have queued some prefetch tasks
        assert len(self.optimizer._prefetch_queue) > 0
        
        # Tasks should be for text-related elements
        task_patterns = [task['pattern'] for task in self.optimizer._prefetch_queue]
        text_patterns = ['AXSelectedText', 'AXTextField', 'AXTextArea']
        assert any(pattern in task_patterns for pattern in text_patterns)


class TestIntegration:
    """Integration tests for performance monitoring system."""
    
    def test_monitor_dashboard_integration(self):
        """Test integration between monitor and dashboard."""
        monitor = PerformanceMonitor({'enabled': True})
        dashboard = PerformanceDashboard(monitor)
        
        try:
            # Generate some performance data
            with monitor.track_operation('test_operation'):
                time.sleep(0.1)
            
            # Update dashboard
            dashboard._update_dashboard_data()
            data = dashboard.get_dashboard_data()
            
            # Dashboard should reflect monitor data
            assert data['summary']['total_operations'] > 0
            assert 'overall_health_score' in data
            
        finally:
            dashboard.shutdown()
            monitor.shutdown()
    
    def test_monitor_cache_optimizer_integration(self):
        """Test integration between monitor and cache optimizer."""
        monitor = PerformanceMonitor({'enabled': True})
        optimizer = AccessibilityCacheOptimizer({'enabled': True})
        
        try:
            # Simulate text capture with caching
            with monitor.track_operation('text_capture') as metric:
                # Simulate cache miss then hit
                result = optimizer.get_cached_element('test_elem', 'TestApp')
                assert result is None  # Miss
                
                optimizer.cache_element('test_elem', 'TestApp', {'role': 'AXTextField'})
                result = optimizer.get_cached_element('test_elem', 'TestApp')
                assert result is not None  # Hit
                
                metric.metadata['cache_hit'] = result is not None
            
            # Check that performance was tracked
            stats = monitor.get_operation_stats('text_capture')
            assert stats['count'] == 1
            
        finally:
            optimizer.shutdown()
            monitor.shutdown()
    
    def test_global_monitor_access(self):
        """Test global performance monitor access."""
        # Test that global monitor is accessible and returns a valid instance
        monitor = get_performance_monitor()
        assert monitor is not None
        assert hasattr(monitor, 'track_operation')
        assert hasattr(monitor, 'get_performance_summary')
        
        # Test that subsequent calls return the same instance (singleton behavior)
        monitor2 = get_performance_monitor()
        assert monitor is monitor2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
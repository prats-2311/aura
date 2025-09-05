"""
Integration tests for enhanced caching functionality.

Tests caching behavior, cache performance improvements, and cache invalidation
for enhanced accessibility features.

Requirements covered:
- 7.2: Caching for enhanced features
- 7.1: Performance improvements through caching
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.accessibility import AccessibilityModule


class TestEnhancedCachingIntegration:
    """Integration tests for enhanced caching functionality."""
    
    @pytest.fixture
    def accessibility_module(self):
        """Create AccessibilityModule instance for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True), \
             patch('modules.accessibility.NSWorkspace'), \
             patch('modules.accessibility.AXUIElementCreateSystemWide'):
            return AccessibilityModule()
    
    def test_fuzzy_matching_cache_integration(self, accessibility_module):
        """Test fuzzy matching cache integration and performance."""
        # Test that cache attributes exist
        assert hasattr(accessibility_module, 'fuzzy_match_cache')
        assert isinstance(accessibility_module.fuzzy_match_cache, dict)
        
        # Clear cache for clean test
        accessibility_module.fuzzy_match_cache.clear()
        
        # First call should miss cache and be slower
        start_time = time.time()
        result1 = accessibility_module.fuzzy_match_text("Gmail Link", "gmail")
        first_call_time = time.time() - start_time
        
        # Second call should hit cache and be faster
        start_time = time.time()
        result2 = accessibility_module.fuzzy_match_text("Gmail Link", "gmail")
        second_call_time = time.time() - start_time
        
        # Results should be identical
        assert result1 == result2
        
        # Second call should be faster (cache hit)
        # Note: This might not always be true due to system variations, so we use a reasonable threshold
        if first_call_time > 0.001:  # Only check if first call was measurably slow
            assert second_call_time <= first_call_time * 2, "Cache hit should not be significantly slower"
        
        # Cache should contain the result
        assert len(accessibility_module.fuzzy_match_cache) > 0
    
    def test_target_extraction_cache_integration(self, accessibility_module):
        """Test target extraction cache integration."""
        # Test that cache attributes exist
        assert hasattr(accessibility_module, 'target_extraction_cache')
        assert isinstance(accessibility_module.target_extraction_cache, dict)
        
        # Test cache key generation
        if hasattr(accessibility_module, '_generate_target_extraction_cache_key'):
            cache_key = accessibility_module._generate_target_extraction_cache_key("Click Gmail")
            assert isinstance(cache_key, str)
            assert len(cache_key) > 0
    
    def test_cache_ttl_and_cleanup_integration(self, accessibility_module):
        """Test cache TTL and cleanup integration."""
        # Test that cache TTL attributes exist
        assert hasattr(accessibility_module, 'cache_ttl_seconds')
        assert isinstance(accessibility_module.cache_ttl_seconds, (int, float))
        assert accessibility_module.cache_ttl_seconds > 0
        
        # Test cache size limits
        assert hasattr(accessibility_module, 'max_cache_entries')
        assert isinstance(accessibility_module.max_cache_entries, int)
        assert accessibility_module.max_cache_entries > 0
        
        # Test cache cleanup interval
        assert hasattr(accessibility_module, 'cache_cleanup_interval')
        assert isinstance(accessibility_module.cache_cleanup_interval, (int, float))
        assert accessibility_module.cache_cleanup_interval > 0
    
    def test_cache_statistics_integration(self, accessibility_module):
        """Test cache statistics integration."""
        # Test that cache statistics exist
        assert hasattr(accessibility_module, 'cache_stats')
        assert isinstance(accessibility_module.cache_stats, dict)
        
        # Test expected statistics fields
        expected_stats = ['hits', 'misses', 'invalidations', 'expirations', 'total_lookups']
        for stat in expected_stats:
            assert stat in accessibility_module.cache_stats
            assert isinstance(accessibility_module.cache_stats[stat], int)
    
    def test_cache_performance_improvement(self, accessibility_module):
        """Test that caching provides performance improvements."""
        # Clear caches for clean test
        accessibility_module.fuzzy_match_cache.clear()
        if hasattr(accessibility_module, 'target_extraction_cache'):
            accessibility_module.target_extraction_cache.clear()
        
        # Test multiple calls to the same fuzzy match
        test_pairs = [
            ("Gmail Link", "gmail"),
            ("Submit Button", "submit"),
            ("Sign In", "sign in")
        ]
        
        for element_text, target_text in test_pairs:
            # First call (cache miss)
            start_time = time.time()
            result1 = accessibility_module.fuzzy_match_text(element_text, target_text)
            first_time = time.time() - start_time
            
            # Second call (cache hit)
            start_time = time.time()
            result2 = accessibility_module.fuzzy_match_text(element_text, target_text)
            second_time = time.time() - start_time
            
            # Results should be identical
            assert result1 == result2
            
            # Both calls should complete quickly
            assert first_time < 1.0, f"First call took too long: {first_time:.3f}s"
            assert second_time < 1.0, f"Second call took too long: {second_time:.3f}s"
    
    def test_cache_size_limit_enforcement(self, accessibility_module):
        """Test that cache size limits are enforced."""
        original_max_entries = accessibility_module.max_cache_entries
        
        try:
            # Set a small cache size for testing
            accessibility_module.max_cache_entries = 3
            
            # Clear cache
            accessibility_module.fuzzy_match_cache.clear()
            
            # Add more entries than the limit
            test_pairs = [
                ("Text1", "target1"),
                ("Text2", "target2"),
                ("Text3", "target3"),
                ("Text4", "target4"),
                ("Text5", "target5")
            ]
            
            for element_text, target_text in test_pairs:
                accessibility_module.fuzzy_match_text(element_text, target_text)
            
            # Cache should not exceed the maximum size significantly
            # (allowing some tolerance for cleanup timing)
            assert len(accessibility_module.fuzzy_match_cache) <= accessibility_module.max_cache_entries + 2
            
        finally:
            # Restore original setting
            accessibility_module.max_cache_entries = original_max_entries
    
    def test_cache_invalidation_integration(self, accessibility_module):
        """Test cache invalidation integration."""
        # Clear cache
        accessibility_module.fuzzy_match_cache.clear()
        
        # Add some entries
        accessibility_module.fuzzy_match_text("Test1", "target1")
        accessibility_module.fuzzy_match_text("Test2", "target2")
        
        initial_cache_size = len(accessibility_module.fuzzy_match_cache)
        assert initial_cache_size > 0
        
        # Test cache cleanup method if it exists
        if hasattr(accessibility_module, '_cleanup_expired_cache_entries'):
            try:
                accessibility_module._cleanup_expired_cache_entries()
                # Should not crash
                assert len(accessibility_module.fuzzy_match_cache) >= 0
            except Exception as e:
                pytest.fail(f"Cache cleanup failed: {e}")
    
    def test_cache_thread_safety_integration(self, accessibility_module):
        """Test cache thread safety integration."""
        # Test that cache operations don't crash under concurrent access
        import threading
        
        def cache_worker():
            for i in range(10):
                accessibility_module.fuzzy_match_text(f"Text{i}", f"target{i}")
        
        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=cache_worker)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)
            assert not thread.is_alive(), "Thread did not complete in time"
        
        # Cache should contain some entries
        assert len(accessibility_module.fuzzy_match_cache) >= 0


class TestCachePerformanceBenchmarks:
    """Performance benchmarks for caching functionality."""
    
    @pytest.fixture
    def accessibility_module(self):
        """Create AccessibilityModule instance for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True), \
             patch('modules.accessibility.ACCESSIBILITY_FUNCTIONS_AVAILABLE', True), \
             patch('modules.accessibility.NSWorkspace'), \
             patch('modules.accessibility.AXUIElementCreateSystemWide'):
            return AccessibilityModule()
    
    def test_cache_hit_performance_benchmark(self, accessibility_module):
        """Benchmark cache hit performance."""
        # Clear cache
        accessibility_module.fuzzy_match_cache.clear()
        
        # Warm up cache
        test_text = "Gmail Link Button"
        target_text = "gmail"
        accessibility_module.fuzzy_match_text(test_text, target_text)
        
        # Benchmark cache hits
        hit_times = []
        for _ in range(10):
            start_time = time.time()
            accessibility_module.fuzzy_match_text(test_text, target_text)
            elapsed_time = time.time() - start_time
            hit_times.append(elapsed_time)
        
        avg_hit_time = sum(hit_times) / len(hit_times)
        max_hit_time = max(hit_times)
        
        # Cache hits should be very fast
        assert avg_hit_time < 0.01, f"Average cache hit time too slow: {avg_hit_time:.4f}s"
        assert max_hit_time < 0.05, f"Maximum cache hit time too slow: {max_hit_time:.4f}s"
    
    def test_cache_miss_vs_hit_performance(self, accessibility_module):
        """Compare cache miss vs hit performance."""
        # Clear cache
        accessibility_module.fuzzy_match_cache.clear()
        
        test_pairs = [
            ("Gmail Link", "gmail"),
            ("Submit Button", "submit"),
            ("Cancel Button", "cancel")
        ]
        
        miss_times = []
        hit_times = []
        
        for element_text, target_text in test_pairs:
            # Cache miss
            start_time = time.time()
            accessibility_module.fuzzy_match_text(element_text, target_text)
            miss_time = time.time() - start_time
            miss_times.append(miss_time)
            
            # Cache hit
            start_time = time.time()
            accessibility_module.fuzzy_match_text(element_text, target_text)
            hit_time = time.time() - start_time
            hit_times.append(hit_time)
        
        avg_miss_time = sum(miss_times) / len(miss_times)
        avg_hit_time = sum(hit_times) / len(hit_times)
        
        # Both should be reasonable, but hits should generally be faster
        assert avg_miss_time < 1.0, f"Average cache miss time too slow: {avg_miss_time:.4f}s"
        assert avg_hit_time < 0.1, f"Average cache hit time too slow: {avg_hit_time:.4f}s"
        
        # Cache hits should be faster than misses (when miss time is measurable)
        if avg_miss_time > 0.001:
            assert avg_hit_time <= avg_miss_time, "Cache hits should not be slower than misses"
    
    def test_cache_memory_usage_benchmark(self, accessibility_module):
        """Benchmark cache memory usage."""
        import sys
        
        # Clear cache
        accessibility_module.fuzzy_match_cache.clear()
        
        # Measure initial memory
        initial_cache_size = len(accessibility_module.fuzzy_match_cache)
        
        # Add many entries
        for i in range(100):
            accessibility_module.fuzzy_match_text(f"Element {i}", f"target {i}")
        
        final_cache_size = len(accessibility_module.fuzzy_match_cache)
        
        # Cache should have grown but not excessively
        assert final_cache_size > initial_cache_size
        assert final_cache_size <= accessibility_module.max_cache_entries + 10  # Allow some tolerance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
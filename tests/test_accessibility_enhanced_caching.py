"""
Test suite for enhanced accessibility caching features.

Tests fuzzy matching result caching, target extraction result caching,
and cache management functionality.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from modules.accessibility import AccessibilityModule
from modules.error_handler import ErrorHandler


class TestFuzzyMatchingCache:
    """Test fuzzy matching result caching."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.accessibility = AccessibilityModule()
        
        # Configure caching for tests
        self.accessibility.configure_enhanced_caching(
            ttl_seconds=60,  # 1 minute for tests
            max_entries=100,
            cleanup_interval=30
        )
    
    def test_fuzzy_match_cache_hit(self):
        """Test fuzzy matching cache hit."""
        # Clear cache to start fresh
        self.accessibility.clear_enhanced_caches()
        
        # Mock fuzzy matching to be available
        with patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True), \
             patch('modules.accessibility.fuzz') as mock_fuzz:
            
            mock_fuzz.partial_ratio.return_value = 90
            
            # First call should compute and cache result
            match1, confidence1 = self.accessibility.fuzzy_match_text("Sign In", "sign in")
            
            # Second call should hit cache
            match2, confidence2 = self.accessibility.fuzzy_match_text("Sign In", "sign in")
            
            # Results should be identical
            assert match1 == match2
            assert confidence1 == confidence2
            assert match1 is True
            assert confidence1 == 90.0
            
            # Fuzzy matching should only be called once (first time)
            assert mock_fuzz.partial_ratio.call_count == 1
    
    def test_fuzzy_match_cache_key_generation(self):
        """Test fuzzy matching cache key generation."""
        # Test that different parameters generate different cache keys
        key1 = self.accessibility._generate_fuzzy_match_cache_key("Sign In", "sign in", 85)
        key2 = self.accessibility._generate_fuzzy_match_cache_key("Sign In", "sign in", 90)
        key3 = self.accessibility._generate_fuzzy_match_cache_key("Sign In", "login", 85)
        
        assert key1 != key2  # Different thresholds
        assert key1 != key3  # Different target text
        assert key2 != key3  # Different target text and threshold
        
        # Test that normalized text is used consistently
        key4 = self.accessibility._generate_fuzzy_match_cache_key("  Sign In  ", "sign in", 85)
        key5 = self.accessibility._generate_fuzzy_match_cache_key("sign in", "Sign In", 85)
        
        # Keys should be similar due to normalization (though order matters)
        assert isinstance(key4, str)
        assert isinstance(key5, str)
    
    def test_fuzzy_match_cache_expiration(self):
        """Test fuzzy matching cache expiration."""
        # Set very short TTL for testing
        self.accessibility.configure_enhanced_caching(ttl_seconds=1)
        
        with patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True), \
             patch('modules.accessibility.fuzz') as mock_fuzz:
            
            mock_fuzz.partial_ratio.return_value = 85
            
            # First call
            match1, confidence1 = self.accessibility.fuzzy_match_text("Test", "test")
            assert mock_fuzz.partial_ratio.call_count == 1
            
            # Second call immediately should hit cache
            match2, confidence2 = self.accessibility.fuzzy_match_text("Test", "test")
            assert mock_fuzz.partial_ratio.call_count == 1  # Still only one call
            
            # Wait for cache to expire
            time.sleep(1.1)
            
            # Third call should miss cache and recompute
            match3, confidence3 = self.accessibility.fuzzy_match_text("Test", "test")
            assert mock_fuzz.partial_ratio.call_count == 2  # Now two calls
    
    def test_fuzzy_match_cache_size_limit(self):
        """Test fuzzy matching cache size limit enforcement."""
        # Set small cache size for testing
        self.accessibility.configure_enhanced_caching(max_entries=3)
        
        with patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True), \
             patch('modules.accessibility.fuzz') as mock_fuzz:
            
            mock_fuzz.partial_ratio.return_value = 80
            
            # Fill cache beyond limit
            test_pairs = [
                ("Button1", "button1"),
                ("Button2", "button2"),
                ("Button3", "button3"),
                ("Button4", "button4"),  # This should trigger cleanup
                ("Button5", "button5")   # This should also trigger cleanup
            ]
            
            for element_text, target_text in test_pairs:
                self.accessibility.fuzzy_match_text(element_text, target_text)
            
            # Cache should not exceed max size
            assert len(self.accessibility.fuzzy_match_cache) <= 3
    
    def test_fuzzy_match_cache_cleanup(self):
        """Test fuzzy matching cache cleanup functionality."""
        # Add some entries to cache
        self.accessibility._cache_fuzzy_match_result("Test1", "test1", 85, True, 90.0)
        self.accessibility._cache_fuzzy_match_result("Test2", "test2", 85, True, 85.0)
        self.accessibility._cache_fuzzy_match_result("Test3", "test3", 85, False, 70.0)
        
        initial_count = len(self.accessibility.fuzzy_match_cache)
        assert initial_count == 3
        
        # Manually trigger cleanup
        self.accessibility._cleanup_fuzzy_match_cache()
        
        # Cache should still contain entries (not expired yet)
        assert len(self.accessibility.fuzzy_match_cache) <= initial_count


class TestTargetExtractionCache:
    """Test target extraction result caching."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.accessibility = AccessibilityModule()
        
        # Configure caching for tests
        self.accessibility.configure_enhanced_caching(
            ttl_seconds=60,
            max_entries=100,
            cleanup_interval=30
        )
    
    def test_target_extraction_cache_storage_and_retrieval(self):
        """Test target extraction cache storage and retrieval."""
        # Clear cache
        self.accessibility.clear_enhanced_caches()
        
        # Cache a result
        command = "Click on the Submit button"
        target = "Submit button"
        action_type = "click"
        confidence = 0.95
        
        self.accessibility._cache_target_extraction_result(command, target, action_type, confidence)
        
        # Retrieve cached result
        cached_result = self.accessibility._get_cached_target_extraction(command)
        
        assert cached_result is not None
        cached_target, cached_action, cached_confidence = cached_result
        assert cached_target == target
        assert cached_action == action_type
        assert cached_confidence == confidence
    
    def test_target_extraction_cache_key_normalization(self):
        """Test target extraction cache key normalization."""
        # Test that similar commands generate the same cache key
        command1 = "Click on the Submit button"
        command2 = "  CLICK ON THE SUBMIT BUTTON  "
        
        key1 = self.accessibility._generate_target_extraction_cache_key(command1)
        key2 = self.accessibility._generate_target_extraction_cache_key(command2)
        
        # Keys should be the same due to normalization
        assert key1 == key2
    
    def test_target_extraction_cache_expiration(self):
        """Test target extraction cache expiration."""
        # Set very short TTL
        self.accessibility.configure_enhanced_caching(ttl_seconds=1)
        
        command = "Type in the search box"
        target = "search box"
        action_type = "type"
        confidence = 0.90
        
        # Cache result
        self.accessibility._cache_target_extraction_result(command, target, action_type, confidence)
        
        # Should be available immediately
        cached_result = self.accessibility._get_cached_target_extraction(command)
        assert cached_result is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        expired_result = self.accessibility._get_cached_target_extraction(command)
        assert expired_result is None
    
    def test_target_extraction_cache_size_limit(self):
        """Test target extraction cache size limit."""
        # Set small cache size
        self.accessibility.configure_enhanced_caching(max_entries=2)
        
        # Add entries beyond limit
        commands = [
            ("Click button1", "button1", "click", 0.9),
            ("Click button2", "button2", "click", 0.9),
            ("Click button3", "button3", "click", 0.9),  # Should trigger cleanup
        ]
        
        for command, target, action, confidence in commands:
            self.accessibility._cache_target_extraction_result(command, target, action, confidence)
        
        # Cache should not exceed limit
        assert len(self.accessibility.target_extraction_cache) <= 2


class TestCacheManagement:
    """Test cache management and configuration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.accessibility = AccessibilityModule()
    
    def test_cache_statistics(self):
        """Test cache statistics reporting."""
        # Add some cached data
        self.accessibility._cache_fuzzy_match_result("Test1", "test1", 85, True, 90.0)
        self.accessibility._cache_target_extraction_result("Click test", "test", "click", 0.9)
        
        stats = self.accessibility.get_cache_statistics()
        
        # Check that enhanced cache stats are included
        assert 'enhanced_caches' in stats
        enhanced_stats = stats['enhanced_caches']
        
        assert 'fuzzy_match_cache' in enhanced_stats
        assert 'target_extraction_cache' in enhanced_stats
        assert 'cache_cleanup' in enhanced_stats
        
        # Check cache entry counts
        assert enhanced_stats['fuzzy_match_cache']['entries'] >= 1
        assert enhanced_stats['target_extraction_cache']['entries'] >= 1
    
    def test_cache_configuration(self):
        """Test cache configuration updates."""
        # Test configuration update
        self.accessibility.configure_enhanced_caching(
            ttl_seconds=120,
            max_entries=500,
            cleanup_interval=60
        )
        
        assert self.accessibility.cache_ttl_seconds == 120
        assert self.accessibility.max_cache_entries == 500
        assert self.accessibility.cache_cleanup_interval == 60
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        # Add some data to caches
        self.accessibility._cache_fuzzy_match_result("Test1", "test1", 85, True, 90.0)
        self.accessibility._cache_target_extraction_result("Click test", "test", "click", 0.9)
        
        # Verify data exists
        assert len(self.accessibility.fuzzy_match_cache) > 0
        assert len(self.accessibility.target_extraction_cache) > 0
        
        # Clear caches
        self.accessibility.clear_enhanced_caches()
        
        # Verify caches are empty
        assert len(self.accessibility.fuzzy_match_cache) == 0
        assert len(self.accessibility.target_extraction_cache) == 0
    
    def test_periodic_cache_cleanup(self):
        """Test periodic cache cleanup functionality."""
        # Set short cleanup interval
        self.accessibility.configure_enhanced_caching(cleanup_interval=1)
        
        # Add some data
        self.accessibility._cache_fuzzy_match_result("Test1", "test1", 85, True, 90.0)
        
        # Reset last cleanup time to force cleanup
        self.accessibility.last_cache_cleanup = time.time() - 2  # 2 seconds ago
        
        # Trigger periodic cleanup
        self.accessibility._periodic_cache_cleanup()
        
        # Last cleanup time should be updated
        assert self.accessibility.last_cache_cleanup > time.time() - 1


class TestCacheIntegration:
    """Test cache integration with actual methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.accessibility = AccessibilityModule()
        
        # Configure fast caching for tests
        self.accessibility.configure_enhanced_caching(
            ttl_seconds=60,
            max_entries=50,
            cleanup_interval=30
        )
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.accessibility.fuzz')
    def test_fuzzy_matching_with_cache_integration(self, mock_fuzz):
        """Test fuzzy matching with cache integration."""
        mock_fuzz.partial_ratio.return_value = 88
        
        # Clear cache
        self.accessibility.clear_enhanced_caches()
        
        # First call should compute and cache
        match1, confidence1 = self.accessibility.fuzzy_match_text("Gmail", "gmail")
        assert match1 is True
        assert confidence1 == 88.0
        assert mock_fuzz.partial_ratio.call_count == 1
        
        # Second identical call should use cache
        match2, confidence2 = self.accessibility.fuzzy_match_text("Gmail", "gmail")
        assert match2 is True
        assert confidence2 == 88.0
        assert mock_fuzz.partial_ratio.call_count == 1  # Still only one call
        
        # Different call should compute again
        match3, confidence3 = self.accessibility.fuzzy_match_text("Login", "login")
        assert match3 is True
        assert confidence3 == 88.0
        assert mock_fuzz.partial_ratio.call_count == 2  # Now two calls
    
    @patch('modules.accessibility.FUZZY_MATCHING_AVAILABLE', False)
    def test_fuzzy_matching_fallback_caching(self):
        """Test that fallback exact matching results are also cached."""
        # Clear cache
        self.accessibility.clear_enhanced_caches()
        
        # First call should use exact matching fallback and cache result
        match1, confidence1 = self.accessibility.fuzzy_match_text("Sign In", "sign in")
        assert match1 is True
        assert confidence1 == 100.0
        
        # Second call should hit cache
        match2, confidence2 = self.accessibility.fuzzy_match_text("Sign In", "sign in")
        assert match2 is True
        assert confidence2 == 100.0
        
        # Verify cache contains the result
        cached_result = self.accessibility._get_cached_fuzzy_match("Sign In", "sign in", 85)
        assert cached_result is not None
        assert cached_result[0] is True  # match_found
        assert cached_result[1] == 100.0  # confidence


if __name__ == "__main__":
    pytest.main([__file__])
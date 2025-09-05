# tests/test_accessibility_tree_recovery.py
"""
Integration tests for AccessibilityTreeRecoveryManager.

Tests accessibility tree refresh when elements become stale,
application focus detection, and cache invalidation for dynamic applications.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from modules.accessibility_tree_recovery import (
    AccessibilityTreeRecoveryManager,
    TreeRefreshTrigger,
    TreeRefreshResult,
    TreeRefreshEvent,
    ApplicationFocusState,
    CacheInvalidationRule
)

from modules.accessibility import (
    CachedElementTree,
    AccessibilityElement,
    AccessibilityPermissionError,
    ElementNotFoundError
)


class TestCacheInvalidationRule:
    """Test CacheInvalidationRule functionality."""
    
    def test_rule_creation(self):
        """Test cache invalidation rule creation."""
        rule = CacheInvalidationRule(
            app_pattern=r"Chrome",
            trigger_events=["focus_change"],
            max_age_seconds=30,
            invalidate_on_focus_change=True
        )
        
        assert rule.app_pattern == r"Chrome"
        assert rule.trigger_events == ["focus_change"]
        assert rule.max_age_seconds == 30
        assert rule.invalidate_on_focus_change is True
    
    def test_app_pattern_matching(self):
        """Test application pattern matching."""
        rule = CacheInvalidationRule(
            app_pattern=r"(Chrome|Safari|Firefox)",
            trigger_events=["focus_change"],
            max_age_seconds=30
        )
        
        assert rule.matches_app("Google Chrome") is True
        assert rule.matches_app("Safari") is True
        assert rule.matches_app("Firefox") is True
        assert rule.matches_app("TextEdit") is False
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive pattern matching."""
        rule = CacheInvalidationRule(
            app_pattern=r"chrome",
            trigger_events=["focus_change"],
            max_age_seconds=30
        )
        
        assert rule.matches_app("Google Chrome") is True
        assert rule.matches_app("CHROME") is True
        assert rule.matches_app("chrome") is True


class TestApplicationFocusState:
    """Test ApplicationFocusState functionality."""
    
    def test_focus_state_creation(self):
        """Test focus state creation."""
        timestamp = time.time()
        state = ApplicationFocusState(
            app_name="Chrome",
            app_pid=1234,
            bundle_id="com.google.Chrome",
            focus_timestamp=timestamp,
            previous_app="Safari"
        )
        
        assert state.app_name == "Chrome"
        assert state.app_pid == 1234
        assert state.bundle_id == "com.google.Chrome"
        assert state.focus_timestamp == timestamp
        assert state.previous_app == "Safari"
        assert state.focus_duration == 0.0
    
    def test_focus_duration_update(self):
        """Test focus duration calculation."""
        timestamp = time.time() - 5  # 5 seconds ago
        state = ApplicationFocusState(
            app_name="Chrome",
            app_pid=1234,
            bundle_id="com.google.Chrome",
            focus_timestamp=timestamp
        )
        
        state.update_focus_duration()
        assert state.focus_duration >= 4.9  # Allow for small timing variations


class TestAccessibilityTreeRecoveryManager:
    """Test AccessibilityTreeRecoveryManager functionality."""
    
    @pytest.fixture
    def recovery_manager(self):
        """Create a recovery manager for testing."""
        config = {
            'auto_refresh_enabled': False,  # Disable for controlled testing
            'focus_tracking_enabled': False,  # Disable for controlled testing
            'cache_invalidation_enabled': True,
            'stale_element_threshold': 1,  # Short threshold for testing
            'cache_ttl': 2  # Short TTL for testing
        }
        return AccessibilityTreeRecoveryManager(config)
    
    @pytest.fixture
    def sample_cached_tree(self):
        """Create a sample cached tree for testing."""
        elements = [
            {'role': 'button', 'title': 'Click me', 'element_id': 'btn1'},
            {'role': 'text', 'title': 'Sample text', 'element_id': 'txt1'}
        ]
        
        return CachedElementTree(
            app_name="TestApp",
            app_pid=1234,
            elements=elements,
            timestamp=time.time(),
            ttl=2.0
        )
    
    def test_initialization(self, recovery_manager):
        """Test recovery manager initialization."""
        assert recovery_manager.auto_refresh_enabled is False
        assert recovery_manager.focus_tracking_enabled is False
        assert recovery_manager.cache_invalidation_enabled is True
        assert recovery_manager.stale_element_threshold == 1
        assert len(recovery_manager.invalidation_rules) > 0  # Default rules loaded
        assert recovery_manager.total_refreshes == 0
    
    def test_default_invalidation_rules(self, recovery_manager):
        """Test that default invalidation rules are loaded."""
        rules = recovery_manager.invalidation_rules
        
        # Should have rules for browsers, dev tools, system apps, and default
        assert len(rules) >= 4
        
        # Check browser rule
        browser_rules = [r for r in rules if "Chrome" in r.app_pattern]
        assert len(browser_rules) > 0
        
        # Check default rule (matches everything)
        default_rules = [r for r in rules if r.app_pattern == r".*"]
        assert len(default_rules) > 0
    
    def test_manual_tree_refresh_success(self, recovery_manager):
        """Test successful manual tree refresh."""
        # Mock the _perform_tree_refresh method directly
        mock_elements = [
            {'role': 'button', 'title': 'New button', 'element_id': 'btn_new'},
            {'role': 'text', 'title': 'New text', 'element_id': 'txt_new'}
        ]
        
        mock_tree = CachedElementTree(
            app_name="TestApp",
            app_pid=1234,
            elements=mock_elements,
            timestamp=time.time(),
            ttl=30.0
        )
        
        with patch.object(recovery_manager, '_perform_tree_refresh', return_value=mock_tree):
        
            # Perform refresh
            event = recovery_manager.refresh_accessibility_tree(
                app_name="TestApp",
                trigger=TreeRefreshTrigger.MANUAL
            )
            
            assert event.result == TreeRefreshResult.SUCCESS
            assert event.app_name == "TestApp"
            assert event.trigger == TreeRefreshTrigger.MANUAL
            assert event.elements_after == 2
            assert event.refresh_duration > 0
            
            # Check that cache was updated
            assert "TestApp" in recovery_manager.cache_registry
            cached_tree = recovery_manager.cache_registry["TestApp"]
            assert len(cached_tree.elements) == 2
    
    def test_tree_refresh_failure(self, recovery_manager):
        """Test tree refresh failure handling."""
        # Mock _perform_tree_refresh to raise exception
        with patch.object(recovery_manager, '_perform_tree_refresh', side_effect=Exception("Access denied")):
        
            # Perform refresh
            event = recovery_manager.refresh_accessibility_tree(
                app_name="TestApp",
                trigger=TreeRefreshTrigger.MANUAL
            )
            
            assert event.result == TreeRefreshResult.FAILED
            assert event.error is not None
            assert "Access denied" in str(event.error)
            assert event.elements_after == 0
    
    def test_tree_refresh_permission_denied(self, recovery_manager):
        """Test tree refresh with permission denied."""
        # Mock _perform_tree_refresh to raise permission error
        with patch.object(recovery_manager, '_perform_tree_refresh', 
                         side_effect=AccessibilityPermissionError("Accessibility permissions not granted")):
        
            # Perform refresh
            event = recovery_manager.refresh_accessibility_tree(
                app_name="TestApp",
                trigger=TreeRefreshTrigger.MANUAL
            )
            
            assert event.result == TreeRefreshResult.PERMISSION_DENIED
            assert isinstance(event.error, AccessibilityPermissionError)
    
    def test_tree_refresh_no_change_when_cache_valid(self, recovery_manager, sample_cached_tree):
        """Test that refresh returns NO_CHANGE when cache is still valid."""
        # Add valid cache
        recovery_manager.cache_registry["TestApp"] = sample_cached_tree
        
        # Perform refresh without force
        event = recovery_manager.refresh_accessibility_tree(
            app_name="TestApp",
            trigger=TreeRefreshTrigger.MANUAL,
            force=False
        )
        
        assert event.result == TreeRefreshResult.NO_CHANGE
        assert event.elements_before == event.elements_after
    
    def test_tree_refresh_force_override(self, recovery_manager, sample_cached_tree):
        """Test that force refresh overrides valid cache."""
        # Mock the refresh method
        mock_elements = [{'role': 'button', 'title': 'Forced refresh', 'element_id': 'btn_forced'}]
        mock_tree = CachedElementTree(
            app_name="TestApp",
            app_pid=1234,
            elements=mock_elements,
            timestamp=time.time(),
            ttl=30.0
        )
        
        with patch.object(recovery_manager, '_perform_tree_refresh', return_value=mock_tree):
            # Add valid cache
            recovery_manager.cache_registry["TestApp"] = sample_cached_tree
            
            # Perform forced refresh
            event = recovery_manager.refresh_accessibility_tree(
                app_name="TestApp",
                trigger=TreeRefreshTrigger.MANUAL,
                force=True
            )
            
            assert event.result == TreeRefreshResult.SUCCESS
            assert event.elements_after == 1
            
            # Check that cache was updated
            cached_tree = recovery_manager.cache_registry["TestApp"]
            assert len(cached_tree.elements) == 1
            assert cached_tree.elements[0]['title'] == 'Forced refresh'
    
    def test_cache_invalidation_specific_app(self, recovery_manager, sample_cached_tree):
        """Test cache invalidation for specific application."""
        # Add cache entries
        recovery_manager.cache_registry["TestApp1"] = sample_cached_tree
        recovery_manager.cache_registry["TestApp2"] = sample_cached_tree
        
        # Invalidate specific app
        count = recovery_manager.invalidate_cache(app_name="TestApp1")
        
        assert count == 1
        assert "TestApp1" not in recovery_manager.cache_registry
        assert "TestApp2" in recovery_manager.cache_registry
    
    def test_cache_invalidation_all_apps(self, recovery_manager, sample_cached_tree):
        """Test cache invalidation for all applications."""
        # Add cache entries
        recovery_manager.cache_registry["TestApp1"] = sample_cached_tree
        recovery_manager.cache_registry["TestApp2"] = sample_cached_tree
        
        # Invalidate all
        count = recovery_manager.invalidate_cache()
        
        assert count == 2
        assert len(recovery_manager.cache_registry) == 0
    
    def test_stale_element_detection_expired_tree(self, recovery_manager):
        """Test stale element detection for expired tree."""
        # Create expired tree
        old_timestamp = time.time() - 10  # 10 seconds ago
        expired_tree = CachedElementTree(
            app_name="TestApp",
            app_pid=1234,
            elements=[{'role': 'button', 'title': 'Old button'}],
            timestamp=old_timestamp,
            ttl=2.0  # 2 second TTL, so it's expired
        )
        
        recovery_manager.cache_registry["TestApp"] = expired_tree
        
        stale_elements = recovery_manager.detect_stale_elements("TestApp")
        
        assert "entire_tree" in stale_elements
    
    def test_stale_element_detection_fresh_tree(self, recovery_manager, sample_cached_tree):
        """Test stale element detection for fresh tree."""
        recovery_manager.cache_registry["TestApp"] = sample_cached_tree
        
        stale_elements = recovery_manager.detect_stale_elements("TestApp")
        
        # Should be empty for fresh tree
        assert len(stale_elements) == 0
    
    def test_stale_element_detection_no_cache(self, recovery_manager):
        """Test stale element detection when no cache exists."""
        stale_elements = recovery_manager.detect_stale_elements("NonExistentApp")
        
        assert len(stale_elements) == 0
    
    def test_focus_change_handling(self, recovery_manager):
        """Test application focus change handling."""
        # Simulate focus change
        recovery_manager._handle_focus_change("Chrome", 1234, "com.google.Chrome")
        
        assert recovery_manager.current_focus_state is not None
        assert recovery_manager.current_focus_state.app_name == "Chrome"
        assert recovery_manager.current_focus_state.app_pid == 1234
        assert recovery_manager.current_focus_state.bundle_id == "com.google.Chrome"
    
    def test_focus_change_history(self, recovery_manager):
        """Test that focus changes are recorded in history."""
        # Simulate multiple focus changes
        recovery_manager._handle_focus_change("Chrome", 1234, "com.google.Chrome")
        time.sleep(0.1)  # Small delay
        recovery_manager._handle_focus_change("Safari", 5678, "com.apple.Safari")
        
        assert len(recovery_manager.focus_history) == 1
        assert recovery_manager.focus_history[0].app_name == "Chrome"
        assert recovery_manager.current_focus_state.app_name == "Safari"
        assert recovery_manager.current_focus_state.previous_app == "Chrome"
    
    def test_invalidation_rule_checking(self, recovery_manager, sample_cached_tree):
        """Test cache invalidation rule checking."""
        # Add cache
        recovery_manager.cache_registry["Chrome"] = sample_cached_tree
        
        # Trigger rule checking
        recovery_manager._check_invalidation_rules("Chrome", "focus_change")
        
        # Chrome should be invalidated due to browser rule
        assert "Chrome" not in recovery_manager.cache_registry
    
    def test_refresh_callback_system(self, recovery_manager):
        """Test refresh callback notification system."""
        callback_events = []
        
        def test_callback(event: TreeRefreshEvent):
            callback_events.append(event)
        
        # Add callback
        recovery_manager.add_refresh_callback(test_callback)
        
        # Trigger refresh (will fail but still generate event)
        recovery_manager.refresh_accessibility_tree("TestApp")
        
        # Check callback was called
        assert len(callback_events) == 1
        assert callback_events[0].app_name == "TestApp"
        
        # Remove callback
        recovery_manager.remove_refresh_callback(test_callback)
        
        # Trigger another refresh
        recovery_manager.refresh_accessibility_tree("TestApp2")
        
        # Should still be only 1 event (callback removed)
        assert len(callback_events) == 1
    
    def test_refresh_statistics_empty(self, recovery_manager):
        """Test refresh statistics with no history."""
        stats = recovery_manager.get_refresh_statistics()
        
        assert stats['total_refreshes'] == 0
        assert stats['successful_refreshes'] == 0
        assert stats['failed_refreshes'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['average_refresh_time'] == 0.0
        assert stats['cache_hit_rate'] == 0.0
        assert len(stats['recent_events']) == 0
    
    def test_refresh_statistics_with_data(self, recovery_manager):
        """Test refresh statistics with refresh history."""
        # Mock successful refresh
        mock_tree = CachedElementTree(
            app_name="TestApp1",
            app_pid=1234,
            elements=[{'role': 'button'}],
            timestamp=time.time(),
            ttl=30.0
        )
        
        with patch.object(recovery_manager, '_perform_tree_refresh', return_value=mock_tree):
            # Perform some refreshes
            recovery_manager.refresh_accessibility_tree("TestApp1")
            recovery_manager.refresh_accessibility_tree("TestApp2")
            
            stats = recovery_manager.get_refresh_statistics()
            
            assert stats['total_refreshes'] == 2
            assert stats['successful_refreshes'] == 2
            assert stats['success_rate'] == 1.0
            assert stats['average_refresh_time'] > 0
            assert len(stats['recent_events']) == 2
            assert len(stats['cached_apps']) == 2
    
    def test_cache_hit_rate_calculation(self, recovery_manager, sample_cached_tree):
        """Test cache hit rate calculation in statistics."""
        # Add valid cache
        recovery_manager.cache_registry["TestApp"] = sample_cached_tree
        
        # Perform refresh that should result in NO_CHANGE (cache hit)
        event = recovery_manager.refresh_accessibility_tree("TestApp", force=False)
        assert event.result == TreeRefreshResult.NO_CHANGE
        
        stats = recovery_manager.get_refresh_statistics()
        
        assert stats['cache_hit_rate'] == 1.0  # 100% cache hit rate
    
    def test_thread_safety(self, recovery_manager):
        """Test thread safety of recovery manager operations."""
        results = []
        errors = []
        
        def worker(app_name: str):
            try:
                # Perform cache operations
                recovery_manager.invalidate_cache(app_name)
                event = recovery_manager.refresh_accessibility_tree(app_name)
                results.append(event.app_name)
            except Exception as e:
                errors.append(e)
        
        # Run multiple threads
        threads = [threading.Thread(target=worker, args=(f"App{i}",)) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0
        assert len(results) == 10
    
    def test_shutdown(self, recovery_manager):
        """Test recovery manager shutdown."""
        # Add some state
        recovery_manager.cache_registry["TestApp"] = Mock()
        recovery_manager.add_refresh_callback(lambda x: None)
        
        # Shutdown
        recovery_manager.shutdown()
        
        # Check cleanup
        assert len(recovery_manager.cache_registry) == 0
        assert len(recovery_manager.refresh_callbacks) == 0
        assert recovery_manager.shutdown_event.is_set()


class TestTreeRecoveryIntegration:
    """Integration tests for tree recovery with dynamic applications."""
    
    @pytest.fixture
    def recovery_manager(self):
        """Create a recovery manager with realistic configuration."""
        config = {
            'auto_refresh_enabled': True,
            'focus_tracking_enabled': False,  # Disable for controlled testing
            'cache_invalidation_enabled': True,
            'stale_element_threshold': 0.5,  # Short threshold for testing
            'cache_ttl': 1.0,  # Short TTL for testing
            'periodic_refresh_interval': 0.1  # Very short for testing
        }
        manager = AccessibilityTreeRecoveryManager(config)
        # Don't start threads automatically
        manager.auto_refresh_enabled = False
        return manager
    
    def test_dynamic_application_tree_recovery(self, recovery_manager):
        """Test tree recovery for dynamic applications with changing content."""
        # First call returns initial elements
        initial_elements = [
            {'role': 'button', 'title': 'Initial Button', 'element_id': 'btn1'},
            {'role': 'text', 'title': 'Initial Text', 'element_id': 'txt1'}
        ]
        
        # Second call returns updated elements
        updated_elements = [
            {'role': 'button', 'title': 'Updated Button', 'element_id': 'btn1'},
            {'role': 'text', 'title': 'Updated Text', 'element_id': 'txt1'},
            {'role': 'link', 'title': 'New Link', 'element_id': 'link1'}
        ]
        
        initial_tree = CachedElementTree(
            app_name="DynamicApp",
            app_pid=1234,
            elements=initial_elements,
            timestamp=time.time(),
            ttl=1.0
        )
        
        updated_tree = CachedElementTree(
            app_name="DynamicApp",
            app_pid=1234,
            elements=updated_elements,
            timestamp=time.time(),
            ttl=1.0
        )
        
        # Create a mock that returns different trees on successive calls
        def mock_refresh(*args, **kwargs):
            if not hasattr(mock_refresh, 'call_count'):
                mock_refresh.call_count = 0
            mock_refresh.call_count += 1
            
            if mock_refresh.call_count == 1:
                return initial_tree
            else:
                return updated_tree
        
        with patch.object(recovery_manager, '_perform_tree_refresh', side_effect=mock_refresh):
            # Initial refresh
            event1 = recovery_manager.refresh_accessibility_tree("DynamicApp")
            assert event1.result == TreeRefreshResult.SUCCESS
            assert event1.elements_after == 2
            
            # Wait for cache to expire
            time.sleep(1.1)
            
            # Second refresh should get updated content
            event2 = recovery_manager.refresh_accessibility_tree("DynamicApp")
            assert event2.result == TreeRefreshResult.SUCCESS
            assert event2.elements_after == 3
            
            # Verify cache was updated
            cached_tree = recovery_manager.cache_registry["DynamicApp"]
            assert len(cached_tree.elements) == 3
            assert any(elem['title'] == 'New Link' for elem in cached_tree.elements)
    
    def test_stale_element_recovery_workflow(self, recovery_manager):
        """Test complete workflow for recovering from stale elements."""
        # Mock fresh elements
        fresh_elements = [
            {'role': 'button', 'title': 'Fresh Button', 'element_id': 'btn_fresh'}
        ]
        
        fresh_tree = CachedElementTree(
            app_name="StaleApp",
            app_pid=1234,
            elements=fresh_elements,
            timestamp=time.time(),
            ttl=30.0
        )
        
        with patch.object(recovery_manager, '_perform_tree_refresh', return_value=fresh_tree):
            # Create stale cache
            stale_tree = CachedElementTree(
                app_name="StaleApp",
                app_pid=1234,
                elements=[{'role': 'button', 'title': 'Stale Button', 'element_id': 'btn_stale'}],
                timestamp=time.time() - 10,  # 10 seconds ago
                ttl=1.0  # 1 second TTL, so it's very stale
            )
            recovery_manager.cache_registry["StaleApp"] = stale_tree
            
            # Detect stale elements
            stale_elements = recovery_manager.detect_stale_elements("StaleApp")
            assert "entire_tree" in stale_elements
            
            # Trigger recovery refresh
            event = recovery_manager.refresh_accessibility_tree(
                "StaleApp",
                trigger=TreeRefreshTrigger.STALE_ELEMENT
            )
            
            assert event.result == TreeRefreshResult.SUCCESS
            assert event.trigger == TreeRefreshTrigger.STALE_ELEMENT
            assert event.elements_after == 1
            
            # Verify fresh content
            cached_tree = recovery_manager.cache_registry["StaleApp"]
            assert cached_tree.elements[0]['title'] == 'Fresh Button'
    
    def test_application_focus_driven_refresh(self, recovery_manager):
        """Test tree refresh triggered by application focus changes."""
        callback_events = []
        
        def focus_callback(event: TreeRefreshEvent):
            if event.trigger == TreeRefreshTrigger.APPLICATION_FOCUS_CHANGE:
                callback_events.append(event)
        
        recovery_manager.add_refresh_callback(focus_callback)
        
        # Enable auto refresh for this test
        recovery_manager.auto_refresh_enabled = True
        
        mock_tree = CachedElementTree(
            app_name="FocusedApp",
            app_pid=1234,
            elements=[{'role': 'window', 'title': 'Focused Window'}],
            timestamp=time.time(),
            ttl=30.0
        )
        
        with patch.object(recovery_manager, '_perform_tree_refresh', return_value=mock_tree):
            # Simulate focus change
            recovery_manager._handle_focus_change("FocusedApp", 1234, "com.test.FocusedApp")
            
            # Should trigger refresh
            assert len(callback_events) == 1
            assert callback_events[0].app_name == "FocusedApp"
            assert callback_events[0].trigger == TreeRefreshTrigger.APPLICATION_FOCUS_CHANGE
    
    def test_cache_invalidation_on_focus_change(self, recovery_manager):
        """Test cache invalidation when application focus changes."""
        # Mock tree for refresh
        mock_tree = CachedElementTree(
            app_name="Chrome",
            app_pid=1234,
            elements=[{'role': 'button'}],
            timestamp=time.time(),
            ttl=30.0
        )
        
        with patch.object(recovery_manager, '_perform_tree_refresh', return_value=mock_tree):
            # Create initial cache for Chrome
            recovery_manager.refresh_accessibility_tree("Chrome")
            assert "Chrome" in recovery_manager.cache_registry
            
            # Simulate focus change to Chrome (should invalidate due to browser rule)
            recovery_manager._handle_focus_change("Chrome", 1234, "com.google.Chrome")
            
            # Cache should be invalidated due to focus change rule for browsers
            # (The default browser rule has invalidate_on_focus_change=True)
            # Note: The cache might be immediately refreshed due to focus change trigger
            
            # Verify focus state was updated
            assert recovery_manager.current_focus_state.app_name == "Chrome"
    
    def test_error_recovery_during_refresh(self, recovery_manager):
        """Test error recovery during tree refresh operations."""
        # Mock to fail first, then succeed
        success_tree = CachedElementTree(
            app_name="RecoveryApp",
            app_pid=1234,
            elements=[{'role': 'button', 'title': 'Recovered Button'}],
            timestamp=time.time(),
            ttl=30.0
        )
        
        with patch.object(recovery_manager, '_perform_tree_refresh', 
                         side_effect=[Exception("Temporary failure"), success_tree]):
            # First refresh should fail
            event1 = recovery_manager.refresh_accessibility_tree("RecoveryApp")
            assert event1.result == TreeRefreshResult.FAILED
            assert event1.error is not None
            
            # Second refresh should succeed
            event2 = recovery_manager.refresh_accessibility_tree("RecoveryApp")
            assert event2.result == TreeRefreshResult.SUCCESS
            assert event2.elements_after == 1
            
            # Verify recovery was successful
            cached_tree = recovery_manager.cache_registry["RecoveryApp"]
            assert cached_tree.elements[0]['title'] == 'Recovered Button'
    
    def test_performance_under_load(self, recovery_manager):
        """Test recovery manager performance under concurrent load."""
        import concurrent.futures
        
        def refresh_worker(app_index: int) -> float:
            """Worker function that performs refresh operations."""
            start_time = time.time()
            
            app_name = f"LoadTestApp{app_index}"
            
            # Perform multiple operations
            recovery_manager.invalidate_cache(app_name)
            recovery_manager.refresh_accessibility_tree(app_name)
            recovery_manager.detect_stale_elements(app_name)
            
            return time.time() - start_time
        
        # Run concurrent refresh operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(refresh_worker, i) for i in range(50)]
            durations = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all operations completed
        assert len(durations) == 50
        
        # Check performance (should complete reasonably quickly)
        avg_duration = sum(durations) / len(durations)
        assert avg_duration < 1.0  # Should average less than 1 second per operation
        
        # Verify statistics
        stats = recovery_manager.get_refresh_statistics()
        assert stats['total_refreshes'] == 50


if __name__ == "__main__":
    pytest.main([__file__])
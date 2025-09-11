"""
Unit tests for unified text capture functionality in AccessibilityModule.

Tests the get_selected_text() method with mocked accessibility and clipboard operations.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call
from typing import Optional, Any

# Import the modules to test
from modules.accessibility import AccessibilityModule, AccessibilityPermissionError, AccessibilityAPIUnavailableError
from modules.automation import AutomationModule


class TestUnifiedTextCapture:
    """Test suite for unified text capture interface."""
    
    @pytest.fixture
    def accessibility_module(self):
        """Create an AccessibilityModule instance for testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True):
            with patch('modules.accessibility.AXUIElementCreateSystemWide'):
                with patch('modules.accessibility.NSWorkspace'):
                    module = AccessibilityModule()
                    module.accessibility_enabled = True
                    module.degraded_mode = False
                    return module
    
    @pytest.fixture
    def automation_module(self):
        """Create an AutomationModule instance for testing."""
        return AutomationModule()
    
    def test_get_selected_text_accessibility_success(self, accessibility_module):
        """Test successful text capture via accessibility API."""
        test_text = "This is selected text"
        
        # Mock the accessibility method to return text
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=test_text):
            with patch.object(accessibility_module, '_log_performance_metrics'):
                result = accessibility_module.get_selected_text()
        
        assert result == test_text
    
    def test_get_selected_text_accessibility_no_text(self, accessibility_module):
        """Test accessibility API when no text is selected."""
        # Mock the accessibility method to return None (no text selected)
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=None):
            # Mock automation module creation
            mock_automation = Mock()
            mock_automation.get_selected_text_via_clipboard.return_value = None
            accessibility_module._automation_module = mock_automation
            
            with patch.object(accessibility_module, '_log_performance_metrics'):
                result = accessibility_module.get_selected_text()
        
        assert result is None
    
    def test_get_selected_text_fallback_to_clipboard(self, accessibility_module):
        """Test fallback to clipboard method when accessibility fails."""
        test_text = "Clipboard captured text"
        
        # Mock accessibility method to raise permission error
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', 
                         side_effect=AccessibilityPermissionError("Permission denied")):
            # Mock automation module and clipboard method
            mock_automation = Mock()
            mock_automation.get_selected_text_via_clipboard.return_value = test_text
            accessibility_module._automation_module = mock_automation
            
            with patch.object(accessibility_module, '_log_performance_metrics'):
                result = accessibility_module.get_selected_text()
        
        assert result == test_text
        mock_automation.get_selected_text_via_clipboard.assert_called_once()
    
    def test_get_selected_text_fallback_api_unavailable(self, accessibility_module):
        """Test fallback when accessibility API is unavailable."""
        test_text = "Fallback text"
        
        # Mock accessibility method to raise API unavailable error
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility',
                         side_effect=AccessibilityAPIUnavailableError("API unavailable")):
            # Mock automation module
            mock_automation = Mock()
            mock_automation.get_selected_text_via_clipboard.return_value = test_text
            accessibility_module._automation_module = mock_automation
            
            with patch.object(accessibility_module, '_log_performance_metrics'):
                result = accessibility_module.get_selected_text()
        
        assert result == test_text
    
    def test_get_selected_text_both_methods_no_text(self, accessibility_module):
        """Test when both methods return None (no text selected)."""
        # Mock both methods to return None
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=None):
            mock_automation = Mock()
            mock_automation.get_selected_text_via_clipboard.return_value = None
            accessibility_module._automation_module = mock_automation
            
            with patch.object(accessibility_module, '_log_performance_metrics'):
                result = accessibility_module.get_selected_text()
        
        assert result is None
    
    def test_get_selected_text_both_methods_fail(self, accessibility_module):
        """Test when both methods fail with errors."""
        # Mock accessibility method to raise permission error
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility',
                         side_effect=AccessibilityPermissionError("Permission denied")):
            # Mock clipboard method to fail
            mock_automation = Mock()
            mock_automation.get_selected_text_via_clipboard.side_effect = Exception("Clipboard error")
            accessibility_module._automation_module = mock_automation
            
            with patch.object(accessibility_module, '_log_performance_metrics'):
                with pytest.raises(Exception) as exc_info:
                    accessibility_module.get_selected_text()
                
                assert "Accessibility permissions required" in str(exc_info.value)
    
    def test_get_selected_text_clipboard_error_handling(self, accessibility_module):
        """Test specific clipboard error handling when accessibility method also fails."""
        # Mock accessibility method to fail with an error (not just return None)
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility',
                         side_effect=AccessibilityAPIUnavailableError("API unavailable")):
            # Mock clipboard method to fail with clipboard-specific error
            mock_automation = Mock()
            mock_automation.get_selected_text_via_clipboard.side_effect = Exception("Clipboard access denied")
            accessibility_module._automation_module = mock_automation
            
            with patch.object(accessibility_module, '_log_performance_metrics'):
                with pytest.raises(Exception) as exc_info:
                    accessibility_module.get_selected_text()
                
                assert "Cannot access clipboard" in str(exc_info.value)
    
    def test_get_selected_text_performance_logging(self, accessibility_module):
        """Test that performance metrics are logged correctly."""
        test_text = "Performance test text"
        
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=test_text):
            with patch.object(accessibility_module, '_log_performance_metrics') as mock_log:
                result = accessibility_module.get_selected_text()
        
        assert result == test_text
        mock_log.assert_called_once()
        
        # Check the logged metrics
        call_args = mock_log.call_args
        assert call_args[0][0] == "get_selected_text_unified"  # operation name
        assert call_args[0][2] is True  # success
        assert call_args[0][3]['method_used'] == 'accessibility_api'
        assert call_args[0][3]['text_length'] == len(test_text)
        assert call_args[0][3]['fallback_triggered'] is False
    
    def test_get_selected_text_fallback_performance_logging(self, accessibility_module):
        """Test performance logging when fallback is triggered."""
        test_text = "Fallback performance test"
        
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility',
                         side_effect=AccessibilityPermissionError("Permission denied")):
            mock_automation = Mock()
            mock_automation.get_selected_text_via_clipboard.return_value = test_text
            accessibility_module._automation_module = mock_automation
            
            with patch.object(accessibility_module, '_log_performance_metrics') as mock_log:
                result = accessibility_module.get_selected_text()
        
        assert result == test_text
        mock_log.assert_called_once()
        
        # Check the logged metrics for fallback
        call_args = mock_log.call_args
        assert call_args[0][0] == "get_selected_text_unified"
        assert call_args[0][2] is True  # success
        assert call_args[0][3]['method_used'] == 'clipboard_fallback'
        assert call_args[0][3]['fallback_triggered'] is True
    
    def test_get_selected_text_automation_module_creation(self, accessibility_module):
        """Test that AutomationModule is created when needed."""
        test_text = "Auto-creation test"
        
        # Ensure no automation module exists
        if hasattr(accessibility_module, '_automation_module'):
            delattr(accessibility_module, '_automation_module')
        
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=None):
            with patch('modules.automation.AutomationModule') as mock_automation_class:
                mock_automation_instance = Mock()
                mock_automation_instance.get_selected_text_via_clipboard.return_value = test_text
                mock_automation_class.return_value = mock_automation_instance
                
                with patch.object(accessibility_module, '_log_performance_metrics'):
                    result = accessibility_module.get_selected_text()
        
        assert result == test_text
        mock_automation_class.assert_called_once()
        assert hasattr(accessibility_module, '_automation_module')
    
    def test_get_selected_text_special_characters(self, accessibility_module):
        """Test text capture with special characters and Unicode."""
        test_text = "Special chars: éñ中文🚀\n\tTabbed text"
        
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=test_text):
            with patch.object(accessibility_module, '_log_performance_metrics'):
                result = accessibility_module.get_selected_text()
        
        assert result == test_text
        assert len(result) == len(test_text)
    
    def test_get_selected_text_long_text(self, accessibility_module):
        """Test text capture with very long text."""
        test_text = "A" * 10000  # 10KB of text
        
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=test_text):
            with patch.object(accessibility_module, '_log_performance_metrics'):
                result = accessibility_module.get_selected_text()
        
        assert result == test_text
        assert len(result) == 10000
    
    def test_get_selected_text_empty_string(self, accessibility_module):
        """Test handling of empty string vs None."""
        # Empty string should be returned as-is (valid selection of empty text)
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=""):
            with patch.object(accessibility_module, '_log_performance_metrics'):
                result = accessibility_module.get_selected_text()
        
        # Empty string from accessibility API should be returned as-is
        assert result == ""
    
    def test_get_selected_text_whitespace_only(self, accessibility_module):
        """Test handling of whitespace-only text."""
        test_text = "   \n\t   "  # Only whitespace
        
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=test_text):
            with patch.object(accessibility_module, '_log_performance_metrics'):
                result = accessibility_module.get_selected_text()
        
        # Whitespace-only text should still be returned as-is
        assert result == test_text


class TestTextCaptureIntegration:
    """Integration tests for text capture across different scenarios."""
    
    @pytest.fixture
    def accessibility_module(self):
        """Create an AccessibilityModule instance for integration testing."""
        with patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True):
            with patch('modules.accessibility.AXUIElementCreateSystemWide'):
                with patch('modules.accessibility.NSWorkspace'):
                    module = AccessibilityModule()
                    module.accessibility_enabled = True
                    module.degraded_mode = False
                    return module
    
    def test_text_capture_timing_requirements(self, accessibility_module):
        """Test that text capture meets timing requirements."""
        test_text = "Timing test text"
        
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=test_text):
            with patch.object(accessibility_module, '_log_performance_metrics') as mock_log:
                start_time = time.time()
                result = accessibility_module.get_selected_text()
                end_time = time.time()
        
        assert result == test_text
        execution_time_ms = (end_time - start_time) * 1000
        
        # Should complete within reasonable time (< 500ms for accessibility API)
        assert execution_time_ms < 500
        
        # Check that performance was logged
        mock_log.assert_called_once()
    
    def test_text_capture_fallback_timing(self, accessibility_module):
        """Test timing when fallback is triggered."""
        test_text = "Fallback timing test"
        
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility',
                         side_effect=AccessibilityPermissionError("Permission denied")):
            mock_automation = Mock()
            mock_automation.get_selected_text_via_clipboard.return_value = test_text
            accessibility_module._automation_module = mock_automation
            
            with patch.object(accessibility_module, '_log_performance_metrics'):
                start_time = time.time()
                result = accessibility_module.get_selected_text()
                end_time = time.time()
        
        assert result == test_text
        execution_time_ms = (end_time - start_time) * 1000
        
        # Should complete within reasonable time even with fallback (< 1000ms)
        assert execution_time_ms < 1000
    
    def test_text_capture_error_recovery(self, accessibility_module):
        """Test error recovery and user feedback."""
        # Test permission error scenario
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility',
                         side_effect=AccessibilityPermissionError("Permission denied")):
            mock_automation = Mock()
            mock_automation.get_selected_text_via_clipboard.side_effect = Exception("Clipboard error")
            accessibility_module._automation_module = mock_automation
            
            with patch.object(accessibility_module, '_log_performance_metrics'):
                with pytest.raises(Exception) as exc_info:
                    accessibility_module.get_selected_text()
                
                # Should provide clear user guidance
                error_message = str(exc_info.value)
                assert "Accessibility permissions required" in error_message
                assert "System Preferences" in error_message
    
    def test_text_capture_success_rates_tracking(self, accessibility_module):
        """Test that success rates are properly tracked."""
        test_text = "Success rate test"
        
        # Test multiple successful captures
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=test_text):
            with patch.object(accessibility_module, '_log_performance_metrics') as mock_log:
                for _ in range(5):
                    result = accessibility_module.get_selected_text()
                    assert result == test_text
        
        # Should have logged performance 5 times
        assert mock_log.call_count == 5
        
        # All calls should indicate success
        for call in mock_log.call_args_list:
            assert call[0][2] is True  # success parameter
    
    def test_text_capture_concurrent_access(self, accessibility_module):
        """Test text capture under concurrent access scenarios."""
        import threading
        import queue
        
        test_text = "Concurrent test text"
        results = queue.Queue()
        errors = queue.Queue()
        
        def capture_text():
            try:
                result = accessibility_module.get_selected_text()
                results.put(result)
            except Exception as e:
                errors.put(e)
        
        with patch.object(accessibility_module, 'get_selected_text_via_accessibility', return_value=test_text):
            with patch.object(accessibility_module, '_log_performance_metrics'):
                # Start multiple threads
                threads = []
                for _ in range(3):
                    thread = threading.Thread(target=capture_text)
                    threads.append(thread)
                    thread.start()
                
                # Wait for all threads to complete
                for thread in threads:
                    thread.join(timeout=5)
        
        # Check results
        assert errors.empty(), f"Unexpected errors: {list(errors.queue)}"
        assert results.qsize() == 3
        
        # All results should be the test text
        while not results.empty():
            result = results.get()
            assert result == test_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
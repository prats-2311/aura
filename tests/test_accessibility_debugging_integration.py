"""
Integration tests for AccessibilityModule with debugging capabilities enabled.

Tests the integration of debugging tools with the accessibility module,
including permission validation, failure analysis, and comprehensive logging.
"""

import pytest
import unittest.mock as mock
import time
from unittest.mock import MagicMock, patch, call
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

# Import the modules to test
from modules.accessibility import AccessibilityModule, ElementMatchResult
from modules.permission_validator import PermissionStatus
from modules.accessibility_debugger import AccessibilityTreeDump, ElementAnalysisResult


@dataclass
class MockPermissionStatus:
    """Mock permission status for testing."""
    has_permissions: bool = True
    permission_level: str = 'FULL'
    missing_permissions: List[str] = None
    granted_permissions: List[str] = None
    can_request_permissions: bool = True
    system_version: str = '12.0'
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.missing_permissions is None:
            self.missing_permissions = []
        if self.granted_permissions is None:
            self.granted_permissions = ['basic_accessibility_access', 'system_wide_element_access']
        if self.recommendations is None:
            self.recommendations = []
    
    def is_sufficient_for_fast_path(self) -> bool:
        return self.has_permissions and self.permission_level in ['FULL', 'PARTIAL']
    
    def get_summary(self) -> str:
        return f"✅ Accessibility permissions granted ({self.permission_level})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'has_permissions': self.has_permissions,
            'permission_level': self.permission_level,
            'missing_permissions': self.missing_permissions,
            'granted_permissions': self.granted_permissions,
            'recommendations': self.recommendations
        }


@dataclass
class MockFailureAnalysis:
    """Mock failure analysis result for testing."""
    target_text: str
    search_strategy: str = "multi_strategy"
    matches_found: int = 0
    best_match: Optional[Dict[str, Any]] = None
    all_matches: List[Dict[str, Any]] = None
    similarity_scores: Dict[str, float] = None
    search_time_ms: float = 100.0
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.all_matches is None:
            self.all_matches = []
        if self.similarity_scores is None:
            self.similarity_scores = {}
        if self.recommendations is None:
            self.recommendations = [
                "Try using more specific text",
                "Check if the element is visible",
                "Verify the application is in focus"
            ]


class TestAccessibilityDebuggingIntegration:
    """Test suite for accessibility module debugging integration."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'fast_path_timeout_ms': 5000,
            'fuzzy_matching_timeout_ms': 200,
            'attribute_check_timeout_ms': 500,
            'fuzzy_matching_enabled': True,
            'fuzzy_confidence_threshold': 85,
            'clickable_roles': ['AXButton', 'AXMenuItem', 'AXLink'],
            'accessibility_attributes': ['AXTitle', 'AXDescription', 'AXValue'],
            'debug_logging': True,
            'log_fuzzy_match_scores': True,
            'performance_monitoring_enabled': True
        }
    
    @pytest.fixture
    def mock_permission_validator(self):
        """Mock permission validator for testing."""
        validator = MagicMock()
        validator.check_accessibility_permissions.return_value = MockPermissionStatus()
        validator.auto_request_permissions = True
        validator.monitor_permission_changes_enabled = True
        validator.add_permission_change_callback = MagicMock()
        validator.monitor_permission_changes = MagicMock()
        return validator
    
    @pytest.fixture
    def mock_accessibility_debugger(self):
        """Mock accessibility debugger for testing."""
        debugger = MagicMock()
        debugger.analyze_element_detection_failure.return_value = MockFailureAnalysis(
            target_text="Sign In",
            matches_found=2,
            best_match={
                'title': 'Sign In Button',
                'role': 'AXButton',
                'match_score': 95.0,
                'matched_text': 'Sign In'
            },
            all_matches=[
                {
                    'title': 'Sign In Button',
                    'role': 'AXButton',
                    'match_score': 95.0,
                    'matched_text': 'Sign In'
                },
                {
                    'title': 'Sign Up',
                    'role': 'AXButton',
                    'match_score': 70.0,
                    'matched_text': 'Sign Up'
                }
            ]
        )
        return debugger
    
    @pytest.fixture
    def mock_diagnostic_tools(self):
        """Mock diagnostic tools for testing."""
        tools = MagicMock()
        tools.run_comprehensive_diagnostics.return_value = {
            'permission_status': 'FULL',
            'accessibility_health': 'GOOD',
            'detected_issues': [],
            'recommendations': []
        }
        return tools
    
    @pytest.fixture
    def mock_error_recovery_manager(self):
        """Mock error recovery manager for testing."""
        manager = MagicMock()
        manager.attempt_recovery.return_value = {'success': True, 'actions_taken': ['retry']}
        return manager
    
    @patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True)
    @patch('modules.accessibility.AccessibilityDebugger')
    @patch('modules.accessibility.AccessibilityHealthChecker')
    @patch('modules.error_recovery.ErrorRecoveryManager')
    @patch('modules.accessibility.PermissionValidator')
    def test_debugging_tools_initialization(self, mock_perm_validator_class, mock_recovery_class, 
                                          mock_diagnostic_class, mock_debugger_class, mock_config):
        """Test that debugging tools are properly initialized."""
        # Setup mocks
        mock_perm_validator_class.return_value = self.mock_permission_validator()
        mock_debugger_class.return_value = self.mock_accessibility_debugger()
        mock_diagnostic_class.return_value = self.mock_diagnostic_tools()
        mock_recovery_class.return_value = self.mock_error_recovery_manager()
        
        # Create accessibility module
        with patch.object(AccessibilityModule, '_initialize_accessibility_api'):
            accessibility_module = AccessibilityModule()
        
        # Verify debugging tools were initialized
        assert accessibility_module.debug_mode_enabled is True
        assert accessibility_module.accessibility_debugger is not None
        assert accessibility_module.diagnostic_tools is not None
        assert accessibility_module.error_recovery_manager is not None
        
        # Verify debugger was initialized with correct config
        mock_debugger_class.assert_called_once()
        debug_config = mock_debugger_class.call_args[0][0]
        assert debug_config['debug_level'] == 'DETAILED'
        assert debug_config['auto_diagnostics'] is True
        assert debug_config['performance_tracking'] is True
    
    @patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True)
    def test_permission_validation_integration(self, mock_config):
        """Test integration of permission validation with debugging."""
        with patch.object(AccessibilityModule, '_initialize_debugging_tools'), \
             patch.object(AccessibilityModule, '_initialize_accessibility_api') as mock_init_api:
            
            # Create module with mock permission validator
            accessibility_module = AccessibilityModule()
            accessibility_module.permission_validator = self.mock_permission_validator()
            accessibility_module.debug_mode_enabled = True
            accessibility_module.debug_logging = True
            
            # Test permission validation during API initialization
            with patch.object(accessibility_module, 'logger') as mock_logger:
                accessibility_module._initialize_accessibility_api()
                
                # Verify permission status was checked
                accessibility_module.permission_validator.check_accessibility_permissions.assert_called_once()
                
                # Verify debug logging occurred
                mock_logger.debug.assert_any_call(
                    "Permission validation result: ✅ Accessibility permissions granted (FULL)"
                )
    
    @patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True)
    def test_find_element_enhanced_with_debugging(self, mock_config):
        """Test find_element_enhanced with debugging capabilities enabled."""
        with patch.object(AccessibilityModule, '_initialize_permission_validator'), \
             patch.object(AccessibilityModule, '_initialize_debugging_tools'), \
             patch.object(AccessibilityModule, '_initialize_accessibility_api'):
            
            # Create module with debugging enabled
            accessibility_module = AccessibilityModule()
            accessibility_module.debug_mode_enabled = True
            accessibility_module.debug_logging = True
            accessibility_module.accessibility_debugger = self.mock_accessibility_debugger()
            
            # Mock the enhanced role detection to return None (element not found)
            with patch.object(accessibility_module, 'is_enhanced_role_detection_available', return_value=True), \
                 patch.object(accessibility_module, '_find_element_with_enhanced_roles_tracked', return_value=(None, {})), \
                 patch.object(accessibility_module, '_find_element_button_only_fallback', return_value=None), \
                 patch.object(accessibility_module, 'logger') as mock_logger:
                
                # Call find_element_enhanced
                result = accessibility_module.find_element_enhanced(
                    role='AXButton',
                    label='Sign In',
                    app_name='TestApp'
                )
                
                # Verify debugging analysis was performed
                accessibility_module.accessibility_debugger.analyze_element_detection_failure.assert_called_once_with(
                    command='click Sign In',
                    target='Sign In',
                    app_name='TestApp'
                )
                
                # Verify debug logging occurred
                mock_logger.debug.assert_any_call(
                    "Starting enhanced element search: role='AXButton', label='Sign In', app='TestApp'"
                )
                mock_logger.debug.assert_any_call(
                    "Failure analysis completed: 2 potential matches found"
                )
                mock_logger.debug.assert_any_call(
                    "Best match: Sign In Button (score: 95.0)"
                )
                
                # Verify result includes debugging information
                assert result.found is False
                assert len(result.fuzzy_matches) > 0
                assert result.fuzzy_matches[0]['title'] == 'Sign In Button'
    
    @patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True)
    def test_comprehensive_logging_integration(self, mock_config):
        """Test comprehensive logging integration with debugging tools."""
        with patch.object(AccessibilityModule, '_initialize_permission_validator'), \
             patch.object(AccessibilityModule, '_initialize_debugging_tools'), \
             patch.object(AccessibilityModule, '_initialize_accessibility_api'):
            
            # Create module with debugging enabled
            accessibility_module = AccessibilityModule()
            accessibility_module.debug_mode_enabled = True
            accessibility_module.debug_logging = True
            accessibility_module.accessibility_debugger = self.mock_accessibility_debugger()
            
            # Mock performance timer context manager
            mock_perf_timer = MagicMock()
            mock_perf_timer.__enter__ = MagicMock(return_value=mock_perf_timer)
            mock_perf_timer.__exit__ = MagicMock(return_value=None)
            
            with patch.object(accessibility_module, '_performance_timer', return_value=mock_perf_timer), \
                 patch.object(accessibility_module, 'is_enhanced_role_detection_available', return_value=True), \
                 patch.object(accessibility_module, '_find_element_with_enhanced_roles_tracked', 
                            side_effect=Exception("Test error")), \
                 patch.object(accessibility_module, '_find_element_original_fallback', return_value=None), \
                 patch.object(accessibility_module, 'logger') as mock_logger:
                
                # Call find_element_enhanced to trigger error handling
                result = accessibility_module.find_element_enhanced(
                    role='AXButton',
                    label='Test Button',
                    app_name='TestApp'
                )
                
                # Verify comprehensive error logging occurred
                mock_logger.warning.assert_called()
                warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
                assert any("Enhanced element detection failed" in msg for msg in warning_calls)
                
                # Verify debugging analysis was performed for final failure
                accessibility_module.accessibility_debugger.analyze_element_detection_failure.assert_called()
    
    @patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True)
    def test_permission_change_callback_integration(self, mock_config):
        """Test integration with permission change callbacks."""
        with patch.object(AccessibilityModule, '_initialize_debugging_tools'), \
             patch.object(AccessibilityModule, '_initialize_accessibility_api'):
            
            # Create module
            accessibility_module = AccessibilityModule()
            accessibility_module.permission_validator = self.mock_permission_validator()
            accessibility_module.debug_mode_enabled = True
            accessibility_module.debug_logging = True
            accessibility_module.degraded_mode = True
            
            # Create mock permission statuses
            old_status = MockPermissionStatus(has_permissions=False, permission_level='NONE')
            new_status = MockPermissionStatus(has_permissions=True, permission_level='FULL')
            
            with patch.object(accessibility_module, 'logger') as mock_logger, \
                 patch.object(accessibility_module, '_initialize_accessibility_api') as mock_init_api:
                
                # Simulate permission change callback
                accessibility_module._on_permission_change(old_status, new_status)
                
                # Verify logging occurred
                mock_logger.info.assert_any_call(
                    "Accessibility permissions changed: NONE -> FULL"
                )
                mock_logger.info.assert_any_call(
                    "Permissions granted - attempting to exit degraded mode"
                )
                
                # Verify API re-initialization was attempted
                mock_init_api.assert_called_once()
    
    @patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True)
    def test_debugging_failure_graceful_degradation(self, mock_config):
        """Test graceful degradation when debugging tools fail to initialize."""
        with patch.object(AccessibilityModule, '_initialize_permission_validator'), \
             patch.object(AccessibilityModule, '_initialize_accessibility_api'), \
             patch('modules.accessibility.AccessibilityDebugger', side_effect=Exception("Debug init failed")):
            
            # Create module - should not fail even if debugging tools fail
            accessibility_module = AccessibilityModule()
            
            # Verify module still works without debugging tools
            assert accessibility_module.debug_mode_enabled is False
            assert accessibility_module.accessibility_debugger is None
            assert accessibility_module.diagnostic_tools is None
            assert accessibility_module.error_recovery_manager is None
    
    @patch('modules.accessibility.ACCESSIBILITY_AVAILABLE', True)
    def test_debugging_analysis_error_handling(self, mock_config):
        """Test error handling in debugging analysis."""
        with patch.object(AccessibilityModule, '_initialize_permission_validator'), \
             patch.object(AccessibilityModule, '_initialize_debugging_tools'), \
             patch.object(AccessibilityModule, '_initialize_accessibility_api'):
            
            # Create module with debugging enabled
            accessibility_module = AccessibilityModule()
            accessibility_module.debug_mode_enabled = True
            accessibility_module.debug_logging = True
            
            # Mock debugger that throws an error
            mock_debugger = MagicMock()
            mock_debugger.analyze_element_detection_failure.side_effect = Exception("Analysis failed")
            accessibility_module.accessibility_debugger = mock_debugger
            
            # Mock performance timer
            mock_perf_timer = MagicMock()
            mock_perf_timer.__enter__ = MagicMock(return_value=mock_perf_timer)
            mock_perf_timer.__exit__ = MagicMock(return_value=None)
            
            with patch.object(accessibility_module, '_performance_timer', return_value=mock_perf_timer), \
                 patch.object(accessibility_module, 'is_enhanced_role_detection_available', return_value=True), \
                 patch.object(accessibility_module, '_find_element_with_enhanced_roles_tracked', return_value=(None, {})), \
                 patch.object(accessibility_module, '_find_element_button_only_fallback', return_value=None), \
                 patch.object(accessibility_module, 'logger') as mock_logger:
                
                # Call find_element_enhanced - should not fail despite debugging error
                result = accessibility_module.find_element_enhanced(
                    role='AXButton',
                    label='Test Button',
                    app_name='TestApp'
                )
                
                # Verify the method completed successfully
                assert result.found is False
                
                # Verify error was logged
                mock_logger.debug.assert_any_call("Debugging analysis failed: Analysis failed")


if __name__ == '__main__':
    pytest.main([__file__])
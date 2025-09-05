"""
Unit tests for PermissionValidator module.

Tests comprehensive accessibility permission validation across different system states.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import time
from datetime import datetime
from typing import Dict, Any, List

# Import the module under test
from modules.permission_validator import (
    PermissionValidator,
    PermissionStatus,
    PermissionCheckResult,
    AccessibilityPermissionError,
    PermissionRequestError,
    SystemCompatibilityError
)


class TestPermissionStatus(unittest.TestCase):
    """Test PermissionStatus dataclass functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.timestamp = datetime.now()
        self.status = PermissionStatus(
            has_permissions=True,
            permission_level='FULL',
            missing_permissions=[],
            granted_permissions=['basic_accessibility_access', 'system_wide_element_access'],
            can_request_permissions=True,
            system_version='12.0',
            recommendations=[],
            timestamp=self.timestamp,
            check_duration_ms=150.5
        )
    
    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        result = self.status.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['has_permissions'], True)
        self.assertEqual(result['permission_level'], 'FULL')
        self.assertEqual(result['system_version'], '12.0')
        self.assertEqual(result['timestamp'], self.timestamp.isoformat())
        self.assertEqual(result['check_duration_ms'], 150.5)
    
    def test_is_sufficient_for_fast_path_full_permissions(self):
        """Test fast path sufficiency check with full permissions."""
        self.assertTrue(self.status.is_sufficient_for_fast_path())
    
    def test_is_sufficient_for_fast_path_partial_permissions(self):
        """Test fast path sufficiency check with partial permissions."""
        self.status.permission_level = 'PARTIAL'
        self.assertTrue(self.status.is_sufficient_for_fast_path())
    
    def test_is_sufficient_for_fast_path_no_permissions(self):
        """Test fast path sufficiency check with no permissions."""
        self.status.has_permissions = False
        self.status.permission_level = 'NONE'
        self.assertFalse(self.status.is_sufficient_for_fast_path())
    
    def test_get_summary_with_permissions(self):
        """Test summary generation with permissions."""
        summary = self.status.get_summary()
        self.assertIn("✅", summary)
        self.assertIn("granted", summary)
        self.assertIn("FULL", summary)
    
    def test_get_summary_without_permissions(self):
        """Test summary generation without permissions."""
        self.status.has_permissions = False
        self.status.missing_permissions = ['basic_access', 'system_access']
        summary = self.status.get_summary()
        self.assertIn("❌", summary)
        self.assertIn("required", summary)
        self.assertIn("2 issues", summary)


class TestPermissionCheckResult(unittest.TestCase):
    """Test PermissionCheckResult dataclass functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.result = PermissionCheckResult(
            check_name="test_check",
            success=True,
            error_message=None,
            check_duration_ms=50.0,
            metadata={'test_key': 'test_value'}
        )
    
    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        result_dict = self.result.to_dict()
        
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['check_name'], 'test_check')
        self.assertEqual(result_dict['success'], True)
        self.assertEqual(result_dict['error_message'], None)
        self.assertEqual(result_dict['check_duration_ms'], 50.0)
        self.assertEqual(result_dict['metadata'], {'test_key': 'test_value'})


class TestPermissionValidator(unittest.TestCase):
    """Test PermissionValidator class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'permission_check_timeout_ms': 5000,
            'auto_request_permissions': True,
            'monitor_permission_changes': True,
            'debug_logging': False
        }
        
        # Mock system information
        self.mock_system_info = {
            'platform': 'Darwin',
            'version': '12.0.0',
            'is_macos': True,
            'macos_version': '12.0',
            'apple_silicon': False
        }
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.platform')
    @patch('modules.permission_validator.psutil')
    def test_initialization_success(self, mock_psutil, mock_platform):
        """Test successful initialization."""
        # Mock platform information
        mock_platform.system.return_value = 'Darwin'
        mock_platform.version.return_value = '12.0.0'
        mock_platform.release.return_value = '21.0.0'
        mock_platform.machine.return_value = 'x86_64'
        mock_platform.python_version.return_value = '3.11.0'
        mock_platform.mac_ver.return_value = ('12.0', ('', '', ''), 'x86_64')
        
        # Mock psutil
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.virtual_memory.return_value.total = 16000000000
        mock_psutil.boot_time.return_value = time.time() - 3600
        
        validator = PermissionValidator(self.config)
        
        self.assertEqual(validator.config, self.config)
        self.assertEqual(validator.permission_check_timeout, 5000)
        self.assertTrue(validator.auto_request_permissions)
        self.assertTrue(validator.monitor_permission_changes)
        self.assertFalse(validator.debug_logging)
        self.assertIsInstance(validator.system_info, dict)
        self.assertTrue(validator.system_info['is_macos'])
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', False)
    def test_initialization_without_frameworks(self):
        """Test initialization without accessibility frameworks."""
        validator = PermissionValidator(self.config)
        
        self.assertFalse(validator.system_info.get('frameworks_available', True))
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.AXIsProcessTrusted')
    @patch('modules.permission_validator.AXUIElementCreateSystemWide')
    @patch('modules.permission_validator.AXUIElementCopyAttributeValue')
    @patch('modules.permission_validator.NSWorkspace')
    def test_check_accessibility_permissions_full_access(self, mock_workspace, mock_copy_attr, 
                                                        mock_create_system, mock_is_trusted):
        """Test permission check with full access."""
        # Mock successful accessibility API calls
        mock_is_trusted.return_value = True
        mock_create_system.return_value = Mock()
        mock_copy_attr.return_value = Mock()
        
        # Mock workspace
        mock_workspace_instance = Mock()
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        mock_workspace_instance.activeApplication.return_value = {
            'NSApplicationName': 'TestApp',
            'NSApplicationBundleIdentifier': 'com.test.app',
            'NSApplicationProcessIdentifier': 1234
        }
        
        validator = PermissionValidator(self.config)
        validator.system_info = self.mock_system_info
        
        status = validator.check_accessibility_permissions()
        
        self.assertIsInstance(status, PermissionStatus)
        self.assertTrue(status.has_permissions)
        self.assertEqual(status.permission_level, 'FULL')
        self.assertGreater(len(status.granted_permissions), 0)
        self.assertEqual(len(status.missing_permissions), 0)
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.AXIsProcessTrusted')
    def test_check_accessibility_permissions_no_access(self, mock_is_trusted):
        """Test permission check with no access."""
        # Mock failed accessibility API calls
        mock_is_trusted.return_value = False
        
        validator = PermissionValidator(self.config)
        validator.system_info = self.mock_system_info
        
        status = validator.check_accessibility_permissions()
        
        self.assertIsInstance(status, PermissionStatus)
        self.assertFalse(status.has_permissions)
        self.assertEqual(status.permission_level, 'NONE')
        self.assertGreater(len(status.missing_permissions), 0)
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', False)
    def test_check_framework_availability_missing(self):
        """Test framework availability check when frameworks are missing."""
        validator = PermissionValidator(self.config)
        
        result = validator._check_framework_availability()
        
        self.assertIsInstance(result, PermissionCheckResult)
        self.assertEqual(result.check_name, 'framework_availability')
        self.assertFalse(result.success)
        self.assertIn('not available', result.error_message)
        self.assertFalse(result.metadata['frameworks_available'])
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.AXIsProcessTrusted')
    @patch('modules.permission_validator.AXUIElementCreateSystemWide')
    def test_check_framework_availability_success(self, mock_create_system, mock_is_trusted):
        """Test framework availability check when frameworks are available."""
        # Mock successful framework calls
        mock_is_trusted.return_value = True
        mock_create_system.return_value = Mock()
        
        validator = PermissionValidator(self.config)
        
        result = validator._check_framework_availability()
        
        self.assertIsInstance(result, PermissionCheckResult)
        self.assertEqual(result.check_name, 'framework_availability')
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        self.assertTrue(result.metadata['AXIsProcessTrusted'])
        self.assertTrue(result.metadata['AXUIElementCreateSystemWide'])
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.AXIsProcessTrusted')
    def test_check_basic_accessibility_access_trusted(self, mock_is_trusted):
        """Test basic accessibility access check when process is trusted."""
        mock_is_trusted.return_value = True
        
        validator = PermissionValidator(self.config)
        
        result = validator._check_basic_accessibility_access()
        
        self.assertIsInstance(result, PermissionCheckResult)
        self.assertEqual(result.check_name, 'basic_accessibility_access')
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        self.assertTrue(result.metadata['is_trusted'])
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.AXIsProcessTrusted')
    def test_check_basic_accessibility_access_not_trusted(self, mock_is_trusted):
        """Test basic accessibility access check when process is not trusted."""
        mock_is_trusted.return_value = False
        
        validator = PermissionValidator(self.config)
        
        result = validator._check_basic_accessibility_access()
        
        self.assertIsInstance(result, PermissionCheckResult)
        self.assertEqual(result.check_name, 'basic_accessibility_access')
        self.assertFalse(result.success)
        self.assertIn('not trusted', result.error_message)
        self.assertFalse(result.metadata['is_trusted'])
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.AXUIElementCreateSystemWide')
    @patch('modules.permission_validator.AXUIElementCopyAttributeValue')
    def test_check_system_wide_element_access_success(self, mock_copy_attr, mock_create_system):
        """Test system-wide element access check with success."""
        # Mock successful system-wide element creation and attribute access
        mock_system_element = Mock()
        mock_create_system.return_value = mock_system_element
        mock_copy_attr.return_value = Mock()  # Non-None return indicates success
        
        validator = PermissionValidator(self.config)
        
        result = validator._check_system_wide_element_access()
        
        self.assertIsInstance(result, PermissionCheckResult)
        self.assertEqual(result.check_name, 'system_wide_element_access')
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        self.assertTrue(result.metadata['system_wide_element'])
        self.assertTrue(result.metadata['focused_app_access'])
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.AXUIElementCreateSystemWide')
    def test_check_system_wide_element_access_failure(self, mock_create_system):
        """Test system-wide element access check with failure."""
        # Mock failed system-wide element creation
        mock_create_system.return_value = None
        
        validator = PermissionValidator(self.config)
        
        result = validator._check_system_wide_element_access()
        
        self.assertIsInstance(result, PermissionCheckResult)
        self.assertEqual(result.check_name, 'system_wide_element_access')
        self.assertFalse(result.success)
        self.assertIn('Cannot create', result.error_message)
        self.assertIsNone(result.metadata['system_wide_element'])
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.NSWorkspace')
    @patch('modules.permission_validator.AXUIElementCreateSystemWide')
    @patch('modules.permission_validator.AXUIElementCopyAttributeValue')
    def test_check_focused_application_access_success(self, mock_copy_attr, mock_create_system, mock_workspace):
        """Test focused application access check with success."""
        # Mock workspace
        mock_workspace_instance = Mock()
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        mock_workspace_instance.activeApplication.return_value = {
            'NSApplicationName': 'TestApp',
            'NSApplicationBundleIdentifier': 'com.test.app',
            'NSApplicationProcessIdentifier': 1234
        }
        
        # Mock accessibility API
        mock_create_system.return_value = Mock()
        mock_copy_attr.return_value = Mock()
        
        validator = PermissionValidator(self.config)
        
        result = validator._check_focused_application_access()
        
        self.assertIsInstance(result, PermissionCheckResult)
        self.assertEqual(result.check_name, 'focused_application_access')
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        self.assertTrue(result.metadata['workspace_access'])
        self.assertTrue(result.metadata['accessibility_access'])
        self.assertEqual(result.metadata['active_app']['app_name'], 'TestApp')
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.AXIsProcessTrusted')
    @patch('modules.permission_validator.AXIsProcessTrustedWithOptions')
    @patch('modules.permission_validator.CFDictionaryCreateMutable')
    @patch('modules.permission_validator.CFStringCreateWithCString')
    @patch('modules.permission_validator.CFDictionarySetValue')
    def test_check_process_trust_status_trusted(self, mock_dict_set, mock_str_create, 
                                              mock_dict_create, mock_trusted_options, mock_is_trusted):
        """Test process trust status check when trusted."""
        mock_is_trusted.return_value = True
        mock_trusted_options.return_value = True
        mock_dict_create.return_value = Mock()
        mock_str_create.return_value = Mock()
        
        validator = PermissionValidator(self.config)
        
        result = validator._check_process_trust_status()
        
        self.assertIsInstance(result, PermissionCheckResult)
        self.assertEqual(result.check_name, 'process_trust_status')
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        self.assertTrue(result.metadata['is_trusted'])
        self.assertTrue(result.metadata['can_request_permissions'])
    
    def test_analyze_permission_results_full_permissions(self):
        """Test permission result analysis with full permissions."""
        checks = [
            PermissionCheckResult('framework_availability', True, None, 10.0, {}),
            PermissionCheckResult('basic_accessibility_access', True, None, 20.0, {}),
            PermissionCheckResult('system_wide_element_access', True, None, 30.0, {}),
            PermissionCheckResult('focused_application_access', True, None, 40.0, {}),
            PermissionCheckResult('process_trust_status', True, None, 50.0, {'can_request_permissions': True}),
        ]
        
        validator = PermissionValidator(self.config)
        validator.system_info = self.mock_system_info
        
        status = validator._analyze_permission_results(checks)
        
        self.assertTrue(status.has_permissions)
        self.assertEqual(status.permission_level, 'FULL')
        self.assertEqual(len(status.missing_permissions), 0)
        self.assertEqual(len(status.granted_permissions), 5)
        self.assertTrue(status.can_request_permissions)
    
    def test_analyze_permission_results_no_permissions(self):
        """Test permission result analysis with no permissions."""
        checks = [
            PermissionCheckResult('framework_availability', False, 'Error', 10.0, {}),
            PermissionCheckResult('basic_accessibility_access', False, 'Error', 20.0, {}),
            PermissionCheckResult('system_wide_element_access', False, 'Error', 30.0, {}),
            PermissionCheckResult('focused_application_access', False, 'Error', 40.0, {}),
            PermissionCheckResult('process_trust_status', False, 'Error', 50.0, {'can_request_permissions': False}),
        ]
        
        validator = PermissionValidator(self.config)
        validator.system_info = self.mock_system_info
        
        status = validator._analyze_permission_results(checks)
        
        self.assertFalse(status.has_permissions)
        self.assertEqual(status.permission_level, 'NONE')
        self.assertEqual(len(status.missing_permissions), 5)
        self.assertEqual(len(status.granted_permissions), 0)
        self.assertFalse(status.can_request_permissions)
    
    def test_analyze_permission_results_partial_permissions(self):
        """Test permission result analysis with partial permissions."""
        checks = [
            PermissionCheckResult('framework_availability', True, None, 10.0, {}),
            PermissionCheckResult('basic_accessibility_access', True, None, 20.0, {}),
            PermissionCheckResult('system_wide_element_access', True, None, 30.0, {}),
            PermissionCheckResult('focused_application_access', False, 'Error', 40.0, {}),
            PermissionCheckResult('process_trust_status', False, 'Error', 50.0, {'can_request_permissions': True}),
        ]
        
        validator = PermissionValidator(self.config)
        validator.system_info = self.mock_system_info
        
        status = validator._analyze_permission_results(checks)
        
        self.assertTrue(status.has_permissions)  # Critical checks passed
        self.assertEqual(status.permission_level, 'PARTIAL')
        self.assertEqual(len(status.missing_permissions), 2)
        self.assertEqual(len(status.granted_permissions), 3)
        self.assertTrue(status.can_request_permissions)
    
    def test_generate_recommendations_no_frameworks(self):
        """Test recommendation generation when frameworks are missing."""
        checks = [
            PermissionCheckResult('framework_availability', False, 'Not available', 10.0, {}),
        ]
        
        validator = PermissionValidator(self.config)
        
        recommendations = validator._generate_recommendations(checks, 'NONE')
        
        self.assertGreater(len(recommendations), 0)
        self.assertTrue(any('PyObjC' in rec for rec in recommendations))
        self.assertTrue(any('pip install' in rec for rec in recommendations))
    
    def test_generate_recommendations_no_basic_access(self):
        """Test recommendation generation when basic access is missing."""
        checks = [
            PermissionCheckResult('basic_accessibility_access', False, 'Not trusted', 10.0, {}),
        ]
        
        validator = PermissionValidator(self.config)
        
        recommendations = validator._generate_recommendations(checks, 'NONE')
        
        self.assertGreater(len(recommendations), 0)
        self.assertTrue(any('System Preferences' in rec for rec in recommendations))
        self.assertTrue(any('accessibility permissions' in rec for rec in recommendations))
    
    def test_guide_permission_setup_non_macos(self):
        """Test permission setup guide for non-macOS systems."""
        validator = PermissionValidator(self.config)
        validator.system_info = {'is_macos': False}
        
        instructions = validator.guide_permission_setup()
        
        self.assertGreater(len(instructions), 0)
        self.assertTrue(any('requires macOS' in inst for inst in instructions))
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    def test_guide_permission_setup_macos_no_permissions(self):
        """Test permission setup guide for macOS without permissions."""
        validator = PermissionValidator(self.config)
        validator.system_info = self.mock_system_info
        
        # Mock permission check to return no permissions
        with patch.object(validator, 'check_accessibility_permissions') as mock_check:
            mock_status = PermissionStatus(
                has_permissions=False,
                permission_level='NONE',
                missing_permissions=['basic_access'],
                granted_permissions=[],
                can_request_permissions=True,
                system_version='12.0',
                recommendations=[],
                timestamp=datetime.now(),
                check_duration_ms=100.0
            )
            mock_check.return_value = mock_status
            
            instructions = validator.guide_permission_setup()
        
        self.assertGreater(len(instructions), 0)
        self.assertTrue(any('System Preferences' in inst for inst in instructions))
        self.assertTrue(any('Accessibility' in inst for inst in instructions))
        self.assertTrue(any('SETUP GUIDE' in inst for inst in instructions))
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.AXIsProcessTrustedWithOptions')
    @patch('modules.permission_validator.CFDictionaryCreateMutable')
    @patch('modules.permission_validator.CFStringCreateWithCString')
    @patch('modules.permission_validator.CFDictionarySetValue')
    def test_attempt_permission_request_success(self, mock_dict_set, mock_str_create, 
                                              mock_dict_create, mock_trusted_options):
        """Test successful permission request."""
        mock_trusted_options.return_value = True
        mock_dict_create.return_value = Mock()
        mock_str_create.return_value = Mock()
        
        validator = PermissionValidator(self.config)
        
        result = validator.attempt_permission_request()
        
        self.assertTrue(result)
        mock_trusted_options.assert_called_once()
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.permission_validator.AXIsProcessTrustedWithOptions')
    @patch('modules.permission_validator.CFDictionaryCreateMutable')
    @patch('modules.permission_validator.CFStringCreateWithCString')
    @patch('modules.permission_validator.CFDictionarySetValue')
    def test_attempt_permission_request_denied(self, mock_dict_set, mock_str_create, 
                                             mock_dict_create, mock_trusted_options):
        """Test denied permission request."""
        mock_trusted_options.return_value = False
        mock_dict_create.return_value = Mock()
        mock_str_create.return_value = Mock()
        
        validator = PermissionValidator(self.config)
        
        result = validator.attempt_permission_request()
        
        self.assertFalse(result)
        mock_trusted_options.assert_called_once()
    
    @patch('modules.permission_validator.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', False)
    def test_attempt_permission_request_no_frameworks(self):
        """Test permission request without frameworks."""
        validator = PermissionValidator(self.config)
        
        with self.assertRaises(PermissionRequestError):
            validator.attempt_permission_request()
    
    def test_permission_cache_functionality(self):
        """Test permission caching functionality."""
        validator = PermissionValidator(self.config)
        
        # Initially no cache
        self.assertFalse(validator._is_permission_cache_valid())
        
        # Create and cache a status
        status = PermissionStatus(
            has_permissions=True,
            permission_level='FULL',
            missing_permissions=[],
            granted_permissions=['test'],
            can_request_permissions=True,
            system_version='12.0',
            recommendations=[],
            timestamp=datetime.now(),
            check_duration_ms=100.0
        )
        
        validator._cache_permission_status(status)
        
        # Cache should now be valid
        self.assertTrue(validator._is_permission_cache_valid())
        
        # Clear cache
        validator._clear_permission_cache()
        self.assertFalse(validator._is_permission_cache_valid())
    
    def test_permission_monitoring_lifecycle(self):
        """Test permission monitoring start/stop lifecycle."""
        validator = PermissionValidator(self.config)
        
        # Initially not monitoring
        self.assertFalse(validator.monitoring_active)
        
        # Start monitoring (call the method, not the property)
        validator.monitor_permission_changes()
        self.assertTrue(validator.monitoring_active)
        self.assertIsNotNone(validator.permission_monitor_thread)
        
        # Stop monitoring
        validator.stop_permission_monitoring()
        self.assertFalse(validator.monitoring_active)
    
    def test_permission_change_callbacks(self):
        """Test permission change callback functionality."""
        validator = PermissionValidator(self.config)
        
        # Create mock callback
        callback = Mock()
        
        # Add callback
        validator.add_permission_change_callback(callback)
        self.assertIn(callback, validator.permission_change_callbacks)
        
        # Remove callback
        validator.remove_permission_change_callback(callback)
        self.assertNotIn(callback, validator.permission_change_callbacks)
    
    def test_has_permission_status_changed(self):
        """Test permission status change detection."""
        validator = PermissionValidator(self.config)
        
        old_status = PermissionStatus(
            has_permissions=False,
            permission_level='NONE',
            missing_permissions=['test'],
            granted_permissions=[],
            can_request_permissions=False,
            system_version='12.0',
            recommendations=[],
            timestamp=datetime.now(),
            check_duration_ms=100.0
        )
        
        new_status = PermissionStatus(
            has_permissions=True,
            permission_level='FULL',
            missing_permissions=[],
            granted_permissions=['test'],
            can_request_permissions=True,
            system_version='12.0',
            recommendations=[],
            timestamp=datetime.now(),
            check_duration_ms=100.0
        )
        
        # Should detect change
        self.assertTrue(validator._has_permission_status_changed(old_status, new_status))
        
        # Should not detect change when same
        self.assertFalse(validator._has_permission_status_changed(new_status, new_status))
    
    def test_get_python_executable_info(self):
        """Test Python executable information gathering."""
        validator = PermissionValidator(self.config)
        
        info = validator._get_python_executable_info()
        
        # Should return info about current Python executable
        self.assertIsNotNone(info)
        self.assertIn('path', info)
        self.assertIn('version', info)
        self.assertIn('executable', info)


class TestExceptionClasses(unittest.TestCase):
    """Test custom exception classes."""
    
    def test_accessibility_permission_error(self):
        """Test AccessibilityPermissionError exception."""
        status = PermissionStatus(
            has_permissions=False,
            permission_level='NONE',
            missing_permissions=['test'],
            granted_permissions=[],
            can_request_permissions=False,
            system_version='12.0',
            recommendations=[],
            timestamp=datetime.now(),
            check_duration_ms=100.0
        )
        
        error = AccessibilityPermissionError("Test error", status)
        
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.permission_status, status)
    
    def test_permission_request_error(self):
        """Test PermissionRequestError exception."""
        error = PermissionRequestError("Request failed", "System error")
        
        self.assertEqual(str(error), "Request failed")
        self.assertEqual(error.system_error, "System error")
    
    def test_system_compatibility_error(self):
        """Test SystemCompatibilityError exception."""
        system_info = {'platform': 'Linux'}
        error = SystemCompatibilityError("Not compatible", system_info)
        
        self.assertEqual(str(error), "Not compatible")
        self.assertEqual(error.system_info, system_info)


if __name__ == '__main__':
    unittest.main()
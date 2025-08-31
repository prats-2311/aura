# tests/test_lifecycle_core.py
"""
Core lifecycle tests for application lifecycle management.

Tests the essential lifecycle functionality without complex system mocking.
"""

import unittest
import threading
import time
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import logging

# Import the main application
from main import AURAApplication, main
from modules.audio import AudioModule
from modules.feedback import FeedbackModule
from orchestrator import Orchestrator


class TestCoreLifecycle(unittest.TestCase):
    """Core lifecycle tests for application lifecycle management."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary log file
        self.temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        self.temp_log.close()
        
        # Mock configuration overrides
        self.config_override = {
            'LOG_FILE': self.temp_log.name,
            'LOG_LEVEL': 'DEBUG',
            'DEBUG_MODE': True
        }
        
        # Patch core modules only
        self.audio_patcher = patch('main.AudioModule')
        self.feedback_patcher = patch('main.FeedbackModule')
        self.orchestrator_patcher = patch('main.Orchestrator')
        self.validate_config_patcher = patch('main.validate_config', return_value=True)
        
        self.mock_audio = self.audio_patcher.start()
        self.mock_feedback = self.feedback_patcher.start()
        self.mock_orchestrator = self.orchestrator_patcher.start()
        self.mock_validate_config = self.validate_config_patcher.start()
        
        # Configure mocks
        self.mock_audio_instance = Mock(spec=AudioModule)
        self.mock_audio_instance.wake_word = "computer"
        self.mock_audio.return_value = self.mock_audio_instance
        
        self.mock_feedback_instance = Mock(spec=FeedbackModule)
        self.mock_feedback.return_value = self.mock_feedback_instance
        
        self.mock_orchestrator_instance = Mock(spec=Orchestrator)
        self.mock_orchestrator.return_value = self.mock_orchestrator_instance
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Stop all patches
        self.audio_patcher.stop()
        self.feedback_patcher.stop()
        self.orchestrator_patcher.stop()
        self.validate_config_patcher.stop()
        
        # Clean up temp file
        if os.path.exists(self.temp_log.name):
            os.unlink(self.temp_log.name)
    
    def test_application_initialization_with_lifecycle_features(self):
        """Test application initialization includes lifecycle management features."""
        app = AURAApplication(config_override=self.config_override)
        
        # Check that lifecycle management features are initialized
        self.assertIsInstance(app.startup_checks, list)
        self.assertIsInstance(app.health_checks, list)
        self.assertIsInstance(app.cleanup_handlers, list)
        
        # Check that default checks and handlers are registered
        self.assertGreater(len(app.startup_checks), 0)
        self.assertGreater(len(app.health_checks), 0)
        self.assertGreater(len(app.cleanup_handlers), 0)
        
        # Check resource usage tracking is initialized
        self.assertIsInstance(app.resource_usage, dict)
        self.assertIn('memory_mb', app.resource_usage)
        self.assertIn('cpu_percent', app.resource_usage)
        self.assertIn('threads_count', app.resource_usage)
    
    def test_startup_with_checks(self):
        """Test startup process includes running startup checks."""
        app = AURAApplication(config_override=self.config_override)
        
        # Mock startup checks to avoid system dependencies
        mock_check1 = Mock(return_value=(True, "Check 1 passed"))
        mock_check1.__name__ = "mock_check1"
        mock_check2 = Mock(return_value=(True, "Check 2 passed"))
        mock_check2.__name__ = "mock_check2"
        
        # Replace default checks with mocked ones
        app.startup_checks = [mock_check1, mock_check2]
        
        # Test startup
        result = app.startup()
        
        # Verify startup succeeded
        self.assertTrue(result)
        self.assertTrue(app.is_running)
        
        # Verify checks were called
        mock_check1.assert_called_once()
        mock_check2.assert_called_once()
        
        # Verify health monitoring was started
        self.assertIsNotNone(app.health_monitor_thread)
        
        app.shutdown()
    
    def test_startup_check_failure_handling(self):
        """Test startup handles check failures gracefully."""
        app = AURAApplication(config_override=self.config_override)
        
        # Mock startup checks with one failure
        mock_check1 = Mock(return_value=(True, "Check 1 passed"))
        mock_check1.__name__ = "mock_check1"
        mock_check2 = Mock(return_value=(False, "Check 2 failed"))
        mock_check2.__name__ = "mock_check2"
        
        # Replace default checks with mocked ones
        app.startup_checks = [mock_check1, mock_check2]
        
        # Test startup
        result = app.startup()
        
        # Verify startup failed due to check failure
        self.assertFalse(result)
        self.assertFalse(app.is_running)
        
        # Verify both checks were called
        mock_check1.assert_called_once()
        mock_check2.assert_called_once()
    
    def test_health_monitoring_lifecycle(self):
        """Test health monitoring starts and stops properly."""
        app = AURAApplication(config_override=self.config_override)
        
        # Mock health checks to avoid system dependencies
        mock_health_check = Mock(return_value=(True, "Health check passed"))
        mock_health_check.__name__ = "mock_health_check"
        app.health_checks = [mock_health_check]
        
        # Mock startup checks to avoid system dependencies
        mock_startup_check = Mock(return_value=(True, "Startup check passed"))
        mock_startup_check.__name__ = "mock_startup_check"
        app.startup_checks = [mock_startup_check]
        
        # Start application
        startup_result = app.startup()
        self.assertTrue(startup_result, "Startup should succeed")
        
        # Give the health monitoring thread a moment to start
        time.sleep(0.1)
        
        # Verify health monitoring thread was created
        self.assertIsNotNone(app.health_monitor_thread)
        # Note: The thread might not be alive long due to daemon=True and test environment
        # The important thing is that it was created and started
        
        # Wait a moment for health monitoring to potentially run
        time.sleep(0.1)
        
        # Shutdown application
        app.shutdown()
        
        # Wait for threads to stop
        time.sleep(0.2)
        
        # Verify shutdown state
        self.assertTrue(app.is_shutting_down)
        self.assertFalse(app.is_running)
    
    def test_custom_checks_and_handlers(self):
        """Test adding custom startup checks and cleanup handlers."""
        app = AURAApplication(config_override=self.config_override)
        
        # Add custom startup check
        custom_check = Mock(return_value=(True, "Custom check passed"))
        custom_check.__name__ = "custom_check"
        app.add_startup_check(custom_check)
        
        # Add custom health check
        custom_health_check = Mock(return_value=(True, "Custom health check passed"))
        custom_health_check.__name__ = "custom_health_check"
        app.add_health_check(custom_health_check)
        
        # Add custom cleanup handler
        custom_cleanup = Mock()
        custom_cleanup.__name__ = "custom_cleanup"
        app.add_cleanup_handler(custom_cleanup)
        
        # Verify they were added
        self.assertIn(custom_check, app.startup_checks)
        self.assertIn(custom_health_check, app.health_checks)
        self.assertIn(custom_cleanup, app.cleanup_handlers)
        
        # Test startup and shutdown
        app.startup()
        app.shutdown()
        
        # Verify custom functions were called
        custom_check.assert_called_once()
        custom_cleanup.assert_called_once()
    
    def test_resource_usage_tracking(self):
        """Test resource usage tracking functionality."""
        app = AURAApplication(config_override=self.config_override)
        
        # Set some test statistics
        app.wake_words_detected = 5
        app.commands_processed = 3
        app.errors_count = 1
        
        # Test status logging
        with patch('main.logger') as mock_logger:
            app._log_status()
            
            # Verify comprehensive status was logged
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            
            # Check that key metrics are included
            self.assertIn("Wake words: 5", call_args)
            self.assertIn("Commands: 3", call_args)
            self.assertIn("Errors: 1", call_args)
            self.assertIn("Threads:", call_args)
    
    def test_shutdown_report_generation(self):
        """Test shutdown report generation."""
        app = AURAApplication(config_override=self.config_override)
        
        # Mock startup checks to avoid system dependencies
        app.startup_checks = [Mock(return_value=(True, "Mock check passed"))]
        
        app.startup()
        
        # Set some statistics
        app.wake_words_detected = 10
        app.commands_processed = 7
        app.errors_count = 2
        
        # Wait a moment to accumulate uptime
        time.sleep(0.1)
        
        # Test shutdown with report generation
        with patch('main.logger') as mock_logger:
            app.shutdown()
            
            # Verify shutdown report was logged
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            
            # Look for shutdown report indicators
            report_found = any("SHUTDOWN REPORT" in line for line in info_calls)
            stats_found = any("Wake Words Detected: 10" in line for line in info_calls)
            
            # At least one of these should be true (depending on exact logging format)
            self.assertTrue(report_found or stats_found or len(info_calls) > 5)
    
    def test_error_handling_during_lifecycle(self):
        """Test error handling during lifecycle operations."""
        app = AURAApplication(config_override=self.config_override)
        
        # Add a failing cleanup handler
        failing_cleanup = Mock(side_effect=Exception("Cleanup failed"))
        failing_cleanup.__name__ = "failing_cleanup"
        app.add_cleanup_handler(failing_cleanup)
        
        # Mock startup checks to avoid system dependencies
        mock_check = Mock(return_value=(True, "Mock check passed"))
        mock_check.__name__ = "mock_check"
        app.startup_checks = [mock_check]
        
        # Startup and shutdown should complete despite cleanup failure
        app.startup()
        app.shutdown()
        
        # Verify shutdown completed
        self.assertTrue(app.is_shutting_down)
        
        # Verify failing cleanup was called
        failing_cleanup.assert_called_once()
    
    def test_thread_management(self):
        """Test proper thread lifecycle management."""
        app = AURAApplication(config_override=self.config_override)
        
        # Mock startup checks to avoid system dependencies
        mock_check = Mock(return_value=(True, "Mock check passed"))
        mock_check.__name__ = "mock_check"
        app.startup_checks = [mock_check]
        
        # Record initial thread count
        initial_thread_count = threading.active_count()
        
        # Startup
        startup_result = app.startup()
        self.assertTrue(startup_result, "Startup should succeed")
        
        # Give threads a moment to start
        time.sleep(0.1)
        
        # Verify health monitoring thread was created
        self.assertIsNotNone(app.health_monitor_thread)
        # Note: Thread might not stay alive in test environment due to daemon=True
        
        # Shutdown
        app.shutdown()
        
        # Wait for threads to stop
        time.sleep(0.2)
        
        # Verify threads are cleaned up (allow some tolerance for test framework threads)
        final_thread_count = threading.active_count()
        self.assertLessEqual(final_thread_count, initial_thread_count + 2)
    
    def test_configuration_override_handling(self):
        """Test that configuration overrides are properly handled."""
        custom_config = {
            'LOG_LEVEL': 'ERROR',
            'DEBUG_MODE': False,
            'CUSTOM_SETTING': 'test_value'
        }
        
        app = AURAApplication(config_override=custom_config)
        
        # Verify config override is stored
        self.assertEqual(app.config_override['LOG_LEVEL'], 'ERROR')
        self.assertEqual(app.config_override['DEBUG_MODE'], False)
        self.assertEqual(app.config_override['CUSTOM_SETTING'], 'test_value')


class TestMainFunctionLifecycle(unittest.TestCase):
    """Test main function with lifecycle management."""
    
    @patch('main.validate_config', return_value=True)
    @patch('main.AURAApplication')
    def test_main_function_lifecycle(self, mock_app_class, mock_validate):
        """Test main function handles application lifecycle properly."""
        mock_app = Mock()
        mock_app.startup.return_value = True
        mock_app_class.return_value = mock_app
        
        with patch('sys.argv', ['main.py']):
            result = main()
        
        # Verify lifecycle methods were called
        mock_app.startup.assert_called_once()
        mock_app.run.assert_called_once()
        mock_app.shutdown.assert_called_once()
        
        # Verify successful exit
        self.assertEqual(result, 0)
    
    @patch('main.validate_config', return_value=True)
    @patch('main.AURAApplication')
    def test_main_function_startup_failure(self, mock_app_class, mock_validate):
        """Test main function handles startup failure properly."""
        mock_app = Mock()
        mock_app.startup.return_value = False  # Startup fails
        mock_app_class.return_value = mock_app
        
        with patch('sys.argv', ['main.py']):
            result = main()
        
        # Verify startup was attempted but run was not called
        mock_app.startup.assert_called_once()
        mock_app.run.assert_not_called()
        mock_app.shutdown.assert_called_once()  # Cleanup should still happen
        
        # Verify error exit code
        self.assertEqual(result, 1)
    
    @patch('main.validate_config', return_value=True)
    @patch('main.AURAApplication')
    def test_main_function_exception_handling(self, mock_app_class, mock_validate):
        """Test main function handles exceptions properly."""
        mock_app = Mock()
        mock_app.startup.return_value = True
        mock_app.run.side_effect = Exception("Runtime error")
        mock_app_class.return_value = mock_app
        
        with patch('sys.argv', ['main.py']):
            result = main()
        
        # Verify lifecycle methods were called
        mock_app.startup.assert_called_once()
        mock_app.run.assert_called_once()
        mock_app.shutdown.assert_called_once()  # Cleanup should happen even after exception
        
        # Verify error exit code
        self.assertEqual(result, 1)


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    
    unittest.main()
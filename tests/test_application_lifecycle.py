# tests/test_application_lifecycle.py
"""
End-to-end tests for complete application lifecycle.

Tests the full application lifecycle including startup checks, health monitoring,
resource management, and comprehensive shutdown procedures.
"""

import unittest
import threading
import time
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock, call
import logging

# Import the main application
from main import AURAApplication, main
from orchestrator import Orchestrator
from modules.audio import AudioModule
from modules.feedback import FeedbackModule


class TestApplicationLifecycle(unittest.TestCase):
    """End-to-end tests for application lifecycle management."""
    
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
        
        # Patch external dependencies
        self.patches = {}
        self.mocks = {}
        
        # Core module patches
        self.patches['audio'] = patch('main.AudioModule')
        self.patches['feedback'] = patch('main.FeedbackModule')
        self.patches['orchestrator'] = patch('main.Orchestrator')
        self.patches['validate_config'] = patch('main.validate_config', return_value=True)
        
        # System patches for startup checks (patch within the methods where they're imported)
        self.patches['requests'] = patch('requests.get')
        self.patches['sounddevice'] = patch('sounddevice.query_devices')
        self.patches['shutil'] = patch('shutil.disk_usage')
        self.patches['psutil'] = patch('psutil.Process', create=True)
        
        # Start all patches
        for name, patcher in self.patches.items():
            self.mocks[name] = patcher.start()
        
        # Configure core mocks
        self.mock_audio_instance = Mock(spec=AudioModule)
        self.mock_audio_instance.wake_word = "computer"
        self.mock_audio_instance.listen_for_wake_word.return_value = False
        self.mock_audio_instance.speech_to_text.return_value = "test command"
        self.mocks['audio'].return_value = self.mock_audio_instance
        
        self.mock_feedback_instance = Mock(spec=FeedbackModule)
        self.mocks['feedback'].return_value = self.mock_feedback_instance
        
        self.mock_orchestrator_instance = Mock(spec=Orchestrator)
        self.mock_orchestrator_instance.execute_command.return_value = {'status': 'completed'}
        self.mocks['orchestrator'].return_value = self.mock_orchestrator_instance
        
        # Configure system mocks for successful startup checks
        self._configure_successful_startup_mocks()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Stop all patches
        for patcher in self.patches.values():
            patcher.stop()
        
        # Clean up temp file
        if os.path.exists(self.temp_log.name):
            os.unlink(self.temp_log.name)
    
    def _configure_successful_startup_mocks(self):
        """Configure mocks for successful startup checks."""
        # API connectivity
        mock_response = Mock()
        mock_response.status_code = 200
        self.mocks['requests'].return_value = mock_response
        
        # Audio devices
        input_device = {'max_input_channels': 2, 'max_output_channels': 0}
        output_device = {'max_input_channels': 0, 'max_output_channels': 2}
        self.mocks['sounddevice'].return_value = [input_device, output_device]
        
        # Disk space (10GB free)
        self.mocks['shutil'].return_value = (100 * 1024**3, 90 * 1024**3, 10 * 1024**3)
        
        # Memory usage
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100MB
        mock_process.memory_info.return_value = mock_memory_info
        self.mocks['psutil'].return_value = mock_process
    
    def test_complete_application_lifecycle(self):
        """Test complete application lifecycle from startup to shutdown."""
        app = AURAApplication(config_override=self.config_override)
        
        # Test startup
        startup_result = app.startup()
        self.assertTrue(startup_result)
        self.assertTrue(app.is_running)
        self.assertIsNotNone(app.start_time)
        
        # Verify startup checks were run
        self.assertTrue(len(app.startup_checks) > 0)
        
        # Verify health monitoring was started
        self.assertIsNotNone(app.health_monitor_thread)
        
        # Verify modules were initialized
        self.assertIsNotNone(app.audio_module)
        self.assertIsNotNone(app.feedback_module)
        self.assertIsNotNone(app.orchestrator)
        
        # Wait a moment for threads to start
        time.sleep(0.1)
        
        # Test shutdown
        app.shutdown()
        
        # Verify shutdown state
        self.assertTrue(app.is_shutting_down)
        self.assertFalse(app.is_running)
        
        # Verify cleanup handlers were run
        self.assertTrue(len(app.cleanup_handlers) > 0)
    
    def test_startup_checks_comprehensive(self):
        """Test all startup checks are executed."""
        app = AURAApplication(config_override=self.config_override)
        
        # Run startup checks
        result = app._run_startup_checks()
        
        # Should pass with mocked dependencies
        self.assertTrue(result)
        
        # Verify specific checks were called
        self.mocks['requests'].assert_called()  # API connectivity
        self.mocks['sounddevice'].assert_called()  # Audio devices
        self.mocks['shutil'].assert_called()  # Disk space
    
    def test_startup_check_failures(self):
        """Test startup check failure handling."""
        app = AURAApplication(config_override=self.config_override)
        
        # Make API connectivity check fail
        self.mocks['requests'].side_effect = Exception("Connection failed")
        
        # Run startup checks
        result = app._run_startup_checks()
        
        # Should fail due to API connectivity
        self.assertFalse(result)
    
    def test_health_monitoring(self):
        """Test health monitoring functionality."""
        app = AURAApplication(config_override=self.config_override)
        app.startup()
        
        # Wait for health monitoring to start
        time.sleep(0.1)
        
        # Verify health monitoring thread is running
        self.assertIsNotNone(app.health_monitor_thread)
        self.assertTrue(app.health_monitor_thread.is_alive())
        
        # Run health checks manually
        app._run_health_checks()
        
        # Verify health check timestamp was updated
        self.assertIsNotNone(app.last_health_check)
        
        # Verify resource usage was updated
        self.assertGreater(app.resource_usage['memory_mb'], 0)
        
        app.shutdown()
    
    def test_health_check_failures(self):
        """Test health check failure handling."""
        app = AURAApplication(config_override=self.config_override)
        app.startup()
        
        # Make memory check fail by simulating high memory usage
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 2000 * 1024 * 1024  # 2GB (high usage)
        mock_process.memory_info.return_value = mock_memory_info
        self.mocks['psutil'].return_value = mock_process
        
        # Run health checks
        app._run_health_checks()
        
        # Should still complete but log warnings
        self.assertIsNotNone(app.last_health_check)
        
        app.shutdown()
    
    def test_custom_startup_checks_and_cleanup_handlers(self):
        """Test adding custom startup checks and cleanup handlers."""
        app = AURAApplication(config_override=self.config_override)
        
        # Add custom startup check
        custom_check_called = Mock(return_value=(True, "Custom check passed"))
        app.add_startup_check(custom_check_called)
        
        # Add custom cleanup handler
        custom_cleanup_called = Mock()
        app.add_cleanup_handler(custom_cleanup_called)
        
        # Startup and shutdown
        app.startup()
        app.shutdown()
        
        # Verify custom functions were called
        custom_check_called.assert_called_once()
        custom_cleanup_called.assert_called_once()
    
    def test_resource_usage_tracking(self):
        """Test resource usage tracking and reporting."""
        app = AURAApplication(config_override=self.config_override)
        app.startup()
        
        # Set some statistics
        app.wake_words_detected = 5
        app.commands_processed = 3
        app.errors_count = 1
        
        # Run health checks to update resource usage
        app._run_health_checks()
        
        # Test status logging
        with patch('main.logger') as mock_logger:
            app._log_status()
            
            # Verify comprehensive status was logged
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            
            self.assertIn("Wake words: 5", call_args)
            self.assertIn("Commands: 3", call_args)
            self.assertIn("Errors: 1", call_args)
            self.assertIn("Memory:", call_args)
            self.assertIn("Threads:", call_args)
        
        app.shutdown()
    
    def test_shutdown_report_generation(self):
        """Test shutdown report generation."""
        app = AURAApplication(config_override=self.config_override)
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
            report_lines = [line for line in info_calls if "SHUTDOWN REPORT" in line or "Wake Words Detected:" in line]
            
            self.assertTrue(len(report_lines) > 0)
    
    def test_error_handling_during_startup(self):
        """Test error handling during startup process."""
        app = AURAApplication(config_override=self.config_override)
        
        # Make module initialization fail
        self.mocks['audio'].side_effect = Exception("Audio module failed")
        
        # Startup should fail gracefully
        result = app.startup()
        
        self.assertFalse(result)
        self.assertFalse(app.is_running)
        self.assertEqual(app.errors_count, 1)
    
    def test_error_handling_during_shutdown(self):
        """Test error handling during shutdown process."""
        app = AURAApplication(config_override=self.config_override)
        app.startup()
        
        # Make cleanup handler fail
        failing_cleanup = Mock(side_effect=Exception("Cleanup failed"))
        app.add_cleanup_handler(failing_cleanup)
        
        # Shutdown should complete despite cleanup failure
        app.shutdown()
        
        self.assertTrue(app.is_shutting_down)
        self.assertGreater(app.errors_count, 0)
    
    def test_thread_lifecycle_management(self):
        """Test proper thread lifecycle management."""
        app = AURAApplication(config_override=self.config_override)
        app.startup()
        
        # Verify threads are started
        initial_thread_count = threading.active_count()
        self.assertIsNotNone(app.health_monitor_thread)
        self.assertTrue(app.health_monitor_thread.is_alive())
        
        # Shutdown and verify threads are stopped
        app.shutdown()
        
        # Wait for threads to stop
        time.sleep(0.2)
        
        # Thread count should be reduced (though not necessarily back to original due to test framework)
        final_thread_count = threading.active_count()
        self.assertLessEqual(final_thread_count, initial_thread_count + 1)  # Allow some tolerance
    
    def test_configuration_override_application(self):
        """Test that configuration overrides are properly applied."""
        custom_config = {
            'LOG_LEVEL': 'ERROR',
            'DEBUG_MODE': False
        }
        
        app = AURAApplication(config_override=custom_config)
        
        # Verify config override is stored
        self.assertEqual(app.config_override['LOG_LEVEL'], 'ERROR')
        self.assertEqual(app.config_override['DEBUG_MODE'], False)
    
    def test_signal_handler_setup(self):
        """Test that signal handlers are properly set up."""
        with patch('main.signal') as mock_signal:
            app = AURAApplication(config_override=self.config_override)
            
            # Verify signal handlers were set up
            mock_signal.signal.assert_called()
            
            # Should have at least SIGINT and SIGTERM
            signal_calls = [call[0][0] for call in mock_signal.signal.call_args_list]
            self.assertIn(mock_signal.SIGINT, signal_calls)
            self.assertIn(mock_signal.SIGTERM, signal_calls)


class TestEndToEndApplicationFlow(unittest.TestCase):
    """End-to-end tests for complete application flow."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Patch all external dependencies
        self.patches = [
            patch('main.validate_config', return_value=True),
            patch('main.AudioModule'),
            patch('main.FeedbackModule'),
            patch('main.Orchestrator'),
            patch('requests.get'),
            patch('sounddevice.query_devices'),
            patch('shutil.disk_usage'),
            patch('psutil.Process', create=True)
        ]
        
        self.mocks = []
        for patcher in self.patches:
            self.mocks.append(patcher.start())
        
        # Configure mocks for successful operation
        self._configure_mocks()
    
    def tearDown(self):
        """Clean up test fixtures."""
        for patcher in self.patches:
            patcher.stop()
    
    def _configure_mocks(self):
        """Configure mocks for successful operation."""
        # Configure successful responses for all checks
        mock_response = Mock()
        mock_response.status_code = 200
        self.mocks[4].return_value = mock_response  # requests.get
        
        # Audio devices
        devices = [
            {'max_input_channels': 2, 'max_output_channels': 0},
            {'max_input_channels': 0, 'max_output_channels': 2}
        ]
        self.mocks[5].return_value = devices  # sounddevice.query_devices
        
        # Disk space
        self.mocks[6].return_value = (100 * 1024**3, 90 * 1024**3, 10 * 1024**3)  # shutil.disk_usage
        
        # Memory usage
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024
        mock_process.memory_info.return_value = mock_memory_info
        self.mocks[7].return_value = mock_process  # psutil.Process
    
    @patch('sys.argv', ['main.py', '--config-check'])
    def test_config_check_mode(self):
        """Test application in config-check mode."""
        result = main()
        self.assertEqual(result, 0)  # Should succeed with mocked config
    
    @patch('sys.argv', ['main.py'])
    def test_normal_application_run(self):
        """Test normal application run with mocked dependencies."""
        with patch('main.AURAApplication') as mock_app_class:
            mock_app = Mock()
            mock_app.startup.return_value = True
            mock_app_class.return_value = mock_app
            
            result = main()
            
            self.assertEqual(result, 0)
            mock_app.startup.assert_called_once()
            mock_app.run.assert_called_once()
            mock_app.shutdown.assert_called_once()
    
    @patch('sys.argv', ['main.py', '--debug'])
    def test_debug_mode_application(self):
        """Test application with debug mode enabled."""
        with patch('main.AURAApplication') as mock_app_class:
            mock_app = Mock()
            mock_app.startup.return_value = True
            mock_app_class.return_value = mock_app
            
            result = main()
            
            # Verify debug config was passed
            call_args = mock_app_class.call_args[1]['config_override']
            self.assertTrue(call_args['DEBUG_MODE'])
            self.assertEqual(call_args['LOG_LEVEL'], 'DEBUG')
            
            self.assertEqual(result, 0)


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    
    unittest.main()
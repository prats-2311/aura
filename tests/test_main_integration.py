# tests/test_main_integration.py
"""
Integration tests for main application flow.

Tests the complete application lifecycle including startup, wake word monitoring,
command processing, and shutdown procedures.
"""

import unittest
import threading
import time
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import logging

# Import the main application
from main import AURAApplication, parse_arguments, main
from orchestrator import Orchestrator
from modules.audio import AudioModule
from modules.feedback import FeedbackModule


class TestMainApplicationIntegration(unittest.TestCase):
    """Integration tests for main application functionality."""
    
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
        
        # Disable actual audio/hardware interactions
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
        self.mock_audio_instance.listen_for_wake_word.return_value = False  # Default to no wake word
        self.mock_audio_instance.speech_to_text.return_value = "test command"
        self.mock_audio.return_value = self.mock_audio_instance
        
        self.mock_feedback_instance = Mock(spec=FeedbackModule)
        self.mock_feedback.return_value = self.mock_feedback_instance
        
        self.mock_orchestrator_instance = Mock(spec=Orchestrator)
        self.mock_orchestrator_instance.execute_command.return_value = {'status': 'completed'}
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
    
    def test_application_initialization(self):
        """Test application initialization."""
        app = AURAApplication(config_override=self.config_override)
        
        # Check initial state
        self.assertFalse(app.is_running)
        self.assertFalse(app.is_shutting_down)
        self.assertIsNone(app.orchestrator)
        self.assertIsNone(app.audio_module)
        self.assertIsNone(app.feedback_module)
        self.assertEqual(app.commands_processed, 0)
        self.assertEqual(app.wake_words_detected, 0)
    
    def test_successful_startup(self):
        """Test successful application startup."""
        app = AURAApplication(config_override=self.config_override)
        
        # Test startup
        result = app.startup()
        
        # Verify startup success
        self.assertTrue(result)
        self.assertTrue(app.is_running)
        self.assertIsNotNone(app.start_time)
        
        # Verify modules were initialized
        self.mock_audio.assert_called_once()
        self.mock_feedback.assert_called_once_with(audio_module=self.mock_audio_instance)
        self.mock_orchestrator.assert_called_once()
        
        # Verify feedback was provided
        self.mock_feedback_instance.speak.assert_called_once()
        
        # Cleanup
        app.shutdown()
    
    def test_startup_failure_invalid_config(self):
        """Test startup failure due to invalid configuration."""
        with patch('main.validate_config', return_value=False):
            app = AURAApplication(config_override=self.config_override)
            
            result = app.startup()
            
            self.assertFalse(result)
            self.assertFalse(app.is_running)
    
    def test_startup_failure_module_initialization(self):
        """Test startup failure due to module initialization error."""
        # Make audio module initialization fail
        self.mock_audio.side_effect = Exception("Audio initialization failed")
        
        app = AURAApplication(config_override=self.config_override)
        
        result = app.startup()
        
        self.assertFalse(result)
        self.assertFalse(app.is_running)
    
    def test_wake_word_detection_and_command_processing(self):
        """Test wake word detection and command processing flow."""
        app = AURAApplication(config_override=self.config_override)
        app.startup()
        
        # Configure mock to detect wake word once
        wake_word_calls = [True, False]  # Detect once, then stop
        self.mock_audio_instance.listen_for_wake_word.side_effect = wake_word_calls
        
        # Start wake word monitoring in a thread
        monitoring_thread = threading.Thread(
            target=app._wake_word_monitoring_loop,
            daemon=True
        )
        monitoring_thread.start()
        
        # Wait for processing
        time.sleep(0.1)
        
        # Stop monitoring
        app.is_running = False
        monitoring_thread.join(timeout=1.0)
        
        # Verify wake word was detected and command was processed
        self.assertEqual(app.wake_words_detected, 1)
        self.assertEqual(app.commands_processed, 1)
        
        # Verify orchestrator was called
        self.mock_orchestrator_instance.execute_command.assert_called_once_with("test command")
        
        app.shutdown()
    
    def test_command_processing_with_empty_command(self):
        """Test command processing with empty voice input."""
        app = AURAApplication(config_override=self.config_override)
        app.startup()
        
        # Configure mock to return empty command
        self.mock_audio_instance.speech_to_text.return_value = ""
        
        # Process command
        app._process_voice_command()
        
        # Verify no command was executed
        self.mock_orchestrator_instance.execute_command.assert_not_called()
        
        # Verify feedback was provided
        self.mock_feedback_instance.speak.assert_called()
        
        app.shutdown()
    
    def test_command_processing_with_orchestrator_error(self):
        """Test command processing when orchestrator raises an error."""
        app = AURAApplication(config_override=self.config_override)
        app.startup()
        
        # Configure orchestrator to raise an error
        self.mock_orchestrator_instance.execute_command.side_effect = Exception("Orchestrator error")
        
        # Process command
        app._process_voice_command()
        
        # Verify error feedback was provided
        self.mock_feedback_instance.speak.assert_called()
        
        app.shutdown()
    
    def test_graceful_shutdown(self):
        """Test graceful application shutdown."""
        app = AURAApplication(config_override=self.config_override)
        app.startup()
        
        # Start a mock wake word thread
        app.wake_word_thread = Mock()
        app.wake_word_thread.is_alive.return_value = True
        
        # Configure orchestrator with thread pool
        app.orchestrator.thread_pool = Mock()
        
        # Perform shutdown
        app.shutdown()
        
        # Verify shutdown state
        self.assertTrue(app.is_shutting_down)
        self.assertFalse(app.is_running)
        
        # Verify thread cleanup
        app.wake_word_thread.join.assert_called_once_with(timeout=5.0)
        
        # Verify orchestrator cleanup
        app.orchestrator.thread_pool.shutdown.assert_called_once_with(wait=True)
    
    def test_double_shutdown_protection(self):
        """Test that multiple shutdown calls are handled gracefully."""
        app = AURAApplication(config_override=self.config_override)
        app.startup()
        
        # First shutdown
        app.shutdown()
        self.assertTrue(app.is_shutting_down)
        
        # Second shutdown should be ignored
        with patch.object(app, '_log_status') as mock_log:
            app.shutdown()
            # Should not perform shutdown operations again
            mock_log.assert_not_called()
    
    def test_status_logging(self):
        """Test periodic status logging."""
        app = AURAApplication(config_override=self.config_override)
        app.startup()
        
        # Set some statistics
        app.wake_words_detected = 5
        app.commands_processed = 3
        
        # Test status logging
        with patch('main.logger') as mock_logger:
            app._log_status()
            mock_logger.info.assert_called_once()
            
            # Verify status information is included
            call_args = mock_logger.info.call_args[0][0]
            self.assertIn("Wake words: 5", call_args)
            self.assertIn("Commands: 3", call_args)
        
        app.shutdown()


class TestCommandLineInterface(unittest.TestCase):
    """Test command-line interface functionality."""
    
    def test_parse_arguments_default(self):
        """Test parsing default arguments."""
        with patch('sys.argv', ['main.py']):
            args = parse_arguments()
            
            self.assertFalse(args.debug)
            self.assertFalse(args.config_check)
            self.assertEqual(args.log_level, 'INFO')  # Default from config
    
    def test_parse_arguments_debug(self):
        """Test parsing debug argument."""
        with patch('sys.argv', ['main.py', '--debug']):
            args = parse_arguments()
            
            self.assertTrue(args.debug)
    
    def test_parse_arguments_config_check(self):
        """Test parsing config-check argument."""
        with patch('sys.argv', ['main.py', '--config-check']):
            args = parse_arguments()
            
            self.assertTrue(args.config_check)
    
    def test_parse_arguments_log_level(self):
        """Test parsing log-level argument."""
        with patch('sys.argv', ['main.py', '--log-level', 'DEBUG']):
            args = parse_arguments()
            
            self.assertEqual(args.log_level, 'DEBUG')
    
    @patch('main.validate_config')
    def test_main_config_check_success(self, mock_validate):
        """Test main function with successful config check."""
        mock_validate.return_value = True
        
        with patch('sys.argv', ['main.py', '--config-check']):
            result = main()
            
            self.assertEqual(result, 0)
            mock_validate.assert_called_once()
    
    @patch('main.validate_config')
    def test_main_config_check_failure(self, mock_validate):
        """Test main function with failed config check."""
        mock_validate.return_value = False
        
        with patch('sys.argv', ['main.py', '--config-check']):
            result = main()
            
            self.assertEqual(result, 1)
            mock_validate.assert_called_once()
    
    @patch('main.AURAApplication')
    def test_main_application_startup_failure(self, mock_app_class):
        """Test main function with application startup failure."""
        mock_app = Mock()
        mock_app.startup.return_value = False
        mock_app_class.return_value = mock_app
        
        with patch('sys.argv', ['main.py']):
            result = main()
            
            self.assertEqual(result, 1)
            mock_app.startup.assert_called_once()
    
    @patch('main.AURAApplication')
    def test_main_application_success(self, mock_app_class):
        """Test main function with successful application run."""
        mock_app = Mock()
        mock_app.startup.return_value = True
        mock_app_class.return_value = mock_app
        
        with patch('sys.argv', ['main.py']):
            result = main()
            
            self.assertEqual(result, 0)
            mock_app.startup.assert_called_once()
            mock_app.run.assert_called_once()
            mock_app.shutdown.assert_called_once()
    
    @patch('main.AURAApplication')
    def test_main_keyboard_interrupt(self, mock_app_class):
        """Test main function with keyboard interrupt."""
        mock_app = Mock()
        mock_app.startup.return_value = True
        mock_app.run.side_effect = KeyboardInterrupt()
        mock_app_class.return_value = mock_app
        
        with patch('sys.argv', ['main.py']):
            result = main()
            
            self.assertEqual(result, 0)  # Keyboard interrupt should return 0
            mock_app.shutdown.assert_called_once()
    
    @patch('main.AURAApplication')
    def test_main_exception_handling(self, mock_app_class):
        """Test main function exception handling."""
        mock_app = Mock()
        mock_app.startup.return_value = True
        mock_app.run.side_effect = Exception("Test error")
        mock_app_class.return_value = mock_app
        
        with patch('sys.argv', ['main.py']):
            result = main()
            
            self.assertEqual(result, 1)  # Exception should return 1
            mock_app.shutdown.assert_called_once()


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    
    unittest.main()
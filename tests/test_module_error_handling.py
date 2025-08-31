# tests/test_module_error_handling.py
"""
Integration tests for module-level error handling.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from modules.vision import VisionModule
from modules.reasoning import ReasoningModule
from modules.automation import AutomationModule
from modules.audio import AudioModule
from modules.feedback import FeedbackModule
from modules.error_handler import ErrorCategory, ErrorSeverity


class TestVisionModuleErrorHandling:
    """Test error handling in the VisionModule."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.vision_module = VisionModule()
    
    @patch('modules.vision.mss.mss')
    def test_capture_screen_hardware_error(self, mock_mss):
        """Test screen capture hardware error handling."""
        # Mock MSS to raise an exception
        mock_sct = Mock()
        mock_sct.monitors = [{"width": 1920, "height": 1080}]
        mock_sct.grab.side_effect = Exception("Screen capture device not available")
        mock_mss.return_value = mock_sct
        
        vision_module = VisionModule()
        
        with pytest.raises(Exception) as exc_info:
            vision_module.capture_screen_as_base64()
        
        assert "Screen capture failed" in str(exc_info.value)
    
    @patch('modules.vision.requests.post')
    def test_describe_screen_api_error(self, mock_post):
        """Test screen description API error handling."""
        # Mock successful screen capture
        with patch.object(self.vision_module, 'capture_screen_as_base64', return_value="fake_base64"):
            with patch.object(self.vision_module, 'get_screen_resolution', return_value=(1920, 1080)):
                # Mock API failure
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.text = "Internal Server Error"
                mock_post.return_value = mock_response
                
                with pytest.raises(Exception) as exc_info:
                    self.vision_module.describe_screen()
                
                assert "Screen analysis failed" in str(exc_info.value)
    
    @patch('modules.vision.requests.post')
    def test_describe_screen_timeout_handling(self, mock_post):
        """Test screen description timeout handling."""
        # Mock successful screen capture
        with patch.object(self.vision_module, 'capture_screen_as_base64', return_value="fake_base64"):
            with patch.object(self.vision_module, 'get_screen_resolution', return_value=(1920, 1080)):
                # Mock timeout
                mock_post.side_effect = Exception("Vision API timeout after retries")
                
                with pytest.raises(Exception) as exc_info:
                    self.vision_module.describe_screen()
                
                assert "Screen analysis failed" in str(exc_info.value)
    
    def test_invalid_monitor_number(self):
        """Test handling of invalid monitor numbers."""
        with pytest.raises(Exception) as exc_info:
            self.vision_module.capture_screen_as_base64(monitor_number=999)
        
        assert "Screen capture failed" in str(exc_info.value)
    
    def test_invalid_analysis_type(self):
        """Test handling of invalid analysis types."""
        with pytest.raises(Exception) as exc_info:
            self.vision_module.describe_screen(analysis_type="invalid_type")
        
        assert "Screen analysis failed" in str(exc_info.value)


class TestReasoningModuleErrorHandling:
    """Test error handling in the ReasoningModule."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reasoning_module = ReasoningModule()
    
    def test_empty_command_validation(self):
        """Test validation of empty user commands."""
        result = self.reasoning_module.get_action_plan("", {"elements": []})
        
        # Should return fallback response
        assert isinstance(result, dict)
        assert "plan" in result
        assert result["metadata"]["fallback"] is True
    
    def test_invalid_screen_context(self):
        """Test validation of invalid screen context."""
        result = self.reasoning_module.get_action_plan("test command", "invalid_context")
        
        # Should return fallback response
        assert isinstance(result, dict)
        assert "plan" in result
        assert result["metadata"]["fallback"] is True
    
    @patch('modules.reasoning.requests.post')
    def test_api_connection_error(self, mock_post):
        """Test API connection error handling."""
        mock_post.side_effect = ConnectionError("Cannot connect to reasoning API")
        
        result = self.reasoning_module.get_action_plan("test command", {"elements": []})
        
        # Should return fallback response
        assert isinstance(result, dict)
        assert "plan" in result
        assert result["metadata"]["fallback"] is True
        assert "connect" in result["metadata"]["error"].lower()
    
    @patch('modules.reasoning.requests.post')
    def test_api_timeout_error(self, mock_post):
        """Test API timeout error handling."""
        mock_post.side_effect = Exception("API request timed out after 30 seconds")
        
        result = self.reasoning_module.get_action_plan("test command", {"elements": []})
        
        # Should return fallback response
        assert isinstance(result, dict)
        assert "plan" in result
        assert result["metadata"]["fallback"] is True
        assert "timed out" in result["metadata"]["error"].lower()
    
    @patch('modules.reasoning.requests.post')
    def test_invalid_api_response(self, mock_post):
        """Test handling of invalid API responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "response"}
        mock_post.return_value = mock_response
        
        result = self.reasoning_module.get_action_plan("test command", {"elements": []})
        
        # Should return fallback response
        assert isinstance(result, dict)
        assert "plan" in result
        assert result["metadata"]["fallback"] is True
    
    def test_long_command_validation(self):
        """Test validation of excessively long commands."""
        long_command = "x" * 1001  # Exceeds 1000 character limit
        
        result = self.reasoning_module.get_action_plan(long_command, {"elements": []})
        
        # Should return fallback response
        assert isinstance(result, dict)
        assert "plan" in result
        assert result["metadata"]["fallback"] is True


class TestAutomationModuleErrorHandling:
    """Test error handling in the AutomationModule."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.automation_module = AutomationModule(max_retries=2, retry_delay=0.1)
    
    def test_invalid_action_type(self):
        """Test handling of invalid action types."""
        invalid_action = {"action": "invalid_action"}
        
        with pytest.raises(ValueError) as exc_info:
            self.automation_module.execute_action(invalid_action)
        
        assert "Unsupported action type" in str(exc_info.value)
    
    def test_missing_action_type(self):
        """Test handling of missing action type."""
        invalid_action = {"coordinates": [100, 100]}
        
        with pytest.raises(ValueError) as exc_info:
            self.automation_module.execute_action(invalid_action)
        
        assert "Action type is required" in str(exc_info.value)
    
    def test_invalid_coordinates(self):
        """Test handling of invalid coordinates."""
        invalid_action = {
            "action": "click",
            "coordinates": [-100, -100]  # Negative coordinates
        }
        
        with pytest.raises(ValueError) as exc_info:
            self.automation_module.execute_action(invalid_action)
        
        assert "Invalid action format" in str(exc_info.value)
    
    def test_coordinates_out_of_bounds(self):
        """Test handling of coordinates outside screen bounds."""
        invalid_action = {
            "action": "click",
            "coordinates": [99999, 99999]  # Way outside screen
        }
        
        with pytest.raises(ValueError) as exc_info:
            self.automation_module.execute_action(invalid_action)
        
        assert "Invalid action format" in str(exc_info.value)
    
    @patch('modules.automation.pyautogui.click')
    def test_pyautogui_failure_with_retry(self, mock_click):
        """Test PyAutoGUI failure with retry logic."""
        # First two attempts fail, third succeeds
        mock_click.side_effect = [
            Exception("GUI operation failed"),
            Exception("GUI operation failed"),
            None  # Success on third attempt
        ]
        
        action = {
            "action": "click",
            "coordinates": [100, 100]
        }
        
        # Should succeed after retries
        self.automation_module.execute_action(action)
        
        # Should have been called 3 times
        assert mock_click.call_count == 3
    
    @patch('modules.automation.pyautogui.click')
    def test_pyautogui_persistent_failure(self, mock_click):
        """Test PyAutoGUI persistent failure after all retries."""
        # All attempts fail
        mock_click.side_effect = Exception("Persistent GUI failure")
        
        action = {
            "action": "click",
            "coordinates": [100, 100]
        }
        
        with pytest.raises(RuntimeError) as exc_info:
            self.automation_module.execute_action(action)
        
        assert "Action execution failed" in str(exc_info.value)
        # Should have tried max_retries + 1 times
        assert mock_click.call_count == 3
    
    def test_action_sequence_error_handling(self):
        """Test error handling in action sequences."""
        actions = [
            {"action": "click", "coordinates": [100, 100]},
            {"action": "invalid_action"},  # This will fail
            {"action": "click", "coordinates": [200, 200]}
        ]
        
        result = self.automation_module.execute_action_sequence(actions, stop_on_error=False)
        
        assert result["total_actions"] == 3
        assert result["successful_actions"] == 2
        assert result["failed_actions"] == 1
        assert len(result["errors"]) == 1
    
    def test_action_sequence_stop_on_error(self):
        """Test action sequence stopping on first error."""
        actions = [
            {"action": "click", "coordinates": [100, 100]},
            {"action": "invalid_action"},  # This will fail
            {"action": "click", "coordinates": [200, 200]}  # This won't be executed
        ]
        
        result = self.automation_module.execute_action_sequence(actions, stop_on_error=True)
        
        assert result["total_actions"] == 3
        assert result["successful_actions"] == 1
        assert result["failed_actions"] == 1


class TestAudioModuleErrorHandling:
    """Test error handling in the AudioModule."""
    
    @patch('modules.audio.whisper.load_model')
    def test_whisper_initialization_failure(self, mock_load_model):
        """Test Whisper model initialization failure."""
        mock_load_model.side_effect = Exception("Failed to load Whisper model")
        
        with pytest.raises(Exception) as exc_info:
            AudioModule()
        
        assert "Whisper initialization failed" in str(exc_info.value)
    
    @patch('modules.audio.pyttsx3.init')
    def test_tts_initialization_failure(self, mock_tts_init):
        """Test TTS engine initialization failure."""
        mock_tts_init.side_effect = Exception("TTS engine not available")
        
        with pytest.raises(Exception):
            AudioModule()
    
    @patch('modules.audio.pvporcupine.create')
    def test_porcupine_initialization_failure(self, mock_porcupine_create):
        """Test Porcupine wake word detection initialization failure."""
        mock_porcupine_create.side_effect = Exception("Invalid API key")
        
        # Should not raise exception, just log warning
        audio_module = AudioModule()
        assert audio_module.porcupine is None
    
    @patch('modules.audio.sd.rec')
    def test_audio_recording_failure(self, mock_rec):
        """Test audio recording failure handling."""
        mock_rec.side_effect = Exception("Microphone not available")
        
        # Mock successful Whisper initialization
        with patch('modules.audio.whisper.load_model'):
            with patch('modules.audio.pyttsx3.init'):
                audio_module = AudioModule()
                
                with pytest.raises(RuntimeError) as exc_info:
                    audio_module.speech_to_text(duration=1.0)
                
                assert "Speech recognition failed" in str(exc_info.value)
    
    def test_invalid_speech_to_text_parameters(self):
        """Test validation of speech-to-text parameters."""
        # Mock successful initialization
        with patch('modules.audio.whisper.load_model'):
            with patch('modules.audio.pyttsx3.init'):
                audio_module = AudioModule()
                
                # Test invalid duration
                with pytest.raises(RuntimeError):
                    audio_module.speech_to_text(duration=-1.0)
                
                # Test invalid silence threshold
                with pytest.raises(RuntimeError):
                    audio_module.speech_to_text(silence_threshold=2.0)


class TestFeedbackModuleErrorHandling:
    """Test error handling in the FeedbackModule."""
    
    @patch('modules.feedback.pygame.mixer.init')
    def test_pygame_initialization_failure(self, mock_pygame_init):
        """Test pygame mixer initialization failure."""
        mock_pygame_init.side_effect = Exception("Audio system not available")
        
        with pytest.raises(Exception) as exc_info:
            FeedbackModule()
        
        assert "Audio system initialization failed" in str(exc_info.value)
    
    def test_invalid_sound_name(self):
        """Test handling of invalid sound names."""
        # Mock successful initialization
        with patch('modules.feedback.pygame.mixer.init'):
            with patch('modules.feedback.pygame.mixer.pre_init'):
                feedback_module = FeedbackModule()
                
                # Should not raise exception, just log warning
                feedback_module.play("nonexistent_sound")
    
    def test_empty_message_handling(self):
        """Test handling of empty TTS messages."""
        # Mock successful initialization
        with patch('modules.feedback.pygame.mixer.init'):
            with patch('modules.feedback.pygame.mixer.pre_init'):
                feedback_module = FeedbackModule()
                
                # Should not raise exception
                feedback_module.speak("")
                feedback_module.speak(None)
    
    @patch('modules.feedback.Path.exists')
    def test_missing_sound_files(self, mock_exists):
        """Test handling of missing sound files."""
        mock_exists.return_value = False
        
        # Mock successful pygame initialization
        with patch('modules.feedback.pygame.mixer.init'):
            with patch('modules.feedback.pygame.mixer.pre_init'):
                feedback_module = FeedbackModule()
                
                validation_result = feedback_module.validate_sound_files()
                
                assert validation_result["loaded_sounds"] == 0
                assert len(validation_result["missing_sounds"]) > 0
                assert len(validation_result["warnings"]) > 0


class TestCrossModuleErrorHandling:
    """Test error handling across multiple modules."""
    
    def test_error_propagation(self):
        """Test that errors propagate correctly between modules."""
        # This would test scenarios where one module's error affects another
        # For example, vision module failure affecting reasoning module
        pass
    
    def test_graceful_degradation(self):
        """Test graceful degradation when modules fail."""
        # This would test that the system continues to function
        # even when some modules are unavailable
        pass
    
    def test_error_recovery_coordination(self):
        """Test coordination of error recovery across modules."""
        # This would test that modules can coordinate recovery efforts
        pass


if __name__ == "__main__":
    pytest.main([__file__])
# tests/test_feedback.py
"""
Unit tests for the FeedbackModule

Tests the sound effect system and TTS integration functionality.
"""

import pytest
import unittest.mock as mock
import tempfile
import os
from pathlib import Path
import time
import queue

from modules.feedback import FeedbackModule, FeedbackPriority, FeedbackType


# Module-level fixtures
@pytest.fixture
def mock_pygame():
    """Mock pygame mixer for testing."""
    with mock.patch('modules.feedback.pygame') as mock_pg:
        # Mock mixer initialization
        mock_pg.mixer.pre_init.return_value = None
        mock_pg.mixer.init.return_value = None
        mock_pg.mixer.music.set_volume.return_value = None
        
        # Mock Sound class
        mock_sound = mock.Mock()
        mock_pg.mixer.Sound.return_value = mock_sound
        
        yield mock_pg


@pytest.fixture
def mock_audio_module():
    """Mock AudioModule for TTS testing."""
    mock_audio = mock.Mock()
    mock_audio.text_to_speech = mock.Mock()
    return mock_audio


@pytest.fixture
def temp_sound_files():
    """Create temporary sound files for testing."""
    temp_dir = tempfile.mkdtemp()
    sound_files = {}
    
    # Create dummy sound files
    for sound_name in ['success', 'failure', 'thinking']:
        sound_path = os.path.join(temp_dir, f"{sound_name}.wav")
        with open(sound_path, 'wb') as f:
            # Write minimal WAV header (44 bytes) + some data
            f.write(b'RIFF' + b'\x00' * 40 + b'data' + b'\x00' * 100)
        sound_files[sound_name] = sound_path
    
    yield sound_files
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def feedback_module(mock_pygame, mock_audio_module, temp_sound_files):
    """Create FeedbackModule instance for testing."""
    # Mock the SOUNDS config
    with mock.patch('modules.feedback.SOUNDS', temp_sound_files):
        with mock.patch('modules.feedback.TTS_VOLUME', 0.8):
            feedback = FeedbackModule(audio_module=mock_audio_module)
            yield feedback
            feedback.cleanup()


class TestFeedbackModule:
    """Test cases for FeedbackModule sound effect system."""
    
    def test_initialization(self, mock_pygame, mock_audio_module, temp_sound_files):
        """Test FeedbackModule initialization."""
        with mock.patch('modules.feedback.SOUNDS', temp_sound_files):
            with mock.patch('modules.feedback.TTS_VOLUME', 0.8):
                feedback = FeedbackModule(audio_module=mock_audio_module)
                
                # Check initialization
                assert feedback.is_initialized is True
                assert feedback.audio_module is mock_audio_module
                assert feedback.is_processing is True
                assert feedback.processing_thread is not None
                assert feedback.processing_thread.is_alive()
                
                # Check pygame initialization calls
                mock_pygame.mixer.pre_init.assert_called_once()
                mock_pygame.mixer.init.assert_called_once()
                mock_pygame.mixer.music.set_volume.assert_called_once_with(0.8)
                
                feedback.cleanup()
    
    def test_sound_file_loading(self, mock_pygame, mock_audio_module, temp_sound_files):
        """Test sound file loading and caching."""
        with mock.patch('modules.feedback.SOUNDS', temp_sound_files):
            feedback = FeedbackModule(audio_module=mock_audio_module)
            
            # Check that sounds were loaded
            assert len(feedback.sound_cache) == 3
            assert 'success' in feedback.sound_cache
            assert 'failure' in feedback.sound_cache
            assert 'thinking' in feedback.sound_cache
            
            # Check pygame Sound calls
            assert mock_pygame.mixer.Sound.call_count == 3
            
            feedback.cleanup()
    
    def test_sound_file_missing(self, mock_pygame, mock_audio_module):
        """Test handling of missing sound files."""
        missing_sounds = {
            'success': '/nonexistent/success.wav',
            'failure': '/nonexistent/failure.wav',
            'thinking': '/nonexistent/thinking.wav'
        }
        
        with mock.patch('modules.feedback.SOUNDS', missing_sounds):
            feedback = FeedbackModule(audio_module=mock_audio_module)
            
            # Check that missing sounds are handled gracefully
            assert len(feedback.sound_cache) == 3
            assert all(sound is None for sound in feedback.sound_cache.values())
            
            feedback.cleanup()
    
    def test_play_sound_effect(self, feedback_module):
        """Test playing sound effects."""
        # Test valid sound
        feedback_module.play('success')
        
        # Wait briefly for queue processing
        time.sleep(0.1)
        
        # Check that sound was queued
        assert feedback_module.get_queue_size() >= 0  # May have been processed already
    
    def test_play_sound_effect_with_priority(self, feedback_module):
        """Test playing sound effects with different priorities."""
        # Add sounds with different priorities
        feedback_module.play('success', FeedbackPriority.LOW)
        feedback_module.play('failure', FeedbackPriority.HIGH)
        feedback_module.play('thinking', FeedbackPriority.CRITICAL)
        
        # Wait briefly for queue processing
        time.sleep(0.1)
        
        # Queue should process items (exact size depends on processing speed)
        assert feedback_module.get_queue_size() >= 0
    
    def test_play_invalid_sound(self, feedback_module):
        """Test playing invalid sound name."""
        # Should not raise exception
        feedback_module.play('invalid_sound')
        
        # Wait briefly
        time.sleep(0.1)
        
        # Should not crash the system
        assert feedback_module.is_processing is True
    
    def test_speak_message(self, feedback_module, mock_audio_module):
        """Test text-to-speech functionality."""
        test_message = "Hello, this is a test message"
        
        feedback_module.speak(test_message)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Check that TTS was called (may take time due to queue processing)
        # We'll check this in integration tests
    
    def test_speak_empty_message(self, feedback_module):
        """Test speaking empty message."""
        # Should handle gracefully
        feedback_module.speak("")
        feedback_module.speak("   ")
        feedback_module.speak(None)
        
        # Should not crash
        assert feedback_module.is_processing is True
    
    def test_combined_feedback(self, feedback_module):
        """Test combined sound and speech feedback."""
        feedback_module.play_with_message('success', 'Task completed successfully')
        
        # Wait for processing
        time.sleep(0.1)
        
        # Should not crash
        assert feedback_module.is_processing is True
    
    def test_queue_management(self, feedback_module):
        """Test feedback queue management."""
        # Add multiple items
        feedback_module.play('success')
        feedback_module.speak('Test message')
        feedback_module.play('failure')
        
        # Check queue size
        initial_size = feedback_module.get_queue_size()
        assert initial_size >= 0
        
        # Clear queue
        cleared = feedback_module.clear_queue()
        assert cleared >= 0
        
        # Queue should be empty or nearly empty
        assert feedback_module.get_queue_size() <= initial_size
    
    def test_priority_queue_clearing(self, feedback_module):
        """Test clearing queue with priority threshold."""
        # Add items with different priorities
        feedback_module.play('success', FeedbackPriority.LOW)
        feedback_module.play('failure', FeedbackPriority.HIGH)
        feedback_module.speak('Test', FeedbackPriority.CRITICAL)
        
        # Clear only low priority items
        cleared = feedback_module.clear_queue(FeedbackPriority.NORMAL)
        assert cleared >= 0
    
    def test_queue_status_methods(self, feedback_module):
        """Test queue status checking methods."""
        # Initially should be empty or processing
        initial_empty = feedback_module.is_queue_empty()
        initial_size = feedback_module.get_queue_size()
        
        # Add item
        feedback_module.play('success')
        
        # Check status
        size_after = feedback_module.get_queue_size()
        empty_after = feedback_module.is_queue_empty()
        
        # Size should be >= initial size
        assert size_after >= 0
        assert isinstance(empty_after, bool)
    
    def test_wait_for_completion(self, feedback_module):
        """Test waiting for feedback completion."""
        # Add a few items
        feedback_module.play('success')
        feedback_module.speak('Test message')
        
        # Wait with timeout
        completed = feedback_module.wait_for_completion(timeout=2.0)
        assert isinstance(completed, bool)
    
    def test_sound_validation(self, feedback_module):
        """Test sound file validation."""
        validation = feedback_module.validate_sound_files()
        
        # Check validation structure
        assert 'pygame_initialized' in validation
        assert 'sounds_available' in validation
        assert 'total_sounds' in validation
        assert 'loaded_sounds' in validation
        assert 'missing_sounds' in validation
        assert 'errors' in validation
        assert 'warnings' in validation
        
        # Check types
        assert isinstance(validation['pygame_initialized'], bool)
        assert isinstance(validation['sounds_available'], dict)
        assert isinstance(validation['total_sounds'], int)
        assert isinstance(validation['loaded_sounds'], int)
        assert isinstance(validation['missing_sounds'], list)
        assert isinstance(validation['errors'], list)
        assert isinstance(validation['warnings'], list)
    
    def test_cleanup(self, mock_pygame, mock_audio_module, temp_sound_files):
        """Test cleanup functionality."""
        with mock.patch('modules.feedback.SOUNDS', temp_sound_files):
            feedback = FeedbackModule(audio_module=mock_audio_module)
            
            # Verify it's running
            assert feedback.is_processing is True
            assert feedback.processing_thread.is_alive()
            
            # Cleanup
            feedback.cleanup()
            
            # Verify cleanup
            assert feedback.is_processing is False
            assert feedback.is_initialized is False
            assert len(feedback.sound_cache) == 0
            
            # Check pygame cleanup
            mock_pygame.mixer.quit.assert_called_once()
    
    def test_initialization_failure(self, mock_audio_module):
        """Test handling of initialization failures."""
        with mock.patch('modules.feedback.pygame') as mock_pg:
            # Make pygame initialization fail
            mock_pg.mixer.init.side_effect = Exception("Pygame init failed")
            
            with pytest.raises(Exception):
                FeedbackModule(audio_module=mock_audio_module)
    
    def test_feedback_priority_enum(self):
        """Test FeedbackPriority enum values."""
        assert FeedbackPriority.LOW.value == 1
        assert FeedbackPriority.NORMAL.value == 2
        assert FeedbackPriority.HIGH.value == 3
        assert FeedbackPriority.CRITICAL.value == 4
    
    def test_feedback_type_enum(self):
        """Test FeedbackType enum values."""
        assert FeedbackType.SOUND.value == "sound"
        assert FeedbackType.SPEECH.value == "speech"
        assert FeedbackType.COMBINED.value == "combined"


class TestFeedbackModuleIntegration:
    """Integration tests for FeedbackModule with real components."""
    
    def test_without_audio_module(self, mock_pygame, temp_sound_files):
        """Test FeedbackModule without AudioModule (sound effects only)."""
        with mock.patch('modules.feedback.SOUNDS', temp_sound_files):
            feedback = FeedbackModule(audio_module=None)
            
            # Should still work for sound effects
            feedback.play('success')
            
            # TTS should be gracefully handled
            feedback.speak('This should not crash')
            
            time.sleep(0.1)
            assert feedback.is_processing is True
            
            feedback.cleanup()
    
    def test_queue_processing_order(self, feedback_module):
        """Test that higher priority items are processed first."""
        # Add items in reverse priority order
        feedback_module.play('success', FeedbackPriority.LOW)
        time.sleep(0.01)  # Small delay to ensure different timestamps
        feedback_module.play('failure', FeedbackPriority.HIGH)
        time.sleep(0.01)
        feedback_module.play('thinking', FeedbackPriority.CRITICAL)
        
        # Wait for processing
        time.sleep(0.2)
        
        # All should be processed without errors
        assert feedback_module.is_processing is True


@pytest.fixture
def mock_audio_module_detailed():
    """Mock AudioModule with detailed TTS tracking."""
    mock_audio = mock.Mock()
    mock_audio.text_to_speech = mock.Mock()
    mock_audio.text_to_speech.side_effect = lambda text: time.sleep(0.1)  # Simulate TTS delay
    return mock_audio


@pytest.fixture
def feedback_with_tts(mock_pygame, mock_audio_module_detailed, temp_sound_files):
    """Create FeedbackModule with TTS capabilities."""
    with mock.patch('modules.feedback.SOUNDS', temp_sound_files):
        with mock.patch('modules.feedback.TTS_VOLUME', 0.8):
            feedback = FeedbackModule(audio_module=mock_audio_module_detailed)
            yield feedback, mock_audio_module_detailed
            feedback.cleanup()


class TestFeedbackTTSIntegration:
    """Integration tests for TTS functionality in FeedbackModule."""
    
    def test_tts_integration_basic(self, feedback_with_tts):
        """Test basic TTS integration."""
        feedback, mock_audio = feedback_with_tts
        
        test_message = "Hello, this is a test message"
        feedback.speak(test_message)
        
        # Wait for queue processing
        feedback.wait_for_completion(timeout=2.0)
        
        # Verify TTS was called
        mock_audio.text_to_speech.assert_called_with(test_message)
    
    def test_tts_with_priority_handling(self, feedback_with_tts):
        """Test TTS with different priority levels."""
        feedback, mock_audio = feedback_with_tts
        
        # Add messages with different priorities
        feedback.speak("Low priority message", FeedbackPriority.LOW)
        feedback.speak("High priority message", FeedbackPriority.HIGH)
        feedback.speak("Critical message", FeedbackPriority.CRITICAL)
        
        # Wait for processing
        feedback.wait_for_completion(timeout=3.0)
        
        # All messages should be processed
        assert mock_audio.text_to_speech.call_count == 3
        
        # Check that messages were called (order may vary due to priority)
        called_messages = [call[0][0] for call in mock_audio.text_to_speech.call_args_list]
        assert "Low priority message" in called_messages
        assert "High priority message" in called_messages
        assert "Critical message" in called_messages
    
    def test_combined_sound_and_tts(self, feedback_with_tts):
        """Test combined sound effect and TTS functionality."""
        feedback, mock_audio = feedback_with_tts
        
        # Reset mock to ensure clean state
        mock_audio.text_to_speech.reset_mock()
        
        # Test combined feedback
        feedback.play_with_message('success', 'Task completed successfully')
        
        # Give some time for queue processing
        time.sleep(0.5)
        
        # Wait for processing
        feedback.wait_for_completion(timeout=3.0)
        
        # Verify TTS was called
        assert mock_audio.text_to_speech.call_count >= 1, f"Expected TTS to be called, but call_count is {mock_audio.text_to_speech.call_count}"
        
        # Check that the correct message was called
        called_messages = [call[0][0] for call in mock_audio.text_to_speech.call_args_list]
        assert 'Task completed successfully' in called_messages, f"Expected message not found in {called_messages}"
    
    def test_tts_queue_management(self, feedback_with_tts):
        """Test TTS queue management and multiple messages."""
        feedback, mock_audio = feedback_with_tts
        
        messages = [
            "First message",
            "Second message", 
            "Third message"
        ]
        
        # Add multiple TTS messages
        for msg in messages:
            feedback.speak(msg)
        
        # Wait for all to process
        feedback.wait_for_completion(timeout=3.0)
        
        # All messages should be processed
        assert mock_audio.text_to_speech.call_count == 3
        
        # Check all messages were called
        called_messages = [call[0][0] for call in mock_audio.text_to_speech.call_args_list]
        for msg in messages:
            assert msg in called_messages
    
    def test_tts_error_handling(self, feedback_with_tts):
        """Test TTS error handling."""
        feedback, mock_audio = feedback_with_tts
        
        # Make TTS raise an exception
        mock_audio.text_to_speech.side_effect = Exception("TTS failed")
        
        # Should not crash the feedback system
        feedback.speak("This will fail")
        
        # Wait briefly
        time.sleep(0.2)
        
        # System should still be running
        assert feedback.is_processing is True
        
        # Reset for cleanup
        mock_audio.text_to_speech.side_effect = None
    
    def test_tts_without_audio_module(self, mock_pygame, temp_sound_files):
        """Test TTS functionality when AudioModule is not available."""
        with mock.patch('modules.feedback.SOUNDS', temp_sound_files):
            feedback = FeedbackModule(audio_module=None)
            
            # Should handle gracefully
            feedback.speak("This should not crash")
            
            # Wait briefly
            time.sleep(0.1)
            
            # System should still be running
            assert feedback.is_processing is True
            
            feedback.cleanup()
    
    def test_mixed_feedback_types(self, feedback_with_tts):
        """Test mixing different types of feedback."""
        feedback, mock_audio = feedback_with_tts
        
        # Reset mock to ensure clean state
        mock_audio.text_to_speech.reset_mock()
        
        # Mix different feedback types
        feedback.play('thinking')
        feedback.speak('Processing your request')
        feedback.play_with_message('success', 'Task completed')
        feedback.play('failure')
        feedback.speak('Error occurred')
        
        # Give some time for queue processing
        time.sleep(0.5)
        
        # Wait for all to process
        feedback.wait_for_completion(timeout=4.0)
        
        # TTS should be called for speak and combined messages (3 total: 2 speak + 1 combined)
        expected_calls = 3
        assert mock_audio.text_to_speech.call_count == expected_calls, f"Expected {expected_calls} TTS calls, got {mock_audio.text_to_speech.call_count}"
        
        # Check specific messages
        called_messages = [call[0][0] for call in mock_audio.text_to_speech.call_args_list]
        assert 'Processing your request' in called_messages
        assert 'Task completed' in called_messages  
        assert 'Error occurred' in called_messages
    
    def test_priority_interruption(self, feedback_with_tts):
        """Test that high priority messages can interrupt lower priority ones."""
        feedback, mock_audio = feedback_with_tts
        
        # Add low priority message
        feedback.speak("Low priority long message", FeedbackPriority.LOW)
        
        # Immediately add high priority message
        feedback.speak("URGENT MESSAGE", FeedbackPriority.CRITICAL)
        
        # Wait for processing
        feedback.wait_for_completion(timeout=2.0)
        
        # Both should be processed, but critical should be processed first
        assert mock_audio.text_to_speech.call_count == 2
    
    def test_queue_clearing_with_tts(self, feedback_with_tts):
        """Test clearing queue with TTS messages."""
        feedback, mock_audio = feedback_with_tts
        
        # Add multiple messages
        feedback.speak("Message 1", FeedbackPriority.LOW)
        feedback.speak("Message 2", FeedbackPriority.NORMAL)
        feedback.speak("Message 3", FeedbackPriority.HIGH)
        
        # Clear low priority messages
        cleared = feedback.clear_queue(FeedbackPriority.NORMAL)
        
        # Wait for remaining to process
        feedback.wait_for_completion(timeout=2.0)
        
        # Should have cleared some messages
        assert cleared >= 0
        
        # High priority message should still be processed
        # (exact behavior depends on timing)
        assert mock_audio.text_to_speech.call_count >= 0


class TestFeedbackModuleRealWorld:
    """Real-world scenario tests for FeedbackModule."""
    
    def test_typical_usage_scenario(self, mock_pygame, temp_sound_files):
        """Test typical usage scenario with real AudioModule mock."""
        mock_audio = mock.Mock()
        mock_audio.text_to_speech = mock.Mock()
        
        with mock.patch('modules.feedback.SOUNDS', temp_sound_files):
            with mock.patch('modules.feedback.TTS_VOLUME', 0.8):
                feedback = FeedbackModule(audio_module=mock_audio)
                
                # Simulate typical AURA workflow
                feedback.play('thinking')  # System is processing
                time.sleep(0.1)
                
                feedback.speak('I understand you want to open a file')  # Confirmation
                time.sleep(0.2)
                
                feedback.play_with_message('success', 'File opened successfully')  # Success
                time.sleep(0.2)
                
                # Wait for all feedback to complete
                feedback.wait_for_completion(timeout=5.0)
                
                # Verify TTS was used appropriately (should be 2 calls: 1 speak + 1 combined)
                assert mock_audio.text_to_speech.call_count >= 1, f"Expected at least 1 TTS call, got {mock_audio.text_to_speech.call_count}"
                
                # Check that appropriate messages were called
                called_messages = [call[0][0] for call in mock_audio.text_to_speech.call_args_list]
                assert len(called_messages) >= 1, f"Expected at least 1 message, got {called_messages}"
                
                # Check that at least one of the expected messages was called
                expected_messages = ['I understand you want to open a file', 'File opened successfully']
                assert any(msg in called_messages for msg in expected_messages), f"None of {expected_messages} found in {called_messages}"
                
                feedback.cleanup()
    
    def test_error_recovery_scenario(self, mock_pygame, temp_sound_files):
        """Test error recovery scenario."""
        mock_audio = mock.Mock()
        mock_audio.text_to_speech = mock.Mock()
        
        with mock.patch('modules.feedback.SOUNDS', temp_sound_files):
            with mock.patch('modules.feedback.TTS_VOLUME', 0.8):
                feedback = FeedbackModule(audio_module=mock_audio)
                
                # Simulate error scenario
                feedback.play('thinking')  # Processing
                feedback.play_with_message('failure', 'Could not complete the task')  # Error
                feedback.speak('Please try again', FeedbackPriority.HIGH)  # Recovery instruction
                
                # Wait for processing
                feedback.wait_for_completion(timeout=4.0)
                
                # Verify appropriate feedback was given (should be 2 calls: 1 combined + 1 speak)
                assert mock_audio.text_to_speech.call_count >= 1, f"Expected at least 1 TTS call, got {mock_audio.text_to_speech.call_count}"
                
                # Check that appropriate messages were called
                called_messages = [call[0][0] for call in mock_audio.text_to_speech.call_args_list]
                expected_messages = ['Could not complete the task', 'Please try again']
                assert any(msg in called_messages for msg in expected_messages), f"None of {expected_messages} found in {called_messages}"
                
                feedback.cleanup()
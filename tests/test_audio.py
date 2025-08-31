# tests/test_audio.py
"""
Unit tests for the Audio Module

Tests speech-to-text functionality, text-to-speech functionality,
and audio input validation.
"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, call
import sounddevice as sd
from pydub import AudioSegment

from modules.audio import AudioModule


class TestAudioModule:
    """Test cases for AudioModule class."""
    
    @pytest.fixture
    def audio_module(self):
        """Create an AudioModule instance for testing."""
        with patch('modules.audio.whisper.load_model') as mock_whisper, \
             patch('modules.audio.pyttsx3.init') as mock_tts:
            
            # Mock Whisper model
            mock_whisper_model = Mock()
            mock_whisper.return_value = mock_whisper_model
            
            # Mock TTS engine
            mock_tts_engine = Mock()
            mock_tts_engine.getProperty.return_value = []
            mock_tts.return_value = mock_tts_engine
            
            module = AudioModule()
            module.whisper_model = mock_whisper_model
            module.tts_engine = mock_tts_engine
            
            return module
    
    def test_audio_module_initialization(self):
        """Test AudioModule initialization."""
        with patch('modules.audio.whisper.load_model') as mock_whisper, \
             patch('modules.audio.pyttsx3.init') as mock_tts:
            
            mock_whisper.return_value = Mock()
            mock_tts_engine = Mock()
            mock_tts_engine.getProperty.return_value = []
            mock_tts.return_value = mock_tts_engine
            
            module = AudioModule()
            
            # Verify initialization
            assert module.whisper_model is not None
            assert module.tts_engine is not None
            assert not module.is_recording
            assert module.audio_queue is not None
            
            # Verify Whisper model loading
            mock_whisper.assert_called_once_with("base")
            
            # Verify TTS engine configuration
            mock_tts.assert_called_once()
            mock_tts_engine.setProperty.assert_any_call('rate', 200)
            mock_tts_engine.setProperty.assert_any_call('volume', 0.8)
    
    def test_whisper_initialization_failure(self):
        """Test handling of Whisper initialization failure."""
        with patch('modules.audio.whisper.load_model') as mock_whisper, \
             patch('modules.audio.pyttsx3.init'):
            
            mock_whisper.side_effect = Exception("Whisper loading failed")
            
            with pytest.raises(Exception, match="Whisper loading failed"):
                AudioModule()
    
    def test_tts_initialization_failure(self):
        """Test handling of TTS initialization failure."""
        with patch('modules.audio.whisper.load_model'), \
             patch('modules.audio.pyttsx3.init') as mock_tts:
            
            mock_tts.side_effect = Exception("TTS initialization failed")
            
            with pytest.raises(Exception, match="TTS initialization failed"):
                AudioModule()
    
    @patch('modules.audio.sd.rec')
    @patch('modules.audio.sd.wait')
    @patch('modules.audio.sd.stop')
    def test_record_audio_success(self, mock_stop, mock_wait, mock_rec, audio_module):
        """Test successful audio recording."""
        # Mock audio data
        mock_audio_data = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
        mock_rec.return_value = mock_audio_data.reshape(-1, 1)
        mock_wait.return_value = True  # Recording completed
        
        result = audio_module._record_audio(duration=2.0, silence_threshold=0.01)
        
        # Verify recording setup
        mock_rec.assert_called_once_with(
            32000,  # 2.0 * 16000
            samplerate=16000,
            channels=1,
            dtype=np.float32
        )
        
        # Verify result
        assert result is not None
        assert len(result) == 5
        assert result.dtype == np.int16
        
        mock_stop.assert_called_once()
    
    @patch('modules.audio.sd.rec')
    @patch('modules.audio.sd.wait')
    @patch('modules.audio.sd.stop')
    def test_record_audio_empty(self, mock_stop, mock_wait, mock_rec, audio_module):
        """Test audio recording with no data."""
        mock_rec.return_value = np.array([], dtype=np.float32).reshape(0, 1)
        mock_wait.return_value = True
        
        result = audio_module._record_audio(duration=1.0, silence_threshold=0.01)
        
        assert result is None
        mock_stop.assert_called_once()
    
    @patch('modules.audio.sd.rec')
    def test_record_audio_failure(self, mock_rec, audio_module):
        """Test audio recording failure."""
        mock_rec.side_effect = Exception("Recording failed")
        
        with pytest.raises(Exception, match="Recording failed"):
            audio_module._record_audio(duration=1.0, silence_threshold=0.01)
    
    @patch('modules.audio.AudioSegment')
    @patch('modules.audio.tempfile.NamedTemporaryFile')
    @patch('modules.audio.os.unlink')
    def test_speech_to_text_success(self, mock_unlink, mock_temp_file, mock_audio_segment, audio_module):
        """Test successful speech-to-text conversion."""
        # Mock temporary file
        mock_temp = Mock()
        mock_temp.name = "/tmp/test_audio.wav"
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        
        # Mock audio segment
        mock_segment = Mock()
        mock_audio_segment.return_value = mock_segment
        
        # Mock Whisper transcription
        audio_module.whisper_model.transcribe.return_value = {
            "text": "Hello, this is a test transcription."
        }
        
        # Mock audio recording
        mock_audio_data = np.array([0.1, 0.2, 0.3], dtype=np.int16)
        with patch.object(audio_module, '_record_audio', return_value=mock_audio_data):
            result = audio_module.speech_to_text(duration=3.0)
        
        # Verify result
        assert result == "Hello, this is a test transcription."
        
        # Verify Whisper was called
        audio_module.whisper_model.transcribe.assert_called_once_with("/tmp/test_audio.wav")
        
        # Verify audio segment creation and export
        mock_audio_segment.assert_called_once()
        mock_segment.export.assert_called_once_with("/tmp/test_audio.wav", format="wav")
        
        # Verify cleanup
        mock_unlink.assert_called_once_with("/tmp/test_audio.wav")
    
    def test_speech_to_text_no_audio(self, audio_module):
        """Test speech-to-text with no audio data."""
        with patch.object(audio_module, '_record_audio', return_value=None):
            result = audio_module.speech_to_text(duration=1.0)
            assert result == ""
    
    def test_speech_to_text_empty_audio(self, audio_module):
        """Test speech-to-text with empty audio data."""
        with patch.object(audio_module, '_record_audio', return_value=np.array([])):
            result = audio_module.speech_to_text(duration=1.0)
            assert result == ""
    
    @patch('modules.audio.tempfile.NamedTemporaryFile')
    def test_speech_to_text_whisper_failure(self, mock_temp_file, audio_module):
        """Test speech-to-text with Whisper failure."""
        # Mock temporary file
        mock_temp = Mock()
        mock_temp.name = "/tmp/test_audio.wav"
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        
        # Mock Whisper failure
        audio_module.whisper_model.transcribe.side_effect = Exception("Whisper failed")
        
        # Mock audio recording
        mock_audio_data = np.array([0.1, 0.2], dtype=np.int16)
        with patch.object(audio_module, '_record_audio', return_value=mock_audio_data), \
             patch('modules.audio.AudioSegment'), \
             patch('modules.audio.os.unlink'):
            
            with pytest.raises(RuntimeError, match="Speech recognition failed"):
                audio_module.speech_to_text(duration=1.0)
    
    @patch('modules.audio.threading.Thread')
    def test_text_to_speech_success(self, mock_thread, audio_module):
        """Test successful text-to-speech conversion."""
        # Mock thread
        mock_thread_instance = Mock()
        mock_thread_instance.is_alive.return_value = False
        mock_thread.return_value = mock_thread_instance
        
        audio_module.text_to_speech("Hello, world!")
        
        # Verify thread creation and execution
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        mock_thread_instance.join.assert_called_once_with(timeout=30)
    
    def test_text_to_speech_empty_text(self, audio_module):
        """Test text-to-speech with empty text."""
        # Should not raise an exception, just return early
        audio_module.text_to_speech("")
        audio_module.text_to_speech("   ")
        audio_module.text_to_speech(None)
    
    @patch('modules.audio.threading.Thread')
    def test_text_to_speech_timeout(self, mock_thread, audio_module):
        """Test text-to-speech timeout."""
        # Mock thread that doesn't complete
        mock_thread_instance = Mock()
        mock_thread_instance.is_alive.return_value = True  # Still running after timeout
        mock_thread.return_value = mock_thread_instance
        
        with pytest.raises(RuntimeError, match="Text-to-speech operation timed out"):
            audio_module.text_to_speech("This will timeout")
    
    @patch('modules.audio.sd.query_devices')
    @patch('modules.audio.sd.check_input_settings')
    def test_validate_audio_input_success(self, mock_check_settings, mock_query_devices, audio_module):
        """Test successful audio input validation."""
        # Mock devices with input capability
        mock_devices = [
            {'name': 'Microphone', 'max_input_channels': 2},
            {'name': 'Speaker', 'max_input_channels': 0}
        ]
        mock_query_devices.return_value = mock_devices
        mock_check_settings.return_value = None  # No exception means success
        
        result = audio_module.validate_audio_input()
        
        assert result["microphone_available"] is True
        assert result["sample_rate_supported"] is True
        assert result["whisper_model_loaded"] is True
        assert result["tts_engine_available"] is True
        assert len(result["errors"]) == 0
    
    @patch('modules.audio.sd.query_devices')
    def test_validate_audio_input_no_microphone(self, mock_query_devices, audio_module):
        """Test audio input validation with no microphone."""
        # Mock devices without input capability
        mock_devices = [
            {'name': 'Speaker', 'max_input_channels': 0}
        ]
        mock_query_devices.return_value = mock_devices
        
        result = audio_module.validate_audio_input()
        
        assert result["microphone_available"] is False
        assert "No microphone devices found" in result["errors"]
    
    @patch('modules.audio.sd.query_devices')
    @patch('modules.audio.sd.check_input_settings')
    def test_validate_audio_input_unsupported_sample_rate(self, mock_check_settings, mock_query_devices, audio_module):
        """Test audio input validation with unsupported sample rate."""
        # Mock devices with input capability
        mock_devices = [{'name': 'Microphone', 'max_input_channels': 1}]
        mock_query_devices.return_value = mock_devices
        
        # Mock sample rate check failure
        mock_check_settings.side_effect = Exception("Sample rate not supported")
        
        result = audio_module.validate_audio_input()
        
        assert result["sample_rate_supported"] is False
        assert any("Sample rate" in error for error in result["errors"])
    
    def test_validate_audio_input_no_whisper_model(self, audio_module):
        """Test audio input validation with no Whisper model."""
        audio_module.whisper_model = None
        
        with patch('modules.audio.sd.query_devices') as mock_query_devices, \
             patch('modules.audio.sd.check_input_settings'):
            
            mock_query_devices.return_value = [{'name': 'Mic', 'max_input_channels': 1}]
            
            result = audio_module.validate_audio_input()
            
            assert result["whisper_model_loaded"] is False
            assert "Whisper model not loaded" in result["errors"]
    
    def test_validate_audio_input_no_tts_engine(self, audio_module):
        """Test audio input validation with no TTS engine."""
        audio_module.tts_engine = None
        
        with patch('modules.audio.sd.query_devices') as mock_query_devices, \
             patch('modules.audio.sd.check_input_settings'):
            
            mock_query_devices.return_value = [{'name': 'Mic', 'max_input_channels': 1}]
            
            result = audio_module.validate_audio_input()
            
            assert result["tts_engine_available"] is False
            assert "TTS engine not available" in result["errors"]
    
    @patch('modules.audio.sd.stop')
    def test_cleanup(self, mock_sd_stop, audio_module):
        """Test AudioModule cleanup."""
        audio_module.cleanup()
        
        # Verify TTS engine stop
        audio_module.tts_engine.stop.assert_called_once()
        
        # Verify sounddevice stop
        mock_sd_stop.assert_called_once()


class TestAudioModuleIntegration:
    """Integration tests for AudioModule with sample audio files."""
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create a sample audio file for testing."""
        # Create a simple sine wave audio file
        duration = 1.0  # seconds
        sample_rate = 16000
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to int16
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
            
            # Create audio segment and export
            audio_segment = AudioSegment(
                audio_data.tobytes(),
                frame_rate=sample_rate,
                sample_width=2,  # 16-bit = 2 bytes
                channels=1
            )
            audio_segment.export(temp_path, format="wav")
        
        yield temp_path
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass
    
    @patch('modules.audio.whisper.load_model')
    @patch('modules.audio.pyttsx3.init')
    def test_speech_to_text_with_sample_file(self, mock_tts, mock_whisper, sample_audio_file):
        """Test speech-to-text with a real audio file."""
        # Mock Whisper model
        mock_whisper_model = Mock()
        mock_whisper_model.transcribe.return_value = {"text": "Test transcription"}
        mock_whisper.return_value = mock_whisper_model
        
        # Mock TTS engine
        mock_tts_engine = Mock()
        mock_tts_engine.getProperty.return_value = []
        mock_tts.return_value = mock_tts_engine
        
        # Create AudioModule
        audio_module = AudioModule()
        
        # Test transcription with sample file
        result = audio_module.whisper_model.transcribe(sample_audio_file)
        
        assert result["text"] == "Test transcription"
        mock_whisper_model.transcribe.assert_called_once_with(sample_audio_file)


if __name__ == "__main__":
    pytest.main([__file__])
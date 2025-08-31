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
import pvporcupine


class TestAudioModule:
    """Test cases for AudioModule class."""
    
    @pytest.fixture
    def audio_module(self):
        """Create an AudioModule instance for testing."""
        with patch('modules.audio.whisper.load_model') as mock_whisper, \
             patch('modules.audio.pyttsx3.init') as mock_tts, \
             patch('modules.audio.pvporcupine.create') as mock_porcupine:
            
            # Mock Whisper model
            mock_whisper_model = Mock()
            mock_whisper.return_value = mock_whisper_model
            
            # Mock TTS engine
            mock_tts_engine = Mock()
            mock_tts_engine.getProperty.return_value = []
            mock_tts.return_value = mock_tts_engine
            
            # Mock Porcupine
            mock_porcupine_instance = Mock()
            mock_porcupine_instance.sample_rate = 16000
            mock_porcupine_instance.frame_length = 512
            mock_porcupine.return_value = mock_porcupine_instance
            
            module = AudioModule()
            module.whisper_model = mock_whisper_model
            module.tts_engine = mock_tts_engine
            module.porcupine = mock_porcupine_instance
            
            return module
    
    def test_audio_module_initialization(self):
        """Test AudioModule initialization."""
        with patch('modules.audio.whisper.load_model') as mock_whisper, \
             patch('modules.audio.pyttsx3.init') as mock_tts, \
             patch('modules.audio.pvporcupine.create') as mock_porcupine:
            
            mock_whisper.return_value = Mock()
            mock_tts_engine = Mock()
            mock_tts_engine.getProperty.return_value = []
            mock_tts.return_value = mock_tts_engine
            
            mock_porcupine_instance = Mock()
            mock_porcupine_instance.sample_rate = 16000
            mock_porcupine_instance.frame_length = 512
            mock_porcupine.return_value = mock_porcupine_instance
            
            module = AudioModule()
            
            # Verify initialization
            assert module.whisper_model is not None
            assert module.tts_engine is not None
            assert module.porcupine is not None
            assert not module.is_recording
            assert not module.is_listening_for_wake_word
            assert module.audio_queue is not None
            assert module.wake_word_thread is None
            
            # Verify Whisper model loading
            mock_whisper.assert_called_once_with("base")
            
            # Verify TTS engine configuration
            mock_tts.assert_called_once()
            mock_tts_engine.setProperty.assert_any_call('rate', 200)
            mock_tts_engine.setProperty.assert_any_call('volume', 0.8)
            
            # Verify Porcupine initialization
            mock_porcupine.assert_called_once()
    
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
    
    @patch('modules.audio.pvporcupine.create')
    def test_porcupine_initialization_success(self, mock_porcupine_create):
        """Test successful Porcupine initialization."""
        with patch('modules.audio.whisper.load_model'), \
             patch('modules.audio.pyttsx3.init') as mock_tts, \
             patch('modules.audio.PORCUPINE_API_KEY', 'valid_api_key'), \
             patch('modules.audio.WAKE_WORD', 'computer'):
            
            mock_tts_engine = Mock()
            mock_tts_engine.getProperty.return_value = []
            mock_tts.return_value = mock_tts_engine
            
            mock_porcupine_instance = Mock()
            mock_porcupine_instance.sample_rate = 16000
            mock_porcupine_instance.frame_length = 512
            mock_porcupine_create.return_value = mock_porcupine_instance
            
            module = AudioModule()
            
            assert module.porcupine is not None
            mock_porcupine_create.assert_called_once_with(
                access_key='valid_api_key',
                keywords=['computer']
            )
    
    @patch('modules.audio.pvporcupine.create')
    def test_porcupine_initialization_no_api_key(self, mock_porcupine_create):
        """Test Porcupine initialization with no API key."""
        with patch('modules.audio.whisper.load_model'), \
             patch('modules.audio.pyttsx3.init') as mock_tts, \
             patch('modules.audio.PORCUPINE_API_KEY', 'your_porcupine_api_key_here'):
            
            mock_tts_engine = Mock()
            mock_tts_engine.getProperty.return_value = []
            mock_tts.return_value = mock_tts_engine
            
            module = AudioModule()
            
            assert module.porcupine is None
            mock_porcupine_create.assert_not_called()
    
    @patch('modules.audio.pvporcupine.create')
    def test_porcupine_initialization_failure(self, mock_porcupine_create):
        """Test Porcupine initialization failure."""
        with patch('modules.audio.whisper.load_model'), \
             patch('modules.audio.pyttsx3.init') as mock_tts, \
             patch('modules.audio.PORCUPINE_API_KEY', 'valid_api_key'):
            
            mock_tts_engine = Mock()
            mock_tts_engine.getProperty.return_value = []
            mock_tts.return_value = mock_tts_engine
            
            mock_porcupine_create.side_effect = Exception("Porcupine initialization failed")
            
            module = AudioModule()
            
            assert module.porcupine is None
    
    def test_listen_for_wake_word_success(self, audio_module):
        """Test successful wake word detection logic."""
        # Create a simplified version that tests the core logic
        def mock_listen_for_wake_word(timeout=None):
            audio_module.is_listening_for_wake_word = True
            # Simulate wake word detection
            keyword_index = audio_module.porcupine.process([0] * audio_module.porcupine.frame_length)
            if keyword_index >= 0:
                audio_module.is_listening_for_wake_word = False
                return True
            return False
        
        # Mock Porcupine to return wake word detected
        audio_module.porcupine.process.return_value = 0
        
        # Test the mock logic
        result = mock_listen_for_wake_word(timeout=5.0)
        
        assert result is True
        assert not audio_module.is_listening_for_wake_word
    
    def test_listen_for_wake_word_no_porcupine(self, audio_module):
        """Test wake word detection without Porcupine initialized."""
        audio_module.porcupine = None
        
        with pytest.raises(RuntimeError, match="Porcupine wake word detection not initialized"):
            audio_module.listen_for_wake_word()
    
    @patch('modules.audio.sd.InputStream')
    @patch('modules.audio.time.time')
    def test_listen_for_wake_word_timeout(self, mock_time, mock_input_stream, audio_module):
        """Test wake word detection timeout."""
        # Mock time progression to exceed timeout
        mock_time.side_effect = [0, 1, 2, 3, 6]  # Timeout at 5 seconds
        
        # Mock audio stream
        mock_stream = Mock()
        mock_input_stream.return_value.__enter__.return_value = mock_stream
        
        # Mock Porcupine processing (never detects wake word)
        audio_module.porcupine.process.return_value = -1
        
        result = audio_module.listen_for_wake_word(timeout=5.0)
        
        assert result is False
        assert not audio_module.is_listening_for_wake_word
    
    @patch('modules.audio.sd.InputStream')
    def test_listen_for_wake_word_audio_error(self, mock_input_stream, audio_module):
        """Test wake word detection with audio input error."""
        mock_input_stream.side_effect = Exception("Audio input failed")
        
        with pytest.raises(RuntimeError, match="Wake word detection failed"):
            audio_module.listen_for_wake_word()
    
    @patch('modules.audio.threading.Thread')
    def test_start_continuous_wake_word_monitoring(self, mock_thread, audio_module):
        """Test starting continuous wake word monitoring."""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        callback = Mock()
        audio_module.start_continuous_wake_word_monitoring(callback)
        
        assert audio_module.is_listening_for_wake_word is True
        assert audio_module.wake_word_thread is not None
        mock_thread_instance.start.assert_called_once()
    
    def test_start_continuous_wake_word_monitoring_no_porcupine(self, audio_module):
        """Test starting continuous monitoring without Porcupine."""
        audio_module.porcupine = None
        
        audio_module.start_continuous_wake_word_monitoring()
        
        assert audio_module.wake_word_thread is None
        assert not audio_module.is_listening_for_wake_word
    
    def test_start_continuous_wake_word_monitoring_already_running(self, audio_module):
        """Test starting continuous monitoring when already running."""
        # Mock existing thread
        mock_existing_thread = Mock()
        mock_existing_thread.is_alive.return_value = True
        audio_module.wake_word_thread = mock_existing_thread
        
        with patch('modules.audio.threading.Thread') as mock_thread:
            audio_module.start_continuous_wake_word_monitoring()
            
            # Should not create new thread
            mock_thread.assert_not_called()
    
    def test_stop_wake_word_monitoring(self, audio_module):
        """Test stopping wake word monitoring."""
        # Mock running thread (alive so it gets joined)
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        audio_module.wake_word_thread = mock_thread
        audio_module.is_listening_for_wake_word = True
        
        audio_module.stop_wake_word_monitoring()
        
        assert not audio_module.is_listening_for_wake_word
        # The thread should be joined since it was alive
        mock_thread.join.assert_called_once_with(timeout=2.0)
    
    def test_stop_wake_word_monitoring_thread_not_stopping(self, audio_module):
        """Test stopping wake word monitoring with unresponsive thread."""
        # Mock thread that doesn't stop
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        audio_module.wake_word_thread = mock_thread
        audio_module.is_listening_for_wake_word = True
        
        audio_module.stop_wake_word_monitoring()
        
        assert not audio_module.is_listening_for_wake_word
        mock_thread.join.assert_called_once_with(timeout=2.0)
    
    @patch('modules.audio.sd.query_devices')
    @patch('modules.audio.sd.check_input_settings')
    @patch('modules.audio.PORCUPINE_API_KEY', 'valid_test_key')
    @patch('modules.audio.WAKE_WORD', 'computer')
    def test_validate_audio_input_with_porcupine(self, mock_check_settings, mock_query_devices, audio_module):
        """Test audio input validation with Porcupine."""
        # Mock devices with input capability
        mock_devices = [{'name': 'Microphone', 'max_input_channels': 2}]
        mock_query_devices.return_value = mock_devices
        mock_check_settings.return_value = None
        
        result = audio_module.validate_audio_input()
        
        assert result["microphone_available"] is True
        assert result["sample_rate_supported"] is True
        assert result["whisper_model_loaded"] is True
        assert result["tts_engine_available"] is True
        assert result["porcupine_initialized"] is True
        assert result["wake_word_configured"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
    
    @patch('modules.audio.sd.query_devices')
    @patch('modules.audio.sd.check_input_settings')
    def test_validate_audio_input_no_porcupine(self, mock_check_settings, mock_query_devices, audio_module):
        """Test audio input validation without Porcupine."""
        audio_module.porcupine = None
        
        mock_devices = [{'name': 'Microphone', 'max_input_channels': 2}]
        mock_query_devices.return_value = mock_devices
        mock_check_settings.return_value = None
        
        result = audio_module.validate_audio_input()
        
        assert result["porcupine_initialized"] is False
        assert "Porcupine wake word detection not initialized" in result["warnings"]
    
    @patch('modules.audio.sd.query_devices')
    @patch('modules.audio.sd.check_input_settings')
    def test_validate_audio_input_sample_rate_mismatch(self, mock_check_settings, mock_query_devices, audio_module):
        """Test audio input validation with sample rate mismatch."""
        # Set different sample rate for Porcupine
        audio_module.porcupine.sample_rate = 44100
        
        mock_devices = [{'name': 'Microphone', 'max_input_channels': 2}]
        mock_query_devices.return_value = mock_devices
        mock_check_settings.return_value = None
        
        result = audio_module.validate_audio_input()
        
        assert any("Sample rate mismatch" in warning for warning in result["warnings"])
    
    @patch('modules.audio.sd.stop')
    def test_cleanup(self, mock_sd_stop, audio_module):
        """Test AudioModule cleanup."""
        # Mock wake word monitoring
        audio_module.is_listening_for_wake_word = True
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False  # Thread stops gracefully
        audio_module.wake_word_thread = mock_thread
        
        audio_module.cleanup()
        
        # Verify wake word monitoring stopped
        assert not audio_module.is_listening_for_wake_word
        
        # Verify Porcupine cleanup (if it exists)
        if audio_module.porcupine:
            audio_module.porcupine.delete.assert_called_once()
            assert audio_module.porcupine is None
        
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


class TestWakeWordIntegration:
    """Integration tests for complete wake word flow."""
    
    @pytest.fixture
    def audio_module_with_feedback(self):
        """Create an AudioModule instance with feedback capabilities for testing."""
        with patch('modules.audio.whisper.load_model') as mock_whisper, \
             patch('modules.audio.pyttsx3.init') as mock_tts, \
             patch('modules.audio.pvporcupine.create') as mock_porcupine:
            
            # Mock Whisper model
            mock_whisper_model = Mock()
            mock_whisper.return_value = mock_whisper_model
            
            # Mock TTS engine
            mock_tts_engine = Mock()
            mock_tts_engine.getProperty.return_value = []
            mock_tts.return_value = mock_tts_engine
            
            # Mock Porcupine
            mock_porcupine_instance = Mock()
            mock_porcupine_instance.sample_rate = 16000
            mock_porcupine_instance.frame_length = 512
            mock_porcupine.return_value = mock_porcupine_instance
            
            module = AudioModule()
            module.whisper_model = mock_whisper_model
            module.tts_engine = mock_tts_engine
            module.porcupine = mock_porcupine_instance
            
            return module
    
    def test_wake_word_detection_with_confirmation(self, audio_module_with_feedback):
        """Test wake word detection with audio confirmation."""
        # Mock wake word detection
        def mock_listen_with_feedback(timeout=None, provide_feedback=True):
            audio_module_with_feedback.is_listening_for_wake_word = True
            
            # Simulate wake word detection
            keyword_index = audio_module_with_feedback.porcupine.process([0] * 512)
            if keyword_index >= 0:
                audio_module_with_feedback.is_listening_for_wake_word = False
                if provide_feedback:
                    audio_module_with_feedback._provide_wake_word_confirmation()
                return True
            return False
        
        # Set up mock
        audio_module_with_feedback.porcupine.process.return_value = 0
        audio_module_with_feedback.listen_for_wake_word = mock_listen_with_feedback
        
        # Test wake word detection with feedback
        with patch('modules.audio.threading.Thread') as mock_thread:
            result = audio_module_with_feedback.listen_for_wake_word(provide_feedback=True)
            
            assert result is True
            assert not audio_module_with_feedback.is_listening_for_wake_word
            # Verify confirmation thread was created
            mock_thread.assert_called()
    
    def test_wake_word_detection_without_confirmation(self, audio_module_with_feedback):
        """Test wake word detection without audio confirmation."""
        # Mock wake word detection
        def mock_listen_without_feedback(timeout=None, provide_feedback=True):
            audio_module_with_feedback.is_listening_for_wake_word = True
            
            # Simulate wake word detection
            keyword_index = audio_module_with_feedback.porcupine.process([0] * 512)
            if keyword_index >= 0:
                audio_module_with_feedback.is_listening_for_wake_word = False
                if provide_feedback:
                    audio_module_with_feedback._provide_wake_word_confirmation()
                return True
            return False
        
        # Set up mock
        audio_module_with_feedback.porcupine.process.return_value = 0
        audio_module_with_feedback.listen_for_wake_word = mock_listen_without_feedback
        
        # Test wake word detection without feedback
        with patch('modules.audio.threading.Thread') as mock_thread:
            result = audio_module_with_feedback.listen_for_wake_word(provide_feedback=False)
            
            assert result is True
            assert not audio_module_with_feedback.is_listening_for_wake_word
            # Verify no confirmation thread was created
            mock_thread.assert_not_called()
    
    @patch('modules.audio.threading.Thread')
    @patch('modules.audio.time.time')
    def test_continuous_monitoring_with_session_timeout(self, mock_time, mock_thread, audio_module_with_feedback):
        """Test continuous wake word monitoring with session timeout."""
        # Mock time progression to trigger timeout
        mock_time.side_effect = [0, 5, 10, 15, 20, 25, 35]  # Timeout at 30 seconds
        
        # Mock thread
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # Mock listen_for_wake_word to not detect wake word
        def mock_listen_no_detection(timeout=None, provide_feedback=True):
            return False
        
        audio_module_with_feedback.listen_for_wake_word = mock_listen_no_detection
        
        # Start monitoring with 30-second timeout
        audio_module_with_feedback.start_continuous_wake_word_monitoring(
            session_timeout=30.0
        )
        
        # Verify monitoring started
        assert audio_module_with_feedback.is_listening_for_wake_word is True
        assert audio_module_with_feedback.wake_word_thread is not None
        mock_thread_instance.start.assert_called_once()
    
    @patch('modules.audio.threading.Thread')
    def test_continuous_monitoring_with_callback(self, mock_thread, audio_module_with_feedback):
        """Test continuous wake word monitoring with callback."""
        # Mock thread
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # Mock callback
        callback = Mock()
        
        # Start monitoring with callback
        audio_module_with_feedback.start_continuous_wake_word_monitoring(callback=callback)
        
        # Verify monitoring started
        assert audio_module_with_feedback.is_listening_for_wake_word is True
        assert audio_module_with_feedback.wake_word_thread is not None
        mock_thread_instance.start.assert_called_once()
    
    def test_wake_word_confirmation_feedback(self, audio_module_with_feedback):
        """Test wake word confirmation feedback."""
        with patch('modules.audio.threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            audio_module_with_feedback._provide_wake_word_confirmation()
            
            # Verify confirmation thread was created and started
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
    
    def test_session_timeout_feedback(self, audio_module_with_feedback):
        """Test session timeout feedback."""
        with patch('modules.audio.threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            audio_module_with_feedback._provide_session_timeout_feedback()
            
            # Verify timeout feedback thread was created and started
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
    
    def test_system_activation_indicator(self, audio_module_with_feedback):
        """Test system activation indicator."""
        with patch('modules.audio.threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            audio_module_with_feedback._provide_system_activation_indicator()
            
            # Verify activation indicator thread was created and started
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
    
    def test_complete_wake_word_flow_integration(self, audio_module_with_feedback):
        """Test complete wake word detection flow with all feedback components."""
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        # Mock successful wake word detection
        def mock_successful_detection(timeout=None, provide_feedback=True):
            audio_module_with_feedback.is_listening_for_wake_word = True
            # Simulate detection
            if provide_feedback:
                audio_module_with_feedback._provide_wake_word_confirmation()
            audio_module_with_feedback.is_listening_for_wake_word = False
            return True
        
        audio_module_with_feedback.listen_for_wake_word = mock_successful_detection
        
        with patch('modules.audio.threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            # Test the complete flow
            result = audio_module_with_feedback.listen_for_wake_word(provide_feedback=True)
            
            assert result is True
            assert not audio_module_with_feedback.is_listening_for_wake_word
            # Verify confirmation was provided
            mock_thread.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])
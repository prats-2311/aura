# tests/conftest.py
"""
Pytest configuration and shared fixtures for AURA tests.
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Import test fixtures
from tests.fixtures.sample_data import SampleData, MockDataGenerator


@pytest.fixture(scope="session")
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_audio_file(temp_directory):
    """Create a temporary audio file for testing."""
    from pydub import AudioSegment
    
    # Create sample audio data
    audio_data = MockDataGenerator.create_mock_audio_data(duration=1.0)
    
    # Create audio segment
    audio_segment = AudioSegment(
        audio_data.tobytes(),
        frame_rate=16000,
        sample_width=2,
        channels=1
    )
    
    # Save to temporary file
    audio_path = os.path.join(temp_directory, "test_audio.wav")
    audio_segment.export(audio_path, format="wav")
    
    yield audio_path
    
    # Cleanup is handled by temp_directory fixture


@pytest.fixture
def sample_sound_files(temp_directory):
    """Create temporary sound files for testing."""
    sound_files = {}
    
    # Create simple WAV files for each sound type
    for sound_name in ['success', 'failure', 'thinking']:
        sound_path = os.path.join(temp_directory, f"{sound_name}.wav")
        
        # Create minimal WAV file
        with open(sound_path, 'wb') as f:
            # Write minimal WAV header (44 bytes) + some data
            f.write(b'RIFF')
            f.write((100).to_bytes(4, 'little'))  # File size
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))  # Format chunk size
            f.write((1).to_bytes(2, 'little'))   # Audio format (PCM)
            f.write((1).to_bytes(2, 'little'))   # Number of channels
            f.write((44100).to_bytes(4, 'little'))  # Sample rate
            f.write((88200).to_bytes(4, 'little'))  # Byte rate
            f.write((2).to_bytes(2, 'little'))   # Block align
            f.write((16).to_bytes(2, 'little'))  # Bits per sample
            f.write(b'data')
            f.write((64).to_bytes(4, 'little'))  # Data chunk size
            f.write(b'\x00' * 64)  # Audio data
        
        sound_files[sound_name] = sound_path
    
    yield sound_files


@pytest.fixture
def mock_config():
    """Mock configuration values for testing."""
    config_values = {
        'VISION_API_BASE': 'http://localhost:1234/v1',
        'VISION_MODEL': 'test-vision-model',
        'VISION_PROMPT': 'Analyze this screen image',
        'FORM_VISION_PROMPT': 'Analyze this form',
        'VISION_API_TIMEOUT': 30,
        'SCREENSHOT_QUALITY': 85,
        'MAX_SCREENSHOT_SIZE': 1920,
        'REASONING_API_BASE': 'http://localhost:8080/v1',
        'REASONING_API_KEY': 'test-api-key',
        'REASONING_MODEL': 'test-reasoning-model',
        'REASONING_META_PROMPT': 'Generate action plan',
        'REASONING_API_TIMEOUT': 30,
        'AUDIO_SAMPLE_RATE': 16000,
        'AUDIO_CHUNK_SIZE': 1024,
        'TTS_SPEED': 1.0,
        'TTS_VOLUME': 0.8,
        'AUDIO_API_TIMEOUT': 30,
        'PORCUPINE_API_KEY': 'test-porcupine-key',
        'WAKE_WORD': 'computer',
        'MOUSE_MOVE_DURATION': 0.25,
        'TYPE_INTERVAL': 0.05,
        'SCROLL_AMOUNT': 100,
        'SOUNDS': {
            'success': '/tmp/success.wav',
            'failure': '/tmp/failure.wav',
            'thinking': '/tmp/thinking.wav'
        }
    }
    
    with patch.multiple('config', **config_values):
        yield config_values


@pytest.fixture
def mock_pygame():
    """Mock pygame for testing."""
    with patch('modules.feedback.pygame.mixer') as mock_mixer:
        mock_mixer.pre_init.return_value = None
        mock_mixer.init.return_value = None
        mock_mixer.quit.return_value = None
        mock_mixer.music.set_volume.return_value = None
        
        # Mock Sound class
        mock_sound = Mock()
        mock_sound.play.return_value = None
        mock_mixer.Sound.return_value = mock_sound
        
        yield mock_mixer


@pytest.fixture
def mock_pyautogui():
    """Mock PyAutoGUI for testing."""
    with patch('modules.automation.pyautogui') as mock_gui:
        mock_gui.size.return_value = (1920, 1080)
        mock_gui.position.return_value = Mock(x=100, y=100)
        mock_gui.moveTo.return_value = None
        mock_gui.click.return_value = None
        mock_gui.doubleClick.return_value = None
        mock_gui.typewrite.return_value = None
        mock_gui.scroll.return_value = None
        mock_gui.hscroll.return_value = None
        mock_gui.hotkey.return_value = None
        mock_gui.press.return_value = None
        mock_gui.FAILSAFE = True
        mock_gui.PAUSE = 0.1
        
        yield mock_gui


@pytest.fixture
def mock_mss():
    """Mock MSS for screen capture testing."""
    with patch('mss.mss') as mock_mss_class:
        mock_sct = Mock()
        mock_sct.monitors = [
            {},  # Index 0 is all monitors
            {"width": 1920, "height": 1080, "left": 0, "top": 0}
        ]
        
        # Mock screenshot
        mock_screenshot = Mock()
        mock_screenshot.size = (1920, 1080)
        mock_screenshot.bgra = MockDataGenerator.create_mock_screenshot_data()
        mock_sct.grab.return_value = mock_screenshot
        mock_sct.close.return_value = None
        
        mock_mss_class.return_value = mock_sct
        yield mock_sct


@pytest.fixture
def mock_whisper():
    """Mock Whisper for speech recognition testing."""
    with patch('modules.audio.whisper.load_model') as mock_load:
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "This is a test transcription",
            "segments": [
                {"avg_logprob": -0.5, "text": "This is a test transcription"}
            ]
        }
        mock_load.return_value = mock_model
        yield mock_model


@pytest.fixture
def mock_pyttsx3():
    """Mock pyttsx3 for TTS testing."""
    with patch('modules.audio.pyttsx3.init') as mock_init:
        mock_engine = Mock()
        mock_engine.getProperty.return_value = []
        mock_engine.setProperty.return_value = None
        mock_engine.say.return_value = None
        mock_engine.runAndWait.return_value = None
        mock_engine.stop.return_value = None
        mock_init.return_value = mock_engine
        yield mock_engine


@pytest.fixture
def mock_porcupine():
    """Mock Porcupine for wake word detection testing."""
    with patch('modules.audio.pvporcupine.create') as mock_create:
        mock_porcupine = Mock()
        mock_porcupine.sample_rate = 16000
        mock_porcupine.frame_length = 512
        mock_porcupine.process.return_value = -1  # No wake word detected by default
        mock_porcupine.delete.return_value = None
        mock_create.return_value = mock_porcupine
        yield mock_porcupine


@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice for audio I/O testing."""
    with patch('modules.audio.sd') as mock_sd:
        mock_sd.query_devices.return_value = [
            {'name': 'Test Microphone', 'max_input_channels': 2},
            {'name': 'Test Speaker', 'max_input_channels': 0}
        ]
        mock_sd.check_input_settings.return_value = None
        mock_sd.rec.return_value = MockDataGenerator.create_mock_audio_data().reshape(-1, 1)
        mock_sd.wait.return_value = True
        mock_sd.stop.return_value = None
        
        # Mock InputStream context manager
        mock_stream = Mock()
        mock_sd.InputStream.return_value.__enter__.return_value = mock_stream
        mock_sd.InputStream.return_value.__exit__.return_value = None
        
        yield mock_sd


@pytest.fixture
def mock_requests():
    """Mock requests for API testing."""
    with patch('modules.vision.requests.post') as mock_post:
        # Default successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = SampleData.get_sample_api_responses()["vision_success"]
        mock_response.text = "Success"
        mock_response.raise_for_status.return_value = None
        mock_response.elapsed.total_seconds.return_value = 1.5
        mock_post.return_value = mock_response
        
        yield mock_post


@pytest.fixture
def sample_data():
    """Provide access to sample data."""
    return SampleData


@pytest.fixture
def mock_data_generator():
    """Provide access to mock data generator."""
    return MockDataGenerator


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to unit test files
        if "test_comprehensive_unit_coverage" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration test files
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.nodeid for keyword in ["test_complete_", "test_end_to_end", "test_lifecycle"]):
            item.add_marker(pytest.mark.slow)
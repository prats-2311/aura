# modules/audio.py
"""
Audio Module for AURA

Handles all audio input/output including:
- Wake word detection using Picovoice Porcupine
- Speech-to-text using OpenAI Whisper
- Text-to-speech for user feedback
"""

import logging
import tempfile
import os
import time
from typing import Optional, Dict, Any
import sounddevice as sd
import numpy as np
import whisper
import pyttsx3
from pydub import AudioSegment
from pydub.playback import play
import threading
import queue

from config import (
    AUDIO_SAMPLE_RATE,
    AUDIO_CHUNK_SIZE,
    TTS_SPEED,
    TTS_VOLUME,
    AUDIO_API_TIMEOUT
)

logger = logging.getLogger(__name__)


class AudioModule:
    """
    Audio Module for AURA
    
    Handles all audio input/output operations including:
    - Speech-to-text conversion using OpenAI Whisper
    - Text-to-speech output using system TTS
    - Audio input validation and preprocessing
    """
    
    def __init__(self):
        """Initialize the AudioModule with required components."""
        self.whisper_model = None
        self.tts_engine = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        
        # Initialize components
        self._initialize_whisper()
        self._initialize_tts()
        
        logger.info("AudioModule initialized successfully")
    
    def _initialize_whisper(self) -> None:
        """Initialize the Whisper model for speech-to-text."""
        try:
            logger.info("Loading Whisper model...")
            # Use base model for good balance of speed and accuracy
            self.whisper_model = whisper.load_model("base")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}")
            raise
    
    def _initialize_tts(self) -> None:
        """Initialize the text-to-speech engine."""
        try:
            logger.info("Initializing TTS engine...")
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS settings
            self.tts_engine.setProperty('rate', int(200 * TTS_SPEED))
            self.tts_engine.setProperty('volume', TTS_VOLUME)
            
            # Try to set a good voice (prefer female voice if available)
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Look for a female voice first, fallback to first available
                female_voice = next((v for v in voices if 'female' in v.name.lower() or 'zira' in v.name.lower()), None)
                selected_voice = female_voice if female_voice else voices[0]
                self.tts_engine.setProperty('voice', selected_voice.id)
                logger.info(f"Selected TTS voice: {selected_voice.name}")
            
            logger.info("TTS engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            raise
    
    def speech_to_text(self, duration: float = 5.0, silence_threshold: float = 0.01) -> str:
        """
        Convert speech to text using Whisper.
        
        Args:
            duration: Maximum recording duration in seconds
            silence_threshold: Threshold for detecting silence (0.0 to 1.0)
            
        Returns:
            Transcribed text from speech
            
        Raises:
            RuntimeError: If speech recognition fails
        """
        try:
            logger.info(f"Starting speech recording for {duration} seconds...")
            
            # Record audio
            audio_data = self._record_audio(duration, silence_threshold)
            
            if audio_data is None or len(audio_data) == 0:
                logger.warning("No audio data recorded")
                return ""
            
            # Save audio to temporary file for Whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Convert numpy array to audio file
                audio_segment = AudioSegment(
                    audio_data.tobytes(),
                    frame_rate=AUDIO_SAMPLE_RATE,
                    sample_width=audio_data.dtype.itemsize,
                    channels=1
                )
                audio_segment.export(temp_path, format="wav")
            
            try:
                # Transcribe using Whisper
                logger.info("Transcribing audio with Whisper...")
                result = self.whisper_model.transcribe(temp_path)
                text = result["text"].strip()
                
                logger.info(f"Transcription result: '{text}'")
                return text
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"Speech-to-text conversion failed: {e}")
            raise RuntimeError(f"Speech recognition failed: {e}")
    
    def _record_audio(self, duration: float, silence_threshold: float) -> Optional[np.ndarray]:
        """
        Record audio from the default microphone.
        
        Args:
            duration: Maximum recording duration in seconds
            silence_threshold: Threshold for detecting silence
            
        Returns:
            Recorded audio data as numpy array
        """
        try:
            logger.debug("Starting audio recording...")
            
            # Calculate number of frames
            frames = int(duration * AUDIO_SAMPLE_RATE)
            
            # Record audio
            audio_data = sd.rec(
                frames,
                samplerate=AUDIO_SAMPLE_RATE,
                channels=1,
                dtype=np.float32
            )
            
            # Wait for recording to complete or detect silence
            start_time = time.time()
            silence_start = None
            silence_duration_threshold = 2.0  # Stop after 2 seconds of silence
            
            while not sd.wait():
                current_time = time.time()
                elapsed = current_time - start_time
                
                if elapsed >= duration:
                    break
                
                # Check for silence (simplified approach)
                if len(audio_data) > 0:
                    recent_audio = audio_data[-int(AUDIO_SAMPLE_RATE * 0.1):]  # Last 0.1 seconds
                    if len(recent_audio) > 0:
                        volume = np.sqrt(np.mean(recent_audio ** 2))
                        
                        if volume < silence_threshold:
                            if silence_start is None:
                                silence_start = current_time
                            elif current_time - silence_start > silence_duration_threshold:
                                logger.debug("Silence detected, stopping recording")
                                break
                        else:
                            silence_start = None
                
                time.sleep(0.1)
            
            # Stop recording
            sd.stop()
            
            # Normalize audio data
            if len(audio_data) > 0:
                audio_data = audio_data.flatten()
                # Convert to int16 for better compatibility
                audio_data = (audio_data * 32767).astype(np.int16)
                
                logger.debug(f"Recorded {len(audio_data)} audio samples")
                return audio_data
            
            return None
            
        except Exception as e:
            logger.error(f"Audio recording failed: {e}")
            raise
    
    def text_to_speech(self, text: str) -> None:
        """
        Convert text to speech using system TTS.
        
        Args:
            text: Text to convert to speech
            
        Raises:
            RuntimeError: If text-to-speech conversion fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for TTS")
            return
        
        try:
            logger.info(f"Converting text to speech: '{text[:50]}...'")
            
            # Use threading to avoid blocking
            def speak_text():
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    logger.error(f"TTS playback failed: {e}")
            
            # Run TTS in separate thread
            tts_thread = threading.Thread(target=speak_text, daemon=True)
            tts_thread.start()
            
            # Wait for completion with timeout
            tts_thread.join(timeout=AUDIO_API_TIMEOUT)
            
            if tts_thread.is_alive():
                logger.warning("TTS operation timed out")
                raise RuntimeError("Text-to-speech operation timed out")
            
            logger.info("Text-to-speech completed successfully")
            
        except Exception as e:
            logger.error(f"Text-to-speech conversion failed: {e}")
            raise RuntimeError(f"Text-to-speech failed: {e}")
    
    def validate_audio_input(self) -> Dict[str, Any]:
        """
        Validate audio input capabilities and settings.
        
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "microphone_available": False,
            "sample_rate_supported": False,
            "whisper_model_loaded": False,
            "tts_engine_available": False,
            "errors": []
        }
        
        try:
            # Check microphone availability
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            validation_result["microphone_available"] = len(input_devices) > 0
            
            if not validation_result["microphone_available"]:
                validation_result["errors"].append("No microphone devices found")
            
            # Check sample rate support
            try:
                sd.check_input_settings(channels=1, samplerate=AUDIO_SAMPLE_RATE)
                validation_result["sample_rate_supported"] = True
            except Exception as e:
                validation_result["errors"].append(f"Sample rate {AUDIO_SAMPLE_RATE} not supported: {e}")
            
            # Check Whisper model
            validation_result["whisper_model_loaded"] = self.whisper_model is not None
            if not validation_result["whisper_model_loaded"]:
                validation_result["errors"].append("Whisper model not loaded")
            
            # Check TTS engine
            validation_result["tts_engine_available"] = self.tts_engine is not None
            if not validation_result["tts_engine_available"]:
                validation_result["errors"].append("TTS engine not available")
            
        except Exception as e:
            validation_result["errors"].append(f"Audio validation failed: {e}")
        
        return validation_result
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        try:
            if self.tts_engine:
                self.tts_engine.stop()
            
            # Stop any ongoing recordings
            sd.stop()
            
            logger.info("AudioModule cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during AudioModule cleanup: {e}")
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
import pvporcupine

from config import (
    AUDIO_SAMPLE_RATE,
    AUDIO_CHUNK_SIZE,
    AUDIO_RECORDING_DURATION,
    AUDIO_SILENCE_THRESHOLD,
    TTS_SPEED,
    TTS_VOLUME,
    AUDIO_API_TIMEOUT,
    PORCUPINE_API_KEY,
    WAKE_WORD
)
from .error_handler import (
    global_error_handler,
    with_error_handling,
    ErrorCategory,
    ErrorSeverity
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
        self.porcupine = None
        self.is_recording = False
        self.is_listening_for_wake_word = False
        self.audio_queue = queue.Queue()
        self.wake_word_thread = None
        
        # Initialize components
        self._initialize_whisper()
        self._initialize_tts()
        self._initialize_porcupine()
        
        logger.info("AudioModule initialized successfully")
    
    def _initialize_whisper(self) -> None:
        """Initialize the Whisper model for speech-to-text with error handling."""
        try:
            logger.info("Loading Whisper model...")
            # Use small model for better sensitivity to quiet speech
            self.whisper_model = whisper.load_model("small")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="audio",
                function="_initialize_whisper",
                category=ErrorCategory.CONFIGURATION_ERROR,
                severity=ErrorSeverity.CRITICAL,
                user_message="Failed to load speech recognition model. Please check your installation."
            )
            logger.error(f"Failed to initialize Whisper model: {error_info.message}")
            raise Exception(f"Whisper initialization failed: {error_info.user_message}")
    
    def _initialize_tts(self) -> None:
        """Initialize the text-to-speech engine with fallback options."""
        try:
            logger.info("Initializing TTS engine...")
            
            # Try different TTS drivers in order of preference
            # Skip nsss on macOS if it's causing AppKit issues
            import platform
            if platform.system() == 'Darwin':
                tts_drivers = ['espeak', 'sapi5']  # Skip nsss for now
            else:
                tts_drivers = ['nsss', 'sapi5', 'espeak']  # macOS, Windows, Linux
            
            for driver in tts_drivers:
                try:
                    logger.debug(f"Trying TTS driver: {driver}")
                    self.tts_engine = pyttsx3.init(driver)
                    break
                except Exception as e:
                    logger.debug(f"TTS driver {driver} failed: {e}")
                    continue
            
            # If no specific driver worked, try default
            if not self.tts_engine:
                logger.debug("Trying default TTS driver")
                self.tts_engine = pyttsx3.init()
            
            if not self.tts_engine:
                raise Exception("No TTS engine could be initialized")
            
            # Configure TTS settings
            self.tts_engine.setProperty('rate', int(200 * TTS_SPEED))
            self.tts_engine.setProperty('volume', TTS_VOLUME)
            
            # Try to set a good voice (prefer female voice if available)
            try:
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Look for a female voice first, fallback to first available
                    female_voice = next((v for v in voices if 'female' in v.name.lower() or 'zira' in v.name.lower()), None)
                    selected_voice = female_voice if female_voice else voices[0]
                    self.tts_engine.setProperty('voice', selected_voice.id)
                    logger.info(f"Selected TTS voice: {selected_voice.name}")
                else:
                    logger.warning("No TTS voices available")
            except Exception as e:
                logger.warning(f"Could not configure TTS voice: {e}")
            
            logger.info("TTS engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            logger.warning("TTS functionality will not be available")
            self.tts_engine = None
    
    def _initialize_porcupine(self) -> None:
        """Initialize the Porcupine wake word detection engine."""
        try:
            logger.info("Initializing Porcupine wake word detection...")
            
            if not PORCUPINE_API_KEY or PORCUPINE_API_KEY == "your_porcupine_api_key_here":
                logger.warning("Porcupine API key not configured. Wake word detection will not be available.")
                return
            
            # Initialize Porcupine with the specified wake word
            self.porcupine = pvporcupine.create(
                access_key=PORCUPINE_API_KEY,
                keywords=[WAKE_WORD]
            )
            
            logger.info(f"Porcupine initialized successfully with wake word: '{WAKE_WORD}'")
            logger.info(f"Expected sample rate: {self.porcupine.sample_rate} Hz")
            logger.info(f"Expected frame length: {self.porcupine.frame_length} samples")
            
        except Exception as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            logger.warning("Wake word detection will not be available")
            self.porcupine = None
    
    @with_error_handling(
        category=ErrorCategory.HARDWARE_ERROR,
        severity=ErrorSeverity.MEDIUM,
        max_retries=2,
        user_message="I'm having trouble hearing you. Please check your microphone and try again."
    )
    def speech_to_text(self, duration: float = None, silence_threshold: float = None) -> str:
        """
        Convert speech to text using Whisper with comprehensive error handling.
        
        Args:
            duration: Maximum recording duration in seconds
            silence_threshold: Threshold for detecting silence (0.0 to 1.0)
            
        Returns:
            Transcribed text from speech
            
        Raises:
            RuntimeError: If speech recognition fails after retries
        """
        try:
            # Use configuration defaults if not specified
            if duration is None:
                duration = AUDIO_RECORDING_DURATION
            if silence_threshold is None:
                silence_threshold = AUDIO_SILENCE_THRESHOLD
                
            # Validate parameters
            if duration <= 0 or duration > 60:
                raise ValueError("Duration must be between 0 and 60 seconds")
            if not 0.0 <= silence_threshold <= 1.0:
                raise ValueError("Silence threshold must be between 0.0 and 1.0")
            
            # Check if Whisper model is loaded
            if not self.whisper_model:
                error_info = global_error_handler.handle_error(
                    error=Exception("Whisper model not initialized"),
                    module="audio",
                    function="speech_to_text",
                    category=ErrorCategory.CONFIGURATION_ERROR,
                    context={"duration": duration, "silence_threshold": silence_threshold}
                )
                raise RuntimeError(f"Speech recognition not available: {error_info.user_message}")
            
            logger.info(f"Starting speech recording for {duration} seconds...")
            
            # Record audio with error handling
            try:
                audio_data = self._record_audio(duration, silence_threshold)
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="audio",
                    function="speech_to_text",
                    category=ErrorCategory.HARDWARE_ERROR,
                    context={"duration": duration, "silence_threshold": silence_threshold}
                )
                raise RuntimeError(f"Audio recording failed: {error_info.user_message}")
            
            if audio_data is None or len(audio_data) == 0:
                logger.warning("No audio data recorded")
                return ""
            
            # Validate audio data
            if len(audio_data) < AUDIO_SAMPLE_RATE * 0.1:  # Less than 0.1 seconds
                logger.warning("Audio recording too short for transcription")
                return ""
            
            # Save audio to temporary file for Whisper
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_path = temp_file.name
                
                # Convert numpy array to audio file with error handling
                try:
                    # Create audio segment from raw audio data
                    audio_segment = AudioSegment(
                        audio_data.tobytes(),
                        frame_rate=AUDIO_SAMPLE_RATE,
                        sample_width=audio_data.dtype.itemsize,
                        channels=1
                    )
                    
                    # Apply some audio processing to improve transcription quality
                    # Normalize volume
                    audio_segment = audio_segment.normalize()
                    
                    # Apply a slight high-pass filter to reduce low-frequency noise
                    # This is a simple approach - more sophisticated filtering could be added
                    if len(audio_segment) > 1000:  # Only if we have enough audio
                        # Simple high-pass by reducing low frequencies
                        audio_segment = audio_segment.high_pass_filter(80)
                    
                    # Export to WAV file
                    audio_segment.export(temp_path, format="wav")
                    
                    # Log audio file info for debugging
                    file_size = os.path.getsize(temp_path)
                    duration_ms = len(audio_segment)
                    logger.info(f"Created audio file for Whisper: {temp_path}")
                    logger.info(f"  File size: {file_size} bytes")
                    logger.info(f"  Duration: {duration_ms}ms ({duration_ms/1000:.2f}s)")
                    logger.info(f"  Sample rate: {audio_segment.frame_rate}Hz")
                    logger.info(f"  Channels: {audio_segment.channels}")
                    
                    # Save a copy for debugging (optional)
                    debug_path = "debug_audio.wav"
                    try:
                        audio_segment.export(debug_path, format="wav")
                        logger.info(f"Debug audio saved to: {debug_path}")
                    except Exception as e:
                        logger.debug(f"Could not save debug audio: {e}")
                    
                    # Check if file is too short for transcription
                    if duration_ms < 500:  # Less than 0.5 seconds
                        logger.warning(f"Audio file is very short ({duration_ms}ms). This may cause transcription issues.")
                    elif duration_ms < 1000:  # Less than 1 second
                        logger.info(f"Audio file is short ({duration_ms}ms). Transcription may be less accurate.")
                    
                except Exception as e:
                    error_info = global_error_handler.handle_error(
                        error=e,
                        module="audio",
                        function="speech_to_text",
                        category=ErrorCategory.PROCESSING_ERROR,
                        context={"audio_length": len(audio_data), "sample_rate": AUDIO_SAMPLE_RATE}
                    )
                    raise RuntimeError(f"Audio processing failed: {error_info.user_message}")
                
                # Transcribe using Whisper with timeout
                try:
                    logger.info("Transcribing audio with Whisper...")
                    
                    # Use threading to implement timeout for Whisper
                    result_queue = queue.Queue()
                    error_queue = queue.Queue()
                    
                    def transcribe_worker():
                        try:
                            # Add more detailed logging for Whisper transcription
                            logger.info(f"Starting Whisper transcription of {temp_path}")
                            
                            # First, try a simple transcription to see if Whisper can process the file
                            try:
                                # Load the audio file to check if it's valid
                                import librosa
                                audio_data_check, sr = librosa.load(temp_path, sr=16000)
                                logger.info(f"Audio file loaded successfully: {len(audio_data_check)} samples at {sr}Hz")
                                
                                # Check audio statistics
                                audio_rms = np.sqrt(np.mean(audio_data_check ** 2))
                                audio_max = np.max(np.abs(audio_data_check))
                                logger.info(f"Audio stats - RMS: {audio_rms:.4f}, Max: {audio_max:.4f}")
                                
                                if audio_rms < 0.001:
                                    logger.warning("Audio file appears to be silent or very quiet")
                                
                            except ImportError:
                                logger.debug("librosa not available for audio validation")
                            except Exception as e:
                                logger.warning(f"Could not validate audio file: {e}")
                            
                            # Try different approaches to transcription
                            logger.info("Running Whisper transcription...")
                            
                            # First try with minimal parameters
                            try:
                                result = self.whisper_model.transcribe(
                                    temp_path,
                                    language="en",
                                    no_speech_threshold=0.1,
                                    temperature=0.0,
                                    fp16=False
                                )
                                logger.info("Whisper transcription with minimal parameters completed")
                            except Exception as e:
                                logger.warning(f"Minimal transcription failed: {e}, trying with default parameters")
                                # Fallback to default parameters
                                result = self.whisper_model.transcribe(temp_path)
                                logger.info("Whisper transcription with default parameters completed")
                            
                            logger.info(f"Whisper transcription completed")
                            
                            # Log detailed result information
                            if isinstance(result, dict):
                                text = result.get("text", "").strip()
                                language = result.get("language", "unknown")
                                segments = result.get("segments", [])
                                
                                logger.info(f"Whisper result details:")
                                logger.info(f"  Text: '{text}'")
                                logger.info(f"  Language: {language}")
                                logger.info(f"  Segments: {len(segments)}")
                                
                                if segments:
                                    for i, segment in enumerate(segments[:3]):  # Log first 3 segments
                                        seg_text = segment.get("text", "").strip()
                                        seg_start = segment.get("start", 0)
                                        seg_end = segment.get("end", 0)
                                        seg_prob = segment.get("avg_logprob", 0)
                                        logger.info(f"    Segment {i+1}: '{seg_text}' ({seg_start:.2f}-{seg_end:.2f}s, prob: {seg_prob:.3f})")
                                
                                # Check if result indicates no speech
                                if not text and segments:
                                    logger.warning("Whisper detected segments but no text - possible silence or unclear speech")
                                elif not text:
                                    logger.warning("Whisper returned no text and no segments - likely silence")
                            
                            result_queue.put(result)
                            
                        except Exception as e:
                            logger.error(f"Whisper transcription error: {e}")
                            error_queue.put(e)
                    
                    transcribe_thread = threading.Thread(target=transcribe_worker, daemon=True)
                    transcribe_thread.start()
                    
                    # Wait for result with timeout
                    transcribe_thread.join(timeout=AUDIO_API_TIMEOUT)
                    
                    if transcribe_thread.is_alive():
                        error_info = global_error_handler.handle_error(
                            error=Exception("Whisper transcription timeout"),
                            module="audio",
                            function="speech_to_text",
                            category=ErrorCategory.TIMEOUT_ERROR,
                            context={"timeout": AUDIO_API_TIMEOUT}
                        )
                        raise RuntimeError(f"Speech recognition timed out: {error_info.user_message}")
                    
                    # Check for errors
                    if not error_queue.empty():
                        transcribe_error = error_queue.get()
                        error_info = global_error_handler.handle_error(
                            error=transcribe_error,
                            module="audio",
                            function="speech_to_text",
                            category=ErrorCategory.PROCESSING_ERROR,
                            context={"temp_file": temp_path}
                        )
                        raise RuntimeError(f"Speech transcription failed: {error_info.user_message}")
                    
                    # Get result
                    if result_queue.empty():
                        error_info = global_error_handler.handle_error(
                            error=Exception("No transcription result"),
                            module="audio",
                            function="speech_to_text",
                            category=ErrorCategory.PROCESSING_ERROR
                        )
                        raise RuntimeError(f"No transcription result: {error_info.user_message}")
                    
                    result = result_queue.get()
                    
                    # Validate result
                    if not isinstance(result, dict) or "text" not in result:
                        error_info = global_error_handler.handle_error(
                            error=Exception("Invalid transcription result format"),
                            module="audio",
                            function="speech_to_text",
                            category=ErrorCategory.PROCESSING_ERROR,
                            context={"result_type": type(result).__name__}
                        )
                        raise RuntimeError(f"Invalid transcription result: {error_info.user_message}")
                    
                    text = result["text"].strip()
                    
                    # Log confidence if available
                    if "segments" in result and result["segments"]:
                        avg_confidence = sum(seg.get("avg_logprob", 0) for seg in result["segments"]) / len(result["segments"])
                        logger.debug(f"Average transcription confidence: {avg_confidence:.3f}")
                    
                    logger.info(f"Transcription result: '{text}'")
                    return text
                    
                except Exception as e:
                    if "Speech recognition" in str(e) or "Speech transcription" in str(e):
                        raise  # Re-raise already handled errors
                    
                    error_info = global_error_handler.handle_error(
                        error=e,
                        module="audio",
                        function="speech_to_text",
                        category=ErrorCategory.PROCESSING_ERROR,
                        context={"temp_file": temp_path}
                    )
                    raise RuntimeError(f"Speech transcription failed: {error_info.user_message}")
                
            finally:
                # Clean up temporary file
                if temp_path:
                    try:
                        os.unlink(temp_path)
                        logger.debug(f"Cleaned up temporary file: {temp_path}")
                    except OSError as e:
                        logger.warning(f"Failed to clean up temporary file {temp_path}: {e}")
                    
        except Exception as e:
            # Re-raise with additional context if not already handled
            if "Speech recognition failed" not in str(e):
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="audio",
                    function="speech_to_text",
                    category=ErrorCategory.PROCESSING_ERROR,
                    context={"duration": duration, "silence_threshold": silence_threshold}
                )
                raise RuntimeError(f"Speech recognition failed: {error_info.user_message}")
            raise
    
    def _record_audio(self, duration: float, silence_threshold: float) -> Optional[np.ndarray]:
        """
        Record audio from the default microphone with improved error handling and debugging.
        
        Args:
            duration: Maximum recording duration in seconds
            silence_threshold: Threshold for detecting silence
            
        Returns:
            Recorded audio data as numpy array
        """
        try:
            logger.debug(f"Starting audio recording for {duration}s with silence threshold {silence_threshold}")
            
            # Check audio device availability
            try:
                devices = sd.query_devices()
                default_input = sd.query_devices(kind='input')
                logger.debug(f"Using input device: {default_input['name']} (index: {default_input.get('index', 'default')})")
            except Exception as e:
                logger.warning(f"Could not query audio devices: {e}")
            
            # Calculate number of frames
            frames = int(duration * AUDIO_SAMPLE_RATE)
            logger.debug(f"Recording {frames} frames at {AUDIO_SAMPLE_RATE}Hz")
            
            # Use simple synchronous recording for better reliability
            logger.info("Starting synchronous audio recording...")
            
            # Record audio synchronously (simpler and more reliable)
            audio_data = sd.rec(
                frames,
                samplerate=AUDIO_SAMPLE_RATE,
                channels=1,
                dtype=np.float32
            )
            
            # Wait for recording to complete
            sd.wait()
            
            # Flatten the audio data
            audio_data = audio_data.flatten()
            
            if len(audio_data) == 0:
                logger.warning("Recorded audio data is empty")
                return None
            
            # Calculate audio statistics for debugging
            duration_recorded = len(audio_data) / AUDIO_SAMPLE_RATE
            volume_rms = np.sqrt(np.mean(audio_data ** 2))
            volume_max = np.max(np.abs(audio_data))
            
            logger.info(f"Audio recording completed:")
            logger.info(f"  Duration: {duration_recorded:.2f}s")
            logger.info(f"  Samples: {len(audio_data)}")
            logger.info(f"  RMS volume: {volume_rms:.4f}")
            logger.info(f"  Max volume: {volume_max:.4f}")
            
            # Check if audio is too quiet
            if volume_rms < 0.001:
                logger.warning(f"Recorded audio is very quiet (RMS: {volume_rms:.4f}). Check microphone levels.")
            elif volume_rms < 0.01:
                logger.info(f"Audio is quiet but may be usable (RMS: {volume_rms:.4f})")
            else:
                logger.info(f"Good audio level detected (RMS: {volume_rms:.4f})")
            
            # Check if audio is too short
            if duration_recorded < 0.5:
                logger.warning(f"Recorded audio is very short ({duration_recorded:.2f}s). May not be sufficient for transcription.")
            
            # Apply gain to boost quiet audio (more aggressive than before)
            if volume_max > 0:
                # Target 30% of max volume, with higher max gain for very quiet audio
                target_level = 0.3
                gain_factor = min(target_level / volume_max, 50.0)  # Max 50x gain for very quiet audio
                
                if gain_factor > 1.0:
                    logger.info(f"Applying gain factor: {gain_factor:.2f} (original max volume: {volume_max:.4f})")
                    audio_data = audio_data * gain_factor
                    
                    # Recalculate stats after gain
                    volume_rms_after = np.sqrt(np.mean(audio_data ** 2))
                    volume_max_after = np.max(np.abs(audio_data))
                    logger.info(f"After gain - RMS: {volume_rms_after:.4f}, Max: {volume_max_after:.4f}")
            
            # Convert to int16 for better compatibility with Whisper
            audio_data = np.clip(audio_data * 32767, -32767, 32767).astype(np.int16)
            
            logger.info(f"Successfully recorded and processed {len(audio_data)} audio samples")
            return audio_data
            
        except Exception as e:
            logger.error(f"Audio recording failed: {e}")
            raise
    
    def listen_for_wake_word(self, timeout: Optional[float] = None, provide_feedback: bool = True) -> bool:
        """
        Listen for the configured wake word using Porcupine.
        
        Args:
            timeout: Maximum time to listen in seconds (None for indefinite)
            provide_feedback: Whether to provide audio confirmation when wake word is detected
            
        Returns:
            True if wake word was detected, False if timeout or error
            
        Raises:
            RuntimeError: If Porcupine is not initialized or audio input fails
        """
        if not self.porcupine:
            raise RuntimeError("Porcupine wake word detection not initialized")
        
        try:
            logger.info(f"Listening for wake word '{WAKE_WORD}'...")
            self.is_listening_for_wake_word = True
            
            # Audio buffer for Porcupine
            audio_buffer = []
            frame_length = self.porcupine.frame_length
            sample_rate = self.porcupine.sample_rate
            
            # Start audio stream
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio input status: {status}")
                
                # Convert to int16 and add to buffer
                audio_data = (indata[:, 0] * 32767).astype(np.int16)
                audio_buffer.extend(audio_data)
            
            # Start recording
            with sd.InputStream(
                callback=audio_callback,
                channels=1,
                samplerate=sample_rate,
                dtype=np.float32,
                blocksize=frame_length
            ):
                start_time = time.time()
                
                while self.is_listening_for_wake_word:
                    # Check timeout
                    if timeout and (time.time() - start_time) > timeout:
                        logger.info("Wake word detection timeout reached")
                        return False
                    
                    # Process audio frames when we have enough data
                    if len(audio_buffer) >= frame_length:
                        # Extract frame
                        frame = audio_buffer[:frame_length]
                        audio_buffer = audio_buffer[frame_length:]
                        
                        # Process with Porcupine
                        keyword_index = self.porcupine.process(frame)
                        
                        if keyword_index >= 0:
                            logger.info(f"Wake word '{WAKE_WORD}' detected!")
                            self.is_listening_for_wake_word = False
                            
                            # Provide audio confirmation if requested
                            if provide_feedback:
                                self._provide_wake_word_confirmation()
                            
                            return True
                    
                    # Small sleep to prevent excessive CPU usage
                    time.sleep(0.01)
                
                return False
                
        except Exception as e:
            logger.error(f"Wake word detection failed: {e}")
            raise RuntimeError(f"Wake word detection failed: {e}")
        finally:
            self.is_listening_for_wake_word = False
    
    def start_continuous_wake_word_monitoring(self, callback=None, session_timeout: Optional[float] = None) -> None:
        """
        Start continuous wake word monitoring in a separate thread.
        
        Args:
            callback: Optional callback function to call when wake word is detected
            session_timeout: Optional timeout for inactive sessions (in seconds)
        """
        if not self.porcupine:
            logger.error("Cannot start wake word monitoring: Porcupine not initialized")
            return
        
        if self.wake_word_thread and self.wake_word_thread.is_alive():
            logger.warning("Wake word monitoring already running")
            return
        
        def monitor_wake_word():
            """Continuous monitoring loop with session timeout handling."""
            logger.info("Starting continuous wake word monitoring...")
            session_start_time = time.time()
            
            while self.is_listening_for_wake_word:
                try:
                    # Check session timeout
                    if session_timeout and (time.time() - session_start_time) > session_timeout:
                        logger.info(f"Session timeout reached after {session_timeout} seconds")
                        self._provide_session_timeout_feedback()
                        break
                    
                    # Listen for wake word (with timeout to allow checking stop condition)
                    detected = self.listen_for_wake_word(timeout=1.0, provide_feedback=True)
                    
                    if detected:
                        # Reset session timer on wake word detection
                        session_start_time = time.time()
                        
                        if callback:
                            callback()
                    
                except Exception as e:
                    logger.error(f"Error in wake word monitoring: {e}")
                    time.sleep(1.0)  # Wait before retrying
            
            logger.info("Wake word monitoring loop ended")
        
        # Start monitoring thread
        self.is_listening_for_wake_word = True
        self.wake_word_thread = threading.Thread(target=monitor_wake_word, daemon=True)
        self.wake_word_thread.start()
        
        logger.info("Continuous wake word monitoring started")
    
    def stop_wake_word_monitoring(self) -> None:
        """Stop continuous wake word monitoring."""
        logger.info("Stopping wake word monitoring...")
        self.is_listening_for_wake_word = False
        
        if self.wake_word_thread and self.wake_word_thread.is_alive():
            self.wake_word_thread.join(timeout=2.0)
            if self.wake_word_thread.is_alive():
                logger.warning("Wake word monitoring thread did not stop gracefully")
        
        logger.info("Wake word monitoring stopped")

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
        
        if not self.tts_engine:
            logger.warning("TTS engine not available, skipping text-to-speech")
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
    
    def test_speech_to_text(self, duration: float = 3.0) -> Dict[str, Any]:
        """
        Test the complete speech-to-text pipeline and return detailed results.
        
        Args:
            duration: Test recording duration in seconds
            
        Returns:
            Dictionary with test results and transcription details
        """
        test_result = {
            "success": False,
            "transcription": "",
            "audio_stats": {},
            "whisper_details": {},
            "error": None
        }
        
        try:
            logger.info(f"Testing complete speech-to-text pipeline for {duration} seconds...")
            logger.info("Please speak clearly after the beep...")
            
            # Record audio
            audio_data = self._record_audio(duration, silence_threshold=0.001)  # Very low threshold
            
            if audio_data is not None and len(audio_data) > 0:
                # Calculate audio statistics
                audio_float = audio_data.astype(np.float32) / 32767.0
                test_result["audio_stats"] = {
                    "samples": len(audio_data),
                    "duration": len(audio_data) / AUDIO_SAMPLE_RATE,
                    "volume_rms": float(np.sqrt(np.mean(audio_float ** 2))),
                    "volume_max": float(np.max(np.abs(audio_float))),
                    "sample_rate": AUDIO_SAMPLE_RATE
                }
                
                logger.info(f"Audio recorded successfully:")
                logger.info(f"  Duration: {test_result['audio_stats']['duration']:.2f}s")
                logger.info(f"  RMS Volume: {test_result['audio_stats']['volume_rms']:.4f}")
                logger.info(f"  Max Volume: {test_result['audio_stats']['volume_max']:.4f}")
                
                # Test transcription
                try:
                    # Use the same duration as the recording
                    transcription = self.speech_to_text(duration=duration)
                    test_result["transcription"] = transcription
                    test_result["success"] = bool(transcription.strip())
                    
                    logger.info(f"Transcription result: '{transcription}'")
                    
                    if not transcription.strip():
                        logger.warning("Transcription was empty - audio may be unclear or too quiet")
                    else:
                        logger.info("Speech-to-text test completed successfully!")
                        
                except Exception as e:
                    test_result["error"] = f"Transcription failed: {e}"
                    logger.error(f"Transcription test failed: {e}")
                    
            else:
                test_result["error"] = "No audio data recorded"
                logger.error("Speech-to-text test failed: No audio data recorded")
                
        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"Speech-to-text test failed: {e}")
        
        return test_result

    def test_microphone(self, duration: float = 2.0) -> Dict[str, Any]:
        """
        Test microphone recording and return audio statistics.
        
        Args:
            duration: Test recording duration in seconds
            
        Returns:
            Dictionary with test results and audio statistics
        """
        test_result = {
            "success": False,
            "duration_recorded": 0.0,
            "samples_recorded": 0,
            "volume_rms": 0.0,
            "volume_max": 0.0,
            "sample_rate": AUDIO_SAMPLE_RATE,
            "error": None
        }
        
        try:
            logger.info(f"Testing microphone for {duration} seconds...")
            
            # Record test audio
            audio_data = self._record_audio(duration, silence_threshold=0.001)  # Very low threshold
            
            if audio_data is not None and len(audio_data) > 0:
                # Calculate statistics
                test_result["samples_recorded"] = len(audio_data)
                test_result["duration_recorded"] = len(audio_data) / AUDIO_SAMPLE_RATE
                
                # Convert to float for calculations
                audio_float = audio_data.astype(np.float32) / 32767.0
                test_result["volume_rms"] = float(np.sqrt(np.mean(audio_float ** 2)))
                test_result["volume_max"] = float(np.max(np.abs(audio_float)))
                
                test_result["success"] = True
                
                logger.info(f"Microphone test results:")
                logger.info(f"  Duration: {test_result['duration_recorded']:.2f}s")
                logger.info(f"  Samples: {test_result['samples_recorded']}")
                logger.info(f"  RMS Volume: {test_result['volume_rms']:.4f}")
                logger.info(f"  Max Volume: {test_result['volume_max']:.4f}")
                
                # Provide feedback on audio quality
                if test_result["volume_rms"] < 0.001:
                    logger.warning("Microphone input is very quiet. Check microphone settings.")
                elif test_result["volume_rms"] > 0.1:
                    logger.info("Good microphone input level detected.")
                else:
                    logger.info("Moderate microphone input level detected.")
                    
            else:
                test_result["error"] = "No audio data recorded"
                logger.error("Microphone test failed: No audio data recorded")
                
        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"Microphone test failed: {e}")
        
        return test_result

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
            "porcupine_initialized": False,
            "wake_word_configured": False,
            "errors": [],
            "warnings": []
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
            
            # Check Porcupine wake word detection
            validation_result["porcupine_initialized"] = self.porcupine is not None
            if not validation_result["porcupine_initialized"]:
                validation_result["warnings"].append("Porcupine wake word detection not initialized")
            
            # Check wake word configuration
            validation_result["wake_word_configured"] = (
                WAKE_WORD and 
                PORCUPINE_API_KEY and 
                PORCUPINE_API_KEY != "your_porcupine_api_key_here"
            )
            if not validation_result["wake_word_configured"]:
                validation_result["warnings"].append("Wake word not properly configured")
            
            # Check Porcupine sample rate compatibility
            if self.porcupine and validation_result["sample_rate_supported"]:
                porcupine_rate = self.porcupine.sample_rate
                if porcupine_rate != AUDIO_SAMPLE_RATE:
                    validation_result["warnings"].append(
                        f"Sample rate mismatch: Porcupine expects {porcupine_rate}Hz, "
                        f"configured for {AUDIO_SAMPLE_RATE}Hz"
                    )
            
        except Exception as e:
            validation_result["errors"].append(f"Audio validation failed: {e}")
        
        return validation_result
    
    def _provide_wake_word_confirmation(self) -> None:
        """
        Provide audio confirmation that wake word was detected.
        Uses a simple beep or TTS confirmation.
        """
        try:
            logger.info("Providing wake word confirmation")
            
            if not self.tts_engine:
                logger.debug("TTS not available, skipping wake word confirmation")
                return
            
            # Try to provide a simple confirmation sound or TTS
            confirmation_message = "Yes?"
            
            # Use TTS for confirmation (non-blocking)
            def speak_confirmation():
                try:
                    self.tts_engine.say(confirmation_message)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    logger.warning(f"TTS confirmation failed: {e}")
            
            # Run confirmation in separate thread to avoid blocking
            confirmation_thread = threading.Thread(target=speak_confirmation, daemon=True)
            confirmation_thread.start()
            
        except Exception as e:
            logger.error(f"Wake word confirmation failed: {e}")
    
    def _provide_session_timeout_feedback(self) -> None:
        """
        Provide feedback when session timeout is reached.
        """
        try:
            logger.info("Providing session timeout feedback")
            
            timeout_message = "Session timed out. Say the wake word to reactivate."
            
            # Use TTS for timeout notification
            def speak_timeout():
                try:
                    if self.tts_engine:
                        self.tts_engine.say(timeout_message)
                        self.tts_engine.runAndWait()
                except Exception as e:
                    logger.warning(f"TTS timeout notification failed: {e}")
            
            # Run timeout notification in separate thread
            timeout_thread = threading.Thread(target=speak_timeout, daemon=True)
            timeout_thread.start()
            
        except Exception as e:
            logger.error(f"Session timeout feedback failed: {e}")
    
    def _provide_system_activation_indicator(self) -> None:
        """
        Provide visual or audio indicator for system activation.
        This could be enhanced with visual indicators in the future.
        """
        try:
            logger.info("System activated - providing activation indicator")
            
            activation_message = "AURA activated. How can I help you?"
            
            # Use TTS for activation notification
            def speak_activation():
                try:
                    if self.tts_engine:
                        self.tts_engine.say(activation_message)
                        self.tts_engine.runAndWait()
                except Exception as e:
                    logger.warning(f"TTS activation notification failed: {e}")
            
            # Run activation notification in separate thread
            activation_thread = threading.Thread(target=speak_activation, daemon=True)
            activation_thread.start()
            
        except Exception as e:
            logger.error(f"System activation indicator failed: {e}")
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        try:
            # Stop wake word monitoring
            self.stop_wake_word_monitoring()
            
            # Clean up Porcupine
            if self.porcupine:
                self.porcupine.delete()
                self.porcupine = None
            
            # Clean up TTS engine
            if self.tts_engine:
                self.tts_engine.stop()
            
            # Stop any ongoing recordings
            sd.stop()
            
            logger.info("AudioModule cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during AudioModule cleanup: {e}")
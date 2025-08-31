# modules/feedback.py
"""
Feedback Module for AURA

Provides audio feedback using sound effects and text-to-speech.
Manages user communication and system status updates.
"""

import logging
import threading
import queue
import time
from pathlib import Path
from typing import Optional, Dict, Any, Union
import pygame
from enum import Enum

from config import SOUNDS, TTS_VOLUME
from .error_handler import (
    global_error_handler,
    with_error_handling,
    ErrorCategory,
    ErrorSeverity
)

logger = logging.getLogger(__name__)


class FeedbackPriority(Enum):
    """Priority levels for feedback messages."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class FeedbackType(Enum):
    """Types of feedback that can be provided."""
    SOUND = "sound"
    SPEECH = "speech"
    COMBINED = "combined"


class FeedbackModule:
    """
    Feedback Module for AURA
    
    Provides audio feedback using sound effects and text-to-speech.
    Manages user communication and system status updates with priority handling.
    """
    
    def __init__(self, audio_module=None):
        """
        Initialize the FeedbackModule.
        
        Args:
            audio_module: Optional AudioModule instance for TTS functionality
        """
        self.audio_module = audio_module
        self.is_initialized = False
        self.feedback_queue = queue.PriorityQueue()
        self.is_processing = False
        self.processing_thread = None
        self.sound_cache = {}
        
        # Initialize pygame mixer for sound effects
        self._initialize_pygame()
        
        # Load and cache sound files
        self._load_sound_files()
        
        # Start feedback processing thread
        self._start_processing_thread()
        
        logger.info("FeedbackModule initialized successfully")
    
    def _initialize_pygame(self) -> None:
        """Initialize pygame mixer for audio playback with error handling."""
        try:
            logger.info("Initializing pygame mixer for sound effects...")
            
            # Initialize pygame mixer with error handling
            try:
                pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
            except pygame.error as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="feedback",
                    function="_initialize_pygame",
                    category=ErrorCategory.HARDWARE_ERROR,
                    severity=ErrorSeverity.HIGH,
                    user_message="Failed to initialize audio system for sound effects."
                )
                raise Exception(f"Pygame mixer initialization failed: {error_info.user_message}")
            
            # Set volume with validation
            try:
                if not 0.0 <= TTS_VOLUME <= 1.0:
                    logger.warning(f"Invalid TTS volume {TTS_VOLUME}, using default 0.7")
                    volume = 0.7
                else:
                    volume = TTS_VOLUME
                
                pygame.mixer.music.set_volume(volume)
                logger.debug(f"Set pygame mixer volume to {volume}")
            except Exception as e:
                logger.warning(f"Failed to set volume: {e}, continuing with default")
            
            self.is_initialized = True
            logger.info("Pygame mixer initialized successfully")
            
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="feedback",
                function="_initialize_pygame",
                category=ErrorCategory.HARDWARE_ERROR,
                severity=ErrorSeverity.HIGH
            )
            logger.error(f"Failed to initialize pygame mixer: {error_info.message}")
            self.is_initialized = False
            raise Exception(f"Audio system initialization failed: {error_info.user_message}")
    
    def _load_sound_files(self) -> None:
        """Load and cache sound files for faster playback."""
        try:
            logger.info("Loading sound files...")
            
            for sound_name, sound_path in SOUNDS.items():
                try:
                    # Check if file exists
                    if not Path(sound_path).exists():
                        logger.warning(f"Sound file not found: {sound_path}")
                        # Create a placeholder sound or skip
                        self.sound_cache[sound_name] = None
                        continue
                    
                    # Check if file is actually an audio file
                    try:
                        with open(sound_path, 'rb') as f:
                            header = f.read(4)
                            if header != b'RIFF':  # WAV files start with RIFF
                                logger.debug(f"Skipping non-audio file: {sound_path}")
                                self.sound_cache[sound_name] = None
                                continue
                    except Exception:
                        logger.debug(f"Could not read file header: {sound_path}")
                        self.sound_cache[sound_name] = None
                        continue
                    
                    # Load sound file
                    sound = pygame.mixer.Sound(sound_path)
                    self.sound_cache[sound_name] = sound
                    logger.debug(f"Loaded sound: {sound_name} from {sound_path}")
                    
                except Exception as e:
                    logger.warning(f"Failed to load sound {sound_name}: {e}")
                    self.sound_cache[sound_name] = None
            
            logger.info(f"Loaded {len([s for s in self.sound_cache.values() if s is not None])} sound files")
            
        except Exception as e:
            logger.error(f"Error loading sound files: {e}")
    
    def _start_processing_thread(self) -> None:
        """Start the background thread for processing feedback queue."""
        try:
            self.is_processing = True
            self.processing_thread = threading.Thread(
                target=self._process_feedback_queue,
                daemon=True,
                name="FeedbackProcessor"
            )
            self.processing_thread.start()
            logger.info("Feedback processing thread started")
            
        except Exception as e:
            logger.error(f"Failed to start feedback processing thread: {e}")
            self.is_processing = False
    
    def _process_feedback_queue(self) -> None:
        """Process feedback items from the queue with priority handling."""
        logger.info("Feedback processing loop started")
        
        while self.is_processing:
            try:
                # Get next feedback item (blocks until available)
                try:
                    # Use timeout to allow checking stop condition
                    priority, timestamp, feedback_item = self.feedback_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process the feedback item
                self._execute_feedback(feedback_item)
                
                # Mark task as done
                self.feedback_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing feedback queue: {e}")
                time.sleep(0.1)  # Brief pause before continuing
        
        logger.info("Feedback processing loop ended")
    
    def _execute_feedback(self, feedback_item: Dict[str, Any]) -> None:
        """
        Execute a single feedback item.
        
        Args:
            feedback_item: Dictionary containing feedback details
        """
        try:
            feedback_type = feedback_item.get("type", FeedbackType.SOUND)
            
            if feedback_type == FeedbackType.SOUND:
                self._play_sound_effect(feedback_item)
            elif feedback_type == FeedbackType.SPEECH:
                self._play_speech(feedback_item)
            elif feedback_type == FeedbackType.COMBINED:
                # Play sound first, then speech
                self._play_sound_effect(feedback_item)
                time.sleep(0.1)  # Brief pause between sound and speech
                self._play_speech(feedback_item)
            
        except Exception as e:
            logger.error(f"Error executing feedback: {e}")
    
    def _play_sound_effect(self, feedback_item: Dict[str, Any]) -> None:
        """
        Play a sound effect.
        
        Args:
            feedback_item: Dictionary containing sound details
        """
        try:
            sound_name = feedback_item.get("sound_name")
            if not sound_name:
                logger.warning("No sound name specified for sound effect")
                return
            
            # Get sound from cache
            sound = self.sound_cache.get(sound_name)
            if sound is None:
                logger.warning(f"Sound '{sound_name}' not available")
                return
            
            # Play sound
            sound.play()
            logger.debug(f"Played sound effect: {sound_name}")
            
        except Exception as e:
            logger.error(f"Error playing sound effect: {e}")
    
    def _play_speech(self, feedback_item: Dict[str, Any]) -> None:
        """
        Play text-to-speech.
        
        Args:
            feedback_item: Dictionary containing speech details
        """
        try:
            message = feedback_item.get("message")
            if not message:
                logger.warning("No message specified for speech")
                return
            
            if not self.audio_module:
                logger.warning("AudioModule not available for TTS")
                return
            
            # Use AudioModule for TTS
            self.audio_module.text_to_speech(message)
            logger.debug(f"Played TTS message: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Error playing TTS message: {e}")
    
    @with_error_handling(
        category=ErrorCategory.HARDWARE_ERROR,
        severity=ErrorSeverity.LOW,
        max_retries=1,
        user_message="Having trouble playing sound effects."
    )
    def play(self, sound_name: str, priority: FeedbackPriority = FeedbackPriority.NORMAL) -> None:
        """
        Play a sound effect with specified priority and error handling.
        
        Args:
            sound_name: Name of the sound to play (success, failure, thinking)
            priority: Priority level for the feedback
        """
        if not self.is_initialized:
            error_info = global_error_handler.handle_error(
                error=Exception("FeedbackModule not initialized"),
                module="feedback",
                function="play",
                category=ErrorCategory.CONFIGURATION_ERROR,
                context={"sound_name": sound_name, "priority": priority.name}
            )
            logger.warning(f"Cannot play sound: {error_info.message}")
            return
        
        try:
            # Validate inputs
            if not sound_name or not isinstance(sound_name, str):
                raise ValueError("Sound name must be a non-empty string")
            
            if not isinstance(priority, FeedbackPriority):
                raise ValueError("Priority must be a FeedbackPriority enum value")
            
            # Validate sound name
            if sound_name not in SOUNDS:
                error_info = global_error_handler.handle_error(
                    error=Exception(f"Unknown sound name: {sound_name}"),
                    module="feedback",
                    function="play",
                    category=ErrorCategory.VALIDATION_ERROR,
                    context={"sound_name": sound_name, "available_sounds": list(SOUNDS.keys())}
                )
                logger.warning(f"Unknown sound name: {error_info.message}")
                return
            
            # Create feedback item
            feedback_item = {
                "type": FeedbackType.SOUND,
                "sound_name": sound_name,
                "timestamp": time.time()
            }
            
            # Add to queue with priority
            try:
                self._add_to_queue(feedback_item, priority)
                logger.debug(f"Queued sound effect: {sound_name} with priority {priority.name}")
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="feedback",
                    function="play",
                    category=ErrorCategory.PROCESSING_ERROR,
                    context={"sound_name": sound_name, "priority": priority.name}
                )
                logger.error(f"Failed to queue sound effect: {error_info.message}")
                # Try to play directly as fallback
                try:
                    self._play_sound_effect(feedback_item)
                except Exception as fallback_error:
                    logger.error(f"Fallback sound playback also failed: {fallback_error}")
            
        except Exception as e:
            error_info = global_error_handler.handle_error(
                error=e,
                module="feedback",
                function="play",
                category=ErrorCategory.PROCESSING_ERROR,
                context={"sound_name": sound_name, "priority": priority.name}
            )
            logger.error(f"Error playing sound effect: {error_info.message}")
    
    def speak(self, message: str, priority: FeedbackPriority = FeedbackPriority.NORMAL) -> None:
        """
        Speak a message using text-to-speech with specified priority.
        
        Args:
            message: Text message to speak
            priority: Priority level for the feedback
        """
        if not message or not message.strip():
            logger.warning("Empty message provided for TTS")
            return
        
        try:
            # Create feedback item
            feedback_item = {
                "type": FeedbackType.SPEECH,
                "message": message.strip()
            }
            
            # Add to queue with priority
            self._add_to_queue(feedback_item, priority)
            
            logger.debug(f"Queued TTS message: {message[:50]}... with priority {priority.name}")
            
        except Exception as e:
            logger.error(f"Error queuing TTS message: {e}")
    
    def play_with_message(
        self, 
        sound_name: str, 
        message: str, 
        priority: FeedbackPriority = FeedbackPriority.NORMAL
    ) -> None:
        """
        Play a sound effect followed by a spoken message.
        
        Args:
            sound_name: Name of the sound to play
            message: Text message to speak after the sound
            priority: Priority level for the feedback
        """
        if not message or not message.strip():
            # Just play sound if no message
            self.play(sound_name, priority)
            return
        
        try:
            # Create combined feedback item
            feedback_item = {
                "type": FeedbackType.COMBINED,
                "sound_name": sound_name,
                "message": message.strip()
            }
            
            # Add to queue with priority
            self._add_to_queue(feedback_item, priority)
            
            logger.debug(f"Queued combined feedback: {sound_name} + message with priority {priority.name}")
            
        except Exception as e:
            logger.error(f"Error queuing combined feedback: {e}")
    
    def _add_to_queue(self, feedback_item: Dict[str, Any], priority: FeedbackPriority) -> None:
        """
        Add feedback item to the priority queue.
        
        Args:
            feedback_item: Dictionary containing feedback details
            priority: Priority level for the feedback
        """
        try:
            # Create priority tuple (lower number = higher priority)
            # Use negative priority value so higher enum values get higher priority
            priority_value = -priority.value
            timestamp = time.time()
            
            # Add to priority queue
            self.feedback_queue.put((priority_value, timestamp, feedback_item))
            
        except Exception as e:
            logger.error(f"Error adding feedback to queue: {e}")
    
    def clear_queue(self, priority_threshold: Optional[FeedbackPriority] = None) -> int:
        """
        Clear feedback queue, optionally only items below a priority threshold.
        
        Args:
            priority_threshold: Only clear items with priority below this level
            
        Returns:
            Number of items cleared from queue
        """
        try:
            if priority_threshold is None:
                # Clear entire queue
                cleared_count = self.feedback_queue.qsize()
                
                # Create new empty queue
                self.feedback_queue = queue.PriorityQueue()
                
                logger.info(f"Cleared entire feedback queue ({cleared_count} items)")
                return cleared_count
            
            else:
                # Clear only items below priority threshold
                temp_items = []
                cleared_count = 0
                
                # Extract all items
                while not self.feedback_queue.empty():
                    try:
                        item = self.feedback_queue.get_nowait()
                        priority_value, timestamp, feedback_item = item
                        
                        # Convert back to priority enum
                        item_priority = FeedbackPriority(-priority_value)
                        
                        if item_priority.value < priority_threshold.value:
                            cleared_count += 1
                        else:
                            temp_items.append(item)
                    except queue.Empty:
                        break
                
                # Put back items that should remain
                for item in temp_items:
                    self.feedback_queue.put(item)
                
                logger.info(f"Cleared {cleared_count} items below priority {priority_threshold.name}")
                return cleared_count
                
        except Exception as e:
            logger.error(f"Error clearing feedback queue: {e}")
            return 0
    
    def get_queue_size(self) -> int:
        """
        Get the current size of the feedback queue.
        
        Returns:
            Number of items in the queue
        """
        return self.feedback_queue.qsize()
    
    def is_queue_empty(self) -> bool:
        """
        Check if the feedback queue is empty.
        
        Returns:
            True if queue is empty, False otherwise
        """
        return self.feedback_queue.empty()
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all queued feedback to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if all feedback completed, False if timeout
        """
        try:
            if timeout:
                # Wait with timeout
                start_time = time.time()
                while not self.feedback_queue.empty():
                    if time.time() - start_time > timeout:
                        return False
                    time.sleep(0.1)
                return True
            else:
                # Wait indefinitely
                self.feedback_queue.join()
                return True
                
        except Exception as e:
            logger.error(f"Error waiting for feedback completion: {e}")
            return False
    
    def validate_sound_files(self) -> Dict[str, Any]:
        """
        Validate that all configured sound files are available and playable.
        
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "pygame_initialized": self.is_initialized,
            "sounds_available": {},
            "total_sounds": len(SOUNDS),
            "loaded_sounds": 0,
            "missing_sounds": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check each configured sound
            for sound_name, sound_path in SOUNDS.items():
                sound_info = {
                    "path": sound_path,
                    "exists": Path(sound_path).exists(),
                    "loaded": False,
                    "playable": False
                }
                
                if sound_info["exists"]:
                    # Check if loaded in cache
                    cached_sound = self.sound_cache.get(sound_name)
                    sound_info["loaded"] = cached_sound is not None
                    
                    if sound_info["loaded"]:
                        validation_result["loaded_sounds"] += 1
                        sound_info["playable"] = True
                    else:
                        validation_result["warnings"].append(f"Sound {sound_name} exists but failed to load")
                else:
                    validation_result["missing_sounds"].append(sound_name)
                    validation_result["warnings"].append(f"Sound file not found: {sound_path}")
                
                validation_result["sounds_available"][sound_name] = sound_info
            
            # Check pygame initialization
            if not validation_result["pygame_initialized"]:
                validation_result["errors"].append("Pygame mixer not initialized")
            
            # Summary
            if validation_result["loaded_sounds"] == 0:
                validation_result["errors"].append("No sound files loaded successfully")
            elif validation_result["loaded_sounds"] < validation_result["total_sounds"]:
                validation_result["warnings"].append(
                    f"Only {validation_result['loaded_sounds']}/{validation_result['total_sounds']} sounds loaded"
                )
            
        except Exception as e:
            validation_result["errors"].append(f"Sound validation failed: {e}")
        
        return validation_result
    
    def cleanup(self) -> None:
        """Clean up feedback module resources."""
        try:
            logger.info("Cleaning up FeedbackModule...")
            
            # Stop processing thread
            self.is_processing = False
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2.0)
                if self.processing_thread.is_alive():
                    logger.warning("Feedback processing thread did not stop gracefully")
            
            # Clear queue
            self.clear_queue()
            
            # Clean up pygame
            if self.is_initialized:
                pygame.mixer.quit()
                self.is_initialized = False
            
            # Clear sound cache
            self.sound_cache.clear()
            
            logger.info("FeedbackModule cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during FeedbackModule cleanup: {e}")
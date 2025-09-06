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
    HYBRID_FAST = "hybrid_fast"
    HYBRID_SLOW = "hybrid_slow"
    HYBRID_FALLBACK = "hybrid_fallback"


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
        
        # Initialize hybrid feedback configuration from config
        from config import (
            HYBRID_FEEDBACK_ENABLED,
            HYBRID_FAST_PATH_FEEDBACK,
            HYBRID_SLOW_PATH_FEEDBACK,
            HYBRID_FALLBACK_FEEDBACK,
            HYBRID_FEEDBACK_VOLUME,
            HYBRID_FEEDBACK_MESSAGES
        )
        
        self.hybrid_config = {
            'enabled': HYBRID_FEEDBACK_ENABLED,
            'fast_path_enabled': HYBRID_FAST_PATH_FEEDBACK,
            'slow_path_enabled': HYBRID_SLOW_PATH_FEEDBACK,
            'fallback_enabled': HYBRID_FALLBACK_FEEDBACK,
            'volume_adjustment': HYBRID_FEEDBACK_VOLUME,
            'messages_enabled': HYBRID_FEEDBACK_MESSAGES
        }
        
        # Initialize pygame mixer for sound effects
        self._initialize_pygame()
        
        # Load and cache sound files
        self._load_sound_files()
        
        # Start feedback processing thread
        self._start_processing_thread()
        
        logger.info(f"FeedbackModule initialized successfully with hybrid config: {self.hybrid_config}")
    
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
        Execute a single feedback item with enhanced conversational and deferred action support.
        
        Args:
            feedback_item: Dictionary containing feedback details
        """
        try:
            feedback_type = feedback_item.get("type", FeedbackType.SOUND)
            
            # Check hybrid configuration
            hybrid_config = getattr(self, 'hybrid_config', {})
            
            if feedback_type == FeedbackType.SOUND:
                self._play_sound_effect(feedback_item)
            elif feedback_type == FeedbackType.SPEECH:
                self._play_enhanced_speech(feedback_item)
            elif feedback_type == FeedbackType.COMBINED:
                # Play sound first, then speech with enhanced timing
                self._play_sound_effect(feedback_item)
                
                # Use custom pause timing if specified
                pause_duration = feedback_item.get("pause_before_speech", 0.1)
                if feedback_item.get("conversational_mode"):
                    pause_duration = max(pause_duration, 0.3)  # Longer pause for conversations
                elif feedback_item.get("deferred_action_mode"):
                    pause_duration = max(pause_duration, 0.2)  # Medium pause for deferred actions
                
                time.sleep(pause_duration)
                self._play_enhanced_speech(feedback_item)
            elif feedback_type == FeedbackType.HYBRID_FAST:
                if hybrid_config.get('fast_path_enabled', True):
                    self._play_hybrid_sound_effect(feedback_item)
            elif feedback_type == FeedbackType.HYBRID_SLOW:
                if hybrid_config.get('slow_path_enabled', True):
                    self._play_hybrid_sound_effect(feedback_item)
                    if feedback_item.get("message"):
                        time.sleep(0.1)
                        self._play_enhanced_speech(feedback_item)
            elif feedback_type == FeedbackType.HYBRID_FALLBACK:
                if hybrid_config.get('fallback_enabled', True):
                    self._play_hybrid_sound_effect(feedback_item)
                    if feedback_item.get("message"):
                        time.sleep(0.2)  # Longer pause for fallback
                        self._play_enhanced_speech(feedback_item)
            
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
    
    def _play_enhanced_speech(self, feedback_item: Dict[str, Any]) -> None:
        """
        Play enhanced text-to-speech with conversational and deferred action optimizations.
        
        Args:
            feedback_item: Dictionary containing enhanced speech details
        """
        try:
            message = feedback_item.get("message")
            if not message:
                logger.warning("No message specified for enhanced speech")
                return
            
            if not self.audio_module:
                logger.warning("AudioModule not available for enhanced TTS")
                return
            
            # Apply message enhancements based on mode
            enhanced_message = self._enhance_speech_message(message, feedback_item)
            
            # Configure TTS settings based on feedback type
            tts_config = self._get_tts_configuration(feedback_item)
            
            # Use AudioModule for enhanced TTS
            if hasattr(self.audio_module, 'text_to_speech_enhanced'):
                # Use enhanced TTS if available
                self.audio_module.text_to_speech_enhanced(enhanced_message, **tts_config)
            else:
                # Fall back to standard TTS
                self.audio_module.text_to_speech(enhanced_message)
            
            # Log feedback details
            mode_info = []
            if feedback_item.get("conversational_mode"):
                mode_info.append("conversational")
            if feedback_item.get("deferred_action_mode"):
                mode_info.append("deferred_action")
            if feedback_item.get("completion_feedback"):
                mode_info.append("completion")
            if feedback_item.get("timeout_feedback"):
                mode_info.append("timeout")
            
            mode_str = f" ({', '.join(mode_info)})" if mode_info else ""
            logger.debug(f"Played enhanced TTS message{mode_str}: {enhanced_message[:50]}...")
            
        except Exception as e:
            logger.error(f"Error playing enhanced TTS message: {e}")
            # Fall back to basic speech
            try:
                self._play_speech(feedback_item)
            except Exception as fallback_error:
                logger.error(f"Fallback speech also failed: {fallback_error}")
    
    def _enhance_speech_message(self, message: str, feedback_item: Dict[str, Any]) -> str:
        """
        Enhance speech message based on feedback context and mode.
        
        Args:
            message: Original message text
            feedback_item: Feedback item containing context
            
        Returns:
            Enhanced message text
        """
        try:
            enhanced_message = message.strip()
            
            # Apply conversational enhancements
            if feedback_item.get("conversational_mode"):
                # Add natural conversational markers
                if not enhanced_message.endswith(('.', '!', '?')):
                    enhanced_message += '.'
                
                # Add slight emphasis for natural speech
                if feedback_item.get("natural_intonation"):
                    # Add pauses for natural speech rhythm
                    enhanced_message = enhanced_message.replace(', ', ', ... ')
                    enhanced_message = enhanced_message.replace('. ', '. ... ')
            
            # Apply deferred action enhancements
            elif feedback_item.get("deferred_action_mode"):
                # Emphasize key words for clarity
                emphasis_words = feedback_item.get("emphasis_words", [])
                for word in emphasis_words:
                    # Simple emphasis by adding slight pause
                    enhanced_message = enhanced_message.replace(
                        word, f"... {word} ..."
                    )
                
                # Add clear instruction markers
                if feedback_item.get("completion_feedback"):
                    enhanced_message = f"... {enhanced_message}"
                elif feedback_item.get("timeout_feedback"):
                    enhanced_message = f"Attention: {enhanced_message}"
            
            # Apply intent recognition enhancements
            elif feedback_item.get("intent_recognition_mode"):
                # Keep it subtle and brief
                enhanced_message = enhanced_message.lower()
            
            return enhanced_message
            
        except Exception as e:
            logger.warning(f"Error enhancing speech message: {e}")
            return message  # Return original message on error
    
    def _get_tts_configuration(self, feedback_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get TTS configuration based on feedback context.
        
        Args:
            feedback_item: Feedback item containing context
            
        Returns:
            Dictionary of TTS configuration parameters
        """
        try:
            config = {}
            
            # Apply speech rate modifications
            rate_modifier = feedback_item.get("speech_rate_modifier", 1.0)
            if rate_modifier != 1.0:
                config['rate_multiplier'] = rate_modifier
            
            # Apply volume modifications
            volume_modifier = feedback_item.get("volume_modifier", 1.0)
            if volume_modifier != 1.0:
                config['volume_multiplier'] = volume_modifier
            
            # Apply mode-specific configurations
            if feedback_item.get("conversational_mode"):
                config['conversational_style'] = True
                config['natural_pauses'] = True
            
            if feedback_item.get("deferred_action_mode"):
                config['clear_articulation'] = True
                config['instruction_style'] = True
            
            if feedback_item.get("completion_feedback"):
                config['confirmation_style'] = True
            
            if feedback_item.get("timeout_feedback"):
                config['alert_style'] = True
            
            return config
            
        except Exception as e:
            logger.warning(f"Error getting TTS configuration: {e}")
            return {}  # Return empty config on error
    
    def _play_hybrid_sound_effect(self, feedback_item: Dict[str, Any]) -> None:
        """
        Play a hybrid sound effect with volume and duration modifications.
        
        Args:
            feedback_item: Dictionary containing hybrid sound details
        """
        try:
            sound_name = feedback_item.get("sound_name")
            if not sound_name:
                logger.warning("No sound name specified for hybrid sound effect")
                return
            
            # Get sound from cache
            sound = self.sound_cache.get(sound_name)
            if sound is None:
                logger.warning(f"Sound '{sound_name}' not available")
                return
            
            # Apply volume modification
            volume_modifier = feedback_item.get("volume_modifier", 1.0)
            hybrid_config = getattr(self, 'hybrid_config', {})
            global_volume_adjustment = hybrid_config.get('volume_adjustment', 1.0)
            
            # Calculate final volume
            final_volume = volume_modifier * global_volume_adjustment
            final_volume = max(0.0, min(1.0, final_volume))  # Clamp to valid range
            
            # Set volume and play sound
            sound.set_volume(final_volume)
            sound.play()
            
            # Duration modification is handled by the sound itself
            # For future enhancement, could implement sound truncation
            duration_modifier = feedback_item.get("duration_modifier", 1.0)
            
            logger.debug(f"Played hybrid sound effect: {sound_name} "
                        f"(volume: {final_volume:.2f}, duration_mod: {duration_modifier:.2f})")
            
        except Exception as e:
            logger.error(f"Error playing hybrid sound effect: {e}")
    
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
    
    def provide_conversational_feedback(
        self, 
        message: str, 
        priority: FeedbackPriority = FeedbackPriority.NORMAL,
        include_thinking_sound: bool = False
    ) -> None:
        """
        Provide audio feedback optimized for conversational interactions.
        
        Args:
            message: Conversational response to speak
            priority: Priority level for the feedback
            include_thinking_sound: Whether to play thinking sound before speaking
        """
        if not message or not message.strip():
            logger.warning("Empty conversational message provided")
            return
        
        try:
            if include_thinking_sound:
                # Play thinking sound followed by conversational response
                feedback_item = {
                    "type": FeedbackType.COMBINED,
                    "sound_name": "thinking",
                    "message": message.strip(),
                    "conversational_mode": True,
                    "speech_rate_modifier": 1.0,  # Normal speech rate for conversations
                    "pause_before_speech": 0.3    # Brief pause after thinking sound
                }
            else:
                # Just speak the conversational response
                feedback_item = {
                    "type": FeedbackType.SPEECH,
                    "message": message.strip(),
                    "conversational_mode": True,
                    "speech_rate_modifier": 1.0,
                    "natural_intonation": True
                }
            
            self._add_to_queue(feedback_item, priority)
            logger.debug(f"Queued conversational feedback: {message[:50]}... with priority {priority.name}")
            
        except Exception as e:
            logger.error(f"Error queuing conversational feedback: {e}")
    
    def provide_deferred_action_instructions(
        self, 
        content_type: str = "content",
        priority: FeedbackPriority = FeedbackPriority.HIGH
    ) -> None:
        """
        Provide audio instructions for deferred action workflows.
        
        Args:
            content_type: Type of content generated (code, text, content)
            priority: Priority level for the feedback
        """
        try:
            # Determine appropriate instruction message based on content type
            if content_type == 'code':
                instruction_message = "Code generated successfully. Click where you want me to type it."
                sound_name = "success"
            elif content_type == 'text':
                instruction_message = "Text generated successfully. Click where you want me to type it."
                sound_name = "success"
            else:
                instruction_message = "Content generated successfully. Click where you want me to place it."
                sound_name = "success"
            
            # Create deferred action instruction feedback
            feedback_item = {
                "type": FeedbackType.COMBINED,
                "sound_name": sound_name,
                "message": instruction_message,
                "deferred_action_mode": True,
                "speech_rate_modifier": 0.9,  # Slightly slower for clarity
                "emphasis_words": ["click", "where", "want"],  # Emphasize key words
                "pause_before_speech": 0.2
            }
            
            self._add_to_queue(feedback_item, priority)
            logger.debug(f"Queued deferred action instructions for {content_type}")
            
        except Exception as e:
            logger.error(f"Error queuing deferred action instructions: {e}")
    
    def provide_deferred_action_completion_feedback(
        self, 
        success: bool, 
        content_type: str = "content",
        priority: FeedbackPriority = FeedbackPriority.HIGH
    ) -> None:
        """
        Provide audio feedback when deferred action completes.
        
        Args:
            success: Whether the action completed successfully
            content_type: Type of content that was placed
            priority: Priority level for the feedback
        """
        try:
            if success:
                if content_type == 'code':
                    message = "Code placed successfully."
                elif content_type == 'text':
                    message = "Text placed successfully."
                else:
                    message = "Content placed successfully."
                sound_name = "success"
            else:
                message = "Failed to place content. Please try again."
                sound_name = "failure"
            
            # Create completion feedback
            feedback_item = {
                "type": FeedbackType.COMBINED,
                "sound_name": sound_name,
                "message": message,
                "deferred_action_mode": True,
                "completion_feedback": True,
                "speech_rate_modifier": 1.0,
                "pause_before_speech": 0.1
            }
            
            self._add_to_queue(feedback_item, priority)
            logger.debug(f"Queued deferred action completion feedback: success={success}")
            
        except Exception as e:
            logger.error(f"Error queuing deferred action completion feedback: {e}")
    
    def provide_deferred_action_timeout_feedback(
        self, 
        elapsed_time: float,
        priority: FeedbackPriority = FeedbackPriority.HIGH
    ) -> None:
        """
        Provide audio feedback when deferred action times out.
        
        Args:
            elapsed_time: Time elapsed before timeout
            priority: Priority level for the feedback
        """
        try:
            timeout_message = f"The deferred action has timed out after {elapsed_time:.0f} seconds. The action has been cancelled."
            
            feedback_item = {
                "type": FeedbackType.COMBINED,
                "sound_name": "failure",
                "message": timeout_message,
                "deferred_action_mode": True,
                "timeout_feedback": True,
                "speech_rate_modifier": 0.9,  # Slower for important timeout info
                "pause_before_speech": 0.3
            }
            
            self._add_to_queue(feedback_item, priority)
            logger.debug(f"Queued deferred action timeout feedback: {elapsed_time:.1f}s")
            
        except Exception as e:
            logger.error(f"Error queuing deferred action timeout feedback: {e}")
    
    def provide_intent_recognition_feedback(
        self, 
        intent_type: str, 
        confidence: float,
        priority: FeedbackPriority = FeedbackPriority.LOW
    ) -> None:
        """
        Provide subtle audio feedback for intent recognition (optional/debug mode).
        
        Args:
            intent_type: Recognized intent type
            confidence: Confidence level of recognition
            priority: Priority level for the feedback
        """
        try:
            # Only provide feedback in debug mode or for low confidence
            if confidence < 0.7:
                # Low confidence - provide subtle thinking sound
                feedback_item = {
                    "type": FeedbackType.SOUND,
                    "sound_name": "thinking",
                    "intent_recognition_mode": True,
                    "volume_modifier": 0.5,  # Quieter for subtle feedback
                    "duration_modifier": 0.3  # Shorter duration
                }
                
                self._add_to_queue(feedback_item, priority)
                logger.debug(f"Queued low-confidence intent recognition feedback: {intent_type} ({confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error queuing intent recognition feedback: {e}")
    
    def provide_mode_transition_feedback(
        self, 
        from_mode: str, 
        to_mode: str,
        priority: FeedbackPriority = FeedbackPriority.LOW
    ) -> None:
        """
        Provide audio feedback for mode transitions (optional/subtle).
        
        Args:
            from_mode: Previous interaction mode
            to_mode: New interaction mode
            priority: Priority level for the feedback
        """
        try:
            # Only provide feedback for significant mode changes
            significant_transitions = [
                ("ready", "waiting_for_user"),
                ("waiting_for_user", "ready"),
                ("processing", "waiting_for_user")
            ]
            
            if (from_mode, to_mode) in significant_transitions:
                if to_mode == "waiting_for_user":
                    # Entering waiting state - subtle success sound
                    sound_name = "success"
                    volume_modifier = 0.6
                elif from_mode == "waiting_for_user":
                    # Exiting waiting state - subtle thinking sound
                    sound_name = "thinking"
                    volume_modifier = 0.4
                else:
                    return  # No feedback for other transitions
                
                feedback_item = {
                    "type": FeedbackType.SOUND,
                    "sound_name": sound_name,
                    "mode_transition": True,
                    "volume_modifier": volume_modifier,
                    "duration_modifier": 0.5
                }
                
                self._add_to_queue(feedback_item, priority)
                logger.debug(f"Queued mode transition feedback: {from_mode} -> {to_mode}")
            
        except Exception as e:
            logger.error(f"Error queuing mode transition feedback: {e}")
    
    def provide_enhanced_error_feedback(
        self, 
        error_message: str, 
        error_context: str = "general",
        priority: FeedbackPriority = FeedbackPriority.HIGH
    ) -> None:
        """
        Provide enhanced audio feedback for errors with context-appropriate messaging.
        
        Args:
            error_message: Error message to speak
            error_context: Context of the error (conversational, deferred_action, gui_interaction, general)
            priority: Priority level for the feedback
        """
        try:
            # Enhance error message based on context
            if error_context == "conversational":
                enhanced_message = f"I'm sorry, I had trouble with that conversation. {error_message}"
            elif error_context == "deferred_action":
                enhanced_message = f"There was an issue with the deferred action. {error_message}"
            elif error_context == "gui_interaction":
                enhanced_message = f"I couldn't complete that action on screen. {error_message}"
            else:
                enhanced_message = error_message
            
            # Create enhanced error feedback
            feedback_item = {
                "type": FeedbackType.COMBINED,
                "sound_name": "failure",
                "message": enhanced_message,
                "error_feedback": True,
                "error_context": error_context,
                "speech_rate_modifier": 0.9,  # Slightly slower for clarity
                "pause_before_speech": 0.2
            }
            
            self._add_to_queue(feedback_item, priority)
            logger.debug(f"Queued enhanced error feedback for {error_context}: {error_message[:50]}...")
            
        except Exception as e:
            logger.error(f"Error queuing enhanced error feedback: {e}")
    
    def provide_success_feedback(
        self, 
        success_message: str = None, 
        success_context: str = "general",
        priority: FeedbackPriority = FeedbackPriority.NORMAL
    ) -> None:
        """
        Provide enhanced audio feedback for successful operations.
        
        Args:
            success_message: Optional success message to speak
            success_context: Context of the success (gui_interaction, deferred_action, conversational, general)
            priority: Priority level for the feedback
        """
        try:
            # Determine appropriate success message if not provided
            if not success_message:
                if success_context == "gui_interaction":
                    success_message = "Action completed successfully."
                elif success_context == "deferred_action":
                    success_message = "Deferred action completed successfully."
                elif success_context == "conversational":
                    success_message = None  # No default message for conversations
                else:
                    success_message = "Operation completed successfully."
            
            # Create success feedback
            if success_message:
                feedback_item = {
                    "type": FeedbackType.COMBINED,
                    "sound_name": "success",
                    "message": success_message,
                    "success_feedback": True,
                    "success_context": success_context,
                    "speech_rate_modifier": 1.0,
                    "pause_before_speech": 0.1
                }
            else:
                # Just play success sound without message
                feedback_item = {
                    "type": FeedbackType.SOUND,
                    "sound_name": "success",
                    "success_feedback": True,
                    "success_context": success_context
                }
            
            self._add_to_queue(feedback_item, priority)
            logger.debug(f"Queued success feedback for {success_context}")
            
        except Exception as e:
            logger.error(f"Error queuing success feedback: {e}")
    
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
    
    def play_fast_path_feedback(self, success: bool = True, priority: FeedbackPriority = FeedbackPriority.LOW) -> None:
        """
        Play audio feedback for fast path execution.
        
        Args:
            success: Whether the fast path execution was successful
            priority: Priority level for the feedback
        """
        try:
            # Check if hybrid feedback is enabled
            if not self.hybrid_config.get('enabled', True) or not self.hybrid_config.get('fast_path_enabled', True):
                return
            
            if success:
                # Subtle success sound for fast path - shorter/quieter than normal success
                feedback_item = {
                    "type": FeedbackType.HYBRID_FAST,
                    "sound_name": "success",
                    "volume_modifier": 0.7,  # Quieter than normal
                    "duration_modifier": 0.5,  # Shorter than normal
                    "message": None
                }
            else:
                # Fast path failed, will fallback - use a neutral sound
                feedback_item = {
                    "type": FeedbackType.HYBRID_FAST,
                    "sound_name": "thinking",
                    "volume_modifier": 0.5,  # Very quiet
                    "duration_modifier": 0.3,  # Very short
                    "message": None
                }
            
            self._add_to_queue(feedback_item, priority)
            logger.debug(f"Queued fast path feedback: success={success}")
            
        except Exception as e:
            logger.error(f"Error queuing fast path feedback: {e}")
    
    def play_slow_path_feedback(self, message: str = None, priority: FeedbackPriority = FeedbackPriority.LOW) -> None:
        """
        Play audio feedback for slow path (vision-based) execution.
        
        Args:
            message: Optional message to speak
            priority: Priority level for the feedback
        """
        try:
            # Check if hybrid feedback is enabled
            if not self.hybrid_config.get('enabled', True) or not self.hybrid_config.get('slow_path_enabled', True):
                return
            
            # Only include message if messages are enabled
            message_to_use = message if self.hybrid_config.get('messages_enabled', True) else None
            
            feedback_item = {
                "type": FeedbackType.HYBRID_SLOW,
                "sound_name": "thinking",
                "volume_modifier": 1.0,  # Normal volume
                "duration_modifier": 1.0,  # Normal duration
                "message": message_to_use
            }
            
            self._add_to_queue(feedback_item, priority)
            logger.debug(f"Queued slow path feedback with message: {message}")
            
        except Exception as e:
            logger.error(f"Error queuing slow path feedback: {e}")
    
    def play_fallback_feedback(self, reason: str = None, priority: FeedbackPriority = FeedbackPriority.NORMAL) -> None:
        """
        Play audio feedback when falling back from fast path to slow path.
        
        Args:
            reason: Optional reason for fallback
            priority: Priority level for the feedback
        """
        try:
            # Check if hybrid feedback is enabled
            if not self.hybrid_config.get('enabled', True) or not self.hybrid_config.get('fallback_enabled', True):
                return
            
            # Only include message if messages are enabled
            message_to_use = None
            if self.hybrid_config.get('messages_enabled', True) and reason:
                message_to_use = f"Switching to visual analysis: {reason}"
            
            # Use a distinctive sound pattern for fallback
            feedback_item = {
                "type": FeedbackType.HYBRID_FALLBACK,
                "sound_name": "thinking",
                "volume_modifier": 0.8,  # Slightly quieter
                "duration_modifier": 1.2,  # Slightly longer
                "message": message_to_use,
                "fallback_reason": reason
            }
            
            self._add_to_queue(feedback_item, priority)
            logger.debug(f"Queued fallback feedback: {reason}")
            
        except Exception as e:
            logger.error(f"Error queuing fallback feedback: {e}")
    
    def configure_hybrid_feedback(self, 
                                fast_path_enabled: bool = True,
                                slow_path_enabled: bool = True,
                                fallback_enabled: bool = True,
                                volume_adjustment: float = 1.0) -> None:
        """
        Configure hybrid feedback preferences.
        
        Args:
            fast_path_enabled: Whether to play fast path feedback
            slow_path_enabled: Whether to play slow path feedback
            fallback_enabled: Whether to play fallback feedback
            volume_adjustment: Global volume adjustment for hybrid feedback (0.0-1.0)
        """
        try:
            # Store configuration in metadata
            if not hasattr(self, 'hybrid_config'):
                self.hybrid_config = {}
            
            self.hybrid_config.update({
                'fast_path_enabled': fast_path_enabled,
                'slow_path_enabled': slow_path_enabled,
                'fallback_enabled': fallback_enabled,
                'volume_adjustment': max(0.0, min(1.0, volume_adjustment))
            })
            
            logger.info(f"Hybrid feedback configured: fast={fast_path_enabled}, slow={slow_path_enabled}, "
                       f"fallback={fallback_enabled}, volume={volume_adjustment}")
            
        except Exception as e:
            logger.error(f"Error configuring hybrid feedback: {e}")
    
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
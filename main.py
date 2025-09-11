# main.py
"""
AURA Main Application

Entry point for the AURA system with continuous wake word monitoring
and command processing capabilities.
"""

import logging
import signal
import sys
import time
import argparse
import threading
from typing import Optional, Dict, Any
from pathlib import Path

from config import (
    PROJECT_NAME, PROJECT_VERSION, PROJECT_DESCRIPTION,
    LOG_LEVEL, LOG_FORMAT, LOG_FILE, DEBUG_MODE,
    validate_config, PORCUPINE_API_KEY, REASONING_API_KEY,
    VISION_API_BASE, REASONING_API_BASE
)
from orchestrator import Orchestrator
from modules.audio import AudioModule
from modules.feedback import FeedbackModule
from modules.performance import cleanup_performance_resources
from modules.performance_dashboard import create_performance_dashboard


class AURAApplication:
    """
    Main AURA Application
    
    Manages the application lifecycle including:
    - Continuous wake word monitoring
    - Command processing coordination
    - Graceful startup and shutdown
    - Resource management
    """
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """
        Initialize AURA application.
        
        Args:
            config_override: Optional configuration overrides
        """
        self.config_override = config_override or {}
        self.orchestrator: Optional[Orchestrator] = None
        self.audio_module: Optional[AudioModule] = None
        self.feedback_module: Optional[FeedbackModule] = None
        
        # Application state
        self.is_running = False
        self.is_shutting_down = False
        self.wake_word_thread: Optional[threading.Thread] = None
        self.command_processing_active = False
        self.health_monitor_thread: Optional[threading.Thread] = None
        
        # Statistics and monitoring
        self.start_time = None
        self.commands_processed = 0
        self.wake_words_detected = 0
        self.errors_count = 0
        self.last_health_check = None
        self.resource_usage = {
            'memory_mb': 0,
            'cpu_percent': 0.0,
            'threads_count': 0
        }
        
        # Resource management
        self.cleanup_handlers = []
        self.startup_checks = []
        self.health_checks = []
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        # Register default startup checks and cleanup handlers
        self._register_default_checks_and_handlers()
        
        # Add performance cleanup handler
        self.add_cleanup_handler(self._cleanup_performance_resources)
        
        logger.info(f"AURA Application initialized - Version {PROJECT_VERSION}")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format=LOG_FORMAT,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(LOG_FILE, mode='a')
            ]
        )
        
        # Set specific logger levels
        if DEBUG_MODE:
            logging.getLogger('modules').setLevel(logging.DEBUG)
            logging.getLogger('orchestrator').setLevel(logging.DEBUG)
        else:
            # Reduce noise from external libraries
            logging.getLogger('urllib3').setLevel(logging.WARNING)
            logging.getLogger('requests').setLevel(logging.WARNING)
            logging.getLogger('sounddevice').setLevel(logging.WARNING)
        
        global logger
        logger = logging.getLogger(__name__)
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Windows compatibility
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)
    
    def _register_default_checks_and_handlers(self) -> None:
        """Register default startup checks and cleanup handlers."""
        # Startup checks
        self.startup_checks.extend([
            self._check_python_version,
            self._check_required_dependencies,
            self._check_api_connectivity,
            self._check_audio_devices,
            self._check_disk_space
        ])
        
        # Health checks
        self.health_checks.extend([
            self._check_memory_usage,
            self._check_thread_health,
            self._check_module_responsiveness
        ])
        
        # Cleanup handlers
        self.cleanup_handlers.extend([
            self._cleanup_audio_resources,
            self._cleanup_orchestrator_resources,
            self._cleanup_temporary_files,
            self._cleanup_logging_handlers
        ])
    
    def add_startup_check(self, check_func: callable) -> None:
        """Add a custom startup check function."""
        self.startup_checks.append(check_func)
    
    def add_health_check(self, check_func: callable) -> None:
        """Add a custom health check function."""
        self.health_checks.append(check_func)
    
    def add_cleanup_handler(self, handler_func: callable) -> None:
        """Add a custom cleanup handler function."""
        self.cleanup_handlers.append(handler_func)
    
    def _check_python_version(self) -> tuple[bool, str]:
        """Check if Python version meets requirements."""
        import sys
        if sys.version_info < (3, 11):
            return False, f"Python 3.11+ required. Current: {sys.version}"
        return True, "Python version OK"
    
    def _check_required_dependencies(self) -> tuple[bool, str]:
        """Check if required dependencies are available."""
        required_modules = [
            'sounddevice', 'numpy', 'whisper', 'pyttsx3',
            'pydub', 'pvporcupine', 'requests', 'mss'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            return False, f"Missing required modules: {', '.join(missing_modules)}"
        return True, "All required dependencies available"
    
    def _check_api_connectivity(self) -> tuple[bool, str]:
        """Check connectivity to required APIs."""
        import requests
        
        # Check vision API (local)
        try:
            response = requests.get(f"{VISION_API_BASE}/models", timeout=5)
            if response.status_code != 200:
                return False, f"Vision API not accessible at {VISION_API_BASE}"
        except Exception as e:
            return False, f"Vision API connectivity failed: {e}"
        
        # Check reasoning API (cloud) - just check if endpoint is reachable
        try:
            response = requests.get(f"{REASONING_API_BASE}/models", 
                                  headers={"Authorization": f"Bearer {REASONING_API_KEY}"}, 
                                  timeout=10)
            # Don't require 200 status, just that we can reach the endpoint
        except Exception as e:
            logger.warning(f"Reasoning API connectivity check failed: {e}")
            # Don't fail startup for cloud API issues
        
        return True, "API connectivity OK"
    
    def _check_audio_devices(self) -> tuple[bool, str]:
        """Check if audio input/output devices are available."""
        try:
            import sounddevice as sd
            
            # Check for input devices
            input_devices = [d for d in sd.query_devices() if d['max_input_channels'] > 0]
            if not input_devices:
                return False, "No audio input devices found"
            
            # Check for output devices
            output_devices = [d for d in sd.query_devices() if d['max_output_channels'] > 0]
            if not output_devices:
                return False, "No audio output devices found"
            
            return True, f"Audio devices OK ({len(input_devices)} input, {len(output_devices)} output)"
            
        except Exception as e:
            return False, f"Audio device check failed: {e}"
    
    def _check_disk_space(self) -> tuple[bool, str]:
        """Check available disk space."""
        import shutil
        
        try:
            # Check current directory disk space
            total, used, free = shutil.disk_usage('.')
            free_gb = free / (1024**3)
            
            if free_gb < 1.0:  # Less than 1GB free
                return False, f"Low disk space: {free_gb:.1f}GB free"
            
            return True, f"Disk space OK ({free_gb:.1f}GB free)"
            
        except Exception as e:
            return False, f"Disk space check failed: {e}"
    
    def _check_memory_usage(self) -> tuple[bool, str]:
        """Check current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            self.resource_usage['memory_mb'] = memory_mb
            
            if memory_mb > 1000:  # More than 1GB
                return False, f"High memory usage: {memory_mb:.1f}MB"
            
            return True, f"Memory usage OK ({memory_mb:.1f}MB)"
            
        except ImportError:
            return True, "Memory monitoring not available (psutil not installed)"
        except Exception as e:
            return False, f"Memory check failed: {e}"
    
    def _check_thread_health(self) -> tuple[bool, str]:
        """Check thread health and count."""
        try:
            import threading
            active_threads = threading.active_count()
            self.resource_usage['threads_count'] = active_threads
            
            if active_threads > 20:  # Too many threads
                return False, f"High thread count: {active_threads}"
            
            # Check if critical threads are alive
            if self.wake_word_thread and not self.wake_word_thread.is_alive():
                return False, "Wake word monitoring thread is dead"
            
            return True, f"Thread health OK ({active_threads} active)"
            
        except Exception as e:
            return False, f"Thread health check failed: {e}"
    
    def _check_module_responsiveness(self) -> tuple[bool, str]:
        """Check if modules are responsive."""
        try:
            # Simple responsiveness check - verify modules exist and have expected methods
            if self.audio_module and not hasattr(self.audio_module, 'listen_for_wake_word'):
                return False, "Audio module not responsive"
            
            if self.orchestrator and not hasattr(self.orchestrator, 'execute_command'):
                return False, "Orchestrator not responsive"
            
            return True, "Module responsiveness OK"
            
        except Exception as e:
            return False, f"Module responsiveness check failed: {e}"
    
    def _cleanup_audio_resources(self) -> None:
        """Clean up audio-related resources."""
        try:
            if self.audio_module:
                # Stop wake word detection
                if hasattr(self.audio_module, 'is_listening_for_wake_word'):
                    self.audio_module.is_listening_for_wake_word = False
                
                # Cleanup Porcupine
                if hasattr(self.audio_module, 'porcupine') and self.audio_module.porcupine:
                    self.audio_module.porcupine.delete()
                    logger.debug("Porcupine resources cleaned up")
                
                # Stop TTS engine
                if hasattr(self.audio_module, 'tts_engine') and self.audio_module.tts_engine:
                    self.audio_module.tts_engine.stop()
                    logger.debug("TTS engine stopped")
                    
        except Exception as e:
            logger.error(f"Error cleaning up audio resources: {e}")
    
    def _cleanup_orchestrator_resources(self) -> None:
        """Clean up orchestrator-related resources."""
        try:
            if self.orchestrator:
                # Shutdown thread pool
                if hasattr(self.orchestrator, 'thread_pool'):
                    self.orchestrator.thread_pool.shutdown(wait=True)
                    logger.debug("Orchestrator thread pool shut down")
                    
        except Exception as e:
            logger.error(f"Error cleaning up orchestrator resources: {e}")
    
    def _cleanup_temporary_files(self) -> None:
        """Clean up temporary files."""
        try:
            import tempfile
            import glob
            
            # Clean up any temporary audio files
            temp_dir = tempfile.gettempdir()
            audio_temp_files = glob.glob(f"{temp_dir}/aura_*.wav")
            for file_path in audio_temp_files:
                try:
                    os.unlink(file_path)
                    logger.debug(f"Cleaned up temporary file: {file_path}")
                except Exception:
                    pass  # Ignore errors for individual files
                    
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")
    
    def _cleanup_logging_handlers(self) -> None:
        """Clean up logging handlers."""
        try:
            # Close file handlers to release file locks
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    root_logger.removeHandler(handler)
                    logger.debug("Logging file handler closed")
                    
        except Exception as e:
            logger.error(f"Error cleaning up logging handlers: {e}")
    
    def _cleanup_performance_resources(self) -> None:
        """Clean up performance-related resources."""
        try:
            # Clean up performance dashboard
            if hasattr(self, '_performance_dashboard') and self._performance_dashboard:
                self._performance_dashboard.shutdown()
                logger.debug("Performance dashboard shut down")
            
            # Clean up other performance resources
            cleanup_performance_resources()
            logger.debug("Performance resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up performance resources: {e}")
    
    def startup(self) -> bool:
        """
        Perform comprehensive application startup procedures.
        
        Returns:
            True if startup successful, False otherwise
        """
        try:
            logger.info("Starting AURA application...")
            self.start_time = time.time()
            
            # Step 1: Configuration validation
            logger.info("Step 1: Validating configuration...")
            if not validate_config():
                logger.error("Configuration validation failed")
                return False
            
            # Step 2: Run startup checks
            logger.info("Step 2: Running startup checks...")
            if not self._run_startup_checks():
                logger.error("Startup checks failed")
                return False
            
            # Step 3: Initialize core modules
            logger.info("Step 3: Initializing core modules...")
            
            # Initialize audio module first (needed for wake word detection)
            self.audio_module = AudioModule()
            
            # Initialize feedback module
            self.feedback_module = FeedbackModule(audio_module=self.audio_module)
            
            # Initialize orchestrator (this will initialize all other modules)
            self.orchestrator = Orchestrator()
            
            # Step 4: Verify all modules are ready
            logger.info("Step 4: Verifying module initialization...")
            if not self._verify_modules():
                logger.error("Module verification failed")
                return False
            
            # Step 5: Start health monitoring
            logger.info("Step 5: Starting health monitoring...")
            self._start_health_monitoring()
            
            # Step 6: Final startup confirmation
            logger.info("Step 6: Startup completed successfully")
            self.is_running = True
            
            # Provide startup feedback
            wake_word = getattr(self.audio_module, 'wake_word', 'computer')
            self.feedback_module.speak(f"{PROJECT_NAME} is ready. Say '{wake_word}' to activate.")
            
            # Log startup summary
            startup_time = time.time() - self.start_time
            logger.info(f"AURA application startup completed in {startup_time:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Startup failed: {e}")
            self.errors_count += 1
            return False
    
    def _run_startup_checks(self) -> bool:
        """
        Run all registered startup checks.
        
        Returns:
            True if all checks pass, False otherwise
        """
        logger.info(f"Running {len(self.startup_checks)} startup checks...")
        
        failed_checks = []
        for i, check_func in enumerate(self.startup_checks):
            try:
                logger.debug(f"Running startup check {i+1}/{len(self.startup_checks)}: {check_func.__name__}")
                success, message = check_func()
                
                if success:
                    logger.debug(f"✅ {check_func.__name__}: {message}")
                else:
                    logger.error(f"❌ {check_func.__name__}: {message}")
                    failed_checks.append((check_func.__name__, message))
                    
            except Exception as e:
                logger.error(f"❌ {check_func.__name__}: Exception - {e}")
                failed_checks.append((check_func.__name__, f"Exception: {e}"))
        
        if failed_checks:
            logger.error(f"Startup checks failed: {len(failed_checks)}/{len(self.startup_checks)}")
            for check_name, error_msg in failed_checks:
                logger.error(f"  - {check_name}: {error_msg}")
            return False
        
        logger.info(f"✅ All {len(self.startup_checks)} startup checks passed")
        return True
    
    def _start_health_monitoring(self) -> None:
        """Start health monitoring in a background thread."""
        if self.health_monitor_thread and self.health_monitor_thread.is_alive():
            logger.warning("Health monitoring already running")
            return
        
        self.health_monitor_thread = threading.Thread(
            target=self._health_monitoring_loop,
            name="HealthMonitor",
            daemon=True
        )
        self.health_monitor_thread.start()
        logger.info("Health monitoring started")
    
    def _health_monitoring_loop(self) -> None:
        """Health monitoring loop that runs in background."""
        logger.debug("Health monitoring loop started")
        
        while self.is_running and not self.is_shutting_down:
            try:
                # Run health checks every 60 seconds
                time.sleep(60.0)
                
                if self.is_shutting_down:
                    break
                
                self._run_health_checks()
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                self.errors_count += 1
                time.sleep(10.0)  # Brief pause before retrying
        
        logger.debug("Health monitoring loop ended")
    
    def _run_health_checks(self) -> None:
        """Run all registered health checks."""
        self.last_health_check = time.time()
        
        failed_checks = []
        for check_func in self.health_checks:
            try:
                success, message = check_func()
                
                if success:
                    logger.debug(f"Health check {check_func.__name__}: {message}")
                else:
                    logger.warning(f"Health check {check_func.__name__}: {message}")
                    failed_checks.append((check_func.__name__, message))
                    
            except Exception as e:
                logger.error(f"Health check {check_func.__name__} failed: {e}")
                failed_checks.append((check_func.__name__, f"Exception: {e}"))
                self.errors_count += 1
        
        if failed_checks:
            logger.warning(f"Health issues detected: {len(failed_checks)}/{len(self.health_checks)}")
            for check_name, error_msg in failed_checks:
                logger.warning(f"  - {check_name}: {error_msg}")
        else:
            logger.debug(f"All {len(self.health_checks)} health checks passed")
    
    def _verify_modules(self) -> bool:
        """
        Verify all modules are properly initialized.
        
        Returns:
            True if all modules are ready, False otherwise
        """
        try:
            # Check orchestrator
            if not self.orchestrator:
                logger.error("Orchestrator not initialized")
                return False
            
            # Check audio module
            if not self.audio_module:
                logger.error("Audio module not initialized")
                return False
            
            # Check feedback module
            if not self.feedback_module:
                logger.error("Feedback module not initialized")
                return False
            
            # Test wake word detection capability
            if not hasattr(self.audio_module, 'listen_for_wake_word'):
                logger.error("Wake word detection not available")
                return False
            
            logger.info("All modules verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Module verification failed: {e}")
            return False
    
    def run(self) -> None:
        """
        Main application loop with continuous wake word monitoring.
        
        This method runs the main application loop, continuously listening
        for wake words and processing commands when detected.
        """
        if not self.is_running:
            logger.error("Application not started. Call startup() first.")
            return
        
        logger.info("Starting main application loop...")
        
        try:
            # Start wake word monitoring in a separate thread
            self.wake_word_thread = threading.Thread(
                target=self._wake_word_monitoring_loop,
                name="WakeWordMonitor",
                daemon=True
            )
            self.wake_word_thread.start()
            
            # Main thread keeps application alive and handles status
            while self.is_running and not self.is_shutting_down:
                try:
                    # Sleep and check status periodically
                    time.sleep(1.0)
                    
                    # Log periodic status (every 5 minutes)
                    if int(time.time()) % 300 == 0:
                        self._log_status()
                        
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(5.0)  # Brief pause before continuing
            
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}")
        finally:
            logger.info("Main application loop ended")
    
    def _wake_word_monitoring_loop(self) -> None:
        """
        Continuous wake word monitoring loop.
        
        Runs in a separate thread to continuously monitor for wake words
        and trigger command processing when detected.
        """
        logger.info("Wake word monitoring started")
        
        while self.is_running and not self.is_shutting_down:
            try:
                # Listen for wake word (with timeout to allow periodic checks)
                wake_word_detected = self.audio_module.listen_for_wake_word(
                    timeout=5.0,  # 5 second timeout
                    provide_feedback=True
                )
                
                if wake_word_detected:
                    self.wake_words_detected += 1
                    logger.info(f"Wake word detected (#{self.wake_words_detected})")
                    
                    # Process command in main thread context
                    self._process_voice_command()
                
            except Exception as e:
                logger.error(f"Error in wake word monitoring: {e}")
                # Brief pause before retrying
                time.sleep(2.0)
        
        logger.info("Wake word monitoring stopped")
    
    def _process_voice_command(self) -> None:
        """
        Process a voice command after wake word detection.
        
        Captures voice input, converts to text, and executes the command
        through the orchestrator.
        """
        if self.command_processing_active:
            logger.warning("Command processing already active, skipping")
            return
        
        self.command_processing_active = True
        
        try:
            logger.info("Processing voice command...")
            
            # Capture voice input
            logger.debug("Listening for voice command...")
            command_text = self.audio_module.speech_to_text()
            
            if not command_text or not command_text.strip():
                logger.warning("No command text received")
                
                # Test microphone to help diagnose the issue
                try:
                    mic_test = self.audio_module.test_microphone(duration=1.0)
                    if mic_test["success"]:
                        if mic_test["volume_rms"] < 0.001:
                            logger.warning(f"Microphone is very quiet (RMS: {mic_test['volume_rms']:.4f}). Check microphone settings.")
                            self.feedback_module.speak("I can't hear you clearly. Please check your microphone settings and speak louder.")
                        else:
                            logger.info(f"Microphone is working (RMS: {mic_test['volume_rms']:.4f}). Speech may not be clear enough for transcription.")
                            self.feedback_module.speak("I can hear you but couldn't understand what you said. Please try speaking more clearly.")
                    else:
                        logger.error(f"Microphone test failed: {mic_test.get('error', 'Unknown error')}")
                        self.feedback_module.speak("I'm having trouble with the microphone. Please check your audio settings.")
                except Exception as e:
                    logger.error(f"Failed to test microphone: {e}")
                    self.feedback_module.speak("I didn't hear a command. Please try again.")
                
                return
            
            logger.info(f"Command received: '{command_text}'")
            self.commands_processed += 1
            
            # Execute command through orchestrator
            try:
                result = self.orchestrator.execute_command(command_text)
                
                # Log execution result
                if result.get('status') == 'completed':
                    logger.info(f"Command executed successfully: {command_text}")
                else:
                    logger.warning(f"Command execution had issues: {result.get('errors', [])}")
                    
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                self.feedback_module.speak("I encountered an error while executing your command.")
        
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            self.feedback_module.speak("I had trouble processing your command. Please try again.")
        
        finally:
            self.command_processing_active = False
    
    def _log_status(self) -> None:
        """Log comprehensive periodic status information."""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        # Calculate rates
        wake_word_rate = self.wake_words_detected / (uptime / 3600) if uptime > 0 else 0  # per hour
        command_rate = self.commands_processed / (uptime / 3600) if uptime > 0 else 0  # per hour
        
        # Thread status
        active_threads = threading.active_count()
        wake_word_status = "Running" if (self.wake_word_thread and self.wake_word_thread.is_alive()) else "Stopped"
        health_monitor_status = "Running" if (self.health_monitor_thread and self.health_monitor_thread.is_alive()) else "Stopped"
        
        # Get performance metrics
        try:
            # Create performance dashboard if not already created
            if not hasattr(self, '_performance_dashboard'):
                self._performance_dashboard = create_performance_dashboard()
            
            if self._performance_dashboard:
                dashboard_data = self._performance_dashboard.get_dashboard_data()
                cache_stats = dashboard_data.get('cache_performance', {})
                health_score = dashboard_data.get('overall_health_score', 0)
                
                # Log comprehensive status with performance data
                logger.info(
                    f"AURA Status Report - "
                    f"Uptime: {uptime:.1f}s, "
                    f"Wake words: {self.wake_words_detected} ({wake_word_rate:.1f}/hr), "
                    f"Commands: {self.commands_processed} ({command_rate:.1f}/hr), "
                    f"Errors: {self.errors_count}, "
                    f"Threads: {active_threads} (Wake: {wake_word_status}, Health: {health_monitor_status}), "
                    f"Memory: {self.resource_usage['memory_mb']:.1f}MB, "
                    f"Health Score: {health_score:.1f}/100"
                )
            else:
                # Fallback logging without performance metrics
                logger.info(
                    f"AURA Status Report - "
                    f"Uptime: {uptime:.1f}s, "
                    f"Wake words: {self.wake_words_detected} ({wake_word_rate:.1f}/hr), "
                    f"Commands: {self.commands_processed} ({command_rate:.1f}/hr), "
                    f"Errors: {self.errors_count}, "
                    f"Threads: {active_threads} (Wake: {wake_word_status}, Health: {health_monitor_status}), "
                    f"Memory: {self.resource_usage['memory_mb']:.1f}MB"
                )
        except Exception as e:
            # Fallback to basic status if performance metrics fail
            logger.info(
                f"AURA Status Report - "
                f"Uptime: {uptime:.1f}s, "
                f"Wake words: {self.wake_words_detected} ({wake_word_rate:.1f}/hr), "
                f"Commands: {self.commands_processed} ({command_rate:.1f}/hr), "
                f"Errors: {self.errors_count}, "
                f"Threads: {active_threads} (Wake: {wake_word_status}, Health: {health_monitor_status}), "
                f"Memory: {self.resource_usage['memory_mb']:.1f}MB"
            )
            logger.debug(f"Performance metrics unavailable: {e}")
    
    def shutdown(self) -> None:
        """
        Perform comprehensive graceful application shutdown.
        
        Stops all monitoring loops, cleans up resources, and shuts down modules.
        """
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress")
            return
        
        logger.info("Initiating AURA shutdown...")
        shutdown_start_time = time.time()
        self.is_shutting_down = True
        self.is_running = False
        
        try:
            # Step 1: Stop monitoring threads
            logger.info("Step 1: Stopping monitoring threads...")
            
            # Stop wake word monitoring
            if self.wake_word_thread and self.wake_word_thread.is_alive():
                logger.debug("Stopping wake word monitoring thread...")
                self.wake_word_thread.join(timeout=5.0)
                if self.wake_word_thread.is_alive():
                    logger.warning("Wake word thread did not stop gracefully")
            
            # Stop health monitoring
            if self.health_monitor_thread and self.health_monitor_thread.is_alive():
                logger.debug("Stopping health monitoring thread...")
                self.health_monitor_thread.join(timeout=3.0)
                if self.health_monitor_thread.is_alive():
                    logger.warning("Health monitor thread did not stop gracefully")
            
            # Step 2: Run cleanup handlers
            logger.info("Step 2: Running cleanup handlers...")
            self._run_cleanup_handlers()
            
            # Step 3: Generate shutdown report
            logger.info("Step 3: Generating shutdown report...")
            self._generate_shutdown_report(shutdown_start_time)
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self.errors_count += 1
    
    def _run_cleanup_handlers(self) -> None:
        """Run all registered cleanup handlers."""
        logger.info(f"Running {len(self.cleanup_handlers)} cleanup handlers...")
        
        for i, handler_func in enumerate(self.cleanup_handlers):
            try:
                logger.debug(f"Running cleanup handler {i+1}/{len(self.cleanup_handlers)}: {handler_func.__name__}")
                handler_func()
                logger.debug(f"✅ {handler_func.__name__} completed")
                
            except Exception as e:
                logger.error(f"❌ Cleanup handler {handler_func.__name__} failed: {e}")
                self.errors_count += 1
        
        logger.info("Cleanup handlers completed")
    
    def _generate_shutdown_report(self, shutdown_start_time: float) -> None:
        """Generate and log shutdown report."""
        shutdown_duration = time.time() - shutdown_start_time
        uptime = time.time() - self.start_time if self.start_time else 0
        
        # Calculate uptime components
        uptime_hours = int(uptime // 3600)
        uptime_minutes = int((uptime % 3600) // 60)
        uptime_seconds = int(uptime % 60)
        
        # Generate report
        report_lines = [
            "=" * 60,
            "AURA SHUTDOWN REPORT",
            "=" * 60,
            f"Shutdown Duration: {shutdown_duration:.2f}s",
            f"Total Uptime: {uptime_hours:02d}:{uptime_minutes:02d}:{uptime_seconds:02d} ({uptime:.1f}s)",
            f"Wake Words Detected: {self.wake_words_detected}",
            f"Commands Processed: {self.commands_processed}",
            f"Errors Encountered: {self.errors_count}",
            f"Last Health Check: {time.ctime(self.last_health_check) if self.last_health_check else 'Never'}",
            "Resource Usage (Last Known):",
            f"  Memory: {self.resource_usage['memory_mb']:.1f}MB",
            f"  Threads: {self.resource_usage['threads_count']}",
            "=" * 60
        ]
        
        for line in report_lines:
            logger.info(line)
        
        # Also print to console for visibility
        print("\n".join(report_lines))


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description=f"{PROJECT_NAME} - {PROJECT_DESCRIPTION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  {sys.argv[0]}                    # Run with default settings
  {sys.argv[0]} --debug           # Run with debug logging
  {sys.argv[0]} --config-check    # Check configuration and exit
  {sys.argv[0]} --version         # Show version and exit

For more information, visit: https://github.com/your-repo/aura
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f"{PROJECT_NAME} {PROJECT_VERSION}"
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--config-check',
        action='store_true',
        help='Check configuration and exit'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default=LOG_LEVEL,
        help=f'Set logging level (default: {LOG_LEVEL})'
    )
    
    parser.add_argument(
        '--log-file',
        default=LOG_FILE,
        help=f'Log file path (default: {LOG_FILE})'
    )
    
    parser.add_argument(
        '--performance',
        action='store_true',
        help='Enable performance monitoring dashboard'
    )
    
    parser.add_argument(
        '--setup-wizard',
        action='store_true',
        help='Run interactive setup wizard'
    )
    
    parser.add_argument(
        '--mock-apis',
        action='store_true',
        help='Use mock APIs for testing'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for AURA application.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Handle special commands
    if args.setup_wizard:
        try:
            from setup_wizard import SetupWizard
            wizard = SetupWizard()
            success = wizard.run()
            return 0 if success else 1
        except ImportError:
            print("❌ Setup wizard not available. Please ensure setup_wizard.py is present.")
            return 1
    
    if args.config_check:
        print(f"{PROJECT_NAME} {PROJECT_VERSION} - Configuration Check")
        print("=" * 50)
        if validate_config():
            print("✅ Configuration is valid")
            return 0
        else:
            print("❌ Configuration has errors")
            return 1
    
    # Apply argument overrides
    config_override = {}
    if args.debug:
        config_override['DEBUG_MODE'] = True
        config_override['LOG_LEVEL'] = 'DEBUG'
    if args.log_level:
        config_override['LOG_LEVEL'] = args.log_level
    if args.log_file:
        config_override['LOG_FILE'] = args.log_file
    if args.performance:
        config_override['ENABLE_PERFORMANCE_MONITORING'] = True
    if args.mock_apis:
        config_override['MOCK_APIS'] = True
    
    # Create and run application
    app = None
    try:
        print(f"{PROJECT_NAME} {PROJECT_VERSION}")
        print(f"{PROJECT_DESCRIPTION}")
        print("=" * 50)
        
        # Create application instance
        app = AURAApplication(config_override=config_override)
        
        # Startup
        if not app.startup():
            print("❌ Application startup failed")
            return 1
        
        print("✅ AURA is running. Press Ctrl+C to stop.")
        
        # Run main loop
        app.run()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Fatal error in main: {e}")
        return 1
    finally:
        if app:
            app.shutdown()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
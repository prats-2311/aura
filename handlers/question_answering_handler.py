"""
Question Answering Handler for AURA

This module implements the QuestionAnsweringHandler that provides fast-path content
comprehension for "what's on my screen" type commands. It leverages existing browser
and PDF text extraction capabilities before falling back to vision-based processing.
"""

import logging
import time
from typing import Dict, Any, Optional, TYPE_CHECKING
from handlers.base_handler import BaseHandler

if TYPE_CHECKING:
    from modules.application_detector import ApplicationInfo


class QuestionAnsweringHandler(BaseHandler):
    """
    Handler for question answering commands with fast-path optimization.
    
    This handler implements a fast path for screen content questions by:
    1. Detecting the active application (browser or PDF reader)
    2. Extracting text content using appropriate modules
    3. Summarizing content using the reasoning module
    4. Falling back to vision-based processing if needed
    
    The fast path significantly reduces response times from 10-30 seconds
    to under 5 seconds for supported applications.
    """
    
    def __init__(self, orchestrator_ref):
        """
        Initialize the QuestionAnsweringHandler.
        
        Args:
            orchestrator_ref: Reference to the main Orchestrator instance
                             for accessing shared modules and system state
        """
        super().__init__(orchestrator_ref)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("QuestionAnsweringHandler initialized with fast-path capabilities")
        
        # Initialize module references for fast access
        self._application_detector = None
        self._browser_handler = None
        self._pdf_handler = None
        self._reasoning_module = None
        self._audio_module = None
        
        # Performance tracking
        self._fast_path_attempts = 0
        self._fast_path_successes = 0
        self._fallback_count = 0
    
    def handle(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a question answering command with fast-path optimization.
        
        This method implements the main logic for processing screen content questions:
        1. Validate the command
        2. Try fast-path extraction (browser/PDF)
        3. Fall back to vision processing if needed
        4. Return results with timing and method information
        
        Args:
            command: The user command (e.g., "what's on my screen")
            context: Additional context including intent and execution metadata
            
        Returns:
            Dictionary containing execution results and metadata
        """
        # Start execution timing and logging
        start_time = self._log_execution_start(command, context)
        
        try:
            # Validate the command
            if not self._validate_command(command):
                result = self._create_error_result(
                    "I didn't receive a valid question. Please try asking again.",
                    method="validation_failed"
                )
                self._log_execution_end(start_time, result, context)
                return result
            
            self.logger.info(f"Processing question answering command: '{command[:50]}...'")
            
            # Try fast path first
            fast_path_result = self._try_fast_path(command)
            
            if fast_path_result:
                self.logger.info("Fast path successful, returning text-based result")
                self._fast_path_successes += 1
                
                result = self._create_success_result(
                    fast_path_result,
                    method="fast_path",
                    extraction_method="text_based"
                )
                self._log_execution_end(start_time, result, context)
                return result
            
            # Fast path failed, fall back to vision processing
            self.logger.info("Fast path failed, falling back to vision processing")
            self._fallback_count += 1
            
            vision_result = self._fallback_to_vision(command)
            self._log_execution_end(start_time, vision_result, context)
            return vision_result
            
        except Exception as e:
            self.logger.error(f"Unexpected error in question answering: {e}")
            result = self._create_error_result(
                "I encountered an unexpected issue while processing your question. Please try again.",
                error=e,
                method="exception_handling"
            )
            self._log_execution_end(start_time, result, context)
            return result
    
    def _try_fast_path(self, command: str) -> Optional[str]:
        """
        Attempt fast-path content extraction and summarization.
        
        This method coordinates the fast path process:
        1. Detect active application
        2. Extract content using appropriate method
        3. Summarize content using reasoning module
        4. Return summarized result or None if failed
        
        Args:
            command: The user command for context
            
        Returns:
            Summarized content string if successful, None if failed
        """
        self.logger.debug("Attempting fast path content extraction")
        self._fast_path_attempts += 1
        
        try:
            # Step 1: Detect active application
            app_info = self._detect_active_application()
            if not app_info:
                self.logger.debug("Could not detect active application, falling back to vision")
                return None
            
            # Step 2: Check if application is supported for fast path
            if not self._is_supported_application(app_info):
                self.logger.debug(f"Application {app_info.name} ({app_info.app_type.value}) not supported for fast path")
                return None
            
            # Step 3: Get appropriate extraction method
            extraction_method = self._get_extraction_method(app_info)
            if not extraction_method:
                self.logger.debug("No extraction method available for this application")
                return None
            
            # Step 4: Extract content using the determined method
            if extraction_method == "browser":
                content = self._extract_browser_content()
            elif extraction_method == "pdf":
                content = self._extract_pdf_content()
            else:
                self.logger.warning(f"Unknown extraction method: {extraction_method}")
                return None
            
            if not content:
                self.logger.debug(f"Content extraction failed using {extraction_method} method")
                return None
            
            self.logger.info(f"Successfully extracted content using {extraction_method} method ({len(content)} characters)")
            
            # Step 5: Summarize content (placeholder for now - will be implemented in later tasks)
            # For now, return the extracted content directly
            return content
            
        except Exception as e:
            self.logger.error(f"Error in fast path processing: {e}")
            return None
    
    def _extract_browser_content(self) -> Optional[str]:
        """
        Extract text content from the active browser application.
        
        This method uses the BrowserAccessibilityHandler to extract text content
        from the currently active browser window. It includes timeout handling
        and content validation.
        
        Returns:
            Extracted text content if successful, None if failed
        """
        self.logger.debug("Attempting browser content extraction")
        
        try:
            # Initialize BrowserAccessibilityHandler if not already done
            if not self._browser_handler:
                from modules.browser_accessibility import BrowserAccessibilityHandler
                self._browser_handler = BrowserAccessibilityHandler()
                self.logger.debug("BrowserAccessibilityHandler initialized")
            
            # Get current application info
            app_info = self._detect_active_application()
            if not app_info:
                self.logger.warning("Could not detect active application for browser content extraction")
                return None
            
            # Verify it's a browser application
            from modules.application_detector import ApplicationType
            if app_info.app_type != ApplicationType.WEB_BROWSER:
                self.logger.warning(f"Active application {app_info.name} is not a browser")
                return None
            
            # Set up timeout for extraction (2 second limit as per requirements)
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Browser content extraction timed out")
            
            # Store old handler to restore later
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(2)  # 2 second timeout
            
            try:
                self.logger.info(f"Extracting content from {app_info.name} ({app_info.browser_type.value if app_info.browser_type else 'unknown browser'})")
                
                # Extract text content using browser-specific method
                content = self._browser_handler.get_page_text_content(app_info)
                
                # Cancel timeout
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
                if not content:
                    self.logger.warning("Browser content extraction returned empty content")
                    return None
                
                # Validate content is substantial (>50 characters as per requirements)
                if len(content.strip()) <= 50:
                    self.logger.warning(f"Extracted content too short ({len(content.strip())} characters), likely not substantial page content")
                    return None
                
                # Additional content validation - check for meaningful content
                if not self._validate_browser_content(content):
                    self.logger.warning("Extracted content failed validation checks")
                    return None
                
                self.logger.info(f"Successfully extracted {len(content)} characters of browser content")
                return content
                
            except TimeoutError:
                # Cancel timeout and restore handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                self.logger.warning("Browser content extraction timed out after 2 seconds")
                return None
            except Exception as e:
                # Cancel timeout and restore handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                self.logger.error(f"Error during browser content extraction: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in browser content extraction setup: {e}")
            return None
    
    def _extract_pdf_content(self) -> Optional[str]:
        """
        Extract text content from the active PDF reader application.
        
        This method uses the PDFHandler to extract text content from the
        currently open PDF document. It includes timeout handling and
        content validation.
        
        Returns:
            Extracted text content if successful, None if failed
        """
        self.logger.debug("Attempting PDF content extraction")
        
        # Placeholder implementation - will be implemented in later tasks
        self.logger.debug("PDF content extraction not yet implemented")
        return None
    
    def _fallback_to_vision(self, command: str) -> Dict[str, Any]:
        """
        Fall back to vision-based question answering.
        
        This method provides seamless fallback to the existing vision-based
        approach when fast path extraction fails or is not applicable.
        The user experience should be identical to the current implementation.
        
        Args:
            command: The user command to process with vision
            
        Returns:
            Vision processing result dictionary
        """
        self.logger.info("Executing vision fallback for question answering")
        
        # Placeholder implementation - will be implemented in later tasks
        # This should call the existing vision-based question answering logic
        self.logger.debug("Vision fallback not yet implemented")
        
        return self._create_error_result(
            "I'm having trouble processing your question right now. Please try again.",
            method="vision_fallback",
            fallback_reason="not_implemented"
        )
    
    def _detect_active_application(self) -> Optional['ApplicationInfo']:
        """
        Detect the currently active application using ApplicationDetector.
        
        This method uses the ApplicationDetector module to get information about
        the currently focused application, including its type and characteristics.
        Implements comprehensive error handling with fallback mechanisms.
        
        Returns:
            ApplicationInfo object if detection succeeds, None if it fails
        """
        try:
            self.logger.debug("Detecting active application")
            
            # Initialize ApplicationDetector if not already done
            if not self._application_detector:
                from modules.application_detector import ApplicationDetector
                self._application_detector = ApplicationDetector()
                self.logger.debug("ApplicationDetector initialized")
            
            # Get active application info
            app_info = self._application_detector.get_active_application_info()
            
            if app_info:
                self.logger.info(f"Detected active application: {app_info.name} ({app_info.app_type.value})")
                if app_info.browser_type:
                    self.logger.debug(f"Browser type: {app_info.browser_type.value}")
                return app_info
            else:
                self.logger.warning("Could not detect active application")
                return None
                
        except Exception as e:
            self.logger.error(f"Error detecting active application: {e}")
            return None
    
    def _is_supported_application(self, app_info: 'ApplicationInfo') -> bool:
        """
        Check if the detected application is supported for fast-path content extraction.
        
        This method determines whether the application type supports fast text extraction
        methods (browser accessibility APIs or PDF text extraction).
        
        Args:
            app_info: ApplicationInfo object from application detection
            
        Returns:
            True if application supports fast path extraction, False otherwise
        """
        try:
            from modules.application_detector import ApplicationType
            
            # Check if application type is supported
            supported_types = [ApplicationType.WEB_BROWSER, ApplicationType.PDF_READER]
            
            if app_info.app_type in supported_types:
                self.logger.debug(f"Application type {app_info.app_type.value} is supported for fast path")
                return True
            else:
                self.logger.debug(f"Application type {app_info.app_type.value} is not supported for fast path")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking application support: {e}")
            return False
    
    def _get_extraction_method(self, app_info: 'ApplicationInfo') -> Optional[str]:
        """
        Determine the appropriate content extraction method based on application type.
        
        This method returns the extraction strategy to use based on the detected
        application type and characteristics.
        
        Args:
            app_info: ApplicationInfo object from application detection
            
        Returns:
            String indicating extraction method ("browser", "pdf") or None if unsupported
        """
        try:
            from modules.application_detector import ApplicationType
            
            if app_info.app_type == ApplicationType.WEB_BROWSER:
                self.logger.debug("Selected browser extraction method")
                return "browser"
            elif app_info.app_type == ApplicationType.PDF_READER:
                self.logger.debug("Selected PDF extraction method")
                return "pdf"
            else:
                self.logger.debug(f"No extraction method available for application type: {app_info.app_type.value}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error determining extraction method: {e}")
            return None
    
    def _validate_browser_content(self, content: str) -> bool:
        """
        Validate that extracted browser content is meaningful and substantial.
        
        This method performs quality checks on extracted content to ensure
        it represents actual page content rather than browser UI elements
        or error messages.
        
        Args:
            content: Extracted text content to validate
            
        Returns:
            True if content passes validation, False otherwise
        """
        if not content or not content.strip():
            return False
        
        content_lower = content.lower().strip()
        
        # Check for common error indicators
        error_indicators = [
            "page not found",
            "404 error",
            "access denied",
            "connection failed",
            "server error",
            "page cannot be displayed",
            "this site can't be reached",
            "no internet connection"
        ]
        
        for indicator in error_indicators:
            if indicator in content_lower:
                self.logger.debug(f"Content contains error indicator: {indicator}")
                return False
        
        # Check for browser UI noise (should be minimal in actual page content)
        ui_noise_indicators = [
            "bookmark this page",
            "add to favorites",
            "print this page",
            "share this page",
            "back to top",
            "skip to main content"
        ]
        
        ui_noise_count = sum(1 for indicator in ui_noise_indicators if indicator in content_lower)
        if ui_noise_count > 2:  # Too much UI noise
            self.logger.debug(f"Content contains too much UI noise ({ui_noise_count} indicators)")
            return False
        
        # Check for reasonable word count (substantial content should have multiple words)
        word_count = len(content.split())
        if word_count < 10:  # Less than 10 words is likely not substantial content
            self.logger.debug(f"Content has too few words ({word_count})")
            return False
        
        # Check for reasonable character-to-word ratio (detect excessive punctuation/symbols)
        char_to_word_ratio = len(content) / word_count if word_count > 0 else 0
        if char_to_word_ratio > 50:  # Likely contains too much non-text content
            self.logger.debug(f"Content has poor character-to-word ratio ({char_to_word_ratio:.1f})")
            return False
        
        self.logger.debug(f"Content validation passed: {word_count} words, {len(content)} characters")
        return True
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for monitoring and optimization.
        
        Returns:
            Dictionary containing performance metrics
        """
        total_attempts = self._fast_path_attempts
        success_rate = (self._fast_path_successes / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            "fast_path_attempts": self._fast_path_attempts,
            "fast_path_successes": self._fast_path_successes,
            "fast_path_success_rate": round(success_rate, 2),
            "fallback_count": self._fallback_count,
            "handler_name": self.__class__.__name__
        }
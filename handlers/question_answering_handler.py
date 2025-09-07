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
                self.logger.info("Fast path successful, speaking result to user")
                self._fast_path_successes += 1
                
                # Speak the summarized content to the user
                self._speak_result(fast_path_result)
                
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
        3. Validate and process content
        4. Summarize content using reasoning module
        5. Return summarized result or None if failed
        
        Args:
            command: The user command for context
            
        Returns:
            Summarized content string if successful, None if failed
        """
        self.logger.debug("Starting fast path orchestration")
        self._fast_path_attempts += 1
        fast_path_start_time = time.time()
        
        try:
            # Step 1: Detect active application
            self.logger.debug("Step 1: Detecting active application")
            app_info = self._detect_active_application()
            if not app_info:
                self.logger.debug("Could not detect active application, falling back to vision")
                return None
            
            # Step 2: Check if application is supported for fast path
            self.logger.debug("Step 2: Checking application support")
            if not self._is_supported_application(app_info):
                self.logger.debug(f"Application {app_info.name} ({app_info.app_type.value}) not supported for fast path")
                return None
            
            # Step 3: Get appropriate extraction method
            self.logger.debug("Step 3: Determining extraction method")
            extraction_method = self._get_extraction_method(app_info)
            if not extraction_method:
                self.logger.debug("No extraction method available for this application")
                return None
            
            # Step 4: Extract content using the determined method
            self.logger.debug(f"Step 4: Extracting content using {extraction_method} method")
            extraction_start_time = time.time()
            
            if extraction_method == "browser":
                content = self._extract_browser_content()
            elif extraction_method == "pdf":
                content = self._extract_pdf_content()
            else:
                self.logger.warning(f"Unknown extraction method: {extraction_method}")
                return None
            
            extraction_time = time.time() - extraction_start_time
            
            if not content:
                self.logger.debug(f"Content extraction failed using {extraction_method} method")
                return None
            
            self.logger.info(f"Successfully extracted content using {extraction_method} method ({len(content)} characters) in {extraction_time:.2f}s")
            
            # Step 5: Process and validate content
            self.logger.debug("Step 5: Processing and validating content")
            processed_content = self._process_content_for_summarization(content)
            if not processed_content:
                self.logger.debug("Content processing failed validation")
                return None
            
            # Step 6: Summarize content using reasoning module
            self.logger.debug("Step 6: Summarizing content")
            summarization_start_time = time.time()
            
            summarized_content = self._summarize_content(processed_content, command)
            if not summarized_content:
                self.logger.debug("Content summarization failed, returning processed content")
                # Fallback to processed content if summarization fails
                summarized_content = self._create_fallback_summary(processed_content)
            
            summarization_time = time.time() - summarization_start_time
            total_fast_path_time = time.time() - fast_path_start_time
            
            # Step 7: Performance monitoring and logging
            self.logger.info(f"Fast path completed successfully in {total_fast_path_time:.2f}s (extraction: {extraction_time:.2f}s, summarization: {summarization_time:.2f}s)")
            self._log_fast_path_performance(app_info, extraction_method, extraction_time, summarization_time, total_fast_path_time, len(content), len(summarized_content))
            
            return summarized_content
            
        except Exception as e:
            fast_path_time = time.time() - fast_path_start_time
            self.logger.error(f"Error in fast path processing after {fast_path_time:.2f}s: {e}")
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
        
        try:
            # Initialize PDFHandler if not already done
            if not self._pdf_handler:
                from modules.pdf_handler import PDFHandler
                self._pdf_handler = PDFHandler()
                self.logger.debug("PDFHandler initialized")
            
            # Get current application info
            app_info = self._detect_active_application()
            if not app_info:
                self.logger.warning("Could not detect active application for PDF content extraction")
                return None
            
            # Verify it's a PDF reader application
            from modules.application_detector import ApplicationType
            if app_info.app_type != ApplicationType.PDF_READER:
                self.logger.warning(f"Active application {app_info.name} is not a PDF reader")
                return None
            
            # Set up timeout for extraction (2 second limit as per requirements)
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("PDF content extraction timed out")
            
            # Store old handler to restore later
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(2)  # 2 second timeout
            
            try:
                self.logger.info(f"Extracting content from PDF reader: {app_info.name}")
                
                # Extract text content using PDFHandler
                content = self._pdf_handler.extract_text_from_open_document(app_info.name)
                
                # Cancel timeout
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
                if not content:
                    self.logger.warning("PDF content extraction returned empty content")
                    return None
                
                # Validate content is substantial (>50 characters as per requirements)
                if len(content.strip()) <= 50:
                    self.logger.warning(f"Extracted PDF content too short ({len(content.strip())} characters), likely not substantial document content")
                    return None
                
                # Additional content validation and cleaning
                cleaned_content = self._validate_and_clean_pdf_content(content)
                if not cleaned_content:
                    self.logger.warning("PDF content failed validation checks")
                    return None
                
                self.logger.info(f"Successfully extracted {len(cleaned_content)} characters of PDF content")
                return cleaned_content
                
            except TimeoutError:
                # Cancel timeout and restore handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                self.logger.warning("PDF content extraction timed out after 2 seconds")
                return None
            except Exception as e:
                # Cancel timeout and restore handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                self.logger.error(f"Error during PDF content extraction: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in PDF content extraction setup: {e}")
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
    
    def _validate_and_clean_pdf_content(self, content: str) -> Optional[str]:
        """
        Validate and clean extracted PDF content to ensure it's meaningful and substantial.
        
        This method performs quality checks and cleaning on extracted PDF content to ensure
        it represents actual document content rather than extraction artifacts or errors.
        
        Args:
            content: Raw extracted PDF text content
            
        Returns:
            Cleaned and validated content string if valid, None if content fails validation
        """
        if not content or not content.strip():
            self.logger.debug("PDF content is empty or whitespace only")
            return None
        
        # Initial cleaning
        cleaned_content = content.strip()
        content_lower = cleaned_content.lower()
        
        # Check for PDF extraction error indicators
        error_indicators = [
            "could not extract text",
            "no text found",
            "extraction failed",
            "corrupted pdf",
            "password protected",
            "encrypted document",
            "unable to read",
            "invalid pdf"
        ]
        
        for indicator in error_indicators:
            if indicator in content_lower:
                self.logger.debug(f"PDF content contains error indicator: {indicator}")
                return None
        
        # Check for excessive extraction artifacts (common in poorly formatted PDFs)
        artifact_patterns = [
            r'^\s*\d+\s*$',  # Lines with only page numbers
            r'^\s*[^\w\s]{3,}\s*$',  # Lines with only symbols/punctuation
            r'^\s*\.{3,}\s*$',  # Lines with only dots
            r'^\s*-{3,}\s*$',  # Lines with only dashes
        ]
        
        import re
        lines = cleaned_content.split('\n')
        clean_lines = []
        artifact_count = 0
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                clean_lines.append('')  # Preserve empty lines for structure
                continue
            
            # Check if line is likely an artifact
            is_artifact = False
            for pattern in artifact_patterns:
                if re.match(pattern, line_stripped):
                    is_artifact = True
                    artifact_count += 1
                    break
            
            if not is_artifact:
                clean_lines.append(line)
        
        # If too many lines are artifacts, the extraction might be poor quality
        total_non_empty_lines = len([line for line in lines if line.strip()])
        if total_non_empty_lines > 0 and artifact_count / total_non_empty_lines > 0.3:
            self.logger.debug(f"PDF content has too many extraction artifacts ({artifact_count}/{total_non_empty_lines})")
            return None
        
        # Rejoin cleaned lines
        cleaned_content = '\n'.join(clean_lines)
        
        # Remove excessive whitespace while preserving structure
        cleaned_content = re.sub(r'\n{4,}', '\n\n\n', cleaned_content)  # Limit consecutive newlines
        cleaned_content = re.sub(r'[ \t]{3,}', '  ', cleaned_content)  # Limit consecutive spaces/tabs
        
        # Final validation checks
        word_count = len(cleaned_content.split())
        if word_count < 10:  # Less than 10 words is likely not substantial content
            self.logger.debug(f"PDF content has too few words ({word_count})")
            return None
        
        # Check for reasonable character-to-word ratio
        char_to_word_ratio = len(cleaned_content) / word_count if word_count > 0 else 0
        if char_to_word_ratio > 100:  # Very high ratio suggests extraction issues
            self.logger.debug(f"PDF content has poor character-to-word ratio ({char_to_word_ratio:.1f})")
            return None
        
        # Check for minimum meaningful content (should have some alphabetic characters)
        alphabetic_chars = sum(1 for char in cleaned_content if char.isalpha())
        if alphabetic_chars < 50:  # Less than 50 alphabetic characters is likely not meaningful
            self.logger.debug(f"PDF content has too few alphabetic characters ({alphabetic_chars})")
            return None
        
        # Check for reasonable text density (alphabetic chars vs total chars)
        text_density = alphabetic_chars / len(cleaned_content) if len(cleaned_content) > 0 else 0
        if text_density < 0.3:  # Less than 30% alphabetic characters suggests poor extraction
            self.logger.debug(f"PDF content has low text density ({text_density:.2f})")
            return None
        
        self.logger.debug(f"PDF content validation passed: {word_count} words, {len(cleaned_content)} characters, {text_density:.2f} text density")
        return cleaned_content
    
    def _process_content_for_summarization(self, content: str) -> Optional[str]:
        """
        Process and prepare extracted content for summarization.
        
        This method handles content length management and ensures the content
        is suitable for summarization by the reasoning module.
        
        Args:
            content: Raw extracted content
            
        Returns:
            Processed content ready for summarization, or None if processing fails
        """
        if not content or not content.strip():
            self.logger.debug("Content is empty or whitespace only")
            return None
        
        # Limit content to 50KB as per design requirements
        MAX_CONTENT_SIZE = 50 * 1024  # 50KB
        
        if len(content) > MAX_CONTENT_SIZE:
            self.logger.info(f"Content size ({len(content)} bytes) exceeds limit, truncating to {MAX_CONTENT_SIZE} bytes")
            # Truncate at word boundary to avoid cutting words in half
            truncated = content[:MAX_CONTENT_SIZE]
            last_space = truncated.rfind(' ')
            if last_space > MAX_CONTENT_SIZE * 0.8:  # Only truncate at word boundary if it's not too far back
                content = truncated[:last_space] + "... [content truncated]"
            else:
                content = truncated + "... [content truncated]"
        
        # Basic content cleaning
        processed_content = content.strip()
        
        # Remove excessive whitespace while preserving structure
        import re
        processed_content = re.sub(r'\n{4,}', '\n\n\n', processed_content)  # Limit consecutive newlines
        processed_content = re.sub(r'[ \t]{3,}', '  ', processed_content)  # Limit consecutive spaces/tabs
        
        # Final validation
        if len(processed_content.split()) < 5:  # Less than 5 words is not worth summarizing
            self.logger.debug("Processed content has too few words for summarization")
            return None
        
        self.logger.debug(f"Content processed for summarization: {len(processed_content)} characters, {len(processed_content.split())} words")
        return processed_content
    
    def _summarize_content(self, content: str, command: str) -> Optional[str]:
        """
        Summarize extracted content using the reasoning module.
        
        This method sends the extracted and processed content to the reasoning
        module for summarization, with timeout handling and error recovery.
        
        Args:
            content: Processed content to summarize
            command: Original user command for context
            
        Returns:
            Summarized content if successful, None if failed
        """
        try:
            # Initialize ReasoningModule if not already done
            if not self._reasoning_module:
                from modules.reasoning import ReasoningModule
                self._reasoning_module = ReasoningModule()
                self.logger.debug("ReasoningModule initialized for summarization")
            
            # Set up timeout for summarization (3 second limit as per requirements)
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Content summarization timed out")
            
            # Store old handler to restore later
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(3)  # 3 second timeout
            
            try:
                # Create summarization prompt based on the user's command
                summarization_prompt = self._create_summarization_prompt(content, command)
                
                self.logger.debug(f"Sending {len(content)} characters to reasoning module for summarization")
                
                # Get summary from reasoning module
                summary_result = self._reasoning_module.process_text_query(summarization_prompt)
                
                # Cancel timeout
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
                if summary_result and summary_result.get('response'):
                    summary = summary_result['response'].strip()
                    if summary and len(summary) > 10:  # Ensure we got a meaningful summary
                        self.logger.info(f"Successfully generated summary: {len(summary)} characters")
                        return summary
                    else:
                        self.logger.warning("Reasoning module returned empty or very short summary")
                        return None
                else:
                    self.logger.warning("Reasoning module returned no response")
                    return None
                    
            except TimeoutError:
                # Cancel timeout and restore handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                self.logger.warning("Content summarization timed out after 3 seconds")
                return None
            except Exception as e:
                # Cancel timeout and restore handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                self.logger.error(f"Error during content summarization: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in summarization setup: {e}")
            return None
    
    def _create_summarization_prompt(self, content: str, command: str) -> str:
        """
        Create an appropriate summarization prompt based on the user's command.
        
        Args:
            content: Content to summarize
            command: Original user command
            
        Returns:
            Formatted prompt for the reasoning module
        """
        # Analyze the command to determine the type of summary needed
        command_lower = command.lower().strip()
        
        if any(phrase in command_lower for phrase in ["what's on", "what is on", "describe", "tell me about"]):
            prompt_type = "general_description"
        elif any(phrase in command_lower for phrase in ["summarize", "summary", "main points"]):
            prompt_type = "summary"
        elif any(phrase in command_lower for phrase in ["key", "important", "highlights"]):
            prompt_type = "key_points"
        else:
            prompt_type = "general_description"
        
        # Create appropriate prompt based on type
        if prompt_type == "summary":
            prompt = f"Please provide a concise summary of the following content:\n\n{content}"
        elif prompt_type == "key_points":
            prompt = f"Please identify the key points and important information from the following content:\n\n{content}"
        else:  # general_description
            prompt = f"Please describe what's shown in the following content in a clear and concise way:\n\n{content}"
        
        return prompt
    
    def _create_fallback_summary(self, content: str) -> str:
        """
        Create a fallback summary when the reasoning module fails.
        
        This method provides a basic summary by extracting the first few sentences
        or paragraphs from the content when full summarization fails.
        
        Args:
            content: Content to create fallback summary from
            
        Returns:
            Basic summary of the content
        """
        if not content or not content.strip():
            return "I found some content on your screen, but I'm having trouble processing it right now."
        
        # Try to extract first few sentences (up to 200 words)
        sentences = content.split('.')
        summary_parts = []
        word_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_words = len(sentence.split())
            if word_count + sentence_words > 200:  # Limit to ~200 words
                break
            
            summary_parts.append(sentence)
            word_count += sentence_words
            
            if len(summary_parts) >= 3:  # Limit to first 3 sentences
                break
        
        if summary_parts:
            fallback_summary = '. '.join(summary_parts)
            if not fallback_summary.endswith('.'):
                fallback_summary += '.'
            
            self.logger.debug(f"Created fallback summary: {len(fallback_summary)} characters")
            return f"Here's what I found on your screen: {fallback_summary}"
        else:
            # If we can't extract sentences, just return a generic message with content type
            content_length = len(content)
            word_count = len(content.split())
            return f"I found content on your screen with approximately {word_count} words ({content_length} characters), but I'm having trouble summarizing it right now."
    
    def _log_fast_path_performance(self, app_info: 'ApplicationInfo', extraction_method: str, 
                                 extraction_time: float, summarization_time: float, 
                                 total_time: float, content_length: int, summary_length: int):
        """
        Log detailed performance metrics for fast path execution.
        
        This method tracks performance data for monitoring and optimization purposes.
        
        Args:
            app_info: Information about the detected application
            extraction_method: Method used for content extraction
            extraction_time: Time taken for content extraction
            summarization_time: Time taken for summarization
            total_time: Total fast path execution time
            content_length: Length of extracted content
            summary_length: Length of final summary
        """
        # Log performance metrics
        performance_data = {
            "application_name": app_info.name,
            "application_type": app_info.app_type.value,
            "browser_type": app_info.browser_type.value if app_info.browser_type else None,
            "extraction_method": extraction_method,
            "extraction_time_seconds": round(extraction_time, 3),
            "summarization_time_seconds": round(summarization_time, 3),
            "total_time_seconds": round(total_time, 3),
            "content_length_chars": content_length,
            "summary_length_chars": summary_length,
            "compression_ratio": round(content_length / summary_length if summary_length > 0 else 0, 2),
            "meets_performance_target": total_time < 5.0  # <5 second requirement
        }
        
        # Log at info level for monitoring
        self.logger.info(f"Fast path performance: {performance_data}")
        
        # Log warning if performance target not met
        if total_time >= 5.0:
            self.logger.warning(f"Fast path exceeded 5-second target: {total_time:.2f}s for {app_info.name}")
        
        # Store performance data for aggregation (could be extended to write to metrics system)
        if not hasattr(self, '_performance_history'):
            self._performance_history = []
        
        self._performance_history.append(performance_data)
        
        # Keep only last 100 performance records to avoid memory growth
        if len(self._performance_history) > 100:
            self._performance_history = self._performance_history[-100:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for monitoring and optimization.
        
        Returns:
            Dictionary containing performance metrics
        """
        total_attempts = self._fast_path_attempts
        success_rate = (self._fast_path_successes / total_attempts * 100) if total_attempts > 0 else 0
        
        stats = {
            "fast_path_attempts": self._fast_path_attempts,
            "fast_path_successes": self._fast_path_successes,
            "fast_path_success_rate": round(success_rate, 2),
            "fallback_count": self._fallback_count,
            "handler_name": self.__class__.__name__
        }
        
        # Add performance history statistics if available
        if hasattr(self, '_performance_history') and self._performance_history:
            recent_performance = self._performance_history[-10:]  # Last 10 executions
            
            avg_total_time = sum(p['total_time_seconds'] for p in recent_performance) / len(recent_performance)
            avg_extraction_time = sum(p['extraction_time_seconds'] for p in recent_performance) / len(recent_performance)
            avg_summarization_time = sum(p['summarization_time_seconds'] for p in recent_performance) / len(recent_performance)
            
            performance_target_met = sum(1 for p in recent_performance if p['meets_performance_target'])
            performance_target_rate = (performance_target_met / len(recent_performance)) * 100
            
            stats.update({
                "recent_avg_total_time_seconds": round(avg_total_time, 3),
                "recent_avg_extraction_time_seconds": round(avg_extraction_time, 3),
                "recent_avg_summarization_time_seconds": round(avg_summarization_time, 3),
                "performance_target_met_rate": round(performance_target_rate, 2),
                "recent_performance_samples": len(recent_performance)
            })
        
        return stats
    
    def _speak_result(self, content: str):
        """
        Speak the summarized content to the user using the AudioModule.
        
        This method handles audio output of the fast path results, with error
        handling to ensure failures don't break the overall flow.
        
        Args:
            content: Content to speak to the user
        """
        try:
            # Initialize AudioModule if not already done
            if not self._audio_module:
                from modules.audio import AudioModule
                self._audio_module = AudioModule()
                self.logger.debug("AudioModule initialized for speech output")
            
            # Speak the content
            self.logger.debug(f"Speaking result to user: {len(content)} characters")
            self._audio_module.speak(content)
            
        except Exception as e:
            self.logger.error(f"Error speaking result to user: {e}")
            # Don't raise the exception - audio failure shouldn't break the handler
            # The result will still be returned in the response
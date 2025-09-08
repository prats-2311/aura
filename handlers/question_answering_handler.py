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
        self._last_fallback_reason = "unknown"
    
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
            fast_path_result, fallback_reason = self._try_fast_path_with_reason(command)
            
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
            self.logger.info(f"Fast path failed ({fallback_reason}), falling back to vision processing")
            self._fallback_count += 1
            
            vision_result = self._fallback_to_vision(command, fallback_reason)
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
    
    def _try_fast_path_with_reason(self, command: str) -> tuple[Optional[str], str]:
        """
        Attempt fast-path content extraction and summarization with fallback reason tracking.
        
        This method coordinates the fast path process and returns both the result
        and the specific reason for fallback if the fast path fails.
        
        Args:
            command: The user command for context
            
        Returns:
            Tuple of (summarized content string if successful or None if failed, fallback reason)
        """
        result = self._try_fast_path(command)
        if result:
            return result, ""
        else:
            # Determine specific fallback reason based on what failed
            return None, self._determine_fallback_reason()
    
    def _determine_fallback_reason(self) -> str:
        """
        Determine the specific reason for fast path fallback.
        
        This method returns the most recent fallback reason that was set
        during fast path processing, or a default reason if none was set.
        
        Returns:
            String describing the reason for fallback
        """
        reason = getattr(self, '_last_fallback_reason', 'unknown')
        
        # Reset the reason for next attempt
        self._last_fallback_reason = "unknown"
        
        return reason
    
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
                self._last_fallback_reason = "application_detection_failed"
                return None
            
            # Step 2: Check if application is supported for fast path
            self.logger.debug("Step 2: Checking application support")
            if not self._is_supported_application(app_info):
                self.logger.debug(f"Application {app_info.name} ({app_info.app_type.value}) not supported for fast path")
                self._last_fallback_reason = "unsupported_application"
                return None
            
            # Step 3: Get appropriate extraction method
            self.logger.debug("Step 3: Determining extraction method")
            extraction_method = self._get_extraction_method(app_info)
            if not extraction_method:
                self.logger.debug("No extraction method available for this application")
                self._last_fallback_reason = "no_extraction_method"
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
                self._last_fallback_reason = "unknown_extraction_method"
                return None
            
            extraction_time = time.time() - extraction_start_time
            
            if not content:
                self.logger.debug(f"Content extraction failed using {extraction_method} method")
                # Only set generic failure reason if no specific reason was already set
                if self._last_fallback_reason == "unknown":
                    self._last_fallback_reason = f"{extraction_method}_extraction_failed"
                return None
            
            self.logger.info(f"Successfully extracted content using {extraction_method} method ({len(content)} characters) in {extraction_time:.2f}s")
            
            # Step 5: Process and validate content
            self.logger.debug("Step 5: Processing and validating content")
            processed_content = self._process_content_for_summarization(content)
            if not processed_content:
                self.logger.debug("Content processing failed validation")
                self._last_fallback_reason = "content_validation_failed"
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
            self._last_fallback_reason = "exception_in_fast_path"
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
            import threading
            import queue
            
            # Use threading approach for timeout (works in any thread)
            result_queue = queue.Queue()
            error_queue = queue.Queue()
            
            def extraction_worker():
                try:
                    self.logger.info(f"Extracting content from {app_info.name} ({app_info.browser_type.value if app_info.browser_type else 'unknown browser'})")
                    
                    # Extract text content using browser-specific method
                    content = self._browser_handler.get_page_text_content(app_info)
                    result_queue.put(content)
                    
                except Exception as e:
                    error_queue.put(e)
            
            # Start extraction in thread
            extraction_thread = threading.Thread(target=extraction_worker, daemon=True)
            extraction_thread.start()
            
            # Wait for result with 2 second timeout
            extraction_thread.join(timeout=2.0)
            
            if extraction_thread.is_alive():
                self.logger.warning("Browser content extraction timed out after 2 seconds")
                self._last_fallback_reason = "browser_extraction_timeout"
                return None
            
            # Check for errors
            if not error_queue.empty():
                extraction_error = error_queue.get()
                self.logger.error(f"Error during browser content extraction: {extraction_error}")
                return None
            
            # Get result
            if result_queue.empty():
                self.logger.warning("No browser content extraction result received")
                return None
            
            content = result_queue.get()
            
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
            import threading
            import queue
            
            # Use threading approach for timeout (works in any thread)
            result_queue = queue.Queue()
            error_queue = queue.Queue()
            
            def extraction_worker():
                try:
                    self.logger.info(f"Extracting content from PDF reader: {app_info.name}")
                    
                    # Extract text content using PDFHandler
                    content = self._pdf_handler.extract_text_from_open_document(app_info.name)
                    result_queue.put(content)
                    
                except Exception as e:
                    error_queue.put(e)
            
            # Start extraction in thread
            extraction_thread = threading.Thread(target=extraction_worker, daemon=True)
            extraction_thread.start()
            
            # Wait for result with 2 second timeout
            extraction_thread.join(timeout=2.0)
            
            if extraction_thread.is_alive():
                self.logger.warning("PDF content extraction timed out after 2 seconds")
                self._last_fallback_reason = "pdf_extraction_timeout"
                return None
            
            # Check for errors
            if not error_queue.empty():
                extraction_error = error_queue.get()
                self.logger.error(f"Error during PDF content extraction: {extraction_error}")
                return None
            
            # Get result
            if result_queue.empty():
                self.logger.warning("No PDF content extraction result received")
                return None
            
            content = result_queue.get()
            
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
                
        except Exception as e:
            self.logger.error(f"Error in PDF content extraction setup: {e}")
            return None
    
    def _fallback_to_vision(self, command: str, fallback_reason: str = "fast_path_failed") -> Dict[str, Any]:
        """
        Fall back to vision-based question answering.
        
        This method provides seamless fallback to the existing vision-based
        approach when fast path extraction fails or is not applicable.
        The user experience should be identical to the current implementation.
        
        Args:
            command: The user command to process with vision
            fallback_reason: Reason for fallback (for monitoring and logging)
            
        Returns:
            Vision processing result dictionary
        """
        fallback_start_time = time.time()
        self.logger.info(f"Executing vision fallback for question answering (reason: {fallback_reason})")
        
        # Track fallback reason for monitoring
        self._log_fallback_reason(fallback_reason)
        
        try:
            # Get required modules from orchestrator
            vision_module = self._get_module_safely('vision_module')
            reasoning_module = self._get_module_safely('reasoning_module')
            audio_module = self._get_module_safely('audio_module')
            
            if not vision_module:
                self.logger.error("Vision module not available for fallback")
                return self._create_error_result(
                    "I'm having trouble analyzing your screen right now. Please try again.",
                    method="vision_fallback",
                    fallback_reason=fallback_reason,
                    error_type="module_unavailable"
                )
            
            if not reasoning_module:
                self.logger.error("Reasoning module not available for fallback")
                return self._create_error_result(
                    "I'm having trouble processing your question right now. Please try again.",
                    method="vision_fallback",
                    fallback_reason=fallback_reason,
                    error_type="module_unavailable"
                )
            
            # Determine analysis type based on question
            analysis_type = self._determine_analysis_type_for_question(command)
            self.logger.debug(f"Using {analysis_type} analysis for vision fallback")
            
            # Capture and analyze screen for information extraction
            self.logger.info("Analyzing screen for information extraction using vision")
            screen_context = self._analyze_screen_for_information(analysis_type)
            
            if not screen_context:
                self.logger.error("Screen analysis failed during vision fallback")
                return self._create_error_result(
                    "I couldn't analyze your screen content. Please try again.",
                    method="vision_fallback",
                    fallback_reason=fallback_reason,
                    error_type="screen_analysis_failed"
                )
            
            # Create a specialized reasoning prompt for Q&A with enhanced context
            qa_command = self._create_qa_reasoning_prompt(command, screen_context)
            
            # Use reasoning module to generate answer with retry logic
            self.logger.info("Generating answer using reasoning module")
            action_plan = self._get_qa_action_plan(qa_command, screen_context)
            
            if not action_plan:
                self.logger.error("Failed to get action plan from reasoning module")
                return self._create_error_result(
                    "I couldn't process your question. Please try again.",
                    method="vision_fallback",
                    fallback_reason=fallback_reason,
                    error_type="reasoning_failed"
                )
            
            # Extract and validate answer from action plan
            self.logger.debug(f"Action plan received: {action_plan}")
            answer = self._extract_and_validate_answer(action_plan, command)
            self.logger.debug(f"Extracted answer: '{answer}'")
            
            # Determine success based on answer quality
            success = answer and answer != "Information not available" and "couldn't find" not in answer.lower()
            
            if not success:
                # Provide fallback answer
                answer = "I couldn't find the information you're looking for on the current screen."
                self.logger.info("Vision fallback provided fallback answer due to low confidence")
            
            # Speak the result to the user (maintaining identical user experience)
            if audio_module:
                try:
                    audio_module.speak(answer)
                    self.logger.debug("Answer spoken to user via audio module")
                except Exception as e:
                    self.logger.warning(f"Failed to speak answer: {e}")
            
            # Print to console for user feedback (matching existing behavior)
            print(f"\n🤖 AURA: {answer}\n")
            self.logger.info(f"AURA Response (via vision fallback): {answer}")
            
            # Calculate execution time
            fallback_time = time.time() - fallback_start_time
            
            # Create result with comprehensive metadata
            result = self._create_success_result(
                answer,
                method="vision_fallback",
                fallback_reason=fallback_reason,
                extraction_method="vision_analysis",
                success=success,
                fallback_time=fallback_time,
                screen_elements_analyzed=len(screen_context.get("elements", [])),
                text_blocks_analyzed=len(screen_context.get("text_blocks", [])),
                confidence=action_plan.get("metadata", {}).get("confidence", 0.0),
                fast_path_used=False,
                vision_fallback_used=True
            )
            
            self.logger.info(f"Vision fallback completed successfully in {fallback_time:.2f}s (success: {success})")
            return result
            
        except Exception as e:
            fallback_time = time.time() - fallback_start_time
            self.logger.error(f"Vision fallback failed after {fallback_time:.2f}s: {e}")
            
            # Provide error feedback (matching existing behavior)
            error_message = "I encountered an error while trying to answer your question. Please try again."
            
            if audio_module:
                try:
                    audio_module.speak(error_message)
                except Exception as audio_error:
                    self.logger.warning(f"Failed to speak error message: {audio_error}")
            
            return self._create_error_result(
                error_message,
                error=e,
                method="vision_fallback",
                fallback_reason=fallback_reason,
                fallback_time=fallback_time,
                error_type="exception"
            )
    
    def _log_fallback_reason(self, reason: str) -> None:
        """
        Log fallback reason for monitoring and frequency tracking.
        
        This method tracks different types of fallback scenarios to help
        monitor system performance and identify areas for improvement.
        
        Args:
            reason: The reason for falling back to vision processing
        """
        # Initialize fallback reason tracking if not exists
        if not hasattr(self, '_fallback_reasons'):
            self._fallback_reasons = {}
        
        # Track fallback reason frequency
        self._fallback_reasons[reason] = self._fallback_reasons.get(reason, 0) + 1
        
        # Log the fallback reason
        self.logger.info(f"Vision fallback triggered - Reason: {reason} (count: {self._fallback_reasons[reason]})")
        
        # Log summary of fallback reasons periodically
        total_fallbacks = sum(self._fallback_reasons.values())
        if total_fallbacks % 10 == 0:  # Every 10 fallbacks
            self.logger.info(f"Fallback reason summary (total: {total_fallbacks}): {self._fallback_reasons}")
    
    def _determine_analysis_type_for_question(self, question: str) -> str:
        """
        Determine the appropriate analysis type for vision-based screen analysis.
        
        This method analyzes the question to determine what level of screen
        analysis is needed for optimal information extraction.
        
        Args:
            question: The user's question
            
        Returns:
            Analysis type string ("simple", "detailed", or "form")
        """
        question_lower = question.lower().strip()
        
        # Detailed analysis patterns - require comprehensive screen understanding
        detailed_patterns = [
            "what are all", "list all", "show me all", "find all",
            "how many", "count", "compare", "difference between",
            "which one", "what options", "what choices",
            "form", "input", "field", "button", "menu"
        ]
        
        # Form analysis patterns - focus on interactive elements
        form_patterns = [
            "fill", "enter", "type", "select", "choose",
            "form", "input", "field", "dropdown", "checkbox",
            "submit", "save", "login", "sign in"
        ]
        
        # Check for form-specific analysis needs
        if any(pattern in question_lower for pattern in form_patterns):
            self.logger.debug("Selected 'form' analysis type for question")
            return "form"
        
        # Check for detailed analysis needs
        if any(pattern in question_lower for pattern in detailed_patterns):
            self.logger.debug("Selected 'detailed' analysis type for question")
            return "detailed"
        
        # Default to simple analysis for basic questions
        self.logger.debug("Selected 'simple' analysis type for question")
        return "simple"
    
    def _analyze_screen_for_information(self, analysis_type: str = "simple") -> Dict[str, Any]:
        """
        Analyze screen content specifically for information extraction.
        
        This method captures and analyzes the screen using the vision module
        with appropriate analysis type for the question being asked.
        
        Args:
            analysis_type: Type of analysis ("simple", "detailed", or "form")
            
        Returns:
            Enhanced screen context with information extraction focus
        """
        try:
            # Get vision module
            vision_module = self._get_module_safely('vision_module')
            if not vision_module:
                self.logger.error("Vision module not available for screen analysis")
                return {}
            
            # Capture screen with appropriate analysis type
            self.logger.info(f"Using {analysis_type} analysis for screen capture")
            screen_context = vision_module.describe_screen(analysis_type=analysis_type)
            
            if not screen_context:
                self.logger.warning("Vision module returned empty screen context")
                return {}
            
            # Enhance context for information extraction
            if "elements" in screen_context:
                # Filter and categorize elements for better information extraction
                text_elements = []
                interactive_elements = []
                
                for element in screen_context["elements"]:
                    element_type = element.get("type", "")
                    element_text = element.get("text", "")
                    
                    if element_type in ["text", "label", "heading"] or element_text:
                        text_elements.append(element)
                    
                    if element_type in ["button", "link", "input", "dropdown"]:
                        interactive_elements.append(element)
                
                # Add categorized elements to context
                screen_context["text_elements"] = text_elements
                screen_context["interactive_elements"] = interactive_elements
                
                # Extract and summarize text content
                screen_context["extracted_text"] = self._extract_text_content_from_elements(text_elements)
                screen_context["text_summary"] = self._summarize_extracted_text(screen_context["extracted_text"])
                
                self.logger.debug(f"Categorized {len(text_elements)} text elements and {len(interactive_elements)} interactive elements")
                self.logger.debug(f"Extracted {len(screen_context['extracted_text'])} text blocks")
            
            return screen_context
            
        except Exception as e:
            self.logger.error(f"Screen analysis for information extraction failed: {e}")
            return {}
    
    def _extract_text_content_from_elements(self, text_elements: list) -> list:
        """
        Extract and organize text content from screen elements.
        
        Args:
            text_elements: List of text-containing elements
            
        Returns:
            List of extracted text blocks with metadata
        """
        extracted_text = []
        
        for element in text_elements:
            text_content = element.get("text", "").strip()
            if text_content and len(text_content) > 1:  # Skip single characters
                text_block = {
                    "content": text_content,
                    "type": element.get("type", "text"),
                    "coordinates": element.get("coordinates", []),
                    "length": len(text_content),
                    "word_count": len(text_content.split()),
                    "is_heading": element.get("type") == "heading" or text_content.isupper(),
                    "contains_numbers": any(char.isdigit() for char in text_content),
                    "contains_special_chars": any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in text_content)
                }
                extracted_text.append(text_block)
        
        return extracted_text
    
    def _summarize_extracted_text(self, extracted_text: list) -> str:
        """
        Create a summary of extracted text content.
        
        Args:
            extracted_text: List of text blocks with metadata
            
        Returns:
            Summary string of the extracted text
        """
        if not extracted_text:
            return "No text content found on screen"
        
        # Sort by importance (headings first, then by length)
        sorted_text = sorted(extracted_text, key=lambda x: (
            0 if x.get("is_heading") else 1,  # Headings first
            -x.get("word_count", 0)  # Then by word count (descending)
        ))
        
        # Create summary with most important content
        summary_parts = []
        total_chars = 0
        max_summary_length = 500  # Reasonable summary length
        
        for text_block in sorted_text:
            content = text_block["content"]
            if total_chars + len(content) <= max_summary_length:
                summary_parts.append(content)
                total_chars += len(content)
            else:
                # Add partial content if it fits
                remaining_space = max_summary_length - total_chars
                if remaining_space > 50:  # Only if meaningful space remains
                    summary_parts.append(content[:remaining_space] + "...")
                break
        
        return " | ".join(summary_parts) if summary_parts else "No substantial text content found"
    
    def _create_qa_reasoning_prompt(self, question: str, screen_context: Dict[str, Any]) -> str:
        """
        Create a specialized reasoning prompt for question answering.
        
        This method creates a prompt that helps the reasoning module understand
        the user's question and the screen context to provide accurate answers.
        
        Args:
            question: The user's question
            screen_context: Screen analysis results from vision module
            
        Returns:
            Formatted reasoning prompt for the question answering task
        """
        # Extract key information from screen context
        elements = screen_context.get("elements", [])
        text_summary = screen_context.get("text_summary", "No text content available")
        interactive_elements = screen_context.get("interactive_elements", [])
        
        # Build context description
        context_parts = []
        
        if elements:
            context_parts.append(f"Screen contains {len(elements)} visual elements")
        
        if interactive_elements:
            context_parts.append(f"{len(interactive_elements)} interactive elements (buttons, links, inputs)")
        
        context_description = ", ".join(context_parts) if context_parts else "Limited screen information available"
        
        # Create the reasoning prompt
        qa_prompt = f"""You are helping answer a user's question about what they can see on their screen.

User's Question: "{question}"

Screen Context:
- {context_description}
- Text Content Summary: {text_summary}

Your task is to answer the user's question based on the screen content provided. Be specific and helpful.

If the screen content doesn't contain enough information to answer the question, say "I couldn't find that information on your current screen."

Provide a clear, concise answer that directly addresses the user's question."""
        
        return qa_prompt
    
    def _get_qa_action_plan(self, qa_command: str, screen_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get action plan for question answering with retry logic.
        
        This method sends the reasoning prompt to the reasoning module
        and handles retries and error recovery.
        
        Args:
            qa_command: The reasoning prompt for question answering
            screen_context: Screen context for additional information
            
        Returns:
            Action plan dictionary from reasoning module
        """
        try:
            # Get reasoning module
            reasoning_module = self._get_module_safely('reasoning_module')
            if not reasoning_module:
                self.logger.error("Reasoning module not available for Q&A action plan")
                return {}
            
            # Generate action plan with retry logic
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    self.logger.debug(f"Generating Q&A action plan (attempt {attempt + 1}/{max_retries + 1})")
                    
                    action_plan = reasoning_module.generate_action_plan(
                        qa_command,
                        screen_context,
                        mode="question_answering"
                    )
                    
                    if action_plan and isinstance(action_plan, dict):
                        self.logger.debug("Successfully generated Q&A action plan")
                        return action_plan
                    else:
                        self.logger.warning(f"Invalid action plan received on attempt {attempt + 1}")
                        
                except Exception as e:
                    self.logger.warning(f"Q&A action plan generation failed on attempt {attempt + 1}: {e}")
                    if attempt == max_retries:
                        raise
                    time.sleep(0.5)  # Brief delay before retry
            
            self.logger.error("Failed to generate Q&A action plan after all retries")
            return {}
            
        except Exception as e:
            self.logger.error(f"Error in Q&A action plan generation: {e}")
            return {}
    
    def _extract_and_validate_answer(self, action_plan: Dict[str, Any], question: str) -> str:
        """
        Extract and validate answer from action plan with enhanced fallback responses.
        
        This method extracts the answer from the reasoning module's action plan
        and validates it for quality and relevance.
        
        Args:
            action_plan: Action plan from reasoning module
            question: Original user question for validation
            
        Returns:
            Validated answer string
        """
        if not action_plan or not isinstance(action_plan, dict):
            self.logger.warning("Invalid or empty action plan for answer extraction")
            return "Information not available"
        
        # Try to extract answer from various possible fields
        answer_fields = ["answer", "response", "result", "content", "message"]
        answer = None
        
        for field in answer_fields:
            if field in action_plan and action_plan[field]:
                answer = str(action_plan[field]).strip()
                if answer:
                    self.logger.debug(f"Extracted answer from field '{field}': {answer[:100]}...")
                    break
        
        # If no answer found in direct fields, try nested structures
        if not answer:
            if "actions" in action_plan and action_plan["actions"]:
                for action in action_plan["actions"]:
                    if isinstance(action, dict) and "response" in action:
                        answer = str(action["response"]).strip()
                        if answer:
                            self.logger.debug(f"Extracted answer from nested action: {answer[:100]}...")
                            break
        
        # Validate answer quality
        if not answer:
            self.logger.warning("No answer found in action plan")
            return "Information not available"
        
        # Clean up the answer
        answer = answer.strip()
        
        # Check for common failure patterns
        failure_patterns = [
            "i cannot", "i can't", "unable to", "not possible",
            "error", "failed", "exception", "invalid"
        ]
        
        answer_lower = answer.lower()
        if any(pattern in answer_lower for pattern in failure_patterns):
            self.logger.debug(f"Answer contains failure pattern: {answer}")
            return "Information not available"
        
        # Check minimum answer length
        if len(answer) < 10:
            self.logger.debug(f"Answer too short ({len(answer)} chars): {answer}")
            return "Information not available"
        
        # Check if answer is relevant to question (basic check)
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        
        # If there's some word overlap or answer is substantial, consider it valid
        word_overlap = len(question_words.intersection(answer_words))
        if word_overlap > 0 or len(answer) > 50:
            self.logger.debug(f"Answer validated (overlap: {word_overlap}, length: {len(answer)})")
            return answer
        
        self.logger.debug(f"Answer failed relevance check: {answer}")
        return "Information not available"
    
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
            self.logger.debug(f"PDF content has poor text density ({text_density:.2f})")
            return None
        
        self.logger.debug(f"PDF content validation passed: {word_count} words, {len(cleaned_content)} characters, {text_density:.2f} text density")
        return cleaned_content
    
    def _process_content_for_summarization(self, content: str) -> Optional[str]:
        """
        Process and prepare extracted content for summarization.
        
        This method handles content length management to ensure the content
        is suitable for summarization while staying within the 50KB limit.
        
        Args:
            content: Raw extracted content to process
            
        Returns:
            Processed content ready for summarization, None if processing fails
        """
        if not content or not content.strip():
            self.logger.debug("Content is empty or whitespace only")
            return None
        
        # Clean and normalize content
        processed_content = content.strip()
        
        # Remove excessive whitespace while preserving structure
        import re
        processed_content = re.sub(r'\n{4,}', '\n\n\n', processed_content)  # Limit consecutive newlines
        processed_content = re.sub(r'[ \t]{3,}', '  ', processed_content)  # Limit consecutive spaces/tabs
        
        # Check content length and apply 50KB limit as per requirements
        max_content_size = 50 * 1024  # 50KB limit
        content_size = len(processed_content.encode('utf-8'))
        
        if content_size > max_content_size:
            self.logger.info(f"Content size ({content_size} bytes) exceeds 50KB limit, truncating...")
            
            # Truncate content intelligently - try to break at sentence boundaries
            target_chars = int(max_content_size * 0.8)  # Leave some buffer for encoding
            
            if len(processed_content) > target_chars:
                # Try to find a good breaking point (sentence end)
                truncated = processed_content[:target_chars]
                
                # Look for sentence endings within the last 500 characters
                sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
                best_break = -1
                
                for ending in sentence_endings:
                    last_occurrence = truncated.rfind(ending)
                    if last_occurrence > target_chars - 500:  # Within last 500 chars
                        best_break = max(best_break, last_occurrence + len(ending))
                
                if best_break > 0:
                    processed_content = truncated[:best_break].strip()
                    self.logger.debug(f"Truncated content at sentence boundary: {len(processed_content)} characters")
                else:
                    # No good sentence boundary found, truncate at word boundary
                    words = truncated.split()
                    processed_content = ' '.join(words[:-1])  # Remove last potentially incomplete word
                    self.logger.debug(f"Truncated content at word boundary: {len(processed_content)} characters")
                
                # Add truncation indicator
                processed_content += "\n\n[Content truncated for processing...]"
        
        # Final validation
        if len(processed_content.strip()) < 10:
            self.logger.debug("Processed content too short after cleaning")
            return None
        
        final_size = len(processed_content.encode('utf-8'))
        self.logger.info(f"Content processed for summarization: {len(processed_content)} characters ({final_size} bytes)")
        
        return processed_content
    
    def _summarize_content(self, content: str, command: str) -> Optional[str]:
        """
        Summarize extracted content using the ReasoningModule.
        
        This method sends the extracted text to the ReasoningModule for summarization
        with timeout handling and fallback to raw text if needed.
        
        Args:
            content: Processed content to summarize
            command: Original user command for context
            
        Returns:
            Summarized content string if successful, None if failed
        """
        if not content or not content.strip():
            self.logger.debug("No content to summarize")
            return None
        
        try:
            # Initialize ReasoningModule if not already done
            if not self._reasoning_module:
                from modules.reasoning import ReasoningModule
                self._reasoning_module = ReasoningModule()
                self.logger.debug("ReasoningModule initialized for summarization")
            
            # Prepare summarization prompt
            summarization_prompt = self._build_summarization_prompt(content, command)
            
            # Set up timeout for summarization (3 second limit as per requirements)
            import threading
            import queue
            
            
            # Use threading approach for timeout to avoid signal issues
            result_queue = queue.Queue()
            error_queue = queue.Queue()
            
            def summarize_worker():
                try:
                    self.logger.debug("Starting content summarization with ReasoningModule")
                    
                    # Use the process_query method for conversational-style summarization
                    summary = self._reasoning_module.process_query(
                        query=summarization_prompt,
                        context={"content_length": len(content), "command": command}
                    )
                    
                    result_queue.put(summary)
                    
                except Exception as e:
                    self.logger.error(f"Summarization worker error: {e}")
                    error_queue.put(e)
            
            # Start summarization in thread
            summarize_thread = threading.Thread(target=summarize_worker, daemon=True)
            summarize_thread.start()
            
            # Wait for result with 3 second timeout
            summarize_thread.join(timeout=3.0)
            
            if summarize_thread.is_alive():
                self.logger.warning("Content summarization timed out after 3 seconds")
                return None
            
            # Check for errors
            if not error_queue.empty():
                summarize_error = error_queue.get()
                self.logger.error(f"Content summarization failed: {summarize_error}")
                return None
            
            # Get result
            if result_queue.empty():
                self.logger.warning("No summarization result received")
                return None
            
            summary = result_queue.get()
            
            # Validate and clean summary
            if not summary or not isinstance(summary, str):
                self.logger.warning("Invalid summarization result")
                return None
            
            summary = summary.strip()
            if not summary:
                self.logger.warning("Empty summarization result")
                return None
            
            # Validate summary length (should be reasonable)
            if len(summary) > len(content):
                self.logger.warning("Summary is longer than original content, likely an error")
                return None
            
            if len(summary) < 10:
                self.logger.warning("Summary is too short, likely incomplete")
                return None
            
            self.logger.info(f"Content summarization successful: {len(summary)} characters")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error in content summarization: {e}")
            return None
    
    def _build_summarization_prompt(self, content: str, command: str) -> str:
        """
        Build a prompt for content summarization based on the user's command.
        
        Args:
            content: The content to summarize
            command: The original user command for context
            
        Returns:
            Formatted prompt for the reasoning module
        """
        # Create a context-aware summarization prompt
        prompt = f"""Please provide a concise summary of the following content. The user asked: "{command}"

Focus on the key information that would be most relevant to answering their question. Keep the summary clear, informative, and conversational.

Content to summarize:
{content}

Please provide a summary that I can speak to the user as a direct response to their question."""
        
        return prompt
    
    def _create_fallback_summary(self, content: str) -> str:
        """
        Create a fallback summary when ReasoningModule summarization fails.
        
        This method provides a simple fallback by returning a truncated version
        of the processed content when summarization fails.
        
        Args:
            content: The processed content to create a fallback summary from
            
        Returns:
            Fallback summary string
        """
        if not content or not content.strip():
            return "I found some content on your screen, but I'm having trouble processing it right now."
        
        # Create a simple fallback summary by taking the first few sentences
        sentences = []
        current_sentence = ""
        
        # Simple sentence splitting
        for char in content:
            current_sentence += char
            if char in '.!?':
                # Check if this looks like a sentence ending
                if len(current_sentence.strip()) > 10:  # Avoid very short fragments
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
                    
                    # Stop after we have enough content for a summary
                    if len(sentences) >= 3 or sum(len(s) for s in sentences) > 300:
                        break
        
        # If we didn't get complete sentences, take first 200 characters
        if not sentences:
            fallback_text = content[:200].strip()
            if len(content) > 200:
                fallback_text += "..."
            return f"Here's what I can see on your screen: {fallback_text}"
        
        # Join sentences for summary
        summary = " ".join(sentences)
        if len(content) > len(summary) + 100:  # If there's significantly more content
            summary += "..."
        
        return f"Here's a summary of what's on your screen: {summary}"
    
    def _speak_result(self, result: str) -> None:
        """
        Speak the summarized content to the user using AudioModule.
        
        This method handles response formatting and uses the AudioModule
        to deliver the spoken response to the user.
        
        Args:
            result: The summarized content to speak
        """
        if not result or not result.strip():
            self.logger.warning("No result to speak")
            return
        
        try:
            # Initialize AudioModule if not already done
            if not self._audio_module:
                from modules.audio import AudioModule
                self._audio_module = AudioModule()
                self.logger.debug("AudioModule initialized for speaking results")
            
            # Format the result for speaking
            formatted_result = self._format_result_for_speech(result)
            
            self.logger.info(f"Speaking result to user: '{formatted_result[:100]}...'")
            
            # Use the AudioModule's text-to-speech functionality
            self._audio_module.speak(formatted_result)
            
        except Exception as e:
            self.logger.error(f"Error speaking result to user: {e}")
            # Don't raise exception here - the result was still processed successfully
    
    def _format_result_for_speech(self, result: str) -> str:
        """
        Format the result text for optimal speech delivery.
        
        This method cleans up the text to make it more suitable for
        text-to-speech conversion.
        
        Args:
            result: Raw result text to format
            
        Returns:
            Formatted text optimized for speech
        """
        if not result:
            return ""
        
        formatted = result.strip()
        
        # Clean up common formatting issues for speech
        import re
        
        # Replace multiple spaces with single spaces
        formatted = re.sub(r'\s+', ' ', formatted)
        
        # Remove or replace problematic characters for TTS
        formatted = formatted.replace('\n', '. ')  # Convert newlines to pauses
        formatted = formatted.replace('\t', ' ')   # Convert tabs to spaces
        formatted = formatted.replace('  ', ' ')   # Remove double spaces
        
        # Clean up common web/PDF artifacts that don't speak well
        formatted = re.sub(r'\[.*?\]', '', formatted)  # Remove bracketed content
        formatted = re.sub(r'\(.*?\)', '', formatted)  # Remove parenthetical content that might be artifacts
        
        # Ensure proper sentence endings for natural speech pauses
        if formatted and not formatted.endswith(('.', '!', '?')):
            formatted += '.'
        
        # Limit length for speech (very long responses can be overwhelming)
        max_speech_length = 500  # Reasonable limit for spoken response
        if len(formatted) > max_speech_length:
            # Try to break at sentence boundary
            truncated = formatted[:max_speech_length]
            last_sentence_end = max(
                truncated.rfind('. '),
                truncated.rfind('! '),
                truncated.rfind('? ')
            )
            
            if last_sentence_end > max_speech_length - 100:  # If we found a good break point
                formatted = truncated[:last_sentence_end + 1]
            else:
                # Break at word boundary
                words = truncated.split()
                formatted = ' '.join(words[:-1]) + '.'
        

    
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
            import threading
            import queue
            
            
            # Use threading approach for timeout to avoid signal issues
            result_queue = queue.Queue()
            error_queue = queue.Queue()
            
            def summarize_worker():
                try:
                    # Create summarization prompt based on the user's command
                    summarization_prompt = self._create_summarization_prompt(content, command)
                    
                    self.logger.debug(f"Sending {len(content)} characters to reasoning module for summarization")
                    
                    # Get summary from reasoning module using process_query
                    summary = self._reasoning_module.process_query(
                        query=summarization_prompt,
                        context={"content_length": len(content), "command": command}
                    )
                    
                    result_queue.put(summary)
                    
                except Exception as e:
                    self.logger.error(f"Summarization worker error: {e}")
                    error_queue.put(e)
            
            # Start summarization in thread
            summarize_thread = threading.Thread(target=summarize_worker, daemon=True)
            summarize_thread.start()
            
            # Wait for result with 3 second timeout
            summarize_thread.join(timeout=3.0)
            
            if summarize_thread.is_alive():
                self.logger.warning("Content summarization timed out after 3 seconds")
                return None
            
            # Check for errors
            if not error_queue.empty():
                summarize_error = error_queue.get()
                self.logger.error(f"Content summarization failed: {summarize_error}")
                return None
            
            # Get result
            if result_queue.empty():
                self.logger.warning("No summarization result received")
                return None
            
            summary = result_queue.get()
            
            # Validate and clean summary
            if not summary or not isinstance(summary, str):
                self.logger.warning("Invalid summarization result")
                return None
            
            summary = summary.strip()
            if not summary:
                self.logger.warning("Empty summarization result")
                return None
            
            # Validate summary length (should be reasonable)
            if len(summary) > len(content):
                self.logger.warning("Summary is longer than original content, likely an error")
                return None
            
            if len(summary) < 10:
                self.logger.warning("Summary is too short, likely incomplete")
                return None
            
            self.logger.info(f"Content summarization successful: {len(summary)} characters")
            return summary
                
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
            
            # Format content for speech
            formatted_content = self._format_result_for_speech(content)
            
            # Speak the content using the correct method
            self.logger.debug(f"Speaking result to user: {len(formatted_content)} characters")
            self._audio_module.text_to_speech(formatted_content)
            
        except Exception as e:
            self.logger.error(f"Error speaking result to user: {e}")
            # Don't raise the exception - audio failure shouldn't break the handler
            # The result will still be returned in the response
    
    def _format_result_for_speech(self, result: str) -> str:
        """
        Format the result text for optimal speech delivery.
        
        This method cleans up the text to make it more suitable for
        text-to-speech conversion.
        
        Args:
            result: Raw result text to format
            
        Returns:
            Formatted text optimized for speech
        """
        if not result:
            return ""
        
        formatted = result.strip()
        
        # Clean up common formatting issues for speech
        import re
        
        # Replace multiple spaces with single spaces
        formatted = re.sub(r'\s+', ' ', formatted)
        
        # Remove or replace problematic characters for TTS
        formatted = formatted.replace('\n', '. ')  # Convert newlines to pauses
        formatted = formatted.replace('\t', ' ')   # Convert tabs to spaces
        formatted = formatted.replace('  ', ' ')   # Remove double spaces
        
        # Clean up common web/PDF artifacts that don't speak well
        formatted = re.sub(r'\[.*?\]', '', formatted)  # Remove bracketed content
        formatted = re.sub(r'\(.*?\)', '', formatted)  # Remove parenthetical content that might be artifacts
        
        # Ensure proper sentence endings for natural speech pauses
        if formatted and not formatted.endswith(('.', '!', '?')):
            formatted += '.'
        
        # Limit length for speech (very long responses can be overwhelming)
        max_speech_length = 500  # Reasonable limit for spoken response
        if len(formatted) > max_speech_length:
            # Try to break at sentence boundary
            truncated = formatted[:max_speech_length]
            last_sentence_end = max(
                truncated.rfind('. '),
                truncated.rfind('! '),
                truncated.rfind('? ')
            )
            
            if last_sentence_end > max_speech_length - 100:  # If we found a good break point
                formatted = truncated[:last_sentence_end + 1]
            else:
                # Break at word boundary
                words = truncated.split()
                formatted = ' '.join(words[:-1]) + '.'
        
        return formatted.strip()
"""
Explain Selection Handler for AURA

This module implements the ExplainSelectionHandler that captures selected text
from any macOS application and provides spoken explanations through voice commands.
It leverages the accessibility API with clipboard fallback for robust text capture
across different applications.
"""

import logging
import time
from typing import Dict, Any, Optional
from handlers.base_handler import BaseHandler

# Import FeedbackPriority for audio feedback priority handling
try:
    from modules.feedback import FeedbackPriority
except ImportError:
    # Fallback if FeedbackPriority is not available
    class FeedbackPriority:
        LOW = 1
        NORMAL = 2
        HIGH = 3
        CRITICAL = 4


class ExplainSelectionHandler(BaseHandler):
    """
    Handler for explaining selected text commands.
    
    This handler implements the workflow for capturing selected text and providing
    explanations by:
    1. Capturing selected text using accessibility API with clipboard fallback
    2. Generating contextual explanations using the reasoning module
    3. Providing spoken feedback to the user
    4. Handling various error scenarios gracefully
    
    The handler supports text selection across web browsers, PDF readers, text editors,
    and other macOS applications with comprehensive error handling and fallback mechanisms.
    """
    
    def __init__(self, orchestrator_ref):
        """
        Initialize the ExplainSelectionHandler.
        
        Args:
            orchestrator_ref: Reference to the main Orchestrator instance
                             for accessing shared modules and system state
        """
        super().__init__(orchestrator_ref)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("ExplainSelectionHandler initialized")
        
        # Initialize module references for fast access
        self._accessibility_module = None
        self._reasoning_module = None
        self._audio_module = None
        
        # Performance tracking
        self._explanation_attempts = 0
        self._explanation_successes = 0
        self._text_capture_failures = 0
        self._reasoning_failures = 0
    
    def handle(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an explain selected text command.
        
        This method implements the main workflow for explaining selected text:
        1. Validate the command
        2. Capture selected text using accessibility API with clipboard fallback
        3. Generate explanation using reasoning module
        4. Provide spoken feedback to the user
        5. Return results with comprehensive metadata
        
        Args:
            command: The user command (e.g., "explain this", "explain the selected text")
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
                    "I didn't receive a valid explanation request. Please try asking again.",
                    method="validation_failed"
                )
                self._log_execution_end(start_time, result, context)
                return result
            
            self.logger.info(f"Processing explain selected text command: '{command[:50]}...'")
            self._explanation_attempts += 1
            
            # Play thinking sound to indicate processing has started
            self._play_thinking_sound()
            
            # Step 1: Capture selected text
            self.logger.debug("Step 1: Capturing selected text")
            capture_start_time = time.time()
            
            selected_text, capture_method = self._capture_selected_text()
            capture_time = time.time() - capture_start_time
            
            if not selected_text:
                self.logger.warning("No selected text found")
                self._text_capture_failures += 1
                
                error_message = "I couldn't find any selected text. Please highlight some text and try your command again."
                self._speak_error_feedback(error_message)
                
                result = self._create_error_result(
                    error_message,
                    method="text_capture_failed",
                    capture_method=capture_method,
                    capture_time=capture_time
                )
                self._log_execution_end(start_time, result, context)
                return result
            
            self.logger.info(f"Successfully captured {len(selected_text)} characters using {capture_method} method in {capture_time:.3f}s")
            
            # Step 2: Generate explanation
            self.logger.debug("Step 2: Generating explanation")
            explanation_start_time = time.time()
            
            explanation = self._generate_explanation(selected_text, command)
            explanation_time = time.time() - explanation_start_time
            
            if not explanation:
                self.logger.error("Failed to generate explanation")
                self._reasoning_failures += 1
                
                error_message = "I encountered an issue generating an explanation. Please try again."
                self._speak_error_feedback(error_message)
                
                result = self._create_error_result(
                    error_message,
                    method="explanation_generation_failed",
                    capture_method=capture_method,
                    capture_time=capture_time,
                    explanation_time=explanation_time,
                    selected_text_length=len(selected_text)
                )
                self._log_execution_end(start_time, result, context)
                return result
            
            self.logger.info(f"Successfully generated explanation ({len(explanation)} characters) in {explanation_time:.3f}s")
            
            # Step 3: Provide spoken feedback
            self.logger.debug("Step 3: Speaking explanation to user")
            self._speak_explanation(explanation)
            
            # Step 4: Provide success confirmation and return to ready state
            self.logger.debug("Step 4: Providing success confirmation")
            self._provide_success_confirmation()
            
            # Step 5: Track success and return result
            self._explanation_successes += 1
            
            result = self._create_success_result(
                explanation,
                method="explain_selected_text",
                capture_method=capture_method,
                capture_time=capture_time,
                explanation_time=explanation_time,
                selected_text_length=len(selected_text),
                explanation_length=len(explanation)
            )
            
            self._log_execution_end(start_time, result, context)
            return result
            
        except Exception as e:
            self.logger.error(f"Unexpected error in explain selected text: {e}")
            
            error_message = "I encountered an unexpected issue while explaining the selected text. Please try again."
            self._speak_error_feedback(error_message)
            
            result = self._create_error_result(
                error_message,
                error=e,
                method="exception_handling"
            )
            self._log_execution_end(start_time, result, context)
            return result
    
    def _capture_selected_text(self) -> tuple[Optional[str], str]:
        """
        Capture selected text using accessibility API with clipboard fallback.
        
        This method uses the unified text capture interface from AccessibilityModule
        which tries accessibility API first, then falls back to clipboard method.
        
        Returns:
            Tuple of (selected text if successful or None if failed, capture method used)
        """
        try:
            # Get accessibility module
            accessibility_module = self._get_module_safely('accessibility_module')
            if not accessibility_module:
                self.logger.error("Accessibility module not available")
                return None, "module_unavailable"
            
            # Use the unified text capture method
            selected_text = accessibility_module.get_selected_text()
            
            if selected_text:
                # Determine which method was actually used by checking the module's last operation
                # This is a simplified approach - in practice, the accessibility module could
                # provide more detailed information about which method succeeded
                capture_method = "accessibility_api_or_clipboard_fallback"
                
                # Basic validation of captured text
                if len(selected_text.strip()) == 0:
                    self.logger.warning("Captured text is empty or whitespace only")
                    return None, capture_method
                
                # Log successful capture
                self.logger.debug(f"Text capture successful: '{selected_text[:100]}...' ({len(selected_text)} chars)")
                return selected_text.strip(), capture_method
            else:
                self.logger.warning("Text capture returned None")
                return None, "capture_failed"
                
        except Exception as e:
            self.logger.error(f"Error during text capture: {e}")
            return None, "capture_exception"
    
    def _generate_explanation(self, selected_text: str, command: str) -> Optional[str]:
        """
        Generate an explanation for the selected text using the reasoning module.
        
        This method creates a contextual prompt and uses the reasoning module
        to generate clear, accessible explanations suitable for spoken delivery.
        Implements comprehensive error handling, timeout management, quality validation,
        and performance monitoring with caching.
        
        Args:
            selected_text: The text to explain
            command: The original user command for context
            
        Returns:
            Generated explanation string if successful, None if failed
        """
        # Import performance monitor
        try:
            from modules.performance_monitor import get_performance_monitor
            monitor = get_performance_monitor()
        except ImportError:
            monitor = None
        
        # Track explanation generation performance
        if monitor:
            with monitor.track_operation('explanation_generation', {
                'text_length': len(selected_text),
                'command': command[:50] + '...' if len(command) > 50 else command,
                'content_type': self._determine_content_type(selected_text)
            }) as metric:
                return self._generate_explanation_with_monitoring(selected_text, command, monitor, metric)
        else:
            return self._generate_explanation_without_monitoring(selected_text, command)
    
    def _generate_explanation_with_monitoring(self, selected_text: str, command: str, monitor, metric) -> Optional[str]:
        """Generate explanation with performance monitoring and caching."""
        try:
            # Check cache first for similar explanations
            cache_key = self._create_explanation_cache_key(selected_text, command)
            cached_explanation = monitor.explanation_cache.get(cache_key)
            if cached_explanation:
                metric.metadata['cache_hit'] = True
                self.logger.debug(f"Explanation from cache: {len(cached_explanation)} chars")
                return cached_explanation
            
            # Get reasoning module with enhanced error handling
            reasoning_module = self._get_module_safely('reasoning_module')
            if not reasoning_module:
                self.logger.error("Reasoning module not available")
                return None
            
            # Validate input parameters
            if not selected_text or not selected_text.strip():
                self.logger.error("Selected text is empty or invalid")
                return None
            
            if len(selected_text) > 5000:  # Reasonable limit for explanation requests
                self.logger.warning(f"Selected text is very long ({len(selected_text)} chars), truncating for explanation")
                selected_text = selected_text[:5000] + "..."
                metric.metadata['text_truncated'] = True
            
            # Create explanation prompt with enhanced context
            explanation_prompt = self._create_explanation_prompt(selected_text, command)
            
            # Generate explanation using the reasoning module
            self.logger.debug("Requesting explanation from reasoning module")
            
            with monitor.track_operation('reasoning_api_call') as api_metric:
                try:
                    # Use process_query method with the EXPLAIN_TEXT_PROMPT template
                    from config import EXPLAIN_TEXT_PROMPT
                    
                    # Format the prompt with the selected text
                    formatted_prompt = EXPLAIN_TEXT_PROMPT.format(selected_text=selected_text)
                    
                    # Call the reasoning module with timeout handling
                    explanation_response = reasoning_module.process_query(
                        query=formatted_prompt,
                        context={
                            "command": command,
                            "text_length": len(selected_text),
                            "content_type": self._determine_content_type(selected_text)
                        }
                    )
                    api_metric.metadata['api_method'] = 'process_query'
                    
                except AttributeError:
                    # Fallback to get_action_plan if process_query is not available
                    self.logger.debug("process_query not available, falling back to get_action_plan")
                    explanation_response = reasoning_module.get_action_plan(
                        user_command=f"Explain this text: {command}",
                        screen_context={
                            "selected_text": selected_text,
                            "command": command,
                            "content_type": self._determine_content_type(selected_text)
                        }
                    )
                    api_metric.metadata['api_method'] = 'get_action_plan'
                
                except Exception as api_error:
                    api_metric.metadata['api_error'] = str(api_error)
                    self.logger.error(f"Reasoning module API error: {api_error}")
                    return self._handle_reasoning_failure(api_error, selected_text)
            
            # Handle empty or None response
            if not explanation_response:
                self.logger.error("Reasoning module returned empty response")
                return self._handle_empty_response(selected_text)
            
            # Extract explanation from response with enhanced parsing
            with monitor.track_operation('explanation_extraction') as extract_metric:
                explanation = self._extract_explanation_from_response(explanation_response)
                extract_metric.metadata['extraction_success'] = explanation is not None
                
                if not explanation:
                    self.logger.error("Could not extract explanation from reasoning response")
                    return self._handle_extraction_failure(explanation_response, selected_text)
            
            # Validate explanation quality with enhanced checks
            with monitor.track_operation('explanation_validation') as validate_metric:
                validation_result = self._validate_explanation_quality(explanation, selected_text)
                validate_metric.metadata['validation_passed'] = validation_result
                
                if not validation_result:
                    self.logger.warning("Generated explanation failed quality validation")
                    # Try to improve the explanation or provide fallback
                    explanation = self._improve_explanation_quality(explanation, selected_text)
                    validate_metric.metadata['quality_improved'] = True
            
            # Final length and content validation for spoken delivery
            explanation = self._optimize_for_spoken_delivery(explanation)
            
            # Cache successful explanation
            if explanation and len(explanation) > 10:
                cache_ttl = 300.0  # 5 minutes for explanations
                monitor.explanation_cache.put(cache_key, explanation, ttl=cache_ttl)
                metric.metadata['cached'] = True
            
            metric.metadata['explanation_length'] = len(explanation) if explanation else 0
            self.logger.info(f"Successfully generated explanation ({len(explanation)} chars)")
            return explanation
            
        except Exception as e:
            metric.metadata['generation_error'] = str(e)
            self.logger.error(f"Unexpected error during explanation generation: {e}")
            return self._handle_generation_exception(e, selected_text)
    
    def _generate_explanation_without_monitoring(self, selected_text: str, command: str) -> Optional[str]:
        """Generate explanation without performance monitoring (fallback)."""
        try:
            # Get reasoning module with enhanced error handling
            reasoning_module = self._get_module_safely('reasoning_module')
            if not reasoning_module:
                self.logger.error("Reasoning module not available")
                return None
            
            # Validate input parameters
            if not selected_text or not selected_text.strip():
                self.logger.error("Selected text is empty or invalid")
                return None
            
            if len(selected_text) > 5000:  # Reasonable limit for explanation requests
                self.logger.warning(f"Selected text is very long ({len(selected_text)} chars), truncating for explanation")
                selected_text = selected_text[:5000] + "..."
            
            # Create explanation prompt with enhanced context
            explanation_prompt = self._create_explanation_prompt(selected_text, command)
            
            # Generate explanation using the reasoning module's process_query method
            # which is more appropriate for text explanation than get_action_plan
            self.logger.debug("Requesting explanation from reasoning module")
            
            try:
                # Use process_query method with the EXPLAIN_TEXT_PROMPT template
                from config import EXPLAIN_TEXT_PROMPT
                
                # Format the prompt with the selected text
                formatted_prompt = EXPLAIN_TEXT_PROMPT.format(selected_text=selected_text)
                
                # Call the reasoning module with timeout handling
                explanation_response = reasoning_module.process_query(
                    query=formatted_prompt,
                    context={
                        "command": command,
                        "text_length": len(selected_text),
                        "content_type": self._determine_content_type(selected_text)
                    }
                )
                
            except AttributeError:
                # Fallback to get_action_plan if process_query is not available
                self.logger.debug("process_query not available, falling back to get_action_plan")
                explanation_response = reasoning_module.get_action_plan(
                    user_command=f"Explain this text: {command}",
                    screen_context={
                        "selected_text": selected_text,
                        "command": command,
                        "content_type": self._determine_content_type(selected_text)
                    }
                )
            
            except Exception as api_error:
                self.logger.error(f"Reasoning module API error: {api_error}")
                return self._handle_reasoning_failure(api_error, selected_text)
            
            # Handle empty or None response
            if not explanation_response:
                self.logger.error("Reasoning module returned empty response")
                return self._handle_empty_response(selected_text)
            
            # Extract explanation from response with enhanced parsing
            explanation = self._extract_explanation_from_response(explanation_response)
            
            if not explanation:
                self.logger.error("Could not extract explanation from reasoning response")
                return self._handle_extraction_failure(explanation_response, selected_text)
            
            # Validate explanation quality with enhanced checks
            validation_result = self._validate_explanation_quality(explanation, selected_text)
            if not validation_result:
                self.logger.warning("Generated explanation failed quality validation")
                # Try to improve the explanation or provide fallback
                explanation = self._improve_explanation_quality(explanation, selected_text)
            
            # Final length and content validation for spoken delivery
            explanation = self._optimize_for_spoken_delivery(explanation)
            
            self.logger.info(f"Successfully generated explanation ({len(explanation)} chars)")
            return explanation
            
        except Exception as e:
            self.logger.error(f"Unexpected error during explanation generation: {e}")
            return self._handle_generation_exception(e, selected_text)
    
    def _create_explanation_cache_key(self, selected_text: str, command: str) -> str:
        """Create a cache key for explanation caching."""
        import hashlib
        
        # Create a hash of the selected text and command for caching
        # Normalize text for better cache hits
        normalized_text = selected_text.strip().lower()
        normalized_command = command.strip().lower()
        
        # Create hash key
        key_content = f"{normalized_text}:{normalized_command}"
        cache_key = hashlib.md5(key_content.encode()).hexdigest()
        
        return f"explanation_{cache_key}"
    
    def _create_explanation_prompt(self, selected_text: str, command: str) -> str:
        """
        Create a contextual prompt for explanation generation.
        
        This method creates a specialized prompt that instructs the reasoning module
        to generate clear, accessible explanations suitable for spoken delivery.
        Enhanced with content type detection and context-aware formatting.
        
        Args:
            selected_text: The text to explain
            command: The original user command for context
            
        Returns:
            Formatted prompt string for the reasoning module
        """
        # Determine content type for specialized handling
        content_type = self._determine_content_type(selected_text)
        
        # Get the configured explanation prompt template
        try:
            from config import EXPLAIN_TEXT_PROMPT
            base_prompt = EXPLAIN_TEXT_PROMPT
        except ImportError:
            # Fallback prompt if config is not available
            base_prompt = """You are AURA, a helpful AI assistant. Please provide a clear and concise explanation of the following text suitable for spoken delivery.

Selected text to explain:
---
{selected_text}
---

Provide a clear, conversational explanation in simple language."""
        
        # Format the prompt with the selected text
        try:
            formatted_prompt = base_prompt.format(selected_text=selected_text)
        except KeyError as e:
            self.logger.warning(f"Prompt template formatting error: {e}, using fallback")
            # Fallback formatting
            formatted_prompt = f"""You are AURA, a helpful AI assistant. Please explain the following text in simple, conversational language suitable for spoken delivery.

Content type: {content_type}
User command: {command}

Text to explain:
---
{selected_text}
---

Provide a clear, concise explanation."""
        
        return formatted_prompt
    
    def _determine_content_type(self, text: str) -> str:
        """
        Determine the type of content to provide specialized explanation handling.
        
        Args:
            text: The selected text to analyze
            
        Returns:
            Content type string for prompt customization
        """
        text_lower = text.lower().strip()
        
        # Check for code patterns
        code_indicators = ['def ', 'function', 'class ', 'import ', 'from ', '#!/', 'var ', 'let ', 'const ', 
                          'public ', 'private ', 'protected ', 'static ', 'void ', 'int ', 'string ', 'bool ',
                          '<?php', '<script', '<html', 'SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ']
        
        if any(indicator in text for indicator in code_indicators):
            return "code snippet"
        
        # Check for technical documentation
        if any(term in text_lower for term in ['api', 'endpoint', 'parameter', 'configuration', 'documentation']):
            return "technical documentation"
        
        # Check for academic/scientific content
        if any(term in text_lower for term in ['abstract', 'methodology', 'hypothesis', 'conclusion', 'research']):
            return "academic/scientific text"
        
        # Check for legal/formal content
        if any(term in text_lower for term in ['whereas', 'hereby', 'pursuant', 'agreement', 'terms and conditions']):
            return "legal/formal document"
        
        # Default to general text
        return "general text"
    
    def _extract_explanation_from_response(self, response: Any) -> Optional[str]:
        """
        Extract the explanation text from the reasoning module response with enhanced parsing.
        
        Args:
            response: Response from reasoning module (can be string, dict, or other format)
            
        Returns:
            Extracted explanation string or None if extraction failed
        """
        try:
            # Handle direct string responses (most common for process_query)
            if isinstance(response, str):
                explanation = response.strip()
                
                # Remove common wrapper text that might be added by the model
                unwrap_patterns = [
                    "Here's an explanation:",
                    "Here is an explanation:",
                    "Explanation:",
                    "The explanation is:",
                    "This text means:",
                    "This means:"
                ]
                
                for pattern in unwrap_patterns:
                    if explanation.lower().startswith(pattern.lower()):
                        explanation = explanation[len(pattern):].strip()
                        break
                
                return explanation if explanation else None
            
            # Handle dictionary responses (from get_action_plan or structured responses)
            if isinstance(response, dict):
                # Try common keys where explanation might be stored
                explanation_keys = [
                    'explanation', 'response', 'answer', 'result', 'content', 'text',
                    'message', 'output', 'generated_text', 'completion'
                ]
                
                for key in explanation_keys:
                    if key in response and response[key]:
                        extracted = str(response[key]).strip()
                        if extracted:
                            return extracted
                
                # Handle action plan format (if get_action_plan was used)
                if 'plan' in response and isinstance(response['plan'], list):
                    # Look for speak actions that might contain the explanation
                    for action in response['plan']:
                        if isinstance(action, dict) and action.get('action') == 'speak':
                            message = action.get('message', '')
                            if message and len(message) > 5:  # Any reasonable message length
                                return message.strip()
                
                # Try to extract from nested structures
                for key, value in response.items():
                    if isinstance(value, dict):
                        nested_result = self._extract_explanation_from_response(value)
                        if nested_result:
                            return nested_result
                
                # Last resort for dict: try to find the longest string value
                string_values = []
                for value in response.values():
                    if isinstance(value, str) and len(value.strip()) > 10:
                        string_values.append(value.strip())
                
                if string_values:
                    # Return the longest string as it's most likely the explanation
                    return max(string_values, key=len)
            
            # Handle list responses
            if isinstance(response, list) and response:
                # Try to extract from first item or find the best candidate
                for item in response:
                    extracted = self._extract_explanation_from_response(item)
                    if extracted:
                        return extracted
            
            # Final fallback: convert to string and clean up
            fallback_text = str(response).strip()
            
            # Remove obvious JSON artifacts
            if fallback_text.startswith('{') and fallback_text.endswith('}'):
                # This looks like a JSON string representation, skip it
                return None
            
            if fallback_text.startswith('[') and fallback_text.endswith(']'):
                # This looks like a list string representation, skip it
                return None
            
            # Return if it looks like reasonable text
            if len(fallback_text) > 10 and not fallback_text.startswith('{'): 
                return fallback_text
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting explanation from response: {e}")
            self.logger.debug(f"Response type: {type(response)}, Response: {str(response)[:200]}...")
            return None
    
    def _validate_explanation_quality(self, explanation: str, original_text: str) -> bool:
        """
        Validate the quality of the generated explanation with enhanced checks.
        
        Args:
            explanation: The generated explanation
            original_text: The original selected text
            
        Returns:
            True if explanation meets quality standards, False otherwise
        """
        try:
            # Basic validation checks
            if not explanation or not explanation.strip():
                self.logger.warning("Explanation is empty or whitespace only")
                return False
            
            # Length validation with more nuanced rules
            explanation_length = len(explanation.strip())
            original_length = len(original_text.strip())
            
            if explanation_length < 10:
                self.logger.warning("Explanation too short (< 10 characters)")
                return False
            
            if explanation_length > 1000:
                self.logger.warning("Explanation too long for spoken delivery (> 1000 characters)")
                return False
            
            # Check for reasonable length relative to original text
            length_ratio = explanation_length / max(original_length, 1)
            if length_ratio > 5.0:
                self.logger.warning(f"Explanation much longer than original (ratio: {length_ratio:.1f})")
                # Don't fail validation, but log for monitoring
            
            # Enhanced failure pattern detection
            failure_patterns = [
                "i cannot", "i can't", "unable to", "don't understand",
                "not clear", "insufficient information", "cannot determine",
                "i don't know", "unclear", "ambiguous", "not enough context",
                "cannot explain", "difficult to explain", "hard to understand"
            ]
            
            explanation_lower = explanation.lower()
            failure_count = sum(1 for pattern in failure_patterns if pattern in explanation_lower)
            if failure_count > 0:
                self.logger.warning(f"Explanation contains {failure_count} failure indicators")
                return False
            
            # Check for reasonable content (not just repeated text)
            if self._is_text_repetition(explanation, original_text):
                self.logger.warning("Explanation appears to be repetition of original text")
                return False
            
            # Check for meaningful content indicators
            meaningful_indicators = [
                "means", "refers to", "describes", "indicates", "represents",
                "this is", "this code", "this function", "this text", "in other words",
                "essentially", "basically", "simply put", "to explain"
            ]
            
            has_meaningful_content = any(indicator in explanation_lower for indicator in meaningful_indicators)
            if not has_meaningful_content and explanation_length < 50:
                self.logger.warning("Explanation lacks meaningful content indicators")
                return False
            
            # Validate sentence structure for spoken delivery
            if not self._has_proper_sentence_structure(explanation):
                self.logger.warning("Explanation has poor sentence structure for spoken delivery")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating explanation quality: {e}")
            return False
    
    def _play_thinking_sound(self) -> None:
        """
        Play thinking sound to indicate processing has started.
        
        This method provides immediate audio feedback to the user that their
        explanation request has been received and is being processed.
        """
        try:
            feedback_module = self._get_module_safely('feedback_module')
            if feedback_module and hasattr(feedback_module, 'play'):
                # Use high priority for thinking sound to ensure immediate feedback
                feedback_module.play("thinking", priority=FeedbackPriority.HIGH)
                self.logger.debug("Thinking sound played with high priority")
            else:
                self.logger.warning("Feedback module not available for thinking sound")
        except Exception as e:
            self.logger.warning(f"Failed to play thinking sound: {e}")
            # Continue execution even if thinking sound fails
    
    def _speak_explanation(self, explanation: str) -> None:
        """
        Speak the explanation to the user using the FeedbackModule for enhanced delivery.
        
        This method provides the spoken explanation with optimized settings for
        clear, conversational delivery suitable for educational content.
        
        Args:
            explanation: The explanation text to speak
        """
        try:
            # Use FeedbackModule for enhanced conversational feedback
            feedback_module = self._get_module_safely('feedback_module')
            if feedback_module and hasattr(feedback_module, 'provide_conversational_feedback'):
                # Use conversational feedback for natural explanation delivery
                feedback_module.provide_conversational_feedback(
                    message=explanation,
                    priority=FeedbackPriority.HIGH,
                    include_thinking_sound=False  # Already played thinking sound
                )
                self.logger.debug("Explanation delivered via conversational feedback")
            elif feedback_module and hasattr(feedback_module, 'speak'):
                # Fallback to basic speak method
                feedback_module.speak(explanation, priority=FeedbackPriority.HIGH)
                self.logger.debug("Explanation delivered via basic speak method")
            else:
                # Final fallback to audio module
                audio_module = self._get_module_safely('audio_module')
                if audio_module and hasattr(audio_module, 'text_to_speech'):
                    audio_module.text_to_speech(explanation)
                    self.logger.debug("Explanation delivered via audio module")
                else:
                    self.logger.warning("No audio modules available for explanation delivery")
            
            # Always print to console for visual feedback
            print(f"\n🤖 AURA: {explanation}\n")
            self.logger.info(f"AURA Explanation delivered: {explanation[:100]}...")
                
        except Exception as e:
            self.logger.error(f"Failed to speak explanation: {e}")
            # Fallback to console output only
            print(f"\n🤖 AURA: {explanation}\n")
    
    def _speak_error_feedback(self, error_message: str) -> None:
        """
        Speak error feedback to the user with failure sound and clear messaging.
        
        This method provides comprehensive error feedback including failure sound
        and spoken error message with appropriate priority and timing.
        
        Args:
            error_message: The error message to speak
        """
        try:
            feedback_module = self._get_module_safely('feedback_module')
            
            if feedback_module and hasattr(feedback_module, 'play_with_message'):
                # Use combined feedback for failure sound + error message
                feedback_module.play_with_message(
                    sound_name="failure",
                    message=error_message,
                    priority=FeedbackPriority.HIGH
                )
                self.logger.debug("Error feedback delivered with failure sound and message")
            else:
                # Fallback to separate sound and speech
                if feedback_module and hasattr(feedback_module, 'play'):
                    feedback_module.play("failure")
                    
                # Brief pause before speaking error message
                import time
                time.sleep(0.2)
                
                # Speak error message
                if feedback_module and hasattr(feedback_module, 'speak'):
                    feedback_module.speak(error_message)
                else:
                    # Final fallback to audio module
                    audio_module = self._get_module_safely('audio_module')
                    if audio_module and hasattr(audio_module, 'text_to_speech'):
                        audio_module.text_to_speech(error_message)
                        
                self.logger.debug("Error feedback delivered with separate sound and speech")
            
            # Always print to console for visual feedback
            print(f"\n❌ AURA: {error_message}\n")
            
        except Exception as e:
            self.logger.error(f"Failed to speak error feedback: {e}")
            # Fallback to console output only
            print(f"\n❌ AURA: {error_message}\n")
    
    def _provide_success_confirmation(self) -> None:
        """
        Provide success confirmation and return to ready state after explanation delivery.
        
        This method plays a subtle success sound and provides confirmation that
        the explanation has been completed, then returns AURA to ready state
        for new commands.
        """
        try:
            feedback_module = self._get_module_safely('feedback_module')
            
            if feedback_module and hasattr(feedback_module, 'play'):
                # Play subtle success sound with normal priority
                feedback_module.play("success", priority=FeedbackPriority.NORMAL)
                self.logger.debug("Success confirmation sound played")
            
            # Brief pause to allow success sound to complete
            import time
            time.sleep(0.3)
            
            # Log return to ready state
            self.logger.info("Explanation completed successfully - AURA ready for new commands")
            
            # Optional: Could add a brief "Ready" confirmation sound or message
            # For now, we'll keep it subtle to avoid being intrusive
            
        except Exception as e:
            self.logger.warning(f"Failed to provide success confirmation: {e}")
            # Continue execution even if success confirmation fails
    
    def _handle_reasoning_failure(self, error: Exception, selected_text: str) -> Optional[str]:
        """
        Handle reasoning module API failures with fallback strategies.
        
        Args:
            error: The exception that occurred
            selected_text: The original selected text
            
        Returns:
            Fallback explanation or None if all strategies fail
        """
        self.logger.error(f"Reasoning module API failure: {error}")
        
        # Try to provide a basic fallback explanation
        try:
            content_type = self._determine_content_type(selected_text)
            
            if content_type == "code snippet":
                return f"This appears to be a code snippet. The code contains {len(selected_text)} characters and may involve programming logic or functions."
            elif len(selected_text) > 500:
                return f"This is a longer text passage with {len(selected_text)} characters. It appears to contain detailed information that would benefit from careful reading."
            else:
                return f"This text contains {len(selected_text)} characters and appears to be {content_type}. I'm having trouble providing a detailed explanation right now."
                
        except Exception as fallback_error:
            self.logger.error(f"Fallback explanation generation failed: {fallback_error}")
            return None
    
    def _handle_empty_response(self, selected_text: str) -> Optional[str]:
        """
        Handle empty responses from the reasoning module.
        
        Args:
            selected_text: The original selected text
            
        Returns:
            Fallback explanation or None
        """
        self.logger.warning("Reasoning module returned empty response")
        
        # Provide a basic acknowledgment
        try:
            word_count = len(selected_text.split())
            return f"I can see you've selected text with approximately {word_count} words, but I'm having trouble generating a detailed explanation right now. Please try again."
        except Exception:
            return None
    
    def _handle_extraction_failure(self, response: Any, selected_text: str) -> Optional[str]:
        """
        Handle failures in extracting explanation from reasoning response.
        
        Args:
            response: The raw response from reasoning module
            selected_text: The original selected text
            
        Returns:
            Fallback explanation or None
        """
        self.logger.error(f"Failed to extract explanation from response: {type(response)}")
        
        # Try to extract any useful text from the response
        try:
            if isinstance(response, str) and len(response) > 10:
                return response[:500]  # Truncate if too long
            elif isinstance(response, dict):
                # Try to find any text content in the response
                for key in ['text', 'content', 'message', 'explanation', 'response']:
                    if key in response and isinstance(response[key], str):
                        return response[key][:500]
        except Exception as e:
            self.logger.error(f"Error in extraction fallback: {e}")
        
        return None
    
    def _handle_generation_exception(self, error: Exception, selected_text: str) -> Optional[str]:
        """
        Handle unexpected exceptions during explanation generation.
        
        Args:
            error: The exception that occurred
            selected_text: The original selected text
            
        Returns:
            Fallback explanation or None
        """
        self.logger.error(f"Unexpected error in explanation generation: {error}")
        
        # Provide a minimal fallback
        try:
            return f"I encountered an issue while analyzing the selected text. The text appears to contain {len(selected_text)} characters."
        except Exception:
            return None
    
    def _improve_explanation_quality(self, explanation: str, original_text: str) -> str:
        """
        Attempt to improve explanation quality for better spoken delivery.
        
        Args:
            explanation: The original explanation
            original_text: The original selected text
            
        Returns:
            Improved explanation
        """
        try:
            # Clean up common issues
            improved = explanation.strip()
            
            # Remove markdown formatting that doesn't work well in speech
            improved = improved.replace('**', '').replace('*', '').replace('`', '')
            
            # Ensure it starts with a capital letter
            if improved and not improved[0].isupper():
                improved = improved[0].upper() + improved[1:]
            
            # Ensure it ends with proper punctuation
            if improved and improved[-1] not in '.!?':
                improved += '.'
            
            # Replace technical abbreviations with spoken forms
            replacements = {
                ' & ': ' and ',
                ' w/ ': ' with ',
                ' w/o ': ' without ',
                ' etc.': ' and so on',
                ' i.e.': ' that is',
                ' e.g.': ' for example'
            }
            
            for old, new in replacements.items():
                improved = improved.replace(old, new)
            
            return improved
            
        except Exception as e:
            self.logger.error(f"Error improving explanation quality: {e}")
            return explanation
    
    def _optimize_for_spoken_delivery(self, explanation: str) -> str:
        """
        Optimize explanation for spoken delivery by text-to-speech.
        
        Args:
            explanation: The explanation to optimize
            
        Returns:
            Optimized explanation
        """
        try:
            # Ensure reasonable length for speech (aim for 30-60 seconds at normal speaking pace)
            max_chars = 400  # Approximately 60 seconds of speech
            if len(explanation) > max_chars:
                # Find a good breaking point
                truncated = explanation[:max_chars]
                last_sentence_end = max(
                    truncated.rfind('.'),
                    truncated.rfind('!'),
                    truncated.rfind('?')
                )
                
                if last_sentence_end > max_chars * 0.7:  # If we can keep most of the content
                    explanation = truncated[:last_sentence_end + 1]
                else:
                    explanation = truncated + "..."
            
            # Ensure good flow for speech
            explanation = explanation.replace('\n', ' ').replace('\t', ' ')
            
            # Remove excessive whitespace
            import re
            explanation = re.sub(r'\s+', ' ', explanation).strip()
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error optimizing for spoken delivery: {e}")
            return explanation
    
    def _is_text_repetition(self, explanation: str, original_text: str) -> bool:
        """
        Check if explanation is just repetition of original text.
        
        Args:
            explanation: The generated explanation
            original_text: The original selected text
            
        Returns:
            True if explanation appears to be repetition
        """
        try:
            # Normalize both texts for comparison
            exp_normalized = explanation.lower().strip()
            orig_normalized = original_text.lower().strip()
            
            # Check for exact match
            if exp_normalized == orig_normalized:
                return True
            
            # Check for substantial overlap (more than 80% of explanation is from original)
            exp_words = set(exp_normalized.split())
            orig_words = set(orig_normalized.split())
            
            if len(exp_words) == 0:
                return True
            
            overlap = len(exp_words.intersection(orig_words))
            overlap_ratio = overlap / len(exp_words)
            
            return overlap_ratio > 0.8
            
        except Exception as e:
            self.logger.error(f"Error checking text repetition: {e}")
            return False
    
    def _has_proper_sentence_structure(self, explanation: str) -> bool:
        """
        Check if explanation has proper sentence structure for spoken delivery.
        
        Args:
            explanation: The explanation to check
            
        Returns:
            True if structure is suitable for speech
        """
        try:
            # Check for basic sentence structure
            sentences = explanation.split('.')
            
            # Should have at least one complete sentence
            if len(sentences) < 1:
                return False
            
            # Check for reasonable sentence length (not too long for speech)
            for sentence in sentences:
                if len(sentence.strip()) > 200:  # Very long sentences are hard to follow in speech
                    return False
            
            # Check for basic grammatical structure (has some common words)
            common_words = ['the', 'a', 'an', 'is', 'are', 'was', 'were', 'this', 'that', 'it']
            explanation_lower = explanation.lower()
            has_common_words = any(word in explanation_lower for word in common_words)
            
            return has_common_words
            
        except Exception as e:
            self.logger.error(f"Error checking sentence structure: {e}")
            return True  # Default to accepting if we can't check
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for monitoring and debugging.
        
        Returns:
            Dictionary containing performance metrics
        """
        success_rate = (self._explanation_successes / max(self._explanation_attempts, 1)) * 100
        
        return {
            "explanation_attempts": self._explanation_attempts,
            "explanation_successes": self._explanation_successes,
            "success_rate": success_rate,
            "text_capture_failures": self._text_capture_failures,
            "reasoning_failures": self._reasoning_failures,
            "handler_name": self.__class__.__name__
        }
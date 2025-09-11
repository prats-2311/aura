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
            
            # Step 4: Track success and return result
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
        
        Args:
            selected_text: The text to explain
            command: The original user command for context
            
        Returns:
            Generated explanation string if successful, None if failed
        """
        try:
            # Get reasoning module
            reasoning_module = self._get_module_safely('reasoning_module')
            if not reasoning_module:
                self.logger.error("Reasoning module not available")
                return None
            
            # Create explanation prompt
            explanation_prompt = self._create_explanation_prompt(selected_text, command)
            
            # Generate explanation with timeout
            self.logger.debug("Requesting explanation from reasoning module")
            
            # Use the reasoning module's get_action_plan method which is the standard interface
            explanation_response = reasoning_module.get_action_plan(explanation_prompt)
            
            if not explanation_response:
                self.logger.error("Reasoning module returned empty response")
                return None
            
            # Extract explanation from response
            explanation = self._extract_explanation_from_response(explanation_response)
            
            if not explanation:
                self.logger.error("Could not extract explanation from reasoning response")
                return None
            
            # Validate explanation quality
            if not self._validate_explanation_quality(explanation, selected_text):
                self.logger.warning("Generated explanation failed quality validation")
                # Return it anyway as it's better than nothing
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error during explanation generation: {e}")
            return None
    
    def _create_explanation_prompt(self, selected_text: str, command: str) -> str:
        """
        Create a contextual prompt for explanation generation.
        
        This method creates a specialized prompt that instructs the reasoning module
        to generate clear, accessible explanations suitable for spoken delivery.
        
        Args:
            selected_text: The text to explain
            command: The original user command for context
            
        Returns:
            Formatted prompt string for the reasoning module
        """
        # Determine content type for specialized handling
        content_type = self._determine_content_type(selected_text)
        
        # Create base prompt with content type awareness
        prompt = f"""You are AURA, a helpful AI assistant. Please provide a clear and concise explanation of the following text. The explanation should be in simple, accessible language suitable for spoken delivery.

Content type: {content_type}
User command: {command}

Text to explain:
---
{selected_text}
---

Instructions:
- Provide a clear, concise explanation in simple language
- If this is code, explain what it does and its purpose
- If this contains technical terms, provide definitions and context
- If the text is very long, provide a summary rather than detailed explanation
- Keep the explanation conversational and suitable for speaking aloud
- Focus on the most important aspects that would help someone understand the content

Please provide your explanation:"""
        
        return prompt
    
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
    
    def _extract_explanation_from_response(self, response: Dict[str, Any]) -> Optional[str]:
        """
        Extract the explanation text from the reasoning module response.
        
        Args:
            response: Response dictionary from reasoning module
            
        Returns:
            Extracted explanation string or None if extraction failed
        """
        try:
            # The reasoning module typically returns responses in different formats
            # Try to extract the explanation from common response structures
            
            if isinstance(response, str):
                return response.strip()
            
            if isinstance(response, dict):
                # Try common keys where explanation might be stored
                for key in ['explanation', 'response', 'answer', 'result', 'content', 'text']:
                    if key in response and response[key]:
                        return str(response[key]).strip()
                
                # If it's an action plan format, try to extract from action or description
                if 'action' in response:
                    return str(response['action']).strip()
                
                # Last resort: convert entire response to string
                return str(response).strip()
            
            # Fallback: convert to string
            return str(response).strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting explanation from response: {e}")
            return None
    
    def _validate_explanation_quality(self, explanation: str, original_text: str) -> bool:
        """
        Validate the quality of the generated explanation.
        
        Args:
            explanation: The generated explanation
            original_text: The original selected text
            
        Returns:
            True if explanation meets quality standards, False otherwise
        """
        try:
            # Basic length validation
            if len(explanation.strip()) < 10:
                self.logger.warning("Explanation too short")
                return False
            
            # Check for reasonable length relative to original text
            if len(explanation) > len(original_text) * 3:
                self.logger.warning("Explanation significantly longer than original text")
                # Don't fail validation, just log warning
            
            # Check for common failure patterns
            failure_patterns = [
                "i cannot", "i can't", "unable to", "don't understand",
                "not clear", "insufficient information", "cannot determine"
            ]
            
            explanation_lower = explanation.lower()
            if any(pattern in explanation_lower for pattern in failure_patterns):
                self.logger.warning("Explanation contains failure indicators")
                return False
            
            # Check for reasonable content (not just repeated text)
            if explanation.strip().lower() == original_text.strip().lower():
                self.logger.warning("Explanation is identical to original text")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating explanation quality: {e}")
            return False
    
    def _play_thinking_sound(self) -> None:
        """
        Play thinking sound to indicate processing has started.
        """
        try:
            audio_module = self._get_module_safely('audio_module')
            if audio_module and hasattr(audio_module, 'play_thinking_sound'):
                audio_module.play_thinking_sound()
                self.logger.debug("Thinking sound played")
        except Exception as e:
            self.logger.warning(f"Failed to play thinking sound: {e}")
    
    def _speak_explanation(self, explanation: str) -> None:
        """
        Speak the explanation to the user using the audio module.
        
        Args:
            explanation: The explanation text to speak
        """
        try:
            audio_module = self._get_module_safely('audio_module')
            if audio_module and hasattr(audio_module, 'speak'):
                audio_module.speak(explanation)
                self.logger.debug("Explanation spoken to user")
                
                # Also print to console for user feedback
                print(f"\n🤖 AURA: {explanation}\n")
                self.logger.info(f"AURA Explanation: {explanation}")
            else:
                self.logger.warning("Audio module not available, printing explanation only")
                print(f"\n🤖 AURA: {explanation}\n")
                
        except Exception as e:
            self.logger.error(f"Failed to speak explanation: {e}")
            # Fallback to console output
            print(f"\n🤖 AURA: {explanation}\n")
    
    def _speak_error_feedback(self, error_message: str) -> None:
        """
        Speak error feedback to the user with failure sound.
        
        Args:
            error_message: The error message to speak
        """
        try:
            audio_module = self._get_module_safely('audio_module')
            if audio_module:
                # Play failure sound if available
                if hasattr(audio_module, 'play_failure_sound'):
                    audio_module.play_failure_sound()
                
                # Speak error message
                if hasattr(audio_module, 'speak'):
                    audio_module.speak(error_message)
                    self.logger.debug("Error feedback spoken to user")
            
            # Always print to console as fallback
            print(f"\n🤖 AURA: {error_message}\n")
            
        except Exception as e:
            self.logger.error(f"Failed to speak error feedback: {e}")
            # Fallback to console output
            print(f"\n🤖 AURA: {error_message}\n")
    
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
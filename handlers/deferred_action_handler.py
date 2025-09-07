"""
Deferred Action Handler for AURA Command Processing

This module handles deferred action workflows where content is generated first,
then the user specifies where to place it by clicking. This includes code generation,
text creation, and other content that needs precise placement.
"""

import time
import threading
from typing import Dict, Any, Optional, Tuple
from .base_handler import BaseHandler


class DeferredActionHandler(BaseHandler):
    """
    Handles deferred action workflows for content generation and placement.
    
    This handler processes content generation requests like:
    - Code generation ("Write me a Python function for...")
    - Text creation ("Write me an email about...")
    - Document generation ("Create a list of...")
    
    The workflow involves:
    1. Generate requested content using appropriate prompts
    2. Clean and format the content
    3. Set up mouse listener for user click
    4. Provide audio instructions to user
    5. Wait for user to click placement location
    6. Execute content placement at clicked location
    """
    
    def __init__(self, orchestrator_ref):
        """Initialize the deferred action handler."""
        super().__init__(orchestrator_ref)
        self.deferred_action_timeout_seconds = 300.0  # 5 minutes default
    
    def handle(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process deferred action requests for content generation and placement.
        
        Args:
            command: Content generation request (e.g., "Write me a Python function")
            context: Execution context with intent and content type information
            
        Returns:
            Execution result, typically with waiting_for_user_action status
        """
        # Validate input
        if not self._validate_command(command):
            return self._create_error_result("Invalid or empty content generation request")
        
        # Log execution start
        start_time = self._log_execution_start(command, context)
        execution_id = context.get('execution_id', f"deferred_{int(time.time())}")
        
        try:
            self.logger.info(f"[{execution_id}] Starting deferred action workflow")
            
            # Check if system is already in deferred action mode
            if getattr(self.orchestrator, 'is_waiting_for_user_action', False):
                self.logger.warning(f"[{execution_id}] System already in deferred action mode, cancelling previous action")
                self._reset_deferred_action_state()
                
                # Provide audio feedback about cancellation
                feedback_module = self._get_module_safely('feedback_module')
                if feedback_module:
                    try:
                        feedback_module.speak("Previous action cancelled. Starting new deferred action.")
                    except Exception as audio_error:
                        self.logger.warning(f"[{execution_id}] Audio feedback failed: {audio_error}")
            
            # Extract content request and type from intent parameters
            intent_data = context.get('intent', {})
            parameters = intent_data.get('parameters', {})
            content_request = parameters.get('content_request', command)
            content_type = parameters.get('content_type', 'text')
            
            # Validate content request
            if not content_request or not content_request.strip():
                raise ValueError("Empty content request for deferred action")
            
            self.logger.info(f"[{execution_id}] Content request: {content_request}, Type: {content_type}")
            
            # Step 1: Generate content
            generated_content = self._generate_content(content_request, content_type, execution_id)
            if not generated_content:
                return self._create_error_result("Failed to generate content")
            
            # Step 2: Clean and format content
            cleaned_content = self._clean_and_format_content(generated_content, content_type)
            
            # Step 3: Set up deferred action state
            self._setup_deferred_action_state(cleaned_content, content_type, execution_id)
            
            # Step 4: Start mouse listener
            self._start_mouse_listener(execution_id)
            
            # Step 5: Provide audio instructions
            self._provide_audio_instructions(content_type, execution_id)
            
            # Step 6: Start timeout monitoring
            self._start_timeout_monitoring(execution_id)
            
            result = self._create_waiting_result(
                "Content generated. Click where you want it placed.",
                execution_id=execution_id,
                content_preview=cleaned_content[:100] + '...' if len(cleaned_content) > 100 else cleaned_content,
                content_type=content_type,
                waiting_since=time.time(),
                timeout_at=time.time() + self.deferred_action_timeout_seconds,
                timeout_seconds=self.deferred_action_timeout_seconds,
                instructions='Click anywhere on the screen where you want the content to be typed.'
            )
            
            # Log execution end
            self._log_execution_end(start_time, result, context)
            return result
            
        except Exception as e:
            self.logger.error(f"[{execution_id}] Deferred action request failed: {e}")
            self._reset_deferred_action_state()
            return self._handle_module_error("deferred_action_handler", e, "deferred action processing")
    
    def _generate_content(self, content_request: str, content_type: str, execution_id: str) -> str:
        """
        Generate content based on the user's request.
        
        Args:
            content_request: Content generation request
            content_type: Type of content to generate (code, text, etc.)
            execution_id: Unique execution identifier
            
        Returns:
            Generated content string
        """
        try:
            reasoning_module = self._get_module_safely('reasoning_module')
            if not reasoning_module:
                raise RuntimeError("Reasoning module not available")
            
            # Use appropriate prompt based on content type
            if content_type == 'code':
                prompt_key = 'CODE_GENERATION_PROMPT'
            else:
                prompt_key = 'TEXT_GENERATION_PROMPT'
            
            self.logger.debug(f"[{execution_id}] Generating {content_type} content using {prompt_key}")
            
            # Import config here to avoid circular imports
            try:
                from config import CODE_GENERATION_PROMPT, TEXT_GENERATION_PROMPT
            except ImportError:
                self.logger.error(f"[{execution_id}] Failed to import prompt templates")
                raise RuntimeError("Prompt templates not available")
            
            # Choose the appropriate prompt based on content type
            if content_type == 'code':
                prompt_template = CODE_GENERATION_PROMPT
            else:  # text, essay, article, etc.
                prompt_template = TEXT_GENERATION_PROMPT
            
            # Format the prompt with the user's request
            formatted_prompt = prompt_template.format(
                request=content_request,
                context=str({'content_type': content_type, 'execution_id': execution_id})
            )
            
            # Generate content using reasoning module's API request method
            response = reasoning_module._make_api_request(formatted_prompt)
            
            if not response or not isinstance(response, dict):
                raise ValueError("Empty or invalid response from reasoning module")
            
            # Extract the content from the response dictionary
            # Handle various API response formats
            if isinstance(response, dict) and 'choices' in response:
                # Handle OpenAI-style response format
                choices = response.get('choices', [])
                if choices and isinstance(choices, list) and len(choices) > 0:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict) and 'message' in first_choice:
                        message = first_choice.get('message', {})
                        if isinstance(message, dict) and 'content' in message:
                            generated_content = message.get('content', '').strip()
                        else:
                            generated_content = str(first_choice.get('message', '')).strip()
                    else:
                        generated_content = str(first_choice).strip()
                else:
                    raise ValueError("No choices in API response")
            else:
                # Handle other response formats
                generated_content = response.get('message', response.get('response', str(response))).strip()
            
            if not generated_content or not generated_content.strip():
                raise ValueError("Empty content generated")
            
            self.logger.info(f"[{execution_id}] Generated {len(generated_content)} characters of {content_type} content")
            return generated_content
            
        except Exception as e:
            self.logger.error(f"[{execution_id}] Content generation failed: {e}")
            raise
    
    def _clean_and_format_content(self, content: str, content_type: str) -> str:
        """
        Clean and format generated content for typing with comprehensive cleaning and formatting.
        
        Args:
            content: Raw generated content
            content_type: Type of content (code, text, etc.)
            
        Returns:
            Cleaned and formatted content ready for typing
        """
        try:
            # Comprehensive list of unwanted prefixes
            unwanted_prefixes = [
                # Common explanatory phrases
                "Here is the code:",
                "Here's the code:",
                "Here is your code:",
                "Here's your code:",
                "The code is:",
                "The following code:",
                "Below is the code:",
                "Here is the requested code:",
                "Here's the requested code:",
                "The requested code is:",
                
                # Text content prefixes
                "Here is the text:",
                "Here's the text:",
                "Here is your text:",
                "Here's your text:",
                "The text is:",
                "The following text:",
                "Below is the text:",
                "Here is the essay:",
                "Here's the essay:",
                "Here is the article:",
                "Here's the article:",
                "The essay is:",
                "The article is:",
                
                # Markdown code blocks
                "```python",
                "```javascript",
                "```js",
                "```typescript",
                "```ts",
                "```html",
                "```css",
                "```java",
                "```c++",
                "```cpp",
                "```c#",
                "```csharp",
                "```json",
                "```yaml",
                "```yml",
                "```xml",
                "```sql",
                "```bash",
                "```shell",
                "```",
                
                # Bold/italic markers
                "**Code:**",
                "**Text:**",
                "**Essay:**",
                "**Article:**",
                "*Code:*",
                "*Text:*",
                "*Essay:*",
                "*Article:*",
                
                # Other common prefixes
                "Solution:",
                "Answer:",
                "Response:",
                "Output:",
                "Result:",
                "Generated code:",
                "Generated text:",
                "Final code:",
                "Final text:",
                "Complete code:",
                "Complete text:"
            ]
            
            # Comprehensive list of unwanted suffixes
            unwanted_suffixes = [
                # Markdown code blocks
                "```",
                "```python",
                "```javascript",
                "```js",
                "```typescript",
                "```ts",
                "```html",
                "```css",
                "```java",
                "```c++",
                "```cpp",
                "```c#",
                "```csharp",
                "```json",
                "```yaml",
                "```yml",
                "```xml",
                "```sql",
                "```bash",
                "```shell",
                
                # End markers
                "**End of code**",
                "**End of text**",
                "**End of essay**",
                "**End of article**",
                "*End of code*",
                "*End of text*",
                "*End of essay*",
                "*End of article*",
                "--- End ---",
                "-- End --",
                "- End -",
                
                # Other common suffixes
                "That's it!",
                "Done!",
                "Complete!",
                "Finished!",
                "Hope this helps!",
                "Let me know if you need anything else!",
                "Feel free to ask if you have questions!"
            ]
            
            # Start with trimmed content
            cleaned_content = content.strip()
            
            # Remove unwanted prefixes (case-insensitive, multiple passes)
            changed = True
            while changed:
                changed = False
                for prefix in unwanted_prefixes:
                    if cleaned_content.lower().startswith(prefix.lower()):
                        cleaned_content = cleaned_content[len(prefix):].strip()
                        changed = True
                        break
            
            # Remove unwanted suffixes (case-insensitive, multiple passes)
            changed = True
            while changed:
                changed = False
                for suffix in unwanted_suffixes:
                    if cleaned_content.lower().endswith(suffix.lower()):
                        cleaned_content = cleaned_content[:-len(suffix)].strip()
                        changed = True
                        break
            
            # Remove duplicate content (common with AI responses)
            cleaned_content = self._remove_duplicate_content(cleaned_content)
            
            # Apply content type-specific formatting
            if content_type == 'code':
                cleaned_content = self._format_code_content(cleaned_content)
            elif content_type == 'text':
                cleaned_content = self._format_text_content(cleaned_content)
            else:
                # Generic content formatting
                cleaned_content = self._format_generic_content(cleaned_content)
            
            # Final cleanup
            cleaned_content = self._final_content_cleanup(cleaned_content)
            
            return cleaned_content
            
        except Exception as e:
            self.logger.warning(f"Error cleaning generated content: {e}")
            return content  # Return original content if cleaning fails
    
    def _remove_duplicate_content(self, content: str) -> str:
        """
        Remove duplicate content that sometimes appears in AI responses.
        
        Args:
            content: Content to check for duplicates
            
        Returns:
            Content with duplicates removed
        """
        try:
            lines = content.split('\n')
            if len(lines) < 2:
                return content
            
            # Check for exact duplicate blocks
            unique_lines = []
            seen_blocks = set()
            
            # Process in chunks to detect duplicate blocks
            for i, line in enumerate(lines):
                # Create a block of 3 lines for comparison
                if i + 2 < len(lines):
                    block = '\n'.join(lines[i:i+3])
                    if block not in seen_blocks:
                        seen_blocks.add(block)
                        unique_lines.append(line)
                    else:
                        # Skip this line as it's part of a duplicate block
                        continue
                else:
                    unique_lines.append(line)
            
            return '\n'.join(unique_lines)
            
        except Exception as e:
            self.logger.warning(f"Error removing duplicate content: {e}")
            return content
    
    def _format_code_content(self, content: str) -> str:
        """
        Format code content with proper indentation and structure.
        
        Args:
            content: Raw code content
            
        Returns:
            Properly formatted code
        """
        try:
            # Remove any remaining markdown code blocks
            if content.startswith('```') and content.endswith('```'):
                lines = content.split('\n')
                if len(lines) > 2:
                    # Remove first and last lines if they're markdown markers
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == '```':
                        lines = lines[:-1]
                    content = '\n'.join(lines)
            
            # Check for single-line code that needs reformatting
            if self._is_single_line_code(content):
                content = self._format_single_line_code(content)
            
            # Ensure proper indentation (convert tabs to spaces)
            content = content.replace('\t', '    ')
            
            # Remove excessive blank lines but preserve intentional spacing
            lines = content.split('\n')
            formatted_lines = []
            blank_line_count = 0
            
            for line in lines:
                if line.strip():  # Non-empty line
                    formatted_lines.append(line)
                    blank_line_count = 0
                else:  # Empty line
                    blank_line_count += 1
                    if blank_line_count <= 2:  # Allow max 2 consecutive blank lines
                        formatted_lines.append(line)
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            self.logger.warning(f"Error formatting code content: {e}")
            return content
    
    def _format_text_content(self, content: str) -> str:
        """
        Format text content with proper paragraph structure.
        
        Args:
            content: Raw text content
            
        Returns:
            Properly formatted text
        """
        try:
            # Ensure proper line breaks between paragraphs
            lines = content.split('\n')
            formatted_lines = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line:  # Non-empty line
                    formatted_lines.append(line)
                    # Add extra line break after paragraphs (except for the last line)
                    if i < len(lines) - 1:
                        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                        if next_line and self._should_add_paragraph_break(line, next_line):
                            formatted_lines.append('')  # Add paragraph break
                elif formatted_lines and formatted_lines[-1]:  # Preserve intentional blank lines
                    formatted_lines.append('')
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            self.logger.warning(f"Error formatting text content: {e}")
            return content
    
    def _format_generic_content(self, content: str) -> str:
        """
        Format generic content with basic cleanup.
        
        Args:
            content: Raw content
            
        Returns:
            Cleaned content
        """
        try:
            # Basic cleanup for unknown content types
            lines = content.split('\n')
            formatted_lines = []
            
            for line in lines:
                # Remove excessive whitespace but preserve indentation
                if line.strip():
                    formatted_lines.append(line.rstrip())
                else:
                    formatted_lines.append('')
            
            # Remove excessive blank lines at start and end
            while formatted_lines and not formatted_lines[0].strip():
                formatted_lines.pop(0)
            while formatted_lines and not formatted_lines[-1].strip():
                formatted_lines.pop()
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            self.logger.warning(f"Error formatting generic content: {e}")
            return content
    
    def _is_single_line_code(self, content: str) -> bool:
        """
        Check if content appears to be single-line code that should be reformatted.
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears to be improperly formatted single-line code
        """
        try:
            # Check if it's a single line with code-like characteristics
            if '\n' in content:
                return False
            
            # Look for code patterns that suggest it should be multi-line
            code_indicators = [
                '{', '}', ';', 'function', 'def ', 'class ', 'if ', 'for ', 'while ',
                'import ', 'from ', 'return ', 'var ', 'let ', 'const ', '=', '(', ')'
            ]
            
            return any(indicator in content for indicator in code_indicators) and len(content) > 50
            
        except Exception:
            return False
    
    def _format_single_line_code(self, content: str) -> str:
        """
        Format single-line code into properly structured multi-line code.
        
        Args:
            content: Single-line code content
            
        Returns:
            Properly formatted multi-line code
        """
        try:
            # Basic formatting for common patterns
            formatted = content
            
            # Add line breaks after common delimiters
            replacements = [
                ('{', '{\n'),
                ('}', '\n}'),
                (';', ';\n'),
                (' if ', '\nif '),
                (' for ', '\nfor '),
                (' while ', '\nwhile '),
                (' def ', '\ndef '),
                (' class ', '\nclass '),
                (' function ', '\nfunction ')
            ]
            
            for old, new in replacements:
                formatted = formatted.replace(old, new)
            
            # Clean up excessive newlines
            while '\n\n\n' in formatted:
                formatted = formatted.replace('\n\n\n', '\n\n')
            
            return formatted.strip()
            
        except Exception as e:
            self.logger.warning(f"Error formatting single-line code: {e}")
            return content
    
    def _should_add_paragraph_break(self, current_line: str, next_line: str) -> bool:
        """
        Determine if a paragraph break should be added between two lines.
        
        Args:
            current_line: Current line of text
            next_line: Next line of text
            
        Returns:
            True if a paragraph break should be added
        """
        try:
            # Add paragraph break if current line ends with sentence-ending punctuation
            if current_line.endswith(('.', '!', '?', ':')):
                return True
            
            # Add paragraph break if next line starts with common paragraph starters
            paragraph_starters = [
                'However,', 'Therefore,', 'Additionally,', 'Furthermore,', 'Moreover,',
                'In conclusion,', 'Finally,', 'First,', 'Second,', 'Third,', 'Next,',
                'Meanwhile,', 'Subsequently,', 'Consequently,', 'Nevertheless,'
            ]
            
            return any(next_line.startswith(starter) for starter in paragraph_starters)
            
        except Exception:
            return False
    
    def _final_content_cleanup(self, content: str) -> str:
        """
        Perform final cleanup on content before returning.
        
        Args:
            content: Content to clean up
            
        Returns:
            Final cleaned content
        """
        try:
            # Remove excessive whitespace
            content = content.strip()
            
            # Ensure content ends with a single newline if it's multi-line
            if '\n' in content and not content.endswith('\n'):
                content += '\n'
            
            # Remove any remaining unwanted characters or patterns
            unwanted_patterns = [
                '\r\n',  # Windows line endings
                '\r',    # Old Mac line endings
            ]
            
            for pattern in unwanted_patterns:
                content = content.replace(pattern, '\n')
            
            return content
            
        except Exception as e:
            self.logger.warning(f"Error in final content cleanup: {e}")
            return content
    
    def _setup_deferred_action_state(self, content: str, content_type: str, execution_id: str) -> None:
        """
        Set up the deferred action state in the orchestrator.
        
        Args:
            content: Cleaned content ready for placement
            content_type: Type of content
            execution_id: Unique execution identifier
        """
        try:
            deferred_action_lock = getattr(self.orchestrator, 'deferred_action_lock', threading.Lock())
            
            with deferred_action_lock:
                # Store action state with enhanced tracking
                current_time = time.time()
                self.orchestrator.pending_action_payload = content
                self.orchestrator.deferred_action_type = 'type'  # Default action is typing
                self.orchestrator.deferred_action_start_time = current_time
                self.orchestrator.deferred_action_timeout_time = current_time + self.deferred_action_timeout_seconds
                self.orchestrator.is_waiting_for_user_action = True
                self.orchestrator.current_deferred_content_type = content_type
                self.orchestrator.mouse_listener_active = False  # Will be set to True when listener starts
                self.orchestrator.system_mode = 'waiting_for_user'
                self.orchestrator.current_execution_id = execution_id
                
                self.logger.debug(f"[{execution_id}] Deferred action state configured (timeout: {self.deferred_action_timeout_seconds}s)")
                
        except Exception as e:
            self.logger.error(f"[{execution_id}] Failed to set up deferred action state: {e}")
            raise
    
    def _start_mouse_listener(self, execution_id: str) -> None:
        """
        Start the global mouse listener for click detection.
        
        Args:
            execution_id: Unique execution identifier
        """
        try:
            self.logger.debug(f"[{execution_id}] Starting mouse listener for deferred action")
            
            # Import mouse listener here to avoid circular imports
            try:
                from utils.mouse_listener import GlobalMouseListener, is_mouse_listener_available
            except ImportError as import_error:
                self.logger.error(f"[{execution_id}] Failed to import mouse listener: {import_error}")
                raise ImportError("Mouse listener module not available. Please check utils/mouse_listener.py")
            
            # Check if mouse listener functionality is available
            if not is_mouse_listener_available():
                self.logger.error(f"[{execution_id}] Mouse listener dependencies not available")
                raise RuntimeError(
                    "Mouse listener not available - pynput library required. "
                    "Install with: pip install pynput"
                )
            
            # Create callback for mouse clicks
            def on_deferred_action_trigger():
                try:
                    self._on_deferred_action_trigger(execution_id)
                except Exception as callback_error:
                    self.logger.error(f"[{execution_id}] Error in mouse click callback: {callback_error}")
            
            # Create and start mouse listener
            self.orchestrator.mouse_listener = GlobalMouseListener(
                on_click_callback=on_deferred_action_trigger,
                execution_id=execution_id
            )
            
            # Start the listener
            self.orchestrator.mouse_listener.start()
            self.orchestrator.mouse_listener_active = True
            
            self.logger.info(f"[{execution_id}] Mouse listener started successfully")
            
        except Exception as e:
            self.logger.error(f"[{execution_id}] Failed to start mouse listener: {e}")
            raise RuntimeError(f"Failed to start mouse listener: {str(e)}")
    
    def _provide_audio_instructions(self, content_type: str, execution_id: str) -> None:
        """
        Provide audio instructions to the user about clicking.
        
        Args:
            content_type: Type of content for appropriate instructions
            execution_id: Unique execution identifier
        """
        try:
            # Prepare instruction message based on content type
            if content_type == 'code':
                instruction_message = "Code generated successfully. Click where you want me to type it."
            elif content_type == 'text':
                instruction_message = "Text generated successfully. Click where you want me to type it."
            else:
                instruction_message = "Content generated successfully. Click where you want me to place it."
            
            # Use enhanced feedback module for audio instructions if available
            feedback_module = self._get_module_safely('feedback_module')
            if feedback_module:
                try:
                    feedback_module.provide_deferred_action_instructions(
                        content_type=content_type,
                        priority=getattr(feedback_module, 'FeedbackPriority', {}).get('HIGH', 'high')
                    )
                    self.logger.debug(f"[{execution_id}] Enhanced deferred action instructions provided")
                except Exception as e:
                    self.logger.warning(f"[{execution_id}] Enhanced instructions failed, falling back to basic: {e}")
                    # Fallback to basic instruction delivery
                    try:
                        feedback_module.speak(instruction_message)
                        self.logger.debug(f"[{execution_id}] Basic audio instructions provided via feedback module")
                    except Exception as fallback_error:
                        self.logger.warning(f"[{execution_id}] Basic feedback also failed: {fallback_error}")
            
            # Also use audio module directly as fallback
            else:
                audio_module = self._get_module_safely('audio_module')
                if audio_module:
                    try:
                        audio_module.text_to_speech(instruction_message)
                        self.logger.debug(f"[{execution_id}] Audio instructions provided via audio module")
                    except Exception as e:
                        self.logger.warning(f"[{execution_id}] Failed to provide audio instructions: {e}")
                else:
                    self.logger.warning(f"[{execution_id}] No audio modules available for instructions")
            
        except Exception as e:
            self.logger.error(f"[{execution_id}] Failed to provide deferred action instructions: {e}")
    
    def _start_timeout_monitoring(self, execution_id: str) -> None:
        """
        Start timeout monitoring for the deferred action.
        
        Args:
            execution_id: Unique execution identifier
        """
        def timeout_monitor():
            try:
                time.sleep(self.deferred_action_timeout_seconds)
                
                # Check if we're still waiting
                if getattr(self.orchestrator, 'is_waiting_for_user_action', False):
                    self.logger.warning(f"[{execution_id}] Deferred action timed out after {self.deferred_action_timeout_seconds}s")
                    self._reset_deferred_action_state()
                    
                    # Provide timeout feedback
                    feedback_module = self._get_module_safely('feedback_module')
                    if feedback_module:
                        try:
                            feedback_module.speak("Action timed out. Please try again.")
                        except Exception as e:
                            self.logger.warning(f"[{execution_id}] Failed to provide timeout feedback: {e}")
                            
            except Exception as e:
                self.logger.error(f"[{execution_id}] Error in timeout monitor: {e}")
        
        # Start timeout monitoring in a separate thread
        timeout_thread = threading.Thread(target=timeout_monitor, daemon=True)
        timeout_thread.start()
    
    def _on_deferred_action_trigger(self, execution_id: str) -> None:
        """
        Callback method triggered when user clicks during deferred action.
        
        Args:
            execution_id: Unique execution identifier
        """
        try:
            self.logger.info(f"[{execution_id}] Deferred action triggered by user click")
            
            deferred_action_lock = getattr(self.orchestrator, 'deferred_action_lock', threading.Lock())
            
            with deferred_action_lock:
                # Verify we're in the correct state
                if not getattr(self.orchestrator, 'is_waiting_for_user_action', False):
                    self.logger.warning(f"[{execution_id}] Deferred action trigger called but not waiting for user action")
                    return
                
                if not getattr(self.orchestrator, 'pending_action_payload', None):
                    self.logger.error(f"[{execution_id}] No pending action payload found")
                    self._reset_deferred_action_state()
                    return
                
                # Get click coordinates if available
                click_coordinates = None
                if hasattr(self.orchestrator, 'mouse_listener') and self.orchestrator.mouse_listener:
                    click_coordinates = self.orchestrator.mouse_listener.get_last_click_coordinates()
                
                self.logger.info(f"[{execution_id}] Executing deferred action at coordinates: {click_coordinates}")
                
                # Execute the pending action
                try:
                    success = self._execute_pending_action(execution_id, click_coordinates)
                    
                    if success:
                        # Provide success feedback
                        self._provide_completion_feedback(execution_id, True)
                        self.logger.info(f"[{execution_id}] Deferred action completed successfully")
                    else:
                        # Provide failure feedback
                        self._provide_completion_feedback(execution_id, False)
                        self.logger.error(f"[{execution_id}] Deferred action execution failed")
                
                except Exception as e:
                    self.logger.error(f"[{execution_id}] Error executing pending deferred action: {e}")
                    self._provide_completion_feedback(execution_id, False)
                
                finally:
                    # Always reset state after execution attempt
                    self._reset_deferred_action_state()
            
        except Exception as e:
            self.logger.error(f"[{execution_id}] Error in deferred action trigger: {e}")
            # Ensure state is reset even on error
            self._reset_deferred_action_state()
    
    def _execute_pending_action(self, execution_id: str, click_coordinates: Optional[Tuple[int, int]]) -> bool:
        """
        Execute the pending deferred action with the generated content.
        
        Args:
            execution_id: Unique execution identifier
            click_coordinates: Where the user clicked
            
        Returns:
            True if execution was successful, False otherwise
        """
        try:
            pending_content = getattr(self.orchestrator, 'pending_action_payload', None)
            if not pending_content:
                self.logger.error(f"[{execution_id}] No pending action payload to execute")
                return False
            
            action_type = getattr(self.orchestrator, 'deferred_action_type', 'type')
            
            self.logger.info(f"[{execution_id}] Executing {action_type} action with {len(pending_content)} characters")
            
            automation_module = self._get_module_safely('automation_module')
            if not automation_module:
                self.logger.error(f"[{execution_id}] Automation module not available")
                return False
            
            # If we have click coordinates, click there first to position cursor
            if click_coordinates:
                try:
                    x, y = click_coordinates
                    self.logger.debug(f"[{execution_id}] Clicking at coordinates ({x}, {y}) before typing")
                    
                    # Use automation module to click at the coordinates
                    click_action = {
                        "action": "click",
                        "coordinates": [int(x), int(y)]
                    }
                    
                    automation_module.execute_action(click_action)
                    self.logger.debug(f"[{execution_id}] Successfully clicked at coordinates ({x}, {y})")
                    
                    # Small delay to ensure click is processed
                    time.sleep(0.2)
                    
                except Exception as e:
                    self.logger.warning(f"[{execution_id}] Failed to click at coordinates: {e}")
            
            # Execute the main action (typically typing)
            if action_type == 'type':
                try:
                    # Use automation module to type the content
                    type_action = {
                        "action": "type",
                        "text": pending_content
                    }
                    
                    automation_module.execute_action(type_action)
                    self.logger.info(f"[{execution_id}] Successfully typed {len(pending_content)} characters")
                    return True
                        
                except Exception as e:
                    self.logger.error(f"[{execution_id}] Error during type action: {e}")
                    return False
            
            else:
                self.logger.error(f"[{execution_id}] Unsupported action type '{action_type}'")
                return False
            
        except Exception as e:
            self.logger.error(f"[{execution_id}] Error executing pending deferred action: {e}")
            return False
    
    def _provide_completion_feedback(self, execution_id: str, success: bool) -> None:
        """
        Provide audio feedback when deferred action completes.
        
        Args:
            execution_id: Unique execution identifier
            success: Whether the action completed successfully
        """
        try:
            if success:
                message = "Content placed successfully."
                sound_type = "success"
            else:
                message = "Failed to place content. Please try again."
                sound_type = "failure"
            
            # Provide enhanced audio feedback
            feedback_module = self._get_module_safely('feedback_module')
            if feedback_module:
                try:
                    # Determine content type from current deferred action context
                    content_type = getattr(self.orchestrator, 'current_deferred_content_type', 'content')
                    
                    feedback_module.provide_deferred_action_completion_feedback(
                        success=success,
                        content_type=content_type,
                        priority=getattr(feedback_module, 'FeedbackPriority', {}).get('HIGH', 'high')
                    )
                    self.logger.debug(f"[{execution_id}] Enhanced completion feedback provided")
                except Exception as e:
                    self.logger.warning(f"[{execution_id}] Enhanced completion feedback failed, falling back to basic: {e}")
                    # Fallback to basic completion feedback
                    try:
                        feedback_module.play_with_message(sound_type, message)
                        self.logger.debug(f"[{execution_id}] Basic completion feedback provided via feedback module")
                    except Exception as fallback_error:
                        self.logger.warning(f"[{execution_id}] Basic completion feedback also failed: {fallback_error}")
            
            # Fallback to audio module
            else:
                audio_module = self._get_module_safely('audio_module')
                if audio_module:
                    try:
                        audio_module.text_to_speech(message)
                        self.logger.debug(f"[{execution_id}] Completion feedback provided via audio module")
                    except Exception as e:
                        self.logger.warning(f"[{execution_id}] Failed to provide audio completion feedback: {e}")
            
        except Exception as e:
            self.logger.error(f"[{execution_id}] Error providing deferred action completion feedback: {e}")
    
    def _reset_deferred_action_state(self) -> None:
        """
        Reset all deferred action state variables and cleanup resources.
        """
        try:
            # Stop mouse listener if active
            if hasattr(self.orchestrator, 'mouse_listener') and self.orchestrator.mouse_listener:
                try:
                    self.orchestrator.mouse_listener.stop()
                    self.logger.debug("Mouse listener stopped successfully")
                except Exception as e:
                    self.logger.warning(f"Error stopping mouse listener: {e}")
                finally:
                    self.orchestrator.mouse_listener = None
            
            # Reset state variables
            self.orchestrator.is_waiting_for_user_action = False
            self.orchestrator.pending_action_payload = None
            self.orchestrator.deferred_action_type = None
            self.orchestrator.deferred_action_start_time = None
            self.orchestrator.deferred_action_timeout_time = None
            self.orchestrator.current_deferred_content_type = None
            self.orchestrator.mouse_listener_active = False
            self.orchestrator.system_mode = 'ready'
            self.orchestrator.current_execution_id = None
            
            self.logger.debug("Deferred action state reset successfully")
            
        except Exception as e:
            self.logger.error(f"Error resetting deferred action state: {e}")
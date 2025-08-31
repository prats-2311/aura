# modules/reasoning.py
"""
AURA Reasoning Module

Handles communication with cloud-based LLMs for intelligent action planning.
Processes user commands and screen context to generate structured action plans.
"""

import json
import logging
import requests
import time
from typing import Dict, Any, Optional
from config import (
    REASONING_API_BASE,
    REASONING_API_KEY,
    REASONING_MODEL,
    REASONING_META_PROMPT,
    REASONING_API_TIMEOUT
)
from .error_handler import (
    global_error_handler,
    with_error_handling,
    ErrorCategory,
    ErrorSeverity
)

# Configure logging
logger = logging.getLogger(__name__)


class ReasoningModule:
    """
    Handles communication with cloud-based reasoning models for action planning.
    
    This module takes user commands and screen context, sends them to a cloud LLM,
    and returns structured action plans that can be executed by the automation module.
    """
    
    def __init__(self):
        """Initialize the reasoning module with API configuration."""
        self.api_base = REASONING_API_BASE
        self.api_key = REASONING_API_KEY
        self.model = REASONING_MODEL
        self.timeout = REASONING_API_TIMEOUT
        
        # Validate configuration
        if not self.api_key or self.api_key == "your_ollama_cloud_api_key_here":
            logger.warning("Reasoning API key not configured properly")
        
        logger.info(f"ReasoningModule initialized with model: {self.model}")
    
    @with_error_handling(
        category=ErrorCategory.API_ERROR,
        severity=ErrorSeverity.MEDIUM,
        max_retries=3,
        retry_delay=2.0,
        user_message="I'm having trouble processing your request. Please try again.",
        fallback_return=None
    )
    def get_action_plan(self, user_command: str, screen_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an action plan based on user command and screen context.
        
        Args:
            user_command (str): The natural language command from the user
            screen_context (dict): JSON description of the current screen state
            
        Returns:
            dict: Structured action plan with steps and metadata
            
        Raises:
            Exception: If API communication fails or response is invalid after retries
        """
        try:
            # Input validation
            if not user_command or not user_command.strip():
                raise ValueError("User command cannot be empty")
            
            if not isinstance(screen_context, dict):
                raise ValueError("Screen context must be a dictionary")
            
            # Validate command length
            if len(user_command) > 1000:
                raise ValueError("User command too long (maximum 1000 characters)")
            
            logger.info(f"Generating action plan for command: '{user_command[:100]}...'")
            
            # Prepare the prompt with user command and screen context
            try:
                prompt = self._build_prompt(user_command, screen_context)
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="reasoning",
                    function="get_action_plan",
                    category=ErrorCategory.PROCESSING_ERROR,
                    context={"command_length": len(user_command), "context_keys": list(screen_context.keys())}
                )
                raise Exception(f"Prompt building failed: {error_info.user_message}")
            
            # Make API request to cloud LLM
            try:
                response = self._make_api_request(prompt)
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="reasoning",
                    function="get_action_plan",
                    category=ErrorCategory.API_ERROR,
                    context={"prompt_length": len(prompt)}
                )
                # Return fallback response for API errors
                return self._get_fallback_response(str(e))
            
            # Parse and validate the response
            try:
                action_plan = self._parse_response(response)
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="reasoning",
                    function="get_action_plan",
                    category=ErrorCategory.PROCESSING_ERROR,
                    context={"response_type": type(response).__name__}
                )
                # Return fallback response for parsing errors
                return self._get_fallback_response(str(e))
            
            # Final validation of action plan
            try:
                self._validate_action_plan(action_plan)
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="reasoning",
                    function="get_action_plan",
                    category=ErrorCategory.VALIDATION_ERROR,
                    context={"plan_keys": list(action_plan.keys()) if isinstance(action_plan, dict) else "not_dict"}
                )
                # Return fallback response for validation errors
                return self._get_fallback_response(str(e))
            
            logger.info(f"Generated action plan with {len(action_plan.get('plan', []))} steps")
            return action_plan
            
        except Exception as e:
            # Final fallback - always return a valid response
            logger.error(f"Failed to generate action plan: {str(e)}")
            return self._get_fallback_response(str(e))
    
    def _build_prompt(self, user_command: str, screen_context: Dict[str, Any]) -> str:
        """
        Build the complete prompt for the reasoning model.
        
        Args:
            user_command (str): User's natural language command
            screen_context (dict): Current screen state description
            
        Returns:
            str: Complete prompt for the LLM
        """
        screen_json = json.dumps(screen_context, indent=2)
        
        prompt = f"""{REASONING_META_PROMPT}

User Command: "{user_command}"

Current Screen State:
{screen_json}

Please analyze the user's command and the current screen state, then provide a detailed action plan in the specified JSON format."""
        
        return prompt
    
    def _make_api_request(self, prompt: str) -> Dict[str, Any]:
        """
        Make API request to the cloud reasoning model with comprehensive error handling.
        
        Args:
            prompt (str): The complete prompt to send
            
        Returns:
            dict: Raw API response
            
        Raises:
            Exception: If API request fails after retries
        """
        # Validate configuration
        if not self.api_base:
            raise ValueError("Reasoning API base URL not configured")
        if not self.api_key or self.api_key == "your_ollama_cloud_api_key_here":
            raise ValueError("Reasoning API key not configured")
        if not self.model:
            raise ValueError("Reasoning model not configured")
        
        # Validate prompt
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if len(prompt) > 50000:  # Reasonable limit
            raise ValueError("Prompt too long (maximum 50000 characters)")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare request payload (format may vary by provider)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for consistent responses
            "max_tokens": 2000
        }
        
        logger.debug(f"Making API request to {self.api_base}/chat/completions")
        
        # Implement retry logic with exponential backoff
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                response_time = time.time() - start_time
                logger.debug(f"API request completed in {response_time:.2f}s")
                
                # Handle different HTTP status codes
                if response.status_code == 200:
                    try:
                        return response.json()
                    except json.JSONDecodeError as e:
                        error_info = global_error_handler.handle_error(
                            error=e,
                            module="reasoning",
                            function="_make_api_request",
                            category=ErrorCategory.PROCESSING_ERROR,
                            context={"response_text": response.text[:500]}
                        )
                        raise Exception(f"Invalid JSON response: {error_info.user_message}")
                
                elif response.status_code == 401:
                    error_info = global_error_handler.handle_error(
                        error=Exception("Authentication failed"),
                        module="reasoning",
                        function="_make_api_request",
                        category=ErrorCategory.CONFIGURATION_ERROR,
                        context={"status_code": response.status_code}
                    )
                    raise Exception(f"API authentication failed: {error_info.user_message}")
                
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = min(5 * (2 ** attempt), 60)  # Exponential backoff, max 60s
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        error_info = global_error_handler.handle_error(
                            error=Exception("Rate limit exceeded"),
                            module="reasoning",
                            function="_make_api_request",
                            category=ErrorCategory.API_ERROR,
                            context={"status_code": response.status_code, "attempts": attempt + 1}
                        )
                        raise Exception(f"API rate limit exceeded: {error_info.user_message}")
                
                elif response.status_code >= 500:
                    # Server error - retry
                    wait_time = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                    logger.warning(f"Server error {response.status_code}, waiting {wait_time}s before retry")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        error_info = global_error_handler.handle_error(
                            error=Exception(f"Server error: {response.status_code}"),
                            module="reasoning",
                            function="_make_api_request",
                            category=ErrorCategory.API_ERROR,
                            context={"status_code": response.status_code, "response": response.text[:500]}
                        )
                        raise Exception(f"API server error: {error_info.user_message}")
                
                else:
                    # Client error - don't retry
                    error_info = global_error_handler.handle_error(
                        error=Exception(f"HTTP {response.status_code}: {response.text}"),
                        module="reasoning",
                        function="_make_api_request",
                        category=ErrorCategory.API_ERROR,
                        context={"status_code": response.status_code, "response": response.text[:500]}
                    )
                    raise Exception(f"API request failed: {error_info.user_message}")
                
            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"API request timed out (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                
            except requests.exceptions.ConnectionError as e:
                last_error = e
                logger.warning(f"Connection error to reasoning API (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
        
        # All retries failed
        if last_error:
            if isinstance(last_error, requests.exceptions.Timeout):
                error_info = global_error_handler.handle_error(
                    error=last_error,
                    module="reasoning",
                    function="_make_api_request",
                    category=ErrorCategory.TIMEOUT_ERROR,
                    context={"timeout": self.timeout, "attempts": max_retries}
                )
                raise Exception(f"API timeout after {max_retries} attempts: {error_info.user_message}")
            elif isinstance(last_error, requests.exceptions.ConnectionError):
                error_info = global_error_handler.handle_error(
                    error=last_error,
                    module="reasoning",
                    function="_make_api_request",
                    category=ErrorCategory.NETWORK_ERROR,
                    context={"api_base": self.api_base, "attempts": max_retries}
                )
                raise Exception(f"Cannot connect to reasoning API: {error_info.user_message}")
            else:
                error_info = global_error_handler.handle_error(
                    error=last_error,
                    module="reasoning",
                    function="_make_api_request",
                    category=ErrorCategory.API_ERROR,
                    context={"attempts": max_retries}
                )
                raise Exception(f"API request failed: {error_info.user_message}")
        
        # Should not reach here
        raise Exception("API request failed for unknown reason")
    
    def _parse_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate the API response.
        
        Args:
            api_response (dict): Raw API response
            
        Returns:
            dict: Parsed action plan
            
        Raises:
            Exception: If response format is invalid
        """
        try:
            # Extract content from API response
            if "choices" not in api_response or not api_response["choices"]:
                raise Exception("Invalid API response: no choices found")
            
            content = api_response["choices"][0]["message"]["content"]
            
            # Parse JSON from the content
            # The LLM might return JSON wrapped in markdown code blocks
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.endswith("```"):
                content = content[:-3]  # Remove ```
            
            action_plan = json.loads(content)
            
            # Validate the action plan structure
            self._validate_action_plan(action_plan)
            
            return action_plan
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}")
        except KeyError as e:
            raise Exception(f"Invalid API response structure: missing {str(e)}")
    
    def _validate_action_plan(self, action_plan: Dict[str, Any]) -> None:
        """
        Validate the structure and content of an action plan.
        
        Args:
            action_plan (dict): The action plan to validate
            
        Raises:
            Exception: If action plan is invalid
        """
        # Check required top-level keys
        if "plan" not in action_plan:
            raise Exception("Action plan missing 'plan' key")
        
        if not isinstance(action_plan["plan"], list):
            raise Exception("Action plan 'plan' must be a list")
        
        # Check if plan is empty
        if len(action_plan["plan"]) == 0:
            raise Exception("Action plan cannot be empty")
        
        # Check if plan is too long (safety limit)
        if len(action_plan["plan"]) > 50:
            raise Exception("Action plan too long (maximum 50 steps)")
        
        # Validate each action in the plan
        valid_actions = {"click", "double_click", "type", "scroll", "speak", "finish"}
        
        for i, action in enumerate(action_plan["plan"]):
            if not isinstance(action, dict):
                raise Exception(f"Action {i} must be a dictionary")
            
            if "action" not in action:
                raise Exception(f"Action {i} missing 'action' key")
            
            action_type = action["action"]
            if action_type not in valid_actions:
                raise Exception(f"Invalid action type '{action_type}' in action {i}")
            
            # Validate action-specific parameters
            self._validate_action_parameters(action, i)
        
        # Validate metadata if present
        if "metadata" in action_plan:
            self._validate_metadata(action_plan["metadata"])
    
    def _validate_action_parameters(self, action: Dict[str, Any], index: int) -> None:
        """
        Validate parameters for a specific action.
        
        Args:
            action (dict): The action to validate
            index (int): Action index for error messages
            
        Raises:
            Exception: If action parameters are invalid
        """
        action_type = action["action"]
        
        if action_type in ["click", "double_click"]:
            if "coordinates" not in action:
                raise Exception(f"Action {index} ({action_type}) missing 'coordinates'")
            
            coords = action["coordinates"]
            if not isinstance(coords, list) or len(coords) != 2:
                raise Exception(f"Action {index} coordinates must be [x, y]")
            
            if not all(isinstance(c, (int, float)) and c >= 0 for c in coords):
                raise Exception(f"Action {index} coordinates must be non-negative numbers")
            
            # Validate reasonable coordinate ranges (assuming max 4K resolution)
            if coords[0] > 4000 or coords[1] > 4000:
                raise Exception(f"Action {index} coordinates seem unreasonably large")
        
        elif action_type == "type":
            if "text" not in action:
                raise Exception(f"Action {index} (type) missing 'text'")
            
            if not isinstance(action["text"], str):
                raise Exception(f"Action {index} text must be a string")
            
            # Validate text length (safety limit)
            if len(action["text"]) > 1000:
                raise Exception(f"Action {index} text too long (maximum 1000 characters)")
        
        elif action_type == "scroll":
            if "direction" not in action:
                raise Exception(f"Action {index} (scroll) missing 'direction'")
            
            if action["direction"] not in ["up", "down", "left", "right"]:
                raise Exception(f"Action {index} invalid scroll direction")
            
            if "amount" in action:
                if not isinstance(action["amount"], (int, float)):
                    raise Exception(f"Action {index} scroll amount must be a number")
                if action["amount"] <= 0:
                    raise Exception(f"Action {index} scroll amount must be positive")
                if action["amount"] > 5000:
                    raise Exception(f"Action {index} scroll amount too large (maximum 5000)")
        
        elif action_type == "speak":
            if "message" not in action:
                raise Exception(f"Action {index} (speak) missing 'message'")
            
            if not isinstance(action["message"], str):
                raise Exception(f"Action {index} message must be a string")
            
            # Validate message length (safety limit)
            if len(action["message"]) > 500:
                raise Exception(f"Action {index} message too long (maximum 500 characters)")
        
        elif action_type == "finish":
            # Finish action doesn't need additional parameters
            pass
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Validate metadata structure and values.
        
        Args:
            metadata (dict): The metadata to validate
            
        Raises:
            Exception: If metadata is invalid
        """
        if not isinstance(metadata, dict):
            raise Exception("Metadata must be a dictionary")
        
        # Validate confidence if present
        if "confidence" in metadata:
            confidence = metadata["confidence"]
            if not isinstance(confidence, (int, float)):
                raise Exception("Confidence must be a number")
            if not 0.0 <= confidence <= 1.0:
                raise Exception("Confidence must be between 0.0 and 1.0")
        
        # Validate estimated_duration if present
        if "estimated_duration" in metadata:
            duration = metadata["estimated_duration"]
            if not isinstance(duration, (int, float)):
                raise Exception("Estimated duration must be a number")
            if duration < 0:
                raise Exception("Estimated duration must be non-negative")
    
    def _get_fallback_response(self, error_message: str) -> Dict[str, Any]:
        """
        Generate a fallback response when reasoning fails.
        
        Args:
            error_message (str): The error that occurred
            
        Returns:
            dict: Fallback action plan
        """
        logger.warning(f"Using fallback response due to error: {error_message}")
        
        # Determine appropriate fallback message based on error type
        if "timeout" in error_message.lower() or "timed out" in error_message.lower():
            message = "I'm taking too long to process your request. Please try a simpler command or check your internet connection."
        elif "connection" in error_message.lower() or "connect" in error_message.lower():
            message = "I'm having trouble connecting to my reasoning service. Please check your internet connection and try again."
        elif "parse" in error_message.lower() or "json" in error_message.lower():
            message = "I'm having trouble understanding the response from my reasoning service. Please try rephrasing your request."
        elif "invalid" in error_message.lower():
            message = "I received an invalid response while processing your request. Please try again with a different command."
        else:
            message = f"I encountered an error while processing your request: {error_message}. Please try again."
        
        return {
            "plan": [
                {
                    "action": "speak",
                    "message": message
                },
                {
                    "action": "finish"
                }
            ],
            "metadata": {
                "confidence": 0.0,
                "estimated_duration": 3.0,
                "fallback": True,
                "error": error_message,
                "error_type": self._classify_error(error_message)
            }
        }
    
    def _classify_error(self, error_message: str) -> str:
        """
        Classify the type of error for better handling.
        
        Args:
            error_message (str): The error message
            
        Returns:
            str: Error classification
        """
        error_lower = error_message.lower()
        
        # Check more specific patterns first
        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        elif "connection" in error_lower or "connect" in error_lower:
            return "connection"
        elif "parse" in error_lower or "json" in error_lower:
            return "parsing"
        elif "invalid" in error_lower or "validation" in error_lower:
            return "validation"
        elif "api" in error_lower:
            return "api"
        else:
            return "unknown"
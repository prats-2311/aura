# modules/reasoning.py
"""
AURA Reasoning Module

Handles communication with cloud-based LLMs for intelligent action planning.
Processes user commands and screen context to generate structured action plans.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional
from config import (
    REASONING_API_BASE,
    REASONING_API_KEY,
    REASONING_MODEL,
    REASONING_META_PROMPT,
    REASONING_API_TIMEOUT
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
    
    def get_action_plan(self, user_command: str, screen_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an action plan based on user command and screen context.
        
        Args:
            user_command (str): The natural language command from the user
            screen_context (dict): JSON description of the current screen state
            
        Returns:
            dict: Structured action plan with steps and metadata
            
        Raises:
            Exception: If API communication fails or response is invalid
        """
        try:
            logger.info(f"Generating action plan for command: '{user_command}'")
            
            # Prepare the prompt with user command and screen context
            prompt = self._build_prompt(user_command, screen_context)
            
            # Make API request to cloud LLM
            response = self._make_api_request(prompt)
            
            # Parse and validate the response
            action_plan = self._parse_response(response)
            
            logger.info(f"Generated action plan with {len(action_plan.get('plan', []))} steps")
            return action_plan
            
        except Exception as e:
            logger.error(f"Failed to generate action plan: {str(e)}")
            # Return fallback response
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
        Make API request to the cloud reasoning model.
        
        Args:
            prompt (str): The complete prompt to send
            
        Returns:
            dict: Raw API response
            
        Raises:
            requests.RequestException: If API request fails
        """
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
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise Exception(f"API request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise Exception("Failed to connect to reasoning API")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
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
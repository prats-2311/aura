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

# Try to import Ollama client, fallback to requests if not available
try:
    from ollama import Client
    OLLAMA_CLIENT_AVAILABLE = True
except ImportError:
    OLLAMA_CLIENT_AVAILABLE = False
    Client = None
from .error_handler import (
    global_error_handler,
    with_error_handling,
    ErrorCategory,
    ErrorSeverity
)
from .performance import (
    connection_pool,
    measure_performance,
    PerformanceMetrics,
    performance_monitor
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
        
        # Initialize Ollama client for cloud API
        self.ollama_client = None
        if OLLAMA_CLIENT_AVAILABLE and self.api_key and self.api_key != "your_ollama_cloud_api_key_here":
            try:
                # Use the correct Ollama Cloud endpoint
                self.ollama_client = Client(
                    host="https://ollama.com",
                    headers={'Authorization': self.api_key}
                )
                logger.info("Initialized Ollama client for cloud API")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama client: {e}")
                self.ollama_client = None
        
        if not self.ollama_client:
            logger.info("Using requests method for API calls")
        
        # Validate configuration
        if not self.api_key or self.api_key == "your_ollama_cloud_api_key_here":
            logger.warning("Reasoning API key not configured properly")
        
        logger.info(f"ReasoningModule initialized with model: {self.model}")
    
    @measure_performance("reasoning_analysis", include_system_metrics=True)
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
        Uses Ollama client if available, falls back to requests.
        
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
        
        # Try Ollama client first if available
        if self.ollama_client:
            return self._make_ollama_request(prompt)
        else:
            return self._make_requests_api_call(prompt)
    
    def _make_ollama_request(self, prompt: str) -> Dict[str, Any]:
        """
        Make API request using Ollama client with correct cloud format.
        
        Args:
            prompt (str): The complete prompt to send
            
        Returns:
            dict: API response in OpenAI format
            
        Raises:
            Exception: If API request fails
        """
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # Prepare messages in Ollama format
                messages = [
                    {
                        'role': 'user',
                        'content': prompt,
                    }
                ]
                
                logger.debug(f"Making Ollama Cloud API request (attempt {attempt + 1})")
                
                # Make the request using Ollama client with correct model format
                # Use the model name directly as configured
                response = self.ollama_client.chat(
                    model=self.model,  # e.g., 'gpt-oss:latest' or 'gpt-oss:120b'
                    messages=messages,
                    stream=False
                )
                
                response_time = time.time() - start_time
                logger.debug(f"Ollama Cloud API request completed in {response_time:.2f}s")
                
                # Convert Ollama response to OpenAI format for compatibility
                openai_format_response = {
                    "choices": [
                        {
                            "message": {
                                "content": response['message']['content']
                            }
                        }
                    ]
                }
                
                return openai_format_response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Ollama Cloud API request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
        
        # All retries failed, raise the last error
        error_info = global_error_handler.handle_error(
            error=last_error,
            module="reasoning",
            function="_make_ollama_request",
            category=ErrorCategory.API_ERROR,
            context={"attempts": max_retries, "model": self.model}
        )
        raise Exception(f"Ollama Cloud API request failed: {error_info.user_message}")
    
    def _make_requests_api_call(self, prompt: str) -> Dict[str, Any]:
        """
        Make API request using requests library (fallback method).
        
        Args:
            prompt (str): The complete prompt to send
            
        Returns:
            dict: Raw API response
            
        Raises:
            Exception: If API request fails after retries
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare request payload in Ollama format
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        }
        
        logger.debug(f"Making requests API call to {self.api_base}/v1/chat/completions")
        
        # Use connection pool for better performance
        session = connection_pool.get_session(self.api_base)
        
        # Implement retry logic with exponential backoff
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # For Ollama Cloud, use the correct API endpoint
                # Ollama Cloud uses a different endpoint structure
                endpoint_url = f"{self.api_base}/api/chat"
                
                response = session.post(
                    endpoint_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                response_time = time.time() - start_time
                logger.debug(f"API request completed in {response_time:.2f}s")
                
                # Handle different HTTP status codes
                if response.status_code == 200:
                    try:
                        ollama_response = response.json()
                        # Convert Ollama response to OpenAI format for compatibility
                        openai_format_response = {
                            "choices": [
                                {
                                    "message": {
                                        "content": ollama_response['message']['content']
                                    }
                                }
                            ]
                        }
                        return openai_format_response
                    except json.JSONDecodeError as e:
                        error_info = global_error_handler.handle_error(
                            error=e,
                            module="reasoning",
                            function="_make_requests_api_call",
                            category=ErrorCategory.PROCESSING_ERROR,
                            context={"response_text": response.text[:500]}
                        )
                        raise Exception(f"Invalid JSON response: {error_info.user_message}")
                    except KeyError as e:
                        error_info = global_error_handler.handle_error(
                            error=e,
                            module="reasoning",
                            function="_make_requests_api_call",
                            category=ErrorCategory.PROCESSING_ERROR,
                            context={"response_data": str(ollama_response)[:500]}
                        )
                        raise Exception(f"Unexpected response format: {error_info.user_message}")
                
                elif response.status_code == 401:
                    error_info = global_error_handler.handle_error(
                        error=Exception("Authentication failed"),
                        module="reasoning",
                        function="_make_requests_api_call",
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
                            function="_make_requests_api_call",
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
                            function="_make_requests_api_call",
                            category=ErrorCategory.API_ERROR,
                            context={"status_code": response.status_code, "response": response.text[:500]}
                        )
                        raise Exception(f"API server error: {error_info.user_message}")
                
                else:
                    # Client error - don't retry
                    error_info = global_error_handler.handle_error(
                        error=Exception(f"HTTP {response.status_code}: {response.text}"),
                        module="reasoning",
                        function="_make_requests_api_call",
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
                    function="_make_requests_api_call",
                    category=ErrorCategory.TIMEOUT_ERROR,
                    context={"timeout": self.timeout, "attempts": max_retries}
                )
                raise Exception(f"API timeout after {max_retries} attempts: {error_info.user_message}")
            elif isinstance(last_error, requests.exceptions.ConnectionError):
                error_info = global_error_handler.handle_error(
                    error=last_error,
                    module="reasoning",
                    function="_make_requests_api_call",
                    category=ErrorCategory.NETWORK_ERROR,
                    context={"api_base": self.api_base, "attempts": max_retries}
                )
                raise Exception(f"Cannot connect to reasoning API: {error_info.user_message}")
            else:
                error_info = global_error_handler.handle_error(
                    error=last_error,
                    module="reasoning",
                    function="_make_requests_api_call",
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
    
    @measure_performance("conversational_query", include_system_metrics=True)
    @with_error_handling(
        category=ErrorCategory.API_ERROR,
        severity=ErrorSeverity.MEDIUM,
        max_retries=2,
        retry_delay=1.0,
        user_message="I'm having trouble generating a response. Please try again.",
        fallback_return="I'm sorry, I'm having trouble processing your request right now. Please try again later."
    )
    def process_query(self, query: str, prompt_template: str = None, context: Dict[str, Any] = None) -> str:
        """
        Process a conversational query using the specified prompt template.
        
        Args:
            query (str): The user's conversational query
            prompt_template (str): The prompt template to use (e.g., 'CONVERSATIONAL_PROMPT')
            context (Dict[str, Any]): Additional context for the conversation
            
        Returns:
            str: Generated conversational response
            
        Raises:
            Exception: If API communication fails or response is invalid after retries
        """
        try:
            # Input validation
            if not query or not query.strip():
                raise ValueError("Query cannot be empty")
            
            if len(query) > 2000:
                raise ValueError("Query too long (maximum 2000 characters)")
            
            logger.info(f"Processing conversational query: '{query[:100]}...'")
            
            # Get the prompt template from config
            prompt_template_text = self._get_prompt_template(prompt_template)
            
            # Build the conversational prompt
            try:
                prompt = self._build_conversational_prompt(query, prompt_template_text, context or {})
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="reasoning",
                    function="process_query",
                    category=ErrorCategory.PROCESSING_ERROR,
                    context={"query_length": len(query), "template": prompt_template}
                )
                raise Exception(f"Prompt building failed: {error_info.user_message}")
            
            # Make API request
            try:
                response = self._make_api_request(prompt)
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="reasoning",
                    function="process_query",
                    category=ErrorCategory.API_ERROR,
                    context={"prompt_length": len(prompt)}
                )
                # Return fallback response for API errors
                return self._get_conversational_fallback(str(e))
            
            # Extract conversational response
            try:
                conversational_response = self._extract_conversational_response(response)
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="reasoning",
                    function="process_query",
                    category=ErrorCategory.PROCESSING_ERROR,
                    context={"response_type": type(response).__name__}
                )
                # Return fallback response for parsing errors
                return self._get_conversational_fallback(str(e))
            
            logger.info(f"Generated conversational response: '{conversational_response[:100]}...'")
            return conversational_response
            
        except Exception as e:
            # Final fallback - always return a valid response
            logger.error(f"Failed to process conversational query: {str(e)}")
            return self._get_conversational_fallback(str(e))
    
    def _get_prompt_template(self, template_name: str) -> str:
        """
        Get the prompt template from config.
        
        Args:
            template_name (str): Name of the template (e.g., 'CONVERSATIONAL_PROMPT')
            
        Returns:
            str: The prompt template text
        """
        try:
            # Import config to get the template
            import config
            
            if template_name and hasattr(config, template_name):
                return getattr(config, template_name)
            else:
                # Default conversational prompt
                return """You are AURA, a helpful AI assistant. The user is having a casual conversation with you. 
Respond in a friendly, natural, and helpful manner. Keep responses concise but warm.

User: {query}

Respond naturally as AURA would, being helpful and conversational. Do not provide JSON responses for conversational interactions."""
                
        except Exception as e:
            logger.warning(f"Failed to get prompt template '{template_name}': {e}")
            # Return default template
            return """You are AURA, a helpful AI assistant. Respond to the user's query in a friendly and helpful manner.

User: {query}

Please provide a natural, conversational response."""
    
    def _build_conversational_prompt(self, query: str, template: str, context: Dict[str, Any]) -> str:
        """
        Build the conversational prompt using the template and context.
        
        Args:
            query (str): User's conversational query
            template (str): Prompt template
            context (Dict[str, Any]): Conversation context
            
        Returns:
            str: Complete conversational prompt
        """
        try:
            # Format the template with the query and context
            formatted_prompt = template.format(
                query=query,
                context=context
            )
            
            # Add conversation history if available
            if context.get('conversation_history'):
                history_text = self._format_conversation_history(context['conversation_history'])
                formatted_prompt = f"{formatted_prompt}\n\nRecent conversation:\n{history_text}"
            
            return formatted_prompt
            
        except Exception as e:
            logger.warning(f"Failed to build conversational prompt: {e}")
            # Return simple fallback prompt
            return f"You are AURA, a helpful AI assistant. Please respond to: {query}"
    
    def _format_conversation_history(self, history: list) -> str:
        """
        Format conversation history for inclusion in prompts.
        
        Args:
            history (list): List of conversation exchanges
            
        Returns:
            str: Formatted conversation history
        """
        try:
            formatted_lines = []
            for exchange in history[-3:]:  # Only include last 3 exchanges
                if isinstance(exchange, dict):
                    user_query = exchange.get('user_query', '')
                    aura_response = exchange.get('aura_response', '')
                    if user_query and aura_response:
                        formatted_lines.append(f"User: {user_query}")
                        formatted_lines.append(f"AURA: {aura_response}")
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            logger.warning(f"Failed to format conversation history: {e}")
            return ""
    
    def _extract_conversational_response(self, api_response: Dict[str, Any]) -> str:
        """
        Extract the conversational response from the API response.
        
        Args:
            api_response (dict): Raw API response
            
        Returns:
            str: Extracted conversational response
            
        Raises:
            Exception: If response format is invalid
        """
        try:
            # Extract content from API response
            if "choices" not in api_response or not api_response["choices"]:
                raise Exception("Invalid API response: no choices found")
            
            content = api_response["choices"][0]["message"]["content"]
            
            # Clean up the response
            content = content.strip()
            
            # Remove any JSON formatting if present (shouldn't be for conversational responses)
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            # Remove common prefixes that might be added by the model
            prefixes_to_remove = [
                "AURA: ",
                "Assistant: ",
                "AI: ",
                "Response: "
            ]
            
            for prefix in prefixes_to_remove:
                if content.startswith(prefix):
                    content = content[len(prefix):].strip()
                    break
            
            # Validate response length
            if len(content) > 1000:
                content = content[:1000] + "..."
                logger.warning("Conversational response truncated due to length")
            
            if not content:
                raise Exception("Empty conversational response")
            
            return content
            
        except KeyError as e:
            raise Exception(f"Invalid API response structure: missing {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to extract conversational response: {str(e)}")
    
    def _get_conversational_fallback(self, error_message: str) -> str:
        """
        Generate a fallback conversational response when processing fails.
        
        Args:
            error_message (str): The error that occurred
            
        Returns:
            str: Fallback conversational response
        """
        logger.warning(f"Using conversational fallback due to error: {error_message}")
        
        # Determine appropriate fallback message based on error type
        if "timeout" in error_message.lower() or "timed out" in error_message.lower():
            return "I'm taking a bit longer than usual to process that. Could you try asking again?"
        elif "connection" in error_message.lower() or "connect" in error_message.lower():
            return "I'm having trouble with my connection right now. Please try again in a moment."
        elif "parse" in error_message.lower() or "json" in error_message.lower():
            return "I'm having trouble understanding that request. Could you rephrase it for me?"
        elif "invalid" in error_message.lower():
            return "Something doesn't seem right with that request. Could you try asking differently?"
        elif "empty" in error_message.lower():
            return "I didn't catch what you said. Could you repeat that?"
        else:
            return "I'm having a bit of trouble right now. Please try again, and I'll do my best to help!"

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
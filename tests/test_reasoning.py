# tests/test_reasoning.py
"""
Unit tests for the ReasoningModule.

Tests cloud LLM communication, action plan generation, and validation logic.
"""

import json
import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from modules.reasoning import ReasoningModule


class TestReasoningModule:
    """Test cases for the ReasoningModule class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.reasoning = ReasoningModule()
        
        # Sample screen context for testing
        self.sample_screen_context = {
            "elements": [
                {
                    "type": "button",
                    "text": "Submit",
                    "coordinates": [100, 200, 150, 230],
                    "description": "Submit button"
                },
                {
                    "type": "input",
                    "text": "",
                    "coordinates": [50, 150, 200, 180],
                    "description": "Text input field"
                }
            ],
            "text_blocks": [
                {
                    "content": "Please enter your name",
                    "coordinates": [50, 100, 200, 120]
                }
            ],
            "metadata": {
                "timestamp": "2024-01-01T12:00:00Z",
                "screen_resolution": [1920, 1080]
            }
        }
        
        # Sample valid action plan
        self.sample_action_plan = {
            "plan": [
                {
                    "action": "click",
                    "coordinates": [50, 150]
                },
                {
                    "action": "type",
                    "text": "John Doe"
                },
                {
                    "action": "click",
                    "coordinates": [100, 200]
                },
                {
                    "action": "speak",
                    "message": "Form submitted successfully"
                },
                {
                    "action": "finish"
                }
            ],
            "metadata": {
                "confidence": 0.95,
                "estimated_duration": 5.2
            }
        }
    
    def test_initialization(self):
        """Test ReasoningModule initialization."""
        reasoning = ReasoningModule()
        assert reasoning.api_base is not None
        assert reasoning.model is not None
        assert reasoning.timeout > 0
    
    def test_build_prompt(self):
        """Test prompt building functionality."""
        user_command = "Fill in the form with my name"
        prompt = self.reasoning._build_prompt(user_command, self.sample_screen_context)
        
        assert user_command in prompt
        assert "Submit" in prompt  # From screen context
        assert "Please enter your name" in prompt  # From screen context
        assert "JSON format" in prompt  # From meta prompt
    
    @patch('modules.reasoning.requests.post')
    def test_make_api_request_success(self, mock_post):
        """Test successful API request."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(self.sample_action_plan)
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        prompt = "test prompt"
        result = self.reasoning._make_api_request(prompt)
        
        assert "choices" in result
        mock_post.assert_called_once()
    
    @patch('modules.reasoning.requests.post')
    def test_make_api_request_timeout(self, mock_post):
        """Test API request timeout handling."""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._make_api_request("test prompt")
        
        assert "timed out" in str(exc_info.value)
    
    @patch('modules.reasoning.requests.post')
    def test_make_api_request_connection_error(self, mock_post):
        """Test API connection error handling."""
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._make_api_request("test prompt")
        
        assert "Failed to connect" in str(exc_info.value)
    
    @patch('modules.reasoning.requests.post')
    def test_make_api_request_http_error(self, mock_post):
        """Test API HTTP error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._make_api_request("test prompt")
        
        assert "401" in str(exc_info.value)
    
    def test_parse_response_success(self):
        """Test successful response parsing."""
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(self.sample_action_plan)
                    }
                }
            ]
        }
        
        result = self.reasoning._parse_response(api_response)
        
        assert result == self.sample_action_plan
        assert "plan" in result
        assert len(result["plan"]) == 5
    
    def test_parse_response_with_markdown(self):
        """Test parsing response with markdown code blocks."""
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": f"```json\n{json.dumps(self.sample_action_plan)}\n```"
                    }
                }
            ]
        }
        
        result = self.reasoning._parse_response(api_response)
        
        assert result == self.sample_action_plan
    
    def test_parse_response_invalid_json(self):
        """Test parsing response with invalid JSON."""
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": "invalid json content"
                    }
                }
            ]
        }
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._parse_response(api_response)
        
        assert "Failed to parse JSON" in str(exc_info.value)
    
    def test_parse_response_missing_choices(self):
        """Test parsing response with missing choices."""
        api_response = {}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._parse_response(api_response)
        
        assert "no choices found" in str(exc_info.value)
    
    def test_validate_action_plan_success(self):
        """Test successful action plan validation."""
        # Should not raise any exception
        self.reasoning._validate_action_plan(self.sample_action_plan)
    
    def test_validate_action_plan_missing_plan(self):
        """Test validation with missing plan key."""
        invalid_plan = {"metadata": {}}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_plan(invalid_plan)
        
        assert "missing 'plan' key" in str(exc_info.value)
    
    def test_validate_action_plan_invalid_plan_type(self):
        """Test validation with invalid plan type."""
        invalid_plan = {"plan": "not a list"}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_plan(invalid_plan)
        
        assert "must be a list" in str(exc_info.value)
    
    def test_validate_action_plan_invalid_action_type(self):
        """Test validation with invalid action type."""
        invalid_plan = {
            "plan": [
                {
                    "action": "invalid_action",
                    "coordinates": [100, 200]
                }
            ]
        }
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_plan(invalid_plan)
        
        assert "Invalid action type" in str(exc_info.value)
    
    def test_validate_action_parameters_click_missing_coordinates(self):
        """Test validation of click action missing coordinates."""
        action = {"action": "click"}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_parameters(action, 0)
        
        assert "missing 'coordinates'" in str(exc_info.value)
    
    def test_validate_action_parameters_click_invalid_coordinates(self):
        """Test validation of click action with invalid coordinates."""
        action = {"action": "click", "coordinates": [100]}  # Missing y coordinate
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_parameters(action, 0)
        
        assert "must be [x, y]" in str(exc_info.value)
    
    def test_validate_action_parameters_type_missing_text(self):
        """Test validation of type action missing text."""
        action = {"action": "type"}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_parameters(action, 0)
        
        assert "missing 'text'" in str(exc_info.value)
    
    def test_validate_action_parameters_scroll_invalid_direction(self):
        """Test validation of scroll action with invalid direction."""
        action = {"action": "scroll", "direction": "diagonal", "amount": 100}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_parameters(action, 0)
        
        assert "invalid scroll direction" in str(exc_info.value)
    
    def test_validate_action_parameters_speak_missing_message(self):
        """Test validation of speak action missing message."""
        action = {"action": "speak"}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_parameters(action, 0)
        
        assert "missing 'message'" in str(exc_info.value)
    
    def test_get_fallback_response(self):
        """Test fallback response generation."""
        error_message = "Unknown error occurred"
        fallback = self.reasoning._get_fallback_response(error_message)
        
        assert "plan" in fallback
        assert len(fallback["plan"]) == 2  # speak + finish
        assert fallback["plan"][0]["action"] == "speak"
        assert fallback["plan"][1]["action"] == "finish"
        assert error_message in fallback["plan"][0]["message"]  # For unknown errors, original message is included
        assert fallback["metadata"]["fallback"] is True
    
    @patch('modules.reasoning.requests.post')
    def test_get_action_plan_success(self, mock_post):
        """Test successful action plan generation."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(self.sample_action_plan)
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        user_command = "Fill in the form"
        result = self.reasoning.get_action_plan(user_command, self.sample_screen_context)
        
        assert result == self.sample_action_plan
        assert "plan" in result
        mock_post.assert_called_once()
    
    @patch('modules.reasoning.requests.post')
    def test_get_action_plan_api_failure(self, mock_post):
        """Test action plan generation with API failure."""
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        user_command = "Fill in the form"
        result = self.reasoning.get_action_plan(user_command, self.sample_screen_context)
        
        # Should return fallback response
        assert "plan" in result
        assert result["metadata"]["fallback"] is True
        assert "speak" in [action["action"] for action in result["plan"]]
    
    def test_validate_action_plan_empty_plan(self):
        """Test validation with empty plan."""
        invalid_plan = {"plan": []}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_plan(invalid_plan)
        
        assert "cannot be empty" in str(exc_info.value)
    
    def test_validate_action_plan_too_long(self):
        """Test validation with plan that's too long."""
        invalid_plan = {
            "plan": [{"action": "finish"}] * 51  # More than 50 steps
        }
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_plan(invalid_plan)
        
        assert "too long" in str(exc_info.value)
    
    def test_validate_action_parameters_coordinates_too_large(self):
        """Test validation of click action with unreasonably large coordinates."""
        action = {"action": "click", "coordinates": [5000, 5000]}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_parameters(action, 0)
        
        assert "unreasonably large" in str(exc_info.value)
    
    def test_validate_action_parameters_text_too_long(self):
        """Test validation of type action with text that's too long."""
        action = {"action": "type", "text": "x" * 1001}  # More than 1000 characters
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_parameters(action, 0)
        
        assert "too long" in str(exc_info.value)
    
    def test_validate_action_parameters_scroll_negative_amount(self):
        """Test validation of scroll action with negative amount."""
        action = {"action": "scroll", "direction": "up", "amount": -100}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_parameters(action, 0)
        
        assert "must be positive" in str(exc_info.value)
    
    def test_validate_action_parameters_scroll_amount_too_large(self):
        """Test validation of scroll action with amount that's too large."""
        action = {"action": "scroll", "direction": "up", "amount": 6000}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_parameters(action, 0)
        
        assert "too large" in str(exc_info.value)
    
    def test_validate_action_parameters_speak_message_too_long(self):
        """Test validation of speak action with message that's too long."""
        action = {"action": "speak", "message": "x" * 501}  # More than 500 characters
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_action_parameters(action, 0)
        
        assert "too long" in str(exc_info.value)
    
    def test_validate_action_parameters_finish_action(self):
        """Test validation of finish action (should not raise exception)."""
        action = {"action": "finish"}
        
        # Should not raise any exception
        self.reasoning._validate_action_parameters(action, 0)
    
    def test_validate_metadata_success(self):
        """Test successful metadata validation."""
        metadata = {
            "confidence": 0.95,
            "estimated_duration": 5.2
        }
        
        # Should not raise any exception
        self.reasoning._validate_metadata(metadata)
    
    def test_validate_metadata_invalid_confidence(self):
        """Test metadata validation with invalid confidence."""
        metadata = {"confidence": 1.5}  # Greater than 1.0
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_metadata(metadata)
        
        assert "between 0.0 and 1.0" in str(exc_info.value)
    
    def test_validate_metadata_negative_duration(self):
        """Test metadata validation with negative duration."""
        metadata = {"estimated_duration": -5.0}
        
        with pytest.raises(Exception) as exc_info:
            self.reasoning._validate_metadata(metadata)
        
        assert "non-negative" in str(exc_info.value)
    
    def test_classify_error_timeout(self):
        """Test error classification for timeout errors."""
        error_type = self.reasoning._classify_error("API request timed out after 30 seconds")
        assert error_type == "timeout"
    
    def test_classify_error_connection(self):
        """Test error classification for connection errors."""
        error_type = self.reasoning._classify_error("Failed to connect to reasoning API")
        assert error_type == "connection"
    
    def test_classify_error_parsing(self):
        """Test error classification for parsing errors."""
        error_type = self.reasoning._classify_error("Failed to parse JSON response")
        assert error_type == "parsing"
    
    def test_classify_error_validation(self):
        """Test error classification for validation errors."""
        error_type = self.reasoning._classify_error("Invalid action type in plan")
        assert error_type == "validation"
    
    def test_classify_error_unknown(self):
        """Test error classification for unknown errors."""
        error_type = self.reasoning._classify_error("Something went wrong")
        assert error_type == "unknown"
    
    def test_fallback_response_timeout_error(self):
        """Test fallback response for timeout errors."""
        fallback = self.reasoning._get_fallback_response("Request timed out")
        
        assert "taking too long" in fallback["plan"][0]["message"]
        assert fallback["metadata"]["error_type"] == "timeout"
    
    def test_fallback_response_connection_error(self):
        """Test fallback response for connection errors."""
        fallback = self.reasoning._get_fallback_response("Connection failed")
        
        assert "trouble connecting" in fallback["plan"][0]["message"]
        assert fallback["metadata"]["error_type"] == "connection"


if __name__ == "__main__":
    pytest.main([__file__])
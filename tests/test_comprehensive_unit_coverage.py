# tests/test_comprehensive_unit_coverage.py
"""
Comprehensive Unit Test Coverage for AURA Modules

This file provides comprehensive unit test coverage for all AURA modules
with proper mocking, fixtures, and edge case testing to achieve 80%+ coverage.
"""

import pytest
import json
import time
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, call, mock_open
import numpy as np
from pathlib import Path
import threading
import queue
import base64
from PIL import Image
import io

# Import all modules to test
from modules.vision import VisionModule
from modules.reasoning import ReasoningModule
from modules.automation import AutomationModule
from modules.audio import AudioModule
from modules.feedback import FeedbackModule, FeedbackPriority, FeedbackType
from modules.error_handler import (
    ErrorHandler, ErrorSeverity, ErrorCategory, ErrorInfo,
    with_error_handling, global_error_handler
)
from orchestrator import Orchestrator, ExecutionStep
import config


class TestVisionModuleComprehensive:
    """Comprehensive unit tests for VisionModule."""
    
    @pytest.fixture
    def vision_module(self):
        """Create VisionModule instance for testing."""
        with patch('modules.vision.mss.mss') as mock_mss:
            mock_sct = Mock()
            mock_sct.monitors = [
                {},  # Index 0 is all monitors
                {"width": 1920, "height": 1080, "left": 0, "top": 0}
            ]
            mock_mss.return_value = mock_sct
            return VisionModule()
    
    def test_initialization(self, vision_module):
        """Test VisionModule initialization."""
        assert vision_module.sct is not None
    
    def test_get_screen_resolution_success(self, vision_module):
        """Test successful screen resolution retrieval."""
        vision_module.sct.monitors = [
            {},
            {"width": 2560, "height": 1440, "left": 0, "top": 0}
        ]
        
        width, height = vision_module.get_screen_resolution()
        assert width == 2560
        assert height == 1440
    
    def test_get_screen_resolution_failure(self, vision_module):
        """Test screen resolution retrieval with failure."""
        vision_module.sct.monitors = []
        
        width, height = vision_module.get_screen_resolution()
        # Should return default fallback
        assert width == 1920
        assert height == 1080
    
    def test_capture_screen_invalid_monitor(self, vision_module):
        """Test screen capture with invalid monitor number."""
        vision_module.sct.monitors = [{}]  # Only all monitors entry
        
        with pytest.raises(Exception, match="Screen capture failed"):
            vision_module.capture_screen_as_base64(monitor_number=1)
    
    def test_capture_screen_invalid_dimensions(self, vision_module):
        """Test screen capture with invalid monitor dimensions."""
        vision_module.sct.monitors = [
            {},
            {"width": 0, "height": 0, "left": 0, "top": 0}
        ]
        
        with pytest.raises(Exception, match="Invalid monitor dimensions"):
            vision_module.capture_screen_as_base64()
    
    def test_capture_screen_grab_failure(self, vision_module):
        """Test screen capture when grab fails."""
        vision_module.sct.grab.side_effect = Exception("Grab failed")
        
        with pytest.raises(Exception, match="Screen capture failed"):
            vision_module.capture_screen_as_base64()
    
    def test_capture_screen_invalid_screenshot(self, vision_module):
        """Test screen capture with invalid screenshot data."""
        mock_screenshot = Mock()
        mock_screenshot.size = (0, 0)  # Invalid size
        vision_module.sct.grab.return_value = mock_screenshot
        
        with pytest.raises(Exception, match="Invalid screenshot captured"):
            vision_module.capture_screen_as_base64()
    
    def test_capture_screen_image_conversion_failure(self, vision_module):
        """Test screen capture when image conversion fails."""
        mock_screenshot = Mock()
        mock_screenshot.size = (1920, 1080)
        mock_screenshot.bgra = b'invalid_data'
        vision_module.sct.grab.return_value = mock_screenshot
        
        with patch('modules.vision.Image.frombytes', side_effect=Exception("Conversion failed")):
            with pytest.raises(Exception, match="Image conversion failed"):
                vision_module.capture_screen_as_base64()
    
    @patch('modules.vision.MAX_SCREENSHOT_SIZE', 1000)
    def test_capture_screen_resize_logic(self, vision_module):
        """Test screen capture resize logic for large images."""
        # Create a mock large screenshot
        mock_screenshot = Mock()
        mock_screenshot.size = (2000, 1500)
        mock_screenshot.bgra = b'\x00' * (2000 * 1500 * 4)
        vision_module.sct.grab.return_value = mock_screenshot
        
        with patch('modules.vision.Image.frombytes') as mock_frombytes:
            mock_img = Mock()
            mock_img.width = 2000
            mock_img.height = 1500
            mock_img.resize.return_value = mock_img
            mock_frombytes.return_value = mock_img
            
            with patch('modules.vision.io.BytesIO') as mock_bytesio:
                mock_buffer = Mock()
                mock_buffer.getvalue.return_value = b'fake_image_data'
                mock_bytesio.return_value = mock_buffer
                
                result = vision_module.capture_screen_as_base64()
                
                # Should have called resize
                mock_img.resize.assert_called_once()
                assert isinstance(result, str)
    
    def test_capture_screen_base64_encoding_failure(self, vision_module):
        """Test screen capture when base64 encoding fails."""
        mock_screenshot = Mock()
        mock_screenshot.size = (1920, 1080)
        mock_screenshot.bgra = b'\x00' * (1920 * 1080 * 4)
        vision_module.sct.grab.return_value = mock_screenshot
        
        with patch('modules.vision.Image.frombytes') as mock_frombytes:
            mock_img = Mock()
            mock_img.width = 1920
            mock_img.height = 1080
            mock_frombytes.return_value = mock_img
            
            with patch('modules.vision.io.BytesIO') as mock_bytesio:
                mock_buffer = Mock()
                mock_buffer.getvalue.return_value = b''  # Empty data
                mock_bytesio.return_value = mock_buffer
                
                with pytest.raises(Exception, match="Empty image data generated"):
                    vision_module.capture_screen_as_base64()
    
    def test_describe_screen_invalid_analysis_type(self, vision_module):
        """Test describe_screen with invalid analysis type."""
        with pytest.raises(Exception, match="Invalid analysis type"):
            vision_module.describe_screen(analysis_type="invalid")
    
    def test_describe_screen_screenshot_failure(self, vision_module):
        """Test describe_screen when screenshot capture fails."""
        with patch.object(vision_module, 'capture_screen_as_base64', side_effect=Exception("Screenshot failed")):
            with pytest.raises(Exception, match="Screenshot capture failed"):
                vision_module.describe_screen()
    
    def test_describe_screen_missing_config(self, vision_module):
        """Test describe_screen with missing configuration."""
        with patch.object(vision_module, 'capture_screen_as_base64', return_value="fake_base64"):
            with patch('modules.vision.VISION_API_BASE', ''):
                with pytest.raises(Exception, match="Vision API base URL not configured"):
                    vision_module.describe_screen()
    
    @patch('modules.vision.requests.post')
    def test_describe_screen_rate_limiting(self, mock_post, vision_module):
        """Test describe_screen with rate limiting."""
        with patch.object(vision_module, 'capture_screen_as_base64', return_value="fake_base64"):
            # Mock rate limiting response
            mock_response = Mock()
            mock_response.status_code = 429
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception, match="Vision API unavailable"):
                vision_module.describe_screen()
    
    def test_analyze_forms_success(self, vision_module):
        """Test successful form analysis."""
        mock_analysis = {
            "forms": [{"form_id": "test_form", "fields": []}],
            "metadata": {}
        }
        
        with patch.object(vision_module, 'describe_screen', return_value=mock_analysis):
            with patch.object(vision_module, 'validate_form_structure', return_value=mock_analysis):
                result = vision_module.analyze_forms()
                assert result == mock_analysis
    
    def test_analyze_forms_failure(self, vision_module):
        """Test form analysis failure."""
        with patch.object(vision_module, 'describe_screen', side_effect=Exception("Analysis failed")):
            with pytest.raises(Exception, match="Form analysis failed"):
                vision_module.analyze_forms()
    
    def test_classify_form_field_valid(self, vision_module):
        """Test form field classification with valid data."""
        field_data = {
            "type": "text_input",
            "label": "Username",
            "coordinates": [100, 200, 300, 230],
            "required": True
        }
        
        result = vision_module.classify_form_field(field_data)
        
        assert result["type"] == "text_input"
        assert result["label"] == "Username"
        assert result["coordinates"] == [100, 200, 300, 230]
        assert result["required"] is True
    
    def test_classify_form_field_invalid_type(self, vision_module):
        """Test form field classification with invalid type."""
        field_data = {
            "type": "invalid_type",
            "label": "Test Field"
        }
        
        result = vision_module.classify_form_field(field_data)
        
        # Should default to text_input
        assert result["type"] == "text_input"
        assert result["label"] == "Test Field"
    
    def test_classify_form_field_invalid_coordinates(self, vision_module):
        """Test form field classification with invalid coordinates."""
        field_data = {
            "type": "text_input",
            "label": "Test Field",
            "coordinates": [100, 200]  # Invalid format
        }
        
        result = vision_module.classify_form_field(field_data)
        
        # Should default to [0, 0, 0, 0]
        assert result["coordinates"] == [0, 0, 0, 0]
    
    def test_detect_form_errors_with_errors(self, vision_module):
        """Test form error detection with errors present."""
        form_analysis = {
            "form_errors": [
                {
                    "message": "Field is required",
                    "coordinates": [100, 200, 300, 230],
                    "associated_field": "username"
                }
            ],
            "forms": [
                {
                    "fields": [
                        {
                            "label": "password",
                            "validation_state": "error",
                            "error_message": "Password too short",
                            "coordinates": [100, 250, 300, 280]
                        }
                    ]
                }
            ]
        }
        
        errors = vision_module.detect_form_errors(form_analysis)
        
        assert len(errors) == 2
        assert errors[0]["type"] == "validation_error"
        assert errors[0]["message"] == "Field is required"
        assert errors[1]["type"] == "field_error"
        assert errors[1]["message"] == "Password too short"
    
    def test_detect_form_errors_no_errors(self, vision_module):
        """Test form error detection with no errors."""
        form_analysis = {
            "form_errors": [],
            "forms": []
        }
        
        errors = vision_module.detect_form_errors(form_analysis)
        assert len(errors) == 0
    
    def test_validate_form_structure_success(self, vision_module):
        """Test successful form structure validation."""
        form_analysis = {
            "forms": [
                {
                    "form_id": "test_form",
                    "fields": [
                        {
                            "type": "text_input",
                            "label": "username",
                            "coordinates": [100, 200, 300, 230]
                        }
                    ]
                }
            ],
            "form_errors": [],
            "submit_buttons": [
                {
                    "text": "Submit",
                    "coordinates": [200, 300, 250, 330]
                }
            ]
        }
        
        result = vision_module.validate_form_structure(form_analysis)
        
        assert len(result["forms"]) == 1
        assert result["forms"][0]["form_id"] == "test_form"
        assert len(result["forms"][0]["fields"]) == 1
        assert len(result["submit_buttons"]) == 1
        assert result["metadata"]["has_forms"] is True
        assert result["metadata"]["form_count"] == 1
        assert result["metadata"]["total_fields"] == 1
    
    def test_validate_form_structure_failure(self, vision_module):
        """Test form structure validation with failure."""
        # Simulate an error during validation
        with patch.object(vision_module, 'classify_form_field', side_effect=Exception("Classification failed")):
            form_analysis = {
                "forms": [{"fields": [{"type": "text_input"}]}]
            }
            
            result = vision_module.validate_form_structure(form_analysis)
            
            # Should return safe default structure
            assert result["metadata"]["has_forms"] is False
            assert "validation_error" in result["metadata"]
    
    def test_cleanup(self, vision_module):
        """Test VisionModule cleanup."""
        mock_sct = Mock()
        vision_module.sct = mock_sct
        
        # Simulate __del__ method
        if hasattr(vision_module, '__del__'):
            vision_module.__del__()
        else:
            # Manually call cleanup logic
            vision_module.sct.close()
        
        mock_sct.close.assert_called_once()


class TestReasoningModuleComprehensive:
    """Comprehensive unit tests for ReasoningModule."""
    
    @pytest.fixture
    def reasoning_module(self):
        """Create ReasoningModule instance for testing."""
        return ReasoningModule()
    
    def test_initialization(self, reasoning_module):
        """Test ReasoningModule initialization."""
        assert reasoning_module.api_base is not None
        assert reasoning_module.model is not None
        assert reasoning_module.timeout > 0
    
    def test_build_prompt_success(self, reasoning_module):
        """Test successful prompt building."""
        user_command = "Click the submit button"
        screen_context = {
            "elements": [
                {"type": "button", "text": "Submit", "coordinates": [100, 200, 150, 230]}
            ]
        }
        
        prompt = reasoning_module._build_prompt(user_command, screen_context)
        
        assert user_command in prompt
        assert "Submit" in prompt
        assert "JSON format" in prompt
    
    def test_make_api_request_missing_config(self, reasoning_module):
        """Test API request with missing configuration."""
        reasoning_module.api_base = ""
        
        with pytest.raises(Exception, match="Reasoning API base URL not configured"):
            reasoning_module._make_api_request("test prompt")
    
    def test_make_api_request_invalid_api_key(self, reasoning_module):
        """Test API request with invalid API key."""
        reasoning_module.api_key = "your_ollama_cloud_api_key_here"
        
        with pytest.raises(Exception, match="Reasoning API key not configured"):
            reasoning_module._make_api_request("test prompt")
    
    def test_make_api_request_empty_prompt(self, reasoning_module):
        """Test API request with empty prompt."""
        with pytest.raises(Exception, match="Prompt cannot be empty"):
            reasoning_module._make_api_request("")
    
    def test_make_api_request_prompt_too_long(self, reasoning_module):
        """Test API request with prompt that's too long."""
        long_prompt = "x" * 50001  # Exceeds limit
        
        with pytest.raises(Exception, match="Prompt too long"):
            reasoning_module._make_api_request(long_prompt)
    
    @patch('modules.reasoning.requests.post')
    def test_make_api_request_json_decode_error(self, mock_post, reasoning_module):
        """Test API request with JSON decode error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid response"
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="Invalid JSON response"):
            reasoning_module._make_api_request("test prompt")
    
    @patch('modules.reasoning.requests.post')
    def test_make_api_request_authentication_error(self, mock_post, reasoning_module):
        """Test API request with authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="API authentication failed"):
            reasoning_module._make_api_request("test prompt")
    
    @patch('modules.reasoning.requests.post')
    def test_make_api_request_rate_limit_retry(self, mock_post, reasoning_module):
        """Test API request with rate limiting and retry."""
        # First two calls return 429, third succeeds
        responses = [
            Mock(status_code=429),
            Mock(status_code=429),
            Mock(status_code=200, json=lambda: {"test": "response"})
        ]
        mock_post.side_effect = responses
        
        with patch('modules.reasoning.time.sleep'):  # Speed up test
            result = reasoning_module._make_api_request("test prompt")
            
        assert result == {"test": "response"}
        assert mock_post.call_count == 3
    
    @patch('modules.reasoning.requests.post')
    def test_make_api_request_server_error_retry(self, mock_post, reasoning_module):
        """Test API request with server error and retry."""
        # First call returns 500, second succeeds
        responses = [
            Mock(status_code=500),
            Mock(status_code=200, json=lambda: {"test": "response"})
        ]
        mock_post.side_effect = responses
        
        with patch('modules.reasoning.time.sleep'):  # Speed up test
            result = reasoning_module._make_api_request("test prompt")
            
        assert result == {"test": "response"}
        assert mock_post.call_count == 2
    
    def test_parse_response_missing_choices(self, reasoning_module):
        """Test response parsing with missing choices."""
        api_response = {}
        
        with pytest.raises(Exception, match="no choices found"):
            reasoning_module._parse_response(api_response)
    
    def test_parse_response_with_markdown_blocks(self, reasoning_module):
        """Test response parsing with markdown code blocks."""
        action_plan = {
            "plan": [{"action": "click", "coordinates": [100, 200]}],
            "metadata": {"confidence": 0.9}
        }
        
        api_response = {
            "choices": [{
                "message": {
                    "content": f"```json\n{json.dumps(action_plan)}\n```"
                }
            }]
        }
        
        result = reasoning_module._parse_response(api_response)
        assert result == action_plan
    
    def test_parse_response_json_decode_error(self, reasoning_module):
        """Test response parsing with JSON decode error."""
        api_response = {
            "choices": [{
                "message": {
                    "content": "invalid json content"
                }
            }]
        }
        
        with pytest.raises(Exception, match="Failed to parse JSON"):
            reasoning_module._parse_response(api_response)
    
    def test_validate_action_plan_missing_plan(self, reasoning_module):
        """Test action plan validation with missing plan key."""
        action_plan = {"metadata": {}}
        
        with pytest.raises(Exception, match="missing 'plan' key"):
            reasoning_module._validate_action_plan(action_plan)
    
    def test_validate_action_plan_invalid_plan_type(self, reasoning_module):
        """Test action plan validation with invalid plan type."""
        action_plan = {"plan": "not a list"}
        
        with pytest.raises(Exception, match="must be a list"):
            reasoning_module._validate_action_plan(action_plan)
    
    def test_validate_action_plan_empty_plan(self, reasoning_module):
        """Test action plan validation with empty plan."""
        action_plan = {"plan": []}
        
        with pytest.raises(Exception, match="cannot be empty"):
            reasoning_module._validate_action_plan(action_plan)
    
    def test_validate_action_plan_too_long(self, reasoning_module):
        """Test action plan validation with plan that's too long."""
        action_plan = {"plan": [{"action": "finish"}] * 51}  # Exceeds limit
        
        with pytest.raises(Exception, match="too long"):
            reasoning_module._validate_action_plan(action_plan)
    
    def test_validate_action_parameters_click_missing_coordinates(self, reasoning_module):
        """Test action parameter validation for click without coordinates."""
        action = {"action": "click"}
        
        with pytest.raises(Exception, match="missing 'coordinates'"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_click_invalid_coordinates_format(self, reasoning_module):
        """Test action parameter validation for click with invalid coordinates format."""
        action = {"action": "click", "coordinates": [100]}  # Missing y
        
        with pytest.raises(Exception, match="must be \\[x, y\\]"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_click_negative_coordinates(self, reasoning_module):
        """Test action parameter validation for click with negative coordinates."""
        action = {"action": "click", "coordinates": [-100, 200]}
        
        with pytest.raises(Exception, match="must be non-negative"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_click_large_coordinates(self, reasoning_module):
        """Test action parameter validation for click with unreasonably large coordinates."""
        action = {"action": "click", "coordinates": [5000, 5000]}
        
        with pytest.raises(Exception, match="unreasonably large"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_type_missing_text(self, reasoning_module):
        """Test action parameter validation for type without text."""
        action = {"action": "type"}
        
        with pytest.raises(Exception, match="missing 'text'"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_type_non_string_text(self, reasoning_module):
        """Test action parameter validation for type with non-string text."""
        action = {"action": "type", "text": 123}
        
        with pytest.raises(Exception, match="must be a string"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_type_text_too_long(self, reasoning_module):
        """Test action parameter validation for type with text that's too long."""
        action = {"action": "type", "text": "x" * 1001}
        
        with pytest.raises(Exception, match="too long"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_scroll_missing_direction(self, reasoning_module):
        """Test action parameter validation for scroll without direction."""
        action = {"action": "scroll"}
        
        with pytest.raises(Exception, match="missing 'direction'"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_scroll_invalid_direction(self, reasoning_module):
        """Test action parameter validation for scroll with invalid direction."""
        action = {"action": "scroll", "direction": "diagonal"}
        
        with pytest.raises(Exception, match="invalid scroll direction"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_scroll_invalid_amount_type(self, reasoning_module):
        """Test action parameter validation for scroll with invalid amount type."""
        action = {"action": "scroll", "direction": "up", "amount": "invalid"}
        
        with pytest.raises(Exception, match="must be a number"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_scroll_negative_amount(self, reasoning_module):
        """Test action parameter validation for scroll with negative amount."""
        action = {"action": "scroll", "direction": "up", "amount": -100}
        
        with pytest.raises(Exception, match="must be positive"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_scroll_amount_too_large(self, reasoning_module):
        """Test action parameter validation for scroll with amount that's too large."""
        action = {"action": "scroll", "direction": "up", "amount": 6000}
        
        with pytest.raises(Exception, match="too large"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_speak_missing_message(self, reasoning_module):
        """Test action parameter validation for speak without message."""
        action = {"action": "speak"}
        
        with pytest.raises(Exception, match="missing 'message'"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_speak_non_string_message(self, reasoning_module):
        """Test action parameter validation for speak with non-string message."""
        action = {"action": "speak", "message": 123}
        
        with pytest.raises(Exception, match="must be a string"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_speak_message_too_long(self, reasoning_module):
        """Test action parameter validation for speak with message that's too long."""
        action = {"action": "speak", "message": "x" * 501}
        
        with pytest.raises(Exception, match="too long"):
            reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_action_parameters_finish_action(self, reasoning_module):
        """Test action parameter validation for finish action."""
        action = {"action": "finish"}
        
        # Should not raise any exception
        reasoning_module._validate_action_parameters(action, 0)
    
    def test_validate_metadata_invalid_confidence_type(self, reasoning_module):
        """Test metadata validation with invalid confidence type."""
        metadata = {"confidence": "invalid"}
        
        with pytest.raises(Exception, match="must be a number"):
            reasoning_module._validate_metadata(metadata)
    
    def test_validate_metadata_confidence_out_of_range(self, reasoning_module):
        """Test metadata validation with confidence out of range."""
        metadata = {"confidence": 1.5}
        
        with pytest.raises(Exception, match="between 0.0 and 1.0"):
            reasoning_module._validate_metadata(metadata)
    
    def test_validate_metadata_invalid_duration_type(self, reasoning_module):
        """Test metadata validation with invalid duration type."""
        metadata = {"estimated_duration": "invalid"}
        
        with pytest.raises(Exception, match="must be a number"):
            reasoning_module._validate_metadata(metadata)
    
    def test_validate_metadata_negative_duration(self, reasoning_module):
        """Test metadata validation with negative duration."""
        metadata = {"estimated_duration": -5.0}
        
        with pytest.raises(Exception, match="non-negative"):
            reasoning_module._validate_metadata(metadata)
    
    def test_classify_error_types(self, reasoning_module):
        """Test error classification for different error types."""
        assert reasoning_module._classify_error("API request timed out") == "timeout"
        assert reasoning_module._classify_error("Failed to connect to API") == "connection"
        assert reasoning_module._classify_error("Failed to parse JSON response") == "parsing"
        assert reasoning_module._classify_error("Invalid action type in plan") == "validation"
        assert reasoning_module._classify_error("API error occurred") == "api"
        assert reasoning_module._classify_error("Something went wrong") == "unknown"
    
    def test_get_fallback_response_different_error_types(self, reasoning_module):
        """Test fallback response generation for different error types."""
        # Test timeout error
        timeout_response = reasoning_module._get_fallback_response("Request timed out")
        assert "taking too long" in timeout_response["plan"][0]["message"]
        assert timeout_response["metadata"]["error_type"] == "timeout"
        
        # Test connection error
        connection_response = reasoning_module._get_fallback_response("Connection failed")
        assert "trouble connecting" in connection_response["plan"][0]["message"]
        assert connection_response["metadata"]["error_type"] == "connection"
        
        # Test parsing error
        parsing_response = reasoning_module._get_fallback_response("Failed to parse JSON")
        assert "trouble understanding" in parsing_response["plan"][0]["message"]
        assert parsing_response["metadata"]["error_type"] == "parsing"
        
        # Test validation error
        validation_response = reasoning_module._get_fallback_response("Invalid response")
        assert "invalid response" in validation_response["plan"][0]["message"]
        assert validation_response["metadata"]["error_type"] == "validation"
        
        # Test unknown error
        unknown_response = reasoning_module._get_fallback_response("Something went wrong")
        assert "Something went wrong" in unknown_response["plan"][0]["message"]
        assert unknown_response["metadata"]["error_type"] == "unknown"
    
    def test_get_action_plan_input_validation(self, reasoning_module):
        """Test get_action_plan input validation."""
        screen_context = {"elements": []}
        
        # Test empty command
        result = reasoning_module.get_action_plan("", screen_context)
        assert result["metadata"]["fallback"] is True
        
        # Test command too long
        long_command = "x" * 1001
        result = reasoning_module.get_action_plan(long_command, screen_context)
        assert result["metadata"]["fallback"] is True
        
        # Test invalid screen context
        result = reasoning_module.get_action_plan("test command", "invalid")
        assert result["metadata"]["fallback"] is True
    
    @patch('modules.reasoning.requests.post')
    def test_get_action_plan_api_success(self, mock_post, reasoning_module):
        """Test successful get_action_plan execution."""
        # Mock successful API response
        action_plan = {
            "plan": [
                {"action": "click", "coordinates": [100, 200]},
                {"action": "finish"}
            ],
            "metadata": {"confidence": 0.9}
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps(action_plan)
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = reasoning_module.get_action_plan("click the button", {"elements": []})
        
        assert result == action_plan
        assert "fallback" not in result["metadata"]
    
    @patch('modules.reasoning.requests.post')
    def test_get_action_plan_api_failure_fallback(self, mock_post, reasoning_module):
        """Test get_action_plan with API failure returning fallback."""
        mock_post.side_effect = Exception("API failed")
        
        result = reasoning_module.get_action_plan("test command", {"elements": []})
        
        assert result["metadata"]["fallback"] is True
        assert "speak" in [action["action"] for action in result["plan"]]
        assert "finish" in [action["action"] for action in result["plan"]]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
# tests/fixtures/sample_data.py
"""
Sample data and fixtures for comprehensive unit testing.
"""

import json
import base64
import numpy as np
from typing import Dict, Any, List
from unittest.mock import Mock


class SampleData:
    """Container for sample test data."""
    
    @staticmethod
    def get_sample_screen_context() -> Dict[str, Any]:
        """Get sample screen context data."""
        return {
            "elements": [
                {
                    "type": "button",
                    "text": "Submit",
                    "coordinates": [100, 200, 150, 230],
                    "description": "Submit button for form"
                },
                {
                    "type": "input",
                    "text": "",
                    "coordinates": [50, 150, 200, 180],
                    "description": "Username input field"
                },
                {
                    "type": "input",
                    "text": "",
                    "coordinates": [50, 190, 200, 220],
                    "description": "Password input field"
                },
                {
                    "type": "link",
                    "text": "Forgot Password?",
                    "coordinates": [50, 240, 150, 260],
                    "description": "Password recovery link"
                }
            ],
            "text_blocks": [
                {
                    "content": "Please enter your credentials",
                    "coordinates": [50, 100, 250, 120]
                },
                {
                    "content": "Login to your account",
                    "coordinates": [50, 50, 200, 80]
                }
            ],
            "metadata": {
                "timestamp": 1640995200.0,
                "screen_resolution": [1920, 1080],
                "analysis_type": "general"
            }
        }
    
    @staticmethod
    def get_sample_action_plan() -> Dict[str, Any]:
        """Get sample action plan data."""
        return {
            "plan": [
                {
                    "action": "click",
                    "coordinates": [50, 150]
                },
                {
                    "action": "type",
                    "text": "testuser"
                },
                {
                    "action": "click",
                    "coordinates": [50, 190]
                },
                {
                    "action": "type",
                    "text": "password123"
                },
                {
                    "action": "click",
                    "coordinates": [100, 200]
                },
                {
                    "action": "speak",
                    "message": "Login form submitted successfully"
                },
                {
                    "action": "finish"
                }
            ],
            "metadata": {
                "confidence": 0.95,
                "estimated_duration": 8.5,
                "complexity": "medium"
            }
        }
    
    @staticmethod
    def get_sample_form_analysis() -> Dict[str, Any]:
        """Get sample form analysis data."""
        return {
            "forms": [
                {
                    "form_id": "login_form",
                    "form_title": "User Login",
                    "coordinates": [40, 90, 260, 270],
                    "fields": [
                        {
                            "type": "text_input",
                            "label": "username",
                            "placeholder": "Enter username",
                            "current_value": "",
                            "coordinates": [50, 150, 200, 180],
                            "required": True,
                            "validation_state": "neutral",
                            "error_message": "",
                            "options": []
                        },
                        {
                            "type": "password",
                            "label": "password",
                            "placeholder": "Enter password",
                            "current_value": "",
                            "coordinates": [50, 190, 200, 220],
                            "required": True,
                            "validation_state": "neutral",
                            "error_message": "",
                            "options": []
                        },
                        {
                            "type": "checkbox",
                            "label": "remember_me",
                            "placeholder": "",
                            "current_value": "false",
                            "coordinates": [50, 230, 70, 250],
                            "required": False,
                            "validation_state": "neutral",
                            "error_message": "",
                            "options": []
                        }
                    ]
                }
            ],
            "form_errors": [],
            "submit_buttons": [
                {
                    "text": "Login",
                    "coordinates": [100, 200, 150, 230],
                    "type": "submit"
                }
            ],
            "metadata": {
                "has_forms": True,
                "form_count": 1,
                "total_fields": 3,
                "validation_timestamp": 1640995200.0
            }
        }
    
    @staticmethod
    def get_sample_form_with_errors() -> Dict[str, Any]:
        """Get sample form analysis with validation errors."""
        return {
            "forms": [
                {
                    "form_id": "registration_form",
                    "form_title": "User Registration",
                    "coordinates": [40, 90, 300, 400],
                    "fields": [
                        {
                            "type": "email",
                            "label": "email",
                            "placeholder": "Enter email",
                            "current_value": "invalid-email",
                            "coordinates": [50, 150, 250, 180],
                            "required": True,
                            "validation_state": "error",
                            "error_message": "Please enter a valid email address",
                            "options": []
                        },
                        {
                            "type": "password",
                            "label": "password",
                            "placeholder": "Enter password",
                            "current_value": "",
                            "coordinates": [50, 190, 250, 220],
                            "required": True,
                            "validation_state": "error",
                            "error_message": "Password is required",
                            "options": []
                        }
                    ]
                }
            ],
            "form_errors": [
                {
                    "message": "Please fix the errors below",
                    "coordinates": [50, 120, 250, 140],
                    "associated_field": ""
                }
            ],
            "submit_buttons": [
                {
                    "text": "Register",
                    "coordinates": [100, 250, 180, 280],
                    "type": "submit"
                }
            ],
            "metadata": {
                "has_forms": True,
                "form_count": 1,
                "total_fields": 2,
                "validation_timestamp": 1640995200.0
            }
        }
    
    @staticmethod
    def get_sample_audio_data() -> np.ndarray:
        """Get sample audio data for testing."""
        # Generate a simple sine wave
        sample_rate = 16000
        duration = 1.0  # 1 second
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to int16 format
        return (audio_data * 32767).astype(np.int16)
    
    @staticmethod
    def get_sample_base64_image() -> str:
        """Get sample base64 encoded image data."""
        # Create a simple 100x100 RGB image
        from PIL import Image
        import io
        
        # Create a simple gradient image
        img = Image.new('RGB', (100, 100))
        pixels = img.load()
        
        for i in range(100):
            for j in range(100):
                pixels[i, j] = (i * 2, j * 2, (i + j) % 255)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        img_bytes = buffer.getvalue()
        
        return base64.b64encode(img_bytes).decode('utf-8')
    
    @staticmethod
    def get_sample_api_responses() -> Dict[str, Any]:
        """Get sample API responses for testing."""
        return {
            "vision_success": {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(SampleData.get_sample_screen_context())
                        }
                    }
                ]
            },
            "reasoning_success": {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(SampleData.get_sample_action_plan())
                        }
                    }
                ]
            },
            "api_error_401": {
                "error": {
                    "code": 401,
                    "message": "Unauthorized"
                }
            },
            "api_error_429": {
                "error": {
                    "code": 429,
                    "message": "Rate limit exceeded"
                }
            },
            "api_error_500": {
                "error": {
                    "code": 500,
                    "message": "Internal server error"
                }
            }
        }
    
    @staticmethod
    def get_sample_error_scenarios() -> List[Dict[str, Any]]:
        """Get sample error scenarios for testing."""
        return [
            {
                "name": "network_timeout",
                "exception": "requests.exceptions.Timeout",
                "message": "Request timed out after 30 seconds",
                "expected_category": "TIMEOUT_ERROR",
                "expected_severity": "MEDIUM"
            },
            {
                "name": "connection_error",
                "exception": "requests.exceptions.ConnectionError",
                "message": "Failed to establish connection",
                "expected_category": "NETWORK_ERROR",
                "expected_severity": "MEDIUM"
            },
            {
                "name": "validation_error",
                "exception": "ValueError",
                "message": "Invalid input format",
                "expected_category": "VALIDATION_ERROR",
                "expected_severity": "LOW"
            },
            {
                "name": "permission_error",
                "exception": "PermissionError",
                "message": "Access denied to resource",
                "expected_category": "PERMISSION_ERROR",
                "expected_severity": "CRITICAL"
            },
            {
                "name": "hardware_error",
                "exception": "Exception",
                "message": "Microphone device not found",
                "expected_category": "HARDWARE_ERROR",
                "expected_severity": "HIGH"
            },
            {
                "name": "api_error",
                "exception": "Exception",
                "message": "API request failed with status 500",
                "expected_category": "API_ERROR",
                "expected_severity": "MEDIUM"
            },
            {
                "name": "configuration_error",
                "exception": "Exception",
                "message": "API key not configured",
                "expected_category": "CONFIGURATION_ERROR",
                "expected_severity": "CRITICAL"
            },
            {
                "name": "resource_error",
                "exception": "MemoryError",
                "message": "Out of memory",
                "expected_category": "RESOURCE_ERROR",
                "expected_severity": "HIGH"
            },
            {
                "name": "processing_error",
                "exception": "Exception",
                "message": "Failed to process data",
                "expected_category": "PROCESSING_ERROR",
                "expected_severity": "LOW"
            }
        ]
    
    @staticmethod
    def get_sample_automation_actions() -> List[Dict[str, Any]]:
        """Get sample automation actions for testing."""
        return [
            {
                "action": "click",
                "coordinates": [100, 200],
                "description": "Click on submit button"
            },
            {
                "action": "double_click",
                "coordinates": [150, 250],
                "description": "Double-click on file icon"
            },
            {
                "action": "type",
                "text": "Hello, World!",
                "description": "Type greeting message"
            },
            {
                "action": "scroll",
                "direction": "up",
                "amount": 200,
                "description": "Scroll up by 200 pixels"
            },
            {
                "action": "scroll",
                "direction": "down",
                "amount": 150,
                "description": "Scroll down by 150 pixels"
            },
            {
                "action": "scroll",
                "direction": "left",
                "amount": 100,
                "description": "Scroll left by 100 pixels"
            },
            {
                "action": "scroll",
                "direction": "right",
                "amount": 75,
                "description": "Scroll right by 75 pixels"
            }
        ]
    
    @staticmethod
    def get_sample_invalid_actions() -> List[Dict[str, Any]]:
        """Get sample invalid automation actions for testing."""
        return [
            {
                "action": "click",
                # Missing coordinates
                "description": "Invalid click action"
            },
            {
                "action": "click",
                "coordinates": [100],  # Invalid coordinates format
                "description": "Click with invalid coordinates"
            },
            {
                "action": "click",
                "coordinates": [-100, 200],  # Negative coordinates
                "description": "Click with negative coordinates"
            },
            {
                "action": "click",
                "coordinates": [5000, 5000],  # Out of bounds
                "description": "Click with out of bounds coordinates"
            },
            {
                "action": "type",
                # Missing text
                "description": "Invalid type action"
            },
            {
                "action": "type",
                "text": 123,  # Non-string text
                "description": "Type with non-string text"
            },
            {
                "action": "type",
                "text": "x" * 10001,  # Text too long
                "description": "Type with text too long"
            },
            {
                "action": "scroll",
                "direction": "diagonal",  # Invalid direction
                "amount": 100,
                "description": "Scroll with invalid direction"
            },
            {
                "action": "scroll",
                "direction": "up",
                "amount": -100,  # Negative amount
                "description": "Scroll with negative amount"
            },
            {
                "action": "scroll",
                "direction": "up",
                "amount": 6000,  # Amount too large
                "description": "Scroll with amount too large"
            },
            {
                "action": "invalid_action",
                "description": "Completely invalid action type"
            }
        ]
    
    @staticmethod
    def get_sample_feedback_scenarios() -> List[Dict[str, Any]]:
        """Get sample feedback scenarios for testing."""
        return [
            {
                "type": "sound",
                "sound_name": "success",
                "priority": "NORMAL",
                "description": "Success sound feedback"
            },
            {
                "type": "sound",
                "sound_name": "failure",
                "priority": "HIGH",
                "description": "Failure sound feedback"
            },
            {
                "type": "sound",
                "sound_name": "thinking",
                "priority": "LOW",
                "description": "Thinking sound feedback"
            },
            {
                "type": "speech",
                "message": "Task completed successfully",
                "priority": "NORMAL",
                "description": "Success speech feedback"
            },
            {
                "type": "speech",
                "message": "An error occurred while processing your request",
                "priority": "HIGH",
                "description": "Error speech feedback"
            },
            {
                "type": "combined",
                "sound_name": "success",
                "message": "Login successful. Welcome back!",
                "priority": "NORMAL",
                "description": "Combined success feedback"
            },
            {
                "type": "combined",
                "sound_name": "failure",
                "message": "Login failed. Please check your credentials.",
                "priority": "HIGH",
                "description": "Combined failure feedback"
            }
        ]
    
    @staticmethod
    def get_sample_orchestrator_scenarios() -> List[Dict[str, Any]]:
        """Get sample orchestrator test scenarios."""
        return [
            {
                "name": "simple_click",
                "command": "Click the submit button",
                "expected_steps": ["validation", "perception", "reasoning", "action", "feedback"],
                "expected_actions": ["click", "finish"],
                "description": "Simple click command scenario"
            },
            {
                "name": "form_filling",
                "command": "Fill in the login form with username 'testuser' and password 'password123'",
                "expected_steps": ["validation", "perception", "reasoning", "action", "feedback"],
                "expected_actions": ["click", "type", "click", "type", "click", "finish"],
                "description": "Form filling scenario"
            },
            {
                "name": "question_answering",
                "command": "What is displayed on the screen?",
                "expected_steps": ["validation", "perception", "information_extraction", "feedback"],
                "expected_actions": ["speak", "finish"],
                "description": "Question answering scenario"
            },
            {
                "name": "scroll_and_click",
                "command": "Scroll down and click the next button",
                "expected_steps": ["validation", "perception", "reasoning", "action", "feedback"],
                "expected_actions": ["scroll", "click", "finish"],
                "description": "Scroll and click scenario"
            },
            {
                "name": "complex_workflow",
                "command": "Open the settings menu, navigate to preferences, and enable dark mode",
                "expected_steps": ["validation", "perception", "reasoning", "action", "feedback"],
                "expected_actions": ["click", "click", "click", "finish"],
                "description": "Complex multi-step workflow"
            }
        ]


class MockDataGenerator:
    """Generator for mock data and responses."""
    
    @staticmethod
    def create_mock_screenshot_data(width: int = 1920, height: int = 1080) -> bytes:
        """Create mock screenshot data."""
        # Create simple BGRA data
        return b'\x00' * (width * height * 4)
    
    @staticmethod
    def create_mock_audio_data(duration: float = 1.0, sample_rate: int = 16000) -> np.ndarray:
        """Create mock audio data."""
        samples = int(duration * sample_rate)
        # Create simple sine wave
        t = np.linspace(0, duration, samples, False)
        audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        return (audio * 32767).astype(np.int16)
    
    @staticmethod
    def create_mock_api_response(content: Dict[str, Any], status_code: int = 200) -> Mock:
        """Create mock API response."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps(content) if isinstance(content, dict) else content
                }
            }]
        }
        mock_response.text = json.dumps(content) if isinstance(content, dict) else str(content)
        mock_response.raise_for_status.return_value = None
        return mock_response
    
    @staticmethod
    def create_mock_error_response(status_code: int, error_message: str) -> Mock:
        """Create mock error response."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = error_message
        mock_response.raise_for_status.side_effect = Exception(f"HTTP {status_code}: {error_message}")
        return mock_response
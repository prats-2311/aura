# tests/test_vision_forms.py
"""
Unit tests for form detection and analysis functionality in VisionModule.

Tests the enhanced vision capabilities for web form identification,
field classification, and validation error detection.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from modules.vision import VisionModule


class TestVisionFormAnalysis:
    """Test form-specific analysis capabilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.vision_module = VisionModule()
    
    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self.vision_module, 'sct'):
            self.vision_module.sct.close()
    
    @patch('modules.vision.requests.post')
    @patch.object(VisionModule, 'capture_screen_as_base64')
    @patch.object(VisionModule, 'get_screen_resolution')
    def test_analyze_forms_success(self, mock_resolution, mock_capture, mock_post):
        """Test successful form analysis."""
        # Mock dependencies
        mock_capture.return_value = "fake_base64_image"
        mock_resolution.return_value = (1920, 1080)
        
        # Mock API response with form data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "forms": [{
                            "form_id": "login_form",
                            "form_title": "Login Form",
                            "coordinates": [100, 100, 400, 300],
                            "fields": [
                                {
                                    "type": "email",
                                    "label": "Email Address",
                                    "placeholder": "Enter your email",
                                    "current_value": "",
                                    "coordinates": [120, 150, 380, 180],
                                    "required": True,
                                    "validation_state": "neutral"
                                },
                                {
                                    "type": "password",
                                    "label": "Password",
                                    "placeholder": "Enter your password",
                                    "current_value": "",
                                    "coordinates": [120, 200, 380, 230],
                                    "required": True,
                                    "validation_state": "neutral"
                                }
                            ]
                        }],
                        "form_errors": [],
                        "submit_buttons": [{
                            "text": "Login",
                            "coordinates": [200, 250, 300, 280],
                            "type": "submit"
                        }]
                    })
                }
            }]
        }
        mock_post.return_value = mock_response
        
        # Test form analysis
        result = self.vision_module.analyze_forms()
        
        # Verify results
        assert "forms" in result
        assert len(result["forms"]) == 1
        assert result["forms"][0]["form_id"] == "login_form"
        assert len(result["forms"][0]["fields"]) == 2
        assert result["metadata"]["analysis_type"] == "form"
        assert result["metadata"]["has_forms"] is True
        assert result["metadata"]["form_count"] == 1
        assert result["metadata"]["total_fields"] == 2
    
    def test_classify_form_field_valid(self):
        """Test form field classification with valid data."""
        field_data = {
            "type": "email",
            "label": "Email Address",
            "placeholder": "Enter your email",
            "current_value": "user@example.com",
            "coordinates": [100, 100, 300, 130],
            "required": True,
            "validation_state": "success",
            "error_message": "",
            "options": []
        }
        
        result = self.vision_module.classify_form_field(field_data)
        
        assert result["type"] == "email"
        assert result["label"] == "Email Address"
        assert result["required"] is True
        assert result["validation_state"] == "success"
        assert result["coordinates"] == [100, 100, 300, 130]
    
    def test_classify_form_field_invalid_type(self):
        """Test form field classification with invalid type."""
        field_data = {
            "type": "invalid_type",
            "label": "Test Field",
            "coordinates": [0, 0, 100, 30]
        }
        
        result = self.vision_module.classify_form_field(field_data)
        
        # Should default to text_input for invalid types
        assert result["type"] == "text_input"
        assert result["label"] == "Test Field"
        assert result["validation_state"] == "neutral"
    
    def test_classify_form_field_missing_data(self):
        """Test form field classification with missing data."""
        field_data = {
            "label": "Incomplete Field"
        }
        
        result = self.vision_module.classify_form_field(field_data)
        
        # Should provide safe defaults
        assert result["type"] == "text_input"
        assert result["label"] == "Incomplete Field"
        assert result["coordinates"] == [0, 0, 0, 0]
        assert result["required"] is False
        assert result["validation_state"] == "neutral"
    
    def test_classify_form_field_invalid_coordinates(self):
        """Test form field classification with invalid coordinates."""
        field_data = {
            "type": "text_input",
            "label": "Test Field",
            "coordinates": [100, 100]  # Invalid - should have 4 values
        }
        
        result = self.vision_module.classify_form_field(field_data)
        
        # Should default to safe coordinates
        assert result["coordinates"] == [0, 0, 0, 0]
    
    def test_detect_form_errors_with_errors(self):
        """Test form error detection with validation errors."""
        form_analysis = {
            "form_errors": [
                {
                    "message": "Email is required",
                    "coordinates": [100, 100, 300, 130],
                    "associated_field": "Email Address"
                }
            ],
            "forms": [{
                "fields": [
                    {
                        "label": "Password",
                        "validation_state": "error",
                        "error_message": "Password too short",
                        "coordinates": [100, 150, 300, 180]
                    }
                ]
            }]
        }
        
        errors = self.vision_module.detect_form_errors(form_analysis)
        
        assert len(errors) == 2
        
        # Check validation error
        validation_error = next(e for e in errors if e["type"] == "validation_error")
        assert validation_error["message"] == "Email is required"
        assert validation_error["associated_field"] == "Email Address"
        
        # Check field error
        field_error = next(e for e in errors if e["type"] == "field_error")
        assert field_error["message"] == "Password too short"
        assert field_error["associated_field"] == "Password"
    
    def test_detect_form_errors_no_errors(self):
        """Test form error detection with no errors."""
        form_analysis = {
            "form_errors": [],
            "forms": [{
                "fields": [
                    {
                        "label": "Email",
                        "validation_state": "success"
                    }
                ]
            }]
        }
        
        errors = self.vision_module.detect_form_errors(form_analysis)
        
        assert len(errors) == 0
    
    def test_validate_form_structure_complete(self):
        """Test form structure validation with complete data."""
        form_analysis = {
            "forms": [{
                "form_id": "test_form",
                "form_title": "Test Form",
                "coordinates": [0, 0, 400, 300],
                "fields": [
                    {
                        "type": "text_input",
                        "label": "Name",
                        "coordinates": [10, 10, 200, 40],
                        "required": True
                    }
                ]
            }],
            "form_errors": [{
                "message": "Test error",
                "coordinates": [10, 50, 200, 70],
                "associated_field": "Name"
            }],
            "submit_buttons": [{
                "text": "Submit",
                "coordinates": [150, 250, 250, 280],
                "type": "submit"
            }],
            "metadata": {
                "timestamp": time.time()
            }
        }
        
        result = self.vision_module.validate_form_structure(form_analysis)
        
        # Verify structure
        assert len(result["forms"]) == 1
        assert result["forms"][0]["form_id"] == "test_form"
        assert len(result["forms"][0]["fields"]) == 1
        assert len(result["form_errors"]) == 1
        assert len(result["submit_buttons"]) == 1
        
        # Verify metadata
        assert result["metadata"]["has_forms"] is True
        assert result["metadata"]["form_count"] == 1
        assert result["metadata"]["total_fields"] == 1
        assert "validation_timestamp" in result["metadata"]
    
    def test_validate_form_structure_empty(self):
        """Test form structure validation with empty data."""
        form_analysis = {}
        
        result = self.vision_module.validate_form_structure(form_analysis)
        
        # Should return safe defaults
        assert result["forms"] == []
        assert result["form_errors"] == []
        assert result["submit_buttons"] == []
        assert result["metadata"]["has_forms"] is False
        assert result["metadata"]["form_count"] == 0
        assert result["metadata"]["total_fields"] == 0
    
    def test_validate_form_structure_missing_ids(self):
        """Test form structure validation with missing form IDs."""
        form_analysis = {
            "forms": [
                {"fields": []},  # Missing form_id
                {"fields": []}   # Missing form_id
            ]
        }
        
        result = self.vision_module.validate_form_structure(form_analysis)
        
        # Should generate default IDs
        assert result["forms"][0]["form_id"] == "form_0"
        assert result["forms"][1]["form_id"] == "form_1"
        assert result["forms"][0]["form_title"] == "Form 1"
        assert result["forms"][1]["form_title"] == "Form 2"
    
    @patch('modules.vision.requests.post')
    @patch.object(VisionModule, 'capture_screen_as_base64')
    @patch.object(VisionModule, 'get_screen_resolution')
    def test_analyze_forms_api_failure(self, mock_resolution, mock_capture, mock_post):
        """Test form analysis with API failure."""
        # Mock dependencies
        mock_capture.return_value = "fake_base64_image"
        mock_resolution.return_value = (1920, 1080)
        
        # Mock API failure
        mock_post.side_effect = Exception("API connection failed")
        
        # Test should raise exception
        with pytest.raises(Exception, match="Screen analysis failed"):
            self.vision_module.analyze_forms()
    
    @patch('modules.vision.requests.post')
    @patch.object(VisionModule, 'capture_screen_as_base64')
    @patch.object(VisionModule, 'get_screen_resolution')
    def test_analyze_forms_invalid_json(self, mock_resolution, mock_capture, mock_post):
        """Test form analysis with invalid JSON response."""
        # Mock dependencies
        mock_capture.return_value = "fake_base64_image"
        mock_resolution.return_value = (1920, 1080)
        
        # Mock API response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Invalid JSON response"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        # Test should raise exception
        with pytest.raises(Exception, match="Screen analysis failed"):
            self.vision_module.analyze_forms()


class TestFormFieldTypes:
    """Test form field type classification and validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.vision_module = VisionModule()
    
    def test_all_valid_field_types(self):
        """Test classification of all valid field types."""
        valid_types = [
            'text_input', 'password', 'email', 'number', 'textarea',
            'select', 'checkbox', 'radio', 'button', 'submit'
        ]
        
        for field_type in valid_types:
            field_data = {
                "type": field_type,
                "label": f"Test {field_type}",
                "coordinates": [0, 0, 100, 30]
            }
            
            result = self.vision_module.classify_form_field(field_data)
            assert result["type"] == field_type
    
    def test_validation_states(self):
        """Test all validation states."""
        valid_states = ['error', 'success', 'neutral']
        
        for state in valid_states:
            field_data = {
                "type": "text_input",
                "label": "Test Field",
                "validation_state": state,
                "coordinates": [0, 0, 100, 30]
            }
            
            result = self.vision_module.classify_form_field(field_data)
            assert result["validation_state"] == state
    
    def test_invalid_validation_state(self):
        """Test invalid validation state defaults to neutral."""
        field_data = {
            "type": "text_input",
            "label": "Test Field",
            "validation_state": "invalid_state",
            "coordinates": [0, 0, 100, 30]
        }
        
        result = self.vision_module.classify_form_field(field_data)
        assert result["validation_state"] == "neutral"


if __name__ == "__main__":
    pytest.main([__file__])
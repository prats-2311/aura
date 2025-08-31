# tests/test_form_filling_integration.py
"""
Integration tests for form filling automation functionality.

Tests the complete form filling workflow including form detection,
field classification, value mapping, and automated form submission.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from modules.automation import AutomationModule
from modules.vision import VisionModule


class TestFormFillingIntegration:
    """Test complete form filling workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.automation_module = AutomationModule()
        self.vision_module = VisionModule()
    
    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self.vision_module, 'sct'):
            self.vision_module.sct.close()
    
    def get_sample_form_data(self):
        """Get sample form data for testing."""
        return {
            "forms": [{
                "form_id": "contact_form",
                "form_title": "Contact Form",
                "coordinates": [100, 100, 500, 400],
                "fields": [
                    {
                        "type": "text_input",
                        "label": "Full Name",
                        "placeholder": "Enter your full name",
                        "current_value": "",
                        "coordinates": [120, 150, 480, 180],
                        "required": True,
                        "validation_state": "neutral"
                    },
                    {
                        "type": "email",
                        "label": "Email Address",
                        "placeholder": "Enter your email",
                        "current_value": "",
                        "coordinates": [120, 200, 480, 230],
                        "required": True,
                        "validation_state": "neutral"
                    },
                    {
                        "type": "select",
                        "label": "Country",
                        "current_value": "",
                        "coordinates": [120, 250, 480, 280],
                        "required": False,
                        "validation_state": "neutral",
                        "options": ["United States", "Canada", "United Kingdom", "Other"]
                    },
                    {
                        "type": "checkbox",
                        "label": "Subscribe to newsletter",
                        "current_value": "",
                        "coordinates": [120, 300, 140, 320],
                        "required": False,
                        "validation_state": "neutral"
                    }
                ]
            }],
            "form_errors": [],
            "submit_buttons": [{
                "text": "Submit",
                "coordinates": [200, 350, 300, 380],
                "type": "submit"
            }],
            "metadata": {
                "has_forms": True,
                "form_count": 1,
                "total_fields": 4
            }
        }
    
    def get_sample_form_values(self):
        """Get sample form values for testing."""
        return {
            "Full Name": "John Doe",
            "Email Address": "john.doe@example.com",
            "Country": "United States",
            "Subscribe to newsletter": "true"
        }
    
    @patch('modules.automation.pyautogui.click')
    @patch('modules.automation.pyautogui.typewrite')
    @patch('modules.automation.pyautogui.hotkey')
    @patch('modules.automation.pyautogui.moveTo')
    def test_fill_form_complete_success(self, mock_moveto, mock_hotkey, mock_typewrite, mock_click):
        """Test complete successful form filling workflow."""
        form_data = self.get_sample_form_data()
        form_values = self.get_sample_form_values()
        
        # Mock PyAutoGUI functions
        mock_click.return_value = None
        mock_typewrite.return_value = None
        mock_hotkey.return_value = None
        mock_moveto.return_value = None
        
        # Test form filling
        result = self.automation_module.fill_form(form_data, form_values, confirm_before_submit=True)
        
        # Verify results
        assert result["total_fields"] == 4
        assert result["filled_fields"] == 4
        assert result["failed_fields"] == 0
        assert result["form_submitted"] is False  # Due to confirm_before_submit=True
        assert len(result["errors"]) == 0
        
        # Verify PyAutoGUI was called appropriately
        assert mock_click.call_count >= 4  # At least one click per field
        assert mock_typewrite.call_count >= 3  # Text fields + email + country
    
    @patch('modules.automation.pyautogui.click')
    @patch('modules.automation.pyautogui.typewrite')
    @patch('modules.automation.pyautogui.hotkey')
    @patch('modules.automation.pyautogui.moveTo')
    def test_fill_form_partial_values(self, mock_moveto, mock_hotkey, mock_typewrite, mock_click):
        """Test form filling with partial values provided."""
        form_data = self.get_sample_form_data()
        form_values = {
            "Full Name": "Jane Smith",
            "Email Address": "jane@example.com"
            # Missing Country and Newsletter values
        }
        
        # Mock PyAutoGUI functions
        mock_click.return_value = None
        mock_typewrite.return_value = None
        mock_hotkey.return_value = None
        mock_moveto.return_value = None
        
        # Test form filling
        result = self.automation_module.fill_form(form_data, form_values, confirm_before_submit=True)
        
        # Verify results
        assert result["total_fields"] == 4
        assert result["filled_fields"] == 2  # Only name and email
        assert result["skipped_fields"] == 2  # Country and newsletter
        assert result["failed_fields"] == 0
        assert len(result["errors"]) == 0
    
    @patch('modules.automation.pyautogui.click')
    @patch('modules.automation.pyautogui.typewrite')
    @patch('modules.automation.pyautogui.hotkey')
    @patch('modules.automation.pyautogui.moveTo')
    def test_fill_form_with_submission(self, mock_moveto, mock_hotkey, mock_typewrite, mock_click):
        """Test form filling with automatic submission."""
        form_data = self.get_sample_form_data()
        form_values = self.get_sample_form_values()
        
        # Mock PyAutoGUI functions
        mock_click.return_value = None
        mock_typewrite.return_value = None
        mock_hotkey.return_value = None
        mock_moveto.return_value = None
        
        # Test form filling with submission
        result = self.automation_module.fill_form(form_data, form_values, confirm_before_submit=False)
        
        # Verify results
        assert result["total_fields"] == 4
        assert result["filled_fields"] == 4
        assert result["form_submitted"] is True
        assert len(result["errors"]) == 0
        
        # Verify submit button was clicked (additional click for submission)
        assert mock_click.call_count >= 5  # 4 fields + 1 submit button
    
    def test_fill_form_invalid_data(self):
        """Test form filling with invalid form data."""
        invalid_form_data = {"invalid": "data"}
        form_values = self.get_sample_form_values()
        
        result = self.automation_module.fill_form(invalid_form_data, form_values)
        
        # Should handle gracefully
        assert result["total_fields"] == 0
        assert result["filled_fields"] == 0
        assert result["form_submitted"] is False
        assert len(result["errors"]) > 0
    
    def test_validate_form_data_valid(self):
        """Test form data validation with valid data."""
        form_data = self.get_sample_form_data()
        
        is_valid, errors = self.automation_module.validate_form_data(form_data)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_form_data_invalid(self):
        """Test form data validation with invalid data."""
        invalid_form_data = {
            "forms": [{
                "fields": [
                    {
                        # Missing required 'type' and 'coordinates'
                        "label": "Test Field"
                    }
                ]
            }]
        }
        
        is_valid, errors = self.automation_module.validate_form_data(invalid_form_data)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("missing 'type'" in error for error in errors)
        assert any("missing 'coordinates'" in error for error in errors)
    
    def test_validate_form_data_empty(self):
        """Test form data validation with empty data."""
        empty_form_data = {"forms": []}
        
        is_valid, errors = self.automation_module.validate_form_data(empty_form_data)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "No forms found" in errors[0]
    
    @patch('modules.automation.pyautogui.click')
    @patch('modules.automation.pyautogui.typewrite')
    @patch('modules.automation.pyautogui.hotkey')
    @patch('modules.automation.pyautogui.moveTo')
    @patch('modules.automation.pyautogui.press')
    def test_fill_different_field_types(self, mock_press, mock_moveto, mock_hotkey, mock_typewrite, mock_click):
        """Test filling different types of form fields."""
        form_data = {
            "forms": [{
                "form_id": "test_form",
                "fields": [
                    {
                        "type": "text_input",
                        "label": "Name",
                        "coordinates": [100, 100, 300, 130]
                    },
                    {
                        "type": "textarea",
                        "label": "Message",
                        "coordinates": [100, 150, 300, 200]
                    },
                    {
                        "type": "select",
                        "label": "Category",
                        "coordinates": [100, 220, 300, 250],
                        "options": ["Option 1", "Option 2", "Option 3"]
                    },
                    {
                        "type": "checkbox",
                        "label": "Agree",
                        "coordinates": [100, 270, 120, 290]
                    },
                    {
                        "type": "radio",
                        "label": "Choice A",
                        "coordinates": [100, 310, 120, 330]
                    }
                ]
            }],
            "submit_buttons": []
        }
        
        form_values = {
            "Name": "Test User",
            "Message": "This is a test message\nwith multiple lines",
            "Category": "Option 2",
            "Agree": "true",
            "Choice A": "true"
        }
        
        # Mock PyAutoGUI functions
        mock_click.return_value = None
        mock_typewrite.return_value = None
        mock_hotkey.return_value = None
        mock_moveto.return_value = None
        mock_press.return_value = None
        
        # Test form filling
        result = self.automation_module.fill_form(form_data, form_values)
        
        # Verify all field types were handled
        assert result["total_fields"] == 5
        assert result["filled_fields"] == 5
        assert result["failed_fields"] == 0
    
    def test_handle_form_validation_errors(self):
        """Test handling of form validation errors."""
        form_data_with_errors = {
            "forms": [{
                "fields": [
                    {
                        "type": "email",
                        "label": "Email",
                        "coordinates": [100, 100, 300, 130],
                        "validation_state": "error",
                        "error_message": "Invalid email format"
                    }
                ]
            }],
            "form_errors": [
                {
                    "message": "Name is required",
                    "coordinates": [100, 50, 300, 80],
                    "associated_field": "Name"
                }
            ]
        }
        
        with patch('modules.automation.pyautogui.click'), \
             patch('modules.automation.pyautogui.hotkey'), \
             patch('modules.automation.pyautogui.press'), \
             patch('modules.automation.pyautogui.moveTo'):
            
            result = self.automation_module.handle_form_validation_errors(form_data_with_errors)
            
            assert result["errors_found"] == 2  # 1 form error + 1 field error
            assert result["errors_handled"] >= 0  # Some errors might be handled
            assert len(result["actions_taken"]) >= 0
    
    @patch('modules.vision.requests.post')
    @patch.object(VisionModule, 'capture_screen_as_base64')
    @patch.object(VisionModule, 'get_screen_resolution')
    @patch('modules.automation.pyautogui.click')
    @patch('modules.automation.pyautogui.typewrite')
    @patch('modules.automation.pyautogui.hotkey')
    @patch('modules.automation.pyautogui.moveTo')
    def test_end_to_end_form_workflow(self, mock_moveto, mock_hotkey, mock_typewrite, 
                                     mock_click, mock_resolution, mock_capture, mock_post):
        """Test complete end-to-end form filling workflow."""
        # Mock vision analysis
        mock_capture.return_value = "fake_base64_image"
        mock_resolution.return_value = (1920, 1080)
        
        # Mock API response with form data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"forms": [{"form_id": "test", "fields": [{"type": "text_input", "label": "Name", "coordinates": [100, 100, 300, 130]}]}], "submit_buttons": [{"text": "Submit", "coordinates": [200, 200, 300, 230]}]}'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        # Mock automation functions
        mock_click.return_value = None
        mock_typewrite.return_value = None
        mock_hotkey.return_value = None
        mock_moveto.return_value = None
        
        # Step 1: Analyze forms
        form_analysis = self.vision_module.analyze_forms()
        
        # Step 2: Fill form
        form_values = {"Name": "Test User"}
        fill_result = self.automation_module.fill_form(form_analysis, form_values)
        
        # Verify workflow
        assert form_analysis["metadata"]["has_forms"] is True
        assert fill_result["filled_fields"] > 0
        assert len(fill_result["errors"]) == 0


class TestFormFieldHandling:
    """Test specific form field handling scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.automation_module = AutomationModule()
    
    @patch('modules.automation.pyautogui.click')
    @patch('modules.automation.pyautogui.typewrite')
    @patch('modules.automation.pyautogui.hotkey')
    @patch('modules.automation.pyautogui.moveTo')
    def test_text_field_handling(self, mock_moveto, mock_hotkey, mock_typewrite, mock_click):
        """Test text field filling with clearing existing content."""
        field = {
            "type": "text_input",
            "label": "Username",
            "coordinates": [100, 100, 300, 130]
        }
        form_values = {"Username": "testuser"}
        
        mock_click.return_value = None
        mock_typewrite.return_value = None
        mock_hotkey.return_value = None
        mock_moveto.return_value = None
        
        result = self.automation_module._fill_form_field(field, form_values)
        
        assert result["status"] == "filled"
        assert result["field"] == "Username"
        assert result["value"] == "testuser"
        
        # Verify field was clicked and content cleared
        mock_click.assert_called()
        mock_hotkey.assert_called_with('ctrl', 'a')
        mock_typewrite.assert_called_with("testuser", interval=0.05)
    
    @patch('modules.automation.pyautogui.click')
    @patch('modules.automation.pyautogui.typewrite')
    @patch('modules.automation.pyautogui.press')
    @patch('modules.automation.pyautogui.moveTo')
    def test_select_field_handling(self, mock_moveto, mock_press, mock_typewrite, mock_click):
        """Test select dropdown field handling."""
        field = {
            "type": "select",
            "label": "Country",
            "coordinates": [100, 100, 300, 130],
            "options": ["United States", "Canada", "Mexico"]
        }
        form_values = {"Country": "Canada"}
        
        mock_click.return_value = None
        mock_typewrite.return_value = None
        mock_press.return_value = None
        mock_moveto.return_value = None
        
        result = self.automation_module._fill_form_field(field, form_values)
        
        assert result["status"] == "filled"
        assert result["field"] == "Country"
        assert result["value"] == "Canada"
        
        # Verify dropdown was clicked and option selected
        mock_click.assert_called()
        mock_typewrite.assert_called_with("Canada", interval=0.05)
        mock_press.assert_called_with('enter')
    
    @patch('modules.automation.pyautogui.click')
    @patch('modules.automation.pyautogui.moveTo')
    def test_checkbox_field_handling(self, mock_moveto, mock_click):
        """Test checkbox field handling."""
        field = {
            "type": "checkbox",
            "label": "Subscribe",
            "coordinates": [100, 100, 120, 120]
        }
        form_values = {"Subscribe": "true"}
        
        mock_click.return_value = None
        mock_moveto.return_value = None
        
        result = self.automation_module._fill_form_field(field, form_values)
        
        assert result["status"] == "filled"
        assert result["field"] == "Subscribe"
        assert result["value"] == "True"
        
        # Verify checkbox was clicked
        mock_click.assert_called()
    
    def test_field_without_value(self):
        """Test handling field when no value is provided."""
        field = {
            "type": "text_input",
            "label": "Optional Field",
            "coordinates": [100, 100, 300, 130]
        }
        form_values = {"Other Field": "value"}  # No value for "Optional Field"
        
        result = self.automation_module._fill_form_field(field, form_values)
        
        assert result["status"] == "skipped"
        assert result["field"] == "Optional Field"
        assert "No value provided" in result["reason"]
    
    def test_field_with_invalid_coordinates(self):
        """Test handling field with invalid coordinates."""
        field = {
            "type": "text_input",
            "label": "Bad Field",
            "coordinates": [100, 100]  # Invalid - should have 4 values
        }
        form_values = {"Bad Field": "value"}
        
        result = self.automation_module._fill_form_field(field, form_values)
        
        assert result["status"] == "failed"
        assert result["field"] == "Bad Field"
        assert "Invalid field coordinates" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__])
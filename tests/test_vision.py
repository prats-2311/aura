"""
Unit tests for the Vision Module

Tests screen capture functionality and API communication.
"""

import base64
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

from modules.vision import VisionModule


class TestVisionModule:
    """Test cases for VisionModule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.vision_module = VisionModule()
    
    @patch('modules.vision.mss.mss')
    def test_capture_screen_as_base64_success(self, mock_mss):
        """Test successful screen capture and base64 encoding."""
        # Mock MSS screenshot
        mock_screenshot = Mock()
        mock_screenshot.size = (1920, 1080)
        mock_screenshot.bgra = b'\x00' * (1920 * 1080 * 4)  # Mock BGRA data
        
        mock_sct_instance = Mock()
        mock_sct_instance.monitors = [
            {},  # Index 0 is all monitors
            {"width": 1920, "height": 1080, "left": 0, "top": 0}  # Primary monitor
        ]
        mock_sct_instance.grab.return_value = mock_screenshot
        mock_mss.return_value = mock_sct_instance
        
        # Create new instance to use mocked MSS
        vision_module = VisionModule()
        
        # Test screen capture
        result = vision_module.capture_screen_as_base64()
        
        # Verify result
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify it's valid base64
        try:
            decoded = base64.b64decode(result)
            assert len(decoded) > 0
        except Exception:
            pytest.fail("Result is not valid base64")
        
        # Verify MSS was called correctly
        mock_sct_instance.grab.assert_called_once()
    
    @patch('modules.vision.mss.mss')
    def test_capture_screen_resize_large_image(self, mock_mss):
        """Test that large screenshots are resized appropriately."""
        # Mock large screenshot
        mock_screenshot = Mock()
        mock_screenshot.size = (3840, 2160)  # 4K resolution
        mock_screenshot.bgra = b'\x00' * (3840 * 2160 * 4)
        
        mock_sct_instance = Mock()
        mock_sct_instance.monitors = [
            {},
            {"width": 3840, "height": 2160, "left": 0, "top": 0}
        ]
        mock_sct_instance.grab.return_value = mock_screenshot
        mock_mss.return_value = mock_sct_instance
        
        vision_module = VisionModule()
        
        with patch('modules.vision.MAX_SCREENSHOT_SIZE', 1920):
            result = vision_module.capture_screen_as_base64()
            
        # Should still return valid base64
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('modules.vision.mss.mss')
    def test_capture_screen_failure(self, mock_mss):
        """Test handling of screen capture failures."""
        mock_sct_instance = Mock()
        mock_sct_instance.grab.side_effect = Exception("Screen capture failed")
        mock_mss.return_value = mock_sct_instance
        
        vision_module = VisionModule()
        
        with pytest.raises(Exception, match="Screen capture failed"):
            vision_module.capture_screen_as_base64()
    
    @patch('modules.vision.mss.mss')
    def test_get_screen_resolution(self, mock_mss):
        """Test getting screen resolution."""
        mock_sct_instance = Mock()
        mock_sct_instance.monitors = [
            {},
            {"width": 1920, "height": 1080, "left": 0, "top": 0}
        ]
        mock_mss.return_value = mock_sct_instance
        
        vision_module = VisionModule()
        width, height = vision_module.get_screen_resolution()
        
        assert width == 1920
        assert height == 1080
    
    @patch('modules.vision.mss.mss')
    def test_get_screen_resolution_failure(self, mock_mss):
        """Test fallback when getting screen resolution fails."""
        mock_sct_instance = Mock()
        mock_sct_instance.monitors = []  # Empty monitors list
        mock_mss.return_value = mock_sct_instance
        
        vision_module = VisionModule()
        width, height = vision_module.get_screen_resolution()
        
        # Should return default fallback
        assert width == 1920
        assert height == 1080
    
    @patch('modules.vision.requests.post')
    @patch.object(VisionModule, 'capture_screen_as_base64')
    @patch.object(VisionModule, 'get_screen_resolution')
    def test_describe_screen_success(self, mock_resolution, mock_capture, mock_post):
        """Test successful screen description via API."""
        # Mock dependencies
        mock_capture.return_value = "fake_base64_data"
        mock_resolution.return_value = (1920, 1080)
        
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "elements": [
                            {
                                "type": "button",
                                "text": "Click me",
                                "coordinates": [100, 200, 150, 230],
                                "description": "A clickable button"
                            }
                        ],
                        "text_blocks": [],
                        "metadata": {}
                    })
                }
            }]
        }
        mock_post.return_value = mock_response
        
        # Test describe_screen
        result = self.vision_module.describe_screen()
        
        # Verify result structure
        assert "elements" in result
        assert "text_blocks" in result
        assert "metadata" in result
        assert len(result["elements"]) == 1
        assert result["elements"][0]["type"] == "button"
        assert result["metadata"]["screen_resolution"] == [1920, 1080]
        
        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "chat/completions" in call_args[0][0]
        assert "model" in call_args[1]["json"]
    
    @patch('modules.vision.requests.post')
    @patch.object(VisionModule, 'capture_screen_as_base64')
    def test_describe_screen_api_failure(self, mock_capture, mock_post):
        """Test handling of API failures with retry logic."""
        mock_capture.return_value = "fake_base64_data"
        
        # Mock API failure
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="API request failed"):
            self.vision_module.describe_screen()
        
        # Should retry 3 times total (initial + 2 retries)
        assert mock_post.call_count == 3
    
    @patch('modules.vision.requests.post')
    @patch.object(VisionModule, 'capture_screen_as_base64')
    def test_describe_screen_timeout_retry(self, mock_capture, mock_post):
        """Test retry logic for API timeouts."""
        mock_capture.return_value = "fake_base64_data"
        
        # Mock timeout exception
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(Exception, match="Vision API timeout after retries"):
            self.vision_module.describe_screen()
        
        # Should retry 3 times total
        assert mock_post.call_count == 3
    
    @patch('modules.vision.requests.post')
    @patch.object(VisionModule, 'capture_screen_as_base64')
    @patch.object(VisionModule, 'get_screen_resolution')
    def test_describe_screen_json_parsing(self, mock_resolution, mock_capture, mock_post):
        """Test JSON parsing from model response."""
        mock_capture.return_value = "fake_base64_data"
        mock_resolution.return_value = (1920, 1080)
        
        # Mock response with JSON wrapped in text
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": 'Here is the analysis: {"elements": [], "text_blocks": []}'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = self.vision_module.describe_screen()
        
        # Should successfully parse JSON
        assert "elements" in result
        assert "text_blocks" in result
        assert isinstance(result["elements"], list)
    
    @patch('modules.vision.requests.post')
    @patch.object(VisionModule, 'capture_screen_as_base64')
    def test_describe_screen_invalid_json(self, mock_capture, mock_post):
        """Test handling of invalid JSON responses."""
        mock_capture.return_value = "fake_base64_data"
        
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "This is not valid JSON content"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="Could not parse JSON"):
            self.vision_module.describe_screen()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
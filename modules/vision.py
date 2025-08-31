# modules/vision.py
"""
Vision Module for AURA

Handles screen capture and communication with local vision models.
Provides structured analysis of desktop content for action planning.
"""

import base64
import io
import json
import logging
import time
from typing import Dict, Optional, Tuple
import requests
from PIL import Image
import mss

from config import (
    VISION_API_BASE,
    VISION_MODEL,
    VISION_PROMPT,
    VISION_API_TIMEOUT,
    SCREENSHOT_QUALITY,
    MAX_SCREENSHOT_SIZE
)

logger = logging.getLogger(__name__)


class VisionModule:
    """
    Vision module for screen capture and analysis.
    
    Handles screenshot capture using MSS library and communicates with
    local vision models for structured screen content analysis.
    """
    
    def __init__(self):
        """Initialize the VisionModule."""
        self.sct = mss.mss()
        logger.info("VisionModule initialized")
    
    def capture_screen_as_base64(self, monitor_number: int = 1) -> str:
        """
        Capture a screenshot and encode it as base64 for API transmission.
        
        Args:
            monitor_number: Monitor to capture (1 for primary monitor)
            
        Returns:
            Base64 encoded screenshot string
            
        Raises:
            Exception: If screen capture fails
        """
        try:
            # Get monitor information
            monitor = self.sct.monitors[monitor_number]
            logger.debug(f"Capturing screen from monitor {monitor_number}: {monitor}")
            
            # Capture screenshot
            screenshot = self.sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Resize if too large
            if img.width > MAX_SCREENSHOT_SIZE or img.height > MAX_SCREENSHOT_SIZE:
                # Calculate new size maintaining aspect ratio
                ratio = min(MAX_SCREENSHOT_SIZE / img.width, MAX_SCREENSHOT_SIZE / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.debug(f"Resized screenshot from {screenshot.size} to {new_size}")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=SCREENSHOT_QUALITY)
            img_bytes = buffer.getvalue()
            base64_string = base64.b64encode(img_bytes).decode('utf-8')
            
            logger.info(f"Screenshot captured and encoded: {len(base64_string)} characters")
            return base64_string
            
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            raise Exception(f"Screen capture failed: {e}")
    
    def get_screen_resolution(self, monitor_number: int = 1) -> Tuple[int, int]:
        """
        Get the resolution of the specified monitor.
        
        Args:
            monitor_number: Monitor to get resolution for (1 for primary)
            
        Returns:
            Tuple of (width, height)
        """
        try:
            monitor = self.sct.monitors[monitor_number]
            width = monitor["width"]
            height = monitor["height"]
            logger.debug(f"Monitor {monitor_number} resolution: {width}x{height}")
            return width, height
        except Exception as e:
            logger.error(f"Failed to get screen resolution: {e}")
            return 1920, 1080  # Default fallback
    
    def describe_screen(self) -> Dict:
        """
        Capture screen and get structured description from vision model.
        
        Returns:
            Dictionary containing structured screen analysis
            
        Raises:
            Exception: If screen analysis fails
        """
        try:
            logger.info("Starting screen analysis")
            
            # Capture screenshot
            screenshot_b64 = self.capture_screen_as_base64()
            
            # Get screen resolution for metadata
            width, height = self.get_screen_resolution()
            
            # Prepare API request
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": VISION_PROMPT
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{screenshot_b64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            # Make API request with retry logic
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    logger.debug(f"Sending request to vision API (attempt {attempt + 1})")
                    response = requests.post(
                        f"{VISION_API_BASE}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=VISION_API_TIMEOUT
                    )
                    
                    if response.status_code == 200:
                        break
                    else:
                        logger.warning(f"API request failed with status {response.status_code}: {response.text}")
                        if attempt == max_retries:
                            raise Exception(f"API request failed: {response.status_code} - {response.text}")
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"API request timed out (attempt {attempt + 1})")
                    if attempt == max_retries:
                        raise Exception("Vision API timeout after retries")
                        
                except requests.exceptions.ConnectionError:
                    logger.warning(f"Connection error to vision API (attempt {attempt + 1})")
                    if attempt == max_retries:
                        raise Exception("Cannot connect to vision API")
                
                # Wait before retry
                if attempt < max_retries:
                    time.sleep(1)
            
            # Parse response
            response_data = response.json()
            
            if "choices" not in response_data or not response_data["choices"]:
                raise Exception("Invalid API response format")
            
            content = response_data["choices"][0]["message"]["content"]
            
            # Parse JSON response from model
            try:
                screen_analysis = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response if it's wrapped in text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    screen_analysis = json.loads(json_match.group())
                else:
                    raise Exception("Could not parse JSON from vision model response")
            
            # Add metadata if not present
            if "metadata" not in screen_analysis:
                screen_analysis["metadata"] = {}
            
            screen_analysis["metadata"].update({
                "timestamp": time.time(),
                "screen_resolution": [width, height]
            })
            
            logger.info(f"Screen analysis completed: {len(screen_analysis.get('elements', []))} elements found")
            return screen_analysis
            
        except Exception as e:
            logger.error(f"Screen analysis failed: {e}")
            raise Exception(f"Screen analysis failed: {e}")
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'sct'):
            self.sct.close()
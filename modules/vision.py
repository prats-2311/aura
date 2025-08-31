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
from typing import Dict, List, Optional, Tuple
import requests
from PIL import Image
import mss

from config import (
    VISION_API_BASE,
    VISION_MODEL,
    VISION_PROMPT,
    FORM_VISION_PROMPT,
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
    
    def describe_screen(self, analysis_type: str = "general") -> Dict:
        """
        Capture screen and get structured description from vision model.
        
        Args:
            analysis_type: Type of analysis to perform ("general" or "form")
        
        Returns:
            Dictionary containing structured screen analysis
            
        Raises:
            Exception: If screen analysis fails
        """
        try:
            logger.info(f"Starting screen analysis (type: {analysis_type})")
            
            # Capture screenshot
            screenshot_b64 = self.capture_screen_as_base64()
            
            # Get screen resolution for metadata
            width, height = self.get_screen_resolution()
            
            # Select appropriate prompt based on analysis type
            prompt = FORM_VISION_PROMPT if analysis_type == "form" else VISION_PROMPT
            
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
                                "text": prompt
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
                "max_tokens": 3000,  # Increased for form analysis
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
                "screen_resolution": [width, height],
                "analysis_type": analysis_type
            })
            
            if analysis_type == "form":
                form_count = len(screen_analysis.get('forms', []))
                total_fields = sum(len(form.get('fields', [])) for form in screen_analysis.get('forms', []))
                logger.info(f"Form analysis completed: {form_count} forms, {total_fields} fields found")
            else:
                element_count = len(screen_analysis.get('elements', []))
                logger.info(f"Screen analysis completed: {element_count} elements found")
            
            return screen_analysis
            
        except Exception as e:
            logger.error(f"Screen analysis failed: {e}")
            raise Exception(f"Screen analysis failed: {e}")
    
    def analyze_forms(self) -> Dict:
        """
        Analyze screen specifically for form elements and structure.
        
        Returns:
            Dictionary containing detailed form analysis
            
        Raises:
            Exception: If form analysis fails
        """
        try:
            logger.info("Starting form-specific analysis")
            raw_analysis = self.describe_screen(analysis_type="form")
            # Validate and normalize the form structure
            validated_analysis = self.validate_form_structure(raw_analysis)
            return validated_analysis
        except Exception as e:
            logger.error(f"Form analysis failed: {e}")
            raise Exception(f"Form analysis failed: {e}")
    
    def classify_form_field(self, field_data: Dict) -> Dict:
        """
        Classify and validate form field data.
        
        Args:
            field_data: Raw field data from vision analysis
            
        Returns:
            Classified and validated field data
        """
        try:
            # Define valid field types
            valid_types = {
                'text_input', 'password', 'email', 'number', 'textarea', 
                'select', 'checkbox', 'radio', 'button', 'submit'
            }
            
            # Ensure field has required properties
            classified_field = {
                'type': field_data.get('type', 'text_input'),
                'label': field_data.get('label', ''),
                'placeholder': field_data.get('placeholder', ''),
                'current_value': field_data.get('current_value', ''),
                'coordinates': field_data.get('coordinates', [0, 0, 0, 0]),
                'required': field_data.get('required', False),
                'validation_state': field_data.get('validation_state', 'neutral'),
                'error_message': field_data.get('error_message', ''),
                'options': field_data.get('options', [])
            }
            
            # Validate field type
            if classified_field['type'] not in valid_types:
                logger.warning(f"Unknown field type: {classified_field['type']}, defaulting to text_input")
                classified_field['type'] = 'text_input'
            
            # Validate coordinates
            coords = classified_field['coordinates']
            if not isinstance(coords, list) or len(coords) != 4:
                logger.warning(f"Invalid coordinates for field {classified_field['label']}")
                classified_field['coordinates'] = [0, 0, 0, 0]
            
            # Validate validation state
            valid_states = {'error', 'success', 'neutral'}
            if classified_field['validation_state'] not in valid_states:
                classified_field['validation_state'] = 'neutral'
            
            return classified_field
            
        except Exception as e:
            logger.error(f"Field classification failed: {e}")
            # Return a safe default field
            return {
                'type': 'text_input',
                'label': field_data.get('label', 'Unknown Field'),
                'placeholder': '',
                'current_value': '',
                'coordinates': [0, 0, 0, 0],
                'required': False,
                'validation_state': 'neutral',
                'error_message': '',
                'options': []
            }
    
    def detect_form_errors(self, form_analysis: Dict) -> List[Dict]:
        """
        Detect and extract form validation errors from analysis.
        
        Args:
            form_analysis: Form analysis data from vision model
            
        Returns:
            List of detected form errors
        """
        try:
            errors = []
            
            # Extract explicit form errors
            form_errors = form_analysis.get('form_errors', [])
            for error in form_errors:
                errors.append({
                    'type': 'validation_error',
                    'message': error.get('message', ''),
                    'coordinates': error.get('coordinates', [0, 0, 0, 0]),
                    'associated_field': error.get('associated_field', '')
                })
            
            # Check for field-level errors
            forms = form_analysis.get('forms', [])
            for form in forms:
                fields = form.get('fields', [])
                for field in fields:
                    if field.get('validation_state') == 'error':
                        errors.append({
                            'type': 'field_error',
                            'message': field.get('error_message', 'Field validation error'),
                            'coordinates': field.get('coordinates', [0, 0, 0, 0]),
                            'associated_field': field.get('label', 'Unknown Field')
                        })
            
            logger.info(f"Detected {len(errors)} form errors")
            return errors
            
        except Exception as e:
            logger.error(f"Error detection failed: {e}")
            return []
    
    def validate_form_structure(self, form_analysis: Dict) -> Dict:
        """
        Validate and normalize form structure data.
        
        Args:
            form_analysis: Raw form analysis from vision model
            
        Returns:
            Validated and normalized form structure
        """
        try:
            validated_analysis = {
                'forms': [],
                'form_errors': [],
                'submit_buttons': [],
                'metadata': form_analysis.get('metadata', {})
            }
            
            # Validate forms
            forms = form_analysis.get('forms', [])
            for i, form in enumerate(forms):
                validated_form = {
                    'form_id': form.get('form_id', f'form_{i}'),
                    'form_title': form.get('form_title', f'Form {i+1}'),
                    'coordinates': form.get('coordinates', [0, 0, 0, 0]),
                    'fields': []
                }
                
                # Validate and classify fields
                fields = form.get('fields', [])
                for field in fields:
                    validated_field = self.classify_form_field(field)
                    validated_form['fields'].append(validated_field)
                
                validated_analysis['forms'].append(validated_form)
            
            # Validate form errors
            form_errors = form_analysis.get('form_errors', [])
            for error in form_errors:
                validated_error = {
                    'message': error.get('message', ''),
                    'coordinates': error.get('coordinates', [0, 0, 0, 0]),
                    'associated_field': error.get('associated_field', '')
                }
                validated_analysis['form_errors'].append(validated_error)
            
            # Validate submit buttons
            submit_buttons = form_analysis.get('submit_buttons', [])
            for button in submit_buttons:
                validated_button = {
                    'text': button.get('text', 'Submit'),
                    'coordinates': button.get('coordinates', [0, 0, 0, 0]),
                    'type': button.get('type', 'submit')
                }
                validated_analysis['submit_buttons'].append(validated_button)
            
            # Update metadata
            validated_analysis['metadata'].update({
                'has_forms': len(validated_analysis['forms']) > 0,
                'form_count': len(validated_analysis['forms']),
                'total_fields': sum(len(form['fields']) for form in validated_analysis['forms']),
                'validation_timestamp': time.time()
            })
            
            logger.info(f"Form structure validated: {validated_analysis['metadata']['form_count']} forms, "
                       f"{validated_analysis['metadata']['total_fields']} fields")
            
            return validated_analysis
            
        except Exception as e:
            logger.error(f"Form structure validation failed: {e}")
            # Return safe default structure
            return {
                'forms': [],
                'form_errors': [],
                'submit_buttons': [],
                'metadata': {
                    'has_forms': False,
                    'form_count': 0,
                    'total_fields': 0,
                    'validation_timestamp': time.time(),
                    'validation_error': str(e)
                }
            }
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'sct'):
            self.sct.close()
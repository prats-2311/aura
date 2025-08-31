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
from .error_handler import (
    global_error_handler,
    with_error_handling,
    ErrorCategory,
    ErrorSeverity
)
from .performance import (
    connection_pool,
    image_cache,
    measure_performance,
    PerformanceMetrics,
    performance_monitor
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
    
    @measure_performance("screen_capture", include_system_metrics=True)
    @with_error_handling(
        category=ErrorCategory.HARDWARE_ERROR,
        severity=ErrorSeverity.HIGH,
        max_retries=2,
        user_message="I'm having trouble capturing your screen. Please check your display settings."
    )
    def capture_screen_as_base64(self, monitor_number: int = 1) -> str:
        """
        Capture a screenshot and encode it as base64 for API transmission.
        
        Args:
            monitor_number: Monitor to capture (1 for primary monitor)
            
        Returns:
            Base64 encoded screenshot string
            
        Raises:
            Exception: If screen capture fails after retries
        """
        try:
            # Validate monitor number
            if monitor_number < 1 or monitor_number >= len(self.sct.monitors):
                raise ValueError(f"Invalid monitor number: {monitor_number}. Available monitors: 1-{len(self.sct.monitors)-1}")
            
            # Get monitor information
            monitor = self.sct.monitors[monitor_number]
            logger.debug(f"Capturing screen from monitor {monitor_number}: {monitor}")
            
            # Validate monitor dimensions
            if monitor['width'] <= 0 or monitor['height'] <= 0:
                raise ValueError(f"Invalid monitor dimensions: {monitor['width']}x{monitor['height']}")
            
            # Capture screenshot with error handling
            try:
                screenshot = self.sct.grab(monitor)
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="vision",
                    function="capture_screen_as_base64",
                    category=ErrorCategory.HARDWARE_ERROR,
                    context={"monitor_number": monitor_number, "monitor": monitor}
                )
                raise Exception(f"Screen capture failed: {error_info.user_message}")
            
            # Validate screenshot
            if not screenshot or screenshot.size[0] <= 0 or screenshot.size[1] <= 0:
                raise ValueError("Invalid screenshot captured")
            
            # Convert to PIL Image with error handling
            try:
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="vision",
                    function="capture_screen_as_base64",
                    category=ErrorCategory.PROCESSING_ERROR,
                    context={"screenshot_size": screenshot.size}
                )
                raise Exception(f"Image conversion failed: {error_info.user_message}")
            
            # Resize if too large
            original_size = (img.width, img.height)
            if img.width > MAX_SCREENSHOT_SIZE or img.height > MAX_SCREENSHOT_SIZE:
                try:
                    # Calculate new size maintaining aspect ratio
                    ratio = min(MAX_SCREENSHOT_SIZE / img.width, MAX_SCREENSHOT_SIZE / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    
                    # Validate new size
                    if new_size[0] <= 0 or new_size[1] <= 0:
                        raise ValueError(f"Invalid resize dimensions: {new_size}")
                    
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    logger.debug(f"Resized screenshot from {original_size} to {new_size}")
                except Exception as e:
                    logger.warning(f"Failed to resize image: {e}. Using original size.")
                    # Continue with original size if resize fails
            
            # Convert to base64 with caching and optimization
            try:
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=SCREENSHOT_QUALITY)
                img_bytes = buffer.getvalue()
                
                # Validate image data
                if len(img_bytes) == 0:
                    raise ValueError("Empty image data generated")
                
                # Use image cache for compression optimization
                base64_string = image_cache.get_compressed_image(img_bytes, SCREENSHOT_QUALITY)
                
                if not base64_string:
                    # Fallback to direct encoding if cache fails
                    base64_string = base64.b64encode(img_bytes).decode('utf-8')
                    logger.warning("Image cache failed, using direct encoding")
                
                # Validate base64 string
                if not base64_string:
                    raise ValueError("Empty base64 string generated")
                
                logger.info(f"Screenshot captured and encoded: {len(base64_string)} characters")
                return base64_string
                
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="vision",
                    function="capture_screen_as_base64",
                    category=ErrorCategory.PROCESSING_ERROR,
                    context={"image_size": (img.width, img.height)}
                )
                raise Exception(f"Base64 encoding failed: {error_info.user_message}")
            
        except Exception as e:
            # Re-raise with additional context if not already handled
            if "Screen capture failed" not in str(e):
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="vision",
                    function="capture_screen_as_base64",
                    category=ErrorCategory.HARDWARE_ERROR,
                    context={"monitor_number": monitor_number}
                )
                raise Exception(f"Screen capture failed: {error_info.user_message}")
            raise
    
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
    
    @measure_performance("vision_analysis", include_system_metrics=True)
    @with_error_handling(
        category=ErrorCategory.API_ERROR,
        severity=ErrorSeverity.MEDIUM,
        max_retries=3,
        retry_delay=2.0,
        user_message="I'm having trouble analyzing your screen. Please try again."
    )
    def describe_screen(self, analysis_type: str = "general") -> Dict:
        """
        Capture screen and get structured description from vision model.
        
        Args:
            analysis_type: Type of analysis to perform ("general" or "form")
        
        Returns:
            Dictionary containing structured screen analysis
            
        Raises:
            Exception: If screen analysis fails after retries
        """
        try:
            # Validate analysis type
            valid_types = ["general", "form"]
            if analysis_type not in valid_types:
                raise ValueError(f"Invalid analysis type: {analysis_type}. Must be one of {valid_types}")
            
            logger.info(f"Starting screen analysis (type: {analysis_type})")
            
            # Capture screenshot with error handling
            try:
                screenshot_b64 = self.capture_screen_as_base64()
            except Exception as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="vision",
                    function="describe_screen",
                    category=ErrorCategory.HARDWARE_ERROR,
                    context={"analysis_type": analysis_type}
                )
                raise Exception(f"Screenshot capture failed: {error_info.user_message}")
            
            # Get screen resolution for metadata
            width, height = self.get_screen_resolution()
            
            # Select appropriate prompt based on analysis type
            prompt = FORM_VISION_PROMPT if analysis_type == "form" else VISION_PROMPT
            
            # Validate configuration
            if not VISION_API_BASE:
                raise ValueError("Vision API base URL not configured")
            if not VISION_MODEL:
                raise ValueError("Vision model not configured")
            if not prompt:
                raise ValueError(f"Prompt not configured for analysis type: {analysis_type}")
            
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
            
            # Make API request with connection pooling and comprehensive error handling
            response = None
            last_error = None
            
            # Use connection pool for better performance
            session = connection_pool.get_session(VISION_API_BASE)
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Sending request to vision API (attempt {attempt + 1})")
                    
                    response = session.post(
                        f"{VISION_API_BASE}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=VISION_API_TIMEOUT
                    )
                    
                    # Check response status
                    if response.status_code == 200:
                        break
                    elif response.status_code == 429:
                        # Rate limited
                        wait_time = min(5 * (attempt + 1), 30)
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    elif response.status_code >= 500:
                        # Server error, retry
                        logger.warning(f"Server error {response.status_code}, retrying...")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        # Client error, don't retry
                        error_info = global_error_handler.handle_error(
                            error=Exception(f"API error: {response.status_code} - {response.text}"),
                            module="vision",
                            function="describe_screen",
                            category=ErrorCategory.API_ERROR,
                            context={"status_code": response.status_code, "response": response.text[:500]}
                        )
                        raise Exception(f"Vision API error: {error_info.user_message}")
                        
                except requests.exceptions.Timeout as e:
                    last_error = e
                    logger.warning(f"API request timed out (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                        
                except requests.exceptions.ConnectionError as e:
                    last_error = e
                    logger.warning(f"Connection error to vision API (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                        
                except requests.exceptions.RequestException as e:
                    last_error = e
                    logger.warning(f"Request error (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
            
            # Check if we got a successful response
            if not response or response.status_code != 200:
                error_info = global_error_handler.handle_error(
                    error=last_error or Exception("Vision API request failed"),
                    module="vision",
                    function="describe_screen",
                    category=ErrorCategory.API_ERROR,
                    context={"max_retries": max_retries, "analysis_type": analysis_type}
                )
                raise Exception(f"Vision API unavailable: {error_info.user_message}")
            
            # Parse response with error handling
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="vision",
                    function="describe_screen",
                    category=ErrorCategory.PROCESSING_ERROR,
                    context={"response_text": response.text[:500]}
                )
                raise Exception(f"Invalid JSON response: {error_info.user_message}")
            
            # Validate response structure
            if "choices" not in response_data or not response_data["choices"]:
                error_info = global_error_handler.handle_error(
                    error=Exception("Invalid API response format"),
                    module="vision",
                    function="describe_screen",
                    category=ErrorCategory.VALIDATION_ERROR,
                    context={"response_data": str(response_data)[:500]}
                )
                raise Exception(f"Invalid response format: {error_info.user_message}")
            
            content = response_data["choices"][0]["message"]["content"]
            
            # Parse JSON response from model with error handling
            screen_analysis = None
            try:
                screen_analysis = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response if it's wrapped in text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        screen_analysis = json.loads(json_match.group())
                    except json.JSONDecodeError as e:
                        error_info = global_error_handler.handle_error(
                            error=e,
                            module="vision",
                            function="describe_screen",
                            category=ErrorCategory.PROCESSING_ERROR,
                            context={"content": content[:500]}
                        )
                        raise Exception(f"Could not parse vision model response: {error_info.user_message}")
                else:
                    error_info = global_error_handler.handle_error(
                        error=Exception("No JSON found in response"),
                        module="vision",
                        function="describe_screen",
                        category=ErrorCategory.PROCESSING_ERROR,
                        context={"content": content[:500]}
                    )
                    raise Exception(f"Invalid vision model response format: {error_info.user_message}")
            
            # Validate screen analysis structure
            if not isinstance(screen_analysis, dict):
                error_info = global_error_handler.handle_error(
                    error=Exception("Screen analysis is not a dictionary"),
                    module="vision",
                    function="describe_screen",
                    category=ErrorCategory.VALIDATION_ERROR,
                    context={"analysis_type": type(screen_analysis).__name__}
                )
                raise Exception(f"Invalid analysis format: {error_info.user_message}")
            
            # Add metadata if not present
            if "metadata" not in screen_analysis:
                screen_analysis["metadata"] = {}
            
            screen_analysis["metadata"].update({
                "timestamp": time.time(),
                "screen_resolution": [width, height],
                "analysis_type": analysis_type,
                "api_response_time": response.elapsed.total_seconds() if response else 0
            })
            
            # Log results
            if analysis_type == "form":
                form_count = len(screen_analysis.get('forms', []))
                total_fields = sum(len(form.get('fields', [])) for form in screen_analysis.get('forms', []))
                logger.info(f"Form analysis completed: {form_count} forms, {total_fields} fields found")
            else:
                element_count = len(screen_analysis.get('elements', []))
                logger.info(f"Screen analysis completed: {element_count} elements found")
            
            return screen_analysis
            
        except Exception as e:
            # Re-raise with additional context if not already handled
            if "Screen analysis failed" not in str(e):
                error_info = global_error_handler.handle_error(
                    error=e,
                    module="vision",
                    function="describe_screen",
                    category=ErrorCategory.PROCESSING_ERROR,
                    context={"analysis_type": analysis_type}
                )
                raise Exception(f"Screen analysis failed: {error_info.user_message}")
            raise
    
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
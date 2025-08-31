# config.py
"""
AURA Configuration Module

Centralized configuration management for all system parameters.
All modules should import settings from this file to ensure consistency.

Environment Setup (Prerequisites):
1. Create Conda environment: conda create --name aura python=3.11 -y
2. Activate environment: conda activate aura
3. Install dependencies: pip install -r requirements.txt
4. Install cliclick (macOS): brew install cliclick

Automation Method Priority (macOS):
1. PRIMARY: cliclick - Most reliable, fast, consistent
2. FALLBACK: AppleScript - Backup method only
3. PyAutoGUI is avoided on macOS due to AppKit compatibility issues
"""

import os
import sys
from pathlib import Path

# -- Project Information --
PROJECT_NAME = "AURA"
PROJECT_VERSION = "1.0.0"
PROJECT_DESCRIPTION = "Autonomous User-side Robotic Assistant"

# -- API Endpoints and Keys --
# Local server for vision model (LM Studio)
VISION_API_BASE = "http://localhost:1234/v1"

# Cloud endpoint for reasoning model (Ollama Cloud or OpenAI)
REASONING_API_BASE = "https://ollama.com"  # Ollama Cloud endpoint
REASONING_API_KEY = os.getenv("REASONING_API_KEY", "4a1181add3774859831c5d5bde617ddc.8jshsyAYcMNquYAN7dxYb7kM")

# Alternative OpenAI configuration (uncomment to use)
# REASONING_API_BASE = "https://api.openai.com/v1"
# REASONING_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")

# -- Model Names --
# Vision model will be auto-detected from LM Studio
VISION_MODEL = None  # Will be dynamically set by get_active_vision_model()
REASONING_MODEL = "gpt-oss:120b"  # The model name in your Ollama cloud service

# Alternative OpenAI model (uncomment to use)
# REASONING_MODEL = "gpt-4-vision-preview"

# -- Wake Word Configuration --
# Get your key from Picovoice Console (https://console.picovoice.ai/)
PORCUPINE_API_KEY = os.getenv("PORCUPINE_API_KEY", "8PD/iIOXWp/WlP5Sjehe0dcGl1uW3LNSLfDxEyOVveRvXkKLgfjhcQ==")
WAKE_WORD = "computer"  # Options: "computer", "jarvis", "aura", etc.

# -- Web Interface Configuration (for future use) --
FRONTEND_PORT = 3200
BACKEND_PORT = 6400
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"
BACKEND_URL = f"http://localhost:{BACKEND_PORT}"

# -- Prompt Engineering --
# The generic prompt to get a description of the screen from the vision model
# Simple prompt for basic screen description (faster processing)
VISION_PROMPT_SIMPLE = """
Look at this screenshot and describe what you see. Focus on buttons, text, and interactive elements.

List any buttons you can see with their exact text. Be specific about button labels.

{
    "description": "what you see on screen",
    "main_elements": ["button: Sign In", "button: Continue with GitHub", "text: Welcome back"]
}
"""

# Detailed prompt for comprehensive analysis (when user specifically asks for details)
VISION_PROMPT_DETAILED = """
What do you see on this screen? List any buttons, text, or clickable elements with their actual text.

{
    "description": "what this screen shows",
    "elements": ["list of buttons and text you can see"]
}
"""

# Clickable elements detection prompt
VISION_PROMPT_CLICKABLE = """
What buttons, links, and clickable elements do you see on this screen? List them with their text.

{
    "clickable_elements": [
        {"text": "actual button text", "type": "button"}
    ],
    "description": "brief description of the screen"
}
"""

# Default to simple prompt for better performance
VISION_PROMPT = VISION_PROMPT_SIMPLE

# Enhanced prompt specifically for form detection and analysis
FORM_VISION_PROMPT = """
Analyze the provided screenshot specifically for web forms and form elements. Identify all form-related elements with detailed classification and structure analysis.

For each form element, determine:
1. Element type (text_input, password, email, number, textarea, select, checkbox, radio, button, submit)
2. Field label or associated text
3. Current value or placeholder text
4. Required/optional status (if visible)
5. Validation state (error, success, neutral)
6. Form grouping or section

Return the response in this JSON structure:
{
    "forms": [
        {
            "form_id": "unique_form_identifier",
            "form_title": "form title or heading",
            "coordinates": [x1, y1, x2, y2],
            "fields": [
                {
                    "type": "text_input|password|email|number|textarea|select|checkbox|radio|button|submit",
                    "label": "field label text",
                    "placeholder": "placeholder text if any",
                    "current_value": "current field value",
                    "coordinates": [x1, y1, x2, y2],
                    "required": true|false,
                    "validation_state": "error|success|neutral",
                    "error_message": "validation error text if any",
                    "options": ["option1", "option2"]  // for select/radio elements
                }
            ]
        }
    ],
    "form_errors": [
        {
            "message": "error message text",
            "coordinates": [x1, y1, x2, y2],
            "associated_field": "field_label"
        }
    ],
    "submit_buttons": [
        {
            "text": "button text",
            "coordinates": [x1, y1, x2, y2],
            "type": "submit|button|reset"
        }
    ],
    "metadata": {
        "has_forms": true|false,
        "form_count": 1,
        "total_fields": 5,
        "timestamp": "current timestamp",
        "screen_resolution": [width, height]
    }
}
"""

# The meta-prompt for the reasoning model
REASONING_META_PROMPT = """
You are AURA, an AI assistant. Your goal is to help a user by controlling their computer. You will be given a user's command and a JSON object describing the current state of their screen. Your task is to reason about this information and return a precise action plan in JSON format.

The action plan should be a list of simple, atomic steps. Possible actions are:
- 'click': Single click at coordinates [x, y]
- 'double_click': Double click at coordinates [x, y]  
- 'type': Type the specified text
- 'scroll': Scroll in direction (up/down/left/right) by amount
- 'speak': Provide spoken feedback to the user
- 'finish': Indicate the task is complete

For web form filling, identify form fields and create a sequence of 'click' and 'type' actions to fill them appropriately.

Return the response in this JSON structure:
{
    "plan": [
        {
            "action": "click|double_click|type|scroll|speak|finish",
            "coordinates": [x, y],  // for click actions
            "text": "text to type",  // for type actions
            "direction": "up|down|left|right",  // for scroll actions
            "amount": 100,  // for scroll actions
            "message": "text to speak"  // for speak actions
        }
    ],
    "metadata": {
        "confidence": 0.95,
        "estimated_duration": 5.2
    }
}
"""

# -- Audio Settings --
# Path to sound effects for feedback
BASE_DIR = Path(__file__).parent
SOUNDS = {
    "success": str(BASE_DIR / "assets" / "sounds" / "success.wav"),
    "failure": str(BASE_DIR / "assets" / "sounds" / "failure.wav"),
    "thinking": str(BASE_DIR / "assets" / "sounds" / "thinking.wav")
}

# Audio processing settings
AUDIO_SAMPLE_RATE = 16000  # Hz, for speech recognition
AUDIO_CHUNK_SIZE = 1024    # Buffer size for audio processing
AUDIO_RECORDING_DURATION = 8.0  # Maximum recording duration in seconds
AUDIO_SILENCE_THRESHOLD = 0.005  # Threshold for silence detection (0.0 to 1.0) - lower = more sensitive
TTS_SPEED = 1.0           # Text-to-speech speed multiplier
TTS_VOLUME = 0.8          # Text-to-speech volume (0.0 to 1.0)

# -- System Settings --
# Screen capture settings
SCREENSHOT_QUALITY = 85    # JPEG quality for API transmission (1-100)
MAX_SCREENSHOT_SIZE = 1920 # Max width/height for screenshots

# Automation settings
MOUSE_MOVE_DURATION = 0.25  # Seconds for smooth cursor movement
TYPE_INTERVAL = 0.05        # Seconds between keystrokes
SCROLL_AMOUNT = 100         # Default scroll amount in pixels

# API timeout settings
VISION_API_TIMEOUT = 180    # Seconds - Increased for vision models (was 120)

# Fallback coordinates for common UI elements when vision fails
FALLBACK_COORDINATES = {
    "sign in": [(363, 360), (400, 350), (350, 370), (380, 360), (363, 340)],
    "login": [(363, 360), (400, 350), (350, 370), (380, 360), (363, 340)],
    "sign up": [(500, 360), (520, 350), (480, 370)],
    "submit": [(400, 400), (350, 400), (450, 400), (400, 380), (400, 420)],
    "continue": [(400, 400), (350, 400), (450, 400)],
    "next": [(450, 400), (400, 400), (500, 400)],
    "ok": [(400, 300), (350, 300), (450, 300)],
    "cancel": [(300, 400), (250, 400), (350, 400)],
    "close": [(600, 100), (650, 100), (550, 100)]
}
REASONING_API_TIMEOUT = 60  # Seconds
AUDIO_API_TIMEOUT = 30      # Seconds

# -- Logging Configuration --
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "aura.log"

# -- Development Settings --
DEBUG_MODE = os.getenv("AURA_DEBUG", "false").lower() == "true"
MOCK_APIS = os.getenv("AURA_MOCK_APIS", "false").lower() == "true"

# -- Environment Validation --
def check_conda_environment():
    """Check if we're running in the correct Conda environment."""
    conda_env = os.getenv('CONDA_DEFAULT_ENV')
    if conda_env != 'aura':
        return False, f"Not in 'aura' conda environment. Current: {conda_env or 'None'}"
    return True, "✅ Running in correct conda environment: aura"

def print_setup_instructions():
    """Print setup instructions if environment is not configured correctly."""
    print("\n" + "="*60)
    print("AURA ENVIRONMENT SETUP REQUIRED")
    print("="*60)
    print("\nPlease run these commands in your terminal:")
    print("\n1. Create Conda environment:")
    print("   conda create --name aura python=3.11 -y")
    print("\n2. Activate environment:")
    print("   conda activate aura")
    print("\n3. Install dependencies:")
    print("   pip install -r requirements.txt")
    print("\n4. API keys are already configured in config.py")
    print("   To override, set environment variables:")
    print("   export REASONING_API_KEY='your_custom_api_key_here'")
    print("   export PORCUPINE_API_KEY='your_custom_porcupine_key_here'")
    print("\n5. Run AURA:")
    print("   python main.py")
    print("\n" + "="*60)

# -- Dynamic Model Detection --
def get_active_vision_model():
    """
    Get the currently active model from LM Studio.
    
    This function queries LM Studio to find whatever model is currently loaded
    and returns its name for use in API requests. It doesn't filter for specific
    model types since the user wants to use whatever model is running.
    
    Returns:
        str: The name of the active model, or None if detection fails
    """
    import requests
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Query LM Studio for available models
        response = requests.get(f"{VISION_API_BASE}/models", timeout=5)
        
        if response.status_code == 200:
            models_data = response.json()
            
            # LM Studio typically returns models in this format
            if "data" in models_data and models_data["data"]:
                # Get the first available model (usually the loaded one)
                active_model = models_data["data"][0]["id"]
                logger.info(f"Detected active model in LM Studio: {active_model}")
                return active_model
            else:
                logger.warning("No models found in LM Studio response")
                return None
                
    except requests.exceptions.ConnectionError:
        logger.warning("Cannot connect to LM Studio. Make sure it's running on http://localhost:1234")
    except requests.exceptions.Timeout:
        logger.warning("LM Studio connection timeout")
    except Exception as e:
        logger.warning(f"Error detecting model: {e}")
    
    return None

def get_current_model_name():
    """
    Get the current model name for API requests.
    Always queries LM Studio fresh to get the currently loaded model.
    
    Returns:
        str: Current model name or a generic fallback that works with most setups
    """
    current_model = get_active_vision_model()
    if current_model:
        return current_model
    else:
        # Return a generic model identifier that LM Studio will accept
        # Most LM Studio setups will route requests to the loaded model regardless of name
        return "loaded-model"

def update_vision_model():
    """Update the VISION_MODEL global variable with the active model."""
    global VISION_MODEL
    if VISION_MODEL is None:
        VISION_MODEL = get_active_vision_model()
    return VISION_MODEL

# -- Configuration Validation --
def validate_config():
    """Validate configuration settings and provide helpful error messages."""
    errors = []
    warnings = []
    
    # Check Conda environment
    env_ok, env_msg = check_conda_environment()
    if not env_ok:
        warnings.append(env_msg)
    
    # Check Python version
    if sys.version_info < (3, 11):
        errors.append(f"Python 3.11+ required. Current: {sys.version}")
    
    # Check required API keys
    if REASONING_API_KEY == "your_ollama_cloud_api_key_here":
        errors.append("REASONING_API_KEY not set. Please set the environment variable or update config.py")
    
    if PORCUPINE_API_KEY == "your_porcupine_api_key_here":
        errors.append("PORCUPINE_API_KEY not set. Please get a key from https://console.picovoice.ai/")
    
    # Check sound files exist
    for sound_name, sound_path in SOUNDS.items():
        if not Path(sound_path).exists():
            warnings.append(f"Sound file not found: {sound_path} (using placeholder)")
    
    # Validate API endpoints
    if not VISION_API_BASE or not VISION_API_BASE.startswith('http'):
        errors.append("Invalid VISION_API_BASE URL")
    
    if not REASONING_API_BASE or not REASONING_API_BASE.startswith('http'):
        errors.append("Invalid REASONING_API_BASE URL")
    
    # Check model names
    if not VISION_MODEL:
        # Try to auto-detect the vision model
        try:
            update_vision_model()
            if VISION_MODEL:
                print(f"✅ Auto-detected vision model: {VISION_MODEL}")
            else:
                warnings.append("VISION_MODEL could not be auto-detected")
        except Exception as e:
            warnings.append(f"VISION_MODEL auto-detection failed: {e}")
    
    if not REASONING_MODEL:
        warnings.append("REASONING_MODEL not specified")
    
    # Validate numeric settings
    if SCREENSHOT_QUALITY < 1 or SCREENSHOT_QUALITY > 100:
        errors.append("SCREENSHOT_QUALITY must be between 1 and 100")
    
    if MAX_SCREENSHOT_SIZE < 100:
        errors.append("MAX_SCREENSHOT_SIZE too small (minimum 100)")
    
    if VISION_API_TIMEOUT < 1:
        errors.append("VISION_API_TIMEOUT too small (minimum 1 second)")
    
    if REASONING_API_TIMEOUT < 1:
        errors.append("REASONING_API_TIMEOUT too small (minimum 1 second)")
    
    # Check audio settings
    if AUDIO_SAMPLE_RATE < 8000:
        warnings.append("AUDIO_SAMPLE_RATE very low (may affect quality)")
    
    if AUDIO_RECORDING_DURATION < 2.0 or AUDIO_RECORDING_DURATION > 30.0:
        warnings.append("AUDIO_RECORDING_DURATION should be between 2-30 seconds")
    
    if not 0.0 <= AUDIO_SILENCE_THRESHOLD <= 1.0:
        warnings.append("AUDIO_SILENCE_THRESHOLD must be between 0.0 and 1.0")
    
    if TTS_VOLUME < 0 or TTS_VOLUME > 1:
        errors.append("TTS_VOLUME must be between 0.0 and 1.0")
    
    # Check automation settings
    if MOUSE_MOVE_DURATION < 0:
        errors.append("MOUSE_MOVE_DURATION cannot be negative")
    
    if TYPE_INTERVAL < 0:
        errors.append("TYPE_INTERVAL cannot be negative")
    
    # Print results
    if warnings:
        print("Configuration Warnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    
    if errors:
        print("\nConfiguration Errors:")
        for error in errors:
            print(f"  ❌ {error}")
        print_setup_instructions()
        return False
    
    if not warnings:
        print("✅ Configuration is valid")
    else:
        print("⚠️  Configuration has warnings but is functional")
    
    return True


def get_config_summary():
    """Get a summary of current configuration."""
    return {
        'project': {
            'name': PROJECT_NAME,
            'version': PROJECT_VERSION,
            'description': PROJECT_DESCRIPTION
        },
        'apis': {
            'vision_base': VISION_API_BASE,
            'reasoning_base': REASONING_API_BASE,
            'vision_model': VISION_MODEL,
            'reasoning_model': REASONING_MODEL,
            'reasoning_key_set': bool(REASONING_API_KEY and REASONING_API_KEY != "your_ollama_cloud_api_key_here"),
            'porcupine_key_set': bool(PORCUPINE_API_KEY and PORCUPINE_API_KEY != "your_porcupine_api_key_here")
        },
        'audio': {
            'wake_word': WAKE_WORD,
            'sample_rate': AUDIO_SAMPLE_RATE,
            'recording_duration': AUDIO_RECORDING_DURATION,
            'silence_threshold': AUDIO_SILENCE_THRESHOLD,
            'tts_speed': TTS_SPEED,
            'tts_volume': TTS_VOLUME
        },
        'vision': {
            'screenshot_quality': SCREENSHOT_QUALITY,
            'max_screenshot_size': MAX_SCREENSHOT_SIZE,
            'api_timeout': VISION_API_TIMEOUT
        },
        'automation': {
            'mouse_move_duration': MOUSE_MOVE_DURATION,
            'type_interval': TYPE_INTERVAL,
            'scroll_amount': SCROLL_AMOUNT
        },
        'system': {
            'debug_mode': DEBUG_MODE,
            'mock_apis': MOCK_APIS,
            'log_level': LOG_LEVEL
        }
    }

if __name__ == "__main__":
    # Run configuration validation
    if validate_config():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors")
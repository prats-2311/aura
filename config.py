# config.py
"""
AURA Configuration Module

Centralized configuration management for all system parameters.
All modules should import settings from this file to ensure consistency.

Environment Setup (Prerequisites):
1. Create Conda environment: conda create --name aura python=3.11 -y
2. Activate environment: conda activate aura
3. Install dependencies: pip install -r requirements.txt
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
REASONING_API_BASE = "https://api.ollama.ai/v1"  # Example URL from a turbo plan
REASONING_API_KEY = os.getenv("REASONING_API_KEY", "4a1181add3774859831c5d5bde617ddc.8jshsyAYcMNquYAN7dxYb7kM")

# Alternative OpenAI configuration (uncomment to use)
# REASONING_API_BASE = "https://api.openai.com/v1"
# REASONING_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")

# -- Model Names --
VISION_MODEL = "google/gemma-3-4b"  # The model name in LM Studio
REASONING_MODEL = "gpt-oss:latest"  # The model name in your Ollama cloud service

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
VISION_PROMPT = """
Analyze the provided screenshot and describe it in structured JSON format. Identify all interactive elements including buttons, links, and input fields. For each element, provide a description, its text content if any, and its bounding box coordinates [x1, y1, x2, y2]. Also, transcribe any significant text blocks.

Return the response in this JSON structure:
{
    "elements": [
        {
            "type": "button|link|input|text|dropdown|checkbox",
            "text": "element text content",
            "coordinates": [x1, y1, x2, y2],
            "description": "detailed element description"
        }
    ],
    "text_blocks": [
        {
            "content": "significant text content",
            "coordinates": [x1, y1, x2, y2]
        }
    ],
    "metadata": {
        "timestamp": "current timestamp",
        "screen_resolution": [width, height]
    }
}
"""

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
VISION_API_TIMEOUT = 30     # Seconds
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

if __name__ == "__main__":
    # Run configuration validation
    if validate_config():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors")
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

# -- Fuzzy Matching Configuration --
# Fuzzy string matching settings for accessibility enhancements
FUZZY_MATCHING_ENABLED = True
FUZZY_CONFIDENCE_THRESHOLD = 85  # Minimum confidence score (0-100) for fuzzy matches
FUZZY_MATCHING_TIMEOUT = 200     # Maximum time in milliseconds for fuzzy matching operations

# Accessibility element detection settings
CLICKABLE_ROLES = [
    "AXButton", "AXLink", "AXMenuItem", 
    "AXCheckBox", "AXRadioButton"
]
ACCESSIBILITY_ATTRIBUTES = ["AXTitle", "AXDescription", "AXValue"]

# Performance settings for enhanced accessibility
FAST_PATH_TIMEOUT = 2000         # Maximum time in milliseconds for fast path execution
ATTRIBUTE_CHECK_TIMEOUT = 500    # Maximum time in milliseconds for attribute checking

# Enhanced fallback configuration
ENHANCED_FALLBACK_ENABLED = True        # Enable enhanced fallback coordination
FALLBACK_PERFORMANCE_LOGGING = True     # Log performance comparison between fast path and vision fallback
FALLBACK_RETRY_DELAY = 0.5              # Delay in seconds before retrying after fallback
MAX_FALLBACK_RETRIES = 1                # Maximum number of fallback retries before giving up
FALLBACK_TIMEOUT_THRESHOLD = 3.0        # Seconds - trigger fallback if fast path exceeds this time

# Performance monitoring settings
PERFORMANCE_MONITORING_ENABLED = True
PERFORMANCE_WARNING_THRESHOLD = 1500  # Warn if operations take longer than this (ms)
PERFORMANCE_HISTORY_SIZE = 100         # Number of recent operations to keep in memory
PERFORMANCE_LOGGING_ENABLED = True     # Enable detailed performance logging

# Debugging settings for accessibility enhancements
ACCESSIBILITY_DEBUG_LOGGING = False
LOG_FUZZY_MATCH_SCORES = False

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

# Hybrid feedback settings
HYBRID_FEEDBACK_ENABLED = True  # Enable hybrid-specific audio feedback
HYBRID_FAST_PATH_FEEDBACK = True  # Play subtle feedback for fast path execution
HYBRID_SLOW_PATH_FEEDBACK = True  # Play feedback when using slow path (vision analysis)
HYBRID_FALLBACK_FEEDBACK = True  # Play feedback when falling back from fast to slow path
HYBRID_FEEDBACK_VOLUME = 0.6  # Volume adjustment for hybrid feedback (0.0 to 1.0)
HYBRID_FEEDBACK_MESSAGES = True  # Enable spoken messages for hybrid feedback

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

# -- Comprehensive Debugging Configuration --
# Debug levels for enhanced logging and debugging output
DEBUG_LEVELS = {
    "BASIC": 1,      # Essential failure information and timing
    "DETAILED": 2,   # Element attributes, search parameters, and match scores
    "VERBOSE": 3     # Complete accessibility tree dumps and all API interactions
}

# Current debug level setting
DEBUG_LEVEL = os.getenv("AURA_DEBUG_LEVEL", "BASIC")  # BASIC, DETAILED, VERBOSE

# Debug output configuration
DEBUG_OUTPUT_FORMAT = "structured"  # structured, json, plain
DEBUG_INCLUDE_TIMESTAMPS = True
DEBUG_INCLUDE_CONTEXT = True
DEBUG_INCLUDE_STACK_TRACE = False  # Only for VERBOSE level

# Debug logging categories - can be enabled/disabled individually
DEBUG_CATEGORIES = {
    "accessibility": True,      # Accessibility tree and element detection
    "permissions": True,        # Permission validation and requests
    "element_search": True,     # Element search and matching operations
    "performance": True,        # Performance metrics and timing
    "error_recovery": True,     # Error recovery attempts and results
    "application_detection": True,  # Application type detection
    "fuzzy_matching": True,     # Fuzzy text matching operations
    "tree_inspection": True,    # Accessibility tree inspection
    "failure_analysis": True,   # Detailed failure analysis
    "diagnostic_tools": True    # Diagnostic tool execution
}

# Debug file output settings
DEBUG_LOG_TO_FILE = True
DEBUG_LOG_TO_CONSOLE = True
DEBUG_LOG_FILE = "aura_debug.log"
DEBUG_LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB max file size
DEBUG_LOG_BACKUP_COUNT = 3  # Keep 3 backup files

# Structured logging format for debug output
DEBUG_STRUCTURED_FORMAT = {
    "timestamp": "%(asctime)s",
    "level": "%(levelname)s",
    "module": "%(name)s",
    "message": "%(message)s",
    "context": "%(context)s",
    "category": "%(category)s",
    "thread": "%(thread)d",
    "process": "%(process)d"
}

# -- Accessibility Debugging Configuration --
# Permission validation settings
PERMISSION_VALIDATION_ENABLED = True
PERMISSION_AUTO_REQUEST = False  # Automatically request permissions if missing
PERMISSION_VALIDATION_TIMEOUT = 5.0  # Seconds to wait for permission validation
PERMISSION_MONITORING_ENABLED = True  # Monitor for runtime permission changes
PERMISSION_GUIDE_ENABLED = True  # Show step-by-step permission setup guide

# Accessibility tree inspection settings
TREE_INSPECTION_ENABLED = True
TREE_DUMP_MAX_DEPTH = 10  # Maximum depth for tree traversal
TREE_DUMP_INCLUDE_HIDDEN = False  # Include hidden elements in tree dumps
TREE_DUMP_CACHE_ENABLED = True  # Cache tree dumps for performance
TREE_DUMP_CACHE_TTL = 30  # Cache time-to-live in seconds
TREE_ELEMENT_ATTRIBUTE_FILTER = []  # Empty list means include all attributes

# Element analysis and search settings
ELEMENT_ANALYSIS_ENABLED = True
ELEMENT_SEARCH_TIMEOUT = 2.0  # Seconds for element search operations
ELEMENT_COMPARISON_ENABLED = True  # Enable element comparison for debugging
FUZZY_MATCH_ANALYSIS_ENABLED = True  # Detailed fuzzy matching analysis
SIMILARITY_SCORE_THRESHOLD = 0.6  # Minimum similarity score for matches
ELEMENT_SEARCH_STRATEGIES = [
    "exact_match",
    "fuzzy_match", 
    "partial_match",
    "role_based",
    "attribute_based"
]

# Application detection and adaptation settings
APPLICATION_DETECTION_ENABLED = True
APPLICATION_STRATEGY_CACHING = True  # Cache detection strategies per application
APPLICATION_STRATEGY_CACHE_TTL = 300  # Cache TTL in seconds
BROWSER_SPECIFIC_HANDLING = True  # Enable browser-specific accessibility handling
NATIVE_APP_OPTIMIZATION = True  # Optimize for native macOS applications
WEB_APP_DETECTION = True  # Detect and handle web applications specially

# Error recovery and retry settings
ERROR_RECOVERY_ENABLED = True
ERROR_RECOVERY_MAX_RETRIES = 3
ERROR_RECOVERY_BACKOFF_FACTOR = 2.0  # Exponential backoff multiplier
ERROR_RECOVERY_BASE_DELAY = 0.5  # Base delay in seconds
ERROR_RECOVERY_MAX_DELAY = 5.0  # Maximum delay in seconds
ACCESSIBILITY_TREE_REFRESH_ENABLED = True
ELEMENT_CACHE_INVALIDATION_ENABLED = True

# Diagnostic tools configuration
DIAGNOSTIC_TOOLS_ENABLED = True
DIAGNOSTIC_AUTO_RUN = False  # Automatically run diagnostics on failures
DIAGNOSTIC_HEALTH_CHECK_INTERVAL = 300  # Seconds between automatic health checks
DIAGNOSTIC_REPORT_FORMAT = "json"  # json, html, text
DIAGNOSTIC_REPORT_INCLUDE_SCREENSHOTS = False  # Include screenshots in reports
DIAGNOSTIC_PERFORMANCE_BENCHMARKING = True
DIAGNOSTIC_ISSUE_PRIORITIZATION = True  # Prioritize issues by impact

# Performance monitoring for debugging
DEBUG_PERFORMANCE_TRACKING = True
DEBUG_EXECUTION_TIME_LOGGING = True
DEBUG_SUCCESS_RATE_TRACKING = True
DEBUG_PERFORMANCE_ALERTS = True
DEBUG_PERFORMANCE_DEGRADATION_THRESHOLD = 0.7  # Alert if success rate drops below 70%
DEBUG_PERFORMANCE_HISTORY_SIZE = 1000  # Number of operations to track

# Interactive debugging settings
INTERACTIVE_DEBUGGING_ENABLED = True
INTERACTIVE_SESSION_RECORDING = False  # Record debugging sessions
INTERACTIVE_STEP_BY_STEP = False  # Enable step-by-step debugging mode
INTERACTIVE_REAL_TIME_FEEDBACK = True  # Provide real-time feedback during debugging

# Command-line debugging tools settings
CLI_DEBUGGING_TOOLS_ENABLED = True
CLI_TREE_INSPECTOR_ENABLED = True
CLI_ELEMENT_TESTER_ENABLED = True
CLI_DIAGNOSTIC_RUNNER_ENABLED = True
CLI_PERFORMANCE_MONITOR_ENABLED = True

# Debugging output and reporting settings
DEBUG_REPORT_AUTO_GENERATION = True
DEBUG_REPORT_INCLUDE_CONTEXT = True
DEBUG_REPORT_INCLUDE_RECOMMENDATIONS = True
DEBUG_REPORT_INCLUDE_RECOVERY_STEPS = True
DEBUG_REPORT_EXPORT_FORMATS = ["json", "html"]  # Available export formats

# Security and privacy settings for debugging
DEBUG_SANITIZE_SENSITIVE_DATA = True  # Remove sensitive data from debug output
DEBUG_CONTENT_FILTERING = True  # Filter potentially sensitive content
DEBUG_PRIVACY_MODE = False  # Enhanced privacy mode for debugging
DEBUG_SECURE_LOG_HANDLING = True  # Secure handling of debug logs

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
    Get the currently active VISION-CAPABLE model from LM Studio.
    Filters out embedding models and other non-vision models.
    
    Returns:
        str: The name of the active vision model, or None if detection fails
    """
    import requests
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Known embedding model patterns to exclude
    EMBEDDING_MODEL_PATTERNS = [
        'embedding', 'embed', 'nomic-embed', 'text-embedding',
        'sentence-transformer', 'bge-', 'e5-', 'gte-'
    ]
    
    # Known vision model patterns to prioritize
    VISION_MODEL_PATTERNS = [
        'vision', 'llava', 'gpt-4v', 'claude-3', 'gemini-pro-vision',
        'minicpm-v', 'qwen-vl', 'internvl', 'cogvlm', 'moondream',
        'bakllava', 'yi-vl', 'deepseek-vl'
    ]
    
    try:
        # Query LM Studio for available models
        response = requests.get(f"{VISION_API_BASE}/models", timeout=5)
        
        if response.status_code == 200:
            models_data = response.json()
            
            # LM Studio typically returns models in this format
            if "data" in models_data and models_data["data"]:
                available_models = [model["id"] for model in models_data["data"]]
                logger.info(f"Available models in LM Studio: {available_models}")
                
                # Filter out embedding models
                vision_capable_models = []
                for model in available_models:
                    model_lower = model.lower()
                    
                    # Skip embedding models
                    if any(pattern in model_lower for pattern in EMBEDDING_MODEL_PATTERNS):
                        logger.debug(f"Skipping embedding model: {model}")
                        continue
                    
                    vision_capable_models.append(model)
                
                if not vision_capable_models:
                    logger.error("No vision-capable models found in LM Studio!")
                    logger.error("Available models are all embedding models. Please load a vision model.")
                    logger.error("Recommended: LLaVA, GPT-4V, MiniCPM-V, or similar vision models")
                    return None
                
                # Prioritize known vision models
                for model in vision_capable_models:
                    model_lower = model.lower()
                    if any(pattern in model_lower for pattern in VISION_MODEL_PATTERNS):
                        logger.info(f"Selected vision model: {model}")
                        return model
                
                # If no known vision models, use the first non-embedding model
                selected_model = vision_capable_models[0]
                logger.warning(f"Using first available non-embedding model: {selected_model}")
                logger.warning("This model may not be vision-capable. Consider loading a proper vision model.")
                return selected_model
                
            else:
                logger.warning("No models found in LM Studio response")
                return None
                
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to LM Studio. Make sure it's running on http://localhost:1234")
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
    
    # Check hybrid feedback settings
    if not 0.0 <= HYBRID_FEEDBACK_VOLUME <= 1.0:
        errors.append("HYBRID_FEEDBACK_VOLUME must be between 0.0 and 1.0")
    
    # Check fuzzy matching configuration
    if not isinstance(FUZZY_MATCHING_ENABLED, bool):
        errors.append("FUZZY_MATCHING_ENABLED must be a boolean")
    
    if not 0 <= FUZZY_CONFIDENCE_THRESHOLD <= 100:
        errors.append("FUZZY_CONFIDENCE_THRESHOLD must be between 0 and 100")
    
    if FUZZY_MATCHING_TIMEOUT < 50 or FUZZY_MATCHING_TIMEOUT > 5000:
        warnings.append("FUZZY_MATCHING_TIMEOUT should be between 50-5000 milliseconds")
    
    if not isinstance(CLICKABLE_ROLES, list) or not CLICKABLE_ROLES:
        errors.append("CLICKABLE_ROLES must be a non-empty list")
    
    if not isinstance(ACCESSIBILITY_ATTRIBUTES, list) or not ACCESSIBILITY_ATTRIBUTES:
        errors.append("ACCESSIBILITY_ATTRIBUTES must be a non-empty list")
    
    if FAST_PATH_TIMEOUT < 500 or FAST_PATH_TIMEOUT > 10000:
        warnings.append("FAST_PATH_TIMEOUT should be between 500-10000 milliseconds")
    
    if ATTRIBUTE_CHECK_TIMEOUT < 100 or ATTRIBUTE_CHECK_TIMEOUT > 2000:
        warnings.append("ATTRIBUTE_CHECK_TIMEOUT should be between 100-2000 milliseconds")
    
    if not isinstance(ACCESSIBILITY_DEBUG_LOGGING, bool):
        errors.append("ACCESSIBILITY_DEBUG_LOGGING must be a boolean")
    
    if not isinstance(LOG_FUZZY_MATCH_SCORES, bool):
        errors.append("LOG_FUZZY_MATCH_SCORES must be a boolean")
    
    # Validate enhanced fallback configuration
    if not isinstance(ENHANCED_FALLBACK_ENABLED, bool):
        errors.append("ENHANCED_FALLBACK_ENABLED must be a boolean")
    
    if not isinstance(FALLBACK_PERFORMANCE_LOGGING, bool):
        errors.append("FALLBACK_PERFORMANCE_LOGGING must be a boolean")
    
    if FALLBACK_RETRY_DELAY < 0.1 or FALLBACK_RETRY_DELAY > 5.0:
        warnings.append("FALLBACK_RETRY_DELAY should be between 0.1-5.0 seconds")
    
    if MAX_FALLBACK_RETRIES < 0 or MAX_FALLBACK_RETRIES > 5:
        warnings.append("MAX_FALLBACK_RETRIES should be between 0-5")
    
    if FALLBACK_TIMEOUT_THRESHOLD < 1.0 or FALLBACK_TIMEOUT_THRESHOLD > 10.0:
        warnings.append("FALLBACK_TIMEOUT_THRESHOLD should be between 1.0-10.0 seconds")
    
    # Check performance monitoring settings
    if not isinstance(PERFORMANCE_MONITORING_ENABLED, bool):
        errors.append("PERFORMANCE_MONITORING_ENABLED must be a boolean")
    
    if PERFORMANCE_WARNING_THRESHOLD < 100 or PERFORMANCE_WARNING_THRESHOLD > 10000:
        warnings.append("PERFORMANCE_WARNING_THRESHOLD should be between 100-10000 milliseconds")
    
    if PERFORMANCE_HISTORY_SIZE < 10 or PERFORMANCE_HISTORY_SIZE > 1000:
        warnings.append("PERFORMANCE_HISTORY_SIZE should be between 10-1000")
    
    if not isinstance(PERFORMANCE_LOGGING_ENABLED, bool):
        errors.append("PERFORMANCE_LOGGING_ENABLED must be a boolean")
    
    # Check automation settings
    if MOUSE_MOVE_DURATION < 0:
        errors.append("MOUSE_MOVE_DURATION cannot be negative")
    
    if TYPE_INTERVAL < 0:
        errors.append("TYPE_INTERVAL cannot be negative")
    
    # Validate debugging configuration
    if DEBUG_LEVEL not in DEBUG_LEVELS:
        errors.append(f"DEBUG_LEVEL must be one of: {list(DEBUG_LEVELS.keys())}")
    
    if DEBUG_OUTPUT_FORMAT not in ["structured", "json", "plain"]:
        errors.append("DEBUG_OUTPUT_FORMAT must be 'structured', 'json', or 'plain'")
    
    # Validate permission validation settings
    if not isinstance(PERMISSION_VALIDATION_ENABLED, bool):
        errors.append("PERMISSION_VALIDATION_ENABLED must be a boolean")
    
    if not isinstance(PERMISSION_AUTO_REQUEST, bool):
        errors.append("PERMISSION_AUTO_REQUEST must be a boolean")
    
    if PERMISSION_VALIDATION_TIMEOUT < 1.0 or PERMISSION_VALIDATION_TIMEOUT > 30.0:
        warnings.append("PERMISSION_VALIDATION_TIMEOUT should be between 1.0-30.0 seconds")
    
    # Validate tree inspection settings
    if TREE_DUMP_MAX_DEPTH < 1 or TREE_DUMP_MAX_DEPTH > 50:
        warnings.append("TREE_DUMP_MAX_DEPTH should be between 1-50")
    
    if TREE_DUMP_CACHE_TTL < 10 or TREE_DUMP_CACHE_TTL > 300:
        warnings.append("TREE_DUMP_CACHE_TTL should be between 10-300 seconds")
    
    # Validate element analysis settings
    if ELEMENT_SEARCH_TIMEOUT < 0.5 or ELEMENT_SEARCH_TIMEOUT > 10.0:
        warnings.append("ELEMENT_SEARCH_TIMEOUT should be between 0.5-10.0 seconds")
    
    if not 0.0 <= SIMILARITY_SCORE_THRESHOLD <= 1.0:
        errors.append("SIMILARITY_SCORE_THRESHOLD must be between 0.0 and 1.0")
    
    if not isinstance(ELEMENT_SEARCH_STRATEGIES, list) or not ELEMENT_SEARCH_STRATEGIES:
        errors.append("ELEMENT_SEARCH_STRATEGIES must be a non-empty list")
    
    # Validate error recovery settings
    if ERROR_RECOVERY_MAX_RETRIES < 0 or ERROR_RECOVERY_MAX_RETRIES > 10:
        warnings.append("ERROR_RECOVERY_MAX_RETRIES should be between 0-10")
    
    if ERROR_RECOVERY_BACKOFF_FACTOR < 1.0 or ERROR_RECOVERY_BACKOFF_FACTOR > 5.0:
        warnings.append("ERROR_RECOVERY_BACKOFF_FACTOR should be between 1.0-5.0")
    
    if ERROR_RECOVERY_BASE_DELAY < 0.1 or ERROR_RECOVERY_BASE_DELAY > 2.0:
        warnings.append("ERROR_RECOVERY_BASE_DELAY should be between 0.1-2.0 seconds")
    
    if ERROR_RECOVERY_MAX_DELAY < 1.0 or ERROR_RECOVERY_MAX_DELAY > 30.0:
        warnings.append("ERROR_RECOVERY_MAX_DELAY should be between 1.0-30.0 seconds")
    
    # Validate diagnostic settings
    if DIAGNOSTIC_HEALTH_CHECK_INTERVAL < 60 or DIAGNOSTIC_HEALTH_CHECK_INTERVAL > 3600:
        warnings.append("DIAGNOSTIC_HEALTH_CHECK_INTERVAL should be between 60-3600 seconds")
    
    if DIAGNOSTIC_REPORT_FORMAT not in ["json", "html", "text"]:
        errors.append("DIAGNOSTIC_REPORT_FORMAT must be 'json', 'html', or 'text'")
    
    # Validate performance monitoring settings
    if not 0.0 <= DEBUG_PERFORMANCE_DEGRADATION_THRESHOLD <= 1.0:
        errors.append("DEBUG_PERFORMANCE_DEGRADATION_THRESHOLD must be between 0.0 and 1.0")
    
    if DEBUG_PERFORMANCE_HISTORY_SIZE < 100 or DEBUG_PERFORMANCE_HISTORY_SIZE > 10000:
        warnings.append("DEBUG_PERFORMANCE_HISTORY_SIZE should be between 100-10000")
    
    # Validate debug report export formats
    valid_export_formats = ["json", "html", "text", "xml"]
    for fmt in DEBUG_REPORT_EXPORT_FORMATS:
        if fmt not in valid_export_formats:
            errors.append(f"Invalid DEBUG_REPORT_EXPORT_FORMAT: {fmt}. Must be one of: {valid_export_formats}")
    
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


def validate_debugging_config():
    """
    Validate debugging configuration settings and provide detailed feedback.
    
    Returns:
        tuple: (is_valid: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []
    
    # Validate debug level
    if DEBUG_LEVEL not in DEBUG_LEVELS:
        errors.append(f"Invalid DEBUG_LEVEL '{DEBUG_LEVEL}'. Must be one of: {list(DEBUG_LEVELS.keys())}")
    
    # Validate output format
    valid_formats = ["structured", "json", "plain"]
    if DEBUG_OUTPUT_FORMAT not in valid_formats:
        errors.append(f"Invalid DEBUG_OUTPUT_FORMAT '{DEBUG_OUTPUT_FORMAT}'. Must be one of: {valid_formats}")
    
    # Validate debug categories
    if not isinstance(DEBUG_CATEGORIES, dict):
        errors.append("DEBUG_CATEGORIES must be a dictionary")
    else:
        for category, enabled in DEBUG_CATEGORIES.items():
            if not isinstance(enabled, bool):
                errors.append(f"DEBUG_CATEGORIES['{category}'] must be a boolean")
    
    # Validate file settings
    if DEBUG_LOG_MAX_SIZE < 1024 * 1024:  # 1MB minimum
        warnings.append("DEBUG_LOG_MAX_SIZE is very small (< 1MB)")
    
    if DEBUG_LOG_BACKUP_COUNT < 1:
        warnings.append("DEBUG_LOG_BACKUP_COUNT should be at least 1")
    
    # Validate permission settings
    if not isinstance(PERMISSION_VALIDATION_ENABLED, bool):
        errors.append("PERMISSION_VALIDATION_ENABLED must be a boolean")
    
    if PERMISSION_VALIDATION_TIMEOUT <= 0:
        errors.append("PERMISSION_VALIDATION_TIMEOUT must be positive")
    elif PERMISSION_VALIDATION_TIMEOUT > 30:
        warnings.append("PERMISSION_VALIDATION_TIMEOUT is very high (> 30 seconds)")
    
    # Validate tree inspection settings
    if TREE_DUMP_MAX_DEPTH <= 0:
        errors.append("TREE_DUMP_MAX_DEPTH must be positive")
    elif TREE_DUMP_MAX_DEPTH > 20:
        warnings.append("TREE_DUMP_MAX_DEPTH is very high (> 20), may impact performance")
    
    if TREE_DUMP_CACHE_TTL <= 0:
        errors.append("TREE_DUMP_CACHE_TTL must be positive")
    
    # Validate element analysis settings
    if ELEMENT_SEARCH_TIMEOUT <= 0:
        errors.append("ELEMENT_SEARCH_TIMEOUT must be positive")
    elif ELEMENT_SEARCH_TIMEOUT > 10:
        warnings.append("ELEMENT_SEARCH_TIMEOUT is very high (> 10 seconds)")
    
    if not 0 <= SIMILARITY_SCORE_THRESHOLD <= 1:
        errors.append("SIMILARITY_SCORE_THRESHOLD must be between 0 and 1")
    
    if not isinstance(ELEMENT_SEARCH_STRATEGIES, list) or not ELEMENT_SEARCH_STRATEGIES:
        errors.append("ELEMENT_SEARCH_STRATEGIES must be a non-empty list")
    
    # Validate error recovery settings
    if ERROR_RECOVERY_MAX_RETRIES < 0:
        errors.append("ERROR_RECOVERY_MAX_RETRIES cannot be negative")
    elif ERROR_RECOVERY_MAX_RETRIES > 10:
        warnings.append("ERROR_RECOVERY_MAX_RETRIES is very high (> 10)")
    
    if ERROR_RECOVERY_BACKOFF_FACTOR < 1:
        errors.append("ERROR_RECOVERY_BACKOFF_FACTOR must be >= 1")
    
    if ERROR_RECOVERY_BASE_DELAY <= 0:
        errors.append("ERROR_RECOVERY_BASE_DELAY must be positive")
    
    if ERROR_RECOVERY_MAX_DELAY <= ERROR_RECOVERY_BASE_DELAY:
        errors.append("ERROR_RECOVERY_MAX_DELAY must be greater than ERROR_RECOVERY_BASE_DELAY")
    
    # Validate diagnostic settings
    if DIAGNOSTIC_HEALTH_CHECK_INTERVAL <= 0:
        errors.append("DIAGNOSTIC_HEALTH_CHECK_INTERVAL must be positive")
    elif DIAGNOSTIC_HEALTH_CHECK_INTERVAL < 60:
        warnings.append("DIAGNOSTIC_HEALTH_CHECK_INTERVAL is very low (< 60 seconds)")
    
    valid_report_formats = ["json", "html", "text"]
    if DIAGNOSTIC_REPORT_FORMAT not in valid_report_formats:
        errors.append(f"Invalid DIAGNOSTIC_REPORT_FORMAT '{DIAGNOSTIC_REPORT_FORMAT}'. Must be one of: {valid_report_formats}")
    
    # Validate performance tracking settings
    if not 0 <= DEBUG_PERFORMANCE_DEGRADATION_THRESHOLD <= 1:
        errors.append("DEBUG_PERFORMANCE_DEGRADATION_THRESHOLD must be between 0 and 1")
    
    if DEBUG_PERFORMANCE_HISTORY_SIZE <= 0:
        errors.append("DEBUG_PERFORMANCE_HISTORY_SIZE must be positive")
    elif DEBUG_PERFORMANCE_HISTORY_SIZE > 10000:
        warnings.append("DEBUG_PERFORMANCE_HISTORY_SIZE is very high (> 10000), may impact memory usage")
    
    # Validate export formats
    valid_export_formats = ["json", "html", "text", "xml"]
    if not isinstance(DEBUG_REPORT_EXPORT_FORMATS, list):
        errors.append("DEBUG_REPORT_EXPORT_FORMATS must be a list")
    else:
        for fmt in DEBUG_REPORT_EXPORT_FORMATS:
            if fmt not in valid_export_formats:
                errors.append(f"Invalid export format '{fmt}'. Must be one of: {valid_export_formats}")
    
    return len(errors) == 0, errors, warnings


def get_debugging_config_defaults():
    """
    Get default values for debugging configuration.
    
    Returns:
        dict: Default debugging configuration values
    """
    return {
        'debug_level': 'BASIC',
        'output_format': 'structured',
        'log_to_file': True,
        'log_to_console': True,
        'permission_validation_enabled': True,
        'permission_auto_request': False,
        'permission_validation_timeout': 5.0,
        'tree_inspection_enabled': True,
        'tree_dump_max_depth': 10,
        'tree_dump_cache_enabled': True,
        'tree_dump_cache_ttl': 30,
        'element_analysis_enabled': True,
        'element_search_timeout': 2.0,
        'similarity_score_threshold': 0.6,
        'application_detection_enabled': True,
        'error_recovery_enabled': True,
        'error_recovery_max_retries': 3,
        'error_recovery_backoff_factor': 2.0,
        'diagnostic_tools_enabled': True,
        'diagnostic_auto_run': False,
        'diagnostic_health_check_interval': 300,
        'debug_performance_tracking': True,
        'debug_performance_degradation_threshold': 0.7,
        'interactive_debugging_enabled': True,
        'cli_debugging_tools_enabled': True,
        'debug_sanitize_sensitive_data': True
    }


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
            'tts_volume': TTS_VOLUME,
            'hybrid_feedback_enabled': HYBRID_FEEDBACK_ENABLED,
            'hybrid_fast_path_feedback': HYBRID_FAST_PATH_FEEDBACK,
            'hybrid_slow_path_feedback': HYBRID_SLOW_PATH_FEEDBACK,
            'hybrid_fallback_feedback': HYBRID_FALLBACK_FEEDBACK,
            'hybrid_feedback_volume': HYBRID_FEEDBACK_VOLUME,
            'hybrid_feedback_messages': HYBRID_FEEDBACK_MESSAGES
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
        },
        'fuzzy_matching': {
            'enabled': FUZZY_MATCHING_ENABLED,
            'confidence_threshold': FUZZY_CONFIDENCE_THRESHOLD,
            'timeout_ms': FUZZY_MATCHING_TIMEOUT,
            'clickable_roles': CLICKABLE_ROLES,
            'accessibility_attributes': ACCESSIBILITY_ATTRIBUTES,
            'fast_path_timeout_ms': FAST_PATH_TIMEOUT,
            'attribute_check_timeout_ms': ATTRIBUTE_CHECK_TIMEOUT,
            'debug_logging': ACCESSIBILITY_DEBUG_LOGGING,
            'log_match_scores': LOG_FUZZY_MATCH_SCORES,
            'enhanced_fallback_enabled': ENHANCED_FALLBACK_ENABLED,
            'fallback_performance_logging': FALLBACK_PERFORMANCE_LOGGING,
            'fallback_retry_delay': FALLBACK_RETRY_DELAY,
            'max_fallback_retries': MAX_FALLBACK_RETRIES,
            'fallback_timeout_threshold': FALLBACK_TIMEOUT_THRESHOLD
        },
        'performance_monitoring': {
            'enabled': PERFORMANCE_MONITORING_ENABLED,
            'warning_threshold_ms': PERFORMANCE_WARNING_THRESHOLD,
            'history_size': PERFORMANCE_HISTORY_SIZE,
            'logging_enabled': PERFORMANCE_LOGGING_ENABLED
        },
        'debugging': {
            'debug_level': DEBUG_LEVEL,
            'output_format': DEBUG_OUTPUT_FORMAT,
            'categories': DEBUG_CATEGORIES,
            'log_to_file': DEBUG_LOG_TO_FILE,
            'log_to_console': DEBUG_LOG_TO_CONSOLE,
            'permission_validation': {
                'enabled': PERMISSION_VALIDATION_ENABLED,
                'auto_request': PERMISSION_AUTO_REQUEST,
                'timeout': PERMISSION_VALIDATION_TIMEOUT,
                'monitoring_enabled': PERMISSION_MONITORING_ENABLED,
                'guide_enabled': PERMISSION_GUIDE_ENABLED
            },
            'tree_inspection': {
                'enabled': TREE_INSPECTION_ENABLED,
                'max_depth': TREE_DUMP_MAX_DEPTH,
                'include_hidden': TREE_DUMP_INCLUDE_HIDDEN,
                'cache_enabled': TREE_DUMP_CACHE_ENABLED,
                'cache_ttl': TREE_DUMP_CACHE_TTL
            },
            'element_analysis': {
                'enabled': ELEMENT_ANALYSIS_ENABLED,
                'search_timeout': ELEMENT_SEARCH_TIMEOUT,
                'comparison_enabled': ELEMENT_COMPARISON_ENABLED,
                'fuzzy_match_analysis': FUZZY_MATCH_ANALYSIS_ENABLED,
                'similarity_threshold': SIMILARITY_SCORE_THRESHOLD,
                'search_strategies': ELEMENT_SEARCH_STRATEGIES
            },
            'application_detection': {
                'enabled': APPLICATION_DETECTION_ENABLED,
                'strategy_caching': APPLICATION_STRATEGY_CACHING,
                'cache_ttl': APPLICATION_STRATEGY_CACHE_TTL,
                'browser_specific': BROWSER_SPECIFIC_HANDLING,
                'native_app_optimization': NATIVE_APP_OPTIMIZATION,
                'web_app_detection': WEB_APP_DETECTION
            },
            'error_recovery': {
                'enabled': ERROR_RECOVERY_ENABLED,
                'max_retries': ERROR_RECOVERY_MAX_RETRIES,
                'backoff_factor': ERROR_RECOVERY_BACKOFF_FACTOR,
                'base_delay': ERROR_RECOVERY_BASE_DELAY,
                'max_delay': ERROR_RECOVERY_MAX_DELAY,
                'tree_refresh_enabled': ACCESSIBILITY_TREE_REFRESH_ENABLED,
                'cache_invalidation_enabled': ELEMENT_CACHE_INVALIDATION_ENABLED
            },
            'diagnostic_tools': {
                'enabled': DIAGNOSTIC_TOOLS_ENABLED,
                'auto_run': DIAGNOSTIC_AUTO_RUN,
                'health_check_interval': DIAGNOSTIC_HEALTH_CHECK_INTERVAL,
                'report_format': DIAGNOSTIC_REPORT_FORMAT,
                'include_screenshots': DIAGNOSTIC_REPORT_INCLUDE_SCREENSHOTS,
                'performance_benchmarking': DIAGNOSTIC_PERFORMANCE_BENCHMARKING,
                'issue_prioritization': DIAGNOSTIC_ISSUE_PRIORITIZATION
            },
            'performance_tracking': {
                'enabled': DEBUG_PERFORMANCE_TRACKING,
                'execution_time_logging': DEBUG_EXECUTION_TIME_LOGGING,
                'success_rate_tracking': DEBUG_SUCCESS_RATE_TRACKING,
                'alerts_enabled': DEBUG_PERFORMANCE_ALERTS,
                'degradation_threshold': DEBUG_PERFORMANCE_DEGRADATION_THRESHOLD,
                'history_size': DEBUG_PERFORMANCE_HISTORY_SIZE
            },
            'interactive_debugging': {
                'enabled': INTERACTIVE_DEBUGGING_ENABLED,
                'session_recording': INTERACTIVE_SESSION_RECORDING,
                'step_by_step': INTERACTIVE_STEP_BY_STEP,
                'real_time_feedback': INTERACTIVE_REAL_TIME_FEEDBACK
            },
            'cli_tools': {
                'enabled': CLI_DEBUGGING_TOOLS_ENABLED,
                'tree_inspector': CLI_TREE_INSPECTOR_ENABLED,
                'element_tester': CLI_ELEMENT_TESTER_ENABLED,
                'diagnostic_runner': CLI_DIAGNOSTIC_RUNNER_ENABLED,
                'performance_monitor': CLI_PERFORMANCE_MONITOR_ENABLED
            },
            'reporting': {
                'auto_generation': DEBUG_REPORT_AUTO_GENERATION,
                'include_context': DEBUG_REPORT_INCLUDE_CONTEXT,
                'include_recommendations': DEBUG_REPORT_INCLUDE_RECOMMENDATIONS,
                'include_recovery_steps': DEBUG_REPORT_INCLUDE_RECOVERY_STEPS,
                'export_formats': DEBUG_REPORT_EXPORT_FORMATS
            },
            'security': {
                'sanitize_sensitive_data': DEBUG_SANITIZE_SENSITIVE_DATA,
                'content_filtering': DEBUG_CONTENT_FILTERING,
                'privacy_mode': DEBUG_PRIVACY_MODE,
                'secure_log_handling': DEBUG_SECURE_LOG_HANDLING
            }
        }
    }

if __name__ == "__main__":
    # Run configuration validation
    if validate_config():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors")
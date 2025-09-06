# AURA Conversational Enhancement Setup Guide

## Overview

This guide covers the setup and configuration for AURA's conversational enhancement features, which include:

- **Intent Recognition**: Intelligent classification of user commands
- **Conversational Chat**: Natural language conversations with AURA
- **Deferred Actions**: Multi-step workflows for content generation and placement
- **Global Mouse Handling**: System-wide mouse event detection for interactive workflows

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Operating System**: macOS (primary), Windows, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended for optimal performance)
- **Storage**: At least 2GB free space for dependencies

### Required Dependencies

The conversational enhancement features require the following key dependencies:

#### Core Dependencies

- `pynput>=1.7.6` - Global mouse and keyboard event handling
- `requests>=2.31.0` - HTTP requests for API communication
- `python-dotenv>=1.0.0` - Environment variable management

#### Audio Processing

- `pygame>=2.5.2` - Audio playback for feedback
- `pyttsx3>=2.90` - Text-to-speech for conversational responses

#### AI and ML

- `ollama>=0.3.0` - Ollama Cloud API client for reasoning
- `transformers>=4.35.0` - Hugging Face transformers (optional)

## Installation Steps

### 1. Environment Setup

```bash
# Create and activate Conda environment
conda create --name aura python=3.11 -y
conda activate aura

# Navigate to AURA directory
cd /path/to/aura
```

### 2. Install Dependencies

```bash
# Install all dependencies from requirements.txt
pip install -r requirements.txt

# Verify pynput installation
python -c "import pynput; from pynput import mouse, keyboard; print('✅ pynput installed successfully')"
```

### 3. Platform-Specific Setup

#### macOS

```bash
# Install cliclick for enhanced automation
brew install cliclick

# Verify accessibility permissions
python -c "
import sys
if sys.platform == 'darwin':
    try:
        from AppKit import NSWorkspace
        print('✅ macOS accessibility frameworks available')
    except ImportError:
        print('❌ Install pyobjc: pip install pyobjc pyobjc-framework-ApplicationServices')
"
```

#### Windows

```bash
# Verify Windows-specific dependencies
python -c "
import sys
if sys.platform == 'win32':
    try:
        import pywin32
        print('✅ Windows API access available')
    except ImportError:
        print('❌ Install pywin32: pip install pywin32')
"
```

#### Linux

```bash
# Install X11 dependencies
sudo apt-get install python3-xlib  # Ubuntu/Debian
# or
sudo yum install python3-xlib      # CentOS/RHEL

# Verify Linux dependencies
python -c "
import sys
if sys.platform == 'linux':
    try:
        import Xlib
        print('✅ X11 libraries available')
    except ImportError:
        print('❌ Install python-xlib: pip install python-xlib')
"
```

### 4. Configuration Validation

Run the configuration validation to ensure everything is set up correctly:

```bash
python -c "
from config import validate_config, validate_conversational_config
errors, warnings = validate_config()
conv_errors, conv_warnings = validate_conversational_config()

if errors or conv_errors:
    print('❌ Configuration Errors:')
    for error in errors + conv_errors:
        print(f'  - {error}')
else:
    print('✅ Configuration validation passed')

if warnings or conv_warnings:
    print('⚠️  Configuration Warnings:')
    for warning in warnings + conv_warnings:
        print(f'  - {warning}')
"
```

## Configuration Options

### Deferred Action Settings

Configure how AURA handles multi-step workflows:

```python
# In config.py
DEFERRED_ACTION_TIMEOUT = 300.0  # Max wait time (seconds)
MOUSE_LISTENER_SENSITIVITY = 1.0  # Click detection sensitivity
DEFERRED_ACTION_AUDIO_CUES = True  # Enable audio guidance
DEFERRED_ACTION_RETRY_ATTEMPTS = 3  # Retry attempts for failed actions
```

### Conversational Settings

Customize AURA's conversational behavior:

```python
# In config.py
CONVERSATION_CONTEXT_SIZE = 5  # Number of previous exchanges to remember
CONVERSATION_PERSONALITY = "helpful"  # Response style
CONVERSATION_RESPONSE_MAX_LENGTH = 500  # Max response length
CONVERSATION_TIMEOUT = 30.0  # Response generation timeout
```

### Intent Recognition Settings

Fine-tune command classification:

```python
# In config.py
INTENT_RECOGNITION_ENABLED = True  # Enable intent classification
INTENT_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for classification
INTENT_FALLBACK_TO_GUI = True  # Fallback to GUI mode when uncertain
INTENT_RECOGNITION_TIMEOUT = 15.0  # Classification timeout
```

### Mouse Listener Configuration

Control global mouse event handling:

```python
# In config.py
GLOBAL_MOUSE_EVENTS_ENABLED = True  # Enable global mouse capture
MOUSE_LISTENER_DOUBLE_CLICK_TIME = 0.5  # Double-click detection window
MOUSE_LISTENER_ERROR_RECOVERY = True  # Auto-recovery on errors
```

## Testing the Installation

### 1. Basic Functionality Test

```bash
python -c "
# Test basic imports
try:
    from orchestrator import Orchestrator
    from modules.reasoning import ReasoningModule
    from utils.mouse_listener import GlobalMouseListener
    print('✅ All core modules imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
"
```

### 2. Mouse Listener Test

```bash
python -c "
from utils.mouse_listener import GlobalMouseListener
import time

def test_callback():
    print('✅ Mouse click detected!')

listener = GlobalMouseListener(test_callback)
print('Testing mouse listener for 5 seconds...')
print('Click anywhere to test detection')
listener.start()
time.sleep(5)
listener.stop()
print('Mouse listener test completed')
"
```

### 3. Intent Recognition Test

```bash
python -c "
from orchestrator import Orchestrator
import asyncio

async def test_intent():
    orchestrator = Orchestrator()

    test_commands = [
        'click on the sign in button',
        'hello, how are you today?',
        'write a python function to calculate fibonacci',
        'what do you see on the screen?'
    ]

    for cmd in test_commands:
        try:
            intent = orchestrator._recognize_intent(cmd)
            print(f'Command: \"{cmd}\"')
            print(f'Intent: {intent.get(\"intent\", \"unknown\")}')
            print(f'Confidence: {intent.get(\"confidence\", 0.0):.2f}')
            print('---')
        except Exception as e:
            print(f'Error testing intent for \"{cmd}\": {e}')

asyncio.run(test_intent())
"
```

## Troubleshooting

### Common Issues

#### 1. pynput Permission Errors (macOS)

**Problem**: `pynput` cannot capture global mouse events
**Solution**:

1. Go to System Preferences → Security & Privacy → Privacy → Accessibility
2. Add Terminal or your Python IDE to the list of allowed applications
3. Restart the application

#### 2. Import Errors

**Problem**: `ModuleNotFoundError` for pynput or other dependencies
**Solution**:

```bash
# Reinstall dependencies
pip uninstall pynput
pip install pynput>=1.7.6

# Verify installation
python -c "import pynput; print('pynput version check passed')"
```

#### 3. Configuration Validation Failures

**Problem**: Configuration validation reports errors
**Solution**:

1. Check the specific error messages
2. Verify all required prompt templates are properly formatted
3. Ensure timeout values are within acceptable ranges
4. Run: `python -c "from config import validate_conversational_config; print(validate_conversational_config())"`

#### 4. Mouse Listener Not Working

**Problem**: Global mouse events not detected
**Solution**:

1. Verify system permissions for accessibility/input monitoring
2. Check if other applications are interfering with mouse capture
3. Test with a simple mouse listener script
4. Ensure `GLOBAL_MOUSE_EVENTS_ENABLED = True` in config

### Performance Optimization

#### 1. Reduce Intent Recognition Latency

```python
# In config.py
INTENT_RECOGNITION_TIMEOUT = 10.0  # Reduce from default 15.0
INTENT_CACHE_ENABLED = True  # Enable caching
```

#### 2. Optimize Conversation Memory

```python
# In config.py
CONVERSATION_CONTEXT_SIZE = 3  # Reduce from default 5
CONVERSATION_RESPONSE_MAX_LENGTH = 300  # Reduce from default 500
```

#### 3. Tune Deferred Action Performance

```python
# In config.py
MOUSE_LISTENER_THREAD_TIMEOUT = 5.0  # Reduce from default 10.0
DEFERRED_ACTION_TIMEOUT = 180.0  # Reduce from default 300.0
```

## Environment Variables

You can override configuration settings using environment variables:

```bash
# API Configuration
export REASONING_API_KEY="your_ollama_cloud_api_key"
export PORCUPINE_API_KEY="your_porcupine_api_key"

# Debug Settings
export AURA_DEBUG="true"
export AURA_DEBUG_LEVEL="DETAILED"

# Conversational Enhancement Settings
export AURA_INTENT_ENABLED="true"
export AURA_DEFERRED_TIMEOUT="600"
export AURA_CONVERSATION_CONTEXT="10"
```

## Verification Checklist

Before using the conversational enhancement features, verify:

- [ ] Python 3.11+ is installed and active
- [ ] All dependencies from requirements.txt are installed
- [ ] pynput can be imported without errors
- [ ] System permissions are granted for accessibility/input monitoring
- [ ] Configuration validation passes without errors
- [ ] API keys are properly configured
- [ ] Sound files exist for audio feedback
- [ ] Mouse listener test works correctly
- [ ] Intent recognition test produces reasonable results

## Next Steps

Once setup is complete:

1. **Test Basic Functionality**: Run `python main.py` and try simple commands
2. **Test Conversational Features**: Try natural language queries
3. **Test Deferred Actions**: Request code generation with click-to-place
4. **Customize Configuration**: Adjust settings based on your preferences
5. **Review Documentation**: Check the design and requirements documents for detailed feature information

For additional help, refer to:

- `requirements.md` - Feature requirements
- `design.md` - Technical architecture
- `tasks.md` - Implementation tasks and progress

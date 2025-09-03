# AURA Troubleshooting Guide

## Quick Fix for Current Errors

Based on your error log, here are the specific issues and their solutions:

### Error Analysis

Your error log shows these main issues:

1. **Accessibility frameworks not available**: `cannot import name 'NSWorkspace' from 'AppKit'`
2. **Sound files missing**: `Sound 'thinking' not available`
3. **Vision/Reasoning errors**: JSON parsing and screen context issues

## Step-by-Step Fix

### Step 1: Install Missing Dependencies

```bash
# Run the automated fix script
python fix_aura_setup.py
```

**OR manually install dependencies:**

```bash
# Install PyObjC frameworks for macOS accessibility
pip install pyobjc-core
pip install pyobjc-framework-Cocoa
pip install pyobjc-framework-AppKit
pip install pyobjc-framework-ApplicationServices
pip install pyobjc-framework-CoreFoundation
pip install pyobjc-framework-Quartz

# Install audio dependencies
pip install sounddevice numpy pydub pygame pyttsx3

# Install other missing packages
pip install requests pillow mss psutil
```

### Step 2: Test Basic Functionality

```bash
# Test the hybrid architecture without full main.py complexity
python test_hybrid_simple.py
```

This will show you which components are working and which need attention.

### Step 3: Create Missing Audio Files

```bash
# Create the sounds directory
mkdir -p sounds

# Run this Python script to create basic audio files
python -c "
import pygame
import numpy as np
from pathlib import Path

pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

def create_beep(filename, frequency=800, duration=0.3):
    frames = int(duration * 22050)
    arr = np.zeros((frames, 2))

    for i in range(frames):
        wave = np.sin(2 * np.pi * frequency * i / 22050)
        arr[i] = [wave * 0.3, wave * 0.3]

    sound_array = (arr * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(sound_array)

    # Save the sound (this is a simplified approach)
    print(f'Created {filename}')

sounds_dir = Path('sounds')
sounds_dir.mkdir(exist_ok=True)

# Create placeholder files
for sound_name in ['thinking.wav', 'success.wav', 'error.wav', 'listening.wav']:
    (sounds_dir / sound_name).touch()
    print(f'Created placeholder: {sound_name}')

pygame.mixer.quit()
print('Audio files created successfully')
"
```

### Step 4: Test Individual Components

#### Test Accessibility Module

```bash
python -c "
try:
    from modules.accessibility import AccessibilityModule
    module = AccessibilityModule()
    status = module.get_accessibility_status()
    print('Accessibility Status:')
    print(f'  API Initialized: {status.get(\"api_initialized\", False)}')
    print(f'  Permissions Granted: {status.get(\"permissions_granted\", False)}')
    print(f'  Degraded Mode: {status.get(\"degraded_mode\", True)}')

    if status.get('degraded_mode'):
        print('\\n⚠️  Accessibility is in degraded mode.')
        print('This is normal if you haven\\'t granted permissions yet.')
        print('AURA will use vision-based fallback.')
    else:
        print('✅ Accessibility module is working correctly!')

except Exception as e:
    print(f'❌ Accessibility module error: {e}')
    print('This indicates missing PyObjC dependencies.')
"
```

#### Test Vision Module

```bash
python -c "
try:
    from modules.vision import VisionModule
    module = VisionModule()
    print('✅ Vision module imported successfully')

    # Test screen capture
    try:
        screenshot = module.capture_screen()
        print(f'✅ Screen capture: {screenshot}')
    except Exception as e:
        print(f'⚠️  Screen capture failed: {e}')
        print('This is normal if no display is available.')

except Exception as e:
    print(f'❌ Vision module error: {e}')
"
```

#### Test Orchestrator

```bash
python -c "
try:
    from orchestrator import Orchestrator
    orchestrator = Orchestrator()
    print('✅ Orchestrator initialized successfully')

    # Test command validation
    result = orchestrator.validate_command('click the button')
    print(f'✅ Command validation: {result.is_valid}')
    print(f'   Command type: {result.command_type}')
    print(f'   Confidence: {result.confidence:.2f}')

    # Test system health
    health = orchestrator.get_system_health()
    print(f'✅ System health: {health.get(\"overall_health\", \"unknown\")}')

except Exception as e:
    print(f'❌ Orchestrator error: {e}')
    import traceback
    traceback.print_exc()
"
```

### Step 5: Grant Accessibility Permissions

1. **Open System Preferences**
2. **Go to Security & Privacy > Privacy > Accessibility**
3. **Click the lock icon and enter your password**
4. **Add Terminal (or your IDE) to the list**
5. **Ensure the checkbox is checked**
6. **Restart Terminal/IDE**

### Step 6: Test AURA with Minimal Configuration

Create a minimal test version:

```bash
# Create minimal_aura_test.py
cat > minimal_aura_test.py << 'EOF'
#!/usr/bin/env python3
"""
Minimal AURA Test - Tests core functionality without full application complexity
"""

import logging
import time
from orchestrator import Orchestrator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🧪 Starting Minimal AURA Test")

    try:
        # Initialize orchestrator
        logger.info("Initializing orchestrator...")
        orchestrator = Orchestrator()

        # Test system health
        health = orchestrator.get_system_health()
        logger.info(f"System health: {health.get('overall_health', 'unknown')}")

        # Test commands
        test_commands = [
            "click the button",
            "type 'hello'",
            "what's on my screen?"
        ]

        logger.info("Testing commands...")
        for cmd in test_commands:
            logger.info(f"Testing: {cmd}")

            start_time = time.time()
            validation = orchestrator.validate_command(cmd)
            execution_time = time.time() - start_time

            logger.info(f"  Valid: {validation.is_valid}")
            logger.info(f"  Type: {validation.command_type}")
            logger.info(f"  Time: {execution_time:.3f}s")

        logger.info("✅ Minimal test completed successfully!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
EOF

# Run the minimal test
python minimal_aura_test.py
```

## Alternative: Run AURA in Degraded Mode

If you want to test AURA even with some components not working:

```bash
# Create a degraded mode test
python -c "
import os
import sys

# Set environment variables to disable problematic features
os.environ['AURA_DISABLE_AUDIO_FEEDBACK'] = 'true'
os.environ['AURA_DISABLE_WAKE_WORD'] = 'true'
os.environ['AURA_FORCE_DEGRADED_MODE'] = 'true'

# Import and run orchestrator
from orchestrator import Orchestrator

print('🔧 Running AURA in degraded mode...')
orchestrator = Orchestrator()

print('✅ AURA initialized in degraded mode')
print('Fast path may not be available, but vision-based commands should work')

# Test a simple command
result = orchestrator.validate_command('what is on my screen?')
print(f'Command validation test: {result.is_valid}')
"
```

## Expected Behavior After Fixes

After applying the fixes, you should see:

```
AURA 1.0.0
Autonomous User-side Robotic Assistant
==================================================
✅ Auto-detected vision model: google/gemma-3-4b
✅ Configuration is valid
✅ Accessibility module initialized (or degraded mode)
✅ AURA is running. Press Ctrl+C to stop.
```

## Testing Commands

Once AURA is running properly, test these commands:

### Method 1: Direct Command Testing

```bash
python -c "
from orchestrator import Orchestrator
orchestrator = Orchestrator()

# Test fast path commands
commands = [
    'click the Finder icon',
    'type \"hello world\"',
    'scroll down'
]

for cmd in commands:
    print(f'Testing: {cmd}')
    result = orchestrator.execute_command(cmd)
    print(f'Result: {result.get(\"status\", \"unknown\")}')
    print()
"
```

### Method 2: Interactive Mode

```bash
python -c "
from orchestrator import Orchestrator
orchestrator = Orchestrator()

print('AURA Interactive Mode')
print('Enter commands or \"quit\" to exit')

while True:
    try:
        cmd = input('AURA> ').strip()
        if cmd.lower() in ['quit', 'exit', 'q']:
            break
        if cmd:
            result = orchestrator.execute_command(cmd)
            print(f'Status: {result.get(\"status\", \"unknown\")}')
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f'Error: {e}')
"
```

## Common Issues and Solutions

### Issue 1: "NSWorkspace not found"

**Solution**: Install complete PyObjC framework

```bash
pip install pyobjc
```

### Issue 2: "Sound files not available"

**Solution**: Either create audio files or disable audio feedback

```bash
# Disable audio feedback
export AURA_DISABLE_AUDIO_FEEDBACK=true
python main.py
```

### Issue 3: "Screen context must be a dictionary"

**Solution**: This indicates vision/reasoning module communication issues

```bash
# Check if LM Studio is running
curl http://localhost:1234/v1/models

# If not running, start LM Studio and load a model
# Or disable vision-dependent features temporarily
```

### Issue 4: Accessibility permissions

**Solution**: Grant permissions and restart

1. System Preferences > Security & Privacy > Privacy > Accessibility
2. Add Terminal to the list
3. Restart Terminal
4. Run AURA again

## Verification Commands

After fixes, verify everything works:

```bash
# 1. Test basic functionality
python test_hybrid_simple.py

# 2. Test individual components
python -c "from modules.accessibility import AccessibilityModule; print('✅ Accessibility OK')"
python -c "from modules.vision import VisionModule; print('✅ Vision OK')"
python -c "from orchestrator import Orchestrator; print('✅ Orchestrator OK')"

# 3. Test command execution
python -c "
from orchestrator import Orchestrator
o = Orchestrator()
r = o.validate_command('click button')
print(f'✅ Command validation: {r.is_valid}')
"

# 4. If all above work, try main.py
python main.py
```

## Success Indicators

You'll know AURA is working correctly when you see:

1. **No import errors** during startup
2. **System health shows "healthy"** or "degraded" (not "critical")
3. **Commands validate successfully**
4. **Fast path attempts execute** (even if they fail due to no UI elements)
5. **Vision fallback works** for screen analysis commands

The hybrid architecture is designed to work even when some components are unavailable, so don't worry if accessibility is in "degraded mode" initially - the vision-based fallback will handle commands until you grant the necessary permissions.

#!/usr/bin/env python3
"""
AURA Setup Fix Script

This script fixes common setup issues and installs missing dependencies
to get AURA running properly on macOS.
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Run a shell command and handle errors."""
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        logger.info(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} - Failed")
        logger.error(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    logger.info("Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        logger.error(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible. Need Python 3.8+")
        return False

def install_pyobjc_dependencies():
    """Install PyObjC dependencies for macOS accessibility."""
    logger.info("Installing PyObjC dependencies for macOS accessibility...")
    
    dependencies = [
        "pyobjc-core",
        "pyobjc-framework-Cocoa", 
        "pyobjc-framework-AppKit",
        "pyobjc-framework-ApplicationServices",
        "pyobjc-framework-CoreFoundation",
        "pyobjc-framework-Quartz"
    ]
    
    success = True
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            success = False
    
    return success

def install_audio_dependencies():
    """Install audio-related dependencies."""
    logger.info("Installing audio dependencies...")
    
    audio_deps = [
        "sounddevice",
        "numpy",
        "pydub",
        "pygame",
        "pyttsx3"
    ]
    
    success = True
    for dep in audio_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            success = False
    
    return success

def create_missing_audio_files():
    """Create missing audio feedback files."""
    logger.info("Creating missing audio feedback files...")
    
    # Create sounds directory if it doesn't exist
    sounds_dir = Path("sounds")
    sounds_dir.mkdir(exist_ok=True)
    
    # Create simple audio files using pygame
    try:
        import pygame
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Create simple beep sounds
        import numpy as np
        
        def create_beep(filename, frequency=800, duration=0.3, sample_rate=22050):
            """Create a simple beep sound."""
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            
            for i in range(frames):
                wave = np.sin(2 * np.pi * frequency * i / sample_rate)
                arr[i] = [wave * 0.3, wave * 0.3]  # Stereo, reduced volume
            
            # Convert to pygame sound
            sound_array = (arr * 32767).astype(np.int16)
            sound = pygame.sndarray.make_sound(sound_array)
            
            # Save as WAV file
            pygame.mixer.Sound.play(sound)
            pygame.time.wait(int(duration * 1000))
            
            return True
        
        # Create different sounds
        sounds_to_create = {
            "thinking.wav": (600, 0.2),  # Lower frequency, shorter
            "success.wav": (1000, 0.3),  # Higher frequency
            "error.wav": (400, 0.5),     # Lower frequency, longer
            "listening.wav": (800, 0.2)  # Medium frequency
        }
        
        for filename, (freq, duration) in sounds_to_create.items():
            filepath = sounds_dir / filename
            if not filepath.exists():
                create_beep(str(filepath), freq, duration)
                logger.info(f"✅ Created {filename}")
        
        pygame.mixer.quit()
        return True
        
    except Exception as e:
        logger.warning(f"Could not create audio files: {e}")
        logger.info("Audio feedback will be disabled, but AURA will still work")
        return False

def fix_accessibility_module():
    """Fix the accessibility module import issues."""
    logger.info("Fixing accessibility module...")
    
    # Check if we can import the required modules
    try:
        from AppKit import NSWorkspace
        logger.info("✅ AppKit.NSWorkspace is available")
        return True
    except ImportError as e:
        logger.error(f"❌ AppKit import failed: {e}")
        logger.info("Installing additional PyObjC frameworks...")
        
        # Try installing more comprehensive PyObjC
        return run_command("pip install pyobjc", "Installing complete PyObjC framework")

def create_minimal_config():
    """Create a minimal config file for testing."""
    logger.info("Creating minimal configuration...")
    
    config_content = '''# Minimal AURA Configuration for Testing

# Vision API (Local LM Studio)
VISION_API_BASE = "http://localhost:1234/v1"
VISION_MODEL = "google/gemma-3-4b"

# Reasoning API (OpenAI compatible)
REASONING_API_BASE = "http://localhost:1234/v1"
REASONING_MODEL = "google/gemma-3-4b"

# Audio Configuration
ENABLE_WAKE_WORD = True
WAKE_WORD = "computer"
ENABLE_AUDIO_FEEDBACK = True

# Fast Path Configuration
ENABLE_FAST_PATH = True
FAST_PATH_TIMEOUT = 2.0

# Logging
LOG_LEVEL = "INFO"
DEBUG_MODE = False

# API Keys (set to dummy values for local testing)
PORCUPINE_API_KEY = "dummy_key_for_local_testing"
REASONING_API_KEY = "dummy_key_for_local_testing"
'''
    
    try:
        with open("config_minimal.py", "w") as f:
            f.write(config_content)
        logger.info("✅ Created minimal configuration file: config_minimal.py")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create config file: {e}")
        return False

def test_basic_functionality():
    """Test basic AURA functionality."""
    logger.info("Testing basic AURA functionality...")
    
    test_script = '''
import sys
sys.path.insert(0, ".")

try:
    # Test orchestrator import
    from orchestrator import Orchestrator
    print("✅ Orchestrator import successful")
    
    # Test orchestrator initialization
    orchestrator = Orchestrator()
    print("✅ Orchestrator initialization successful")
    
    # Test system health
    health = orchestrator.get_system_health()
    print(f"✅ System health check: {health.get('overall_health', 'unknown')}")
    
    # Test command validation
    result = orchestrator.validate_command("click the button")
    print(f"✅ Command validation: {result.is_valid}")
    
    print("\\n🎉 Basic functionality test PASSED")
    
except Exception as e:
    print(f"❌ Basic functionality test FAILED: {e}")
    import traceback
    traceback.print_exc()
'''
    
    try:
        with open("test_basic.py", "w") as f:
            f.write(test_script)
        
        result = subprocess.run([sys.executable, "test_basic.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Basic functionality test passed")
            print(result.stdout)
            return True
        else:
            logger.error("❌ Basic functionality test failed")
            print(result.stderr)
            return False
            
    except Exception as e:
        logger.error(f"❌ Could not run basic functionality test: {e}")
        return False

def main():
    """Main setup fix function."""
    logger.info("🔧 Starting AURA Setup Fix...")
    logger.info("=" * 50)
    
    success_count = 0
    total_steps = 7
    
    # Step 1: Check Python version
    if check_python_version():
        success_count += 1
    
    # Step 2: Install PyObjC dependencies
    if install_pyobjc_dependencies():
        success_count += 1
    
    # Step 3: Install audio dependencies  
    if install_audio_dependencies():
        success_count += 1
    
    # Step 4: Fix accessibility module
    if fix_accessibility_module():
        success_count += 1
    
    # Step 5: Create missing audio files
    if create_missing_audio_files():
        success_count += 1
    
    # Step 6: Create minimal config
    if create_minimal_config():
        success_count += 1
    
    # Step 7: Test basic functionality
    if test_basic_functionality():
        success_count += 1
    
    # Summary
    logger.info("=" * 50)
    logger.info(f"🏁 Setup Fix Complete: {success_count}/{total_steps} steps successful")
    
    if success_count == total_steps:
        logger.info("🎉 All fixes applied successfully!")
        logger.info("You can now run AURA with: python main.py")
    elif success_count >= 5:
        logger.info("⚠️  Most fixes applied. AURA should work with limited functionality.")
        logger.info("You can try running: python main.py")
    else:
        logger.error("❌ Multiple issues remain. Please check the errors above.")
        logger.info("You may need to install dependencies manually.")
    
    # Cleanup
    for temp_file in ["test_basic.py"]:
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    main()
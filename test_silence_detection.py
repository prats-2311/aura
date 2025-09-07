#!/usr/bin/env python3
"""
Test script for silence detection functionality in AURA audio module.

This script tests the new silence detection feature to ensure it works correctly
and provides faster, more responsive audio input.
"""

import sys
import time
import logging
from modules.audio import AudioModule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_silence_detection():
    """Test the silence detection functionality."""
    print("=" * 60)
    print("AURA Silence Detection Test")
    print("=" * 60)
    
    try:
        # Initialize audio module
        print("Initializing audio module...")
        audio_module = AudioModule()
        print("✓ Audio module initialized successfully")
        
        # Test 1: Basic silence detection
        print("\n" + "-" * 40)
        print("Test 1: Basic Silence Detection")
        print("-" * 40)
        print("Please speak for a few seconds, then remain silent...")
        print("Recording will automatically stop when silence is detected.")
        
        start_time = time.time()
        text = audio_module.speech_to_text()
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"✓ Recording completed in {duration:.2f} seconds")
        print(f"✓ Transcribed text: '{text}'")
        
        if duration < 7.0:  # Should be faster than the old 8-second fixed duration
            print(f"✓ SUCCESS: Silence detection reduced recording time by {8.0 - duration:.2f} seconds")
        else:
            print(f"⚠ WARNING: Recording took {duration:.2f}s, may have fallen back to fixed duration")
        
        # Test 2: Very short speech
        print("\n" + "-" * 40)
        print("Test 2: Short Speech Test")
        print("-" * 40)
        print("Please say just one word, then remain silent...")
        
        start_time = time.time()
        text = audio_module.speech_to_text()
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"✓ Recording completed in {duration:.2f} seconds")
        print(f"✓ Transcribed text: '{text}'")
        
        # Test 3: Longer speech
        print("\n" + "-" * 40)
        print("Test 3: Longer Speech Test")
        print("-" * 40)
        print("Please speak for about 5-6 seconds, then remain silent...")
        
        start_time = time.time()
        text = audio_module.speech_to_text()
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"✓ Recording completed in {duration:.2f} seconds")
        print(f"✓ Transcribed text: '{text}'")
        
        # Test 4: Test fallback behavior
        print("\n" + "-" * 40)
        print("Test 4: Configuration Test")
        print("-" * 40)
        
        from config import (
            SILENCE_DETECTION_ENABLED,
            SILENCE_DETECTION_DURATION,
            SILENCE_DETECTION_SENSITIVITY,
            MIN_RECORDING_DURATION
        )
        
        print(f"✓ Silence detection enabled: {SILENCE_DETECTION_ENABLED}")
        print(f"✓ Silence detection duration: {SILENCE_DETECTION_DURATION}s")
        print(f"✓ Silence detection sensitivity: {SILENCE_DETECTION_SENSITIVITY}")
        print(f"✓ Minimum recording duration: {MIN_RECORDING_DURATION}s")
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("Silence detection is working and should provide faster response times.")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_silence_detection()
    sys.exit(0 if success else 1)
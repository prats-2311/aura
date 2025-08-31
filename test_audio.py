#!/usr/bin/env python3
"""
Audio Testing Script for AURA

This script helps debug audio recording and transcription issues.
"""

import logging
import sys
from modules.audio import AudioModule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run audio tests."""
    print("AURA Audio Testing Script")
    print("=" * 40)
    
    try:
        # Initialize audio module
        print("Initializing audio module...")
        audio_module = AudioModule()
        print("✅ Audio module initialized successfully")
        
        # Test microphone
        print("\n1. Testing microphone...")
        mic_test = audio_module.test_microphone(duration=2.0)
        
        if mic_test["success"]:
            print(f"✅ Microphone test passed")
            print(f"   Duration: {mic_test['duration_recorded']:.2f}s")
            print(f"   RMS Volume: {mic_test['volume_rms']:.4f}")
            print(f"   Max Volume: {mic_test['volume_max']:.4f}")
        else:
            print(f"❌ Microphone test failed: {mic_test.get('error', 'Unknown error')}")
            return
        
        # Test speech-to-text
        print("\n2. Testing speech-to-text...")
        print("   Please say something clearly when prompted...")
        
        stt_test = audio_module.test_speech_to_text(duration=5.0)
        
        if stt_test["success"]:
            print(f"✅ Speech-to-text test passed")
            print(f"   Transcription: '{stt_test['transcription']}'")
        else:
            print(f"❌ Speech-to-text test failed: {stt_test.get('error', 'Unknown error')}")
            if stt_test["audio_stats"]:
                stats = stt_test["audio_stats"]
                print(f"   Audio stats: {stats['duration']:.2f}s, RMS: {stats['volume_rms']:.4f}")
        
        # Test wake word detection
        print("\n3. Testing wake word detection...")
        if audio_module.porcupine:
            print("   Say 'computer' to test wake word detection...")
            try:
                detected = audio_module.listen_for_wake_word(timeout=10.0)
                if detected:
                    print("✅ Wake word detection test passed")
                else:
                    print("❌ Wake word not detected within timeout")
            except Exception as e:
                print(f"❌ Wake word detection test failed: {e}")
        else:
            print("❌ Wake word detection not available (Porcupine not initialized)")
        
        print("\n" + "=" * 40)
        print("Audio testing completed!")
        
    except Exception as e:
        print(f"❌ Audio testing failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
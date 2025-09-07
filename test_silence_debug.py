#!/usr/bin/env python3
"""
Debug script for silence detection - shows real-time audio levels.
"""

import sys
import time
import logging
import numpy as np
import sounddevice as sd
from config import (
    AUDIO_SAMPLE_RATE,
    SILENCE_DETECTION_CHUNK_SIZE,
    SILENCE_DETECTION_SENSITIVITY
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_audio_levels():
    """Test and display real-time audio levels to help calibrate silence detection."""
    print("=" * 60)
    print("AURA Silence Detection Debug - Audio Level Monitor")
    print("=" * 60)
    print(f"Sample rate: {AUDIO_SAMPLE_RATE} Hz")
    print(f"Chunk size: {SILENCE_DETECTION_CHUNK_SIZE}s")
    print(f"Current silence threshold: {SILENCE_DETECTION_SENSITIVITY}")
    print()
    print("This will show real-time audio levels for 10 seconds.")
    print("Try speaking and then being silent to see the difference.")
    print("Press Ctrl+C to stop early.")
    print()
    
    chunk_size = int(SILENCE_DETECTION_CHUNK_SIZE * AUDIO_SAMPLE_RATE)
    max_chunks = int(10.0 / SILENCE_DETECTION_CHUNK_SIZE)  # 10 seconds
    
    try:
        with sd.InputStream(
            samplerate=AUDIO_SAMPLE_RATE,
            channels=1,
            dtype=np.float32,
            blocksize=chunk_size
        ) as stream:
            
            print("Recording started...")
            print("Time    | RMS Level | Status")
            print("-" * 35)
            
            for chunk_count in range(max_chunks):
                # Read audio chunk
                audio_chunk, overflowed = stream.read(chunk_size)
                
                if overflowed:
                    print("Audio overflow detected!")
                
                # Calculate RMS
                audio_chunk = audio_chunk.flatten()
                chunk_rms = np.sqrt(np.mean(audio_chunk ** 2))
                
                # Determine status
                is_silent = chunk_rms < SILENCE_DETECTION_SENSITIVITY
                status = "SILENT" if is_silent else "SOUND"
                
                # Display
                elapsed = (chunk_count + 1) * SILENCE_DETECTION_CHUNK_SIZE
                print(f"{elapsed:5.1f}s | {chunk_rms:8.4f} | {status}")
                
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nRecommendations:")
    print("- If you see mostly SOUND when silent, increase SILENCE_DETECTION_SENSITIVITY")
    print("- If you see mostly SILENT when speaking, decrease SILENCE_DETECTION_SENSITIVITY")
    print(f"- Current threshold: {SILENCE_DETECTION_SENSITIVITY}")
    print("- Typical speaking levels: 0.05-0.3")
    print("- Typical silence levels: 0.001-0.02")

if __name__ == "__main__":
    test_audio_levels()
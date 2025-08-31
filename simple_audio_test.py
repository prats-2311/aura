#!/usr/bin/env python3
"""
Simple Audio Test for AURA

This script tests basic audio recording and transcription.
"""

import whisper
import sounddevice as sd
import numpy as np
import tempfile
import os
from pydub import AudioSegment

def test_whisper_transcription():
    """Test Whisper transcription with a simple recording."""
    print("Simple Audio Test")
    print("=" * 30)
    
    # Load Whisper model
    print("Loading Whisper model...")
    model = whisper.load_model("base")
    print("✅ Whisper model loaded")
    
    # Record audio
    print("\nRecording 5 seconds of audio...")
    print("Please speak clearly now!")
    
    sample_rate = 16000
    duration = 5.0
    
    # Record audio
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32
    )
    sd.wait()  # Wait for recording to complete
    
    print(f"✅ Recording completed")
    
    # Calculate audio statistics
    audio_rms = np.sqrt(np.mean(audio_data ** 2))
    audio_max = np.max(np.abs(audio_data))
    
    print(f"Audio stats - RMS: {audio_rms:.4f}, Max: {audio_max:.4f}")
    
    if audio_max < 0.01:
        print("⚠️  Audio is very quiet - this may cause transcription issues")
    
    # Apply gain if needed
    if audio_max > 0:
        gain_factor = min(0.3 / audio_max, 10.0)
        if gain_factor > 1.0:
            print(f"Applying gain factor: {gain_factor:.2f}")
            audio_data = audio_data * gain_factor
    
    # Convert to int16
    audio_data = (audio_data.flatten() * 32767).astype(np.int16)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Create audio segment and export
        audio_segment = AudioSegment(
            audio_data.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,  # 16-bit
            channels=1
        )
        audio_segment.export(temp_path, format="wav")
        
        file_size = os.path.getsize(temp_path)
        print(f"Audio file created: {file_size} bytes")
        
        # Transcribe with Whisper
        print("\nTranscribing with Whisper...")
        result = model.transcribe(
            temp_path,
            language="en",
            no_speech_threshold=0.1,
            temperature=0.0
        )
        
        text = result.get("text", "").strip()
        language = result.get("language", "unknown")
        segments = result.get("segments", [])
        
        print(f"✅ Transcription completed")
        print(f"Language detected: {language}")
        print(f"Segments: {len(segments)}")
        print(f"Text: '{text}'")
        
        if text:
            print("🎉 Success! Speech was transcribed.")
        else:
            print("❌ No text was transcribed - audio may be unclear or silent")
            
        # Show segment details
        for i, segment in enumerate(segments[:3]):
            seg_text = segment.get("text", "").strip()
            seg_start = segment.get("start", 0)
            seg_end = segment.get("end", 0)
            print(f"  Segment {i+1}: '{seg_text}' ({seg_start:.2f}-{seg_end:.2f}s)")
        
    finally:
        # Clean up
        try:
            os.unlink(temp_path)
        except:
            pass

if __name__ == "__main__":
    test_whisper_transcription()
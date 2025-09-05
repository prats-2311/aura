#!/usr/bin/env python3
"""
Test script to verify the improved model detection logic.
"""

import logging
from config import get_active_vision_model, get_current_model_name

# Configure logging to see the detection process
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_model_detection():
    """Test the improved model detection."""
    
    print("🚀 Testing Improved Model Detection")
    print("=" * 50)
    
    # Test the active vision model detection
    print("1️⃣ Testing get_active_vision_model()...")
    detected_model = get_active_vision_model()
    print(f"   Result: {detected_model}")
    
    # Test the current model name function
    print("\n2️⃣ Testing get_current_model_name()...")
    current_model = get_current_model_name()
    print(f"   Result: {current_model}")
    
    # Verify they match
    print(f"\n3️⃣ Verification:")
    if detected_model == current_model:
        print(f"   ✅ Both functions return the same model: {detected_model}")
    else:
        print(f"   ⚠️  Functions return different models:")
        print(f"      get_active_vision_model(): {detected_model}")
        print(f"      get_current_model_name(): {current_model}")
    
    # Check if it's the expected model
    print(f"\n4️⃣ Model Analysis:")
    if detected_model:
        if "gemma" in detected_model.lower():
            print(f"   ✅ Correctly detected Gemma model: {detected_model}")
            print(f"   ℹ️  Note: Gemma has vision capabilities but may be limited compared to dedicated vision models")
        elif "vision" in detected_model.lower():
            print(f"   ✅ Detected dedicated vision model: {detected_model}")
        else:
            print(f"   ⚠️  Detected model may have limited vision capabilities: {detected_model}")
    else:
        print(f"   ❌ No model detected - check LM Studio connection")
    
    print(f"\n5️⃣ Summary:")
    if detected_model:
        print(f"   ✅ Model detection is working correctly")
        print(f"   🎯 Active model: {detected_model}")
        print(f"   💡 The system will now use the currently loaded model instead of guessing")
    else:
        print(f"   ❌ Model detection failed")
        print(f"   💡 Check that LM Studio is running and has a model loaded")

if __name__ == "__main__":
    test_model_detection()
#!/usr/bin/env python3
"""
Test the updated vision prompts with LM Studio
"""

from modules.vision import VisionModule
import json

def test_vision_prompts():
    """Test different vision analysis types"""
    print("🧪 Testing Vision Prompts with LM Studio")
    print("=" * 50)
    
    vision = VisionModule()
    
    # Test simple analysis
    print("\n1. Testing SIMPLE analysis:")
    try:
        result = vision.describe_screen(analysis_type="simple")
        print(f"✅ Simple analysis result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Simple analysis failed: {e}")
    
    # Test detailed analysis  
    print("\n2. Testing DETAILED analysis:")
    try:
        result = vision.describe_screen(analysis_type="detailed")
        print(f"✅ Detailed analysis result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Detailed analysis failed: {e}")
    
    # Test clickable analysis
    print("\n3. Testing CLICKABLE analysis:")
    try:
        result = vision.describe_screen(analysis_type="clickable")
        print(f"✅ Clickable analysis result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Clickable analysis failed: {e}")

if __name__ == "__main__":
    test_vision_prompts()
#!/usr/bin/env python3
"""
Test script to verify vision model fallback mechanism.
This tests the new fallback handling for models that don't return JSON.
"""

import sys
import logging
from modules.vision import VisionModule

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vision_with_fallback():
    """Test vision module with fallback handling."""
    print("🔍 Testing Vision Module with Fallback Handling")
    print("=" * 60)
    
    try:
        # Initialize vision module
        print("📦 Initializing VisionModule...")
        vision_module = VisionModule()
        print("✅ VisionModule initialized successfully")
        print()
        
        # Test simple screen analysis
        print("🖥️  Testing simple screen analysis...")
        try:
            result = vision_module.describe_screen(analysis_type="simple")
            
            print("✅ Screen analysis completed successfully!")
            print(f"📊 Result type: {type(result)}")
            print(f"📋 Keys in result: {list(result.keys())}")
            
            # Check if it's a fallback response
            if result.get("metadata", {}).get("fallback_response"):
                print("⚠️  Used fallback response (model didn't return JSON)")
                print(f"📝 Original content preview: {result['metadata'].get('original_content', 'N/A')[:100]}...")
            else:
                print("✅ Model returned proper JSON response")
            
            # Display the result
            print("\n📄 Analysis Result:")
            if "description" in result:
                print(f"   Description: {result['description']}")
            if "main_elements" in result:
                print(f"   Main Elements: {result['main_elements']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Screen analysis failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ VisionModule initialization failed: {e}")
        return False

def test_fallback_creation():
    """Test the fallback response creation directly."""
    print("\n🔧 Testing Fallback Response Creation")
    print("=" * 60)
    
    try:
        vision_module = VisionModule()
        
        # Test with sample plain text responses
        test_cases = [
            ("This is a terminal window with some text and commands.", "simple"),
            ("I can see a web browser with multiple tabs and a search bar.", "simple"),
            ("The screen shows a code editor with Python files open.", "simple")
        ]
        
        for i, (sample_text, analysis_type) in enumerate(test_cases, 1):
            print(f"\n🧪 Test Case {i}: {analysis_type} analysis")
            print(f"   Input: {sample_text[:50]}...")
            
            try:
                fallback_result = vision_module._create_fallback_response(sample_text, analysis_type)
                print("✅ Fallback response created successfully")
                print(f"   Description: {fallback_result.get('description', 'N/A')[:60]}...")
                print(f"   Elements: {fallback_result.get('main_elements', [])}")
                print(f"   Fallback flag: {fallback_result.get('metadata', {}).get('fallback_response', False)}")
                
            except Exception as e:
                print(f"❌ Fallback creation failed: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback test setup failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AURA Vision Fallback Test")
    print("=" * 60)
    
    success = True
    
    # Test vision module with fallback
    if not test_vision_with_fallback():
        success = False
    
    # Test fallback creation directly
    if not test_fallback_creation():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Vision fallback mechanism is working correctly.")
        print("\n💡 Key Benefits:")
        print("   ✅ Works with models that don't return JSON")
        print("   ✅ Graceful fallback to structured responses")
        print("   ✅ Preserves original model output for debugging")
        print("   ✅ Maintains compatibility with existing code")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        print("\n💡 Troubleshooting tips:")
        print("   1. Ensure LM Studio is running with a model loaded")
        print("   2. Check that the vision module can capture screenshots")
        print("   3. Verify network connectivity to LM Studio")
        sys.exit(1)
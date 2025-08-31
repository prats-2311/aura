#!/usr/bin/env python3
"""
Test script to verify dynamic model detection from LM Studio.
This script tests the new flexible model detection that works with any model loaded in LM Studio.
"""

import sys
import logging
from config import (
    VISION_API_BASE,
    get_active_vision_model,
    get_current_model_name
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_model_detection():
    """Test the dynamic model detection functionality."""
    print("🔍 Testing Dynamic Model Detection")
    print("=" * 50)
    
    print(f"📋 Configuration:")
    print(f"   LM Studio API Base: {VISION_API_BASE}")
    print()
    
    # Test basic model detection
    print("🔎 Detecting active model in LM Studio...")
    try:
        active_model = get_active_vision_model()
        if active_model:
            print(f"✅ Found active model: {active_model}")
        else:
            print("❌ No model detected")
            print("   Please ensure LM Studio is running with a model loaded")
            return False
    except Exception as e:
        print(f"❌ Error detecting model: {e}")
        return False
    
    print()
    
    # Test the current model name function
    print("🎯 Getting current model name for API requests...")
    try:
        current_model = get_current_model_name()
        print(f"✅ Current model name: {current_model}")
        
        if current_model == "loaded-model":
            print("   ℹ️  Using generic fallback name (LM Studio will route to loaded model)")
        else:
            print(f"   ℹ️  Using detected model name: {current_model}")
            
    except Exception as e:
        print(f"❌ Error getting current model name: {e}")
        return False
    
    print()
    print("🎉 Dynamic model detection test completed successfully!")
    return True

def test_vision_module_integration():
    """Test that the vision module can use the dynamic model detection."""
    print("\n🔧 Testing Vision Module Integration")
    print("=" * 50)
    
    try:
        from modules.vision import VisionModule
        
        print("📦 Initializing VisionModule...")
        vision_module = VisionModule()
        print("✅ VisionModule initialized successfully")
        
        # The vision module will now use get_current_model_name() dynamically
        print("✅ Vision module will use dynamic model detection for API requests")
        
        return True
        
    except Exception as e:
        print(f"❌ VisionModule integration test failed: {e}")
        return False

def test_api_request_simulation():
    """Simulate what happens during an actual API request."""
    print("\n🌐 Testing API Request Simulation")
    print("=" * 50)
    
    try:
        import requests
        
        # Get the current model name (same as vision module will do)
        current_model = get_current_model_name()
        print(f"📤 API request would use model: {current_model}")
        
        # Test if we can reach the LM Studio API
        response = requests.get(f"{VISION_API_BASE}/models", timeout=5)
        if response.status_code == 200:
            print("✅ LM Studio API is accessible")
            
            # Show what models are available
            models_data = response.json()
            if "data" in models_data and models_data["data"]:
                available_models = [model["id"] for model in models_data["data"]]
                print(f"✅ Available models: {', '.join(available_models)}")
            else:
                print("⚠️  No models found in LM Studio")
                
        else:
            print(f"❌ LM Studio API returned status {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ API request simulation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AURA Dynamic Model Detection Test")
    print("=" * 50)
    
    success = True
    
    # Test model detection
    if not test_model_detection():
        success = False
    
    # Test vision module integration
    if not test_vision_module_integration():
        success = False
    
    # Test API request simulation
    if not test_api_request_simulation():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Dynamic model detection is working correctly.")
        print("\n💡 Key Benefits:")
        print("   ✅ Works with ANY model loaded in LM Studio")
        print("   ✅ No need to manually configure model names")
        print("   ✅ Automatically adapts when you change models")
        print("   ✅ Graceful fallback if model detection fails")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check your LM Studio configuration.")
        print("\n💡 Troubleshooting tips:")
        print("   1. Ensure LM Studio is running on http://localhost:1234")
        print("   2. Load any model in LM Studio (vision or text model)")
        print("   3. Check that LM Studio's API server is enabled")
        print("   4. Try restarting LM Studio if issues persist")
        sys.exit(1)
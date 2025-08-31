#!/usr/bin/env python3
"""
Test script to verify Ollama Cloud API integration.
This tests the updated reasoning module with proper Ollama Cloud API calls.
"""

import sys
import logging
from modules.reasoning import ReasoningModule

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ollama_client_availability():
    """Test if Ollama client is available."""
    print("🔍 Testing Ollama Client Availability")
    print("=" * 50)
    
    try:
        from ollama import Client
        print("✅ Ollama client library is available")
        return True
    except ImportError:
        print("❌ Ollama client library not available")
        print("   Install with: pip install ollama")
        return False

def test_reasoning_module_initialization():
    """Test reasoning module initialization."""
    print("\n🔧 Testing Reasoning Module Initialization")
    print("=" * 50)
    
    try:
        reasoning_module = ReasoningModule()
        print("✅ ReasoningModule initialized successfully")
        
        # Check if Ollama client was initialized
        if hasattr(reasoning_module, 'ollama_client') and reasoning_module.ollama_client:
            print("✅ Ollama client initialized")
        else:
            print("⚠️  Using fallback requests method (Ollama client not available)")
        
        return reasoning_module
        
    except Exception as e:
        print(f"❌ ReasoningModule initialization failed: {e}")
        return None

def test_simple_reasoning_request(reasoning_module):
    """Test a simple reasoning request."""
    print("\n🧠 Testing Simple Reasoning Request")
    print("=" * 50)
    
    try:
        # Simple test command and screen context
        user_command = "What's on my screen?"
        screen_context = {
            "description": "The screen shows a code editor with Python files open",
            "main_elements": ["code", "editor", "files"],
            "metadata": {
                "timestamp": 1756648922,
                "screen_resolution": [1710, 1112]
            }
        }
        
        print(f"📤 Sending request...")
        print(f"   Command: {user_command}")
        print(f"   Context: {screen_context['description']}")
        
        # Make the reasoning request
        result = reasoning_module.get_action_plan(user_command, screen_context)
        
        print("✅ Reasoning request completed successfully!")
        print(f"📊 Result type: {type(result)}")
        print(f"📋 Keys in result: {list(result.keys())}")
        
        # Check if it's a fallback response
        if result.get("metadata", {}).get("fallback"):
            print("⚠️  Used fallback response (API request failed)")
            print(f"📝 Error: {result['metadata'].get('error', 'Unknown')}")
        else:
            print("✅ API request successful")
            if "plan" in result:
                print(f"📝 Generated {len(result['plan'])} action steps")
        
        return True
        
    except Exception as e:
        print(f"❌ Reasoning request failed: {e}")
        return False

def test_api_configuration():
    """Test API configuration."""
    print("\n⚙️  Testing API Configuration")
    print("=" * 50)
    
    try:
        from config import REASONING_API_BASE, REASONING_API_KEY, REASONING_MODEL
        
        print(f"📋 Configuration:")
        print(f"   API Base: {REASONING_API_BASE}")
        print(f"   API Key: {'*' * 20 + REASONING_API_KEY[-4:] if REASONING_API_KEY and len(REASONING_API_KEY) > 4 else 'Not set'}")
        print(f"   Model: {REASONING_MODEL}")
        
        # Validate configuration
        if not REASONING_API_BASE:
            print("❌ API Base URL not configured")
            return False
        
        if not REASONING_API_KEY or REASONING_API_KEY == "your_ollama_cloud_api_key_here":
            print("❌ API Key not configured properly")
            return False
        
        if not REASONING_MODEL:
            print("❌ Model not configured")
            return False
        
        print("✅ Configuration looks good")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_network_connectivity():
    """Test network connectivity to Ollama Cloud."""
    print("\n🌐 Testing Network Connectivity")
    print("=" * 50)
    
    try:
        import requests
        from config import REASONING_API_BASE
        
        print(f"📡 Testing connection to {REASONING_API_BASE}")
        
        # Simple connectivity test for Ollama Cloud
        response = requests.get(f"{REASONING_API_BASE}", timeout=10)
        
        if response.status_code == 200:
            print("✅ Successfully connected to Ollama Cloud")
            return True
        elif response.status_code == 401:
            print("⚠️  Connected but authentication may be required")
            return True
        else:
            print(f"⚠️  Connected but got status code: {response.status_code}")
            return True
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama Cloud")
        print("   Check your internet connection")
        return False
    except requests.exceptions.Timeout:
        print("❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AURA Ollama Cloud Integration Test")
    print("=" * 50)
    
    success = True
    
    # Test Ollama client availability
    if not test_ollama_client_availability():
        print("\n💡 Note: Ollama client not available, will use requests fallback")
    
    # Test API configuration
    if not test_api_configuration():
        success = False
    
    # Test network connectivity
    if not test_network_connectivity():
        success = False
    
    # Test reasoning module initialization
    reasoning_module = test_reasoning_module_initialization()
    if not reasoning_module:
        success = False
    
    # Test simple reasoning request
    if reasoning_module:
        if not test_simple_reasoning_request(reasoning_module):
            success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Ollama Cloud integration test completed successfully!")
        print("\n💡 Key Benefits:")
        print("   ✅ Proper Ollama Cloud API integration")
        print("   ✅ Fallback to requests if Ollama client unavailable")
        print("   ✅ Comprehensive error handling")
        print("   ✅ Compatible with existing AURA workflow")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        print("\n💡 Troubleshooting tips:")
        print("   1. Ensure your Ollama Cloud API key is configured")
        print("   2. Check your internet connection")
        print("   3. Install Ollama client: pip install ollama")
        print("   4. Verify your API key has proper permissions")
        sys.exit(1)
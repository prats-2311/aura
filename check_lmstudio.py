#!/usr/bin/env python3
"""
Simple LM Studio connectivity and configuration checker.
This script helps verify that LM Studio is properly set up for AURA.
"""

import requests
import json

def check_lmstudio_status():
    """Check LM Studio status and configuration."""
    print("🔍 LM Studio Configuration Checker")
    print("=" * 50)
    
    api_base = "http://localhost:1234/v1"
    
    # Step 1: Check if LM Studio is running
    print("1️⃣ Checking if LM Studio is running...")
    try:
        response = requests.get(f"{api_base}/models", timeout=5)
        print("✅ LM Studio is running and accessible")
    except requests.exceptions.ConnectionError:
        print("❌ LM Studio is not running or not accessible")
        print("\n💡 To fix this:")
        print("   1. Start LM Studio application")
        print("   2. Go to 'Local Server' tab")
        print("   3. Click 'Start Server' (should show port 1234)")
        print("   4. Make sure 'CORS' is enabled if needed")
        return False
    except Exception as e:
        print(f"❌ Error connecting to LM Studio: {e}")
        return False
    
    # Step 2: Check if models are loaded
    print("\n2️⃣ Checking loaded models...")
    try:
        if response.status_code == 200:
            models_data = response.json()
            
            if "data" in models_data and models_data["data"]:
                models = [model["id"] for model in models_data["data"]]
                print(f"✅ Found {len(models)} loaded model(s):")
                for i, model in enumerate(models, 1):
                    print(f"   {i}. {model}")
                
                # Show which model AURA would use
                active_model = models[0]  # LM Studio typically loads one at a time
                print(f"\n🎯 AURA would use: {active_model}")
                
            else:
                print("❌ No models are loaded in LM Studio")
                print("\n💡 To fix this:")
                print("   1. In LM Studio, go to 'My Models' tab")
                print("   2. Download a model if you don't have any")
                print("   3. Click 'Load' next to a model")
                print("   4. Wait for the model to fully load")
                return False
                
        else:
            print(f"❌ LM Studio API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False
    
    # Step 3: Test a simple API call
    print("\n3️⃣ Testing API functionality...")
    try:
        test_payload = {
            "model": active_model,
            "messages": [{"role": "user", "content": "Hello, can you respond with just 'OK'?"}],
            "max_tokens": 10,
            "temperature": 0.1
        }
        
        response = requests.post(f"{api_base}/chat/completions", 
                               json=test_payload, 
                               timeout=30)
        
        if response.status_code == 200:
            print("✅ API test successful - LM Studio is working correctly")
            
            # Show the response
            result = response.json()
            if "choices" in result and result["choices"]:
                content = result["choices"][0]["message"]["content"]
                print(f"   Model response: '{content.strip()}'")
            
        else:
            print(f"❌ API test failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False
    
    # Step 4: Check model capabilities
    print("\n4️⃣ Analyzing model capabilities...")
    model_name_lower = active_model.lower()
    
    # Check if it's likely a vision model
    vision_keywords = ['llava', 'vision', 'multimodal', 'bakllava', 'moondream', 
                      'cogvlm', 'internvl', 'gpt-4v', 'claude-3', 'gemini-pro-vision']
    
    is_vision_model = any(keyword in model_name_lower for keyword in vision_keywords)
    
    if is_vision_model:
        print("✅ This appears to be a vision-capable model")
        print("   🎯 Perfect for AURA's screen analysis features")
    else:
        print("ℹ️  This appears to be a text-only model")
        print("   🎯 Will work for AURA's reasoning, but vision tasks may be limited")
        print("   💡 Consider loading a vision model (LLaVA, Moondream) for full functionality")
    
    print("\n🎉 LM Studio is properly configured for AURA!")
    return True

def show_recommended_models():
    """Show recommended models for different use cases."""
    print("\n📋 Recommended Models for AURA")
    print("=" * 50)
    
    print("\n🎯 For Full Functionality (Vision + Text):")
    print("   • LLaVA v1.6 Mistral 7B - Excellent vision capabilities")
    print("   • LLaVA v1.6 Vicuna 7B - Alternative LLaVA variant")
    print("   • Moondream2 - Lightweight and fast")
    print("   • BakLLaVA - Good balance of speed and capability")
    
    print("\n💬 For Text-Only Tasks:")
    print("   • Llama 3.1 8B Instruct - Great reasoning")
    print("   • Gemma 2 9B IT - Fast and efficient")
    print("   • Mistral 7B Instruct - Balanced performance")
    print("   • Qwen 2.5 7B Instruct - Strong reasoning")
    
    print("\n⚡ Performance Tips:")
    print("   • Smaller models (7B) = Faster responses")
    print("   • Larger models (13B+) = Better accuracy")
    print("   • Vision models = Slower but can see your screen")
    print("   • Text models = Faster but limited to reasoning only")

if __name__ == "__main__":
    success = check_lmstudio_status()
    
    if not success:
        show_recommended_models()
        print("\n" + "=" * 50)
        print("❌ LM Studio setup incomplete")
        print("Please fix the issues above and run this script again")
    else:
        print("\n" + "=" * 50)
        print("✅ LM Studio is ready for AURA!")
        print("You can now run: python test_dynamic_model.py")
        print("Or start AURA with: python main.py")
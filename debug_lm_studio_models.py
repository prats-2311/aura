#!/usr/bin/env python3
"""
Debug script to check what models LM Studio is reporting and why the detection isn't working.
"""

import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_lm_studio_models():
    """Debug LM Studio model detection."""
    
    VISION_API_BASE = "http://localhost:1234/v1"
    
    # Known embedding model patterns to exclude
    EMBEDDING_MODEL_PATTERNS = [
        'embedding', 'embed', 'nomic-embed', 'text-embedding',
        'sentence-transformer', 'bge-', 'e5-', 'gte-'
    ]
    
    # Known vision model patterns to prioritize
    VISION_MODEL_PATTERNS = [
        'vision', 'llava', 'gpt-4v', 'claude-3', 'gemini-pro-vision',
        'minicpm-v', 'qwen-vl', 'internvl', 'cogvlm', 'moondream',
        'bakllava', 'yi-vl', 'deepseek-vl', 'gemma'  # Added gemma
    ]
    
    try:
        print("🔍 Checking LM Studio models...")
        print(f"📡 Querying: {VISION_API_BASE}/models")
        
        # Query LM Studio for available models
        response = requests.get(f"{VISION_API_BASE}/models", timeout=5)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            models_data = response.json()
            print(f"📋 Raw response: {json.dumps(models_data, indent=2)}")
            
            # LM Studio typically returns models in this format
            if "data" in models_data and models_data["data"]:
                available_models = [model["id"] for model in models_data["data"]]
                print(f"📝 Available models: {available_models}")
                
                # Check each model
                for model in available_models:
                    model_lower = model.lower()
                    print(f"\n🔍 Analyzing model: {model}")
                    
                    # Check if it's an embedding model
                    is_embedding = any(pattern in model_lower for pattern in EMBEDDING_MODEL_PATTERNS)
                    print(f"   📊 Is embedding model: {is_embedding}")
                    
                    if is_embedding:
                        print(f"   ⏭️  Skipping embedding model: {model}")
                        continue
                    
                    # Check if it's a known vision model
                    is_vision = any(pattern in model_lower for pattern in VISION_MODEL_PATTERNS)
                    print(f"   👁️  Is known vision model: {is_vision}")
                    
                    if is_vision:
                        print(f"   ✅ Would select vision model: {model}")
                        return model
                    else:
                        print(f"   ⚠️  Not recognized as vision model: {model}")
                
                # If we get here, no known vision models were found
                non_embedding_models = [m for m in available_models 
                                      if not any(pattern in m.lower() for pattern in EMBEDDING_MODEL_PATTERNS)]
                
                if non_embedding_models:
                    selected = non_embedding_models[0]
                    print(f"\n⚠️  No known vision models found. Would use first non-embedding: {selected}")
                    return selected
                else:
                    print(f"\n❌ No suitable models found!")
                    return None
                    
            else:
                print("❌ No models found in LM Studio response")
                return None
                
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to LM Studio. Make sure it's running on http://localhost:1234")
    except requests.exceptions.Timeout:
        print("⏰ LM Studio connection timeout")
    except Exception as e:
        print(f"💥 Error detecting model: {e}")
    
    return None

def check_currently_loaded_model():
    """Check what model is currently loaded by making a test request."""
    
    VISION_API_BASE = "http://localhost:1234/v1"
    
    try:
        print("\n🎯 Checking currently loaded model...")
        
        # Make a simple completion request to see what model responds
        test_payload = {
            "model": "any-model-name",  # LM Studio often ignores this and uses loaded model
            "messages": [
                {"role": "user", "content": "What model are you?"}
            ],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        response = requests.post(
            f"{VISION_API_BASE}/chat/completions",
            json=test_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test request successful")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            
            # Check if the response contains model information
            if 'model' in result:
                print(f"🎯 Currently loaded model: {result['model']}")
                return result['model']
            else:
                print("ℹ️  No model info in response, but request succeeded")
                return "loaded-model"
        else:
            print(f"❌ Test request failed: {response.status_code}")
            print(f"📋 Error response: {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 Error checking loaded model: {e}")
        return None

if __name__ == "__main__":
    print("🚀 LM Studio Model Detection Debug")
    print("=" * 50)
    
    # Check available models
    detected_model = debug_lm_studio_models()
    
    # Check currently loaded model
    loaded_model = check_currently_loaded_model()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    print(f"🔍 Detected model from /models endpoint: {detected_model}")
    print(f"🎯 Currently loaded model: {loaded_model}")
    
    if detected_model:
        print(f"✅ Model detection working")
    else:
        print(f"❌ Model detection failed")
        
    print("\n💡 RECOMMENDATIONS:")
    if not detected_model:
        print("1. Make sure LM Studio is running")
        print("2. Make sure a model is loaded in LM Studio")
        print("3. Check that LM Studio is accessible at http://localhost:1234")
    elif "gemma" in detected_model.lower():
        print("1. Gemma models may have limited vision capabilities")
        print("2. Consider loading a dedicated vision model like LLaVA or MiniCPM-V")
        print("3. For now, the system will use Gemma but vision features may be limited")
    else:
        print("1. Model detection is working correctly")
        print("2. The detected model should work for vision tasks")
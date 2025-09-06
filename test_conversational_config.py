#!/usr/bin/env python3
"""
Test script for conversational enhancement configuration parameters.

This script tests that all new configuration parameters are properly
set and within valid ranges.
"""

import sys
from pathlib import Path

def test_deferred_action_config():
    """Test deferred action configuration parameters."""
    print("🔍 Testing deferred action configuration...")
    
    try:
        from config import (
            DEFERRED_ACTION_TIMEOUT, DEFERRED_ACTION_MAX_TIMEOUT, DEFERRED_ACTION_MIN_TIMEOUT,
            MOUSE_LISTENER_SENSITIVITY, MOUSE_LISTENER_DOUBLE_CLICK_TIME,
            DEFERRED_ACTION_AUDIO_CUES, DEFERRED_ACTION_VISUAL_FEEDBACK,
            DEFERRED_ACTION_RETRY_ATTEMPTS
        )
        
        # Test timeout values
        assert DEFERRED_ACTION_MIN_TIMEOUT <= DEFERRED_ACTION_TIMEOUT <= DEFERRED_ACTION_MAX_TIMEOUT, \
            f"DEFERRED_ACTION_TIMEOUT ({DEFERRED_ACTION_TIMEOUT}) not within valid range"
        
        # Test sensitivity
        assert 0.1 <= MOUSE_LISTENER_SENSITIVITY <= 2.0, \
            f"MOUSE_LISTENER_SENSITIVITY ({MOUSE_LISTENER_SENSITIVITY}) not within valid range"
        
        # Test double-click time
        assert 0.1 <= MOUSE_LISTENER_DOUBLE_CLICK_TIME <= 2.0, \
            f"MOUSE_LISTENER_DOUBLE_CLICK_TIME ({MOUSE_LISTENER_DOUBLE_CLICK_TIME}) not within valid range"
        
        # Test boolean flags
        assert isinstance(DEFERRED_ACTION_AUDIO_CUES, bool), "DEFERRED_ACTION_AUDIO_CUES must be boolean"
        assert isinstance(DEFERRED_ACTION_VISUAL_FEEDBACK, bool), "DEFERRED_ACTION_VISUAL_FEEDBACK must be boolean"
        
        # Test retry attempts
        assert 1 <= DEFERRED_ACTION_RETRY_ATTEMPTS <= 10, \
            f"DEFERRED_ACTION_RETRY_ATTEMPTS ({DEFERRED_ACTION_RETRY_ATTEMPTS}) not within valid range"
        
        print("✅ Deferred action configuration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Deferred action configuration test failed: {e}")
        return False

def test_conversational_config():
    """Test conversational configuration parameters."""
    print("\n🔍 Testing conversational configuration...")
    
    try:
        from config import (
            CONVERSATION_CONTEXT_SIZE, CONVERSATION_MAX_CONTEXT_SIZE,
            CONVERSATION_PERSONALITY, CONVERSATION_RESPONSE_MAX_LENGTH,
            CONVERSATION_TIMEOUT, ENABLE_FOLLOW_UP_SUGGESTIONS,
            CONVERSATION_MEMORY_ENABLED
        )
        
        # Test context size
        assert 1 <= CONVERSATION_CONTEXT_SIZE <= CONVERSATION_MAX_CONTEXT_SIZE, \
            f"CONVERSATION_CONTEXT_SIZE ({CONVERSATION_CONTEXT_SIZE}) not within valid range"
        
        # Test response length
        assert 50 <= CONVERSATION_RESPONSE_MAX_LENGTH <= 2000, \
            f"CONVERSATION_RESPONSE_MAX_LENGTH ({CONVERSATION_RESPONSE_MAX_LENGTH}) not within valid range"
        
        # Test timeout
        assert 5.0 <= CONVERSATION_TIMEOUT <= 120.0, \
            f"CONVERSATION_TIMEOUT ({CONVERSATION_TIMEOUT}) not within valid range"
        
        # Test string values
        assert isinstance(CONVERSATION_PERSONALITY, str) and CONVERSATION_PERSONALITY, \
            "CONVERSATION_PERSONALITY must be non-empty string"
        
        # Test boolean flags
        assert isinstance(ENABLE_FOLLOW_UP_SUGGESTIONS, bool), "ENABLE_FOLLOW_UP_SUGGESTIONS must be boolean"
        assert isinstance(CONVERSATION_MEMORY_ENABLED, bool), "CONVERSATION_MEMORY_ENABLED must be boolean"
        
        print("✅ Conversational configuration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Conversational configuration test failed: {e}")
        return False

def test_intent_recognition_config():
    """Test intent recognition configuration parameters."""
    print("\n🔍 Testing intent recognition configuration...")
    
    try:
        from config import (
            INTENT_RECOGNITION_ENABLED, INTENT_FALLBACK_TO_GUI,
            INTENT_CONFIDENCE_THRESHOLD, INTENT_RECOGNITION_TIMEOUT,
            INTENT_CLASSIFICATION_RETRIES, INTENT_CACHE_ENABLED,
            INTENT_CACHE_TTL
        )
        
        # Test confidence threshold
        assert 0.1 <= INTENT_CONFIDENCE_THRESHOLD <= 1.0, \
            f"INTENT_CONFIDENCE_THRESHOLD ({INTENT_CONFIDENCE_THRESHOLD}) not within valid range"
        
        # Test timeout
        assert 5.0 <= INTENT_RECOGNITION_TIMEOUT <= 60.0, \
            f"INTENT_RECOGNITION_TIMEOUT ({INTENT_RECOGNITION_TIMEOUT}) not within valid range"
        
        # Test retries
        assert 0 <= INTENT_CLASSIFICATION_RETRIES <= 5, \
            f"INTENT_CLASSIFICATION_RETRIES ({INTENT_CLASSIFICATION_RETRIES}) not within valid range"
        
        # Test cache TTL
        assert 60 <= INTENT_CACHE_TTL <= 3600, \
            f"INTENT_CACHE_TTL ({INTENT_CACHE_TTL}) not within recommended range"
        
        # Test boolean flags
        assert isinstance(INTENT_RECOGNITION_ENABLED, bool), "INTENT_RECOGNITION_ENABLED must be boolean"
        assert isinstance(INTENT_FALLBACK_TO_GUI, bool), "INTENT_FALLBACK_TO_GUI must be boolean"
        assert isinstance(INTENT_CACHE_ENABLED, bool), "INTENT_CACHE_ENABLED must be boolean"
        
        print("✅ Intent recognition configuration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Intent recognition configuration test failed: {e}")
        return False

def test_content_generation_config():
    """Test content generation configuration parameters."""
    print("\n🔍 Testing content generation configuration...")
    
    try:
        from config import (
            CODE_GENERATION_MAX_LENGTH, CODE_GENERATION_TIMEOUT,
            TEXT_GENERATION_MAX_LENGTH, CONTENT_VALIDATION_ENABLED,
            CONTENT_SANITIZATION_ENABLED
        )
        
        # Test max lengths
        assert 100 <= CODE_GENERATION_MAX_LENGTH <= 10000, \
            f"CODE_GENERATION_MAX_LENGTH ({CODE_GENERATION_MAX_LENGTH}) not within valid range"
        
        assert 50 <= TEXT_GENERATION_MAX_LENGTH <= 5000, \
            f"TEXT_GENERATION_MAX_LENGTH ({TEXT_GENERATION_MAX_LENGTH}) not within valid range"
        
        # Test timeout
        assert 10.0 <= CODE_GENERATION_TIMEOUT <= 180.0, \
            f"CODE_GENERATION_TIMEOUT ({CODE_GENERATION_TIMEOUT}) not within valid range"
        
        # Test boolean flags
        assert isinstance(CONTENT_VALIDATION_ENABLED, bool), "CONTENT_VALIDATION_ENABLED must be boolean"
        assert isinstance(CONTENT_SANITIZATION_ENABLED, bool), "CONTENT_SANITIZATION_ENABLED must be boolean"
        
        print("✅ Content generation configuration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Content generation configuration test failed: {e}")
        return False

def test_prompt_templates():
    """Test that prompt templates are properly configured."""
    print("\n🔍 Testing prompt templates...")
    
    try:
        from config import (
            INTENT_RECOGNITION_PROMPT, CONVERSATIONAL_PROMPT, CODE_GENERATION_PROMPT
        )
        
        # Test that prompts exist and are strings
        assert isinstance(INTENT_RECOGNITION_PROMPT, str) and len(INTENT_RECOGNITION_PROMPT.strip()) > 50, \
            "INTENT_RECOGNITION_PROMPT must be a substantial string"
        
        assert isinstance(CONVERSATIONAL_PROMPT, str) and len(CONVERSATIONAL_PROMPT.strip()) > 50, \
            "CONVERSATIONAL_PROMPT must be a substantial string"
        
        assert isinstance(CODE_GENERATION_PROMPT, str) and len(CODE_GENERATION_PROMPT.strip()) > 50, \
            "CODE_GENERATION_PROMPT must be a substantial string"
        
        # Test for required placeholders
        assert '{command}' in INTENT_RECOGNITION_PROMPT, \
            "INTENT_RECOGNITION_PROMPT must contain '{command}' placeholder"
        
        assert '{query}' in CONVERSATIONAL_PROMPT, \
            "CONVERSATIONAL_PROMPT must contain '{query}' placeholder"
        
        assert '{request}' in CODE_GENERATION_PROMPT and '{context}' in CODE_GENERATION_PROMPT, \
            "CODE_GENERATION_PROMPT must contain '{request}' and '{context}' placeholders"
        
        print("✅ Prompt template tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Prompt template test failed: {e}")
        return False

def test_mouse_listener_config():
    """Test mouse listener configuration parameters."""
    print("\n🔍 Testing mouse listener configuration...")
    
    try:
        from config import (
            MOUSE_LISTENER_THREAD_TIMEOUT, MOUSE_LISTENER_CLEANUP_DELAY,
            MOUSE_LISTENER_ERROR_RECOVERY, GLOBAL_MOUSE_EVENTS_ENABLED
        )
        
        # Test timeout values
        assert MOUSE_LISTENER_THREAD_TIMEOUT > 0, \
            f"MOUSE_LISTENER_THREAD_TIMEOUT ({MOUSE_LISTENER_THREAD_TIMEOUT}) must be positive"
        
        assert MOUSE_LISTENER_CLEANUP_DELAY > 0, \
            f"MOUSE_LISTENER_CLEANUP_DELAY ({MOUSE_LISTENER_CLEANUP_DELAY}) must be positive"
        
        # Test boolean flags
        assert isinstance(MOUSE_LISTENER_ERROR_RECOVERY, bool), "MOUSE_LISTENER_ERROR_RECOVERY must be boolean"
        assert isinstance(GLOBAL_MOUSE_EVENTS_ENABLED, bool), "GLOBAL_MOUSE_EVENTS_ENABLED must be boolean"
        
        print("✅ Mouse listener configuration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Mouse listener configuration test failed: {e}")
        return False

def test_pynput_dependency():
    """Test that pynput dependency is properly installed and functional."""
    print("\n🔍 Testing pynput dependency...")
    
    try:
        import pynput
        from pynput import mouse, keyboard
        
        # Test that we can create listeners (but don't start them)
        def dummy_callback(*args):
            pass
        
        mouse_listener = mouse.Listener(on_click=dummy_callback)
        keyboard_listener = keyboard.Listener(on_press=dummy_callback)
        
        print("✅ pynput dependency tests passed")
        return True
        
    except ImportError as e:
        print(f"❌ pynput dependency test failed: {e}")
        print("   Install with: pip install pynput>=1.7.6")
        return False
    except Exception as e:
        print(f"❌ pynput functionality test failed: {e}")
        return False

def main():
    """Run all configuration tests."""
    print("🧪 AURA Conversational Enhancement Configuration Tests")
    print("=" * 60)
    
    tests = [
        ("Deferred Action Config", test_deferred_action_config),
        ("Conversational Config", test_conversational_config),
        ("Intent Recognition Config", test_intent_recognition_config),
        ("Content Generation Config", test_content_generation_config),
        ("Prompt Templates", test_prompt_templates),
        ("Mouse Listener Config", test_mouse_listener_config),
        ("pynput Dependency", test_pynput_dependency),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All configuration tests passed!")
        print("✅ Conversational enhancement configuration is properly set up")
        return True
    else:
        print(f"\n⚠️  {total - passed} configuration tests failed")
        print("Please check the configuration in config.py")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
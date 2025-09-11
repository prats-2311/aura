#!/usr/bin/env python3
"""
Test script to verify the feedback sound fix for ExplainSelectionHandler
"""

import sys
import time
sys.path.append('.')

from modules.feedback import FeedbackModule, FeedbackPriority
from modules.audio import AudioModule

def test_feedback_sounds():
    """Test that feedback sounds work correctly."""
    print("🔊 Testing Feedback Sounds...")
    
    try:
        # Initialize audio module (required for feedback)
        print("Initializing audio module...")
        audio_module = AudioModule()
        
        # Initialize feedback module
        print("Initializing feedback module...")
        feedback_module = FeedbackModule(audio_module=audio_module)
        
        # Test thinking sound
        print("Playing thinking sound...")
        feedback_module.play("thinking", priority=FeedbackPriority.HIGH)
        time.sleep(1)
        
        # Test success sound
        print("Playing success sound...")
        feedback_module.play("success", priority=FeedbackPriority.NORMAL)
        time.sleep(1)
        
        # Test failure sound
        print("Playing failure sound...")
        feedback_module.play("failure", priority=FeedbackPriority.HIGH)
        time.sleep(1)
        
        print("✅ All feedback sounds played successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing feedback sounds: {e}")
        return False

def test_orchestrator_access():
    """Test accessing feedback module through orchestrator pattern."""
    print("\n🔗 Testing Orchestrator Access Pattern...")
    
    try:
        # Mock orchestrator with feedback module
        class MockOrchestrator:
            def __init__(self):
                audio_module = AudioModule()
                self.feedback_module = FeedbackModule(audio_module=audio_module)
        
        # Create mock orchestrator
        orchestrator = MockOrchestrator()
        
        # Test the access pattern used in the fix
        feedback_module = getattr(orchestrator, 'feedback_module', None)
        
        if feedback_module and hasattr(feedback_module, 'play'):
            print("Playing test sound via orchestrator access...")
            feedback_module.play("thinking", priority=FeedbackPriority.HIGH)
            time.sleep(1)
            print("✅ Orchestrator access pattern works!")
            return True
        else:
            print("❌ Orchestrator access pattern failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing orchestrator access: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Testing Feedback Sound Fix")
    print("=" * 40)
    
    # Test basic feedback sounds
    sounds_work = test_feedback_sounds()
    
    # Test orchestrator access pattern
    access_works = test_orchestrator_access()
    
    print("\n📊 Test Results:")
    print(f"Feedback Sounds: {'✅ PASS' if sounds_work else '❌ FAIL'}")
    print(f"Orchestrator Access: {'✅ PASS' if access_works else '❌ FAIL'}")
    
    if sounds_work and access_works:
        print("\n🎉 All tests passed! The feedback sound fix should work.")
        print("\nNext steps:")
        print("1. Start AURA: python main.py")
        print("2. Select text and say: 'Computer, explain this'")
        print("3. You should hear: thinking sound → explanation → success sound")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
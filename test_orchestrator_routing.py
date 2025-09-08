#!/usr/bin/env python3
"""
Test Orchestrator Routing

This script tests that the orchestrator properly routes question_answering
intents to the QuestionAnsweringHandler instead of GUIHandler.
"""

import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_handler_initialization():
    """Test that the QuestionAnsweringHandler is properly initialized."""
    
    print("🧪 Testing Orchestrator Handler Initialization")
    print("=" * 60)
    
    try:
        from orchestrator import Orchestrator
        
        print("1️⃣ Creating orchestrator instance...")
        orchestrator = Orchestrator()
        
        print("2️⃣ Checking handler initialization...")
        
        # Check if QuestionAnsweringHandler is initialized
        if hasattr(orchestrator, 'question_answering_handler'):
            if orchestrator.question_answering_handler is not None:
                print(f"✅ QuestionAnsweringHandler initialized: {orchestrator.question_answering_handler.__class__.__name__}")
            else:
                print("❌ QuestionAnsweringHandler is None")
                return False
        else:
            print("❌ QuestionAnsweringHandler attribute not found")
            return False
        
        # Check other handlers
        handlers = [
            ('gui_handler', 'GUIHandler'),
            ('conversation_handler', 'ConversationHandler'),
            ('deferred_action_handler', 'DeferredActionHandler')
        ]
        
        for attr_name, class_name in handlers:
            if hasattr(orchestrator, attr_name):
                handler = getattr(orchestrator, attr_name)
                if handler is not None:
                    print(f"✅ {class_name} initialized: {handler.__class__.__name__}")
                else:
                    print(f"❌ {class_name} is None")
            else:
                print(f"❌ {class_name} attribute not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Handler initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intent_routing():
    """Test that question_answering intent is routed to QuestionAnsweringHandler."""
    
    print("\n🔄 Testing Intent Routing")
    print("=" * 60)
    
    try:
        from orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        
        # Test intent routing
        test_intents = [
            ("gui_interaction", "GUIHandler"),
            ("conversational_chat", "ConversationHandler"),
            ("deferred_action", "DeferredActionHandler"),
            ("question_answering", "QuestionAnsweringHandler")
        ]
        
        for intent, expected_handler in test_intents:
            print(f"\n🎯 Testing intent: {intent}")
            
            handler = orchestrator._get_handler_for_intent(intent)
            
            if handler is not None:
                actual_handler = handler.__class__.__name__
                if actual_handler == expected_handler:
                    print(f"✅ {intent} → {actual_handler}")
                else:
                    print(f"❌ {intent} → {actual_handler} (expected {expected_handler})")
                    return False
            else:
                print(f"❌ {intent} → None (expected {expected_handler})")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Intent routing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_question_answering_handler():
    """Test the QuestionAnsweringHandler directly."""
    
    print("\n🤖 Testing QuestionAnsweringHandler Directly")
    print("=" * 60)
    
    try:
        from handlers.question_answering_handler import QuestionAnsweringHandler
        
        # Create a mock orchestrator
        class MockOrchestrator:
            pass
        
        mock_orchestrator = MockOrchestrator()
        
        print("1️⃣ Creating QuestionAnsweringHandler...")
        handler = QuestionAnsweringHandler(mock_orchestrator)
        print(f"✅ Handler created: {handler.__class__.__name__}")
        
        print("2️⃣ Testing handler methods...")
        
        # Test validation
        is_valid = handler._validate_command("what's on my screen")
        print(f"✅ Command validation: {is_valid}")
        
        # Test application detection (will likely fail but shouldn't crash)
        try:
            app_info = handler._detect_active_application()
            if app_info:
                print(f"✅ Application detection: {app_info.name}")
            else:
                print("⚠️ Application detection: None (expected in test environment)")
        except Exception as e:
            print(f"⚠️ Application detection failed: {e} (expected in test environment)")
        
        return True
        
    except Exception as e:
        print(f"❌ QuestionAnsweringHandler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    
    print("🚀 Orchestrator Routing Test Suite")
    print("=" * 60)
    print("This test verifies that the QuestionAnsweringHandler is properly")
    print("integrated into the orchestrator and routing system.")
    print("=" * 60)
    
    # Run tests
    test1_success = test_handler_initialization()
    test2_success = test_intent_routing()
    test3_success = test_question_answering_handler()
    
    # Final results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    tests = [
        ("Handler Initialization", test1_success),
        ("Intent Routing", test2_success),
        ("QuestionAnsweringHandler", test3_success)
    ]
    
    passed_count = 0
    for test_name, success in tests:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed_count += 1
    
    print("=" * 60)
    
    if passed_count == len(tests):
        print("🎉 ALL TESTS PASSED!")
        print("✅ QuestionAnsweringHandler is properly integrated")
        print("✅ Intent routing should work correctly")
        print("✅ 'What's on my screen?' should now use the fast path")
    else:
        print(f"⚠️ {passed_count}/{len(tests)} TESTS PASSED")
        print("❌ There are issues with the integration")
        print("❌ The system may still route to GUIHandler")
    
    return passed_count == len(tests)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
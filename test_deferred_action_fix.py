#!/usr/bin/env python3
"""
Test script to verify the DeferredActionHandler fix for the process_query method error.
"""

import sys
import time
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.insert(0, '.')

def test_deferred_action_handler_fix():
    """Test that the DeferredActionHandler no longer calls the non-existent process_query method."""
    print("🔧 Testing DeferredActionHandler Fix")
    
    try:
        from handlers.deferred_action_handler import DeferredActionHandler
        from modules.reasoning import ReasoningModule
        
        # Create a mock orchestrator with all required attributes
        class MockOrchestrator:
            def __init__(self):
                self.reasoning_module = ReasoningModule()
                self.feedback_module = None
                self.audio_module = None
                self.automation_module = None
                self.is_waiting_for_user_action = False
                self.deferred_action_lock = Mock()
                self.deferred_action_lock.__enter__ = Mock(return_value=None)
                self.deferred_action_lock.__exit__ = Mock(return_value=None)
        
        # Create handler
        mock_orchestrator = MockOrchestrator()
        handler = DeferredActionHandler(mock_orchestrator)
        
        # Mock the API request to avoid actual network calls
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)'
                }
            }]
        }
        
        with patch.object(mock_orchestrator.reasoning_module, '_make_api_request', return_value=mock_response):
            # Test content generation
            content = handler._generate_content(
                content_request="Write a Python function for Fibonacci sequence",
                content_type="code",
                execution_id="test_123"
            )
            
            if content and 'fibonacci' in content.lower():
                print("✅ SUCCESS: Content generation works with correct API method")
                print(f"   Generated content preview: {content[:50]}...")
                return True
            else:
                print(f"❌ FAILED: Content generation returned unexpected result: {content}")
                return False
                
    except AttributeError as e:
        if 'process_query' in str(e):
            print(f"❌ FAILED: Still trying to call process_query method: {e}")
            return False
        else:
            print(f"❌ FAILED: Unexpected AttributeError: {e}")
            return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False

def test_config_import():
    """Test that the config import works correctly."""
    print("\n🔧 Testing Config Import")
    
    try:
        from config import CODE_GENERATION_PROMPT, TEXT_GENERATION_PROMPT
        
        if CODE_GENERATION_PROMPT and TEXT_GENERATION_PROMPT:
            print("✅ SUCCESS: Prompt templates imported successfully")
            print(f"   CODE_GENERATION_PROMPT length: {len(CODE_GENERATION_PROMPT)} chars")
            print(f"   TEXT_GENERATION_PROMPT length: {len(TEXT_GENERATION_PROMPT)} chars")
            return True
        else:
            print("❌ FAILED: Prompt templates are empty")
            return False
            
    except ImportError as e:
        print(f"❌ FAILED: Could not import prompt templates: {e}")
        return False

def main():
    """Run all tests for the DeferredActionHandler fix."""
    print("🚀 Running DeferredActionHandler Fix Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: DeferredActionHandler fix
    results.append(test_deferred_action_handler_fix())
    
    # Test 2: Config import
    results.append(test_config_import())
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🎉 DeferredActionHandler fix is working correctly!")
        print("\nFix Summary:")
        print("- ✅ Replaced non-existent process_query() method call")
        print("- ✅ Now uses _make_api_request() like the orchestrator")
        print("- ✅ Proper response parsing implemented")
        print("- ✅ Config import added for prompt templates")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("\n⚠️  Please review the failed tests above")
        return 1

if __name__ == "__main__":
    exit(main())
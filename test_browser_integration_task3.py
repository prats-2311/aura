#!/usr/bin/env python3
"""
Integration test for Task 3: Browser Content Extraction

This test verifies that the browser content extraction integrates properly
with the existing QuestionAnsweringHandler workflow.
"""

import sys
import os
import logging
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_browser_integration():
    """Test browser content extraction integration with the handler workflow."""
    
    print("=" * 60)
    print("Testing Browser Content Extraction Integration")
    print("=" * 60)
    
    try:
        # Import required modules
        from handlers.question_answering_handler import QuestionAnsweringHandler
        from modules.application_detector import ApplicationInfo, ApplicationType, BrowserType
        
        # Create a mock orchestrator
        mock_orchestrator = Mock()
        
        # Create handler instance
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        print("✓ Handler created successfully")
        
        # Test the full fast path workflow with browser content
        print("\n1. Testing full fast path workflow...")
        
        # Create a browser application
        browser_app = ApplicationInfo(
            name="Google Chrome",
            bundle_id="com.google.Chrome",
            process_id=12345,
            app_type=ApplicationType.WEB_BROWSER,
            browser_type=BrowserType.CHROME
        )
        
        # Mock content that should pass validation
        valid_content = """
        This is a comprehensive article about machine learning and artificial intelligence.
        The content covers various topics including neural networks, deep learning, and
        natural language processing. It provides detailed explanations and practical
        examples for developers and researchers working in the field of AI.
        """
        
        # Mock the dependencies
        with patch.object(handler, '_detect_active_application', return_value=browser_app):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_handler_class:
                mock_handler_instance = Mock()
                mock_handler_instance.get_page_text_content.return_value = valid_content
                mock_handler_class.return_value = mock_handler_instance
                
                # Test the fast path method
                result = handler._try_fast_path("what's on my screen")
                
                assert result is not None, "Fast path should succeed with valid browser content"
                assert result == valid_content, "Should return the extracted content"
                print(f"✓ Fast path returned {len(result)} characters of content")
        
        # Test integration with the main handle method
        print("\n2. Testing integration with main handle method...")
        
        with patch.object(handler, '_detect_active_application', return_value=browser_app):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_handler_class:
                mock_handler_instance = Mock()
                mock_handler_instance.get_page_text_content.return_value = valid_content
                mock_handler_class.return_value = mock_handler_instance
                
                # Test the main handle method
                context = {
                    "intent": {"intent": "question_answering"}, 
                    "timestamp": "2024-01-01T00:00:00",
                    "execution_id": "test_001"
                }
                result = handler.handle("what's on my screen", context)
                
                assert result is not None, "Handle method should return a result"
                assert result.get("status") == "success", "Result should indicate success"
                assert result.get("method") == "fast_path", "Should use fast path method"
                print("✓ Main handle method successfully uses browser content extraction")
        
        # Test fallback behavior when browser extraction fails
        print("\n3. Testing fallback behavior...")
        
        # Reset the handler to ensure clean state
        handler._browser_handler = None
        
        with patch.object(handler, '_detect_active_application', return_value=browser_app):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_handler_class:
                mock_handler_instance = Mock()
                mock_handler_instance.get_page_text_content.return_value = None  # Extraction fails
                mock_handler_class.return_value = mock_handler_instance
                
                # Mock the fallback method to return a success result
                with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                    mock_fallback.return_value = {
                        "status": "success",
                        "message": "Vision fallback result",
                        "method": "vision_fallback"
                    }
                    
                    context = {
                        "intent": {"intent": "question_answering"}, 
                        "timestamp": "2024-01-01T00:00:00",
                        "execution_id": "test_002"
                    }
                    result = handler.handle("what's on my screen", context)
                    
                    assert result is not None, "Should return fallback result"
                    assert result.get("method") == "vision_fallback", "Should use vision fallback"
                    assert mock_fallback.called, "Should call vision fallback when extraction fails"
                    print("✓ Correctly falls back to vision when browser extraction fails")
        
        # Test performance tracking
        print("\n4. Testing performance tracking...")
        
        # Reset performance counters
        handler._fast_path_attempts = 0
        handler._fast_path_successes = 0
        handler._fallback_count = 0
        
        # Successful extraction
        handler._browser_handler = None  # Reset handler
        with patch.object(handler, '_detect_active_application', return_value=browser_app):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_handler_class:
                mock_handler_instance = Mock()
                mock_handler_instance.get_page_text_content.return_value = valid_content
                mock_handler_class.return_value = mock_handler_instance
                
                context = {
                    "intent": {"intent": "question_answering"}, 
                    "timestamp": "2024-01-01T00:00:00",
                    "execution_id": "test_003"
                }
                result = handler.handle("what's on my screen", context)
                
                stats = handler.get_performance_stats()
                assert stats["fast_path_attempts"] > 0, "Should track fast path attempts"
                assert stats["fast_path_successes"] > 0, "Should track fast path successes"
                print(f"✓ Performance tracking: {stats['fast_path_success_rate']}% success rate")
        
        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("Browser content extraction is properly integrated")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_browser_integration()
    sys.exit(0 if success else 1)
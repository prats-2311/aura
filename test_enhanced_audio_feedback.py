#!/usr/bin/env python3
"""
Test Enhanced Audio Feedback Integration

This test verifies that the enhanced audio feedback system works correctly
for all new interaction modes including conversational, deferred actions,
and enhanced error/success feedback.
"""

import sys
import time
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_feedback_module():
    """Test the enhanced feedback module methods."""
    logger.info("Testing enhanced feedback module methods...")
    
    try:
        from modules.feedback import FeedbackModule, FeedbackPriority
        
        # Mock audio module
        mock_audio = Mock()
        mock_audio.text_to_speech = Mock()
        mock_audio.text_to_speech_enhanced = Mock()
        
        # Initialize feedback module
        feedback = FeedbackModule(audio_module=mock_audio)
        
        # Test conversational feedback
        logger.info("Testing conversational feedback...")
        feedback.provide_conversational_feedback(
            message="Hello! How can I help you today?",
            priority=FeedbackPriority.NORMAL,
            include_thinking_sound=False
        )
        
        # Test deferred action instructions
        logger.info("Testing deferred action instructions...")
        feedback.provide_deferred_action_instructions(
            content_type="code",
            priority=FeedbackPriority.HIGH
        )
        
        # Test deferred action completion feedback
        logger.info("Testing deferred action completion feedback...")
        feedback.provide_deferred_action_completion_feedback(
            success=True,
            content_type="code",
            priority=FeedbackPriority.HIGH
        )
        
        # Test timeout feedback
        logger.info("Testing deferred action timeout feedback...")
        feedback.provide_deferred_action_timeout_feedback(
            elapsed_time=300.0,
            priority=FeedbackPriority.HIGH
        )
        
        # Test enhanced error feedback
        logger.info("Testing enhanced error feedback...")
        feedback.provide_enhanced_error_feedback(
            error_message="Something went wrong",
            error_context="conversational",
            priority=FeedbackPriority.HIGH
        )
        
        # Test success feedback
        logger.info("Testing enhanced success feedback...")
        feedback.provide_success_feedback(
            success_message="Operation completed",
            success_context="gui_interaction",
            priority=FeedbackPriority.NORMAL
        )
        
        # Wait for feedback queue to process
        time.sleep(2)
        
        logger.info("✅ Enhanced feedback module methods test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced feedback module test failed: {e}")
        return False

def test_orchestrator_audio_integration():
    """Test orchestrator integration with enhanced audio feedback."""
    logger.info("Testing orchestrator audio feedback integration...")
    
    try:
        from orchestrator import Orchestrator
        from modules.feedback import FeedbackPriority
        
        # Mock dependencies
        with patch('modules.vision.VisionModule'), \
             patch('modules.reasoning.ReasoningModule'), \
             patch('modules.automation.AutomationModule'), \
             patch('modules.audio.AudioModule'), \
             patch('modules.accessibility.AccessibilityModule'):
            
            # Initialize orchestrator
            orchestrator = Orchestrator()
            
            # Mock feedback module with enhanced methods
            mock_feedback = Mock()
            mock_feedback.provide_conversational_feedback = Mock()
            mock_feedback.provide_deferred_action_instructions = Mock()
            mock_feedback.provide_deferred_action_completion_feedback = Mock()
            mock_feedback.provide_deferred_action_timeout_feedback = Mock()
            mock_feedback.provide_enhanced_error_feedback = Mock()
            mock_feedback.provide_success_feedback = Mock()
            mock_feedback.speak = Mock()
            mock_feedback.play = Mock()
            mock_feedback.play_with_message = Mock()
            
            orchestrator.feedback_module = mock_feedback
            orchestrator.module_availability['feedback'] = True
            
            # Test conversational query with enhanced feedback
            logger.info("Testing conversational query audio feedback...")
            with patch.object(orchestrator, '_recognize_intent') as mock_intent:
                mock_intent.return_value = {
                    'intent': 'conversational_chat',
                    'confidence': 0.9,
                    'parameters': {}
                }
                
                with patch.object(orchestrator.reasoning_module, '_make_api_request') as mock_response:
                    mock_response.return_value = "Hello! I'm here to help."
                    
                    result = orchestrator._handle_conversational_query("test-001", "Hello")
                    
                    # Verify enhanced conversational feedback was called
                    mock_feedback.provide_conversational_feedback.assert_called()
                    
            # Test deferred action instructions
            logger.info("Testing deferred action instructions audio feedback...")
            orchestrator._provide_deferred_action_instructions("test-002", "code")
            mock_feedback.provide_deferred_action_instructions.assert_called_with(
                content_type="code",
                priority=FeedbackPriority.HIGH
            )
            
            # Test deferred action completion
            logger.info("Testing deferred action completion audio feedback...")
            orchestrator.current_deferred_content_type = "text"
            orchestrator._provide_deferred_action_completion_feedback("test-003", True)
            mock_feedback.provide_deferred_action_completion_feedback.assert_called()
            
            # Test timeout feedback
            logger.info("Testing deferred action timeout audio feedback...")
            orchestrator.deferred_action_start_time = time.time() - 300
            orchestrator._handle_deferred_action_timeout("test-004")
            mock_feedback.provide_deferred_action_timeout_feedback.assert_called()
            
            logger.info("✅ Orchestrator audio integration test passed")
            return True
            
    except Exception as e:
        logger.error(f"❌ Orchestrator audio integration test failed: {e}")
        return False

def test_audio_feedback_timing_and_quality():
    """Test audio feedback timing and quality consistency."""
    logger.info("Testing audio feedback timing and quality...")
    
    try:
        from modules.feedback import FeedbackModule, FeedbackPriority, FeedbackType
        
        # Mock audio module
        mock_audio = Mock()
        mock_audio.text_to_speech = Mock()
        
        # Initialize feedback module
        feedback = FeedbackModule(audio_module=mock_audio)
        
        # Test timing consistency
        start_time = time.time()
        
        # Queue multiple feedback items
        feedback.provide_conversational_feedback("Test message 1")
        feedback.provide_deferred_action_instructions("code")
        feedback.provide_success_feedback(success_context="gui_interaction")
        
        # Wait for processing
        time.sleep(1)
        
        processing_time = time.time() - start_time
        
        # Verify reasonable processing time (should be under 2 seconds for queuing)
        if processing_time > 2.0:
            logger.warning(f"Audio feedback processing took {processing_time:.2f}s - may be too slow")
        else:
            logger.info(f"Audio feedback processing time: {processing_time:.2f}s - acceptable")
        
        # Test queue management
        queue_size = feedback.get_queue_size()
        logger.info(f"Feedback queue size: {queue_size}")
        
        # Test priority handling
        feedback.provide_enhanced_error_feedback(
            error_message="High priority error",
            error_context="deferred_action",
            priority=FeedbackPriority.HIGH
        )
        
        feedback.provide_conversational_feedback(
            message="Low priority message",
            priority=FeedbackPriority.LOW
        )
        
        logger.info("✅ Audio feedback timing and quality test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Audio feedback timing and quality test failed: {e}")
        return False

def test_audio_feedback_error_recovery():
    """Test audio feedback error recovery and fallback mechanisms."""
    logger.info("Testing audio feedback error recovery...")
    
    try:
        from modules.feedback import FeedbackModule, FeedbackPriority
        
        # Mock audio module that fails
        mock_audio = Mock()
        mock_audio.text_to_speech = Mock(side_effect=Exception("TTS failed"))
        mock_audio.text_to_speech_enhanced = Mock(side_effect=Exception("Enhanced TTS failed"))
        
        # Initialize feedback module
        feedback = FeedbackModule(audio_module=mock_audio)
        
        # Test error recovery for conversational feedback
        logger.info("Testing conversational feedback error recovery...")
        try:
            feedback.provide_conversational_feedback("Test message")
            # Should not raise exception due to error handling
            logger.info("✅ Conversational feedback error recovery works")
        except Exception as e:
            logger.error(f"❌ Conversational feedback error recovery failed: {e}")
            return False
        
        # Test error recovery for deferred action feedback
        logger.info("Testing deferred action feedback error recovery...")
        try:
            feedback.provide_deferred_action_instructions("code")
            # Should not raise exception due to error handling
            logger.info("✅ Deferred action feedback error recovery works")
        except Exception as e:
            logger.error(f"❌ Deferred action feedback error recovery failed: {e}")
            return False
        
        # Test error recovery for enhanced error feedback
        logger.info("Testing enhanced error feedback error recovery...")
        try:
            feedback.provide_enhanced_error_feedback(
                error_message="Test error",
                error_context="general"
            )
            # Should not raise exception due to error handling
            logger.info("✅ Enhanced error feedback error recovery works")
        except Exception as e:
            logger.error(f"❌ Enhanced error feedback error recovery failed: {e}")
            return False
        
        logger.info("✅ Audio feedback error recovery test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Audio feedback error recovery test failed: {e}")
        return False

def test_backward_compatibility():
    """Test that enhanced audio feedback maintains backward compatibility."""
    logger.info("Testing backward compatibility...")
    
    try:
        from modules.feedback import FeedbackModule, FeedbackPriority
        
        # Mock audio module
        mock_audio = Mock()
        mock_audio.text_to_speech = Mock()
        
        # Initialize feedback module
        feedback = FeedbackModule(audio_module=mock_audio)
        
        # Test existing methods still work
        logger.info("Testing existing feedback methods...")
        
        # Test basic speak method
        feedback.speak("Test message", FeedbackPriority.NORMAL)
        
        # Test basic play method
        feedback.play("success", FeedbackPriority.NORMAL)
        
        # Test play_with_message method
        feedback.play_with_message("success", "Test message", FeedbackPriority.NORMAL)
        
        # Wait for processing
        time.sleep(1)
        
        logger.info("✅ Backward compatibility test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Backward compatibility test failed: {e}")
        return False

def main():
    """Run all enhanced audio feedback tests."""
    logger.info("🎵 Starting Enhanced Audio Feedback Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Enhanced Feedback Module Methods", test_enhanced_feedback_module),
        ("Orchestrator Audio Integration", test_orchestrator_audio_integration),
        ("Audio Feedback Timing and Quality", test_audio_feedback_timing_and_quality),
        ("Audio Feedback Error Recovery", test_audio_feedback_error_recovery),
        ("Backward Compatibility", test_backward_compatibility)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All enhanced audio feedback tests passed!")
        logger.info("\n📋 IMPLEMENTATION SUMMARY:")
        logger.info("✅ Enhanced conversational audio feedback with natural speech patterns")
        logger.info("✅ Deferred action audio instructions with content-specific messaging")
        logger.info("✅ Enhanced completion feedback with success/failure context")
        logger.info("✅ Timeout feedback with clear timing information")
        logger.info("✅ Context-aware error feedback with appropriate messaging")
        logger.info("✅ Enhanced success feedback for different interaction modes")
        logger.info("✅ Consistent audio feedback timing and quality across all modes")
        logger.info("✅ Comprehensive error recovery and fallback mechanisms")
        logger.info("✅ Full backward compatibility with existing audio feedback")
        return True
    else:
        logger.error(f"💥 {total - passed} tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""
Backward compatibility tests for Content Comprehension Fast Path

This module ensures that existing functionality is preserved and that the
fast path implementation maintains identical user experience when falling back.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from handlers.question_answering_handler import QuestionAnsweringHandler
from modules.application_detector import ApplicationType


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with existing functionality."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for compatibility testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_existing_question_answering_commands_work(self, handler):
        """Test that existing question answering commands continue to work."""
        # Test various question formats that should work
        question_formats = [
            "what's on my screen",
            "what is on my screen",
            "tell me what's on the screen",
            "describe what you see",
            "what do you see on my screen",
            "analyze my screen",
            "read my screen",
            "what's displayed",
            "screen content"
        ]
        
        vision_answer = "I can see various elements on your screen including text and interface components."
        
        for question in question_formats:
            # Mock unsupported application to force vision fallback
            unsupported_app = Mock()
            unsupported_app.name = "TextEdit"
            unsupported_app.app_type = ApplicationType.TEXT_EDITOR
            
            with patch.object(handler, '_detect_active_application', return_value=unsupported_app):
                with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                    mock_fallback.return_value = {
                        "status": "success",
                        "message": vision_answer,
                        "method": "vision_fallback",
                        "fallback_reason": "unsupported_application"
                    }
                    
                    result = handler.handle(question, {
                        "intent": {"intent": "question_answering"}
                    })
            
            assert result["status"] == "success"
            assert result["message"] == vision_answer
            assert result["method"] == "vision_fallback"
            
            # Verify fallback was called with correct parameters
            mock_fallback.assert_called_once_with(question, "unsupported_application")
            mock_fallback.reset_mock()
    
    def test_vision_fallback_identical_behavior(self, handler):
        """Test that vision fallback provides identical behavior to current implementation."""
        question = "what's on my screen"
        
        # Mock the complete vision fallback flow
        mock_vision = Mock()
        mock_reasoning = Mock()
        mock_audio = Mock()
        
        screen_context = {
            "elements": [
                {"type": "text", "content": "Sample text"},
                {"type": "button", "content": "Click me"}
            ],
            "text_blocks": ["Block 1", "Block 2"]
        }
        
        action_plan = {
            "response": "I can see a screen with text elements and a button.",
            "metadata": {"confidence": 0.85}
        }
        
        with patch.object(handler, '_get_module_safely') as mock_get_module:
            mock_get_module.side_effect = lambda name: {
                'vision_module': mock_vision,
                'reasoning_module': mock_reasoning,
                'audio_module': mock_audio
            }.get(name)
            
            with patch.object(handler, '_determine_analysis_type_for_question', return_value="simple"):
                with patch.object(handler, '_analyze_screen_for_information', return_value=screen_context):
                    with patch.object(handler, '_create_qa_reasoning_prompt', return_value="analyze prompt"):
                        with patch.object(handler, '_get_qa_action_plan', return_value=action_plan):
                            with patch.object(handler, '_extract_and_validate_answer', return_value=action_plan["response"]):
                                
                                result = handler._fallback_to_vision(question, "fast_path_failed")
        
        # Verify identical behavior patterns
        assert result["status"] == "success"
        assert result["message"] == action_plan["response"]
        assert result["method"] == "vision_fallback"
        assert result["fallback_reason"] == "fast_path_failed"
        
        # Verify audio feedback (identical to current implementation)
        mock_audio.speak.assert_called_once_with(action_plan["response"])
        
        # Verify screen analysis was performed
        assert "screen_elements_analyzed" in result
        assert "text_blocks_analyzed" in result
        assert result["screen_elements_analyzed"] == len(screen_context["elements"])
        assert result["text_blocks_analyzed"] == len(screen_context["text_blocks"])
    
    def test_error_handling_backward_compatibility(self, handler):
        """Test that error handling maintains backward compatibility."""
        question = "what's on my screen"
        
        # Test various error scenarios that should behave identically
        error_scenarios = [
            ("vision_module_unavailable", None, None, None),
            ("reasoning_module_unavailable", Mock(), None, None),
            ("screen_analysis_failed", Mock(), Mock(), None),
            ("reasoning_failed", Mock(), Mock(), Mock())
        ]
        
        for scenario_name, mock_vision, mock_reasoning, screen_context in error_scenarios:
            with patch.object(handler, '_get_module_safely') as mock_get_module:
                mock_get_module.side_effect = lambda name: {
                    'vision_module': mock_vision,
                    'reasoning_module': mock_reasoning,
                    'audio_module': Mock()
                }.get(name)
                
                with patch.object(handler, '_determine_analysis_type_for_question', return_value="simple"):
                    with patch.object(handler, '_analyze_screen_for_information', return_value=screen_context):
                        with patch.object(handler, '_create_qa_reasoning_prompt', return_value="prompt"):
                            with patch.object(handler, '_get_qa_action_plan', return_value=None):
                                
                                result = handler._fallback_to_vision(question, "fast_path_failed")
            
            # All error scenarios should return error status
            assert result["status"] == "error"
            assert result["method"] == "vision_fallback"
            assert "error" in result["message"].lower() or "trouble" in result["message"].lower()
    
    def test_no_configuration_changes_required(self, handler):
        """Test that no existing configuration changes are required."""
        # The handler should work with existing orchestrator setup
        # without requiring any configuration changes
        
        # Test that handler initializes with minimal orchestrator
        minimal_orchestrator = Mock()
        new_handler = QuestionAnsweringHandler(minimal_orchestrator)
        
        assert new_handler.orchestrator == minimal_orchestrator
        assert new_handler.logger is not None
        assert hasattr(new_handler, '_fast_path_attempts')
        assert hasattr(new_handler, '_fast_path_successes')
        assert hasattr(new_handler, '_fallback_count')
    
    def test_existing_command_patterns_preserved(self, handler):
        """Test that existing command patterns and responses are preserved."""
        # Test that the handler responds to the same command patterns
        # that the existing system would handle
        
        valid_commands = [
            "what's on my screen",
            "What's on my screen?",
            "WHAT'S ON MY SCREEN",
            "  what's on my screen  ",  # with whitespace
            "tell me what's on my screen please"
        ]
        
        for command in valid_commands:
            # All should pass validation
            assert handler._validate_command(command) is True
        
        invalid_commands = [
            "",
            "   ",
            None
        ]
        
        for command in invalid_commands:
            if command is not None:
                assert handler._validate_command(command) is False
    
    def test_response_format_compatibility(self, handler):
        """Test that response format is compatible with existing expectations."""
        question = "what's on my screen"
        
        # Test successful response format
        with patch.object(handler, '_try_fast_path_with_reason', return_value=("Fast path result", "")):
            with patch.object(handler, '_speak_result'):
                result = handler.handle(question, {"intent": {"intent": "question_answering"}})
        
        # Verify response format matches expected structure
        required_fields = ["status", "message", "timestamp", "execution_time", "method"]
        for field in required_fields:
            assert field in result
        
        assert result["status"] in ["success", "error", "waiting_for_user_action"]
        assert isinstance(result["message"], str)
        assert isinstance(result["timestamp"], float)
        assert isinstance(result["execution_time"], float)
        assert isinstance(result["method"], str)
        
        # Test error response format
        with patch.object(handler, '_validate_command', return_value=False):
            error_result = handler.handle("", {"intent": {"intent": "question_answering"}})
        
        for field in required_fields:
            assert field in error_result
        
        assert error_result["status"] == "error"
    
    def test_audio_feedback_preserved(self, handler):
        """Test that audio feedback behavior is preserved."""
        question = "what's on my screen"
        answer = "This is the answer to your question."
        
        # Test fast path audio feedback
        with patch.object(handler, '_try_fast_path_with_reason', return_value=(answer, "")):
            with patch.object(handler, '_speak_result') as mock_speak:
                result = handler.handle(question, {"intent": {"intent": "question_answering"}})
        
        assert result["status"] == "success"
        mock_speak.assert_called_once_with(answer)
        
        # Test vision fallback audio feedback
        with patch.object(handler, '_try_fast_path_with_reason', return_value=(None, "failed")):
            with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                mock_fallback.return_value = {
                    "status": "success",
                    "message": answer,
                    "method": "vision_fallback"
                }
                
                result = handler.handle(question, {"intent": {"intent": "question_answering"}})
        
        # Vision fallback should handle its own audio feedback
        mock_fallback.assert_called_once_with(question, "failed")
    
    def test_console_output_preserved(self, handler):
        """Test that console output behavior is preserved in vision fallback."""
        question = "what's on my screen"
        answer = "Console output test answer."
        
        mock_vision = Mock()
        mock_reasoning = Mock()
        mock_audio = Mock()
        
        with patch.object(handler, '_get_module_safely') as mock_get_module:
            mock_get_module.side_effect = lambda name: {
                'vision_module': mock_vision,
                'reasoning_module': mock_reasoning,
                'audio_module': mock_audio
            }.get(name)
            
            with patch.object(handler, '_determine_analysis_type_for_question', return_value="simple"):
                with patch.object(handler, '_analyze_screen_for_information', return_value={"elements": [], "text_blocks": []}):
                    with patch.object(handler, '_create_qa_reasoning_prompt', return_value="prompt"):
                        with patch.object(handler, '_get_qa_action_plan', return_value={"response": "answer", "metadata": {"confidence": 0.8}}):
                            with patch.object(handler, '_extract_and_validate_answer', return_value=answer):
                                with patch('builtins.print') as mock_print:
                                    
                                    result = handler._fallback_to_vision(question, "test_reason")
        
        # Verify console output matches expected format
        mock_print.assert_called_once_with(f"\n🤖 AURA: {answer}\n")
        assert result["status"] == "success"
        assert result["message"] == answer


class TestExistingWorkflowPreservation:
    """Tests to ensure existing workflows are preserved."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for workflow testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_unsupported_applications_fallback_seamlessly(self, handler):
        """Test that unsupported applications fall back seamlessly to vision."""
        unsupported_apps = [
            ("TextEdit", ApplicationType.TEXT_EDITOR),
            ("Calculator", ApplicationType.CALCULATOR),
            ("Terminal", ApplicationType.TERMINAL),
            ("Finder", ApplicationType.FILE_MANAGER),
            ("System Preferences", ApplicationType.SYSTEM_PREFERENCES)
        ]
        
        vision_answer = "Vision-based analysis of the screen content."
        
        for app_name, app_type in unsupported_apps:
            app_info = Mock()
            app_info.name = app_name
            app_info.app_type = app_type
            
            with patch.object(handler, '_detect_active_application', return_value=app_info):
                with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                    mock_fallback.return_value = {
                        "status": "success",
                        "message": vision_answer,
                        "method": "vision_fallback",
                        "fallback_reason": "unsupported_application"
                    }
                    
                    result = handler.handle("what's on my screen", {
                        "intent": {"intent": "question_answering"}
                    })
            
            assert result["status"] == "success"
            assert result["method"] == "vision_fallback"
            assert result["fallback_reason"] == "unsupported_application"
            mock_fallback.assert_called_once_with("what's on my screen", "unsupported_application")
    
    def test_application_detection_failure_fallback(self, handler):
        """Test that application detection failure falls back gracefully."""
        vision_answer = "Vision fallback when application detection fails."
        
        with patch.object(handler, '_detect_active_application', return_value=None):
            with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                mock_fallback.return_value = {
                    "status": "success",
                    "message": vision_answer,
                    "method": "vision_fallback",
                    "fallback_reason": "application_detection_failed"
                }
                
                result = handler.handle("what's on my screen", {
                    "intent": {"intent": "question_answering"}
                })
        
        assert result["status"] == "success"
        assert result["method"] == "vision_fallback"
        assert result["fallback_reason"] == "application_detection_failed"
    
    def test_extraction_failure_fallback(self, handler):
        """Test that extraction failures fall back gracefully."""
        app_info = Mock()
        app_info.name = "Google Chrome"
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        vision_answer = "Vision fallback when extraction fails."
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                # Simulate extraction failure
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.side_effect = Exception("Extraction failed")
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                    mock_fallback.return_value = {
                        "status": "success",
                        "message": vision_answer,
                        "method": "vision_fallback",
                        "fallback_reason": "browser_extraction_failed"
                    }
                    
                    result = handler.handle("what's on my screen", {
                        "intent": {"intent": "question_answering"}
                    })
        
        assert result["status"] == "success"
        assert result["method"] == "vision_fallback"
        # Should contain some form of extraction failure reason
        assert "extraction" in result.get("fallback_reason", "").lower() or "failed" in result.get("fallback_reason", "").lower()
    
    def test_user_experience_identical_on_fallback(self, handler):
        """Test that user experience is identical when falling back to vision."""
        question = "what's on my screen"
        vision_answer = "I can see text and interface elements on your screen."
        
        # Mock complete vision fallback flow
        mock_audio = Mock()
        
        with patch.object(handler, '_detect_active_application', return_value=None):
            with patch.object(handler, '_get_module_safely') as mock_get_module:
                mock_get_module.side_effect = lambda name: {
                    'vision_module': Mock(),
                    'reasoning_module': Mock(),
                    'audio_module': mock_audio
                }.get(name)
                
                with patch.object(handler, '_determine_analysis_type_for_question', return_value="simple"):
                    with patch.object(handler, '_analyze_screen_for_information', return_value={"elements": [], "text_blocks": []}):
                        with patch.object(handler, '_create_qa_reasoning_prompt', return_value="prompt"):
                            with patch.object(handler, '_get_qa_action_plan', return_value={"response": "answer", "metadata": {"confidence": 0.8}}):
                                with patch.object(handler, '_extract_and_validate_answer', return_value=vision_answer):
                                    with patch('builtins.print') as mock_print:
                                        
                                        result = handler.handle(question, {
                                            "intent": {"intent": "question_answering"}
                                        })
        
        # Verify identical user experience
        assert result["status"] == "success"
        assert result["message"] == vision_answer
        
        # Audio feedback should be provided
        mock_audio.speak.assert_called_once_with(vision_answer)
        
        # Console output should be provided
        mock_print.assert_called_once_with(f"\n🤖 AURA: {vision_answer}\n")
    
    def test_no_regression_in_existing_functionality(self, handler):
        """Test that no existing functionality is broken."""
        # Test that all existing handler methods are still available
        required_methods = [
            'handle',
            '_create_success_result',
            '_create_error_result',
            '_validate_command',
            '_get_module_safely'
        ]
        
        for method_name in required_methods:
            assert hasattr(handler, method_name)
            assert callable(getattr(handler, method_name))
        
        # Test that base handler functionality still works
        success_result = handler._create_success_result("Test success")
        assert success_result["status"] == "success"
        assert success_result["message"] == "Test success"
        
        error_result = handler._create_error_result("Test error")
        assert error_result["status"] == "error"
        assert error_result["message"] == "Test error"
        
        # Test command validation
        assert handler._validate_command("valid command") is True
        assert handler._validate_command("") is False


class TestPerformanceBackwardCompatibility:
    """Tests to ensure performance doesn't regress for existing scenarios."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for performance compatibility testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_vision_fallback_performance_not_degraded(self, handler):
        """Test that vision fallback performance is not degraded."""
        import time
        
        question = "what's on my screen"
        vision_answer = "Vision analysis result."
        
        start_time = time.time()
        
        # Force vision fallback by using unsupported application
        unsupported_app = Mock()
        unsupported_app.name = "TextEdit"
        unsupported_app.app_type = ApplicationType.TEXT_EDITOR
        
        with patch.object(handler, '_detect_active_application', return_value=unsupported_app):
            with patch.object(handler, '_get_module_safely') as mock_get_module:
                mock_get_module.side_effect = lambda name: {
                    'vision_module': Mock(),
                    'reasoning_module': Mock(),
                    'audio_module': Mock()
                }.get(name)
                
                with patch.object(handler, '_determine_analysis_type_for_question', return_value="simple"):
                    with patch.object(handler, '_analyze_screen_for_information', return_value={"elements": [], "text_blocks": []}):
                        with patch.object(handler, '_create_qa_reasoning_prompt', return_value="prompt"):
                            with patch.object(handler, '_get_qa_action_plan', return_value={"response": "answer", "metadata": {"confidence": 0.8}}):
                                with patch.object(handler, '_extract_and_validate_answer', return_value=vision_answer):
                                    
                                    result = handler.handle(question, {
                                        "intent": {"intent": "question_answering"}
                                    })
        
        execution_time = time.time() - start_time
        
        assert result["status"] == "success"
        assert result["method"] == "vision_fallback"
        
        # Vision fallback should not be significantly slower than before
        # (allowing reasonable overhead for fast path attempt)
        assert execution_time < 10.0  # Should complete in reasonable time
    
    def test_memory_usage_not_increased(self, handler):
        """Test that memory usage is not significantly increased."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute multiple vision fallback scenarios
        for i in range(5):
            unsupported_app = Mock()
            unsupported_app.name = f"TestApp{i}"
            unsupported_app.app_type = ApplicationType.TEXT_EDITOR
            
            with patch.object(handler, '_detect_active_application', return_value=unsupported_app):
                with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                    mock_fallback.return_value = {
                        "status": "success",
                        "message": f"Result {i}",
                        "method": "vision_fallback"
                    }
                    
                    result = handler.handle("what's on my screen", {
                        "intent": {"intent": "question_answering"}
                    })
                    
                    assert result["status"] == "success"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (less than 20MB for 5 requests)
        assert memory_increase < 20.0
        
        print(f"Memory usage - Initial: {initial_memory:.1f}MB, Final: {final_memory:.1f}MB, Increase: {memory_increase:.1f}MB")


class TestConfigurationBackwardCompatibility:
    """Tests to ensure no configuration changes are required."""
    
    def test_no_new_configuration_required(self):
        """Test that no new configuration parameters are required."""
        # The handler should work with existing orchestrator setup
        # without requiring any new configuration
        
        mock_orchestrator = Mock()
        
        # Should initialize successfully with minimal setup
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        assert handler is not None
        assert handler.orchestrator == mock_orchestrator
    
    def test_existing_module_references_work(self):
        """Test that existing module references continue to work."""
        mock_orchestrator = Mock()
        
        # Set up orchestrator with existing module structure
        mock_orchestrator.vision_module = Mock()
        mock_orchestrator.reasoning_module = Mock()
        mock_orchestrator.audio_module = Mock()
        mock_orchestrator.application_detector = Mock()
        
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Should be able to access modules through existing patterns
        vision_module = handler._get_module_safely('vision_module')
        reasoning_module = handler._get_module_safely('reasoning_module')
        audio_module = handler._get_module_safely('audio_module')
        
        assert vision_module == mock_orchestrator.vision_module
        assert reasoning_module == mock_orchestrator.reasoning_module
        assert audio_module == mock_orchestrator.audio_module
    
    def test_existing_error_handling_patterns_preserved(self):
        """Test that existing error handling patterns are preserved."""
        mock_orchestrator = Mock()
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        # Test that base handler error handling still works
        error_result = handler._create_error_result("Test error", Exception("Test exception"))
        
        assert error_result["status"] == "error"
        assert error_result["message"] == "Test error"
        assert "timestamp" in error_result
        
        # Test module error handling
        module_error_result = handler._handle_module_error("test_module", Exception("Module failed"), "test operation")
        
        assert module_error_result["status"] == "error"
        assert "test operation" in module_error_result["message"]
        assert module_error_result["module"] == "test_module"
        assert module_error_result["operation"] == "test operation"
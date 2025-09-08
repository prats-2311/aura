"""
Unit tests for QuestionAnsweringHandler

This module provides comprehensive unit tests for the QuestionAnsweringHandler,
covering all methods, error scenarios, and performance requirements.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call
from handlers.question_answering_handler import QuestionAnsweringHandler
from modules.application_detector import ApplicationType, BrowserType


class TestQuestionAnsweringHandler:
    """Test suite for QuestionAnsweringHandler unit tests."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator with all required modules."""
        orchestrator = Mock()
        
        # Mock modules
        orchestrator.application_detector = Mock()
        orchestrator.browser_accessibility_handler = Mock()
        orchestrator.pdf_handler = Mock()
        orchestrator.reasoning_module = Mock()
        orchestrator.audio_module = Mock()
        orchestrator.vision_module = Mock()
        
        return orchestrator
    
    @pytest.fixture
    def handler(self, mock_orchestrator):
        """Create a QuestionAnsweringHandler instance with mocked dependencies."""
        return QuestionAnsweringHandler(mock_orchestrator)
    
    @pytest.fixture
    def sample_app_info(self):
        """Create sample application info for testing."""
        app_info = Mock()
        app_info.name = "Google Chrome"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.CHROME
        return app_info
    
    def test_handler_initialization(self, mock_orchestrator):
        """Test that handler initializes correctly with orchestrator reference."""
        handler = QuestionAnsweringHandler(mock_orchestrator)
        
        assert handler.orchestrator == mock_orchestrator
        assert handler.logger is not None
        assert handler._fast_path_attempts == 0
        assert handler._fast_path_successes == 0
        assert handler._fallback_count == 0
    
    def test_handle_invalid_command(self, handler):
        """Test handling of invalid/empty commands."""
        # Test empty command
        result = handler.handle("", {"intent": {"intent": "question_answering"}})
        
        assert result["status"] == "error"
        assert "valid question" in result["message"]
        assert result["method"] == "validation_failed"
    
    def test_handle_whitespace_command(self, handler):
        """Test handling of whitespace-only commands."""
        result = handler.handle("   ", {"intent": {"intent": "question_answering"}})
        
        assert result["status"] == "error"
        assert "valid question" in result["message"]
    
    def test_handle_successful_fast_path(self, handler, sample_app_info):
        """Test successful fast path execution."""
        # Mock fast path success
        with patch.object(handler, '_try_fast_path_with_reason') as mock_fast_path:
            mock_fast_path.return_value = ("This is the summarized content", "")
            
            with patch.object(handler, '_speak_result') as mock_speak:
                result = handler.handle("what's on my screen", {"intent": {"intent": "question_answering"}})
        
        assert result["status"] == "success"
        assert result["message"] == "This is the summarized content"
        assert result["method"] == "fast_path"
        assert result["extraction_method"] == "text_based"
        assert "execution_time" in result
        mock_speak.assert_called_once_with("This is the summarized content")
    
    def test_handle_fast_path_failure_fallback(self, handler):
        """Test fallback to vision when fast path fails."""
        # Mock fast path failure
        with patch.object(handler, '_try_fast_path_with_reason') as mock_fast_path:
            mock_fast_path.return_value = (None, "application_detection_failed")
            
            with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                mock_fallback.return_value = {
                    "status": "success",
                    "message": "Vision fallback result",
                    "method": "vision_fallback"
                }
                
                result = handler.handle("what's on my screen", {"intent": {"intent": "question_answering"}})
        
        assert result["status"] == "success"
        assert result["message"] == "Vision fallback result"
        assert result["method"] == "vision_fallback"
        mock_fallback.assert_called_once_with("what's on my screen", "application_detection_failed")
    
    def test_handle_exception_handling(self, handler):
        """Test exception handling in main handle method."""
        with patch.object(handler, '_validate_command', side_effect=Exception("Test error")):
            result = handler.handle("what's on my screen", {"intent": {"intent": "question_answering"}})
        
        assert result["status"] == "error"
        assert "unexpected issue" in result["message"]
        assert result["method"] == "exception_handling"
    
    def test_try_fast_path_application_detection_failure(self, handler):
        """Test fast path when application detection fails."""
        with patch.object(handler, '_detect_active_application', return_value=None):
            result = handler._try_fast_path("what's on my screen")
        
        assert result is None
        assert handler._determine_fallback_reason() == "application_detection_failed"
    
    def test_try_fast_path_unsupported_application(self, handler):
        """Test fast path with unsupported application."""
        app_info = Mock()
        app_info.name = "TextEdit"
        app_info.app_type = ApplicationType.NATIVE_APP
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch.object(handler, '_is_supported_application', return_value=False):
                result = handler._try_fast_path("what's on my screen")
        
        assert result is None
        assert handler._determine_fallback_reason() == "unsupported_application"
    
    def test_try_fast_path_no_extraction_method(self, handler, sample_app_info):
        """Test fast path when no extraction method is available."""
        with patch.object(handler, '_detect_active_application', return_value=sample_app_info):
            with patch.object(handler, '_is_supported_application', return_value=True):
                with patch.object(handler, '_get_extraction_method', return_value=None):
                    result = handler._try_fast_path("what's on my screen")
        
        assert result is None
        assert handler._determine_fallback_reason() == "no_extraction_method"
    
    def test_try_fast_path_browser_extraction_success(self, handler, sample_app_info):
        """Test successful browser content extraction in fast path."""
        extracted_content = "This is the extracted browser content with more than 50 characters."
        summarized_content = "This is the summarized content."
        
        with patch.object(handler, '_detect_active_application', return_value=sample_app_info):
            with patch.object(handler, '_is_supported_application', return_value=True):
                with patch.object(handler, '_get_extraction_method', return_value="browser"):
                    with patch.object(handler, '_extract_browser_content', return_value=extracted_content):
                        with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                            with patch.object(handler, '_summarize_content', return_value=summarized_content):
                                result = handler._try_fast_path("what's on my screen")
        
        assert result == summarized_content
    
    def test_try_fast_path_pdf_extraction_success(self, handler):
        """Test successful PDF content extraction in fast path."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        extracted_content = "This is the extracted PDF content with more than 50 characters."
        summarized_content = "This is the summarized PDF content."
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch.object(handler, '_is_supported_application', return_value=True):
                with patch.object(handler, '_get_extraction_method', return_value="pdf"):
                    with patch.object(handler, '_extract_pdf_content', return_value=extracted_content):
                        with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                            with patch.object(handler, '_summarize_content', return_value=summarized_content):
                                result = handler._try_fast_path("what's on my screen")
        
        assert result == summarized_content
    
    def test_try_fast_path_content_extraction_failure(self, handler, sample_app_info):
        """Test fast path when content extraction fails."""
        with patch.object(handler, '_detect_active_application', return_value=sample_app_info):
            with patch.object(handler, '_is_supported_application', return_value=True):
                with patch.object(handler, '_get_extraction_method', return_value="browser"):
                    with patch.object(handler, '_extract_browser_content', return_value=None):
                        result = handler._try_fast_path("what's on my screen")
        
        assert result is None
    
    def test_try_fast_path_content_validation_failure(self, handler, sample_app_info):
        """Test fast path when content validation fails."""
        with patch.object(handler, '_detect_active_application', return_value=sample_app_info):
            with patch.object(handler, '_is_supported_application', return_value=True):
                with patch.object(handler, '_get_extraction_method', return_value="browser"):
                    with patch.object(handler, '_extract_browser_content', return_value="content"):
                        with patch.object(handler, '_process_content_for_summarization', return_value=None):
                            result = handler._try_fast_path("what's on my screen")
        
        assert result is None
        assert handler._determine_fallback_reason() == "content_validation_failed"
    
    def test_try_fast_path_summarization_failure_fallback(self, handler, sample_app_info):
        """Test fast path when summarization fails but fallback summary works."""
        extracted_content = "This is the extracted content with more than 50 characters."
        fallback_summary = "Fallback summary of the content."
        
        with patch.object(handler, '_detect_active_application', return_value=sample_app_info):
            with patch.object(handler, '_is_supported_application', return_value=True):
                with patch.object(handler, '_get_extraction_method', return_value="browser"):
                    with patch.object(handler, '_extract_browser_content', return_value=extracted_content):
                        with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                            with patch.object(handler, '_summarize_content', return_value=None):
                                with patch.object(handler, '_create_fallback_summary', return_value=fallback_summary):
                                    result = handler._try_fast_path("what's on my screen")
        
        assert result == fallback_summary
    
    def test_try_fast_path_exception_handling(self, handler):
        """Test exception handling in fast path."""
        with patch.object(handler, '_detect_active_application', side_effect=Exception("Test error")):
            result = handler._try_fast_path("what's on my screen")
        
        assert result is None
        assert handler._determine_fallback_reason() == "exception_in_fast_path"
    
    def test_extract_browser_content_success(self, handler, sample_app_info):
        """Test successful browser content extraction."""
        content = "This is extracted browser content with more than 50 characters for validation."
        
        # Mock BrowserAccessibilityHandler
        mock_browser_handler = Mock()
        mock_browser_handler.get_page_text_content.return_value = content
        
        with patch.object(handler, '_detect_active_application', return_value=sample_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler', return_value=mock_browser_handler):
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == content
        mock_browser_handler.get_page_text_content.assert_called_once_with(sample_app_info)
    
    def test_extract_browser_content_no_app_detection(self, handler):
        """Test browser content extraction when app detection fails."""
        with patch.object(handler, '_detect_active_application', return_value=None):
            result = handler._extract_browser_content()
        
        assert result is None
    
    def test_extract_browser_content_not_browser(self, handler):
        """Test browser content extraction with non-browser app."""
        app_info = Mock()
        app_info.name = "TextEdit"
        app_info.app_type = ApplicationType.NATIVE_APP
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            result = handler._extract_browser_content()
        
        assert result is None
    
    def test_extract_browser_content_timeout(self, handler, sample_app_info):
        """Test browser content extraction timeout handling."""
        # Mock a slow extraction that times out
        mock_browser_handler = Mock()
        
        def slow_extraction(*args):
            time.sleep(3)  # Longer than 2 second timeout
            return "content"
        
        mock_browser_handler.get_page_text_content.side_effect = slow_extraction
        
        with patch.object(handler, '_detect_active_application', return_value=sample_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler', return_value=mock_browser_handler):
                result = handler._extract_browser_content()
        
        assert result is None
        assert handler._last_fallback_reason == "browser_extraction_timeout"
    
    def test_extract_browser_content_too_short(self, handler, sample_app_info):
        """Test browser content extraction with content too short."""
        short_content = "short"  # Less than 50 characters
        
        mock_browser_handler = Mock()
        mock_browser_handler.get_page_text_content.return_value = short_content
        
        with patch.object(handler, '_detect_active_application', return_value=sample_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler', return_value=mock_browser_handler):
                result = handler._extract_browser_content()
        
        assert result is None
    
    def test_extract_browser_content_validation_failure(self, handler, sample_app_info):
        """Test browser content extraction with validation failure."""
        content = "This is extracted browser content with more than 50 characters for validation."
        
        mock_browser_handler = Mock()
        mock_browser_handler.get_page_text_content.return_value = content
        
        with patch.object(handler, '_detect_active_application', return_value=sample_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler', return_value=mock_browser_handler):
                with patch.object(handler, '_validate_browser_content', return_value=False):
                    result = handler._extract_browser_content()
        
        assert result is None
    
    def test_extract_pdf_content_success(self, handler):
        """Test successful PDF content extraction."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        content = "This is extracted PDF content with more than 50 characters for validation."
        cleaned_content = "This is cleaned PDF content with more than 50 characters."
        
        # Mock PDFHandler
        mock_pdf_handler = Mock()
        mock_pdf_handler.extract_text_from_open_document.return_value = content
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler', return_value=mock_pdf_handler):
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        assert result == cleaned_content
        mock_pdf_handler.extract_text_from_open_document.assert_called_once_with("Preview")
    
    def test_extract_pdf_content_no_app_detection(self, handler):
        """Test PDF content extraction when app detection fails."""
        with patch.object(handler, '_detect_active_application', return_value=None):
            result = handler._extract_pdf_content()
        
        assert result is None
    
    def test_extract_pdf_content_not_pdf_reader(self, handler):
        """Test PDF content extraction with non-PDF reader app."""
        app_info = Mock()
        app_info.name = "Chrome"
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            result = handler._extract_pdf_content()
        
        assert result is None
    
    def test_extract_pdf_content_timeout(self, handler):
        """Test PDF content extraction timeout handling."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        # Mock a slow extraction that times out
        mock_pdf_handler = Mock()
        
        def slow_extraction(*args):
            time.sleep(3)  # Longer than 2 second timeout
            return "content"
        
        mock_pdf_handler.extract_text_from_open_document.side_effect = slow_extraction
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler', return_value=mock_pdf_handler):
                result = handler._extract_pdf_content()
        
        assert result is None
        assert handler._last_fallback_reason == "pdf_extraction_timeout"
    
    def test_extract_pdf_content_too_short(self, handler):
        """Test PDF content extraction with content too short."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        short_content = "short"  # Less than 50 characters
        
        mock_pdf_handler = Mock()
        mock_pdf_handler.extract_text_from_open_document.return_value = short_content
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler', return_value=mock_pdf_handler):
                result = handler._extract_pdf_content()
        
        assert result is None
    
    def test_extract_pdf_content_validation_failure(self, handler):
        """Test PDF content extraction with validation failure."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        content = "This is extracted PDF content with more than 50 characters for validation."
        
        mock_pdf_handler = Mock()
        mock_pdf_handler.extract_text_from_open_document.return_value = content
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler', return_value=mock_pdf_handler):
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=None):
                    result = handler._extract_pdf_content()
        
        assert result is None
    
    def test_fallback_to_vision_success(self, handler):
        """Test successful vision fallback."""
        # Mock required modules
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
                            with patch.object(handler, '_extract_and_validate_answer', return_value="This is the answer"):
                                result = handler._fallback_to_vision("what's on my screen", "fast_path_failed")
        
        assert result["status"] == "success"
        assert result["message"] == "This is the answer"
        assert result["method"] == "vision_fallback"
        assert result["fallback_reason"] == "fast_path_failed"
        mock_audio.speak.assert_called_once_with("This is the answer")
    
    def test_fallback_to_vision_module_unavailable(self, handler):
        """Test vision fallback when vision module is unavailable."""
        with patch.object(handler, '_get_module_safely', return_value=None):
            result = handler._fallback_to_vision("what's on my screen", "fast_path_failed")
        
        assert result["status"] == "error"
        assert "trouble analyzing" in result["message"]
        assert result["method"] == "vision_fallback"
        assert result["error_type"] == "module_unavailable"
    
    def test_fallback_to_vision_screen_analysis_failure(self, handler):
        """Test vision fallback when screen analysis fails."""
        mock_vision = Mock()
        mock_reasoning = Mock()
        
        with patch.object(handler, '_get_module_safely') as mock_get_module:
            mock_get_module.side_effect = lambda name: {
                'vision_module': mock_vision,
                'reasoning_module': mock_reasoning,
                'audio_module': Mock()
            }.get(name)
            
            with patch.object(handler, '_determine_analysis_type_for_question', return_value="simple"):
                with patch.object(handler, '_analyze_screen_for_information', return_value=None):
                    result = handler._fallback_to_vision("what's on my screen", "fast_path_failed")
        
        assert result["status"] == "error"
        assert "couldn't analyze" in result["message"]
        assert result["error_type"] == "screen_analysis_failed"
    
    def test_fallback_to_vision_reasoning_failure(self, handler):
        """Test vision fallback when reasoning fails."""
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
                        with patch.object(handler, '_get_qa_action_plan', return_value=None):
                            result = handler._fallback_to_vision("what's on my screen", "fast_path_failed")
        
        assert result["status"] == "error"
        assert "couldn't process" in result["message"]
        assert result["error_type"] == "reasoning_failed"
    
    def test_fallback_to_vision_exception_handling(self, handler):
        """Test vision fallback exception handling."""
        # Mock the first call to succeed but later calls to fail
        def mock_get_module(name):
            if name == 'vision_module':
                raise Exception("Test error")
            return Mock()
        
        with patch.object(handler, '_get_module_safely', side_effect=mock_get_module):
            result = handler._fallback_to_vision("what's on my screen", "fast_path_failed")
        
        assert result["status"] == "error"
        assert "encountered an error" in result["message"]
        assert result["error_type"] == "exception"
    
    def test_detect_active_application_success(self, handler, sample_app_info):
        """Test successful application detection."""
        handler._application_detector = Mock()
        handler._application_detector.get_active_application_info.return_value = sample_app_info
        
        result = handler._detect_active_application()
        
        assert result == sample_app_info
        handler._application_detector.get_active_application_info.assert_called_once()
    
    def test_detect_active_application_failure(self, handler):
        """Test application detection failure."""
        handler._application_detector = Mock()
        handler._application_detector.get_active_application_info.return_value = None
        
        result = handler._detect_active_application()
        
        assert result is None
    
    def test_detect_active_application_exception(self, handler):
        """Test application detection exception handling."""
        handler._application_detector = Mock()
        handler._application_detector.get_active_application_info.side_effect = Exception("Test error")
        
        result = handler._detect_active_application()
        
        assert result is None
    
    def test_is_supported_application_browser(self, handler):
        """Test supported application detection for browsers."""
        app_info = Mock()
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        result = handler._is_supported_application(app_info)
        
        assert result is True
    
    def test_is_supported_application_pdf_reader(self, handler):
        """Test supported application detection for PDF readers."""
        app_info = Mock()
        app_info.app_type = ApplicationType.PDF_READER
        
        result = handler._is_supported_application(app_info)
        
        assert result is True
    
    def test_is_supported_application_unsupported(self, handler):
        """Test supported application detection for unsupported apps."""
        app_info = Mock()
        app_info.app_type = ApplicationType.NATIVE_APP
        
        result = handler._is_supported_application(app_info)
        
        assert result is False
    
    def test_get_extraction_method_browser(self, handler):
        """Test extraction method determination for browsers."""
        app_info = Mock()
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        result = handler._get_extraction_method(app_info)
        
        assert result == "browser"
    
    def test_get_extraction_method_pdf_reader(self, handler):
        """Test extraction method determination for PDF readers."""
        app_info = Mock()
        app_info.app_type = ApplicationType.PDF_READER
        
        result = handler._get_extraction_method(app_info)
        
        assert result == "pdf"
    
    def test_get_extraction_method_unsupported(self, handler):
        """Test extraction method determination for unsupported apps."""
        app_info = Mock()
        app_info.app_type = ApplicationType.NATIVE_APP
        
        result = handler._get_extraction_method(app_info)
        
        assert result is None
    
    def test_performance_tracking(self, handler):
        """Test performance tracking metrics."""
        # Initial state
        assert handler._fast_path_attempts == 0
        assert handler._fast_path_successes == 0
        assert handler._fallback_count == 0
        
        # Simulate successful fast path through handle method
        with patch.object(handler, '_try_fast_path_with_reason') as mock_fast_path:
            mock_fast_path.return_value = ("summary", "")
            with patch.object(handler, '_speak_result'):
                result = handler.handle("what's on my screen", {"intent": {"intent": "question_answering"}})
        
        assert result["status"] == "success"
        assert handler._fast_path_successes == 1
        assert handler._fallback_count == 0
        
        # Simulate failed fast path (fallback)
        with patch.object(handler, '_try_fast_path_with_reason') as mock_fast_path:
            mock_fast_path.return_value = (None, "failed")
            with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                mock_fallback.return_value = {"status": "success", "method": "vision_fallback"}
                handler.handle("what's on my screen", {"intent": {"intent": "question_answering"}})
        
        assert handler._fast_path_successes == 1
        assert handler._fallback_count == 1
    
    def test_fallback_reason_tracking(self, handler):
        """Test fallback reason tracking and logging."""
        # Test different fallback reasons
        reasons = ["application_detection_failed", "unsupported_application", "extraction_failed"]
        
        for reason in reasons:
            handler._log_fallback_reason(reason)
        
        # Check that reasons are tracked
        assert hasattr(handler, '_fallback_reasons')
        assert handler._fallback_reasons["application_detection_failed"] == 1
        assert handler._fallback_reasons["unsupported_application"] == 1
        assert handler._fallback_reasons["extraction_failed"] == 1
    
    def test_determine_fallback_reason(self, handler):
        """Test fallback reason determination."""
        # Set a specific reason
        handler._last_fallback_reason = "test_reason"
        
        reason = handler._determine_fallback_reason()
        
        assert reason == "test_reason"
        # Should reset after retrieval
        assert handler._determine_fallback_reason() == "unknown"
    
    def test_speak_result(self, handler):
        """Test speaking result to user."""
        handler._audio_module = Mock()
        
        with patch.object(handler, '_format_result_for_speech', return_value="Test message"):
            handler._speak_result("Test message")
        
        handler._audio_module.text_to_speech.assert_called_once_with("Test message")
    
    def test_speak_result_no_audio_module(self, handler):
        """Test speaking result when audio module is unavailable."""
        handler._audio_module = None
        
        # Should not raise exception
        handler._speak_result("Test message")
    
    def test_speak_result_audio_exception(self, handler):
        """Test speaking result when audio module raises exception."""
        handler._audio_module = Mock()
        handler._audio_module.text_to_speech.side_effect = Exception("Audio error")
        
        with patch.object(handler, '_format_result_for_speech', return_value="Test message"):
            # Should not raise exception
            handler._speak_result("Test message")


class TestQuestionAnsweringHandlerPerformance:
    """Performance-specific tests for QuestionAnsweringHandler."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for performance testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_fast_path_performance_under_5_seconds(self, handler):
        """Test that fast path completes within 5 seconds."""
        app_info = Mock()
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch.object(handler, '_is_supported_application', return_value=True):
                with patch.object(handler, '_get_extraction_method', return_value="browser"):
                    with patch.object(handler, '_extract_browser_content', return_value="content"):
                        with patch.object(handler, '_process_content_for_summarization', return_value="content"):
                            with patch.object(handler, '_summarize_content', return_value="summary"):
                                result = handler._try_fast_path("what's on my screen")
        
        execution_time = time.time() - start_time
        
        assert result == "summary"
        assert execution_time < 5.0  # Should complete in under 5 seconds
    
    def test_browser_extraction_timeout_2_seconds(self, handler):
        """Test that browser extraction times out after 2 seconds."""
        app_info = Mock()
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        # Mock slow extraction
        def slow_extraction(*args):
            time.sleep(2.5)  # Longer than timeout
            return "content"
        
        mock_browser_handler = Mock()
        mock_browser_handler.get_page_text_content.side_effect = slow_extraction
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler', return_value=mock_browser_handler):
                result = handler._extract_browser_content()
        
        execution_time = time.time() - start_time
        
        assert result is None
        assert execution_time < 3.0  # Should timeout before 3 seconds
        assert handler._last_fallback_reason == "browser_extraction_timeout"
    
    def test_pdf_extraction_timeout_2_seconds(self, handler):
        """Test that PDF extraction times out after 2 seconds."""
        app_info = Mock()
        app_info.app_type = ApplicationType.PDF_READER
        
        # Mock slow extraction
        def slow_extraction(*args):
            time.sleep(2.5)  # Longer than timeout
            return "content"
        
        mock_pdf_handler = Mock()
        mock_pdf_handler.extract_text_from_open_document.side_effect = slow_extraction
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler', return_value=mock_pdf_handler):
                result = handler._extract_pdf_content()
        
        execution_time = time.time() - start_time
        
        assert result is None
        assert execution_time < 3.0  # Should timeout before 3 seconds
        assert handler._last_fallback_reason == "pdf_extraction_timeout"
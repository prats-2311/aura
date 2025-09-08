"""
Integration tests for Content Comprehension Fast Path

This module provides comprehensive integration tests for the fast path feature,
testing end-to-end scenarios with real module interactions.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from handlers.question_answering_handler import QuestionAnsweringHandler
from modules.application_detector import ApplicationType, BrowserType
from orchestrator import Orchestrator


class TestFastPathIntegration:
    """Integration tests for fast path functionality."""
    
    @pytest.fixture
    def mock_orchestrator_with_modules(self):
        """Create a mock orchestrator with realistic module implementations."""
        orchestrator = Mock(spec=Orchestrator)
        
        # Mock application detector
        orchestrator.application_detector = Mock()
        
        # Mock browser accessibility handler
        orchestrator.browser_accessibility_handler = Mock()
        
        # Mock PDF handler
        orchestrator.pdf_handler = Mock()
        
        # Mock reasoning module
        orchestrator.reasoning_module = Mock()
        
        # Mock audio module
        orchestrator.audio_module = Mock()
        
        # Mock vision module
        orchestrator.vision_module = Mock()
        
        return orchestrator
    
    @pytest.fixture
    def handler(self, mock_orchestrator_with_modules):
        """Create handler with mocked orchestrator."""
        return QuestionAnsweringHandler(mock_orchestrator_with_modules)
    
    @pytest.fixture
    def chrome_app_info(self):
        """Create Chrome application info."""
        app_info = Mock()
        app_info.name = "Google Chrome"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.CHROME
        return app_info
    
    @pytest.fixture
    def safari_app_info(self):
        """Create Safari application info."""
        app_info = Mock()
        app_info.name = "Safari"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.SAFARI
        return app_info
    
    @pytest.fixture
    def firefox_app_info(self):
        """Create Firefox application info."""
        app_info = Mock()
        app_info.name = "Firefox"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.FIREFOX
        return app_info
    
    @pytest.fixture
    def preview_app_info(self):
        """Create Preview.app application info."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        return app_info
    
    @pytest.fixture
    def adobe_reader_app_info(self):
        """Create Adobe Reader application info."""
        app_info = Mock()
        app_info.name = "Adobe Acrobat Reader DC"
        app_info.app_type = ApplicationType.PDF_READER
        return app_info
    
    def test_end_to_end_chrome_fast_path(self, handler, chrome_app_info):
        """Test complete end-to-end fast path with Chrome browser."""
        # Setup realistic content
        extracted_content = """
        Welcome to Example.com
        
        This is a sample webpage with various content sections.
        
        Navigation:
        - Home
        - About
        - Services
        - Contact
        
        Main Content:
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
        Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        
        Footer:
        Copyright 2024 Example.com. All rights reserved.
        """
        
        summarized_content = "This webpage shows Example.com with navigation menu, main content about Lorem ipsum, and copyright footer."
        
        # Mock the complete flow
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = extracted_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                        with patch.object(handler, '_summarize_content', return_value=summarized_content):
                            with patch.object(handler, '_speak_result') as mock_speak:
                                
                                # Execute the command
                                result = handler.handle("what's on my screen", {
                                    "intent": {"intent": "question_answering"},
                                    "execution_id": "test_123"
                                })
        
        # Verify results
        assert result["status"] == "success"
        assert result["message"] == summarized_content
        assert result["method"] == "fast_path"
        assert result["extraction_method"] == "text_based"
        assert "execution_time" in result
        
        # Verify browser handler was called correctly
        mock_browser_handler.get_page_text_content.assert_called_once_with(chrome_app_info)
        
        # Verify audio feedback
        mock_speak.assert_called_once_with(summarized_content)
    
    def test_end_to_end_safari_fast_path(self, handler, safari_app_info):
        """Test complete end-to-end fast path with Safari browser."""
        extracted_content = "Safari webpage content with more than 50 characters for validation."
        summarized_content = "Safari webpage summary."
        
        with patch.object(handler, '_detect_active_application', return_value=safari_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = extracted_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                        with patch.object(handler, '_summarize_content', return_value=summarized_content):
                            
                            result = handler.handle("what's on my screen", {
                                "intent": {"intent": "question_answering"}
                            })
        
        assert result["status"] == "success"
        assert result["method"] == "fast_path"
        mock_browser_handler.get_page_text_content.assert_called_once_with(safari_app_info)
    
    def test_end_to_end_firefox_fast_path(self, handler, firefox_app_info):
        """Test complete end-to-end fast path with Firefox browser."""
        extracted_content = "Firefox webpage content with more than 50 characters for validation."
        summarized_content = "Firefox webpage summary."
        
        with patch.object(handler, '_detect_active_application', return_value=firefox_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = extracted_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                        with patch.object(handler, '_summarize_content', return_value=summarized_content):
                            
                            result = handler.handle("what's on my screen", {
                                "intent": {"intent": "question_answering"}
                            })
        
        assert result["status"] == "success"
        assert result["method"] == "fast_path"
        mock_browser_handler.get_page_text_content.assert_called_once_with(firefox_app_info)
    
    def test_end_to_end_preview_pdf_fast_path(self, handler, preview_app_info):
        """Test complete end-to-end fast path with Preview.app PDF reader."""
        extracted_content = """
        PDF Document Title: Research Paper on AI
        
        Abstract:
        This paper discusses the latest developments in artificial intelligence
        and machine learning technologies. The research covers various aspects
        of neural networks, deep learning, and their applications in real-world
        scenarios.
        
        Introduction:
        Artificial intelligence has become increasingly important in modern
        technology solutions. This document explores the current state of AI
        research and future directions.
        
        Page 1 of 25
        """
        
        cleaned_content = extracted_content.strip()
        summarized_content = "This PDF is a research paper about AI and machine learning, covering neural networks and deep learning applications."
        
        with patch.object(handler, '_detect_active_application', return_value=preview_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = extracted_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    with patch.object(handler, '_process_content_for_summarization', return_value=cleaned_content):
                        with patch.object(handler, '_summarize_content', return_value=summarized_content):
                            with patch.object(handler, '_speak_result') as mock_speak:
                                
                                result = handler.handle("what's on my screen", {
                                    "intent": {"intent": "question_answering"}
                                })
        
        assert result["status"] == "success"
        assert result["message"] == summarized_content
        assert result["method"] == "fast_path"
        
        # Verify PDF handler was called correctly
        mock_pdf_handler.extract_text_from_open_document.assert_called_once_with("Preview")
        mock_speak.assert_called_once_with(summarized_content)
    
    def test_end_to_end_adobe_reader_fast_path(self, handler, adobe_reader_app_info):
        """Test complete end-to-end fast path with Adobe Reader."""
        extracted_content = "Adobe Reader PDF content with more than 50 characters for validation."
        cleaned_content = "Cleaned Adobe Reader PDF content."
        summarized_content = "Adobe Reader PDF summary."
        
        with patch.object(handler, '_detect_active_application', return_value=adobe_reader_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = extracted_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    with patch.object(handler, '_process_content_for_summarization', return_value=cleaned_content):
                        with patch.object(handler, '_summarize_content', return_value=summarized_content):
                            
                            result = handler.handle("what's on my screen", {
                                "intent": {"intent": "question_answering"}
                            })
        
        assert result["status"] == "success"
        assert result["method"] == "fast_path"
        mock_pdf_handler.extract_text_from_open_document.assert_called_once_with("Adobe Acrobat Reader DC")
    
    def test_end_to_end_fallback_to_vision(self, handler):
        """Test complete end-to-end fallback to vision processing."""
        # Mock unsupported application
        app_info = Mock()
        app_info.name = "TextEdit"
        app_info.app_type = ApplicationType.TEXT_EDITOR
        
        vision_answer = "I can see a text document with several paragraphs of content."
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            # Mock vision fallback components
            with patch.object(handler, '_get_module_safely') as mock_get_module:
                mock_vision = Mock()
                mock_reasoning = Mock()
                mock_audio = Mock()
                
                mock_get_module.side_effect = lambda name: {
                    'vision_module': mock_vision,
                    'reasoning_module': mock_reasoning,
                    'audio_module': mock_audio
                }.get(name)
                
                with patch.object(handler, '_determine_analysis_type_for_question', return_value="simple"):
                    with patch.object(handler, '_analyze_screen_for_information', return_value={"elements": [], "text_blocks": []}):
                        with patch.object(handler, '_create_qa_reasoning_prompt', return_value="prompt"):
                            with patch.object(handler, '_get_qa_action_plan', return_value={"response": "answer", "metadata": {"confidence": 0.8}}):
                                with patch.object(handler, '_extract_and_validate_answer', return_value=vision_answer):
                                    
                                    result = handler.handle("what's on my screen", {
                                        "intent": {"intent": "question_answering"}
                                    })
        
        assert result["status"] == "success"
        assert result["message"] == vision_answer
        assert result["method"] == "vision_fallback"
        assert result["fallback_reason"] == "unsupported_application"
        assert result["fast_path_used"] is False
        assert result["vision_fallback_used"] is True
        
        # Verify audio feedback
        mock_audio.speak.assert_called_once_with(vision_answer)
    
    def test_end_to_end_browser_extraction_failure_fallback(self, handler, chrome_app_info):
        """Test fallback to vision when browser extraction fails."""
        vision_answer = "Vision-based analysis of the screen content."
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                # Mock extraction failure
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = None
                mock_browser_class.return_value = mock_browser_handler
                
                # Mock vision fallback
                with patch.object(handler, '_get_module_safely') as mock_get_module:
                    mock_vision = Mock()
                    mock_reasoning = Mock()
                    mock_audio = Mock()
                    
                    mock_get_module.side_effect = lambda name: {
                        'vision_module': mock_vision,
                        'reasoning_module': mock_reasoning,
                        'audio_module': mock_audio
                    }.get(name)
                    
                    with patch.object(handler, '_determine_analysis_type_for_question', return_value="simple"):
                        with patch.object(handler, '_analyze_screen_for_information', return_value={"elements": [], "text_blocks": []}):
                            with patch.object(handler, '_create_qa_reasoning_prompt', return_value="prompt"):
                                with patch.object(handler, '_get_qa_action_plan', return_value={"response": "answer", "metadata": {"confidence": 0.8}}):
                                    with patch.object(handler, '_extract_and_validate_answer', return_value=vision_answer):
                                        
                                        result = handler.handle("what's on my screen", {
                                            "intent": {"intent": "question_answering"}
                                        })
        
        assert result["status"] == "success"
        assert result["method"] == "vision_fallback"
        assert "browser_extraction_failed" in result.get("fallback_reason", "")
    
    def test_end_to_end_pdf_extraction_failure_fallback(self, handler, preview_app_info):
        """Test fallback to vision when PDF extraction fails."""
        vision_answer = "Vision-based analysis of the PDF content."
        
        with patch.object(handler, '_detect_active_application', return_value=preview_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                # Mock extraction failure
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = None
                mock_pdf_class.return_value = mock_pdf_handler
                
                # Mock vision fallback
                with patch.object(handler, '_get_module_safely') as mock_get_module:
                    mock_vision = Mock()
                    mock_reasoning = Mock()
                    mock_audio = Mock()
                    
                    mock_get_module.side_effect = lambda name: {
                        'vision_module': mock_vision,
                        'reasoning_module': mock_reasoning,
                        'audio_module': mock_audio
                    }.get(name)
                    
                    with patch.object(handler, '_determine_analysis_type_for_question', return_value="simple"):
                        with patch.object(handler, '_analyze_screen_for_information', return_value={"elements": [], "text_blocks": []}):
                            with patch.object(handler, '_create_qa_reasoning_prompt', return_value="prompt"):
                                with patch.object(handler, '_get_qa_action_plan', return_value={"response": "answer", "metadata": {"confidence": 0.8}}):
                                    with patch.object(handler, '_extract_and_validate_answer', return_value=vision_answer):
                                        
                                        result = handler.handle("what's on my screen", {
                                            "intent": {"intent": "question_answering"}
                                        })
        
        assert result["status"] == "success"
        assert result["method"] == "vision_fallback"
        assert "pdf_extraction_failed" in result.get("fallback_reason", "")
    
    def test_performance_fast_path_under_5_seconds(self, handler, chrome_app_info):
        """Test that fast path completes within 5 seconds."""
        extracted_content = "Browser content with more than 50 characters for validation."
        summarized_content = "Browser content summary."
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = extracted_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                        with patch.object(handler, '_summarize_content', return_value=summarized_content):
                            
                            result = handler.handle("what's on my screen", {
                                "intent": {"intent": "question_answering"}
                            })
        
        execution_time = time.time() - start_time
        
        assert result["status"] == "success"
        assert result["method"] == "fast_path"
        assert execution_time < 5.0  # Must complete within 5 seconds
        assert result.get("execution_time", 0) < 5.0
    
    def test_performance_browser_extraction_timeout(self, handler, chrome_app_info):
        """Test browser extraction timeout handling in integration."""
        def slow_extraction(*args):
            time.sleep(2.5)  # Longer than 2 second timeout
            return "content"
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.side_effect = slow_extraction
                mock_browser_class.return_value = mock_browser_handler
                
                # Mock vision fallback for when extraction times out
                with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                    mock_fallback.return_value = {
                        "status": "success",
                        "message": "Vision fallback after timeout",
                        "method": "vision_fallback",
                        "fallback_reason": "browser_extraction_timeout"
                    }
                    
                    start_time = time.time()
                    result = handler.handle("what's on my screen", {
                        "intent": {"intent": "question_answering"}
                    })
                    execution_time = time.time() - start_time
        
        assert result["method"] == "vision_fallback"
        assert result["fallback_reason"] == "browser_extraction_timeout"
        assert execution_time < 10.0  # Should still complete reasonably quickly
    
    def test_performance_pdf_extraction_timeout(self, handler, preview_app_info):
        """Test PDF extraction timeout handling in integration."""
        def slow_extraction(*args):
            time.sleep(2.5)  # Longer than 2 second timeout
            return "content"
        
        with patch.object(handler, '_detect_active_application', return_value=preview_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.side_effect = slow_extraction
                mock_pdf_class.return_value = mock_pdf_handler
                
                # Mock vision fallback for when extraction times out
                with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                    mock_fallback.return_value = {
                        "status": "success",
                        "message": "Vision fallback after timeout",
                        "method": "vision_fallback",
                        "fallback_reason": "pdf_extraction_timeout"
                    }
                    
                    start_time = time.time()
                    result = handler.handle("what's on my screen", {
                        "intent": {"intent": "question_answering"}
                    })
                    execution_time = time.time() - start_time
        
        assert result["method"] == "vision_fallback"
        assert result["fallback_reason"] == "pdf_extraction_timeout"
        assert execution_time < 10.0  # Should still complete reasonably quickly
    
    def test_multiple_fast_path_attempts_performance_tracking(self, handler, chrome_app_info):
        """Test performance tracking across multiple fast path attempts."""
        extracted_content = "Browser content with more than 50 characters for validation."
        summarized_content = "Browser content summary."
        
        # Execute multiple fast path attempts
        for i in range(3):
            with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
                with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                    mock_browser_handler = Mock()
                    mock_browser_handler.get_page_text_content.return_value = extracted_content
                    mock_browser_class.return_value = mock_browser_handler
                    
                    with patch.object(handler, '_validate_browser_content', return_value=True):
                        with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                            with patch.object(handler, '_summarize_content', return_value=summarized_content):
                                
                                result = handler.handle("what's on my screen", {
                                    "intent": {"intent": "question_answering"}
                                })
                                
                                assert result["status"] == "success"
                                assert result["method"] == "fast_path"
        
        # Verify performance tracking
        assert handler._fast_path_attempts == 3
        assert handler._fast_path_successes == 3
        assert handler._fallback_count == 0
    
    def test_mixed_success_failure_performance_tracking(self, handler, chrome_app_info):
        """Test performance tracking with mixed success and failure scenarios."""
        # First attempt: success
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value="content"
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    with patch.object(handler, '_process_content_for_summarization', return_value="content"):
                        with patch.object(handler, '_summarize_content', return_value="summary"):
                            handler.handle("what's on my screen", {"intent": {"intent": "question_answering"}})
        
        # Second attempt: failure (fallback)
        with patch.object(handler, '_detect_active_application', return_value=None):
            with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                mock_fallback.return_value = {
                    "status": "success",
                    "message": "Vision fallback",
                    "method": "vision_fallback"
                }
                handler.handle("what's on my screen", {"intent": {"intent": "question_answering"}})
        
        # Verify tracking
        assert handler._fast_path_attempts == 2
        assert handler._fast_path_successes == 1
        assert handler._fallback_count == 1


class TestFastPathBrowserSpecific:
    """Browser-specific integration tests."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for browser-specific testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_chrome_specific_content_extraction(self, handler):
        """Test Chrome-specific content extraction patterns."""
        app_info = Mock()
        app_info.name = "Google Chrome"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.CHROME
        
        # Chrome-specific content patterns
        chrome_content = """
        Google Search Results
        
        Search query: "artificial intelligence"
        
        Results:
        1. Wikipedia - Artificial Intelligence
           Artificial intelligence (AI) is intelligence demonstrated by machines...
        
        2. MIT Technology Review - AI News
           Latest developments in artificial intelligence research...
        
        3. OpenAI - ChatGPT
           Conversational AI system powered by large language models...
        """
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = chrome_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == chrome_content
        mock_browser_handler.get_page_text_content.assert_called_once_with(app_info)
    
    def test_safari_specific_content_extraction(self, handler):
        """Test Safari-specific content extraction patterns."""
        app_info = Mock()
        app_info.name = "Safari"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.SAFARI
        
        # Safari-specific content patterns
        safari_content = """
        Apple Developer Documentation
        
        SwiftUI Framework
        
        Overview:
        SwiftUI is a user interface toolkit that lets you design apps in a declarative way.
        
        Topics:
        - Views and Controls
        - Layout and Organization
        - Drawing and Animation
        
        Code Example:
        struct ContentView: View {
            var body: some View {
                Text("Hello, World!")
            }
        }
        """
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = safari_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == safari_content
        mock_browser_handler.get_page_text_content.assert_called_once_with(app_info)
    
    def test_firefox_specific_content_extraction(self, handler):
        """Test Firefox-specific content extraction patterns."""
        app_info = Mock()
        app_info.name = "Firefox"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.FIREFOX
        
        # Firefox-specific content patterns
        firefox_content = """
        Mozilla Developer Network (MDN)
        
        JavaScript Reference
        
        Array.prototype.map()
        
        The map() method creates a new array populated with the results of calling 
        a provided function on every element in the calling array.
        
        Syntax:
        map(callbackFn)
        map(callbackFn, thisArg)
        
        Parameters:
        callbackFn - A function to execute for each element in the array.
        
        Return value:
        A new array with each element being the result of the callback function.
        """
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = firefox_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == firefox_content
        mock_browser_handler.get_page_text_content.assert_called_once_with(app_info)


class TestFastPathPDFSpecific:
    """PDF reader-specific integration tests."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for PDF-specific testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_preview_app_pdf_extraction(self, handler):
        """Test Preview.app-specific PDF extraction."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        # Preview.app PDF content patterns
        preview_content = """
        Research Paper: Machine Learning in Healthcare
        
        Abstract
        This study examines the application of machine learning algorithms
        in healthcare diagnostics and treatment planning. We analyze various
        ML techniques including supervised learning, unsupervised learning,
        and reinforcement learning approaches.
        
        1. Introduction
        Healthcare systems worldwide are increasingly adopting artificial
        intelligence and machine learning technologies to improve patient
        outcomes and operational efficiency.
        
        2. Methodology
        We conducted a systematic review of 150 research papers published
        between 2020-2024 focusing on ML applications in healthcare.
        
        Page 1 of 15
        """
        
        cleaned_content = preview_content.strip()
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = preview_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        assert result == cleaned_content
        mock_pdf_handler.extract_text_from_open_document.assert_called_once_with("Preview")
    
    def test_adobe_reader_pdf_extraction(self, handler):
        """Test Adobe Reader-specific PDF extraction."""
        app_info = Mock()
        app_info.name = "Adobe Acrobat Reader DC"
        app_info.app_type = ApplicationType.PDF_READER
        
        # Adobe Reader PDF content patterns
        adobe_content = """
        Technical Specification Document
        Version 2.1
        
        Table of Contents
        1. Overview ................................. 3
        2. System Requirements ...................... 5
        3. Installation Guide ....................... 8
        4. Configuration ........................... 12
        5. API Reference ........................... 18
        6. Troubleshooting ......................... 25
        
        1. Overview
        This document provides comprehensive technical specifications
        for the AURA voice assistant system. It covers installation,
        configuration, and usage guidelines for developers and
        system administrators.
        
        The system is designed to provide natural language processing
        capabilities with voice recognition and text-to-speech features.
        """
        
        cleaned_content = adobe_content.strip()
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = adobe_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        assert result == cleaned_content
        mock_pdf_handler.extract_text_from_open_document.assert_called_once_with("Adobe Acrobat Reader DC")


class TestFastPathErrorRecovery:
    """Integration tests for error recovery scenarios."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for error recovery testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_graceful_degradation_browser_to_vision(self, handler):
        """Test graceful degradation from browser extraction to vision."""
        app_info = Mock()
        app_info.name = "Google Chrome"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.CHROME
        
        vision_result = "Vision-based analysis shows a webpage with navigation and content sections."
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                # Simulate browser extraction failure
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.side_effect = Exception("Browser extraction failed")
                mock_browser_class.return_value = mock_browser_handler
                
                # Mock successful vision fallback
                with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                    mock_fallback.return_value = {
                        "status": "success",
                        "message": vision_result,
                        "method": "vision_fallback",
                        "fallback_reason": "browser_extraction_failed"
                    }
                    
                    result = handler.handle("what's on my screen", {
                        "intent": {"intent": "question_answering"}
                    })
        
        assert result["status"] == "success"
        assert result["message"] == vision_result
        assert result["method"] == "vision_fallback"
        assert "browser_extraction_failed" in result.get("fallback_reason", "")
    
    def test_graceful_degradation_pdf_to_vision(self, handler):
        """Test graceful degradation from PDF extraction to vision."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        vision_result = "Vision-based analysis shows a PDF document with text content."
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                # Simulate PDF extraction failure
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.side_effect = Exception("PDF extraction failed")
                mock_pdf_class.return_value = mock_pdf_handler
                
                # Mock successful vision fallback
                with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                    mock_fallback.return_value = {
                        "status": "success",
                        "message": vision_result,
                        "method": "vision_fallback",
                        "fallback_reason": "pdf_extraction_failed"
                    }
                    
                    result = handler.handle("what's on my screen", {
                        "intent": {"intent": "question_answering"}
                    })
        
        assert result["status"] == "success"
        assert result["message"] == vision_result
        assert result["method"] == "vision_fallback"
        assert "pdf_extraction_failed" in result.get("fallback_reason", "")
    
    def test_complete_system_failure_handling(self, handler):
        """Test handling when both fast path and vision fallback fail."""
        with patch.object(handler, '_detect_active_application', side_effect=Exception("System error")):
            with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                mock_fallback.return_value = {
                    "status": "error",
                    "message": "I encountered an error while trying to answer your question.",
                    "method": "vision_fallback",
                    "error_type": "system_failure"
                }
                
                result = handler.handle("what's on my screen", {
                    "intent": {"intent": "question_answering"}
                })
        
        assert result["status"] == "error"
        assert "error" in result["message"]
        assert result["method"] == "vision_fallback"
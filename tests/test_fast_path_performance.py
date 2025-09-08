"""
Performance tests for Content Comprehension Fast Path

This module provides comprehensive performance tests to validate the <5 second
response time requirement and other performance metrics.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from handlers.question_answering_handler import QuestionAnsweringHandler
from modules.application_detector import ApplicationType, BrowserType


class TestFastPathPerformanceRequirements:
    """Performance tests for fast path response time requirements."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for performance testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    @pytest.fixture
    def chrome_app_info(self):
        """Create Chrome application info."""
        app_info = Mock()
        app_info.name = "Google Chrome"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.CHROME
        return app_info
    
    @pytest.fixture
    def preview_app_info(self):
        """Create Preview.app application info."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        return app_info
    
    @pytest.mark.performance
    def test_end_to_end_browser_under_5_seconds(self, handler, chrome_app_info):
        """Test complete browser fast path execution under 5 seconds."""
        extracted_content = "Browser content with more than 50 characters for validation testing purposes."
        summarized_content = "Browser content summary for user."
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = extracted_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                        with patch.object(handler, '_summarize_content', return_value=summarized_content):
                            with patch.object(handler, '_speak_result'):
                                
                                result = handler.handle("what's on my screen", {
                                    "intent": {"intent": "question_answering"},
                                    "execution_id": "perf_test_001"
                                })
        
        execution_time = time.time() - start_time
        
        assert result["status"] == "success"
        assert result["method"] == "fast_path"
        assert execution_time < 5.0  # Must complete within 5 seconds
        assert result.get("execution_time", 0) < 5.0
        
        print(f"Browser fast path execution time: {execution_time:.3f}s")
    
    @pytest.mark.performance
    def test_end_to_end_pdf_under_5_seconds(self, handler, preview_app_info):
        """Test complete PDF fast path execution under 5 seconds."""
        extracted_content = "PDF content with more than 50 characters for validation testing purposes."
        cleaned_content = extracted_content.strip()
        summarized_content = "PDF content summary for user."
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=preview_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = extracted_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    with patch.object(handler, '_process_content_for_summarization', return_value=cleaned_content):
                        with patch.object(handler, '_summarize_content', return_value=summarized_content):
                            with patch.object(handler, '_speak_result'):
                                
                                result = handler.handle("what's on my screen", {
                                    "intent": {"intent": "question_answering"},
                                    "execution_id": "perf_test_002"
                                })
        
        execution_time = time.time() - start_time
        
        assert result["status"] == "success"
        assert result["method"] == "fast_path"
        assert execution_time < 5.0  # Must complete within 5 seconds
        assert result.get("execution_time", 0) < 5.0
        
        print(f"PDF fast path execution time: {execution_time:.3f}s")
    
    @pytest.mark.performance
    def test_browser_extraction_under_2_seconds(self, handler, chrome_app_info):
        """Test browser content extraction completes within 2 seconds."""
        content = "Browser content with more than 50 characters for validation testing."
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        execution_time = time.time() - start_time
        
        assert result == content
        assert execution_time < 2.0  # Must complete within 2 seconds
        
        print(f"Browser extraction time: {execution_time:.3f}s")
    
    @pytest.mark.performance
    def test_pdf_extraction_under_2_seconds(self, handler, preview_app_info):
        """Test PDF content extraction completes within 2 seconds."""
        content = "PDF content with more than 50 characters for validation testing."
        cleaned_content = content.strip()
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=preview_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        execution_time = time.time() - start_time
        
        assert result == cleaned_content
        assert execution_time < 2.0  # Must complete within 2 seconds
        
        print(f"PDF extraction time: {execution_time:.3f}s")
    
    @pytest.mark.performance
    def test_summarization_under_3_seconds(self, handler):
        """Test content summarization completes within 3 seconds."""
        content = "This is a long piece of content that needs to be summarized. " * 50  # ~3KB content
        command = "what's on my screen"
        summarized_result = "This is a summarized version of the content."
        
        # Mock reasoning module
        mock_reasoning = Mock()
        mock_reasoning.generate_action_plan.return_value = {
            "response": summarized_result,
            "metadata": {"confidence": 0.9}
        }
        
        start_time = time.time()
        
        with patch.object(handler, '_get_module_safely', return_value=mock_reasoning):
            result = handler._summarize_content(content, command)
        
        execution_time = time.time() - start_time
        
        assert result == summarized_result
        assert execution_time < 3.0  # Must complete within 3 seconds
        
        print(f"Summarization time: {execution_time:.3f}s")
    
    @pytest.mark.performance
    def test_application_detection_under_1_second(self, handler, chrome_app_info):
        """Test application detection completes within 1 second."""
        # Mock application detector
        handler._application_detector = Mock()
        handler._application_detector.detect_application_type.return_value = chrome_app_info
        
        start_time = time.time()
        
        result = handler._detect_active_application()
        
        execution_time = time.time() - start_time
        
        assert result == chrome_app_info
        assert execution_time < 1.0  # Must complete within 1 second
        
        print(f"Application detection time: {execution_time:.3f}s")
    
    @pytest.mark.performance
    def test_multiple_consecutive_requests_performance(self, handler, chrome_app_info):
        """Test performance consistency across multiple consecutive requests."""
        extracted_content = "Browser content with more than 50 characters for validation testing."
        summarized_content = "Browser content summary."
        
        execution_times = []
        
        for i in range(5):  # Test 5 consecutive requests
            start_time = time.time()
            
            with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
                with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                    mock_browser_handler = Mock()
                    mock_browser_handler.get_page_text_content.return_value = extracted_content
                    mock_browser_class.return_value = mock_browser_handler
                    
                    with patch.object(handler, '_validate_browser_content', return_value=True):
                        with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                            with patch.object(handler, '_summarize_content', return_value=summarized_content):
                                with patch.object(handler, '_speak_result'):
                                    
                                    result = handler.handle("what's on my screen", {
                                        "intent": {"intent": "question_answering"},
                                        "execution_id": f"perf_test_multi_{i}"
                                    })
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            assert result["status"] == "success"
            assert result["method"] == "fast_path"
            assert execution_time < 5.0  # Each request must be under 5 seconds
        
        # Check consistency - no request should be significantly slower
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        print(f"Multiple requests - Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s")
        
        # Maximum time should not be more than 2x the average (consistency check)
        assert max_time < avg_time * 2.0
        assert avg_time < 3.0  # Average should be well under the 5 second limit


class TestTimeoutHandling:
    """Tests for timeout handling and performance boundaries."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for timeout testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    @pytest.fixture
    def chrome_app_info(self):
        """Create Chrome application info."""
        app_info = Mock()
        app_info.name = "Google Chrome"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.CHROME
        return app_info
    
    @pytest.fixture
    def preview_app_info(self):
        """Create Preview.app application info."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        return app_info
    
    @pytest.mark.performance
    def test_browser_extraction_timeout_2_seconds(self, handler, chrome_app_info):
        """Test browser extraction timeout after 2 seconds."""
        def slow_extraction(*args):
            time.sleep(2.5)  # Longer than 2 second timeout
            return "content"
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.side_effect = slow_extraction
                mock_browser_class.return_value = mock_browser_handler
                
                result = handler._extract_browser_content()
        
        execution_time = time.time() - start_time
        
        assert result is None
        assert execution_time < 3.0  # Should timeout before 3 seconds
        assert execution_time >= 2.0  # Should wait at least 2 seconds
        assert handler._last_fallback_reason == "browser_extraction_timeout"
        
        print(f"Browser extraction timeout after: {execution_time:.3f}s")
    
    @pytest.mark.performance
    def test_pdf_extraction_timeout_2_seconds(self, handler, preview_app_info):
        """Test PDF extraction timeout after 2 seconds."""
        def slow_extraction(*args):
            time.sleep(2.5)  # Longer than 2 second timeout
            return "content"
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=preview_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.side_effect = slow_extraction
                mock_pdf_class.return_value = mock_pdf_handler
                
                result = handler._extract_pdf_content()
        
        execution_time = time.time() - start_time
        
        assert result is None
        assert execution_time < 3.0  # Should timeout before 3 seconds
        assert execution_time >= 2.0  # Should wait at least 2 seconds
        assert handler._last_fallback_reason == "pdf_extraction_timeout"
        
        print(f"PDF extraction timeout after: {execution_time:.3f}s")
    
    @pytest.mark.performance
    def test_summarization_timeout_3_seconds(self, handler):
        """Test summarization timeout after 3 seconds."""
        content = "Content to be summarized."
        command = "what's on my screen"
        
        def slow_summarization(*args, **kwargs):
            time.sleep(3.5)  # Longer than 3 second timeout
            return {"response": "summary", "metadata": {"confidence": 0.9}}
        
        mock_reasoning = Mock()
        mock_reasoning.generate_action_plan.side_effect = slow_summarization
        
        start_time = time.time()
        
        with patch.object(handler, '_get_module_safely', return_value=mock_reasoning):
            result = handler._summarize_content(content, command)
        
        execution_time = time.time() - start_time
        
        # Should return None or fallback content due to timeout
        # The exact behavior depends on implementation
        assert execution_time < 4.0  # Should timeout before 4 seconds
        
        print(f"Summarization timeout after: {execution_time:.3f}s")
    
    @pytest.mark.performance
    def test_fast_path_timeout_fallback_to_vision(self, handler, chrome_app_info):
        """Test fast path timeout triggers fallback to vision within reasonable time."""
        def slow_extraction(*args):
            time.sleep(2.5)  # Causes timeout
            return "content"
        
        vision_result = "Vision fallback result"
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.side_effect = slow_extraction
                mock_browser_class.return_value = mock_browser_handler
                
                # Mock vision fallback
                with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                    mock_fallback.return_value = {
                        "status": "success",
                        "message": vision_result,
                        "method": "vision_fallback",
                        "fallback_reason": "browser_extraction_timeout"
                    }
                    
                    result = handler.handle("what's on my screen", {
                        "intent": {"intent": "question_answering"}
                    })
        
        execution_time = time.time() - start_time
        
        assert result["status"] == "success"
        assert result["method"] == "vision_fallback"
        assert result["fallback_reason"] == "browser_extraction_timeout"
        assert execution_time < 10.0  # Total time should still be reasonable
        
        print(f"Fast path timeout + vision fallback time: {execution_time:.3f}s")


class TestPerformanceUnderLoad:
    """Tests for performance under various load conditions."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for load testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    @pytest.fixture
    def chrome_app_info(self):
        """Create Chrome application info."""
        app_info = Mock()
        app_info.name = "Google Chrome"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.CHROME
        return app_info
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_requests_performance(self, handler, chrome_app_info):
        """Test performance with concurrent requests (simulating multiple users)."""
        extracted_content = "Browser content with more than 50 characters for validation testing."
        summarized_content = "Browser content summary."
        
        results = []
        execution_times = []
        
        def execute_request(request_id):
            start_time = time.time()
            
            with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
                with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                    mock_browser_handler = Mock()
                    mock_browser_handler.get_page_text_content.return_value = extracted_content
                    mock_browser_class.return_value = mock_browser_handler
                    
                    with patch.object(handler, '_validate_browser_content', return_value=True):
                        with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                            with patch.object(handler, '_summarize_content', return_value=summarized_content):
                                with patch.object(handler, '_speak_result'):
                                    
                                    result = handler.handle("what's on my screen", {
                                        "intent": {"intent": "question_answering"},
                                        "execution_id": f"concurrent_test_{request_id}"
                                    })
            
            execution_time = time.time() - start_time
            results.append((request_id, result, execution_time))
            execution_times.append(execution_time)
        
        # Execute 3 concurrent requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=execute_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout for safety
        
        # Verify all requests completed successfully
        assert len(results) == 3
        
        for request_id, result, execution_time in results:
            assert result["status"] == "success"
            assert result["method"] == "fast_path"
            assert execution_time < 5.0  # Each request should still be under 5 seconds
        
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        
        print(f"Concurrent requests - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
        
        # Performance should not degrade significantly under concurrent load
        assert max_time < 6.0  # Allow slight degradation but still reasonable
    
    @pytest.mark.performance
    def test_large_content_processing_performance(self, handler, chrome_app_info):
        """Test performance with large content (near 50KB limit)."""
        # Create large content (approximately 50KB)
        large_content = "This is a large piece of content that simulates a very long webpage or document. " * 600  # ~50KB
        summarized_content = "This is a summary of the large content."
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = large_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    with patch.object(handler, '_process_content_for_summarization', return_value=large_content):
                        with patch.object(handler, '_summarize_content', return_value=summarized_content):
                            with patch.object(handler, '_speak_result'):
                                
                                result = handler.handle("what's on my screen", {
                                    "intent": {"intent": "question_answering"},
                                    "execution_id": "large_content_test"
                                })
        
        execution_time = time.time() - start_time
        
        assert result["status"] == "success"
        assert result["method"] == "fast_path"
        assert execution_time < 7.0  # Allow extra time for large content but still reasonable
        
        print(f"Large content processing time: {execution_time:.3f}s (content size: {len(large_content)} chars)")
    
    @pytest.mark.performance
    def test_memory_usage_during_processing(self, handler, chrome_app_info):
        """Test that memory usage remains reasonable during processing."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process multiple requests to check for memory leaks
        extracted_content = "Browser content with more than 50 characters for validation testing."
        summarized_content = "Browser content summary."
        
        for i in range(10):  # Process 10 requests
            with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
                with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                    mock_browser_handler = Mock()
                    mock_browser_handler.get_page_text_content.return_value = extracted_content
                    mock_browser_class.return_value = mock_browser_handler
                    
                    with patch.object(handler, '_validate_browser_content', return_value=True):
                        with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                            with patch.object(handler, '_summarize_content', return_value=summarized_content):
                                with patch.object(handler, '_speak_result'):
                                    
                                    result = handler.handle("what's on my screen", {
                                        "intent": {"intent": "question_answering"},
                                        "execution_id": f"memory_test_{i}"
                                    })
                                    
                                    assert result["status"] == "success"
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage - Initial: {initial_memory:.1f}MB, Final: {final_memory:.1f}MB, Increase: {memory_increase:.1f}MB")
        
        # Memory increase should be reasonable (less than 50MB for 10 requests)
        assert memory_increase < 50.0


class TestPerformanceMetrics:
    """Tests for performance metrics collection and reporting."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for metrics testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_performance_metrics_collection(self, handler):
        """Test that performance metrics are properly collected."""
        # Initial state
        assert handler._fast_path_attempts == 0
        assert handler._fast_path_successes == 0
        assert handler._fallback_count == 0
        
        # Simulate successful fast path
        app_info = Mock()
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch.object(handler, '_is_supported_application', return_value=True):
                with patch.object(handler, '_get_extraction_method', return_value="browser"):
                    with patch.object(handler, '_extract_browser_content', return_value="content"):
                        with patch.object(handler, '_process_content_for_summarization', return_value="content"):
                            with patch.object(handler, '_summarize_content', return_value="summary"):
                                result = handler._try_fast_path("what's on my screen")
        
        assert handler._fast_path_attempts == 1
        assert handler._fast_path_successes == 1
        assert handler._fallback_count == 0
        assert result == "summary"
        
        # Simulate failed fast path (fallback)
        with patch.object(handler, '_detect_active_application', return_value=None):
            with patch.object(handler, '_fallback_to_vision') as mock_fallback:
                mock_fallback.return_value = {"status": "success", "method": "vision_fallback"}
                handler.handle("what's on my screen", {"intent": {"intent": "question_answering"}})
        
        assert handler._fast_path_attempts == 2
        assert handler._fast_path_successes == 1
        assert handler._fallback_count == 1
    
    def test_success_rate_calculation(self, handler):
        """Test success rate calculation for performance monitoring."""
        # Simulate mixed success/failure scenarios
        app_info = Mock()
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        # 3 successful attempts
        for i in range(3):
            with patch.object(handler, '_detect_active_application', return_value=app_info):
                with patch.object(handler, '_is_supported_application', return_value=True):
                    with patch.object(handler, '_get_extraction_method', return_value="browser"):
                        with patch.object(handler, '_extract_browser_content', return_value="content"):
                            with patch.object(handler, '_process_content_for_summarization', return_value="content"):
                                with patch.object(handler, '_summarize_content', return_value="summary"):
                                    handler._try_fast_path("what's on my screen")
        
        # 2 failed attempts
        for i in range(2):
            with patch.object(handler, '_detect_active_application', return_value=None):
                handler._try_fast_path("what's on my screen")
        
        # Calculate success rate
        success_rate = handler._fast_path_successes / handler._fast_path_attempts if handler._fast_path_attempts > 0 else 0
        
        assert handler._fast_path_attempts == 5
        assert handler._fast_path_successes == 3
        assert success_rate == 0.6  # 60% success rate
        
        print(f"Fast path success rate: {success_rate:.1%}")
    
    def test_fallback_reason_tracking(self, handler):
        """Test tracking of different fallback reasons for performance analysis."""
        # Test different fallback scenarios
        fallback_scenarios = [
            "application_detection_failed",
            "unsupported_application", 
            "browser_extraction_timeout",
            "pdf_extraction_failed",
            "content_validation_failed"
        ]
        
        for reason in fallback_scenarios:
            handler._log_fallback_reason(reason)
        
        # Add duplicate reasons to test frequency tracking
        handler._log_fallback_reason("application_detection_failed")
        handler._log_fallback_reason("browser_extraction_timeout")
        
        # Verify tracking
        assert hasattr(handler, '_fallback_reasons')
        assert handler._fallback_reasons["application_detection_failed"] == 2
        assert handler._fallback_reasons["unsupported_application"] == 1
        assert handler._fallback_reasons["browser_extraction_timeout"] == 2
        assert handler._fallback_reasons["pdf_extraction_failed"] == 1
        assert handler._fallback_reasons["content_validation_failed"] == 1
        
        total_fallbacks = sum(handler._fallback_reasons.values())
        assert total_fallbacks == 7
        
        print(f"Fallback reasons: {handler._fallback_reasons}")


@pytest.mark.performance
class TestPerformanceRegression:
    """Tests to detect performance regressions."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for regression testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_performance_baseline_browser(self, handler):
        """Establish performance baseline for browser fast path."""
        app_info = Mock()
        app_info.name = "Google Chrome"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.CHROME
        
        extracted_content = "Browser content with more than 50 characters for validation testing."
        summarized_content = "Browser content summary."
        
        execution_times = []
        
        # Run multiple iterations to get stable baseline
        for i in range(10):
            start_time = time.time()
            
            with patch.object(handler, '_detect_active_application', return_value=app_info):
                with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                    mock_browser_handler = Mock()
                    mock_browser_handler.get_page_text_content.return_value = extracted_content
                    mock_browser_class.return_value = mock_browser_handler
                    
                    with patch.object(handler, '_validate_browser_content', return_value=True):
                        with patch.object(handler, '_process_content_for_summarization', return_value=extracted_content):
                            with patch.object(handler, '_summarize_content', return_value=summarized_content):
                                with patch.object(handler, '_speak_result'):
                                    
                                    result = handler.handle("what's on my screen", {
                                        "intent": {"intent": "question_answering"},
                                        "execution_id": f"baseline_browser_{i}"
                                    })
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            assert result["status"] == "success"
            assert result["method"] == "fast_path"
        
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        print(f"Browser baseline - Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s")
        
        # Establish baseline expectations
        assert avg_time < 2.0  # Average should be well under 5 second requirement
        assert max_time < 3.0  # Maximum should still be reasonable
        assert all(t < 5.0 for t in execution_times)  # All executions under requirement
    
    def test_performance_baseline_pdf(self, handler):
        """Establish performance baseline for PDF fast path."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        extracted_content = "PDF content with more than 50 characters for validation testing."
        cleaned_content = extracted_content.strip()
        summarized_content = "PDF content summary."
        
        execution_times = []
        
        # Run multiple iterations to get stable baseline
        for i in range(10):
            start_time = time.time()
            
            with patch.object(handler, '_detect_active_application', return_value=app_info):
                with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                    mock_pdf_handler = Mock()
                    mock_pdf_handler.extract_text_from_open_document.return_value = extracted_content
                    mock_pdf_class.return_value = mock_pdf_handler
                    
                    with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                        with patch.object(handler, '_process_content_for_summarization', return_value=cleaned_content):
                            with patch.object(handler, '_summarize_content', return_value=summarized_content):
                                with patch.object(handler, '_speak_result'):
                                    
                                    result = handler.handle("what's on my screen", {
                                        "intent": {"intent": "question_answering"},
                                        "execution_id": f"baseline_pdf_{i}"
                                    })
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            assert result["status"] == "success"
            assert result["method"] == "fast_path"
        
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        print(f"PDF baseline - Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s")
        
        # Establish baseline expectations
        assert avg_time < 2.0  # Average should be well under 5 second requirement
        assert max_time < 3.0  # Maximum should still be reasonable
        assert all(t < 5.0 for t in execution_times)  # All executions under requirement
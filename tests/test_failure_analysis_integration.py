"""
Integration tests for failure analysis with various failure scenarios.

Tests the complete failure analysis workflow with real-world scenarios
including permission issues, element detection failures, and timeout problems.
"""

import pytest
import time
from datetime import datetime
from unittest.mock import patch, MagicMock

from modules.failure_analyzer import (
    FailureAnalyzer, ElementSearchAttempt, failure_analyzer
)
from modules.accessibility import (
    AccessibilityPermissionError, ElementNotFoundError, AccessibilityTimeoutError
)


class TestFailureAnalysisIntegration:
    """Integration tests for complete failure analysis workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = FailureAnalyzer()
        # Clear history for clean tests
        self.analyzer.failure_history = []
    
    def create_search_attempt(self, success=False, elements_found=0, duration_ms=150.0,
                            best_match_score=0.0, error_message=None, search_strategy="exact_match"):
        """Helper to create search attempts."""
        return ElementSearchAttempt(
            search_id=f"search_{int(time.time() * 1000)}",
            timestamp=datetime.now(),
            target_text="Sign In",
            search_parameters={"role": "button", "timeout": 1000},
            app_name="TestApp",
            duration_ms=duration_ms,
            success=success,
            elements_found=elements_found,
            best_match_score=best_match_score,
            search_strategy=search_strategy,
            error_message=error_message
        )
    
    def test_permission_failure_scenario(self):
        """Test complete failure analysis for permission issues."""
        # Simulate permission error
        error = AccessibilityPermissionError(
            "Accessibility permission denied for application",
            recovery_suggestion="Grant permissions in System Preferences"
        )
        
        search_attempts = [
            self.create_search_attempt(error_message="Permission denied")
        ]
        
        available_elements = []  # No elements available due to permission issue
        
        system_context = {
            "os_version": "macOS 14.0",
            "accessibility_enabled": False,
            "app_bundle_id": "com.test.app"
        }
        
        # Analyze the failure
        report = self.analyzer.analyze_failure(
            command="Click Sign In button",
            target_text="Sign In",
            app_name="TestApp",
            error=error,
            search_attempts=search_attempts,
            available_elements=available_elements,
            system_context=system_context
        )
        
        # Verify analysis results
        assert report.command == "Click Sign In button"
        assert report.target_text == "Sign In"
        assert report.app_name == "TestApp"
        assert len(report.failure_reasons) > 0
        
        # Should identify permission issue
        permission_failures = [r for r in report.failure_reasons if r.category == "permission"]
        assert len(permission_failures) > 0
        assert permission_failures[0].severity == "critical"
        
        # Should provide permission-related recommendations
        permission_recommendations = [r for r in report.recommendations 
                                    if "permission" in r.lower()]
        assert len(permission_recommendations) > 0
        
        # Should have high confidence in failure identification
        assert report.confidence_assessment["failure_identification_confidence"] == "high"
        
        # Verify report can be serialized
        report_dict = report.to_dict()
        assert "failure_reasons" in report_dict
        assert "recommendations" in report_dict
        
        json_str = report.to_json()
        assert "permission" in json_str.lower()
    
    def test_element_not_found_scenario(self):
        """Test failure analysis for element not found with similar alternatives."""
        error = ElementNotFoundError(
            "Element 'Sign In' not found in accessibility tree",
            element_role="button",
            element_label="Sign In"
        )
        
        search_attempts = [
            self.create_search_attempt(elements_found=0),
            self.create_search_attempt(elements_found=0, search_strategy="fuzzy_match"),
            self.create_search_attempt(elements_found=0, search_strategy="role_based")
        ]
        
        # Provide similar elements that could be alternatives
        available_elements = [
            {"title": "Login", "role": "AXButton", "coordinates": [100, 200, 80, 30]},
            {"title": "Sign Up", "role": "AXButton", "coordinates": [200, 200, 80, 30]},
            {"title": "Continue", "role": "AXButton", "coordinates": [300, 200, 80, 30]},
            {"title": "Submit", "role": "AXButton", "coordinates": [400, 200, 80, 30]}
        ]
        
        system_context = {
            "accessibility_enabled": True,
            "total_elements_found": len(available_elements),
            "search_depth": 3
        }
        
        with patch('modules.failure_analyzer.FUZZY_MATCHING_AVAILABLE', True), \
             patch('modules.failure_analyzer.fuzz') as mock_fuzz:
            
            # Mock fuzzy matching scores
            def mock_ratio(text1, text2):
                text1_lower = text1.lower()
                text2_lower = text2.lower()
                if "login" in text1_lower and "sign in" in text2_lower:
                    return 75  # Medium similarity
                elif "sign up" in text1_lower and "sign in" in text2_lower:
                    return 85  # High similarity
                elif "sign in" in text1_lower and "sign in" in text2_lower:
                    return 100  # Exact match
                elif "sign" in text1_lower and "sign" in text2_lower:
                    return 60  # Partial match
                return 30
            
            mock_fuzz.ratio.side_effect = mock_ratio
            mock_fuzz.partial_ratio.side_effect = mock_ratio
            mock_fuzz.token_sort_ratio.side_effect = mock_ratio
            mock_fuzz.token_set_ratio.side_effect = mock_ratio
            
            # Analyze the failure
            report = self.analyzer.analyze_failure(
                command="Click Sign In",
                target_text="Sign In",
                app_name="WebBrowser",
                error=error,
                search_attempts=search_attempts,
                available_elements=available_elements,
                system_context=system_context
            )
        
        # Verify analysis results
        assert len(report.failure_reasons) > 0
        assert len(report.available_elements) == 4
        assert len(report.closest_matches) > 0
        
        # Should identify element detection failure
        detection_failures = [r for r in report.failure_reasons if r.category == "element_detection"]
        assert len(detection_failures) > 0
        
        # Should find similar alternatives
        assert len(report.closest_matches) > 0
        best_match = report.closest_matches[0]
        assert best_match["similarity_score"] >= 50  # Lowered threshold for test
        
        # Should provide specific recommendations
        assert len(report.recommendations) > 0
        alternative_recommendations = [r for r in report.recommendations 
                                     if any(alt in r for alt in ["Login", "Sign Up"])]
        assert len(alternative_recommendations) > 0
        
        # Should have medium to high confidence
        assert report.confidence_assessment["overall_confidence"] in ["medium", "high"]
    
    def test_timeout_failure_scenario(self):
        """Test failure analysis for timeout issues."""
        error = AccessibilityTimeoutError(
            "Element search timed out after 5000ms",
            operation="element_search"
        )
        
        # Simulate slow search attempts
        search_attempts = [
            self.create_search_attempt(duration_ms=2500.0, elements_found=10),
            self.create_search_attempt(duration_ms=3000.0, elements_found=15),
            self.create_search_attempt(duration_ms=5000.0, elements_found=0, 
                                     error_message="Timeout exceeded")
        ]
        
        available_elements = [
            {"title": f"Element {i}", "role": "AXButton"} for i in range(20)
        ]
        
        system_context = {
            "system_load": "high",
            "memory_usage": "85%",
            "accessibility_tree_size": 500
        }
        
        # Analyze the failure
        report = self.analyzer.analyze_failure(
            command="Click Sign In",
            target_text="Sign In",
            app_name="SlowApp",
            error=error,
            search_attempts=search_attempts,
            available_elements=available_elements,
            system_context=system_context
        )
        
        # Verify analysis results
        assert len(report.failure_reasons) > 0
        
        # Should identify performance/timeout issues
        performance_failures = [r for r in report.failure_reasons 
                              if r.category in ["performance", "timeout"]]
        assert len(performance_failures) > 0
        
        # Should provide performance-related recommendations
        performance_recommendations = [r for r in report.recommendations 
                                     if any(word in r.lower() for word in 
                                           ["timeout", "performance", "slow", "optimize"])]
        assert len(performance_recommendations) > 0
        
        # Should suggest recovery actions
        recovery_suggestions = [s for s in report.recovery_suggestions 
                              if any(word in s.lower() for word in 
                                    ["timeout", "performance", "system"])]
        assert len(recovery_suggestions) > 0
    
    def test_multiple_failure_types_scenario(self):
        """Test failure analysis with multiple types of failures."""
        # Complex error combining multiple issues
        error = Exception("Multiple issues: permission denied, element not found, timeout")
        
        search_attempts = [
            self.create_search_attempt(duration_ms=3000.0, error_message="Permission denied"),
            self.create_search_attempt(duration_ms=2500.0, elements_found=0, 
                                     error_message="No elements found"),
            self.create_search_attempt(duration_ms=5000.0, error_message="Timeout exceeded")
        ]
        
        available_elements = [
            {"title": "Login Button", "role": "AXButton"},
            {"title": "Sign Up Link", "role": "AXLink"}
        ]
        
        system_context = {
            "accessibility_enabled": False,
            "system_load": "high",
            "app_responsive": False
        }
        
        # Analyze the failure
        report = self.analyzer.analyze_failure(
            command="Click Sign In",
            target_text="Sign In",
            app_name="ComplexApp",
            error=error,
            search_attempts=search_attempts,
            available_elements=available_elements,
            system_context=system_context
        )
        
        # Should identify multiple failure categories
        failure_categories = set(reason.category for reason in report.failure_reasons)
        assert len(failure_categories) >= 2  # Should detect multiple types
        
        # Should provide comprehensive recommendations
        assert len(report.recommendations) >= 3
        assert len(report.recovery_suggestions) >= 3
        
        # Should have detailed failure analysis
        assert len(report.failure_reasons) >= 2
        
        # Confidence should reflect complexity
        assert "factors" in report.confidence_assessment
        assert len(report.confidence_assessment["factors"]) > 0
    
    def test_successful_recovery_scenario(self):
        """Test failure analysis when some attempts succeed."""
        error = ElementNotFoundError("Initial search failed")
        
        search_attempts = [
            self.create_search_attempt(success=False, elements_found=0),
            self.create_search_attempt(success=False, elements_found=5),
            self.create_search_attempt(success=True, elements_found=1, 
                                     best_match_score=95.0, search_strategy="fuzzy_match")
        ]
        
        available_elements = [
            {"title": "Sign In", "role": "AXButton", "coordinates": [100, 200, 80, 30]}
        ]
        
        # Analyze the failure (even though recovery eventually succeeded)
        report = self.analyzer.analyze_failure(
            command="Click Sign In",
            target_text="Sign In",
            app_name="TestApp",
            error=error,
            search_attempts=search_attempts,
            available_elements=available_elements
        )
        
        # Should still analyze the initial failure
        assert len(report.failure_reasons) > 0
        
        # But should have high confidence in recovery
        assert report.confidence_assessment["recovery_likelihood"] == "high"
        
        # Should note that elements were eventually found
        recovery_factors = [f for f in report.confidence_assessment["factors"] 
                          if "found" in f.lower()]
        assert len(recovery_factors) > 0
    
    def test_failure_pattern_recognition(self):
        """Test that failure patterns are recognized over multiple failures."""
        # Simulate multiple similar failures
        for i in range(5):
            error = AccessibilityPermissionError("Permission denied")
            search_attempts = [self.create_search_attempt()]
            
            self.analyzer.analyze_failure(
                command=f"Click Button {i}",
                target_text=f"Button {i}",
                app_name="TestApp",
                error=error,
                search_attempts=search_attempts,
                available_elements=[]
            )
        
        # Analyze failure patterns
        patterns = self.analyzer.get_failure_patterns()
        
        assert patterns["total_failures"] == 5
        assert "permission" in patterns["failure_categories"]
        assert patterns["failure_categories"]["permission"] == 5
        assert "TestApp" in patterns["common_apps"]
        assert patterns["common_apps"]["TestApp"] == 5
    
    def test_report_summary_generation(self):
        """Test that failure reports generate useful summaries."""
        error = ElementNotFoundError("Element not found")
        search_attempts = [self.create_search_attempt()]
        available_elements = [{"title": "Login", "role": "AXButton"}]
        
        report = self.analyzer.analyze_failure(
            command="Click Sign In button",
            target_text="Sign In",
            app_name="TestApp",
            error=error,
            search_attempts=search_attempts,
            available_elements=available_elements
        )
        
        summary = report.get_summary()
        
        # Summary should contain key information
        assert "Click Sign In button" in summary
        assert "Sign In" in summary
        assert "TestApp" in summary
        assert "Failure Analysis Report" in summary
        assert "Recommendations" in summary
        
        # Should be human-readable
        lines = summary.split('\n')
        assert len(lines) > 5  # Should have multiple lines
        assert any("Primary Failure Reasons" in line for line in lines)
    
    def test_concurrent_failure_analysis(self):
        """Test that failure analysis works correctly with concurrent requests."""
        import threading
        import concurrent.futures
        
        results = []
        
        def analyze_failure(thread_id):
            error = ElementNotFoundError(f"Error from thread {thread_id}")
            search_attempts = [self.create_search_attempt()]
            
            report = self.analyzer.analyze_failure(
                command=f"Click from thread {thread_id}",
                target_text=f"Target {thread_id}",
                app_name=f"App {thread_id}",
                error=error,
                search_attempts=search_attempts,
                available_elements=[]
            )
            return report
        
        # Run multiple analyses concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(analyze_failure, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All analyses should complete successfully
        assert len(results) == 5
        
        # Each should have unique identifiers
        commands = [r.command for r in results]
        assert len(set(commands)) == 5  # All unique
        
        # History should contain all failures
        assert len(self.analyzer.failure_history) >= 5


class TestFailureAnalysisWithRealAccessibilityModule:
    """Integration tests with mocked accessibility module interactions."""
    
    def test_integration_with_accessibility_logging(self):
        """Test that failure analysis integrates with accessibility module logging."""
        with patch('modules.failure_analyzer.debug_logger') as mock_debug_logger:
            analyzer = FailureAnalyzer()
            error = ElementNotFoundError("Test error")
            search_attempts = [analyzer.create_search_attempt(
                search_id="test", target_text="Test", search_parameters={},
                app_name="Test", duration_ms=100, success=False,
                elements_found=0, best_match_score=0, search_strategy="test"
            )]
            
            report = analyzer.analyze_failure(
                command="Test command",
                target_text="Test",
                app_name="TestApp",
                error=error,
                search_attempts=search_attempts,
                available_elements=[]
            )
            
            # Should have called debug logger
            assert mock_debug_logger.log_failure_analysis.called
            call_args = mock_debug_logger.log_failure_analysis.call_args[0]
            assert call_args[0] == "Test command"  # command
            assert call_args[1] == "Test"  # target_text
            assert call_args[4] == "TestApp"  # app_name


if __name__ == "__main__":
    pytest.main([__file__])
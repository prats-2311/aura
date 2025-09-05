"""
Unit tests for failure analysis and reporting functionality.

Tests the comprehensive failure analysis system with detailed reporting,
similarity analysis, and recovery recommendations.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

from modules.failure_analyzer import (
    FailureAnalyzer, FailureReason, ElementSearchAttempt, FailureAnalysisReport,
    failure_analyzer
)


class TestFailureReason:
    """Test the FailureReason dataclass."""
    
    def test_failure_reason_creation(self):
        """Test creating a failure reason."""
        reason = FailureReason(
            category="permission",
            code="access_denied",
            message="Accessibility permissions not granted",
            severity="critical",
            technical_details={"error_code": 1001},
            recovery_suggestion="Grant permissions in System Preferences"
        )
        
        assert reason.category == "permission"
        assert reason.code == "access_denied"
        assert reason.severity == "critical"
        assert reason.technical_details["error_code"] == 1001
    
    def test_failure_reason_to_dict(self):
        """Test converting failure reason to dictionary."""
        reason = FailureReason(
            category="element_detection",
            code="not_found",
            message="Element not found",
            severity="high"
        )
        
        result = reason.to_dict()
        
        assert result["category"] == "element_detection"
        assert result["code"] == "not_found"
        assert result["message"] == "Element not found"
        assert result["severity"] == "high"


class TestElementSearchAttempt:
    """Test the ElementSearchAttempt dataclass."""
    
    def test_search_attempt_creation(self):
        """Test creating a search attempt."""
        attempt = ElementSearchAttempt(
            search_id="search_001",
            timestamp=datetime.now(),
            target_text="Sign In",
            search_parameters={"role": "button", "timeout": 1000},
            app_name="TestApp",
            duration_ms=150.5,
            success=False,
            elements_found=0,
            best_match_score=0.0,
            search_strategy="exact_match",
            error_message="No elements found"
        )
        
        assert attempt.search_id == "search_001"
        assert attempt.target_text == "Sign In"
        assert attempt.success is False
        assert attempt.elements_found == 0
        assert attempt.error_message == "No elements found"
    
    def test_search_attempt_to_dict(self):
        """Test converting search attempt to dictionary."""
        timestamp = datetime.now()
        attempt = ElementSearchAttempt(
            search_id="search_001",
            timestamp=timestamp,
            target_text="Sign In",
            search_parameters={"role": "button"},
            app_name="TestApp",
            duration_ms=150.5,
            success=True,
            elements_found=1,
            best_match_score=95.0,
            search_strategy="fuzzy_match"
        )
        
        result = attempt.to_dict()
        
        assert result["search_id"] == "search_001"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["success"] is True
        assert result["best_match_score"] == 95.0


class TestFailureAnalysisReport:
    """Test the FailureAnalysisReport dataclass."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.timestamp = datetime.now()
        self.failure_reason = FailureReason(
            category="element_detection",
            code="not_found",
            message="Element not found",
            severity="high"
        )
        self.search_attempt = ElementSearchAttempt(
            search_id="search_001",
            timestamp=self.timestamp,
            target_text="Sign In",
            search_parameters={"role": "button"},
            app_name="TestApp",
            duration_ms=150.5,
            success=False,
            elements_found=0,
            best_match_score=0.0,
            search_strategy="exact_match"
        )
    
    def test_report_creation(self):
        """Test creating a failure analysis report."""
        report = FailureAnalysisReport(
            command="Click Sign In",
            target_text="Sign In",
            app_name="TestApp",
            timestamp=self.timestamp,
            failure_reasons=[self.failure_reason],
            search_attempts=[self.search_attempt],
            available_elements=[{"title": "Login", "role": "button"}],
            closest_matches=[{"title": "Login", "similarity_score": 75.0}],
            similarity_analysis={"target_length": 7},
            system_context={"os": "macOS"},
            recommendations=["Try using 'Login' instead"],
            recovery_suggestions=["Verify element exists"],
            confidence_assessment={"overall_confidence": "medium"}
        )
        
        assert report.command == "Click Sign In"
        assert report.target_text == "Sign In"
        assert len(report.failure_reasons) == 1
        assert len(report.search_attempts) == 1
        assert len(report.recommendations) == 1
    
    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        report = FailureAnalysisReport(
            command="Click Sign In",
            target_text="Sign In",
            app_name="TestApp",
            timestamp=self.timestamp,
            failure_reasons=[self.failure_reason],
            search_attempts=[self.search_attempt],
            available_elements=[],
            closest_matches=[],
            similarity_analysis={},
            system_context={},
            recommendations=[],
            recovery_suggestions=[],
            confidence_assessment={}
        )
        
        result = report.to_dict()
        
        assert result["command"] == "Click Sign In"
        assert result["timestamp"] == self.timestamp.isoformat()
        assert len(result["failure_reasons"]) == 1
        assert len(result["search_attempts"]) == 1
    
    def test_report_to_json(self):
        """Test converting report to JSON."""
        report = FailureAnalysisReport(
            command="Click Sign In",
            target_text="Sign In",
            app_name="TestApp",
            timestamp=self.timestamp,
            failure_reasons=[self.failure_reason],
            search_attempts=[self.search_attempt],
            available_elements=[],
            closest_matches=[],
            similarity_analysis={},
            system_context={},
            recommendations=[],
            recovery_suggestions=[],
            confidence_assessment={}
        )
        
        json_str = report.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["command"] == "Click Sign In"
        assert "timestamp" in parsed
    
    def test_report_get_summary(self):
        """Test getting report summary."""
        report = FailureAnalysisReport(
            command="Click Sign In",
            target_text="Sign In",
            app_name="TestApp",
            timestamp=self.timestamp,
            failure_reasons=[self.failure_reason],
            search_attempts=[self.search_attempt],
            available_elements=[{"title": "Login"}],
            closest_matches=[{"title": "Login", "similarity_score": 75.0}],
            similarity_analysis={},
            system_context={},
            recommendations=["Try using 'Login' instead"],
            recovery_suggestions=[],
            confidence_assessment={}
        )
        
        summary = report.get_summary()
        
        assert "Click Sign In" in summary
        assert "Sign In" in summary
        assert "TestApp" in summary
        assert "Element not found" in summary
        assert "Try using 'Login' instead" in summary


class TestFailureAnalyzer:
    """Test the main FailureAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = FailureAnalyzer()
        self.search_attempt = ElementSearchAttempt(
            search_id="search_001",
            timestamp=datetime.now(),
            target_text="Sign In",
            search_parameters={"role": "button"},
            app_name="TestApp",
            duration_ms=150.5,
            success=False,
            elements_found=0,
            best_match_score=0.0,
            search_strategy="exact_match"
        )
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = FailureAnalyzer()
        
        assert analyzer.max_history_size == 100
        assert len(analyzer.common_failure_patterns) > 0
        assert "permission_denied" in analyzer.common_failure_patterns
        assert "element_not_found" in analyzer.common_failure_patterns
    
    def test_analyze_failure_permission_error(self):
        """Test analyzing permission-related failures."""
        error = Exception("Accessibility permission denied")
        available_elements = [{"title": "Login", "role": "button"}]
        
        report = self.analyzer.analyze_failure(
            command="Click Sign In",
            target_text="Sign In",
            app_name="TestApp",
            error=error,
            search_attempts=[self.search_attempt],
            available_elements=available_elements
        )
        
        assert report.command == "Click Sign In"
        assert report.target_text == "Sign In"
        assert len(report.failure_reasons) > 0
        
        # Should detect permission issue
        permission_reasons = [r for r in report.failure_reasons if r.category == "permission"]
        assert len(permission_reasons) > 0
        assert permission_reasons[0].severity == "critical"
    
    def test_analyze_failure_element_not_found(self):
        """Test analyzing element not found failures."""
        error = Exception("Element not found in accessibility tree")
        available_elements = [
            {"title": "Login", "role": "button"},
            {"title": "Register", "role": "button"}
        ]
        
        report = self.analyzer.analyze_failure(
            command="Click Sign In",
            target_text="Sign In",
            app_name="TestApp",
            error=error,
            search_attempts=[self.search_attempt],
            available_elements=available_elements
        )
        
        assert len(report.failure_reasons) > 0
        assert len(report.available_elements) == 2
        assert len(report.recommendations) > 0
    
    @patch('modules.failure_analyzer.FUZZY_MATCHING_AVAILABLE', True)
    @patch('modules.failure_analyzer.fuzz')
    def test_find_closest_matches(self, mock_fuzz):
        """Test finding closest matches with fuzzy matching."""
        mock_fuzz.ratio.return_value = 85
        mock_fuzz.partial_ratio.return_value = 90
        mock_fuzz.token_sort_ratio.return_value = 80
        mock_fuzz.token_set_ratio.return_value = 75
        
        available_elements = [
            {"title": "Sign In", "role": "button"},
            {"title": "Login", "role": "button"},
            {"title": "Register", "role": "button"}
        ]
        
        matches = self.analyzer._find_closest_matches("Sign In", available_elements)
        
        assert len(matches) > 0
        assert matches[0]["similarity_score"] == 90  # Best score from partial_ratio
        assert "similarity_category" in matches[0]
    
    @patch('modules.failure_analyzer.FUZZY_MATCHING_AVAILABLE', False)
    def test_find_closest_matches_no_fuzzy(self):
        """Test finding closest matches when fuzzy matching is unavailable."""
        available_elements = [{"title": "Login", "role": "button"}]
        
        matches = self.analyzer._find_closest_matches("Sign In", available_elements)
        
        assert matches == []
    
    def test_perform_similarity_analysis(self):
        """Test performing similarity analysis."""
        available_elements = [
            {"title": "Sign In Button", "role": "button"},
            {"title": "Login Form", "role": "form"},
            {"title": "User Registration", "role": "button"}
        ]
        
        with patch('modules.failure_analyzer.FUZZY_MATCHING_AVAILABLE', True), \
             patch('modules.failure_analyzer.fuzz') as mock_fuzz:
            mock_fuzz.ratio.return_value = 75
            
            analysis = self.analyzer._perform_similarity_analysis("Sign In", available_elements)
            
            assert analysis["target_text"] == "Sign In"
            assert analysis["target_length"] == 7
            assert analysis["available_element_count"] == 3
            assert "similarity_distribution" in analysis
            assert "common_words" in analysis
    
    def test_get_similarity_category(self):
        """Test similarity score categorization."""
        assert self.analyzer._get_similarity_category(100) == "exact_match"
        assert self.analyzer._get_similarity_category(90) == "high_similarity"
        assert self.analyzer._get_similarity_category(75) == "medium_similarity"
        assert self.analyzer._get_similarity_category(55) == "low_similarity"
        assert self.analyzer._get_similarity_category(30) == "no_similarity"
    
    def test_generate_recommendations(self):
        """Test generating recommendations."""
        failure_reasons = [
            FailureReason(
                category="element_detection",
                code="not_found",
                message="Element not found",
                severity="high",
                recovery_suggestion="Verify element exists"
            )
        ]
        
        closest_matches = [
            {"matched_text": "Login", "similarity_score": 85.0}
        ]
        
        similarity_analysis = {
            "common_words": ["sign"],
            "suggested_alternatives": [{"text": "Sign Up", "role": "button"}]
        }
        
        recommendations = self.analyzer._generate_recommendations(
            failure_reasons, closest_matches, similarity_analysis
        )
        
        assert len(recommendations) > 0
        assert any("Login" in rec for rec in recommendations)
        assert any("sign" in rec.lower() for rec in recommendations)
    
    def test_generate_recovery_suggestions(self):
        """Test generating recovery suggestions."""
        failure_reasons = [
            FailureReason(category="permission", code="denied", message="", severity="critical"),
            FailureReason(category="performance", code="timeout", message="", severity="medium")
        ]
        
        suggestions = self.analyzer._generate_recovery_suggestions(failure_reasons)
        
        assert len(suggestions) > 0
        # Should include suggestions for both permission and performance categories
        permission_suggestions = [s for s in suggestions if "permission" in s.lower()]
        performance_suggestions = [s for s in suggestions if "timeout" in s.lower() or "performance" in s.lower()]
        
        assert len(permission_suggestions) > 0
        assert len(performance_suggestions) > 0
    
    def test_assess_confidence(self):
        """Test confidence assessment."""
        failure_reasons = [
            FailureReason(category="permission", code="denied", message="", severity="critical")
        ]
        
        closest_matches = [
            {"similarity_score": 90.0}
        ]
        
        search_attempts = [
            ElementSearchAttempt(
                search_id="1", timestamp=datetime.now(), target_text="test",
                search_parameters={}, app_name="test", duration_ms=100,
                success=False, elements_found=5, best_match_score=0,
                search_strategy="test"
            )
        ]
        
        confidence = self.analyzer._assess_confidence(failure_reasons, closest_matches, search_attempts)
        
        assert "overall_confidence" in confidence
        assert "failure_identification_confidence" in confidence
        assert "recommendation_confidence" in confidence
        assert "recovery_likelihood" in confidence
        assert isinstance(confidence["factors"], list)
        
        # Should have high confidence due to critical failure and high similarity match
        assert confidence["failure_identification_confidence"] == "high"
        assert confidence["recommendation_confidence"] == "high"
    
    def test_create_search_attempt(self):
        """Test creating search attempt."""
        attempt = self.analyzer.create_search_attempt(
            search_id="test_001",
            target_text="Sign In",
            search_parameters={"role": "button", "timeout": 1000},
            app_name="TestApp",
            duration_ms=250.5,
            success=True,
            elements_found=1,
            best_match_score=95.0,
            search_strategy="fuzzy_match",
            error_message=None
        )
        
        assert attempt.search_id == "test_001"
        assert attempt.target_text == "Sign In"
        assert attempt.success is True
        assert attempt.elements_found == 1
        assert attempt.best_match_score == 95.0
        assert attempt.error_message is None
    
    def test_add_to_history(self):
        """Test adding reports to history."""
        # Create a test report
        report = FailureAnalysisReport(
            command="test", target_text="test", app_name="test",
            timestamp=datetime.now(), failure_reasons=[], search_attempts=[],
            available_elements=[], closest_matches=[], similarity_analysis={},
            system_context={}, recommendations=[], recovery_suggestions=[],
            confidence_assessment={}
        )
        
        initial_count = len(self.analyzer.failure_history)
        self.analyzer._add_to_history(report)
        
        assert len(self.analyzer.failure_history) == initial_count + 1
        assert self.analyzer.failure_history[-1] == report
    
    def test_history_size_limit(self):
        """Test that history maintains size limit."""
        # Set a small limit for testing
        self.analyzer.max_history_size = 3
        
        # Add more reports than the limit
        for i in range(5):
            report = FailureAnalysisReport(
                command=f"test_{i}", target_text="test", app_name="test",
                timestamp=datetime.now(), failure_reasons=[], search_attempts=[],
                available_elements=[], closest_matches=[], similarity_analysis={},
                system_context={}, recommendations=[], recovery_suggestions=[],
                confidence_assessment={}
            )
            self.analyzer._add_to_history(report)
        
        # Should only keep the last 3 reports
        assert len(self.analyzer.failure_history) == 3
        assert self.analyzer.failure_history[0].command == "test_2"
        assert self.analyzer.failure_history[-1].command == "test_4"
    
    def test_get_failure_patterns_empty_history(self):
        """Test getting failure patterns with empty history."""
        self.analyzer.failure_history = []
        
        patterns = self.analyzer.get_failure_patterns()
        
        assert "message" in patterns
        assert "No failure history available" in patterns["message"]
    
    def test_get_failure_patterns_with_history(self):
        """Test getting failure patterns with history."""
        # Add some test reports to history
        for i in range(3):
            failure_reason = FailureReason(
                category="element_detection" if i % 2 == 0 else "permission",
                code="test", message="test", severity="high"
            )
            report = FailureAnalysisReport(
                command=f"test_{i}", target_text=f"target_{i}", app_name=f"app_{i % 2}",
                timestamp=datetime.now(), failure_reasons=[failure_reason],
                search_attempts=[], available_elements=[], closest_matches=[],
                similarity_analysis={}, system_context={}, recommendations=[],
                recovery_suggestions=[], confidence_assessment={}
            )
            self.analyzer._add_to_history(report)
        
        patterns = self.analyzer.get_failure_patterns()
        
        assert patterns["total_failures"] == 3
        assert "failure_categories" in patterns
        assert "common_apps" in patterns
        assert "frequent_targets" in patterns
        
        # Check that categories were counted correctly
        assert patterns["failure_categories"]["element_detection"] == 2
        assert patterns["failure_categories"]["permission"] == 1


class TestGlobalFailureAnalyzer:
    """Test the global failure analyzer instance."""
    
    def test_global_instance_exists(self):
        """Test that global failure analyzer instance exists."""
        assert failure_analyzer is not None
        assert isinstance(failure_analyzer, FailureAnalyzer)
    
    def test_global_instance_functionality(self):
        """Test that global instance works correctly."""
        search_attempt = failure_analyzer.create_search_attempt(
            search_id="global_test",
            target_text="Test",
            search_parameters={},
            app_name="TestApp",
            duration_ms=100,
            success=False,
            elements_found=0,
            best_match_score=0,
            search_strategy="test"
        )
        
        assert search_attempt.search_id == "global_test"
        assert search_attempt.target_text == "Test"


if __name__ == "__main__":
    pytest.main([__file__])
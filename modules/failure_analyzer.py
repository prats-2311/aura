"""
Failure Analysis Module

Provides comprehensive failure analysis and reporting for accessibility issues,
element detection failures, and system diagnostics with detailed recommendations.
"""

import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import traceback

# Import debug logger for structured logging
from .debug_logger import debug_logger, log_basic, log_detailed, log_verbose

# Import fuzzy matching for similarity analysis
try:
    from thefuzz import fuzz
    FUZZY_MATCHING_AVAILABLE = True
except ImportError:
    FUZZY_MATCHING_AVAILABLE = False


@dataclass
class FailureReason:
    """Represents a specific failure reason with details."""
    category: str  # permission, element_not_found, timeout, api_error, etc.
    code: str      # Specific error code
    message: str   # Human-readable description
    severity: str  # critical, high, medium, low
    technical_details: Optional[Dict[str, Any]] = None
    recovery_suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)


@dataclass
class ElementSearchAttempt:
    """Represents a single element search attempt with parameters and results."""
    search_id: str
    timestamp: datetime
    target_text: str
    search_parameters: Dict[str, Any]
    app_name: str
    duration_ms: float
    success: bool
    elements_found: int
    best_match_score: float
    search_strategy: str
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class FailureAnalysisReport:
    """Comprehensive failure analysis report with recommendations."""
    command: str
    target_text: str
    app_name: str
    timestamp: datetime
    failure_reasons: List[FailureReason]
    search_attempts: List[ElementSearchAttempt]
    available_elements: List[Dict[str, Any]]
    closest_matches: List[Dict[str, Any]]
    similarity_analysis: Dict[str, Any]
    system_context: Dict[str, Any]
    recommendations: List[str]
    recovery_suggestions: List[str]
    confidence_assessment: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and export."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['failure_reasons'] = [reason.to_dict() for reason in self.failure_reasons]
        result['search_attempts'] = [attempt.to_dict() for attempt in self.search_attempts]
        return result
    
    def to_json(self) -> str:
        """Export as JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the failure analysis."""
        summary_lines = [
            f"Failure Analysis Report for: {self.command}",
            f"Target: {self.target_text}",
            f"Application: {self.app_name}",
            f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Primary Failure Reasons ({len(self.failure_reasons)}):"
        ]
        
        for i, reason in enumerate(self.failure_reasons, 1):
            summary_lines.append(f"  {i}. [{reason.severity.upper()}] {reason.category}: {reason.message}")
        
        summary_lines.extend([
            "",
            f"Search Attempts: {len(self.search_attempts)}",
            f"Available Elements: {len(self.available_elements)}",
            f"Closest Matches: {len(self.closest_matches)}",
            "",
            f"Recommendations ({len(self.recommendations)}):"
        ])
        
        for i, rec in enumerate(self.recommendations, 1):
            summary_lines.append(f"  {i}. {rec}")
        
        return "\n".join(summary_lines)


class FailureAnalyzer:
    """
    Analyzes accessibility failures and provides detailed reports with recommendations.
    
    This class provides comprehensive failure analysis for element detection failures,
    permission issues, timeout problems, and other accessibility-related errors.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.failure_history: List[FailureAnalysisReport] = []
        self.max_history_size = 100
        
        # Failure pattern recognition
        self.common_failure_patterns = {
            'permission_denied': {
                'keywords': ['permission', 'denied', 'accessibility', 'authorized'],
                'category': 'permission',
                'severity': 'critical',
                'recovery': 'Grant accessibility permissions in System Preferences'
            },
            'element_not_found': {
                'keywords': ['not found', 'no element', 'no match', 'empty result'],
                'category': 'element_detection',
                'severity': 'high',
                'recovery': 'Verify element exists and is visible'
            },
            'timeout': {
                'keywords': ['timeout', 'timed out', 'exceeded', 'slow'],
                'category': 'performance',
                'severity': 'medium',
                'recovery': 'Increase timeout or optimize search parameters'
            },
            'api_error': {
                'keywords': ['api error', 'framework', 'unavailable', 'import'],
                'category': 'system',
                'severity': 'critical',
                'recovery': 'Install required frameworks and dependencies'
            }
        }
        
        # Element similarity thresholds
        self.similarity_thresholds = {
            'exact_match': 100,
            'high_similarity': 85,
            'medium_similarity': 70,
            'low_similarity': 50
        }
        
        # Recovery suggestion templates
        self.recovery_templates = {
            'permission': [
                "Grant accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility",
                "Restart the application after granting permissions",
                "Check if the application is in the accessibility permissions list"
            ],
            'element_detection': [
                "Verify the target element is visible on screen",
                "Check if the element text matches exactly (case-sensitive)",
                "Try using partial text matching or fuzzy search",
                "Ensure the application window is in focus"
            ],
            'performance': [
                "Increase timeout values in configuration",
                "Reduce the number of concurrent operations",
                "Clear element cache and retry",
                "Check system performance and available memory"
            ],
            'system': [
                "Install required accessibility frameworks",
                "Update macOS to the latest version",
                "Restart the system to refresh accessibility services",
                "Check for conflicting accessibility applications"
            ]
        }
    
    def analyze_failure(self, command: str, target_text: str, app_name: str,
                       error: Exception, search_attempts: List[ElementSearchAttempt],
                       available_elements: List[Dict[str, Any]],
                       system_context: Optional[Dict[str, Any]] = None) -> FailureAnalysisReport:
        """
        Perform comprehensive failure analysis.
        
        Args:
            command: Original user command
            target_text: Extracted target text
            app_name: Application name
            error: The exception that occurred
            search_attempts: List of search attempts made
            available_elements: Elements that were found during search
            system_context: Additional system context information
            
        Returns:
            Comprehensive failure analysis report
        """
        start_time = time.time()
        
        # Log the start of failure analysis
        log_basic(
            "failure_analysis",
            f"Starting failure analysis for command: {command}",
            context={
                "command": command,
                "target": target_text,
                "app_name": app_name,
                "error_type": type(error).__name__,
                "error_message": str(error)
            },
            module="failure_analyzer"
        )
        
        # Analyze failure reasons
        failure_reasons = self._analyze_failure_reasons(error, search_attempts, system_context)
        
        # Find closest matches
        closest_matches = self._find_closest_matches(target_text, available_elements)
        
        # Perform similarity analysis
        similarity_analysis = self._perform_similarity_analysis(target_text, available_elements)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(failure_reasons, closest_matches, similarity_analysis)
        
        # Generate recovery suggestions
        recovery_suggestions = self._generate_recovery_suggestions(failure_reasons)
        
        # Assess confidence in recommendations
        confidence_assessment = self._assess_confidence(failure_reasons, closest_matches, search_attempts)
        
        # Create failure analysis report
        report = FailureAnalysisReport(
            command=command,
            target_text=target_text,
            app_name=app_name,
            timestamp=datetime.now(),
            failure_reasons=failure_reasons,
            search_attempts=search_attempts,
            available_elements=available_elements,
            closest_matches=closest_matches,
            similarity_analysis=similarity_analysis,
            system_context=system_context or {},
            recommendations=recommendations,
            recovery_suggestions=recovery_suggestions,
            confidence_assessment=confidence_assessment
        )
        
        # Add to history
        self._add_to_history(report)
        
        # Log completion
        analysis_duration = (time.time() - start_time) * 1000
        log_basic(
            "failure_analysis",
            f"Failure analysis completed in {analysis_duration:.2f}ms",
            context={
                "duration_ms": analysis_duration,
                "failure_reasons_count": len(failure_reasons),
                "recommendations_count": len(recommendations),
                "closest_matches_count": len(closest_matches)
            },
            module="failure_analyzer"
        )
        
        # Log detailed analysis using debug logger
        debug_logger.log_failure_analysis(
            command, target_text, 
            [reason.message for reason in failure_reasons],
            recommendations, app_name
        )
        
        return report
    
    def _analyze_failure_reasons(self, error: Exception, search_attempts: List[ElementSearchAttempt],
                                system_context: Optional[Dict[str, Any]]) -> List[FailureReason]:
        """Analyze the error and search attempts to determine failure reasons."""
        failure_reasons = []
        error_message = str(error).lower()
        error_type = type(error).__name__
        
        # Check for known failure patterns
        for pattern_name, pattern_info in self.common_failure_patterns.items():
            if any(keyword in error_message for keyword in pattern_info['keywords']):
                failure_reasons.append(FailureReason(
                    category=pattern_info['category'],
                    code=pattern_name,
                    message=f"{pattern_info['category'].title()} issue detected: {str(error)}",
                    severity=pattern_info['severity'],
                    technical_details={
                        'error_type': error_type,
                        'error_message': str(error),
                        'pattern_matched': pattern_name
                    },
                    recovery_suggestion=pattern_info['recovery']
                ))
        
        # Analyze search attempts for additional insights
        if search_attempts:
            total_attempts = len(search_attempts)
            successful_attempts = sum(1 for attempt in search_attempts if attempt.success)
            avg_duration = sum(attempt.duration_ms for attempt in search_attempts) / total_attempts
            
            if successful_attempts == 0:
                failure_reasons.append(FailureReason(
                    category='element_detection',
                    code='no_successful_searches',
                    message=f"All {total_attempts} search attempts failed",
                    severity='high',
                    technical_details={
                        'total_attempts': total_attempts,
                        'average_duration_ms': avg_duration,
                        'search_strategies': list(set(attempt.search_strategy for attempt in search_attempts))
                    },
                    recovery_suggestion='Try different search strategies or verify element exists'
                ))
            
            # Check for performance issues
            if avg_duration > 2000:  # 2 seconds
                failure_reasons.append(FailureReason(
                    category='performance',
                    code='slow_search_performance',
                    message=f"Search operations are slow (avg: {avg_duration:.1f}ms)",
                    severity='medium',
                    technical_details={
                        'average_duration_ms': avg_duration,
                        'slowest_attempt_ms': max(attempt.duration_ms for attempt in search_attempts)
                    },
                    recovery_suggestion='Optimize search parameters or increase system resources'
                ))
        
        # If no specific patterns matched, create a generic failure reason
        if not failure_reasons:
            failure_reasons.append(FailureReason(
                category='unknown',
                code='unclassified_error',
                message=f"Unclassified error: {str(error)}",
                severity='medium',
                technical_details={
                    'error_type': error_type,
                    'error_message': str(error),
                    'stack_trace': traceback.format_exc()
                },
                recovery_suggestion='Review error details and system logs for more information'
            ))
        
        return failure_reasons
    
    def _find_closest_matches(self, target_text: str, available_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find the closest matching elements using fuzzy matching."""
        if not FUZZY_MATCHING_AVAILABLE or not available_elements:
            return []
        
        matches = []
        target_lower = target_text.lower()
        
        for element in available_elements:
            element_texts = []
            
            # Collect all text attributes
            if element.get('title'):
                element_texts.append(element['title'])
            if element.get('description'):
                element_texts.append(element['description'])
            if element.get('value'):
                element_texts.append(str(element['value']))
            
            # Calculate similarity scores for each text
            for text in element_texts:
                if text:
                    text_lower = text.lower()
                    
                    # Calculate different similarity metrics
                    ratio_score = fuzz.ratio(target_lower, text_lower)
                    partial_score = fuzz.partial_ratio(target_lower, text_lower)
                    token_sort_score = fuzz.token_sort_ratio(target_lower, text_lower)
                    token_set_score = fuzz.token_set_ratio(target_lower, text_lower)
                    
                    # Use the highest score
                    best_score = max(ratio_score, partial_score, token_sort_score, token_set_score)
                    
                    if best_score >= self.similarity_thresholds['low_similarity']:
                        match_info = element.copy()
                        match_info.update({
                            'matched_text': text,
                            'similarity_score': best_score,
                            'ratio_score': ratio_score,
                            'partial_score': partial_score,
                            'token_sort_score': token_sort_score,
                            'token_set_score': token_set_score,
                            'similarity_category': self._get_similarity_category(best_score)
                        })
                        matches.append(match_info)
        
        # Sort by similarity score (highest first) and return top 10
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        return matches[:10]
    
    def _perform_similarity_analysis(self, target_text: str, available_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform detailed similarity analysis between target and available elements."""
        if not FUZZY_MATCHING_AVAILABLE:
            return {"error": "Fuzzy matching not available"}
        
        analysis = {
            'target_text': target_text,
            'target_length': len(target_text),
            'target_words': target_text.split(),
            'available_element_count': len(available_elements),
            'similarity_distribution': {
                'exact_match': 0,
                'high_similarity': 0,
                'medium_similarity': 0,
                'low_similarity': 0,
                'no_similarity': 0
            },
            'common_words': [],
            'suggested_alternatives': []
        }
        
        all_element_texts = []
        for element in available_elements:
            if element.get('title'):
                all_element_texts.append(element['title'])
            if element.get('description'):
                all_element_texts.append(element['description'])
        
        # Analyze word overlap
        target_words = set(word.lower() for word in target_text.split())
        element_words = set()
        for text in all_element_texts:
            if text:
                element_words.update(word.lower() for word in text.split())
        
        analysis['common_words'] = list(target_words.intersection(element_words))
        
        # Calculate similarity distribution
        for text in all_element_texts:
            if text:
                score = fuzz.ratio(target_text.lower(), text.lower())
                category = self._get_similarity_category(score)
                analysis['similarity_distribution'][category] += 1
        
        # Generate suggested alternatives based on common words
        if analysis['common_words']:
            for element in available_elements:
                element_text = element.get('title', '')
                if element_text and any(word in element_text.lower() for word in analysis['common_words']):
                    analysis['suggested_alternatives'].append({
                        'text': element_text,
                        'role': element.get('role', 'unknown'),
                        'reason': 'Contains common words with target'
                    })
        
        return analysis
    
    def _get_similarity_category(self, score: float) -> str:
        """Categorize similarity score."""
        if score >= self.similarity_thresholds['exact_match']:
            return 'exact_match'
        elif score >= self.similarity_thresholds['high_similarity']:
            return 'high_similarity'
        elif score >= self.similarity_thresholds['medium_similarity']:
            return 'medium_similarity'
        elif score >= self.similarity_thresholds['low_similarity']:
            return 'low_similarity'
        else:
            return 'no_similarity'
    
    def _generate_recommendations(self, failure_reasons: List[FailureReason],
                                closest_matches: List[Dict[str, Any]],
                                similarity_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on failure analysis."""
        recommendations = []
        
        # Recommendations based on failure reasons
        for reason in failure_reasons:
            if reason.recovery_suggestion:
                recommendations.append(reason.recovery_suggestion)
        
        # Recommendations based on closest matches
        if closest_matches:
            best_match = closest_matches[0]
            if best_match['similarity_score'] >= self.similarity_thresholds['high_similarity']:
                recommendations.append(
                    f"Try using '{best_match['matched_text']}' instead (similarity: {best_match['similarity_score']:.1f}%)"
                )
            elif best_match['similarity_score'] >= self.similarity_thresholds['medium_similarity']:
                recommendations.append(
                    f"Consider using '{best_match['matched_text']}' as an alternative (similarity: {best_match['similarity_score']:.1f}%)"
                )
        
        # Recommendations based on similarity analysis
        if similarity_analysis.get('common_words'):
            recommendations.append(
                f"Target contains common words: {', '.join(similarity_analysis['common_words'])}. "
                "Try using these words individually."
            )
        
        if similarity_analysis.get('suggested_alternatives'):
            alt = similarity_analysis['suggested_alternatives'][0]
            recommendations.append(f"Try targeting '{alt['text']}' which shares common words with your target")
        
        # General recommendations if no specific ones found
        if not recommendations:
            recommendations.extend([
                "Verify the target element is visible and accessible",
                "Check if the application window is in focus",
                "Try using partial text matching",
                "Ensure accessibility permissions are granted"
            ])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _generate_recovery_suggestions(self, failure_reasons: List[FailureReason]) -> List[str]:
        """Generate recovery suggestions based on failure categories."""
        recovery_suggestions = []
        categories = set(reason.category for reason in failure_reasons)
        
        for category in categories:
            if category in self.recovery_templates:
                recovery_suggestions.extend(self.recovery_templates[category])
        
        return list(set(recovery_suggestions))  # Remove duplicates
    
    def _assess_confidence(self, failure_reasons: List[FailureReason],
                          closest_matches: List[Dict[str, Any]],
                          search_attempts: List[ElementSearchAttempt]) -> Dict[str, Any]:
        """Assess confidence in the failure analysis and recommendations."""
        confidence = {
            'overall_confidence': 'medium',
            'failure_identification_confidence': 'high',
            'recommendation_confidence': 'medium',
            'recovery_likelihood': 'medium',
            'factors': []
        }
        
        # Assess failure identification confidence
        critical_failures = sum(1 for reason in failure_reasons if reason.severity == 'critical')
        if critical_failures > 0:
            confidence['failure_identification_confidence'] = 'high'
            confidence['factors'].append('Critical system issues identified')
        
        # Assess recommendation confidence based on closest matches
        if closest_matches:
            best_score = closest_matches[0]['similarity_score']
            if best_score >= self.similarity_thresholds['high_similarity']:
                confidence['recommendation_confidence'] = 'high'
                confidence['recovery_likelihood'] = 'high'
                confidence['factors'].append('High-similarity alternative found')
            elif best_score >= self.similarity_thresholds['medium_similarity']:
                confidence['recommendation_confidence'] = 'medium'
                confidence['factors'].append('Medium-similarity alternative found')
        
        # Assess based on search attempts
        if search_attempts:
            if all(attempt.elements_found == 0 for attempt in search_attempts):
                confidence['factors'].append('No elements found in any search attempt')
                confidence['recovery_likelihood'] = 'low'
            elif any(attempt.elements_found > 0 for attempt in search_attempts):
                confidence['factors'].append('Some elements found, targeting issue likely')
                confidence['recovery_likelihood'] = 'high'
        
        # Calculate overall confidence
        high_confidence_factors = sum(1 for factor in confidence['factors'] 
                                    if 'high' in factor.lower() or 'critical' in factor.lower())
        if high_confidence_factors >= 2:
            confidence['overall_confidence'] = 'high'
        elif high_confidence_factors == 0:
            confidence['overall_confidence'] = 'low'
        
        return confidence
    
    def _add_to_history(self, report: FailureAnalysisReport):
        """Add report to failure history with size management."""
        self.failure_history.append(report)
        
        # Maintain history size limit
        if len(self.failure_history) > self.max_history_size:
            self.failure_history = self.failure_history[-self.max_history_size:]
    
    def get_failure_patterns(self) -> Dict[str, Any]:
        """Analyze failure history to identify patterns."""
        if not self.failure_history:
            return {"message": "No failure history available"}
        
        patterns = {
            'total_failures': len(self.failure_history),
            'failure_categories': {},
            'common_apps': {},
            'frequent_targets': {},
            'time_analysis': {},
            'success_rate_by_category': {}
        }
        
        # Analyze failure categories
        for report in self.failure_history:
            for reason in report.failure_reasons:
                category = reason.category
                patterns['failure_categories'][category] = patterns['failure_categories'].get(category, 0) + 1
            
            # Track common apps
            app = report.app_name
            patterns['common_apps'][app] = patterns['common_apps'].get(app, 0) + 1
            
            # Track frequent targets
            target = report.target_text
            patterns['frequent_targets'][target] = patterns['frequent_targets'].get(target, 0) + 1
        
        return patterns
    
    def create_search_attempt(self, search_id: str, target_text: str, search_parameters: Dict[str, Any],
                            app_name: str, duration_ms: float, success: bool, elements_found: int,
                            best_match_score: float, search_strategy: str,
                            error_message: Optional[str] = None) -> ElementSearchAttempt:
        """Create a new element search attempt record."""
        return ElementSearchAttempt(
            search_id=search_id,
            timestamp=datetime.now(),
            target_text=target_text,
            search_parameters=search_parameters,
            app_name=app_name,
            duration_ms=duration_ms,
            success=success,
            elements_found=elements_found,
            best_match_score=best_match_score,
            search_strategy=search_strategy,
            error_message=error_message
        )


# Global failure analyzer instance
failure_analyzer = FailureAnalyzer()
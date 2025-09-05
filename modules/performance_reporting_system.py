# modules/performance_reporting_system.py
"""
Performance Reporting and Feedback System for AURA Click Debugging Enhancement

Provides real-time feedback about fast path effectiveness, performance improvement
detection, and comprehensive performance reporting with trends and recommendations.
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
from pathlib import Path

from .fast_path_performance_monitor import (
    FastPathPerformanceMonitor,
    FastPathMetric,
    PerformanceAlert,
    fast_path_performance_monitor
)

logger = logging.getLogger(__name__)


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    timestamp: float = field(default_factory=time.time)
    report_id: str = ""
    time_period_hours: float = 1.0
    summary: Dict[str, Any] = field(default_factory=dict)
    trends: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    app_performance: Dict[str, Any] = field(default_factory=dict)
    improvement_factors: List[str] = field(default_factory=list)
    degradation_factors: List[str] = field(default_factory=list)
    health_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackMessage:
    """Real-time feedback message."""
    timestamp: float = field(default_factory=time.time)
    message_type: str = ""  # 'success', 'warning', 'error', 'info'
    title: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    action_required: bool = False
    suggested_actions: List[str] = field(default_factory=list)


class PerformanceImprovementDetector:
    """Detects and analyzes performance improvements and degradations."""
    
    def __init__(self):
        """Initialize improvement detector."""
        self.baseline_metrics = {}
        self.improvement_history = deque(maxlen=100)
        self.degradation_history = deque(maxlen=100)
        self.last_analysis_time = time.time()
        
    def analyze_performance_changes(self, current_stats: Dict[str, Any], 
                                  previous_stats: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze performance changes and identify improvement/degradation factors.
        
        Args:
            current_stats: Current performance statistics
            previous_stats: Previous performance statistics for comparison
            
        Returns:
            Analysis results with improvement/degradation factors
        """
        analysis = {
            'improvements': [],
            'degradations': [],
            'stable_metrics': [],
            'overall_trend': 'stable',
            'confidence': 0.0
        }
        
        if not previous_stats:
            return analysis
        
        # Analyze success rate changes
        current_success = current_stats.get('success_rate_percent', 0)
        previous_success = previous_stats.get('success_rate_percent', 0)
        
        if current_success > previous_success * 1.1:  # 10% improvement
            analysis['improvements'].append({
                'metric': 'success_rate',
                'improvement_percent': ((current_success - previous_success) / previous_success) * 100,
                'current_value': current_success,
                'previous_value': previous_success,
                'possible_factors': self._identify_success_rate_improvement_factors(current_stats)
            })
        elif current_success < previous_success * 0.9:  # 10% degradation
            analysis['degradations'].append({
                'metric': 'success_rate',
                'degradation_percent': ((previous_success - current_success) / previous_success) * 100,
                'current_value': current_success,
                'previous_value': previous_success,
                'possible_factors': self._identify_success_rate_degradation_factors(current_stats)
            })
        else:
            analysis['stable_metrics'].append('success_rate')
        
        # Analyze execution time changes
        current_time = current_stats.get('avg_execution_time_seconds', 0)
        previous_time = previous_stats.get('avg_execution_time_seconds', 0)
        
        if current_time < previous_time * 0.9:  # 10% improvement (faster)
            analysis['improvements'].append({
                'metric': 'execution_time',
                'improvement_percent': ((previous_time - current_time) / previous_time) * 100,
                'current_value': current_time,
                'previous_value': previous_time,
                'possible_factors': self._identify_execution_time_improvement_factors(current_stats)
            })
        elif current_time > previous_time * 1.1:  # 10% degradation (slower)
            analysis['degradations'].append({
                'metric': 'execution_time',
                'degradation_percent': ((current_time - previous_time) / previous_time) * 100,
                'current_value': current_time,
                'previous_value': previous_time,
                'possible_factors': self._identify_execution_time_degradation_factors(current_stats)
            })
        else:
            analysis['stable_metrics'].append('execution_time')
        
        # Analyze fallback rate changes
        current_fallback = current_stats.get('fallback_rate_percent', 0)
        previous_fallback = previous_stats.get('fallback_rate_percent', 0)
        
        if current_fallback < previous_fallback * 0.9:  # Fewer fallbacks is good
            analysis['improvements'].append({
                'metric': 'fallback_rate',
                'improvement_percent': ((previous_fallback - current_fallback) / previous_fallback) * 100,
                'current_value': current_fallback,
                'previous_value': previous_fallback,
                'possible_factors': ['Better element detection', 'Improved accessibility API usage']
            })
        elif current_fallback > previous_fallback * 1.1:  # More fallbacks is bad
            analysis['degradations'].append({
                'metric': 'fallback_rate',
                'degradation_percent': ((current_fallback - previous_fallback) / previous_fallback) * 100,
                'current_value': current_fallback,
                'previous_value': previous_fallback,
                'possible_factors': ['Application changes', 'Accessibility API issues', 'System performance']
            })
        else:
            analysis['stable_metrics'].append('fallback_rate')
        
        # Determine overall trend
        improvement_count = len(analysis['improvements'])
        degradation_count = len(analysis['degradations'])
        
        if improvement_count > degradation_count:
            analysis['overall_trend'] = 'improving'
        elif degradation_count > improvement_count:
            analysis['overall_trend'] = 'degrading'
        else:
            analysis['overall_trend'] = 'stable'
        
        # Calculate confidence based on data quality
        total_executions = current_stats.get('total_executions', 0)
        analysis['confidence'] = min(1.0, total_executions / 50.0)  # Full confidence at 50+ executions
        
        return analysis
    
    def _identify_success_rate_improvement_factors(self, stats: Dict[str, Any]) -> List[str]:
        """Identify possible factors for success rate improvement."""
        factors = []
        
        # Check if element detection time improved
        if stats.get('avg_element_detection_time_seconds', 0) < 0.5:
            factors.append('Faster element detection')
        
        # Check if specific apps are performing better
        app_performance = stats.get('app_performance', {})
        for app, app_stats in app_performance.items():
            if app_stats.get('success_rate_percent', 0) > 80:
                factors.append(f'Improved {app} compatibility')
        
        # Check if fallback rate decreased
        if stats.get('fallback_rate_percent', 0) < 20:
            factors.append('Reduced fallback to vision system')
        
        return factors or ['General system optimization']
    
    def _identify_success_rate_degradation_factors(self, stats: Dict[str, Any]) -> List[str]:
        """Identify possible factors for success rate degradation."""
        factors = []
        
        # Check if element detection time increased
        if stats.get('avg_element_detection_time_seconds', 0) > 2.0:
            factors.append('Slower element detection')
        
        # Check if specific apps are performing poorly
        app_performance = stats.get('app_performance', {})
        for app, app_stats in app_performance.items():
            if app_stats.get('consecutive_failures', 0) > 3:
                factors.append(f'{app} compatibility issues')
        
        # Check if fallback rate increased
        if stats.get('fallback_rate_percent', 0) > 50:
            factors.append('Increased fallback to vision system')
        
        return factors or ['Unknown system changes']
    
    def _identify_execution_time_improvement_factors(self, stats: Dict[str, Any]) -> List[str]:
        """Identify possible factors for execution time improvement."""
        factors = []
        
        if stats.get('avg_element_detection_time_seconds', 0) < 0.3:
            factors.append('Optimized element detection algorithms')
        
        if stats.get('avg_matching_time_seconds', 0) < 0.1:
            factors.append('Improved text matching performance')
        
        return factors or ['System performance optimization']
    
    def _identify_execution_time_degradation_factors(self, stats: Dict[str, Any]) -> List[str]:
        """Identify possible factors for execution time degradation."""
        factors = []
        
        if stats.get('avg_element_detection_time_seconds', 0) > 1.0:
            factors.append('Slower element detection')
        
        if stats.get('avg_matching_time_seconds', 0) > 0.5:
            factors.append('Slower text matching')
        
        return factors or ['System performance degradation']


class PerformanceReportingSystem:
    """
    Comprehensive performance reporting and feedback system.
    
    Provides real-time feedback, trend analysis, and detailed performance reports
    with actionable recommendations.
    """
    
    def __init__(self, monitor: FastPathPerformanceMonitor = None):
        """
        Initialize performance reporting system.
        
        Args:
            monitor: Fast path performance monitor instance
        """
        self.monitor = monitor or fast_path_performance_monitor
        self.improvement_detector = PerformanceImprovementDetector()
        
        # Report storage
        self.reports_history = deque(maxlen=100)
        self.feedback_history = deque(maxlen=200)
        
        # Baseline tracking
        self.baseline_stats = None
        self.last_report_time = time.time()
        self.report_interval = 300  # 5 minutes
        
        # Feedback thresholds
        self.excellent_threshold = 90.0  # % success rate
        self.good_threshold = 75.0
        self.fair_threshold = 60.0
        self.poor_threshold = 40.0
        
        logger.info("Performance reporting system initialized")
    
    def generate_real_time_feedback(self) -> FeedbackMessage:
        """
        Generate real-time feedback about fast path effectiveness.
        
        Returns:
            Real-time feedback message
        """
        try:
            # Get current performance statistics
            stats = self.monitor.get_performance_statistics(time_window_minutes=15)
            success_rate = stats['success_rate_percent']
            avg_time = stats['avg_execution_time_seconds']
            total_executions = stats['total_executions']
            
            # Determine feedback type and message
            if total_executions == 0:
                return FeedbackMessage(
                    message_type="info",
                    title="No Recent Activity",
                    message="No fast path executions in the last 15 minutes",
                    details={'stats': stats}
                )
            
            # Generate feedback based on performance
            if success_rate >= self.excellent_threshold:
                return FeedbackMessage(
                    message_type="success",
                    title="Excellent Performance",
                    message=f"Fast path performing excellently with {success_rate:.1f}% success rate and {avg_time:.2f}s average execution time",
                    details={
                        'success_rate': success_rate,
                        'avg_time': avg_time,
                        'total_executions': total_executions,
                        'performance_level': 'excellent'
                    }
                )
            
            elif success_rate >= self.good_threshold:
                return FeedbackMessage(
                    message_type="success",
                    title="Good Performance",
                    message=f"Fast path performing well with {success_rate:.1f}% success rate and {avg_time:.2f}s average execution time",
                    details={
                        'success_rate': success_rate,
                        'avg_time': avg_time,
                        'total_executions': total_executions,
                        'performance_level': 'good'
                    },
                    suggested_actions=["Continue current usage patterns"]
                )
            
            elif success_rate >= self.fair_threshold:
                return FeedbackMessage(
                    message_type="warning",
                    title="Fair Performance",
                    message=f"Fast path performance is fair with {success_rate:.1f}% success rate. Consider optimization.",
                    details={
                        'success_rate': success_rate,
                        'avg_time': avg_time,
                        'total_executions': total_executions,
                        'performance_level': 'fair'
                    },
                    action_required=True,
                    suggested_actions=[
                        "Check application compatibility",
                        "Review element detection strategies",
                        "Monitor for specific app issues"
                    ]
                )
            
            elif success_rate >= self.poor_threshold:
                return FeedbackMessage(
                    message_type="warning",
                    title="Poor Performance",
                    message=f"Fast path performance is poor with {success_rate:.1f}% success rate. Optimization needed.",
                    details={
                        'success_rate': success_rate,
                        'avg_time': avg_time,
                        'total_executions': total_executions,
                        'performance_level': 'poor'
                    },
                    action_required=True,
                    suggested_actions=[
                        "Run comprehensive diagnostics",
                        "Check accessibility permissions",
                        "Review application-specific strategies",
                        "Consider system performance optimization"
                    ]
                )
            
            else:
                return FeedbackMessage(
                    message_type="error",
                    title="Critical Performance Issues",
                    message=f"Fast path performance is critical with {success_rate:.1f}% success rate. Immediate action required.",
                    details={
                        'success_rate': success_rate,
                        'avg_time': avg_time,
                        'total_executions': total_executions,
                        'performance_level': 'critical'
                    },
                    action_required=True,
                    suggested_actions=[
                        "Run full system diagnostics immediately",
                        "Check accessibility permissions and API availability",
                        "Review system logs for errors",
                        "Consider switching to vision-only mode temporarily"
                    ]
                )
        
        except Exception as e:
            logger.error(f"Failed to generate real-time feedback: {e}")
            return FeedbackMessage(
                message_type="error",
                title="Feedback Generation Error",
                message=f"Unable to generate performance feedback: {str(e)}",
                details={'error': str(e)}
            )
    
    def detect_performance_improvements(self) -> Dict[str, Any]:
        """
        Detect and analyze performance improvements.
        
        Returns:
            Performance improvement analysis
        """
        try:
            current_stats = self.monitor.get_performance_statistics(time_window_minutes=30)
            
            # Get previous stats for comparison
            previous_stats = None
            if len(self.reports_history) > 0:
                previous_report = self.reports_history[-1]
                previous_stats = previous_report.summary
            
            # Analyze changes
            analysis = self.improvement_detector.analyze_performance_changes(
                current_stats, previous_stats
            )
            
            # Generate improvement summary
            improvement_summary = {
                'timestamp': time.time(),
                'has_improvements': len(analysis['improvements']) > 0,
                'has_degradations': len(analysis['degradations']) > 0,
                'overall_trend': analysis['overall_trend'],
                'confidence': analysis['confidence'],
                'improvements': analysis['improvements'],
                'degradations': analysis['degradations'],
                'stable_metrics': analysis['stable_metrics'],
                'recommendations': self._generate_improvement_recommendations(analysis)
            }
            
            return improvement_summary
            
        except Exception as e:
            logger.error(f"Failed to detect performance improvements: {e}")
            return {
                'timestamp': time.time(),
                'error': str(e),
                'has_improvements': False,
                'has_degradations': False
            }
    
    def _generate_improvement_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on performance analysis."""
        recommendations = []
        
        if analysis['overall_trend'] == 'improving':
            recommendations.append("Performance is improving - continue current optimization efforts")
            
            # Specific improvement recommendations
            for improvement in analysis['improvements']:
                metric = improvement['metric']
                if metric == 'success_rate':
                    recommendations.append("Success rate improvements detected - maintain current element detection strategies")
                elif metric == 'execution_time':
                    recommendations.append("Execution time improvements detected - current performance optimizations are effective")
                elif metric == 'fallback_rate':
                    recommendations.append("Reduced fallback rate - fast path reliability is improving")
        
        elif analysis['overall_trend'] == 'degrading':
            recommendations.append("Performance is degrading - investigate and address issues")
            
            # Specific degradation recommendations
            for degradation in analysis['degradations']:
                metric = degradation['metric']
                if metric == 'success_rate':
                    recommendations.append("Success rate declining - check application compatibility and accessibility permissions")
                elif metric == 'execution_time':
                    recommendations.append("Execution time increasing - check system performance and optimize algorithms")
                elif metric == 'fallback_rate':
                    recommendations.append("Increased fallback rate - review element detection strategies")
        
        else:
            recommendations.append("Performance is stable - monitor for changes and maintain current strategies")
        
        return recommendations
    
    def generate_performance_summary_report(self, time_period_hours: float = 24.0) -> PerformanceReport:
        """
        Generate comprehensive performance summary report.
        
        Args:
            time_period_hours: Time period for the report in hours
            
        Returns:
            Comprehensive performance report
        """
        try:
            # Get performance statistics
            time_window_minutes = int(time_period_hours * 60)
            stats = self.monitor.get_performance_statistics(time_window_minutes=time_window_minutes)
            
            # Get improvement analysis
            improvement_analysis = self.detect_performance_improvements()
            
            # Calculate health score
            health_score = self._calculate_health_score(stats)
            
            # Generate recommendations
            recommendations = self._generate_comprehensive_recommendations(stats, improvement_analysis)
            
            # Get recent alerts
            recent_alerts = [
                {
                    'timestamp': alert['timestamp'],
                    'type': alert['type'],
                    'severity': alert['severity'],
                    'message': alert['message']
                }
                for alert in stats.get('recent_alerts', [])
            ]
            
            # Create report
            report = PerformanceReport(
                report_id=f"perf_report_{int(time.time())}",
                time_period_hours=time_period_hours,
                summary=stats,
                trends={
                    'overall_trend': improvement_analysis.get('overall_trend', 'stable'),
                    'success_rate_trend': stats.get('performance_trends', {}).get('success_rate_trend', 'stable'),
                    'execution_time_trend': stats.get('performance_trends', {}).get('execution_time_trend', 'stable'),
                    'confidence': improvement_analysis.get('confidence', 0.0)
                },
                recommendations=recommendations,
                alerts=recent_alerts,
                app_performance=stats.get('app_performance', {}),
                improvement_factors=[
                    factor for improvement in improvement_analysis.get('improvements', [])
                    for factor in improvement.get('possible_factors', [])
                ],
                degradation_factors=[
                    factor for degradation in improvement_analysis.get('degradations', [])
                    for factor in degradation.get('possible_factors', [])
                ],
                health_score=health_score,
                metadata={
                    'generated_by': 'PerformanceReportingSystem',
                    'monitor_version': '1.0.0',
                    'data_quality': 'high' if stats.get('total_executions', 0) > 50 else 'medium'
                }
            )
            
            # Store report
            self.reports_history.append(report)
            self.last_report_time = time.time()
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return PerformanceReport(
                report_id=f"error_report_{int(time.time())}",
                time_period_hours=time_period_hours,
                summary={'error': str(e)},
                recommendations=[f"Report generation failed: {str(e)}"]
            )
    
    def _calculate_health_score(self, stats: Dict[str, Any]) -> float:
        """Calculate overall performance health score (0-100)."""
        try:
            score = 100.0
            
            # Success rate impact (40% of score)
            success_rate = stats.get('success_rate_percent', 0)
            if success_rate < 50:
                score -= 40
            elif success_rate < 70:
                score -= 20
            elif success_rate < 90:
                score -= 10
            
            # Execution time impact (30% of score)
            avg_time = stats.get('avg_execution_time_seconds', 0)
            if avg_time > 3.0:
                score -= 30
            elif avg_time > 2.0:
                score -= 20
            elif avg_time > 1.0:
                score -= 10
            
            # Fallback rate impact (20% of score)
            fallback_rate = stats.get('fallback_rate_percent', 0)
            if fallback_rate > 50:
                score -= 20
            elif fallback_rate > 30:
                score -= 10
            elif fallback_rate > 15:
                score -= 5
            
            # Alert severity impact (10% of score)
            recent_alerts = stats.get('recent_alerts', [])
            critical_alerts = sum(1 for alert in recent_alerts if alert.get('severity') == 'critical')
            high_alerts = sum(1 for alert in recent_alerts if alert.get('severity') == 'high')
            
            score -= critical_alerts * 5
            score -= high_alerts * 2
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Health score calculation failed: {e}")
            return 50.0  # Default to medium health
    
    def _generate_comprehensive_recommendations(self, stats: Dict[str, Any], 
                                              improvement_analysis: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations based on all available data."""
        recommendations = []
        
        success_rate = stats.get('success_rate_percent', 0)
        avg_time = stats.get('avg_execution_time_seconds', 0)
        fallback_rate = stats.get('fallback_rate_percent', 0)
        total_executions = stats.get('total_executions', 0)
        
        # Data quality recommendations
        if total_executions < 10:
            recommendations.append("Insufficient data for reliable analysis - continue using the system to gather more metrics")
        
        # Success rate recommendations
        if success_rate < 50:
            recommendations.append("Critical: Success rate below 50% - run comprehensive diagnostics immediately")
            recommendations.append("Check accessibility permissions and API availability")
            recommendations.append("Consider temporarily switching to vision-only mode")
        elif success_rate < 70:
            recommendations.append("Success rate needs improvement - check application compatibility")
            recommendations.append("Review element detection strategies for failing applications")
        
        # Execution time recommendations
        if avg_time > 3.0:
            recommendations.append("Execution time is too slow - optimize element detection algorithms")
            recommendations.append("Check system performance and available resources")
        elif avg_time > 1.5:
            recommendations.append("Consider optimizing element detection for better performance")
        
        # Fallback rate recommendations
        if fallback_rate > 50:
            recommendations.append("High fallback rate indicates fast path reliability issues")
            recommendations.append("Focus on improving element detection accuracy")
        
        # Application-specific recommendations
        app_performance = stats.get('app_performance', {})
        problematic_apps = [
            app for app, app_stats in app_performance.items()
            if app_stats.get('success_rate_percent', 0) < 30 and app_stats.get('total_attempts', 0) > 5
        ]
        
        if problematic_apps:
            recommendations.append(f"Develop specific strategies for problematic applications: {', '.join(problematic_apps)}")
        
        # Trend-based recommendations
        if improvement_analysis.get('overall_trend') == 'improving':
            recommendations.append("Performance is improving - continue current optimization efforts")
        elif improvement_analysis.get('overall_trend') == 'degrading':
            recommendations.append("Performance is degrading - investigate recent system changes")
        
        # Add improvement-specific recommendations
        recommendations.extend(improvement_analysis.get('recommendations', []))
        
        return recommendations
    
    def export_performance_report(self, report: PerformanceReport, format: str = 'json') -> str:
        """
        Export performance report in specified format.
        
        Args:
            report: Performance report to export
            format: Export format ('json', 'html', 'text')
            
        Returns:
            Formatted report string
        """
        try:
            if format.lower() == 'json':
                return json.dumps(asdict(report), indent=2, default=str)
            
            elif format.lower() == 'html':
                return self._generate_html_report(report)
            
            elif format.lower() == 'text':
                return self._generate_text_report(report)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return f"Export failed: {e}"
    
    def _generate_html_report(self, report: PerformanceReport) -> str:
        """Generate HTML format report."""
        html = f"""
        <html>
        <head><title>AURA Fast Path Performance Report</title></head>
        <body>
        <h1>Fast Path Performance Report</h1>
        <p><strong>Generated:</strong> {datetime.fromtimestamp(report.timestamp)}</p>
        <p><strong>Time Period:</strong> {report.time_period_hours} hours</p>
        <p><strong>Health Score:</strong> {report.health_score:.1f}/100</p>
        
        <h2>Summary</h2>
        <ul>
        <li>Total Executions: {report.summary.get('total_executions', 0)}</li>
        <li>Success Rate: {report.summary.get('success_rate_percent', 0):.1f}%</li>
        <li>Average Execution Time: {report.summary.get('avg_execution_time_seconds', 0):.2f}s</li>
        <li>Fallback Rate: {report.summary.get('fallback_rate_percent', 0):.1f}%</li>
        </ul>
        
        <h2>Recommendations</h2>
        <ul>
        {''.join(f'<li>{rec}</li>' for rec in report.recommendations)}
        </ul>
        
        <h2>Trends</h2>
        <p>Overall Trend: {report.trends.get('overall_trend', 'stable')}</p>
        
        </body>
        </html>
        """
        return html
    
    def _generate_text_report(self, report: PerformanceReport) -> str:
        """Generate plain text format report."""
        text = f"""
AURA Fast Path Performance Report
================================

Generated: {datetime.fromtimestamp(report.timestamp)}
Time Period: {report.time_period_hours} hours
Health Score: {report.health_score:.1f}/100

Summary:
--------
Total Executions: {report.summary.get('total_executions', 0)}
Success Rate: {report.summary.get('success_rate_percent', 0):.1f}%
Average Execution Time: {report.summary.get('avg_execution_time_seconds', 0):.2f}s
Fallback Rate: {report.summary.get('fallback_rate_percent', 0):.1f}%

Trends:
-------
Overall Trend: {report.trends.get('overall_trend', 'stable')}

Recommendations:
---------------
{chr(10).join(f'• {rec}' for rec in report.recommendations)}

Alerts:
-------
{chr(10).join(f'• [{alert["severity"].upper()}] {alert["message"]}' for alert in report.alerts)}
        """
        return text.strip()
    
    def get_feedback_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get feedback message history for specified time period."""
        cutoff_time = time.time() - (hours * 3600)
        return [
            asdict(feedback) for feedback in self.feedback_history
            if feedback.timestamp >= cutoff_time
        ]
    
    def should_generate_report(self) -> bool:
        """Check if it's time to generate a new performance report."""
        return time.time() - self.last_report_time >= self.report_interval


# Global performance reporting system instance
performance_reporting_system = PerformanceReportingSystem()
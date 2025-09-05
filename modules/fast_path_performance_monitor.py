# modules/fast_path_performance_monitor.py
"""
Fast Path Performance Monitor for AURA Click Debugging Enhancement

Provides real-time performance tracking specifically for fast path execution,
including success rate monitoring, performance degradation detection, and alerting.
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import statistics
import json

logger = logging.getLogger(__name__)


@dataclass
class FastPathMetric:
    """Individual fast path execution metric."""
    timestamp: float = field(default_factory=time.time)
    command: str = ""
    app_name: Optional[str] = None
    execution_time: float = 0.0
    element_detection_time: float = 0.0
    matching_time: float = 0.0
    success: bool = False
    element_found: bool = False
    fallback_triggered: bool = False
    error_message: str = ""
    search_strategy: str = ""
    element_count: int = 0
    similarity_score: float = 0.0
    accessibility_api_available: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert for degradation detection."""
    timestamp: float = field(default_factory=time.time)
    alert_type: str = ""  # 'degradation', 'improvement', 'threshold'
    severity: str = ""    # 'low', 'medium', 'high', 'critical'
    message: str = ""
    current_value: float = 0.0
    threshold_value: float = 0.0
    recommendation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class RollingAverageCalculator:
    """Calculate rolling averages for performance metrics."""
    
    def __init__(self, window_size: int = 50):
        """
        Initialize rolling average calculator.
        
        Args:
            window_size: Number of values to include in rolling average
        """
        self.window_size = window_size
        self.values = deque(maxlen=window_size)
        self.lock = threading.Lock()
    
    def add_value(self, value: float) -> None:
        """Add a new value to the rolling average."""
        with self.lock:
            self.values.append(value)
    
    def get_average(self) -> float:
        """Get current rolling average."""
        with self.lock:
            if not self.values:
                return 0.0
            return sum(self.values) / len(self.values)
    
    def get_trend(self, recent_ratio: float = 0.3) -> str:
        """
        Get trend direction (improving, degrading, stable).
        
        Args:
            recent_ratio: Ratio of recent values to compare against older values
            
        Returns:
            Trend direction string
        """
        with self.lock:
            if len(self.values) < 10:
                return "insufficient_data"
            
            recent_count = max(1, int(len(self.values) * recent_ratio))
            if recent_count >= len(self.values):
                return "insufficient_data"
            
            recent_values = list(self.values)[-recent_count:]
            older_values = list(self.values)[:-recent_count]
            
            if not older_values or not recent_values:
                return "insufficient_data"
            
            recent_avg = sum(recent_values) / len(recent_values)
            older_avg = sum(older_values) / len(older_values)
            
            # Use a more conservative threshold for stability
            if abs(recent_avg - older_avg) < 0.01:  # Very small difference
                return "stable"
            elif recent_avg > older_avg * 1.1:  # 10% improvement threshold
                return "improving"
            elif recent_avg < older_avg * 0.9:  # 10% degradation threshold
                return "degrading"
            else:
                return "stable"


class FastPathPerformanceMonitor:
    """
    Real-time performance monitoring for fast path execution.
    
    Tracks success rates, execution times, and performance trends with
    alerting for degradation and improvement detection.
    """
    
    def __init__(self, max_metrics: int = 1000, alert_callback: Optional[Callable] = None):
        """
        Initialize fast path performance monitor.
        
        Args:
            max_metrics: Maximum number of metrics to keep in memory
            alert_callback: Optional callback function for performance alerts
        """
        self.max_metrics = max_metrics
        self.alert_callback = alert_callback
        
        # Metrics storage
        self.metrics = deque(maxlen=max_metrics)
        self.metrics_lock = threading.Lock()
        
        # Rolling averages
        self.success_rate_calculator = RollingAverageCalculator(window_size=50)
        self.execution_time_calculator = RollingAverageCalculator(window_size=50)
        self.element_detection_time_calculator = RollingAverageCalculator(window_size=50)
        self.matching_time_calculator = RollingAverageCalculator(window_size=50)
        
        # Performance thresholds
        self.success_rate_warning_threshold = 70.0  # %
        self.success_rate_critical_threshold = 50.0  # %
        self.execution_time_warning_threshold = 2.0  # seconds
        self.execution_time_critical_threshold = 5.0  # seconds
        self.degradation_detection_window = 20  # number of recent metrics to analyze
        
        # Alert tracking
        self.recent_alerts = deque(maxlen=100)
        self.alert_cooldown = {}  # Alert type -> last alert time
        self.alert_cooldown_duration = 300  # 5 minutes
        
        # Application-specific tracking
        self.app_performance = defaultdict(lambda: {
            'success_rate': RollingAverageCalculator(30),
            'execution_time': RollingAverageCalculator(30),
            'total_attempts': 0,
            'successful_attempts': 0,
            'last_success_time': 0.0,
            'consecutive_failures': 0
        })
        
        # Performance trends
        self.performance_trends = {
            'success_rate_trend': "stable",
            'execution_time_trend': "stable",
            'last_trend_update': time.time()
        }
        
        logger.info(f"Fast path performance monitor initialized with {max_metrics} max metrics")
    
    def record_fast_path_execution(self, metric: FastPathMetric) -> None:
        """
        Record a fast path execution metric.
        
        Args:
            metric: Fast path execution metric to record
        """
        with self.metrics_lock:
            self.metrics.append(metric)
            
            # Update rolling averages
            success_value = 100.0 if metric.success and not metric.fallback_triggered else 0.0
            self.success_rate_calculator.add_value(success_value)
            self.execution_time_calculator.add_value(metric.execution_time)
            self.element_detection_time_calculator.add_value(metric.element_detection_time)
            self.matching_time_calculator.add_value(metric.matching_time)
            
            # Update application-specific tracking
            if metric.app_name:
                app_stats = self.app_performance[metric.app_name]
                app_stats['total_attempts'] += 1
                
                if metric.success and not metric.fallback_triggered:
                    app_stats['successful_attempts'] += 1
                    app_stats['last_success_time'] = metric.timestamp
                    app_stats['consecutive_failures'] = 0
                else:
                    app_stats['consecutive_failures'] += 1
                
                app_stats['success_rate'].add_value(success_value)
                app_stats['execution_time'].add_value(metric.execution_time)
            
            # Check for performance alerts periodically to avoid overhead
            if len(self.metrics) % 10 == 0 and len(self.metrics) >= 10:  # Check every 10th metric after we have some data
                self._check_performance_alerts(metric)
            
            # Update performance trends periodically
            if time.time() - self.performance_trends['last_trend_update'] > 60:  # Every minute
                self._update_performance_trends()
    
    def _check_performance_alerts(self, latest_metric: FastPathMetric) -> None:
        """Check for performance alerts based on latest metric and trends."""
        current_time = time.time()
        
        # Get current performance statistics
        current_success_rate = self.get_current_success_rate()
        current_avg_execution_time = self.execution_time_calculator.get_average()
        
        # Check success rate alerts
        if current_success_rate < self.success_rate_critical_threshold:
            self._trigger_alert(
                alert_type="success_rate_critical",
                severity="critical",
                message=f"Fast path success rate critically low: {current_success_rate:.1f}%",
                current_value=current_success_rate,
                threshold_value=self.success_rate_critical_threshold,
                recommendation="Run comprehensive diagnostics and check accessibility permissions"
            )
        elif current_success_rate < self.success_rate_warning_threshold:
            self._trigger_alert(
                alert_type="success_rate_warning",
                severity="medium",
                message=f"Fast path success rate below optimal: {current_success_rate:.1f}%",
                current_value=current_success_rate,
                threshold_value=self.success_rate_warning_threshold,
                recommendation="Check application compatibility and element detection strategies"
            )
        
        # Check execution time alerts
        if current_avg_execution_time > self.execution_time_critical_threshold:
            self._trigger_alert(
                alert_type="execution_time_critical",
                severity="high",
                message=f"Fast path execution time critically slow: {current_avg_execution_time:.2f}s",
                current_value=current_avg_execution_time,
                threshold_value=self.execution_time_critical_threshold,
                recommendation="Optimize element detection algorithms and check system performance"
            )
        elif current_avg_execution_time > self.execution_time_warning_threshold:
            self._trigger_alert(
                alert_type="execution_time_warning",
                severity="medium",
                message=f"Fast path execution time slower than optimal: {current_avg_execution_time:.2f}s",
                current_value=current_avg_execution_time,
                threshold_value=self.execution_time_warning_threshold,
                recommendation="Consider optimizing accessibility tree traversal"
            )
        
        # Check for performance degradation
        self._check_performance_degradation()
        
        # Check application-specific issues
        if latest_metric.app_name:
            self._check_application_specific_alerts(latest_metric.app_name)
    
    def _check_performance_degradation(self) -> None:
        """Check for performance degradation trends."""
        # Only check trends if we have enough data
        if len(self.metrics) < 20:
            return
            
        success_rate_trend = self.success_rate_calculator.get_trend()
        execution_time_trend = self.execution_time_calculator.get_trend()
        
        if success_rate_trend == "degrading":
            self._trigger_alert(
                alert_type="performance_degradation",
                severity="medium",
                message="Fast path success rate is degrading over time",
                current_value=self.get_current_success_rate(),
                threshold_value=0.0,
                recommendation="Analyze recent failures and check for system changes"
            )
        
        if execution_time_trend == "degrading":
            self._trigger_alert(
                alert_type="performance_degradation",
                severity="medium",
                message="Fast path execution time is increasing over time",
                current_value=self.execution_time_calculator.get_average(),
                threshold_value=0.0,
                recommendation="Check system resources and optimize performance"
            )
        
        # Check for improvement to provide positive feedback
        if success_rate_trend == "improving":
            self._trigger_alert(
                alert_type="performance_improvement",
                severity="low",
                message="Fast path success rate is improving",
                current_value=self.get_current_success_rate(),
                threshold_value=0.0,
                recommendation="Current optimizations are working well"
            )
    
    def _check_application_specific_alerts(self, app_name: str) -> None:
        """Check for application-specific performance issues."""
        app_stats = self.app_performance[app_name]
        
        # Check for consecutive failures
        if app_stats['consecutive_failures'] >= 5:
            self._trigger_alert(
                alert_type="app_consecutive_failures",
                severity="high",
                message=f"Fast path failing consistently for {app_name}: {app_stats['consecutive_failures']} consecutive failures",
                current_value=app_stats['consecutive_failures'],
                threshold_value=5,
                recommendation=f"Check {app_name} accessibility implementation and update detection strategies",
                metadata={'app_name': app_name}
            )
        
        # Check for low app-specific success rate
        app_success_rate = app_stats['success_rate'].get_average()
        if app_stats['total_attempts'] >= 10 and app_success_rate < 30:
            self._trigger_alert(
                alert_type="app_low_success_rate",
                severity="medium",
                message=f"Low fast path success rate for {app_name}: {app_success_rate:.1f}%",
                current_value=app_success_rate,
                threshold_value=30,
                recommendation=f"Develop application-specific detection strategy for {app_name}",
                metadata={'app_name': app_name}
            )
    
    def _trigger_alert(self, alert_type: str, severity: str, message: str, 
                      current_value: float, threshold_value: float, 
                      recommendation: str, metadata: Dict[str, Any] = None) -> None:
        """Trigger a performance alert with cooldown protection."""
        current_time = time.time()
        
        # Check cooldown
        if alert_type in self.alert_cooldown:
            if current_time - self.alert_cooldown[alert_type] < self.alert_cooldown_duration:
                return  # Still in cooldown period
        
        # Create alert
        alert = PerformanceAlert(
            timestamp=current_time,
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_value=current_value,
            threshold_value=threshold_value,
            recommendation=recommendation,
            metadata=metadata or {}
        )
        
        # Store alert
        self.recent_alerts.append(alert)
        self.alert_cooldown[alert_type] = current_time
        
        # Log alert
        log_level = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL
        }.get(severity, logging.INFO)
        
        logger.log(log_level, f"Performance Alert [{severity.upper()}]: {message}")
        
        # Call alert callback if provided
        if self.alert_callback:
            try:
                self.alert_callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def _update_performance_trends(self) -> None:
        """Update performance trend analysis."""
        self.performance_trends.update({
            'success_rate_trend': self.success_rate_calculator.get_trend(),
            'execution_time_trend': self.execution_time_calculator.get_trend(),
            'last_trend_update': time.time()
        })
    
    def get_current_success_rate(self, time_window_minutes: int = 15) -> float:
        """
        Get current fast path success rate.
        
        Args:
            time_window_minutes: Time window for calculation
            
        Returns:
            Success rate percentage
        """
        # Use rolling average for better performance
        return self.success_rate_calculator.get_average()
    
    def get_performance_statistics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics.
        
        Args:
            time_window_minutes: Time window for statistics
            
        Returns:
            Performance statistics dictionary
        """
        cutoff_time = time.time() - (time_window_minutes * 60)
        
        with self.metrics_lock:
            recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return {
                    'time_window_minutes': time_window_minutes,
                    'total_executions': 0,
                    'success_rate_percent': 0.0,
                    'avg_execution_time_seconds': 0.0,
                    'avg_element_detection_time_seconds': 0.0,
                    'avg_matching_time_seconds': 0.0,
                    'fallback_rate_percent': 0.0,
                    'element_found_rate_percent': 0.0,
                    'performance_trends': self.performance_trends,
                    'recent_alerts': [],
                    'app_performance': {}
                }
            
            # Calculate statistics
            total_executions = len(recent_metrics)
            successful_executions = sum(1 for m in recent_metrics if m.success and not m.fallback_triggered)
            fallback_executions = sum(1 for m in recent_metrics if m.fallback_triggered)
            element_found_executions = sum(1 for m in recent_metrics if m.element_found)
            
            success_rate = (successful_executions / total_executions) * 100
            fallback_rate = (fallback_executions / total_executions) * 100
            element_found_rate = (element_found_executions / total_executions) * 100
            
            avg_execution_time = statistics.mean(m.execution_time for m in recent_metrics)
            avg_element_detection_time = statistics.mean(m.element_detection_time for m in recent_metrics)
            avg_matching_time = statistics.mean(m.matching_time for m in recent_metrics)
            
            # Get recent alerts
            alert_cutoff = time.time() - (time_window_minutes * 60)
            recent_alerts = [
                {
                    'timestamp': alert.timestamp,
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'recommendation': alert.recommendation
                }
                for alert in self.recent_alerts
                if alert.timestamp >= alert_cutoff
            ]
            
            # Get application performance
            app_performance = {}
            for app_name, stats in self.app_performance.items():
                if stats['total_attempts'] > 0:
                    app_performance[app_name] = {
                        'total_attempts': stats['total_attempts'],
                        'successful_attempts': stats['successful_attempts'],
                        'success_rate_percent': stats['success_rate'].get_average(),
                        'avg_execution_time_seconds': stats['execution_time'].get_average(),
                        'consecutive_failures': stats['consecutive_failures'],
                        'last_success_time': stats['last_success_time']
                    }
            
            return {
                'timestamp': time.time(),
                'time_window_minutes': time_window_minutes,
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'success_rate_percent': success_rate,
                'avg_execution_time_seconds': avg_execution_time,
                'avg_element_detection_time_seconds': avg_element_detection_time,
                'avg_matching_time_seconds': avg_matching_time,
                'fallback_rate_percent': fallback_rate,
                'element_found_rate_percent': element_found_rate,
                'performance_trends': self.performance_trends.copy(),
                'recent_alerts': recent_alerts,
                'app_performance': app_performance,
                'rolling_averages': {
                    'success_rate': self.success_rate_calculator.get_average(),
                    'execution_time': self.execution_time_calculator.get_average(),
                    'element_detection_time': self.element_detection_time_calculator.get_average(),
                    'matching_time': self.matching_time_calculator.get_average()
                }
            }
    
    def should_suggest_diagnostics(self) -> bool:
        """
        Check if diagnostic tools should be suggested based on performance.
        
        Returns:
            True if diagnostics should be suggested
        """
        current_success_rate = self.get_current_success_rate()
        return current_success_rate < 50.0
    
    def get_performance_feedback_message(self) -> str:
        """
        Get real-time performance feedback message for user.
        
        Returns:
            Human-readable performance feedback message
        """
        stats = self.get_performance_statistics(time_window_minutes=15)
        success_rate = stats['success_rate_percent']
        avg_time = stats['avg_execution_time_seconds']
        
        if success_rate >= 90:
            return f"✅ Fast path performing excellently: {success_rate:.1f}% success rate, {avg_time:.2f}s average time"
        elif success_rate >= 70:
            return f"✅ Fast path performing well: {success_rate:.1f}% success rate, {avg_time:.2f}s average time"
        elif success_rate >= 50:
            return f"⚠️ Fast path performance degraded: {success_rate:.1f}% success rate, {avg_time:.2f}s average time"
        else:
            return f"❌ Fast path performance critical: {success_rate:.1f}% success rate - diagnostics recommended"
    
    def export_performance_data(self, format: str = 'json', time_window_minutes: int = 60) -> str:
        """
        Export performance data in specified format.
        
        Args:
            format: Export format ('json', 'csv')
            time_window_minutes: Time window for export
            
        Returns:
            Formatted performance data
        """
        try:
            stats = self.get_performance_statistics(time_window_minutes)
            
            if format.lower() == 'json':
                return json.dumps(stats, indent=2, default=str)
            elif format.lower() == 'csv':
                lines = [
                    "metric,value,timestamp",
                    f"success_rate_percent,{stats['success_rate_percent']},{stats['timestamp']}",
                    f"avg_execution_time_seconds,{stats['avg_execution_time_seconds']},{stats['timestamp']}",
                    f"fallback_rate_percent,{stats['fallback_rate_percent']},{stats['timestamp']}",
                    f"total_executions,{stats['total_executions']},{stats['timestamp']}"
                ]
                return '\n'.join(lines)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export performance data: {e}")
            return f"Export failed: {e}"


# Global fast path performance monitor instance
fast_path_performance_monitor = FastPathPerformanceMonitor()
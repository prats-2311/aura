"""
Performance Dashboard for AURA

This module provides a comprehensive performance dashboard and alerting system
for monitoring the explain selected text feature and other AURA operations.
It includes real-time metrics, trend analysis, and optimization recommendations.
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import statistics


@dataclass
class PerformanceTrend:
    """Performance trend analysis result."""
    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str  # 'improving', 'degrading', 'stable'
    significance: str  # 'high', 'medium', 'low'


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation."""
    category: str
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    expected_improvement: str
    implementation_effort: str  # 'low', 'medium', 'high'


class PerformanceDashboard:
    """
    Real-time performance dashboard for AURA operations.
    
    Provides comprehensive monitoring, trend analysis, and optimization
    recommendations for the explain selected text feature.
    """
    
    def __init__(self, performance_monitor):
        """
        Initialize performance dashboard.
        
        Args:
            performance_monitor: PerformanceMonitor instance to track
        """
        self.logger = logging.getLogger(__name__)
        self.monitor = performance_monitor
        
        # Dashboard configuration
        self.update_interval = 30.0  # Update dashboard every 30 seconds
        self.trend_analysis_window = 300.0  # 5 minutes for trend analysis
        self.alert_cooldown = 60.0  # 1 minute cooldown between similar alerts
        
        # Dashboard state
        self._dashboard_data = {}
        self._last_update = 0.0
        self._last_alerts = {}
        self._trend_history = []
        
        # Background update thread
        self._update_thread = None
        self._stop_updates = threading.Event()
        
        # Alert callbacks
        self._alert_callbacks = []
        
        # Start dashboard updates
        self._start_dashboard_updates()
        
        self.logger.info("Performance dashboard initialized")
    
    def _start_dashboard_updates(self) -> None:
        """Start background dashboard update thread."""
        def update_worker():
            while not self._stop_updates.wait(self.update_interval):
                try:
                    self._update_dashboard_data()
                    self._analyze_performance_trends()
                    self._check_performance_alerts()
                except Exception as e:
                    self.logger.error(f"Dashboard update error: {e}")
        
        self._update_thread = threading.Thread(target=update_worker, daemon=True)
        self._update_thread.start()
    
    def _update_dashboard_data(self) -> None:
        """Update dashboard data with current metrics."""
        current_time = time.time()
        
        # Get current performance summary
        summary = self.monitor.get_performance_summary()
        
        # Get operation-specific statistics
        text_capture_stats = self.monitor.get_operation_stats('text_capture')
        explanation_stats = self.monitor.get_operation_stats('explanation_generation')
        
        # Get cache statistics
        cache_stats = self.monitor.get_cache_stats()
        
        # Calculate derived metrics
        overall_health_score = self._calculate_health_score(summary, text_capture_stats, explanation_stats)
        
        # Update dashboard data
        self._dashboard_data = {
            'timestamp': current_time,
            'overall_health_score': overall_health_score,
            'summary': summary,
            'text_capture': text_capture_stats,
            'explanation_generation': explanation_stats,
            'cache_performance': cache_stats,
            'recent_alerts': self.monitor.get_recent_alerts(5),
            'optimization_recommendations': self._generate_optimization_recommendations()
        }
        
        self._last_update = current_time
    
    def _calculate_health_score(self, summary: Dict[str, Any], 
                               text_capture_stats: Dict[str, Any],
                               explanation_stats: Dict[str, Any]) -> float:
        """
        Calculate overall system health score (0-100).
        
        Args:
            summary: Overall performance summary
            text_capture_stats: Text capture performance statistics
            explanation_stats: Explanation generation performance statistics
            
        Returns:
            Health score from 0 (poor) to 100 (excellent)
        """
        score = 100.0
        
        # Success rate impact (40% of score)
        overall_success_rate = summary.get('success_rate', 0.0)
        score *= (0.6 + 0.4 * overall_success_rate)
        
        # Performance impact (30% of score)
        avg_duration = summary.get('avg_duration_ms', 0.0)
        if avg_duration > 0:
            # Penalize slow operations (target: < 2000ms)
            performance_factor = min(1.0, 2000.0 / avg_duration)
            score *= (0.7 + 0.3 * performance_factor)
        
        # Cache effectiveness impact (20% of score)
        cache_stats = self.monitor.get_cache_stats()
        avg_hit_rate = 0.0
        cache_count = 0
        
        for cache_name, stats in cache_stats.items():
            if 'hit_rate' in stats:
                avg_hit_rate += stats['hit_rate']
                cache_count += 1
        
        if cache_count > 0:
            avg_hit_rate /= cache_count
            score *= (0.8 + 0.2 * avg_hit_rate)
        
        # Alert frequency impact (10% of score)
        recent_alerts = len(self.monitor.get_recent_alerts(10))
        alert_penalty = min(0.1, recent_alerts * 0.01)
        score *= (1.0 - alert_penalty)
        
        return max(0.0, min(100.0, score))
    
    def _analyze_performance_trends(self) -> None:
        """Analyze performance trends over time."""
        current_time = time.time()
        
        # Get current metrics
        current_summary = self.monitor.get_performance_summary()
        
        # Store trend data point
        trend_point = {
            'timestamp': current_time,
            'success_rate': current_summary.get('success_rate', 0.0),
            'avg_duration_ms': current_summary.get('avg_duration_ms', 0.0),
            'total_operations': current_summary.get('total_operations', 0),
            'health_score': self._dashboard_data.get('overall_health_score', 0.0)
        }
        
        self._trend_history.append(trend_point)
        
        # Keep only recent history (last hour)
        cutoff_time = current_time - 3600.0
        self._trend_history = [p for p in self._trend_history if p['timestamp'] > cutoff_time]
        
        # Analyze trends if we have enough data
        if len(self._trend_history) >= 10:
            trends = self._calculate_trends()
            self._dashboard_data['trends'] = trends
    
    def _calculate_trends(self) -> List[PerformanceTrend]:
        """Calculate performance trends from historical data."""
        trends = []
        
        if len(self._trend_history) < 10:
            return trends
        
        # Split data into recent and previous periods
        mid_point = len(self._trend_history) // 2
        recent_data = self._trend_history[mid_point:]
        previous_data = self._trend_history[:mid_point]
        
        # Calculate trends for key metrics
        metrics = ['success_rate', 'avg_duration_ms', 'health_score']
        
        for metric in metrics:
            recent_values = [p[metric] for p in recent_data if p[metric] is not None]
            previous_values = [p[metric] for p in previous_data if p[metric] is not None]
            
            if recent_values and previous_values:
                recent_avg = statistics.mean(recent_values)
                previous_avg = statistics.mean(previous_values)
                
                if previous_avg > 0:
                    change_percent = ((recent_avg - previous_avg) / previous_avg) * 100
                else:
                    change_percent = 0.0
                
                # Determine trend direction and significance
                if abs(change_percent) < 5.0:
                    direction = 'stable'
                    significance = 'low'
                elif change_percent > 0:
                    direction = 'improving' if metric != 'avg_duration_ms' else 'degrading'
                    significance = 'high' if abs(change_percent) > 20 else 'medium'
                else:
                    direction = 'degrading' if metric != 'avg_duration_ms' else 'improving'
                    significance = 'high' if abs(change_percent) > 20 else 'medium'
                
                trend = PerformanceTrend(
                    metric_name=metric,
                    current_value=recent_avg,
                    previous_value=previous_avg,
                    change_percent=change_percent,
                    trend_direction=direction,
                    significance=significance
                )
                trends.append(trend)
        
        return trends
    
    def _check_performance_alerts(self) -> None:
        """Check for performance issues and trigger alerts."""
        current_time = time.time()
        
        # Check health score
        health_score = self._dashboard_data.get('overall_health_score', 100.0)
        if health_score < 70.0:
            self._trigger_alert('health_score_low', {
                'current_score': health_score,
                'threshold': 70.0,
                'severity': 'high' if health_score < 50.0 else 'medium'
            })
        
        # Check success rate trends
        trends = self._dashboard_data.get('trends', [])
        for trend in trends:
            if trend.metric_name == 'success_rate' and trend.trend_direction == 'degrading':
                if trend.significance == 'high':
                    self._trigger_alert('success_rate_degrading', {
                        'current_rate': trend.current_value,
                        'change_percent': trend.change_percent,
                        'severity': 'high'
                    })
        
        # Check cache performance
        cache_stats = self._dashboard_data.get('cache_performance', {})
        for cache_name, stats in cache_stats.items():
            hit_rate = stats.get('hit_rate', 0.0)
            if hit_rate < 0.2:  # Less than 20% hit rate
                self._trigger_alert('cache_performance_low', {
                    'cache_name': cache_name,
                    'hit_rate': hit_rate,
                    'threshold': 0.2,
                    'severity': 'medium'
                })
    
    def _trigger_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Trigger a performance alert with cooldown."""
        current_time = time.time()
        
        # Check cooldown
        last_alert_time = self._last_alerts.get(alert_type, 0.0)
        if current_time - last_alert_time < self.alert_cooldown:
            return
        
        # Create alert
        alert = {
            'type': alert_type,
            'timestamp': current_time,
            'data': data,
            'message': self._format_alert_message(alert_type, data)
        }
        
        # Log alert
        severity = data.get('severity', 'medium')
        if severity == 'high':
            self.logger.error(f"Performance alert: {alert['message']}")
        else:
            self.logger.warning(f"Performance alert: {alert['message']}")
        
        # Trigger callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
        
        # Update last alert time
        self._last_alerts[alert_type] = current_time
    
    def _format_alert_message(self, alert_type: str, data: Dict[str, Any]) -> str:
        """Format alert message for display."""
        if alert_type == 'health_score_low':
            return f"System health score is low: {data['current_score']:.1f}/100"
        elif alert_type == 'success_rate_degrading':
            return f"Success rate degrading: {data['current_rate']:.1%} ({data['change_percent']:+.1f}%)"
        elif alert_type == 'cache_performance_low':
            return f"Cache '{data['cache_name']}' hit rate is low: {data['hit_rate']:.1%}"
        else:
            return f"Performance alert: {alert_type}"
    
    def _generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on current performance."""
        recommendations = []
        
        # Analyze text capture performance
        text_capture_stats = self._dashboard_data.get('text_capture', {})
        if text_capture_stats:
            success_rate = text_capture_stats.get('success_rate', 1.0)
            avg_duration = text_capture_stats.get('avg_duration_ms', 0.0)
            
            if success_rate < 0.9:
                recommendations.append(OptimizationRecommendation(
                    category='text_capture',
                    priority='high',
                    title='Improve Text Capture Reliability',
                    description=f'Text capture success rate is {success_rate:.1%}. Consider improving fallback mechanisms and error handling.',
                    expected_improvement='10-20% improvement in success rate',
                    implementation_effort='medium'
                ))
            
            if avg_duration > 1000.0:
                recommendations.append(OptimizationRecommendation(
                    category='text_capture',
                    priority='medium',
                    title='Optimize Text Capture Speed',
                    description=f'Text capture is slow (avg: {avg_duration:.0f}ms). Consider caching accessibility connections.',
                    expected_improvement='30-50% reduction in capture time',
                    implementation_effort='low'
                ))
        
        # Analyze explanation generation performance
        explanation_stats = self._dashboard_data.get('explanation_generation', {})
        if explanation_stats:
            avg_duration = explanation_stats.get('avg_duration_ms', 0.0)
            
            if avg_duration > 5000.0:
                recommendations.append(OptimizationRecommendation(
                    category='explanation_generation',
                    priority='high',
                    title='Optimize Explanation Generation',
                    description=f'Explanation generation is slow (avg: {avg_duration:.0f}ms). Consider prompt optimization or model caching.',
                    expected_improvement='20-40% reduction in generation time',
                    implementation_effort='medium'
                ))
        
        # Analyze cache performance
        cache_stats = self._dashboard_data.get('cache_performance', {})
        for cache_name, stats in cache_stats.items():
            hit_rate = stats.get('hit_rate', 0.0)
            if hit_rate < 0.3:
                recommendations.append(OptimizationRecommendation(
                    category='caching',
                    priority='medium',
                    title=f'Improve {cache_name.title()} Cache Effectiveness',
                    description=f'Cache hit rate is low ({hit_rate:.1%}). Consider adjusting TTL or improving cache keys.',
                    expected_improvement='15-25% improvement in response time',
                    implementation_effort='low'
                ))
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))
        
        return recommendations
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data."""
        # Update if data is stale
        if time.time() - self._last_update > self.update_interval:
            self._update_dashboard_data()
        
        return self._dashboard_data.copy()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        dashboard_data = self.get_dashboard_data()
        
        return {
            'report_timestamp': time.time(),
            'health_score': dashboard_data.get('overall_health_score', 0.0),
            'summary': dashboard_data.get('summary', {}),
            'trends': [
                {
                    'metric': trend.metric_name,
                    'direction': trend.trend_direction,
                    'change_percent': trend.change_percent,
                    'significance': trend.significance
                }
                for trend in dashboard_data.get('trends', [])
            ],
            'recommendations': [
                {
                    'category': rec.category,
                    'priority': rec.priority,
                    'title': rec.title,
                    'description': rec.description,
                    'expected_improvement': rec.expected_improvement,
                    'implementation_effort': rec.implementation_effort
                }
                for rec in dashboard_data.get('optimization_recommendations', [])
            ],
            'recent_alerts': dashboard_data.get('recent_alerts', [])
        }
    
    def add_alert_callback(self, callback: callable) -> None:
        """Add callback for performance alerts."""
        self._alert_callbacks.append(callback)
    
    def shutdown(self) -> None:
        """Shutdown dashboard and cleanup resources."""
        if self._update_thread:
            self._stop_updates.set()
            self._update_thread.join(timeout=5)
        
        self.logger.info("Performance dashboard shutdown complete")


def create_performance_dashboard() -> Optional[PerformanceDashboard]:
    """Create and return a performance dashboard instance."""
    try:
        from .performance_monitor import get_performance_monitor
        monitor = get_performance_monitor()
        
        if monitor.enabled:
            return PerformanceDashboard(monitor)
        else:
            return None
    except ImportError:
        return None
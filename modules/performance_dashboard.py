# modules/performance_dashboard.py
"""
Performance Dashboard for AURA

Provides real-time performance monitoring and optimization recommendations.
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import asdict
from datetime import datetime, timedelta

from .performance import (
    performance_monitor,
    connection_pool,
    image_cache,
    parallel_processor
)
from performance_config import *

logger = logging.getLogger(__name__)


class PerformanceDashboard:
    """
    Performance dashboard for monitoring and optimization.
    
    Provides real-time metrics, performance analysis, and optimization recommendations.
    """
    
    def __init__(self):
        """Initialize the performance dashboard."""
        self.start_time = time.time()
        self.last_optimization_check = time.time()
        self.optimization_recommendations = []
        
        logger.info("Performance dashboard initialized")
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """
        Get real-time performance metrics.
        
        Returns:
            Dictionary containing current performance metrics
        """
        try:
            # Get performance summary
            summary = performance_monitor.get_performance_summary(time_window_minutes=5)
            
            # Get system metrics
            system_metrics = performance_monitor.get_system_metrics()
            
            # Get cache statistics
            cache_stats = image_cache.get_cache_stats()
            
            # Get operation statistics
            operation_stats = performance_monitor.get_operation_stats()
            
            # Calculate uptime
            uptime_seconds = time.time() - self.start_time
            
            return {
                'timestamp': time.time(),
                'uptime_seconds': uptime_seconds,
                'uptime_formatted': self._format_duration(uptime_seconds),
                'performance_summary': summary,
                'system_metrics': system_metrics,
                'cache_statistics': cache_stats,
                'operation_statistics': operation_stats,
                'optimization_recommendations': self.get_optimization_recommendations(),
                'health_status': self._calculate_health_status(summary, system_metrics, cache_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            return {
                'timestamp': time.time(),
                'error': str(e),
                'health_status': 'unknown'
            }
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate optimization recommendations based on current performance.
        
        Returns:
            List of optimization recommendations
        """
        try:
            recommendations = []
            
            # Check if we should run optimization analysis
            if time.time() - self.last_optimization_check < 60:  # Check every minute
                return self.optimization_recommendations
            
            self.last_optimization_check = time.time()
            
            # Get current metrics
            summary = performance_monitor.get_performance_summary(time_window_minutes=15)
            system_metrics = performance_monitor.get_system_metrics()
            cache_stats = image_cache.get_cache_stats()
            
            # Memory optimization recommendations
            if system_metrics.get('memory_mb', 0) > MEMORY_WARNING_THRESHOLD_MB:
                recommendations.append({
                    'type': 'memory',
                    'priority': 'high' if system_metrics['memory_mb'] > MEMORY_CRITICAL_THRESHOLD_MB else 'medium',
                    'title': 'High Memory Usage Detected',
                    'description': f"Memory usage is {system_metrics['memory_mb']:.1f}MB. Consider reducing cache size or restarting the application.",
                    'action': 'reduce_cache_size',
                    'current_value': system_metrics['memory_mb'],
                    'threshold': MEMORY_WARNING_THRESHOLD_MB
                })
            
            # CPU optimization recommendations
            if system_metrics.get('cpu_percent', 0) > CPU_WARNING_THRESHOLD_PERCENT:
                recommendations.append({
                    'type': 'cpu',
                    'priority': 'high' if system_metrics['cpu_percent'] > CPU_CRITICAL_THRESHOLD_PERCENT else 'medium',
                    'title': 'High CPU Usage Detected',
                    'description': f"CPU usage is {system_metrics['cpu_percent']:.1f}%. Consider reducing parallel processing or optimizing operations.",
                    'action': 'reduce_parallelization',
                    'current_value': system_metrics['cpu_percent'],
                    'threshold': CPU_WARNING_THRESHOLD_PERCENT
                })
            
            # Cache optimization recommendations
            cache_hit_rate = cache_stats.get('hit_rate_percent', 0)
            if cache_hit_rate < TARGET_CACHE_HIT_RATE_PERCENT and cache_stats.get('total_requests', 0) > 10:
                recommendations.append({
                    'type': 'cache',
                    'priority': 'medium',
                    'title': 'Low Cache Hit Rate',
                    'description': f"Cache hit rate is {cache_hit_rate:.1f}%. Consider increasing cache size or adjusting cache expiry.",
                    'action': 'increase_cache_size',
                    'current_value': cache_hit_rate,
                    'threshold': TARGET_CACHE_HIT_RATE_PERCENT
                })
            
            # Performance optimization recommendations
            avg_duration = summary.get('avg_duration_seconds', 0)
            if avg_duration > TARGET_API_RESPONSE_TIME_MS / 1000:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'medium',
                    'title': 'Slow Operation Performance',
                    'description': f"Average operation time is {avg_duration:.2f}s. Consider optimizing API calls or enabling more parallelization.",
                    'action': 'optimize_api_calls',
                    'current_value': avg_duration,
                    'threshold': TARGET_API_RESPONSE_TIME_MS / 1000
                })
            
            # Success rate recommendations
            success_rate = summary.get('success_rate_percent', 100)
            if success_rate < 95 and summary.get('total_operations', 0) > 5:
                recommendations.append({
                    'type': 'reliability',
                    'priority': 'high',
                    'title': 'Low Success Rate',
                    'description': f"Operation success rate is {success_rate:.1f}%. Check error logs and consider improving error handling.",
                    'action': 'improve_error_handling',
                    'current_value': success_rate,
                    'threshold': 95
                })
            
            # Cache size recommendations
            cache_size_mb = cache_stats.get('size_mb', 0)
            cache_max_mb = cache_stats.get('max_size_mb', IMAGE_CACHE_MAX_SIZE_MB)
            if cache_size_mb > cache_max_mb * 0.9:
                recommendations.append({
                    'type': 'cache',
                    'priority': 'low',
                    'title': 'Cache Nearly Full',
                    'description': f"Cache is {cache_size_mb:.1f}MB of {cache_max_mb}MB. Consider increasing cache size or reducing cache expiry.",
                    'action': 'manage_cache_size',
                    'current_value': cache_size_mb,
                    'threshold': cache_max_mb * 0.9
                })
            
            self.optimization_recommendations = recommendations
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            return []
    
    def _calculate_health_status(self, summary: Dict, system_metrics: Dict, cache_stats: Dict) -> str:
        """
        Calculate overall system health status.
        
        Args:
            summary: Performance summary
            system_metrics: System metrics
            cache_stats: Cache statistics
            
        Returns:
            Health status string
        """
        try:
            health_score = 100
            
            # Factor in success rate
            success_rate = summary.get('success_rate_percent', 100)
            if success_rate < 95:
                health_score -= (95 - success_rate) * 2
            
            # Factor in memory usage
            memory_mb = system_metrics.get('memory_mb', 0)
            if memory_mb > MEMORY_WARNING_THRESHOLD_MB:
                health_score -= min(30, (memory_mb - MEMORY_WARNING_THRESHOLD_MB) / 10)
            
            # Factor in CPU usage
            cpu_percent = system_metrics.get('cpu_percent', 0)
            if cpu_percent > CPU_WARNING_THRESHOLD_PERCENT:
                health_score -= min(20, (cpu_percent - CPU_WARNING_THRESHOLD_PERCENT) / 2)
            
            # Factor in average response time
            avg_duration = summary.get('avg_duration_seconds', 0)
            target_duration = TARGET_API_RESPONSE_TIME_MS / 1000
            if avg_duration > target_duration:
                health_score -= min(15, (avg_duration - target_duration) * 5)
            
            # Determine health status
            if health_score >= 90:
                return 'excellent'
            elif health_score >= 75:
                return 'good'
            elif health_score >= 60:
                return 'fair'
            elif health_score >= 40:
                return 'poor'
            else:
                return 'critical'
                
        except Exception as e:
            logger.error(f"Health status calculation failed: {e}")
            return 'unknown'
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def export_metrics(self, format: str = 'json', time_window_minutes: int = 60) -> str:
        """
        Export performance metrics in specified format.
        
        Args:
            format: Export format ('json', 'csv')
            time_window_minutes: Time window for metrics
            
        Returns:
            Formatted metrics string
        """
        try:
            metrics = self.get_real_time_metrics()
            
            if format.lower() == 'json':
                return json.dumps(metrics, indent=2, default=str)
            elif format.lower() == 'csv':
                # Simple CSV export for key metrics
                lines = [
                    "metric,value,timestamp",
                    f"uptime_seconds,{metrics.get('uptime_seconds', 0)},{metrics.get('timestamp', 0)}",
                    f"memory_mb,{metrics.get('system_metrics', {}).get('memory_mb', 0)},{metrics.get('timestamp', 0)}",
                    f"cpu_percent,{metrics.get('system_metrics', {}).get('cpu_percent', 0)},{metrics.get('timestamp', 0)}",
                    f"cache_hit_rate,{metrics.get('cache_statistics', {}).get('hit_rate_percent', 0)},{metrics.get('timestamp', 0)}",
                    f"success_rate,{metrics.get('performance_summary', {}).get('success_rate_percent', 0)},{metrics.get('timestamp', 0)}"
                ]
                return '\n'.join(lines)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return f"Export failed: {e}"
    
    def apply_optimization_recommendation(self, recommendation_id: str) -> Dict[str, Any]:
        """
        Apply a specific optimization recommendation.
        
        Args:
            recommendation_id: ID of the recommendation to apply
            
        Returns:
            Result of applying the optimization
        """
        try:
            # This would implement automatic optimization based on recommendations
            # For now, return a placeholder response
            return {
                'success': True,
                'message': f"Optimization {recommendation_id} would be applied",
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to apply optimization: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance trends over time.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Performance trends data
        """
        try:
            # This would analyze historical performance data
            # For now, return current snapshot
            current_metrics = self.get_real_time_metrics()
            
            return {
                'time_period_hours': hours,
                'current_snapshot': current_metrics,
                'trends': {
                    'memory_usage': 'stable',
                    'cpu_usage': 'stable',
                    'cache_performance': 'improving',
                    'success_rate': 'stable'
                },
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return {
                'error': str(e),
                'timestamp': time.time()
            }


# Global dashboard instance
performance_dashboard = PerformanceDashboard()
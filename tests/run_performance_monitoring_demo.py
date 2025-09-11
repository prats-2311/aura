#!/usr/bin/env python3
"""
Performance Monitoring System Demo

This script demonstrates the performance monitoring, caching, and optimization
features implemented for the explain selected text feature.
"""

import time
import random
from typing import Dict, Any

# Import the performance monitoring components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.performance_monitor import get_performance_monitor
from modules.performance_dashboard import create_performance_dashboard
from modules.accessibility_cache_optimizer import get_cache_optimizer


def simulate_text_capture_operations(monitor, optimizer, num_operations: int = 20):
    """Simulate text capture operations with varying performance."""
    print(f"\n🔍 Simulating {num_operations} text capture operations...")
    
    for i in range(num_operations):
        # Simulate different performance characteristics
        if i < 5:
            # First 5 operations are slow (cold start)
            duration = random.uniform(0.8, 1.2)  # 800-1200ms
            success_rate = 0.8  # 80% success rate initially
        elif i < 15:
            # Middle operations improve with caching
            duration = random.uniform(0.2, 0.5)  # 200-500ms
            success_rate = 0.95  # 95% success rate with cache
        else:
            # Later operations are optimized
            duration = random.uniform(0.1, 0.3)  # 100-300ms
            success_rate = 0.98  # 98% success rate
        
        # Simulate operation
        try:
            with monitor.track_operation('text_capture', {
                'method': 'accessibility_api' if random.random() > 0.3 else 'clipboard_fallback',
                'app_name': random.choice(['Safari', 'Chrome', 'TextEdit', 'VS Code'])
            }) as metric:
                time.sleep(duration)
                
                # Simulate success/failure
                if random.random() < success_rate:
                    text_length = random.randint(10, 500)
                    metric.metadata['text_length'] = text_length
                    metric.metadata['success'] = True
                    
                    # Simulate caching
                    if i >= 5:  # Start caching after 5 operations
                        cache_key = f"text_capture_{i % 3}"  # Simulate cache hits
                        optimizer.cache_element(cache_key, 'TestApp', {
                            'text': f'Sample text {i}',
                            'length': text_length
                        })
                else:
                    raise Exception(f"Simulated text capture failure {i}")
        except Exception as e:
            # Failures are tracked by the performance monitor
            pass
        
        if (i + 1) % 5 == 0:
            print(f"  Completed {i + 1}/{num_operations} operations")


def simulate_explanation_generation(monitor, num_operations: int = 15):
    """Simulate explanation generation operations."""
    print(f"\n💭 Simulating {num_operations} explanation generation operations...")
    
    for i in range(num_operations):
        # Simulate different text types and complexities
        text_types = ['code', 'technical', 'general', 'academic']
        text_type = random.choice(text_types)
        
        # Different types have different performance characteristics
        if text_type == 'code':
            duration = random.uniform(2.0, 4.0)  # Code explanations take longer
        elif text_type == 'technical':
            duration = random.uniform(1.5, 3.0)  # Technical content is complex
        else:
            duration = random.uniform(0.8, 2.0)  # General text is faster
        
        with monitor.track_operation('explanation_generation', {
            'text_type': text_type,
            'text_length': random.randint(50, 1000)
        }) as metric:
            time.sleep(duration)
            
            # Simulate caching for similar explanations
            if i >= 3 and random.random() < 0.3:  # 30% cache hit rate after warmup
                metric.metadata['cache_hit'] = True
                duration *= 0.1  # Cache hits are much faster
            else:
                metric.metadata['cache_hit'] = False
            
            explanation_length = random.randint(100, 800)
            metric.metadata['explanation_length'] = explanation_length
        
        if (i + 1) % 5 == 0:
            print(f"  Completed {i + 1}/{num_operations} operations")


def demonstrate_performance_alerts(monitor):
    """Demonstrate the performance alerting system."""
    print(f"\n⚠️  Demonstrating performance alerts...")
    
    alerts_triggered = []
    
    def alert_callback(alert):
        alerts_triggered.append(alert)
        severity_emoji = "🚨" if alert.severity == 'critical' else "⚠️"
        print(f"  {severity_emoji} ALERT: {alert.alert_type} - {alert.operation} took {alert.actual_ms:.0f}ms")
    
    monitor.add_alert_callback(alert_callback)
    
    # Trigger warning alert
    with monitor.track_operation('slow_text_capture'):
        time.sleep(1.6)  # Exceed warning threshold (1500ms)
    
    # Trigger critical alert
    with monitor.track_operation('very_slow_explanation'):
        time.sleep(2.1)  # Exceed critical threshold (2000ms)
    
    print(f"  Triggered {len(alerts_triggered)} performance alerts")


def display_performance_summary(monitor, dashboard):
    """Display comprehensive performance summary."""
    print(f"\n📊 Performance Summary")
    print("=" * 50)
    
    # Overall summary
    summary = monitor.get_performance_summary()
    print(f"Total Operations: {summary['total_operations']}")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    print(f"Average Duration: {summary['avg_duration_ms']:.1f}ms")
    print(f"95th Percentile: {summary['p95_duration_ms']:.1f}ms")
    
    # Operation-specific stats
    print(f"\n📈 Operation Statistics:")
    text_stats = monitor.get_operation_stats('text_capture')
    if text_stats:
        print(f"  Text Capture: {text_stats['count']} ops, "
              f"{text_stats['success_rate']:.1%} success, "
              f"{text_stats['avg_duration_ms']:.1f}ms avg")
    
    explanation_stats = monitor.get_operation_stats('explanation_generation')
    if explanation_stats:
        print(f"  Explanation: {explanation_stats['count']} ops, "
              f"{explanation_stats['success_rate']:.1%} success, "
              f"{explanation_stats['avg_duration_ms']:.1f}ms avg")
    
    # Cache performance
    print(f"\n💾 Cache Performance:")
    cache_stats = monitor.get_cache_stats()
    for cache_name, stats in cache_stats.items():
        print(f"  {cache_name.title()}: {stats['hit_rate']:.1%} hit rate, "
              f"{stats['size']}/{stats['max_size']} entries")
    
    # Health score
    if dashboard:
        dashboard_data = dashboard.get_dashboard_data()
        health_score = dashboard_data.get('overall_health_score', 0)
        health_emoji = "🟢" if health_score > 80 else "🟡" if health_score > 60 else "🔴"
        print(f"\n{health_emoji} System Health Score: {health_score:.1f}/100")


def display_optimization_recommendations(monitor, optimizer, dashboard):
    """Display optimization recommendations."""
    print(f"\n🔧 Optimization Recommendations")
    print("=" * 50)
    
    # Text capture recommendations
    text_recommendations = monitor.optimize_text_capture_performance()
    if text_recommendations['recommendations']:
        print("Text Capture Optimizations:")
        for rec in text_recommendations['recommendations']:
            print(f"  • {rec}")
    
    # Explanation recommendations
    explanation_recommendations = monitor.optimize_explanation_performance()
    if explanation_recommendations['recommendations']:
        print("\nExplanation Generation Optimizations:")
        for rec in explanation_recommendations['recommendations']:
            print(f"  • {rec}")
    
    # Cache recommendations
    cache_recommendations = optimizer.get_optimization_recommendations()
    if cache_recommendations:
        print("\nCache Optimizations:")
        for rec in cache_recommendations:
            print(f"  • {rec['title']}: {rec['description']}")
    
    # Dashboard recommendations
    if dashboard:
        dashboard_data = dashboard.get_dashboard_data()
        dashboard_recommendations = dashboard_data.get('optimization_recommendations', [])
        if dashboard_recommendations:
            print("\nSystem-wide Optimizations:")
            for rec in dashboard_recommendations:
                priority_emoji = "🔴" if rec.priority == 'high' else "🟡" if rec.priority == 'medium' else "🟢"
                print(f"  {priority_emoji} {rec.title}: {rec.description}")


def main():
    """Run the performance monitoring demonstration."""
    print("🚀 AURA Performance Monitoring System Demo")
    print("=" * 60)
    
    # Initialize components
    print("\n🔧 Initializing performance monitoring components...")
    monitor = get_performance_monitor()
    dashboard = create_performance_dashboard()
    optimizer = get_cache_optimizer()
    
    print(f"✅ Performance Monitor: {'Enabled' if monitor.enabled else 'Disabled'}")
    print(f"✅ Performance Dashboard: {'Available' if dashboard else 'Unavailable'}")
    print(f"✅ Cache Optimizer: {'Enabled' if optimizer.enabled else 'Disabled'}")
    
    # Run simulations
    simulate_text_capture_operations(monitor, optimizer, 20)
    simulate_explanation_generation(monitor, 15)
    demonstrate_performance_alerts(monitor)
    
    # Allow dashboard to update
    if dashboard:
        print("\n⏳ Updating dashboard data...")
        time.sleep(2)  # Allow background updates
        dashboard._update_dashboard_data()
    
    # Display results
    display_performance_summary(monitor, dashboard)
    display_optimization_recommendations(monitor, optimizer, dashboard)
    
    print(f"\n🎉 Demo completed successfully!")
    print(f"📝 Check the performance logs for detailed metrics and analysis.")
    
    # Cleanup
    if dashboard:
        dashboard.shutdown()
    optimizer.shutdown()
    monitor.shutdown()


if __name__ == '__main__':
    main()
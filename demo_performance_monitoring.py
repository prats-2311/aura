#!/usr/bin/env python3
"""
Demo script for AURA Fast Path Performance Monitoring System

This script demonstrates the performance monitoring and reporting capabilities
implemented for the click debugging enhancement.
"""

import time
import random
from modules.fast_path_performance_monitor import (
    FastPathPerformanceMonitor,
    FastPathMetric
)
from modules.performance_reporting_system import PerformanceReportingSystem


def simulate_fast_path_executions(monitor, num_executions=50):
    """Simulate various fast path execution scenarios."""
    print(f"Simulating {num_executions} fast path executions...")
    
    apps = ["Chrome", "Safari", "Mail", "Finder", "TextEdit"]
    commands = [
        "click on button",
        "click on link",
        "click on menu item",
        "click on search box",
        "click on submit"
    ]
    
    for i in range(num_executions):
        # Simulate different performance characteristics
        app = random.choice(apps)
        command = random.choice(commands)
        
        # Simulate performance variation by app
        if app == "Chrome":
            # Chrome generally performs well
            success_rate = 0.85
            base_time = 0.5
        elif app == "Safari":
            # Safari has moderate performance
            success_rate = 0.75
            base_time = 0.8
        elif app == "Mail":
            # Mail has some issues
            success_rate = 0.60
            base_time = 1.2
        else:
            # Other apps have variable performance
            success_rate = 0.70
            base_time = 1.0
        
        # Add some randomness
        success = random.random() < success_rate
        execution_time = base_time + random.uniform(-0.3, 0.5)
        element_detection_time = execution_time * 0.7
        matching_time = execution_time * 0.2
        
        # Create metric
        metric = FastPathMetric(
            command=f"{command} in {app}",
            app_name=app,
            execution_time=max(0.1, execution_time),
            element_detection_time=max(0.05, element_detection_time),
            matching_time=max(0.01, matching_time),
            success=success,
            element_found=success or random.random() < 0.3,
            fallback_triggered=not success,
            error_message="Element not found" if not success else "",
            search_strategy="enhanced_role_detection" if success else "button_only",
            element_count=random.randint(5, 50),
            similarity_score=random.uniform(0.6, 1.0) if success else random.uniform(0.1, 0.5)
        )
        
        monitor.record_fast_path_execution(metric)
        
        # Small delay to simulate real usage
        time.sleep(0.01)
        
        # Print progress
        if (i + 1) % 10 == 0:
            print(f"  Completed {i + 1}/{num_executions} executions")


def demonstrate_performance_monitoring():
    """Demonstrate the performance monitoring system."""
    print("=" * 60)
    print("AURA Fast Path Performance Monitoring Demo")
    print("=" * 60)
    
    # Initialize monitoring system
    print("\n1. Initializing performance monitoring system...")
    monitor = FastPathPerformanceMonitor()
    reporting_system = PerformanceReportingSystem(monitor=monitor)
    
    # Simulate initial poor performance
    print("\n2. Simulating initial poor performance period...")
    for i in range(15):
        metric = FastPathMetric(
            command=f"test command {i}",
            app_name="ProblematicApp",
            execution_time=2.5 + random.uniform(0, 1),
            success=random.random() < 0.3,  # 30% success rate
            fallback_triggered=True
        )
        monitor.record_fast_path_execution(metric)
    
    # Generate initial feedback
    feedback = reporting_system.generate_real_time_feedback()
    print(f"\nInitial Performance Feedback:")
    print(f"  Type: {feedback.message_type}")
    print(f"  Title: {feedback.title}")
    print(f"  Message: {feedback.message}")
    if feedback.suggested_actions:
        print(f"  Suggested Actions:")
        for action in feedback.suggested_actions[:3]:
            print(f"    - {action}")
    
    # Simulate mixed performance
    print("\n3. Simulating mixed performance scenarios...")
    simulate_fast_path_executions(monitor, num_executions=30)
    
    # Show current statistics
    print("\n4. Current Performance Statistics:")
    stats = monitor.get_performance_statistics(time_window_minutes=60)
    print(f"  Total Executions: {stats['total_executions']}")
    print(f"  Success Rate: {stats['success_rate_percent']:.1f}%")
    print(f"  Average Execution Time: {stats['avg_execution_time_seconds']:.2f}s")
    print(f"  Fallback Rate: {stats['fallback_rate_percent']:.1f}%")
    print(f"  Element Found Rate: {stats['element_found_rate_percent']:.1f}%")
    
    # Show application-specific performance
    print("\n5. Application-Specific Performance:")
    for app_name, app_stats in stats['app_performance'].items():
        print(f"  {app_name}:")
        print(f"    Success Rate: {app_stats['success_rate_percent']:.1f}%")
        print(f"    Total Attempts: {app_stats['total_attempts']}")
        print(f"    Avg Execution Time: {app_stats['avg_execution_time_seconds']:.2f}s")
    
    # Show recent alerts
    if stats['recent_alerts']:
        print("\n6. Recent Performance Alerts:")
        for alert in stats['recent_alerts'][-3:]:  # Show last 3 alerts
            print(f"  [{alert['severity'].upper()}] {alert['message']}")
            print(f"    Recommendation: {alert['recommendation']}")
    
    # Simulate performance improvement
    print("\n7. Simulating performance improvements...")
    for i in range(20):
        metric = FastPathMetric(
            command=f"improved command {i}",
            app_name=random.choice(["Chrome", "Safari", "TextEdit"]),
            execution_time=0.4 + random.uniform(0, 0.3),
            success=random.random() < 0.9,  # 90% success rate
            fallback_triggered=False
        )
        monitor.record_fast_path_execution(metric)
    
    # Generate comprehensive report
    print("\n8. Generating Comprehensive Performance Report...")
    report = reporting_system.generate_performance_summary_report(time_period_hours=1.0)
    
    print(f"\nPerformance Report Summary:")
    print(f"  Report ID: {report.report_id}")
    print(f"  Health Score: {report.health_score:.1f}/100")
    print(f"  Overall Trend: {report.trends['overall_trend']}")
    print(f"  Total Executions: {report.summary['total_executions']}")
    print(f"  Success Rate: {report.summary['success_rate_percent']:.1f}%")
    
    print(f"\nTop Recommendations:")
    for i, recommendation in enumerate(report.recommendations[:3], 1):
        print(f"  {i}. {recommendation}")
    
    # Show improvement factors
    if report.improvement_factors:
        print(f"\nImprovement Factors Detected:")
        for factor in report.improvement_factors[:3]:
            print(f"  - {factor}")
    
    # Generate final feedback
    final_feedback = reporting_system.generate_real_time_feedback()
    print(f"\nFinal Performance Feedback:")
    print(f"  {final_feedback.title}: {final_feedback.message}")
    
    # Demonstrate export functionality
    print("\n9. Demonstrating Export Functionality...")
    
    # Export as JSON
    json_export = reporting_system.export_performance_report(report, format='json')
    print(f"  JSON export size: {len(json_export)} characters")
    
    # Export as text
    text_export = reporting_system.export_performance_report(report, format='text')
    print(f"  Text export preview:")
    print("  " + "\n  ".join(text_export.split('\n')[:5]) + "...")
    
    print("\n" + "=" * 60)
    print("Performance Monitoring Demo Complete!")
    print("=" * 60)
    
    # Show diagnostic suggestion
    if monitor.should_suggest_diagnostics():
        print("\n⚠️  Performance is below optimal - consider running diagnostics")
    else:
        print("\n✅ Performance is within acceptable range")


if __name__ == "__main__":
    demonstrate_performance_monitoring()
#!/usr/bin/env python3
"""
Demo script for AURA Diagnostic Tools

This script demonstrates the comprehensive diagnostic tools functionality
including health checking, performance benchmarking, and intelligent reporting.
"""

import sys
import json
from datetime import datetime

try:
    from modules.diagnostic_tools import (
        AccessibilityHealthChecker,
        AdvancedDiagnosticReporter,
        DiagnosticIssue,
        PerformanceBenchmark
    )
    DIAGNOSTIC_TOOLS_AVAILABLE = True
except ImportError as e:
    DIAGNOSTIC_TOOLS_AVAILABLE = False
    print(f"Diagnostic tools not available: {e}")
    sys.exit(1)


def demo_basic_health_check():
    """Demonstrate basic health checking functionality."""
    print("=" * 60)
    print("DEMO: Basic Accessibility Health Check")
    print("=" * 60)
    
    # Initialize health checker
    config = {
        'test_applications': ['Finder', 'Safari', 'Terminal'],
        'known_good_elements': {
            'Finder': ['New Folder', 'View', 'Go'],
            'Safari': ['Address and Search', 'Bookmarks', 'History'],
            'Terminal': ['Shell', 'Edit', 'View']
        },
        'debug_level': 'DETAILED'
    }
    
    health_checker = AccessibilityHealthChecker(config)
    
    try:
        # Run comprehensive health check
        print("Running comprehensive health check...")
        report = health_checker.run_comprehensive_health_check()
        
        # Display results
        print(f"\nHealth Score: {report.overall_health_score:.1f}/100")
        print(f"Generation Time: {report.generation_time_ms:.1f}ms")
        print(f"Issues Found: {len(report.detected_issues)}")
        
        # Show critical issues
        critical_issues = [i for i in report.detected_issues if i.severity == 'CRITICAL']
        if critical_issues:
            print(f"\nCRITICAL ISSUES ({len(critical_issues)}):")
            for issue in critical_issues:
                print(f"  • {issue.title}")
                print(f"    Impact: {issue.impact}")
        
        # Show top recommendations
        print(f"\nTOP RECOMMENDATIONS:")
        for i, rec in enumerate(report.recommendations[:3], 1):
            if rec.strip():
                print(f"  {i}. {rec}")
        
    except Exception as e:
        print(f"Health check failed: {e}")


def demo_advanced_reporting():
    """Demonstrate advanced diagnostic reporting."""
    print("\n" + "=" * 60)
    print("DEMO: Advanced Diagnostic Reporting")
    print("=" * 60)
    
    # Initialize advanced reporter
    config = {
        'test_applications': ['Finder', 'Safari'],
        'known_good_elements': {
            'Finder': ['New Folder', 'View'],
            'Safari': ['Address and Search', 'Bookmarks']
        },
        'debug_level': 'VERBOSE'
    }
    
    advanced_reporter = AdvancedDiagnosticReporter(config)
    
    try:
        # Generate comprehensive report
        print("Generating comprehensive diagnostic report...")
        report = advanced_reporter.generate_comprehensive_report(
            include_benchmarks=True,
            include_detailed_analysis=True
        )
        
        # Display enhanced results
        print(f"\nEnhanced Health Score: {report.overall_health_score:.1f}/100")
        print(f"System Info: {report.system_info.get('platform', 'Unknown')} {report.system_info.get('version', '')}")
        
        # Show issue breakdown
        if report.detected_issues:
            issue_counts = {}
            for issue in report.detected_issues:
                issue_counts[issue.severity] = issue_counts.get(issue.severity, 0) + 1
            
            print(f"\nISSUE BREAKDOWN:")
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                count = issue_counts.get(severity, 0)
                if count > 0:
                    print(f"  {severity}: {count}")
        
        # Show performance benchmarks
        if report.benchmark_results:
            print(f"\nPERFORMANCE BENCHMARKS:")
            for benchmark in report.benchmark_results:
                print(f"  • {benchmark.test_name}: {benchmark.success_rate:.1%} success rate")
                if benchmark.fast_path_time and benchmark.vision_fallback_time:
                    speedup = benchmark.vision_fallback_time / benchmark.fast_path_time
                    print(f"    Fast path {speedup:.1f}x faster than vision fallback")
        
        # Export report in different formats
        print(f"\nEXPORTING REPORTS:")
        
        # Text export
        text_report = advanced_reporter.export_detailed_report(report, 'TEXT')
        with open('diagnostic_report.txt', 'w') as f:
            f.write(text_report)
        print("  • Text report saved to: diagnostic_report.txt")
        
        # JSON export
        json_report = advanced_reporter.export_detailed_report(report, 'JSON')
        with open('diagnostic_report.json', 'w') as f:
            f.write(json_report)
        print("  • JSON report saved to: diagnostic_report.json")
        
        # HTML export
        html_report = advanced_reporter.export_detailed_report(report, 'HTML')
        with open('diagnostic_report.html', 'w') as f:
            f.write(html_report)
        print("  • HTML report saved to: diagnostic_report.html")
        
    except Exception as e:
        print(f"Advanced reporting failed: {e}")


def demo_issue_analysis():
    """Demonstrate issue analysis and prioritization."""
    print("\n" + "=" * 60)
    print("DEMO: Issue Analysis and Prioritization")
    print("=" * 60)
    
    # Create sample issues
    sample_issues = [
        DiagnosticIssue(
            severity='CRITICAL',
            category='PERMISSIONS',
            title='No Accessibility Permissions',
            description='AURA lacks accessibility permissions for fast path execution',
            impact='All commands fall back to slower vision processing',
            remediation_steps=[
                'Open System Preferences > Security & Privacy > Privacy > Accessibility',
                'Add Terminal to the accessibility permissions list',
                'Restart AURA after granting permissions'
            ],
            metadata={'permission_level': 'NONE'},
            timestamp=datetime.now()
        ),
        DiagnosticIssue(
            severity='HIGH',
            category='PERFORMANCE',
            title='Poor Element Detection Rate',
            description='Element detection success rate below 70%',
            impact='Frequent command failures and slower execution',
            remediation_steps=[
                'Update applications to latest versions',
                'Check application accessibility settings',
                'Clear application caches'
            ],
            metadata={'success_rate': 0.45},
            timestamp=datetime.now()
        ),
        DiagnosticIssue(
            severity='MEDIUM',
            category='SYSTEM',
            title='High Memory Usage',
            description='System memory usage above 85%',
            impact='Potential performance degradation',
            remediation_steps=[
                'Close unnecessary applications',
                'Restart system if usage remains high'
            ],
            metadata={'memory_percent': 87.5},
            timestamp=datetime.now()
        )
    ]
    
    # Initialize reporter for analysis
    from modules.diagnostic_tools import DiagnosticReportGenerator
    report_generator = DiagnosticReportGenerator()
    
    # Prioritize issues
    print("Prioritizing issues by impact...")
    prioritized_issues = report_generator.prioritize_issues(sample_issues)
    
    print(f"\nPRIORITIZED ISSUES:")
    for i, issue in enumerate(prioritized_issues, 1):
        print(f"{i}. [{issue.severity}] {issue.title}")
        print(f"   Category: {issue.category}")
        print(f"   Impact: {issue.impact}")
        print(f"   Top Remediation: {issue.remediation_steps[0] if issue.remediation_steps else 'None'}")
        print()
    
    # Generate issue summary
    issue_summary = report_generator.generate_issue_summary(sample_issues)
    print(f"ISSUE SUMMARY:")
    print(f"  Total Issues: {issue_summary['total_issues']}")
    print(f"  By Severity: {issue_summary['by_severity']}")
    print(f"  By Category: {issue_summary['by_category']}")
    print(f"  Overall Impact: {issue_summary['impact_assessment']['overall']}")


def main():
    """Run all diagnostic tool demos."""
    print("AURA Diagnostic Tools Demo")
    print("=" * 60)
    print("This demo showcases the comprehensive diagnostic capabilities")
    print("including health checking, performance analysis, and reporting.")
    print()
    
    if not DIAGNOSTIC_TOOLS_AVAILABLE:
        print("ERROR: Diagnostic tools are not available.")
        print("Please ensure all required modules are installed.")
        return
    
    try:
        # Run demos
        demo_basic_health_check()
        demo_advanced_reporting()
        demo_issue_analysis()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("Check the generated report files:")
        print("  • diagnostic_report.txt")
        print("  • diagnostic_report.json") 
        print("  • diagnostic_report.html")
        print()
        print("These tools can help identify and resolve accessibility issues")
        print("that prevent AURA's fast path from working optimally.")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
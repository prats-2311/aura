"""
Unit tests for diagnostic tools module.

Tests comprehensive accessibility health checking, performance benchmarking,
and diagnostic reporting functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime
from typing import Dict, Any, List

# Import the module under test
try:
    from modules.diagnostic_tools import (
        AccessibilityHealthChecker,
        DiagnosticReportGenerator,
        DiagnosticIssue,
        PerformanceBenchmark,
        DiagnosticReport
    )
    from modules.permission_validator import PermissionStatus
    DIAGNOSTIC_TOOLS_AVAILABLE = True
except ImportError as e:
    DIAGNOSTIC_TOOLS_AVAILABLE = False
    print(f"Diagnostic tools not available for testing: {e}")


@unittest.skipUnless(DIAGNOSTIC_TOOLS_AVAILABLE, "Diagnostic tools not available")
class TestDiagnosticIssue(unittest.TestCase):
    """Test DiagnosticIssue data class."""
    
    def test_diagnostic_issue_creation(self):
        """Test creating a diagnostic issue."""
        issue = DiagnosticIssue(
            severity='HIGH',
            category='PERMISSIONS',
            title='Test Issue',
            description='Test description',
            impact='Test impact',
            remediation_steps=['Step 1', 'Step 2'],
            metadata={'key': 'value'},
            timestamp=datetime.now()
        )
        
        self.assertEqual(issue.severity, 'HIGH')
        self.assertEqual(issue.category, 'PERMISSIONS')
        self.assertEqual(issue.title, 'Test Issue')
        self.assertEqual(len(issue.remediation_steps), 2)
    
    def test_diagnostic_issue_to_dict(self):
        """Test converting diagnostic issue to dictionary."""
        timestamp = datetime.now()
        issue = DiagnosticIssue(
            severity='CRITICAL',
            category='SYSTEM',
            title='Critical Issue',
            description='Critical description',
            impact='High impact',
            remediation_steps=['Fix it'],
            metadata={'error': 'test'},
            timestamp=timestamp
        )
        
        issue_dict = issue.to_dict()
        
        self.assertEqual(issue_dict['severity'], 'CRITICAL')
        self.assertEqual(issue_dict['category'], 'SYSTEM')
        self.assertEqual(issue_dict['timestamp'], timestamp.isoformat())
        self.assertIn('metadata', issue_dict)


@unittest.skipUnless(DIAGNOSTIC_TOOLS_AVAILABLE, "Diagnostic tools not available")
class TestPerformanceBenchmark(unittest.TestCase):
    """Test PerformanceBenchmark data class."""
    
    def test_performance_benchmark_creation(self):
        """Test creating a performance benchmark."""
        benchmark = PerformanceBenchmark(
            test_name='test_app',
            fast_path_time=0.1,
            vision_fallback_time=0.5,
            performance_ratio=0.2,
            success_rate=0.8,
            error_message=None,
            metadata={'app': 'TestApp'},
            timestamp=datetime.now()
        )
        
        self.assertEqual(benchmark.test_name, 'test_app')
        self.assertEqual(benchmark.fast_path_time, 0.1)
        self.assertEqual(benchmark.vision_fallback_time, 0.5)
        self.assertEqual(benchmark.performance_ratio, 0.2)
        self.assertEqual(benchmark.success_rate, 0.8)
    
    def test_performance_benchmark_to_dict(self):
        """Test converting performance benchmark to dictionary."""
        timestamp = datetime.now()
        benchmark = PerformanceBenchmark(
            test_name='benchmark_test',
            fast_path_time=0.05,
            vision_fallback_time=0.25,
            performance_ratio=0.2,
            success_rate=0.9,
            error_message=None,
            metadata={'elements': 5},
            timestamp=timestamp
        )
        
        benchmark_dict = benchmark.to_dict()
        
        self.assertEqual(benchmark_dict['test_name'], 'benchmark_test')
        self.assertEqual(benchmark_dict['fast_path_time'], 0.05)
        self.assertEqual(benchmark_dict['timestamp'], timestamp.isoformat())


@unittest.skipUnless(DIAGNOSTIC_TOOLS_AVAILABLE, "Diagnostic tools not available")
class TestAccessibilityHealthChecker(unittest.TestCase):
    """Test AccessibilityHealthChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'test_applications': ['TestApp1', 'TestApp2'],
            'known_good_elements': {
                'TestApp1': ['Button1', 'Button2'],
                'TestApp2': ['Menu1', 'Menu2']
            }
        }
        
        # Mock the dependencies
        with patch('modules.diagnostic_tools.MODULES_AVAILABLE', True):
            with patch('modules.diagnostic_tools.PermissionValidator'):
                with patch('modules.diagnostic_tools.AccessibilityDebugger'):
                    with patch('modules.diagnostic_tools.PerformanceMonitor'):
                        self.health_checker = AccessibilityHealthChecker(self.config)
    
    def test_health_checker_initialization(self):
        """Test health checker initialization."""
        self.assertIsNotNone(self.health_checker)
        self.assertEqual(self.health_checker.test_applications, ['TestApp1', 'TestApp2'])
        self.assertIn('TestApp1', self.health_checker.known_good_elements)
    
    @patch('modules.diagnostic_tools.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.diagnostic_tools.NSWorkspace')
    def test_get_available_test_applications(self, mock_workspace):
        """Test getting available test applications."""
        # Mock running applications
        mock_app1 = Mock()
        mock_app1.localizedName.return_value = 'TestApp1'
        mock_app2 = Mock()
        mock_app2.localizedName.return_value = 'TestApp2'
        mock_app3 = Mock()
        mock_app3.localizedName.return_value = 'OtherApp'
        
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = [mock_app1, mock_app2, mock_app3]
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        available_apps = self.health_checker._get_available_test_applications()
        
        self.assertIn('TestApp1', available_apps)
        self.assertIn('TestApp2', available_apps)
        self.assertNotIn('OtherApp', available_apps)
    
    def test_gather_system_information(self):
        """Test gathering system information."""
        with patch('platform.system', return_value='Darwin'):
            with patch('platform.version', return_value='Darwin Kernel Version 21.0.0'):
                with patch('platform.python_version', return_value='3.9.0'):
                    system_info = self.health_checker._gather_system_information()
        
        self.assertIn('platform', system_info)
        self.assertIn('version', system_info)
        self.assertIn('python_version', system_info)
        self.assertIn('timestamp', system_info)
    
    @patch('modules.diagnostic_tools.PSUTIL_AVAILABLE', True)
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    def test_gather_system_information_with_psutil(self, mock_cpu_count, mock_memory):
        """Test gathering system information with psutil available."""
        mock_memory.return_value = Mock(
            total=8589934592,  # 8GB
            available=4294967296,  # 4GB
            percent=50.0
        )
        mock_cpu_count.return_value = 8
        
        with patch('psutil.disk_usage') as mock_disk:
            mock_disk.return_value = Mock(
                total=1000000000000,  # 1TB
                free=500000000000,    # 500GB
                percent=50.0
            )
            
            system_info = self.health_checker._gather_system_information()
        
        self.assertIn('cpu_count', system_info)
        self.assertIn('memory_total_gb', system_info)
        self.assertIn('memory_percent', system_info)
        self.assertEqual(system_info['cpu_count'], 8)
        self.assertEqual(system_info['memory_percent'], 50.0)
    
    def test_check_accessibility_permissions(self):
        """Test checking accessibility permissions."""
        # Mock permission validator
        mock_permission_status = Mock()
        mock_permission_status.has_permissions = True
        mock_permission_status.permission_level = 'FULL'
        
        self.health_checker.permission_validator = Mock()
        self.health_checker.permission_validator.check_accessibility_permissions.return_value = mock_permission_status
        
        result = self.health_checker._check_accessibility_permissions()
        
        self.assertIsNotNone(result)
        self.assertTrue(result.has_permissions)
        self.assertEqual(result.permission_level, 'FULL')
    
    @patch('modules.diagnostic_tools.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True)
    @patch('modules.diagnostic_tools.AXIsProcessTrusted')
    def test_check_accessibility_api_health(self, mock_ax_trusted):
        """Test checking accessibility API health."""
        mock_ax_trusted.return_value = True
        
        with patch('modules.diagnostic_tools.NSWorkspace') as mock_workspace:
            mock_workspace_instance = Mock()
            mock_workspace_instance.runningApplications.return_value = []
            mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
            
            health_info = self.health_checker._check_accessibility_api_health()
        
        self.assertTrue(health_info['api_available'])
        self.assertTrue(health_info['process_trusted'])
        self.assertEqual(health_info['running_applications_count'], 0)
    
    def test_analyze_system_issues_critical_permissions(self):
        """Test analyzing system issues with critical permission problems."""
        system_info = {'platform': 'Darwin'}
        
        # Mock permission status with no permissions
        permission_status = Mock()
        permission_status.has_permissions = False
        permission_status.permission_level = 'NONE'
        permission_status.recommendations = ['Grant permissions']
        permission_status.to_dict.return_value = {'has_permissions': False}
        
        accessibility_health = {'api_available': True, 'system_wide_access': True}
        benchmark_results = []
        
        issues = self.health_checker._analyze_system_issues(
            system_info, permission_status, accessibility_health, benchmark_results
        )
        
        # Should find critical permission issue
        critical_issues = [i for i in issues if i.severity == 'CRITICAL']
        self.assertTrue(len(critical_issues) > 0)
        
        permission_issues = [i for i in issues if i.category == 'PERMISSIONS']
        self.assertTrue(len(permission_issues) > 0)
    
    def test_analyze_system_issues_performance_problems(self):
        """Test analyzing system issues with performance problems."""
        system_info = {'platform': 'Darwin', 'memory_percent': 95.0}
        permission_status = Mock()
        permission_status.has_permissions = True
        permission_status.permission_level = 'FULL'
        
        accessibility_health = {'api_available': True, 'system_wide_access': True}
        
        # Mock failed benchmarks
        failed_benchmark = Mock()
        failed_benchmark.success_rate = 0.3
        failed_benchmark.to_dict.return_value = {'success_rate': 0.3}
        benchmark_results = [failed_benchmark]
        
        issues = self.health_checker._analyze_system_issues(
            system_info, permission_status, accessibility_health, benchmark_results
        )
        
        # Should find performance and memory issues
        performance_issues = [i for i in issues if i.category == 'PERFORMANCE']
        memory_issues = [i for i in issues if 'Memory' in i.title]
        
        self.assertTrue(len(performance_issues) > 0)
        self.assertTrue(len(memory_issues) > 0)
    
    def test_calculate_health_score_perfect_system(self):
        """Test calculating health score for a perfect system."""
        # Mock perfect permission status
        permission_status = Mock()
        permission_status.has_permissions = True
        permission_status.permission_level = 'FULL'
        
        accessibility_health = {
            'api_available': True,
            'system_wide_access': True
        }
        
        issues = []  # No issues
        
        # Mock perfect benchmarks
        perfect_benchmark = Mock()
        perfect_benchmark.success_rate = 1.0
        benchmark_results = [perfect_benchmark]
        
        score = self.health_checker._calculate_health_score(
            permission_status, accessibility_health, issues, benchmark_results
        )
        
        self.assertEqual(score, 100.0)
    
    def test_calculate_health_score_critical_issues(self):
        """Test calculating health score with critical issues."""
        permission_status = None  # Unknown permissions
        
        accessibility_health = {
            'api_available': False,
            'system_wide_access': False
        }
        
        # Mock critical issue
        critical_issue = Mock()
        critical_issue.severity = 'CRITICAL'
        issues = [critical_issue]
        
        benchmark_results = []
        
        score = self.health_checker._calculate_health_score(
            permission_status, accessibility_health, issues, benchmark_results
        )
        
        # Should be significantly reduced
        self.assertLess(score, 50.0)
    
    def test_generate_recommendations_critical_issues(self):
        """Test generating recommendations for critical issues."""
        # Mock critical permission issue
        critical_issue = Mock()
        critical_issue.severity = 'CRITICAL'
        critical_issue.category = 'PERMISSIONS'
        issues = [critical_issue]
        
        benchmark_results = []
        
        recommendations = self.health_checker._generate_recommendations(issues, benchmark_results)
        
        self.assertTrue(len(recommendations) > 0)
        self.assertTrue(any('critical' in rec.lower() for rec in recommendations))
        self.assertTrue(any('accessibility permissions' in rec.lower() for rec in recommendations))
    
    def test_generate_recommendations_healthy_system(self):
        """Test generating recommendations for a healthy system."""
        issues = []  # No issues
        
        # Mock successful benchmarks
        good_benchmark = Mock()
        good_benchmark.success_rate = 0.9
        benchmark_results = [good_benchmark]
        
        recommendations = self.health_checker._generate_recommendations(issues, benchmark_results)
        
        self.assertTrue(len(recommendations) > 0)
        self.assertTrue(any('healthy' in rec.lower() for rec in recommendations))


@unittest.skipUnless(DIAGNOSTIC_TOOLS_AVAILABLE, "Diagnostic tools not available")
class TestDiagnosticReportGenerator(unittest.TestCase):
    """Test DiagnosticReportGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.report_generator = DiagnosticReportGenerator()
    
    def test_report_generator_initialization(self):
        """Test report generator initialization."""
        self.assertIsNotNone(self.report_generator)
        self.assertIn('CRITICAL', self.report_generator.severity_weights)
        self.assertIn('PERMISSIONS', self.report_generator.category_weights)
    
    def test_prioritize_issues(self):
        """Test prioritizing issues by severity and category."""
        # Create test issues with different priorities
        critical_issue = DiagnosticIssue(
            severity='CRITICAL',
            category='PERMISSIONS',
            title='Critical Permission Issue',
            description='Critical',
            impact='High',
            remediation_steps=[],
            metadata={},
            timestamp=datetime.now()
        )
        
        low_issue = DiagnosticIssue(
            severity='LOW',
            category='CONFIGURATION',
            title='Low Config Issue',
            description='Low',
            impact='Low',
            remediation_steps=[],
            metadata={},
            timestamp=datetime.now()
        )
        
        high_issue = DiagnosticIssue(
            severity='HIGH',
            category='SYSTEM',
            title='High System Issue',
            description='High',
            impact='Medium',
            remediation_steps=[],
            metadata={},
            timestamp=datetime.now()
        )
        
        issues = [low_issue, critical_issue, high_issue]
        prioritized = self.report_generator.prioritize_issues(issues)
        
        # Critical should be first, low should be last
        self.assertEqual(prioritized[0].severity, 'CRITICAL')
        self.assertEqual(prioritized[-1].severity, 'LOW')
    
    def test_generate_remediation_steps_permissions(self):
        """Test generating remediation steps for permission issues."""
        permission_issue = DiagnosticIssue(
            severity='CRITICAL',
            category='PERMISSIONS',
            title='Permission Issue',
            description='No permissions',
            impact='High',
            remediation_steps=['Grant permissions'],
            metadata={},
            timestamp=datetime.now()
        )
        
        steps = self.report_generator.generate_remediation_steps(permission_issue)
        
        self.assertTrue(len(steps) > 1)
        self.assertTrue(any('System Preferences' in step for step in steps))
        self.assertTrue(any('Accessibility' in step for step in steps))
    
    def test_generate_remediation_steps_system(self):
        """Test generating remediation steps for system issues."""
        system_issue = DiagnosticIssue(
            severity='HIGH',
            category='SYSTEM',
            title='System Issue',
            description='System problem',
            impact='Medium',
            remediation_steps=['Check system'],
            metadata={},
            timestamp=datetime.now()
        )
        
        steps = self.report_generator.generate_remediation_steps(system_issue)
        
        self.assertTrue(len(steps) > 1)
        self.assertTrue(any('macOS version' in step for step in steps))
    
    def test_generate_issue_summary(self):
        """Test generating issue summary."""
        issues = [
            DiagnosticIssue(
                severity='CRITICAL',
                category='PERMISSIONS',
                title='Critical Issue 1',
                description='Critical',
                impact='High',
                remediation_steps=[],
                metadata={},
                timestamp=datetime.now()
            ),
            DiagnosticIssue(
                severity='CRITICAL',
                category='SYSTEM',
                title='Critical Issue 2',
                description='Critical',
                impact='High',
                remediation_steps=[],
                metadata={},
                timestamp=datetime.now()
            ),
            DiagnosticIssue(
                severity='HIGH',
                category='PERFORMANCE',
                title='High Issue',
                description='High',
                impact='Medium',
                remediation_steps=[],
                metadata={},
                timestamp=datetime.now()
            )
        ]
        
        summary = self.report_generator.generate_issue_summary(issues)
        
        self.assertEqual(summary['total_issues'], 3)
        self.assertEqual(summary['by_severity']['CRITICAL'], 2)
        self.assertEqual(summary['by_severity']['HIGH'], 1)
        self.assertEqual(summary['by_category']['PERMISSIONS'], 1)
        self.assertEqual(summary['by_category']['SYSTEM'], 1)
        self.assertEqual(summary['by_category']['PERFORMANCE'], 1)
        self.assertEqual(len(summary['critical_issues']), 2)
        self.assertEqual(len(summary['high_priority_issues']), 1)
        self.assertEqual(summary['impact_assessment']['overall'], 'CRITICAL')


@unittest.skipUnless(DIAGNOSTIC_TOOLS_AVAILABLE, "Diagnostic tools not available")
class TestDiagnosticReport(unittest.TestCase):
    """Test DiagnosticReport data class."""
    
    def test_diagnostic_report_creation(self):
        """Test creating a diagnostic report."""
        timestamp = datetime.now()
        
        report = DiagnosticReport(
            timestamp=timestamp,
            system_info={'platform': 'Darwin'},
            permission_status=None,
            accessibility_health={'api_available': True},
            performance_metrics={'success_rate': 0.8},
            benchmark_results=[],
            detected_issues=[],
            recommendations=['Test recommendation'],
            overall_health_score=85.0,
            generation_time_ms=100.0
        )
        
        self.assertEqual(report.timestamp, timestamp)
        self.assertEqual(report.overall_health_score, 85.0)
        self.assertEqual(len(report.recommendations), 1)
    
    def test_generate_summary(self):
        """Test generating report summary."""
        timestamp = datetime.now()
        
        # Create test issue
        test_issue = DiagnosticIssue(
            severity='HIGH',
            category='PERMISSIONS',
            title='Test Issue',
            description='Test',
            impact='Medium',
            remediation_steps=[],
            metadata={},
            timestamp=timestamp
        )
        
        report = DiagnosticReport(
            timestamp=timestamp,
            system_info={'platform': 'Darwin'},
            permission_status=None,
            accessibility_health={'api_available': True},
            performance_metrics={'success_rate': 0.8},
            benchmark_results=[],
            detected_issues=[test_issue],
            recommendations=['Fix the issue', 'Monitor system'],
            overall_health_score=75.0,
            generation_time_ms=150.0
        )
        
        summary = report.generate_summary()
        
        self.assertIn('AURA Diagnostic Report', summary)
        self.assertIn('75.0/100', summary)
        self.assertIn('Issues Found: 1 total', summary)
        self.assertIn('Fix the issue', summary)
    
    def test_export_report_json(self):
        """Test exporting report as JSON."""
        timestamp = datetime.now()
        
        report = DiagnosticReport(
            timestamp=timestamp,
            system_info={'platform': 'Darwin'},
            permission_status=None,
            accessibility_health={'api_available': True},
            performance_metrics={'success_rate': 0.8},
            benchmark_results=[],
            detected_issues=[],
            recommendations=['Test'],
            overall_health_score=90.0,
            generation_time_ms=50.0
        )
        
        json_export = report.export_report('JSON')
        
        self.assertIn('"overall_health_score": 90.0', json_export)
        self.assertIn('"platform": "Darwin"', json_export)
    
    def test_export_report_text(self):
        """Test exporting report as text."""
        timestamp = datetime.now()
        
        report = DiagnosticReport(
            timestamp=timestamp,
            system_info={'platform': 'Darwin'},
            permission_status=None,
            accessibility_health={'api_available': True},
            performance_metrics={'success_rate': 0.8},
            benchmark_results=[],
            detected_issues=[],
            recommendations=['Test recommendation'],
            overall_health_score=95.0,
            generation_time_ms=25.0
        )
        
        text_export = report.export_report('TEXT')
        
        self.assertIn('AURA Diagnostic Report', text_export)
        self.assertIn('95.0/100', text_export)


if __name__ == '__main__':
    unittest.main()
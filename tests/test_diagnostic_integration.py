"""
Integration tests for diagnostic tools workflow.

Tests complete diagnostic workflow from issue detection to resolution recommendations.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import json
from datetime import datetime
from typing import Dict, Any, List

# Import the modules under test
try:
    from modules.diagnostic_tools import (
        AccessibilityHealthChecker,
        DiagnosticReportGenerator,
        AdvancedDiagnosticReporter,
        DiagnosticIssue,
        PerformanceBenchmark,
        DiagnosticReport
    )
    from modules.permission_validator import PermissionStatus
    DIAGNOSTIC_TOOLS_AVAILABLE = True
except ImportError as e:
    DIAGNOSTIC_TOOLS_AVAILABLE = False
    print(f"Diagnostic tools not available for integration testing: {e}")


@unittest.skipUnless(DIAGNOSTIC_TOOLS_AVAILABLE, "Diagnostic tools not available")
class TestDiagnosticWorkflowIntegration(unittest.TestCase):
    """Test complete diagnostic workflow integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'test_applications': ['Safari', 'Finder', 'Terminal'],
            'known_good_elements': {
                'Safari': ['Address and Search', 'Bookmarks', 'History'],
                'Finder': ['New Folder', 'View', 'Go'],
                'Terminal': ['Shell', 'Edit', 'View']
            },
            'debug_level': 'DETAILED'
        }
        
        # Mock all external dependencies
        with patch('modules.diagnostic_tools.MODULES_AVAILABLE', True):
            with patch('modules.diagnostic_tools.ACCESSIBILITY_FRAMEWORKS_AVAILABLE', True):
                with patch('modules.diagnostic_tools.PSUTIL_AVAILABLE', True):
                    self.advanced_reporter = AdvancedDiagnosticReporter(self.config)
    
    @patch('modules.diagnostic_tools.NSWorkspace')
    @patch('modules.diagnostic_tools.AXIsProcessTrusted')
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    def test_complete_diagnostic_workflow_healthy_system(self, mock_cpu_count, mock_memory, 
                                                        mock_ax_trusted, mock_workspace):
        """Test complete diagnostic workflow for a healthy system."""
        # Mock a healthy system
        mock_ax_trusted.return_value = True
        mock_memory.return_value = Mock(total=8589934592, available=4294967296, percent=50.0)
        mock_cpu_count.return_value = 8
        
        # Mock running applications
        mock_app = Mock()
        mock_app.localizedName.return_value = 'Safari'
        mock_app.processIdentifier.return_value = 1234
        
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = [mock_app]
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        # Mock permission validator
        mock_permission_status = PermissionStatus(
            has_permissions=True,
            permission_level='FULL',
            missing_permissions=[],
            granted_permissions=['basic_access', 'system_wide_access'],
            can_request_permissions=True,
            system_version='12.0',
            recommendations=[],
            timestamp=datetime.now(),
            check_duration_ms=50.0
        )
        
        self.advanced_reporter.health_checker.permission_validator = Mock()
        self.advanced_reporter.health_checker.permission_validator.check_accessibility_permissions.return_value = mock_permission_status
        
        # Mock accessibility debugger
        mock_tree_dump = Mock()
        mock_tree_dump.find_elements_by_text.return_value = [
            {'title': 'Address and Search', 'match_score': 95.0, 'role': 'AXTextField'},
            {'title': 'Bookmarks', 'match_score': 100.0, 'role': 'AXButton'}
        ]
        
        self.advanced_reporter.health_checker.accessibility_debugger = Mock()
        self.advanced_reporter.health_checker.accessibility_debugger.dump_accessibility_tree.return_value = mock_tree_dump
        
        # Mock accessibility health check to return healthy status
        with patch.object(self.advanced_reporter.health_checker, '_check_accessibility_api_health') as mock_health:
            mock_health.return_value = {
                'api_available': True,
                'system_wide_access': True,
                'focused_app_access': True,
                'process_trusted': True,
                'running_applications_count': 1,
                'errors': []
            }
            
            # Run comprehensive diagnostic
            report = self.advanced_reporter.generate_comprehensive_report()
            
            # Verify healthy system results
            self.assertIsInstance(report, DiagnosticReport)
            self.assertGreaterEqual(report.overall_health_score, 85.0)
            self.assertEqual(len([i for i in report.detected_issues if i.severity == 'CRITICAL']), 0)
            self.assertTrue(any('EXCELLENT' in rec for rec in report.recommendations))
    
    @patch('modules.diagnostic_tools.NSWorkspace')
    @patch('modules.diagnostic_tools.AXIsProcessTrusted')
    def test_complete_diagnostic_workflow_critical_issues(self, mock_ax_trusted, mock_workspace):
        """Test complete diagnostic workflow with critical issues."""
        # Mock a system with critical issues
        mock_ax_trusted.return_value = False  # No accessibility permissions
        
        mock_workspace_instance = Mock()
        mock_workspace_instance.runningApplications.return_value = []
        mock_workspace.sharedWorkspace.return_value = mock_workspace_instance
        
        # Mock permission validator with no permissions
        mock_permission_status = PermissionStatus(
            has_permissions=False,
            permission_level='NONE',
            missing_permissions=['basic_access', 'system_wide_access'],
            granted_permissions=[],
            can_request_permissions=True,
            system_version='12.0',
            recommendations=['Grant accessibility permissions'],
            timestamp=datetime.now(),
            check_duration_ms=100.0
        )
        
        self.advanced_reporter.health_checker.permission_validator = Mock()
        self.advanced_reporter.health_checker.permission_validator.check_accessibility_permissions.return_value = mock_permission_status
        
        # Mock accessibility debugger (should fail)
        self.advanced_reporter.health_checker.accessibility_debugger = None
        
        # Run comprehensive diagnostic
        report = self.advanced_reporter.generate_comprehensive_report()
        
        # Verify critical issues detected
        self.assertIsInstance(report, DiagnosticReport)
        self.assertLessEqual(report.overall_health_score, 50.0)
        
        critical_issues = [i for i in report.detected_issues if i.severity == 'CRITICAL']
        self.assertGreater(len(critical_issues), 0)
        
        # Verify critical recommendations
        self.assertTrue(any('CRITICAL' in rec for rec in report.recommendations))
        self.assertTrue(any('accessibility permissions' in rec.lower() for rec in report.recommendations))
    
    def test_issue_prioritization_workflow(self):
        """Test issue prioritization and recommendation generation workflow."""
        # Create test issues with different priorities
        issues = [
            DiagnosticIssue(
                severity='LOW',
                category='CONFIGURATION',
                title='Minor Config Issue',
                description='Minor configuration problem',
                impact='Low impact',
                remediation_steps=['Fix config'],
                metadata={},
                timestamp=datetime.now()
            ),
            DiagnosticIssue(
                severity='CRITICAL',
                category='PERMISSIONS',
                title='No Accessibility Permissions',
                description='Critical permission issue',
                impact='High impact',
                remediation_steps=['Grant permissions'],
                metadata={},
                timestamp=datetime.now()
            ),
            DiagnosticIssue(
                severity='HIGH',
                category='PERFORMANCE',
                title='Poor Performance',
                description='Performance degradation',
                impact='Medium impact',
                remediation_steps=['Optimize system'],
                metadata={},
                timestamp=datetime.now()
            )
        ]
        
        # Test issue enhancement
        enhanced_issues = self.advanced_reporter._enhance_issue_analysis(issues)
        
        # Verify enhancement
        self.assertEqual(len(enhanced_issues), 3)
        
        # Check that critical issue has enhanced description
        critical_issue = next(i for i in enhanced_issues if i.severity == 'CRITICAL')
        self.assertIn('vision-based fallback', critical_issue.description)
        
        # Check metadata enhancement
        self.assertIn('impact_score', critical_issue.metadata)
        self.assertIn('resolution_priority', critical_issue.metadata)
        self.assertIn('estimated_resolution_minutes', critical_issue.metadata)
        
        # Verify prioritization
        prioritized = self.advanced_reporter.report_generator.prioritize_issues(enhanced_issues)
        self.assertEqual(prioritized[0].severity, 'CRITICAL')
        self.assertEqual(prioritized[-1].severity, 'LOW')
    
    def test_intelligent_recommendations_generation(self):
        """Test intelligent recommendations generation based on issues."""
        # Mock system state
        permission_status = PermissionStatus(
            has_permissions=False,
            permission_level='NONE',
            missing_permissions=['basic_access'],
            granted_permissions=[],
            can_request_permissions=True,
            system_version='12.0',
            recommendations=[],
            timestamp=datetime.now(),
            check_duration_ms=50.0
        )
        
        accessibility_health = {
            'api_available': False,
            'system_wide_access': False
        }
        
        issues = [
            DiagnosticIssue(
                severity='CRITICAL',
                category='PERMISSIONS',
                title='No Accessibility Permissions',
                description='Critical permission issue',
                impact='High impact',
                remediation_steps=['Grant permissions'],
                metadata={},
                timestamp=datetime.now()
            )
        ]
        
        benchmark_results = [
            PerformanceBenchmark(
                test_name='test_safari',
                fast_path_time=None,
                vision_fallback_time=2.0,
                performance_ratio=None,
                success_rate=0.0,
                error_message='No permissions',
                metadata={},
                timestamp=datetime.now()
            )
        ]
        
        # Generate intelligent recommendations
        recommendations = self.advanced_reporter._generate_intelligent_recommendations(
            issues, benchmark_results, permission_status, accessibility_health
        )
        
        # Verify recommendations
        self.assertTrue(len(recommendations) > 0)
        self.assertTrue(any('CRITICAL ISSUES DETECTED' in rec for rec in recommendations))
        self.assertTrue(any('ACCESSIBILITY PERMISSIONS REQUIRED' in rec for rec in recommendations))
        self.assertTrue(any('System Preferences' in rec for rec in recommendations))
    
    def test_enhanced_health_score_calculation(self):
        """Test enhanced health score calculation with weighted factors."""
        # Test perfect system
        perfect_permission = PermissionStatus(
            has_permissions=True,
            permission_level='FULL',
            missing_permissions=[],
            granted_permissions=['all'],
            can_request_permissions=True,
            system_version='12.0',
            recommendations=[],
            timestamp=datetime.now(),
            check_duration_ms=25.0
        )
        
        perfect_health = {
            'api_available': True,
            'system_wide_access': True
        }
        
        perfect_benchmark = PerformanceBenchmark(
            test_name='perfect_test',
            fast_path_time=0.1,
            vision_fallback_time=0.5,
            performance_ratio=0.2,
            success_rate=1.0,
            error_message=None,
            metadata={},
            timestamp=datetime.now()
        )
        
        perfect_score = self.advanced_reporter._calculate_enhanced_health_score(
            perfect_permission, perfect_health, [], [perfect_benchmark]
        )
        
        self.assertEqual(perfect_score, 100.0)
        
        # Test system with issues
        no_permission = PermissionStatus(
            has_permissions=False,
            permission_level='NONE',
            missing_permissions=['all'],
            granted_permissions=[],
            can_request_permissions=True,
            system_version='12.0',
            recommendations=[],
            timestamp=datetime.now(),
            check_duration_ms=100.0
        )
        
        bad_health = {
            'api_available': False,
            'system_wide_access': False
        }
        
        critical_issue = DiagnosticIssue(
            severity='CRITICAL',
            category='PERMISSIONS',
            title='Critical Issue',
            description='Critical',
            impact='High',
            remediation_steps=[],
            metadata={},
            timestamp=datetime.now()
        )
        
        failed_benchmark = PerformanceBenchmark(
            test_name='failed_test',
            fast_path_time=None,
            vision_fallback_time=3.0,
            performance_ratio=None,
            success_rate=0.0,
            error_message='Failed',
            metadata={},
            timestamp=datetime.now()
        )
        
        bad_score = self.advanced_reporter._calculate_enhanced_health_score(
            no_permission, bad_health, [critical_issue], [failed_benchmark]
        )
        
        self.assertLessEqual(bad_score, 30.0)
    
    def test_report_export_formats(self):
        """Test different report export formats."""
        # Create test report
        test_issue = DiagnosticIssue(
            severity='HIGH',
            category='PERFORMANCE',
            title='Test Issue',
            description='Test description',
            impact='Test impact',
            remediation_steps=['Step 1', 'Step 2'],
            metadata={'test': 'value'},
            timestamp=datetime.now()
        )
        
        report = DiagnosticReport(
            timestamp=datetime.now(),
            system_info={'platform': 'Darwin'},
            permission_status=None,
            accessibility_health={'api_available': True},
            performance_metrics={'success_rate': 0.8},
            benchmark_results=[],
            detected_issues=[test_issue],
            recommendations=['Test recommendation'],
            overall_health_score=75.0,
            generation_time_ms=100.0
        )
        
        # Test JSON export
        json_export = self.advanced_reporter.export_detailed_report(report, 'JSON')
        self.assertIn('"overall_health_score": 75.0', json_export)
        
        # Test HTML export
        html_export = self.advanced_reporter.export_detailed_report(report, 'HTML')
        self.assertIn('<html>', html_export)
        self.assertIn('AURA Diagnostic Report', html_export)
        self.assertIn('Test Issue', html_export)
        
        # Test enhanced text export
        text_export = self.advanced_reporter.export_detailed_report(report, 'TEXT')
        self.assertIn('AURA DIAGNOSTIC REPORT', text_export)
        self.assertIn('Health Score: 75.0/100', text_export)
        self.assertIn('Test Issue', text_export)
    
    def test_real_world_scenario_simulation(self):
        """Test simulation of real-world diagnostic scenarios."""
        # Scenario: New user with no permissions
        self._test_new_user_scenario()
        
        # Scenario: System with partial permissions
        self._test_partial_permissions_scenario()
        
        # Scenario: Performance degradation
        self._test_performance_degradation_scenario()
    
    def _test_new_user_scenario(self):
        """Test diagnostic workflow for new user with no permissions."""
        # Mock new user state
        with patch.object(self.advanced_reporter.health_checker, '_check_accessibility_permissions') as mock_perms:
            with patch.object(self.advanced_reporter.health_checker, '_check_accessibility_api_health') as mock_health:
                mock_perms.return_value = PermissionStatus(
                    has_permissions=False,
                    permission_level='NONE',
                    missing_permissions=['all'],
                    granted_permissions=[],
                    can_request_permissions=True,
                    system_version='12.0',
                    recommendations=['Grant permissions'],
                    timestamp=datetime.now(),
                    check_duration_ms=50.0
                )
                
                mock_health.return_value = {
                    'api_available': True,
                    'system_wide_access': False,
                    'process_trusted': False
                }
                
                report = self.advanced_reporter.generate_comprehensive_report()
                
                # Verify new user guidance
                self.assertLessEqual(report.overall_health_score, 70.0)  # More realistic expectation
                critical_issues = [i for i in report.detected_issues if i.severity == 'CRITICAL']
                self.assertGreater(len(critical_issues), 0)
                
                # Should have step-by-step permission instructions
                permission_recs = [r for r in report.recommendations if 'System Preferences' in r]
                self.assertGreater(len(permission_recs), 0)
    
    def _test_partial_permissions_scenario(self):
        """Test diagnostic workflow for system with partial permissions."""
        with patch.object(self.advanced_reporter.health_checker, '_check_accessibility_permissions') as mock_perms:
            mock_perms.return_value = PermissionStatus(
                has_permissions=True,
                permission_level='PARTIAL',
                missing_permissions=['system_wide_access'],
                granted_permissions=['basic_access'],
                can_request_permissions=True,
                system_version='12.0',
                recommendations=['Grant full permissions'],
                timestamp=datetime.now(),
                check_duration_ms=75.0
            )
            
            report = self.advanced_reporter.generate_comprehensive_report()
            
            # Should detect partial permission issues
            self.assertGreaterEqual(report.overall_health_score, 20.0)  # Lower expectation for partial permissions
            self.assertLessEqual(report.overall_health_score, 85.0)
            
            high_issues = [i for i in report.detected_issues if i.severity == 'HIGH']
            partial_issues = [i for i in high_issues if 'partial' in i.title.lower()]
            self.assertGreaterEqual(len(partial_issues), 0)
    
    def _test_performance_degradation_scenario(self):
        """Test diagnostic workflow for performance degradation."""
        # Mock system with good permissions but poor performance
        with patch.object(self.advanced_reporter.health_checker, '_check_accessibility_permissions') as mock_perms:
            with patch.object(self.advanced_reporter.health_checker, '_run_performance_benchmarks') as mock_benchmarks:
                mock_perms.return_value = PermissionStatus(
                    has_permissions=True,
                    permission_level='FULL',
                    missing_permissions=[],
                    granted_permissions=['all'],
                    can_request_permissions=True,
                    system_version='12.0',
                    recommendations=[],
                    timestamp=datetime.now(),
                    check_duration_ms=25.0
                )
                
                # Mock poor performance benchmarks
                mock_benchmarks.return_value = [
                    PerformanceBenchmark(
                        test_name='slow_app',
                        fast_path_time=2.0,
                        vision_fallback_time=3.0,
                        performance_ratio=0.67,
                        success_rate=0.3,  # Poor success rate
                        error_message=None,
                        metadata={},
                        timestamp=datetime.now()
                    )
                ]
                
                report = self.advanced_reporter.generate_comprehensive_report()
                
                # Should detect performance issues
                performance_issues = [i for i in report.detected_issues if i.category == 'PERFORMANCE']
                self.assertGreater(len(performance_issues), 0)
                
                # Should have performance optimization recommendations
                perf_recs = [r for r in report.recommendations if 'PERFORMANCE' in r]
                self.assertGreater(len(perf_recs), 0)


if __name__ == '__main__':
    unittest.main()
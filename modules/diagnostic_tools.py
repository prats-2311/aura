"""
Diagnostic Tools for AURA - Comprehensive accessibility health checking and reporting

This module provides automated diagnostic tools for accessibility issues,
including system health checks, performance benchmarking, and recommendation systems.
"""

import logging
import time
import json
import threading
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import subprocess
import os

# Import existing modules
try:
    from .permission_validator import PermissionValidator, PermissionStatus
    from .accessibility_debugger import AccessibilityDebugger, AccessibilityTreeDump
    from .performance import PerformanceMonitor, HybridPerformanceMonitor, PerformanceMetrics
    MODULES_AVAILABLE = True
except ImportError as e:
    MODULES_AVAILABLE = False
    logging.warning(f"Some modules not available for diagnostic tools: {e}")

# Import system utilities
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Import accessibility frameworks
try:
    from ApplicationServices import AXIsProcessTrusted
    from AppKit import NSWorkspace
    ACCESSIBILITY_FRAMEWORKS_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_FRAMEWORKS_AVAILABLE = False


@dataclass
class DiagnosticIssue:
    """Represents a diagnostic issue found during health checking."""
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'
    category: str  # 'PERMISSIONS', 'PERFORMANCE', 'CONFIGURATION', 'SYSTEM'
    title: str
    description: str
    impact: str
    remediation_steps: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class PerformanceBenchmark:
    """Performance benchmark results."""
    test_name: str
    fast_path_time: Optional[float]
    vision_fallback_time: Optional[float]
    performance_ratio: Optional[float]  # fast_path_time / vision_fallback_time
    success_rate: float
    error_message: Optional[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class DiagnosticReport:
    """Comprehensive system diagnostic report."""
    timestamp: datetime
    system_info: Dict[str, Any]
    permission_status: Optional[PermissionStatus]
    accessibility_health: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    benchmark_results: List[PerformanceBenchmark]
    detected_issues: List[DiagnosticIssue]
    recommendations: List[str]
    overall_health_score: float  # 0-100
    generation_time_ms: float
    
    def generate_summary(self) -> str:
        """Generate human-readable diagnostic summary."""
        lines = []
        lines.append("=== AURA Diagnostic Report ===")
        lines.append(f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Overall Health Score: {self.overall_health_score:.1f}/100")
        lines.append("")
        
        # Permission status
        if self.permission_status:
            lines.append(f"Accessibility Permissions: {self.permission_status.get_summary()}")
        
        # Issues summary
        if self.detected_issues:
            critical_issues = [i for i in self.detected_issues if i.severity == 'CRITICAL']
            high_issues = [i for i in self.detected_issues if i.severity == 'HIGH']
            
            lines.append(f"Issues Found: {len(self.detected_issues)} total")
            if critical_issues:
                lines.append(f"  - {len(critical_issues)} CRITICAL issues")
            if high_issues:
                lines.append(f"  - {len(high_issues)} HIGH priority issues")
        else:
            lines.append("Issues Found: None")
        
        # Performance summary
        if self.benchmark_results:
            successful_benchmarks = [b for b in self.benchmark_results if b.success_rate > 0.8]
            lines.append(f"Performance Tests: {len(successful_benchmarks)}/{len(self.benchmark_results)} passed")
        
        # Top recommendations
        if self.recommendations:
            lines.append("")
            lines.append("Top Recommendations:")
            for i, rec in enumerate(self.recommendations[:3], 1):
                lines.append(f"  {i}. {rec}")
        
        return "\n".join(lines)
    
    def export_report(self, format: str = 'JSON') -> str:
        """Export report in specified format."""
        if format.upper() == 'JSON':
            data = asdict(self)
            data['timestamp'] = self.timestamp.isoformat()
            if self.permission_status:
                data['permission_status'] = self.permission_status.to_dict()
            return json.dumps(data, indent=2, default=str)
        elif format.upper() == 'TEXT':
            return self.generate_summary()
        else:
            raise ValueError(f"Unsupported export format: {format}")


class AccessibilityHealthChecker:
    """Automated accessibility health checking system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the accessibility health checker.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize components
        self.permission_validator = None
        self.accessibility_debugger = None
        self.performance_monitor = None
        
        if MODULES_AVAILABLE:
            try:
                self.permission_validator = PermissionValidator(config)
                self.accessibility_debugger = AccessibilityDebugger(config)
                self.performance_monitor = PerformanceMonitor()
            except Exception as e:
                self.logger.warning(f"Could not initialize some diagnostic components: {e}")
        
        # Test applications for benchmarking
        self.test_applications = self.config.get('test_applications', [
            'Finder', 'Safari', 'System Preferences', 'Terminal'
        ])
        
        # Known good elements for testing
        self.known_good_elements = self.config.get('known_good_elements', {
            'Finder': ['New Folder', 'View', 'Go'],
            'Safari': ['Address and Search', 'Bookmarks', 'History'],
            'System Preferences': ['Show All', 'Search'],
            'Terminal': ['Shell', 'Edit', 'View']
        })
        
        self.logger.info("Accessibility health checker initialized")
    
    def run_comprehensive_health_check(self) -> DiagnosticReport:
        """
        Run comprehensive accessibility health check.
        
        Returns:
            Complete diagnostic report with findings and recommendations
        """
        start_time = time.time()
        self.logger.info("Starting comprehensive accessibility health check")
        
        try:
            # Gather system information
            system_info = self._gather_system_information()
            
            # Check accessibility permissions
            permission_status = self._check_accessibility_permissions()
            
            # Check accessibility API availability
            accessibility_health = self._check_accessibility_api_health()
            
            # Run performance benchmarks
            benchmark_results = self._run_performance_benchmarks()
            
            # Collect performance metrics
            performance_metrics = self._collect_performance_metrics()
            
            # Analyze issues
            detected_issues = self._analyze_system_issues(
                system_info, permission_status, accessibility_health, benchmark_results
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(detected_issues, benchmark_results)
            
            # Calculate overall health score
            health_score = self._calculate_health_score(
                permission_status, accessibility_health, detected_issues, benchmark_results
            )
            
            generation_time_ms = (time.time() - start_time) * 1000
            
            # Create diagnostic report
            report = DiagnosticReport(
                timestamp=datetime.now(),
                system_info=system_info,
                permission_status=permission_status,
                accessibility_health=accessibility_health,
                performance_metrics=performance_metrics,
                benchmark_results=benchmark_results,
                detected_issues=detected_issues,
                recommendations=recommendations,
                overall_health_score=health_score,
                generation_time_ms=generation_time_ms
            )
            
            self.logger.info(f"Health check completed in {generation_time_ms:.1f}ms, "
                           f"health score: {health_score:.1f}/100")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            # Return minimal report with error information
            return DiagnosticReport(
                timestamp=datetime.now(),
                system_info={'error': str(e)},
                permission_status=None,
                accessibility_health={'error': str(e)},
                performance_metrics={},
                benchmark_results=[],
                detected_issues=[DiagnosticIssue(
                    severity='CRITICAL',
                    category='SYSTEM',
                    title='Health Check Failed',
                    description=f'Diagnostic health check failed: {str(e)}',
                    impact='Cannot assess system health',
                    remediation_steps=['Check system logs', 'Restart AURA', 'Contact support'],
                    metadata={'exception': str(e)},
                    timestamp=datetime.now()
                )],
                recommendations=['Fix health check system before proceeding'],
                overall_health_score=0.0,
                generation_time_ms=(time.time() - start_time) * 1000
            )
    
    def test_element_detection_capability(self, app_name: str, 
                                        element_texts: List[str]) -> Dict[str, Any]:
        """
        Test element detection capability with known good elements.
        
        Args:
            app_name: Name of application to test
            element_texts: List of element texts to search for
            
        Returns:
            Test results dictionary
        """
        start_time = time.time()
        results = {
            'app_name': app_name,
            'total_elements_tested': len(element_texts),
            'elements_found': 0,
            'elements_not_found': 0,
            'detection_rate': 0.0,
            'avg_detection_time': 0.0,
            'test_results': [],
            'errors': []
        }
        
        try:
            if not self.accessibility_debugger:
                results['errors'].append('Accessibility debugger not available')
                return results
            
            # Get accessibility tree for the application
            tree_dump = self.accessibility_debugger.dump_accessibility_tree(app_name)
            
            total_detection_time = 0.0
            
            for element_text in element_texts:
                element_start_time = time.time()
                
                try:
                    # Try to find the element
                    matches = tree_dump.find_elements_by_text(element_text, fuzzy=True, threshold=70.0)
                    
                    detection_time = (time.time() - element_start_time) * 1000
                    total_detection_time += detection_time
                    
                    test_result = {
                        'element_text': element_text,
                        'found': len(matches) > 0,
                        'match_count': len(matches),
                        'best_match_score': matches[0].get('match_score', 0) if matches else 0,
                        'detection_time_ms': detection_time
                    }
                    
                    if matches:
                        results['elements_found'] += 1
                        test_result['best_match'] = matches[0]
                    else:
                        results['elements_not_found'] += 1
                    
                    results['test_results'].append(test_result)
                    
                except Exception as e:
                    results['errors'].append(f"Error testing '{element_text}': {str(e)}")
                    results['elements_not_found'] += 1
            
            # Calculate summary statistics
            if results['total_elements_tested'] > 0:
                results['detection_rate'] = (results['elements_found'] / results['total_elements_tested']) * 100
            
            if results['elements_found'] > 0:
                results['avg_detection_time'] = total_detection_time / len(element_texts)
            
            test_duration = (time.time() - start_time) * 1000
            results['total_test_time_ms'] = test_duration
            
            self.logger.info(f"Element detection test for {app_name}: "
                           f"{results['elements_found']}/{results['total_elements_tested']} found "
                           f"({results['detection_rate']:.1f}%)")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Element detection test failed for {app_name}: {e}")
            results['errors'].append(f"Test failed: {str(e)}")
            return results
    
    def _gather_system_information(self) -> Dict[str, Any]:
        """Gather comprehensive system information."""
        system_info = {
            'timestamp': datetime.now().isoformat(),
            'platform': 'unknown',
            'version': 'unknown',
            'python_version': 'unknown',
            'accessibility_frameworks': ACCESSIBILITY_FRAMEWORKS_AVAILABLE,
            'modules_available': MODULES_AVAILABLE,
            'psutil_available': PSUTIL_AVAILABLE
        }
        
        try:
            import platform
            system_info.update({
                'platform': platform.system(),
                'version': platform.version(),
                'release': platform.release(),
                'machine': platform.machine(),
                'python_version': platform.python_version()
            })
            
            # macOS specific information
            if system_info['platform'] == 'Darwin':
                mac_ver = platform.mac_ver()
                system_info.update({
                    'macos_version': mac_ver[0],
                    'is_apple_silicon': system_info['machine'] in ['arm64', 'aarch64']
                })
        except Exception as e:
            system_info['system_info_error'] = str(e)
        
        # System resources
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('.')
                system_info.update({
                    'cpu_count': psutil.cpu_count(),
                    'memory_total_gb': memory.total / (1024**3),
                    'memory_available_gb': memory.available / (1024**3),
                    'memory_percent': memory.percent,
                    'disk_total_gb': disk.total / (1024**3),
                    'disk_free_gb': disk.free / (1024**3),
                    'disk_percent': disk.percent
                })
            except Exception as e:
                system_info['resource_info_error'] = str(e)
        
        return system_info
    
    def _check_accessibility_permissions(self) -> Optional[PermissionStatus]:
        """Check accessibility permissions status."""
        try:
            if self.permission_validator:
                return self.permission_validator.check_accessibility_permissions()
            else:
                self.logger.warning("Permission validator not available")
                return None
        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            return None
    
    def _check_accessibility_api_health(self) -> Dict[str, Any]:
        """Check accessibility API health and availability."""
        health_info = {
            'api_available': False,
            'system_wide_access': False,
            'focused_app_access': False,
            'running_applications_count': 0,
            'test_results': {},
            'errors': []
        }
        
        try:
            if not ACCESSIBILITY_FRAMEWORKS_AVAILABLE:
                health_info['errors'].append('Accessibility frameworks not available')
                return health_info
            
            # Test basic API availability
            try:
                is_trusted = AXIsProcessTrusted()
                health_info['api_available'] = True
                health_info['process_trusted'] = bool(is_trusted)
            except Exception as e:
                health_info['errors'].append(f'API availability test failed: {str(e)}')
            
            # Test system-wide access
            try:
                from ApplicationServices import AXUIElementCreateSystemWide, AXUIElementCopyAttributeValue, kAXFocusedApplicationAttribute
                system_wide = AXUIElementCreateSystemWide()
                if system_wide:
                    focused_app = AXUIElementCopyAttributeValue(system_wide, kAXFocusedApplicationAttribute)
                    health_info['system_wide_access'] = focused_app is not None
                    health_info['focused_app_access'] = focused_app is not None
            except Exception as e:
                health_info['errors'].append(f'System-wide access test failed: {str(e)}')
            
            # Test application enumeration
            try:
                workspace = NSWorkspace.sharedWorkspace()
                if workspace:
                    running_apps = workspace.runningApplications()
                    health_info['running_applications_count'] = len(running_apps)
                    
                    # Test accessibility for a few applications
                    test_apps = running_apps[:3]  # Test first 3 apps
                    for app in test_apps:
                        app_name = app.localizedName()
                        try:
                            from ApplicationServices import AXUIElementCreateApplication
                            app_element = AXUIElementCreateApplication(app.processIdentifier())
                            health_info['test_results'][app_name] = {
                                'accessible': app_element is not None,
                                'pid': app.processIdentifier()
                            }
                        except Exception as e:
                            health_info['test_results'][app_name] = {
                                'accessible': False,
                                'error': str(e)
                            }
            except Exception as e:
                health_info['errors'].append(f'Application enumeration test failed: {str(e)}')
            
        except Exception as e:
            health_info['errors'].append(f'Accessibility API health check failed: {str(e)}')
        
        return health_info
    
    def _run_performance_benchmarks(self) -> List[PerformanceBenchmark]:
        """Run performance benchmarks comparing fast path vs vision fallback."""
        benchmarks = []
        
        # Test with available applications
        available_apps = self._get_available_test_applications()
        
        for app_name in available_apps[:3]:  # Limit to 3 apps for performance
            try:
                benchmark = self._benchmark_application_performance(app_name)
                if benchmark:
                    benchmarks.append(benchmark)
            except Exception as e:
                self.logger.error(f"Benchmark failed for {app_name}: {e}")
                benchmarks.append(PerformanceBenchmark(
                    test_name=f"benchmark_{app_name}",
                    fast_path_time=None,
                    vision_fallback_time=None,
                    performance_ratio=None,
                    success_rate=0.0,
                    error_message=str(e),
                    metadata={'app_name': app_name},
                    timestamp=datetime.now()
                ))
        
        return benchmarks
    
    def _benchmark_application_performance(self, app_name: str) -> Optional[PerformanceBenchmark]:
        """Benchmark performance for a specific application."""
        try:
            # Get known good elements for this application
            test_elements = self.known_good_elements.get(app_name, [])
            if not test_elements:
                return None
            
            # Test element detection capability (simulates fast path)
            fast_path_results = self.test_element_detection_capability(app_name, test_elements)
            
            # Calculate metrics
            fast_path_time = fast_path_results.get('avg_detection_time', 0) / 1000.0  # Convert to seconds
            success_rate = fast_path_results.get('detection_rate', 0) / 100.0
            
            # For vision fallback time, we estimate based on typical vision processing time
            # In a real implementation, this would involve actual vision API calls
            vision_fallback_time = fast_path_time * 5.0  # Estimate vision is 5x slower
            
            performance_ratio = fast_path_time / vision_fallback_time if vision_fallback_time > 0 else None
            
            return PerformanceBenchmark(
                test_name=f"benchmark_{app_name}",
                fast_path_time=fast_path_time,
                vision_fallback_time=vision_fallback_time,
                performance_ratio=performance_ratio,
                success_rate=success_rate,
                error_message=None,
                metadata={
                    'app_name': app_name,
                    'elements_tested': len(test_elements),
                    'elements_found': fast_path_results.get('elements_found', 0),
                    'test_results': fast_path_results
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Performance benchmark failed for {app_name}: {e}")
            return None
    
    def _get_available_test_applications(self) -> List[str]:
        """Get list of available applications for testing."""
        available_apps = []
        
        try:
            if not ACCESSIBILITY_FRAMEWORKS_AVAILABLE:
                return available_apps
            
            workspace = NSWorkspace.sharedWorkspace()
            if not workspace:
                return available_apps
            
            running_apps = workspace.runningApplications()
            running_app_names = [app.localizedName() for app in running_apps]
            
            # Filter test applications to only those currently running
            for app_name in self.test_applications:
                if app_name in running_app_names:
                    available_apps.append(app_name)
            
        except Exception as e:
            self.logger.error(f"Failed to get available test applications: {e}")
        
        return available_apps
    
    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics."""
        metrics = {}
        
        try:
            if self.performance_monitor:
                metrics = self.performance_monitor.get_performance_summary(time_window_minutes=60)
            
            # Add system metrics
            if PSUTIL_AVAILABLE:
                metrics.update({
                    'current_cpu_percent': psutil.cpu_percent(interval=1),
                    'current_memory_percent': psutil.virtual_memory().percent,
                    'current_disk_percent': psutil.disk_usage('.').percent
                })
        except Exception as e:
            self.logger.error(f"Failed to collect performance metrics: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _analyze_system_issues(self, system_info: Dict[str, Any], 
                             permission_status: Optional[PermissionStatus],
                             accessibility_health: Dict[str, Any],
                             benchmark_results: List[PerformanceBenchmark]) -> List[DiagnosticIssue]:
        """Analyze system state and identify issues."""
        issues = []
        
        # Check permission issues
        if permission_status:
            if not permission_status.has_permissions:
                issues.append(DiagnosticIssue(
                    severity='CRITICAL',
                    category='PERMISSIONS',
                    title='Accessibility Permissions Not Granted',
                    description='AURA does not have accessibility permissions required for fast path execution',
                    impact='All commands will fall back to slower vision-based processing',
                    remediation_steps=permission_status.recommendations or ['Grant accessibility permissions in System Preferences'],
                    metadata={'permission_status': permission_status.to_dict()},
                    timestamp=datetime.now()
                ))
            elif permission_status.permission_level == 'PARTIAL':
                issues.append(DiagnosticIssue(
                    severity='HIGH',
                    category='PERMISSIONS',
                    title='Partial Accessibility Permissions',
                    description='AURA has partial accessibility permissions which may cause reliability issues',
                    impact='Some commands may fail or be unreliable',
                    remediation_steps=permission_status.recommendations or ['Grant full accessibility permissions'],
                    metadata={'permission_status': permission_status.to_dict()},
                    timestamp=datetime.now()
                ))
        else:
            # No permission status available - this is also a critical issue
            issues.append(DiagnosticIssue(
                severity='CRITICAL',
                category='PERMISSIONS',
                title='Cannot Check Accessibility Permissions',
                description='Unable to determine accessibility permission status',
                impact='Fast path functionality may be disabled',
                remediation_steps=['Check system compatibility', 'Verify PyObjC installation'],
                metadata={'error': 'permission_status_unavailable'},
                timestamp=datetime.now()
            ))
        
        # Check accessibility API health
        if not accessibility_health.get('api_available', False):
            issues.append(DiagnosticIssue(
                severity='CRITICAL',
                category='SYSTEM',
                title='Accessibility API Not Available',
                description='macOS Accessibility API is not available or accessible',
                impact='Fast path execution is completely disabled',
                remediation_steps=[
                    'Check if PyObjC frameworks are installed',
                    'Verify macOS version compatibility',
                    'Restart the application'
                ],
                metadata={'accessibility_health': accessibility_health},
                timestamp=datetime.now()
            ))
        
        if not accessibility_health.get('system_wide_access', False):
            issues.append(DiagnosticIssue(
                severity='HIGH',
                category='PERMISSIONS',
                title='System-Wide Accessibility Access Failed',
                description='Cannot access system-wide accessibility elements',
                impact='Element detection may be limited or unreliable',
                remediation_steps=[
                    'Grant full accessibility permissions',
                    'Restart the application after granting permissions',
                    'Check System Preferences > Security & Privacy > Privacy > Accessibility'
                ],
                metadata={'accessibility_health': accessibility_health},
                timestamp=datetime.now()
            ))
        
        # Check performance benchmarks
        failed_benchmarks = [b for b in benchmark_results if b.success_rate < 0.5]
        if failed_benchmarks:
            issues.append(DiagnosticIssue(
                severity='HIGH',
                category='PERFORMANCE',
                title='Poor Element Detection Performance',
                description=f'{len(failed_benchmarks)} applications have low element detection success rates',
                impact='Commands may frequently fail or fall back to vision processing',
                remediation_steps=[
                    'Check application-specific accessibility settings',
                    'Verify applications are properly focused',
                    'Consider updating application versions'
                ],
                metadata={'failed_benchmarks': [b.to_dict() for b in failed_benchmarks]},
                timestamp=datetime.now()
            ))
        
        # Check system resources
        if system_info.get('memory_percent', 0) > 90:
            issues.append(DiagnosticIssue(
                severity='MEDIUM',
                category='SYSTEM',
                title='High Memory Usage',
                description=f'System memory usage is at {system_info.get("memory_percent", 0):.1f}%',
                impact='Performance may be degraded, increased risk of failures',
                remediation_steps=[
                    'Close unnecessary applications',
                    'Restart the system if memory usage remains high',
                    'Consider increasing system memory'
                ],
                metadata={'memory_info': {k: v for k, v in system_info.items() if 'memory' in k}},
                timestamp=datetime.now()
            ))
        
        # Check for framework availability
        if not system_info.get('accessibility_frameworks', False):
            issues.append(DiagnosticIssue(
                severity='CRITICAL',
                category='CONFIGURATION',
                title='Accessibility Frameworks Missing',
                description='Required PyObjC accessibility frameworks are not installed',
                impact='Fast path execution is completely disabled',
                remediation_steps=[
                    'Install PyObjC frameworks: pip install pyobjc-framework-AppKit pyobjc-framework-Accessibility',
                    'Restart the application after installation'
                ],
                metadata={'system_info': system_info},
                timestamp=datetime.now()
            ))
        
        return issues
    
    def _generate_recommendations(self, issues: List[DiagnosticIssue], 
                                benchmark_results: List[PerformanceBenchmark]) -> List[str]:
        """Generate actionable recommendations based on diagnostic results."""
        recommendations = []
        
        # Priority recommendations based on critical issues
        critical_issues = [i for i in issues if i.severity == 'CRITICAL']
        if critical_issues:
            recommendations.append("Address critical issues immediately to restore fast path functionality")
            
            # Specific recommendations for critical issues
            for issue in critical_issues:
                if issue.category == 'PERMISSIONS':
                    recommendations.append("Grant accessibility permissions in System Preferences > Security & Privacy")
                elif issue.category == 'CONFIGURATION':
                    recommendations.append("Install missing dependencies and restart AURA")
                elif issue.category == 'SYSTEM':
                    recommendations.append("Check system compatibility and accessibility API availability")
        
        # Performance recommendations
        successful_benchmarks = [b for b in benchmark_results if b.success_rate > 0.8]
        if len(successful_benchmarks) < len(benchmark_results) / 2:
            recommendations.append("Improve element detection reliability by updating application accessibility settings")
        
        # System optimization recommendations
        high_issues = [i for i in issues if i.severity == 'HIGH']
        if high_issues:
            recommendations.append("Resolve high-priority issues to improve system reliability")
        
        # General recommendations
        if not recommendations:
            recommendations.append("System appears healthy - monitor performance and run diagnostics periodically")
        
        recommendations.append("Run diagnostics again after making changes to verify improvements")
        
        return recommendations
    
    def _calculate_health_score(self, permission_status: Optional[PermissionStatus],
                              accessibility_health: Dict[str, Any],
                              issues: List[DiagnosticIssue],
                              benchmark_results: List[PerformanceBenchmark]) -> float:
        """Calculate overall system health score (0-100)."""
        score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == 'CRITICAL':
                score -= 25.0
            elif issue.severity == 'HIGH':
                score -= 15.0
            elif issue.severity == 'MEDIUM':
                score -= 10.0
            elif issue.severity == 'LOW':
                score -= 5.0
        
        # Deduct points for poor permissions
        if permission_status:
            if not permission_status.has_permissions:
                score -= 20.0
            elif permission_status.permission_level == 'PARTIAL':
                score -= 10.0
        else:
            score -= 15.0  # Unknown permission status
        
        # Deduct points for poor accessibility health
        if not accessibility_health.get('api_available', False):
            score -= 20.0
        if not accessibility_health.get('system_wide_access', False):
            score -= 15.0
        
        # Deduct points for poor benchmark performance
        if benchmark_results:
            avg_success_rate = sum(b.success_rate for b in benchmark_results) / len(benchmark_results)
            score -= (1.0 - avg_success_rate) * 20.0
        
        # Ensure score is within bounds
        return max(0.0, min(100.0, score))


class DiagnosticReportGenerator:
    """Generates diagnostic reports with actionable recommendations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the diagnostic report generator.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Issue prioritization weights
        self.severity_weights = {
            'CRITICAL': 100,
            'HIGH': 75,
            'MEDIUM': 50,
            'LOW': 25,
            'INFO': 10
        }
        
        # Category impact weights
        self.category_weights = {
            'PERMISSIONS': 90,
            'SYSTEM': 85,
            'PERFORMANCE': 70,
            'CONFIGURATION': 60
        }
        
        self.logger.info("Diagnostic report generator initialized")
    
    def prioritize_issues(self, issues: List[DiagnosticIssue]) -> List[DiagnosticIssue]:
        """
        Prioritize issues based on severity and impact on fast path performance.
        
        Args:
            issues: List of diagnostic issues
            
        Returns:
            Sorted list of issues by priority (highest first)
        """
        def calculate_priority_score(issue: DiagnosticIssue) -> float:
            severity_score = self.severity_weights.get(issue.severity, 0)
            category_score = self.category_weights.get(issue.category, 0)
            
            # Combine scores with weights
            priority_score = (severity_score * 0.7) + (category_score * 0.3)
            
            return priority_score
        
        # Sort by priority score (highest first)
        prioritized_issues = sorted(issues, key=calculate_priority_score, reverse=True)
        
        self.logger.debug(f"Prioritized {len(issues)} issues")
        return prioritized_issues
    
    def generate_remediation_steps(self, issue: DiagnosticIssue) -> List[str]:
        """
        Generate detailed remediation steps for a specific issue.
        
        Args:
            issue: Diagnostic issue
            
        Returns:
            List of detailed remediation steps
        """
        base_steps = issue.remediation_steps.copy()
        
        # Add category-specific steps
        if issue.category == 'PERMISSIONS':
            base_steps.extend([
                "Open System Preferences > Security & Privacy > Privacy > Accessibility",
                "Click the lock icon and enter your password",
                "Add Terminal (or your Python IDE) to the list of allowed applications",
                "Restart AURA after granting permissions"
            ])
        
        elif issue.category == 'SYSTEM':
            base_steps.extend([
                "Check macOS version compatibility (requires macOS 10.14+)",
                "Verify system integrity with 'sudo /usr/libexec/repair_packages --verify --standard-pkgs'",
                "Consider restarting the system if issues persist"
            ])
        
        elif issue.category == 'PERFORMANCE':
            base_steps.extend([
                "Monitor system resources and close unnecessary applications",
                "Update applications to latest versions",
                "Clear application caches if performance issues persist"
            ])
        
        elif issue.category == 'CONFIGURATION':
            base_steps.extend([
                "Verify all required dependencies are installed",
                "Check configuration files for syntax errors",
                "Reset configuration to defaults if necessary"
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_steps = []
        for step in base_steps:
            if step not in seen:
                seen.add(step)
                unique_steps.append(step)
        
        return unique_steps
    
    def generate_issue_summary(self, issues: List[DiagnosticIssue]) -> Dict[str, Any]:
        """
        Generate a summary of issues by category and severity.
        
        Args:
            issues: List of diagnostic issues
            
        Returns:
            Issue summary dictionary
        """
        summary = {
            'total_issues': len(issues),
            'by_severity': defaultdict(int),
            'by_category': defaultdict(int),
            'critical_issues': [],
            'high_priority_issues': [],
            'impact_assessment': {}
        }
        
        for issue in issues:
            summary['by_severity'][issue.severity] += 1
            summary['by_category'][issue.category] += 1
            
            if issue.severity == 'CRITICAL':
                summary['critical_issues'].append(issue.title)
            elif issue.severity == 'HIGH':
                summary['high_priority_issues'].append(issue.title)
        
        # Convert defaultdicts to regular dicts
        summary['by_severity'] = dict(summary['by_severity'])
        summary['by_category'] = dict(summary['by_category'])
        
        # Assess overall impact
        if summary['by_severity'].get('CRITICAL', 0) > 0:
            summary['impact_assessment']['overall'] = 'CRITICAL'
            summary['impact_assessment']['description'] = 'System has critical issues that prevent normal operation'
        elif summary['by_severity'].get('HIGH', 0) > 0:
            summary['impact_assessment']['overall'] = 'HIGH'
            summary['impact_assessment']['description'] = 'System has high-priority issues that significantly impact performance'
        elif summary['by_severity'].get('MEDIUM', 0) > 0:
            summary['impact_assessment']['overall'] = 'MEDIUM'
            summary['impact_assessment']['description'] = 'System has moderate issues that may affect reliability'
        else:
            summary['impact_assessment']['overall'] = 'LOW'
            summary['impact_assessment']['description'] = 'System is functioning well with minor issues'
        
        return summary


class AdvancedDiagnosticReporter:
    """Advanced diagnostic reporting with intelligent recommendations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the advanced diagnostic reporter.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize components
        self.health_checker = AccessibilityHealthChecker(config)
        self.report_generator = DiagnosticReportGenerator(config)
        
        # Recommendation templates
        self.recommendation_templates = {
            'CRITICAL_PERMISSIONS': [
                "Grant accessibility permissions immediately to restore fast path functionality",
                "Open System Preferences > Security & Privacy > Privacy > Accessibility",
                "Add Terminal (or your Python IDE) to the accessibility permissions list",
                "Restart AURA after granting permissions to activate fast path"
            ],
            'CRITICAL_API': [
                "Install required PyObjC frameworks: pip install pyobjc-framework-AppKit pyobjc-framework-Accessibility",
                "Verify macOS version compatibility (requires macOS 10.14 or later)",
                "Restart the application after installing dependencies"
            ],
            'HIGH_PERFORMANCE': [
                "Optimize system performance by closing unnecessary applications",
                "Update applications to latest versions for better accessibility support",
                "Consider increasing system memory if usage is consistently high"
            ],
            'MEDIUM_CONFIGURATION': [
                "Review and update AURA configuration settings",
                "Clear application caches if performance issues persist",
                "Verify all configuration files are properly formatted"
            ]
        }
        
        # Issue impact scoring
        self.impact_scores = {
            'fast_path_disabled': 100,
            'partial_functionality': 75,
            'performance_degraded': 50,
            'minor_issues': 25,
            'informational': 10
        }
        
        self.logger.info("Advanced diagnostic reporter initialized")
    
    def generate_comprehensive_report(self, include_benchmarks: bool = True,
                                    include_detailed_analysis: bool = True) -> DiagnosticReport:
        """
        Generate comprehensive diagnostic report with advanced analysis.
        
        Args:
            include_benchmarks: Whether to include performance benchmarks
            include_detailed_analysis: Whether to include detailed issue analysis
            
        Returns:
            Comprehensive diagnostic report
        """
        start_time = time.time()
        self.logger.info("Generating comprehensive diagnostic report")
        
        try:
            # Run basic health check
            base_report = self.health_checker.run_comprehensive_health_check()
            
            # Enhance with advanced analysis
            if include_detailed_analysis:
                enhanced_issues = self._enhance_issue_analysis(base_report.detected_issues)
                base_report.detected_issues = enhanced_issues
            
            # Add intelligent recommendations
            intelligent_recommendations = self._generate_intelligent_recommendations(
                base_report.detected_issues,
                base_report.benchmark_results,
                base_report.permission_status,
                base_report.accessibility_health
            )
            base_report.recommendations = intelligent_recommendations
            
            # Recalculate health score with enhanced analysis
            base_report.overall_health_score = self._calculate_enhanced_health_score(
                base_report.permission_status,
                base_report.accessibility_health,
                base_report.detected_issues,
                base_report.benchmark_results
            )
            
            # Update generation time
            base_report.generation_time_ms = (time.time() - start_time) * 1000
            
            self.logger.info(f"Comprehensive report generated in {base_report.generation_time_ms:.1f}ms")
            return base_report
            
        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive report: {e}")
            raise
    
    def _enhance_issue_analysis(self, issues: List[DiagnosticIssue]) -> List[DiagnosticIssue]:
        """Enhance issue analysis with additional context and impact assessment."""
        enhanced_issues = []
        
        for issue in issues:
            # Create enhanced copy
            enhanced_issue = DiagnosticIssue(
                severity=issue.severity,
                category=issue.category,
                title=issue.title,
                description=self._enhance_issue_description(issue),
                impact=self._calculate_detailed_impact(issue),
                remediation_steps=self._enhance_remediation_steps(issue),
                metadata=self._enhance_issue_metadata(issue),
                timestamp=issue.timestamp
            )
            
            enhanced_issues.append(enhanced_issue)
        
        return enhanced_issues
    
    def _enhance_issue_description(self, issue: DiagnosticIssue) -> str:
        """Enhance issue description with additional context."""
        base_description = issue.description
        
        # Add context based on category and severity
        if issue.category == 'PERMISSIONS' and issue.severity == 'CRITICAL':
            base_description += " This prevents AURA from accessing application UI elements directly, " \
                              "forcing all commands to use the slower vision-based fallback method."
        
        elif issue.category == 'PERFORMANCE' and 'detection' in issue.title.lower():
            base_description += " Poor element detection significantly impacts user experience " \
                              "and may cause commands to fail or take much longer to execute."
        
        elif issue.category == 'SYSTEM' and 'memory' in issue.title.lower():
            base_description += " High memory usage can cause system instability and " \
                              "significantly degrade AURA's performance."
        
        return base_description
    
    def _calculate_detailed_impact(self, issue: DiagnosticIssue) -> str:
        """Calculate detailed impact assessment for an issue."""
        impact_details = []
        
        # Base impact from original issue
        impact_details.append(issue.impact)
        
        # Add specific impacts based on issue type
        if issue.category == 'PERMISSIONS':
            if issue.severity == 'CRITICAL':
                impact_details.extend([
                    "Fast path execution completely disabled",
                    "All commands use slower vision processing (5-10x slower)",
                    "Increased system resource usage",
                    "Higher failure rate for complex UI interactions"
                ])
            elif issue.severity == 'HIGH':
                impact_details.extend([
                    "Intermittent fast path failures",
                    "Reduced reliability for certain applications",
                    "Occasional fallback to vision processing"
                ])
        
        elif issue.category == 'PERFORMANCE':
            impact_details.extend([
                "Degraded user experience",
                "Increased command execution time",
                "Higher system resource consumption"
            ])
        
        elif issue.category == 'SYSTEM':
            impact_details.extend([
                "System instability risk",
                "Potential for application crashes",
                "Reduced overall system performance"
            ])
        
        return " | ".join(impact_details)
    
    def _enhance_remediation_steps(self, issue: DiagnosticIssue) -> List[str]:
        """Enhance remediation steps with detailed instructions."""
        enhanced_steps = issue.remediation_steps.copy()
        
        # Add template-based steps
        template_key = f"{issue.severity}_{issue.category}"
        if template_key in self.recommendation_templates:
            template_steps = self.recommendation_templates[template_key]
            # Add template steps that aren't already present
            for step in template_steps:
                if not any(step.lower() in existing.lower() for existing in enhanced_steps):
                    enhanced_steps.append(step)
        
        # Add verification steps
        enhanced_steps.append("Verify the fix by running AURA diagnostics again")
        enhanced_steps.append("Test with a simple command to confirm functionality")
        
        return enhanced_steps
    
    def _enhance_issue_metadata(self, issue: DiagnosticIssue) -> Dict[str, Any]:
        """Enhance issue metadata with additional diagnostic information."""
        enhanced_metadata = issue.metadata.copy()
        
        # Add impact scoring
        impact_score = self._calculate_impact_score(issue)
        enhanced_metadata['impact_score'] = impact_score
        
        # Add resolution priority
        enhanced_metadata['resolution_priority'] = self._calculate_resolution_priority(issue)
        
        # Add estimated resolution time
        enhanced_metadata['estimated_resolution_minutes'] = self._estimate_resolution_time(issue)
        
        # Add related issues
        enhanced_metadata['related_categories'] = self._find_related_categories(issue)
        
        return enhanced_metadata
    
    def _calculate_impact_score(self, issue: DiagnosticIssue) -> int:
        """Calculate numerical impact score for an issue."""
        base_score = 0
        
        # Severity scoring
        severity_scores = {'CRITICAL': 40, 'HIGH': 30, 'MEDIUM': 20, 'LOW': 10, 'INFO': 5}
        base_score += severity_scores.get(issue.severity, 0)
        
        # Category scoring
        category_scores = {'PERMISSIONS': 35, 'SYSTEM': 30, 'PERFORMANCE': 25, 'CONFIGURATION': 15}
        base_score += category_scores.get(issue.category, 0)
        
        # Specific issue type scoring
        if 'accessibility' in issue.title.lower():
            base_score += 20
        if 'permission' in issue.title.lower():
            base_score += 15
        if 'memory' in issue.title.lower():
            base_score += 10
        
        return min(base_score, 100)  # Cap at 100
    
    def _calculate_resolution_priority(self, issue: DiagnosticIssue) -> str:
        """Calculate resolution priority for an issue."""
        impact_score = self._calculate_impact_score(issue)
        
        if impact_score >= 80:
            return 'IMMEDIATE'
        elif impact_score >= 60:
            return 'HIGH'
        elif impact_score >= 40:
            return 'MEDIUM'
        elif impact_score >= 20:
            return 'LOW'
        else:
            return 'WHEN_CONVENIENT'
    
    def _estimate_resolution_time(self, issue: DiagnosticIssue) -> int:
        """Estimate resolution time in minutes for an issue."""
        if issue.category == 'PERMISSIONS':
            return 5  # Usually quick to grant permissions
        elif issue.category == 'CONFIGURATION':
            return 10  # Configuration changes
        elif issue.category == 'SYSTEM':
            return 30  # May require system changes or restarts
        elif issue.category == 'PERFORMANCE':
            return 15  # Performance optimization
        else:
            return 20  # Default estimate
    
    def _find_related_categories(self, issue: DiagnosticIssue) -> List[str]:
        """Find categories related to this issue."""
        related = []
        
        if issue.category == 'PERMISSIONS':
            related.extend(['SYSTEM', 'CONFIGURATION'])
        elif issue.category == 'SYSTEM':
            related.extend(['PERFORMANCE', 'PERMISSIONS'])
        elif issue.category == 'PERFORMANCE':
            related.extend(['SYSTEM', 'CONFIGURATION'])
        elif issue.category == 'CONFIGURATION':
            related.extend(['PERMISSIONS', 'SYSTEM'])
        
        return related
    
    def _generate_intelligent_recommendations(self, issues: List[DiagnosticIssue],
                                            benchmark_results: List[PerformanceBenchmark],
                                            permission_status: Optional[PermissionStatus],
                                            accessibility_health: Dict[str, Any]) -> List[str]:
        """Generate intelligent recommendations based on comprehensive analysis."""
        recommendations = []
        
        # Prioritize issues
        prioritized_issues = self.report_generator.prioritize_issues(issues)
        
        # Critical issues first
        critical_issues = [i for i in prioritized_issues if i.severity == 'CRITICAL']
        if critical_issues:
            recommendations.append("🚨 CRITICAL ISSUES DETECTED - Address immediately:")
            for issue in critical_issues[:3]:  # Top 3 critical issues
                recommendations.append(f"   • {issue.title}: {issue.remediation_steps[0] if issue.remediation_steps else 'See detailed report'}")
        
        # Permission-specific recommendations
        if permission_status and not permission_status.has_permissions:
            recommendations.extend([
                "",
                "🔐 ACCESSIBILITY PERMISSIONS REQUIRED:",
                "   1. Open System Preferences > Security & Privacy > Privacy > Accessibility",
                "   2. Click the lock icon and enter your password",
                "   3. Add Terminal (or your Python IDE) to the list",
                "   4. Restart AURA to activate fast path functionality"
            ])
        
        # Performance recommendations
        failed_benchmarks = [b for b in benchmark_results if b.success_rate < 0.7]
        if failed_benchmarks:
            recommendations.extend([
                "",
                "⚡ PERFORMANCE OPTIMIZATION:",
                f"   • {len(failed_benchmarks)} applications have poor element detection",
                "   • Consider updating applications to latest versions",
                "   • Check application-specific accessibility settings"
            ])
        
        # System health recommendations
        if not accessibility_health.get('api_available', True):
            recommendations.extend([
                "",
                "🔧 SYSTEM REPAIR NEEDED:",
                "   • Install PyObjC frameworks: pip install pyobjc-framework-AppKit pyobjc-framework-Accessibility",
                "   • Verify macOS version compatibility",
                "   • Restart application after installing dependencies"
            ])
        
        # Preventive recommendations
        recommendations.extend([
            "",
            "🛡️ PREVENTIVE MEASURES:",
            "   • Run diagnostics weekly to catch issues early",
            "   • Keep applications updated for better accessibility support",
            "   • Monitor system resources to prevent performance degradation"
        ])
        
        # Success recommendations
        if not critical_issues and len([i for i in issues if i.severity in ['HIGH', 'MEDIUM']]) == 0:
            recommendations.extend([
                "",
                "✅ SYSTEM HEALTH EXCELLENT:",
                "   • All critical systems functioning properly",
                "   • Fast path accessibility working optimally",
                "   • Continue monitoring with periodic diagnostics"
            ])
        elif not critical_issues:
            recommendations.extend([
                "",
                "✅ SYSTEM HEALTH GOOD:",
                "   • No critical issues detected",
                "   • Minor issues may affect performance",
                "   • Address remaining issues when convenient"
            ])
        
        return recommendations
    
    def _calculate_enhanced_health_score(self, permission_status: Optional[PermissionStatus],
                                       accessibility_health: Dict[str, Any],
                                       issues: List[DiagnosticIssue],
                                       benchmark_results: List[PerformanceBenchmark]) -> float:
        """Calculate enhanced health score with weighted factors."""
        score = 100.0
        
        # Permission factor (40% weight) - Most critical for AURA
        if permission_status:
            if not permission_status.has_permissions:
                score -= 40.0  # Major penalty for no permissions
            elif permission_status.permission_level == 'PARTIAL':
                score -= 20.0  # Moderate penalty for partial permissions
        else:
            score -= 30.0  # Penalty for unknown permission status
        
        # API health factor (25% weight)
        if not accessibility_health.get('api_available', False):
            score -= 25.0  # Major penalty if API not available
        if not accessibility_health.get('system_wide_access', False):
            score -= 15.0  # Penalty for no system-wide access
        
        # Issues factor (25% weight) - Penalize based on severity
        for issue in issues:
            if issue.severity == 'CRITICAL':
                score -= 20.0  # Heavy penalty for critical issues
            elif issue.severity == 'HIGH':
                score -= 10.0  # Moderate penalty for high issues
            elif issue.severity == 'MEDIUM':
                score -= 5.0   # Light penalty for medium issues
            elif issue.severity == 'LOW':
                score -= 2.0   # Minimal penalty for low issues
        
        # Performance factor (10% weight)
        if benchmark_results:
            avg_success_rate = sum(b.success_rate for b in benchmark_results) / len(benchmark_results)
            score -= (1.0 - avg_success_rate) * 10.0
        
        return max(0.0, min(100.0, score))
    
    def export_detailed_report(self, report: DiagnosticReport, 
                             format: str = 'JSON',
                             include_metadata: bool = True) -> str:
        """
        Export detailed diagnostic report with enhanced formatting.
        
        Args:
            report: Diagnostic report to export
            format: Export format ('JSON', 'TEXT', 'HTML')
            include_metadata: Whether to include detailed metadata
            
        Returns:
            Formatted report string
        """
        if format.upper() == 'HTML':
            return self._export_html_report(report, include_metadata)
        elif format.upper() == 'TEXT':
            return self._export_enhanced_text_report(report, include_metadata)
        else:
            return report.export_report(format)
    
    def _export_html_report(self, report: DiagnosticReport, include_metadata: bool) -> str:
        """Export report as HTML with styling."""
        html_parts = []
        
        # HTML header
        html_parts.append("""
<!DOCTYPE html>
<html>
<head>
    <title>AURA Diagnostic Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .critical { color: #d32f2f; font-weight: bold; }
        .high { color: #f57c00; font-weight: bold; }
        .medium { color: #fbc02d; }
        .low { color: #388e3c; }
        .issue { margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }
        .recommendations { background-color: #e8f5e8; padding: 15px; border-radius: 5px; }
        .score { font-size: 24px; font-weight: bold; }
    </style>
</head>
<body>
""")
        
        # Report header
        html_parts.append(f"""
<div class="header">
    <h1>AURA Diagnostic Report</h1>
    <p><strong>Generated:</strong> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Health Score:</strong> <span class="score">{report.overall_health_score:.1f}/100</span></p>
    <p><strong>Generation Time:</strong> {report.generation_time_ms:.1f}ms</p>
</div>
""")
        
        # Issues section
        if report.detected_issues:
            html_parts.append("<h2>Detected Issues</h2>")
            for issue in report.detected_issues:
                severity_class = issue.severity.lower()
                html_parts.append(f"""
<div class="issue">
    <h3 class="{severity_class}">[{issue.severity}] {issue.title}</h3>
    <p><strong>Category:</strong> {issue.category}</p>
    <p><strong>Description:</strong> {issue.description}</p>
    <p><strong>Impact:</strong> {issue.impact}</p>
    <p><strong>Remediation Steps:</strong></p>
    <ul>
""")
                for step in issue.remediation_steps:
                    html_parts.append(f"        <li>{step}</li>")
                html_parts.append("    </ul>")
                html_parts.append("</div>")
        
        # Recommendations section
        if report.recommendations:
            html_parts.append('<div class="recommendations">')
            html_parts.append("<h2>Recommendations</h2>")
            html_parts.append("<ul>")
            for rec in report.recommendations:
                html_parts.append(f"    <li>{rec}</li>")
            html_parts.append("</ul>")
            html_parts.append("</div>")
        
        # HTML footer
        html_parts.append("</body></html>")
        
        return "\n".join(html_parts)
    
    def _export_enhanced_text_report(self, report: DiagnosticReport, include_metadata: bool) -> str:
        """Export enhanced text report with better formatting."""
        lines = []
        
        # Header with ASCII art
        lines.extend([
            "=" * 80,
            "                        AURA DIAGNOSTIC REPORT",
            "=" * 80,
            f"Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Health Score: {report.overall_health_score:.1f}/100",
            f"Generation Time: {report.generation_time_ms:.1f}ms",
            ""
        ])
        
        # Health score visualization
        score = report.overall_health_score
        if score >= 90:
            status_icon = "🟢"
            status_text = "EXCELLENT"
        elif score >= 75:
            status_icon = "🟡"
            status_text = "GOOD"
        elif score >= 50:
            status_icon = "🟠"
            status_text = "NEEDS ATTENTION"
        else:
            status_icon = "🔴"
            status_text = "CRITICAL"
        
        lines.extend([
            f"System Status: {status_icon} {status_text}",
            ""
        ])
        
        # Issues summary
        if report.detected_issues:
            issue_counts = {}
            for issue in report.detected_issues:
                issue_counts[issue.severity] = issue_counts.get(issue.severity, 0) + 1
            
            lines.append("ISSUES SUMMARY:")
            lines.append("-" * 40)
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
                count = issue_counts.get(severity, 0)
                if count > 0:
                    icon = {'CRITICAL': '🚨', 'HIGH': '⚠️', 'MEDIUM': '⚡', 'LOW': 'ℹ️', 'INFO': '📝'}.get(severity, '•')
                    lines.append(f"{icon} {severity}: {count} issue{'s' if count != 1 else ''}")
            lines.append("")
        
        # Detailed issues
        if report.detected_issues:
            lines.append("DETAILED ISSUES:")
            lines.append("=" * 50)
            
            for i, issue in enumerate(report.detected_issues, 1):
                lines.extend([
                    f"{i}. [{issue.severity}] {issue.title}",
                    f"   Category: {issue.category}",
                    f"   Description: {issue.description}",
                    f"   Impact: {issue.impact}",
                    "   Remediation Steps:"
                ])
                
                for j, step in enumerate(issue.remediation_steps, 1):
                    lines.append(f"      {j}. {step}")
                
                if include_metadata and issue.metadata:
                    lines.append("   Metadata:")
                    for key, value in issue.metadata.items():
                        lines.append(f"      {key}: {value}")
                
                lines.append("")
        
        # Recommendations
        if report.recommendations:
            lines.append("RECOMMENDATIONS:")
            lines.append("=" * 50)
            for i, rec in enumerate(report.recommendations, 1):
                if rec.strip():  # Skip empty lines
                    if rec.startswith('   '):  # Sub-item
                        lines.append(rec)
                    else:
                        lines.append(f"{i}. {rec}")
            lines.append("")
        
        # Footer
        lines.extend([
            "=" * 80,
            "End of Report - Run diagnostics again after making changes",
            "=" * 80
        ])
        
        return "\n".join(lines)
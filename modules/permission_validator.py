"""
PermissionValidator for AURA - Comprehensive Accessibility Permission Management

This module provides comprehensive accessibility permission validation, detection,
and guidance for macOS systems using PyObjC frameworks.
"""

import logging
import time
import subprocess
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import threading

# Import macOS frameworks for permission detection
try:
    import objc
    from ApplicationServices import (
        AXUIElementCreateSystemWide,
        AXUIElementCopyAttributeValue,
        kAXFocusedApplicationAttribute,
        AXIsProcessTrusted,
        AXIsProcessTrustedWithOptions
    )
    from CoreFoundation import (
        kCFBooleanTrue,
        CFDictionaryCreateMutable,
        kCFTypeDictionaryKeyCallBacks,
        kCFTypeDictionaryValueCallBacks,
        CFDictionarySetValue,
        CFStringCreateWithCString,
        kCFStringEncodingUTF8
    )
    from AppKit import NSWorkspace, NSApplication
    ACCESSIBILITY_FRAMEWORKS_AVAILABLE = True
except ImportError as e:
    ACCESSIBILITY_FRAMEWORKS_AVAILABLE = False
    logging.warning(f"Accessibility frameworks not available: {e}")

# Import system information utilities
try:
    import platform
    import psutil
    SYSTEM_INFO_AVAILABLE = True
except ImportError:
    SYSTEM_INFO_AVAILABLE = False
    logging.warning("System information utilities not available")


@dataclass
class PermissionStatus:
    """Detailed accessibility permission status."""
    has_permissions: bool
    permission_level: str  # 'NONE', 'PARTIAL', 'FULL'
    missing_permissions: List[str]
    granted_permissions: List[str]
    can_request_permissions: bool
    system_version: str
    recommendations: List[str]
    timestamp: datetime
    check_duration_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    def is_sufficient_for_fast_path(self) -> bool:
        """Check if permissions are sufficient for fast path execution."""
        return self.has_permissions and self.permission_level in ['FULL', 'PARTIAL']
    
    def get_summary(self) -> str:
        """Get human-readable permission status summary."""
        if self.has_permissions:
            return f"✅ Accessibility permissions granted ({self.permission_level})"
        else:
            return f"❌ Accessibility permissions required ({len(self.missing_permissions)} issues)"


@dataclass
class PermissionCheckResult:
    """Result from a specific permission check operation."""
    check_name: str
    success: bool
    error_message: Optional[str]
    check_duration_ms: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)


class AccessibilityPermissionError(Exception):
    """Raised when accessibility permissions are insufficient."""
    def __init__(self, message: str, permission_status: PermissionStatus):
        super().__init__(message)
        self.permission_status = permission_status


class PermissionRequestError(Exception):
    """Raised when permission request fails."""
    def __init__(self, message: str, system_error: Optional[str] = None):
        super().__init__(message)
        self.system_error = system_error


class SystemCompatibilityError(Exception):
    """Raised when system is not compatible with permission operations."""
    def __init__(self, message: str, system_info: Dict[str, Any]):
        super().__init__(message)
        self.system_info = system_info


class PermissionValidator:
    """
    Validates and guides accessibility permission setup for macOS systems.
    
    Provides comprehensive permission checking, request functionality,
    and step-by-step guidance for users to grant accessibility permissions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the permission validator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Configuration settings
        self.permission_check_timeout = self.config.get('permission_check_timeout_ms', 5000)
        self.auto_request_permissions = self.config.get('auto_request_permissions', True)
        self.monitor_permission_changes_enabled = self.config.get('monitor_permission_changes', True)
        self.debug_logging = self.config.get('debug_logging', False)
        
        # Permission monitoring state
        self.last_permission_check = None
        self.permission_monitor_thread = None
        self.permission_change_callbacks = []
        self.monitoring_active = False
        self.monitor_interval = 30.0  # seconds
        
        # Permission check cache
        self.permission_cache = {}
        self.cache_ttl = 60.0  # seconds
        
        # System information
        self.system_info = self._gather_system_information()
        
        # Initialize logging
        if self.debug_logging:
            self.logger.setLevel(logging.DEBUG)
        
        self.logger.info("PermissionValidator initialized")
        if self.debug_logging:
            self.logger.debug(f"System info: {self.system_info}")
    
    def _gather_system_information(self) -> Dict[str, Any]:
        """Gather system information for permission validation."""
        system_info = {
            'platform': platform.system(),
            'version': platform.version(),
            'release': platform.release(),
            'machine': platform.machine(),
            'python_version': platform.python_version(),
            'frameworks_available': ACCESSIBILITY_FRAMEWORKS_AVAILABLE,
            'system_info_available': SYSTEM_INFO_AVAILABLE
        }
        
        try:
            if SYSTEM_INFO_AVAILABLE:
                system_info.update({
                    'cpu_count': psutil.cpu_count(),
                    'memory_total': psutil.virtual_memory().total,
                    'boot_time': psutil.boot_time()
                })
        except Exception as e:
            self.logger.debug(f"Could not gather extended system info: {e}")
        
        # macOS specific information
        if system_info['platform'] == 'Darwin':
            try:
                # Get macOS version details
                version_info = platform.mac_ver()
                system_info.update({
                    'macos_version': version_info[0],
                    'macos_version_info': version_info,
                    'is_macos': True
                })
                
                # Check if running on Apple Silicon
                if system_info['machine'] in ['arm64', 'aarch64']:
                    system_info['apple_silicon'] = True
                else:
                    system_info['apple_silicon'] = False
                    
            except Exception as e:
                self.logger.debug(f"Could not gather macOS specific info: {e}")
                system_info['is_macos'] = True  # Assume macOS if platform is Darwin
        else:
            system_info['is_macos'] = False
        
        return system_info
    
    def check_accessibility_permissions(self) -> PermissionStatus:
        """
        Check current accessibility permission status with comprehensive validation.
        
        Returns:
            PermissionStatus with detailed permission information
        """
        start_time = time.time()
        
        try:
            # Check cache first
            if self._is_permission_cache_valid():
                cached_status = self.permission_cache.get('status')
                if cached_status:
                    self.logger.debug("Returning cached permission status")
                    return cached_status
            
            # Perform comprehensive permission checks
            permission_checks = self._perform_permission_checks()
            
            # Analyze results and create status
            status = self._analyze_permission_results(permission_checks)
            
            # Calculate check duration
            check_duration = (time.time() - start_time) * 1000
            status.check_duration_ms = check_duration
            status.timestamp = datetime.now()
            
            # Cache the result
            self._cache_permission_status(status)
            
            # Log results
            self._log_permission_check_results(status, permission_checks)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            # Return a failed status
            return PermissionStatus(
                has_permissions=False,
                permission_level='NONE',
                missing_permissions=['permission_check_failed'],
                granted_permissions=[],
                can_request_permissions=False,
                system_version=self.system_info.get('macos_version', 'unknown'),
                recommendations=[f"Permission check failed: {str(e)}"],
                timestamp=datetime.now(),
                check_duration_ms=(time.time() - start_time) * 1000
            )
    
    def _perform_permission_checks(self) -> List[PermissionCheckResult]:
        """Perform individual permission checks."""
        checks = []
        
        # Check 1: Framework availability
        checks.append(self._check_framework_availability())
        
        # Check 2: Basic accessibility API access
        checks.append(self._check_basic_accessibility_access())
        
        # Check 3: System-wide element access
        checks.append(self._check_system_wide_element_access())
        
        # Check 4: Focused application access
        checks.append(self._check_focused_application_access())
        
        # Check 5: Process trust status
        checks.append(self._check_process_trust_status())
        
        # Check 6: System preferences accessibility
        checks.append(self._check_system_preferences_accessibility())
        
        return checks
    
    def _check_framework_availability(self) -> PermissionCheckResult:
        """Check if required frameworks are available."""
        start_time = time.time()
        
        try:
            if not ACCESSIBILITY_FRAMEWORKS_AVAILABLE:
                return PermissionCheckResult(
                    check_name="framework_availability",
                    success=False,
                    error_message="Accessibility frameworks not available",
                    check_duration_ms=(time.time() - start_time) * 1000,
                    metadata={
                        'frameworks_available': False,
                        'import_error': 'PyObjC frameworks not installed'
                    }
                )
            
            # Test framework functions
            test_results = {}
            
            # Test AXIsProcessTrusted
            try:
                AXIsProcessTrusted()
                test_results['AXIsProcessTrusted'] = True
            except Exception as e:
                test_results['AXIsProcessTrusted'] = False
                test_results['AXIsProcessTrusted_error'] = str(e)
            
            # Test AXUIElementCreateSystemWide
            try:
                system_wide = AXUIElementCreateSystemWide()
                test_results['AXUIElementCreateSystemWide'] = system_wide is not None
            except Exception as e:
                test_results['AXUIElementCreateSystemWide'] = False
                test_results['AXUIElementCreateSystemWide_error'] = str(e)
            
            success = all(test_results.get(key, False) for key in ['AXIsProcessTrusted', 'AXUIElementCreateSystemWide'])
            
            return PermissionCheckResult(
                check_name="framework_availability",
                success=success,
                error_message=None if success else "Some framework functions failed",
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata=test_results
            )
            
        except Exception as e:
            return PermissionCheckResult(
                check_name="framework_availability",
                success=False,
                error_message=f"Framework check failed: {str(e)}",
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata={'exception': str(e)}
            )
    
    def _check_basic_accessibility_access(self) -> PermissionCheckResult:
        """Check basic accessibility API access."""
        start_time = time.time()
        
        try:
            if not ACCESSIBILITY_FRAMEWORKS_AVAILABLE:
                return PermissionCheckResult(
                    check_name="basic_accessibility_access",
                    success=False,
                    error_message="Frameworks not available",
                    check_duration_ms=(time.time() - start_time) * 1000,
                    metadata={}
                )
            
            # Check if process is trusted
            is_trusted = AXIsProcessTrusted()
            
            return PermissionCheckResult(
                check_name="basic_accessibility_access",
                success=bool(is_trusted),
                error_message=None if is_trusted else "Process not trusted for accessibility",
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata={'is_trusted': bool(is_trusted)}
            )
            
        except Exception as e:
            return PermissionCheckResult(
                check_name="basic_accessibility_access",
                success=False,
                error_message=f"Basic access check failed: {str(e)}",
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata={'exception': str(e)}
            )
    
    def _check_system_wide_element_access(self) -> PermissionCheckResult:
        """Check system-wide element access."""
        start_time = time.time()
        
        try:
            if not ACCESSIBILITY_FRAMEWORKS_AVAILABLE:
                return PermissionCheckResult(
                    check_name="system_wide_element_access",
                    success=False,
                    error_message="Frameworks not available",
                    check_duration_ms=(time.time() - start_time) * 1000,
                    metadata={}
                )
            
            # Try to create system-wide element
            system_wide = AXUIElementCreateSystemWide()
            if system_wide is None:
                return PermissionCheckResult(
                    check_name="system_wide_element_access",
                    success=False,
                    error_message="Cannot create system-wide element",
                    check_duration_ms=(time.time() - start_time) * 1000,
                    metadata={'system_wide_element': None}
                )
            
            # Try to access system-wide attributes
            try:
                import objc
                error = objc.NULL
                focused_app = AXUIElementCopyAttributeValue(system_wide, kAXFocusedApplicationAttribute, error)
                has_focused_app = focused_app is not None
            except Exception as e:
                has_focused_app = False
                focused_app_error = str(e)
            else:
                focused_app_error = None
            
            return PermissionCheckResult(
                check_name="system_wide_element_access",
                success=has_focused_app,
                error_message=focused_app_error,
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata={
                    'system_wide_element': system_wide is not None,
                    'focused_app_access': has_focused_app,
                    'focused_app_error': focused_app_error
                }
            )
            
        except Exception as e:
            return PermissionCheckResult(
                check_name="system_wide_element_access",
                success=False,
                error_message=f"System-wide access check failed: {str(e)}",
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata={'exception': str(e)}
            )
    
    def _check_focused_application_access(self) -> PermissionCheckResult:
        """Check focused application access."""
        start_time = time.time()
        
        try:
            if not ACCESSIBILITY_FRAMEWORKS_AVAILABLE:
                return PermissionCheckResult(
                    check_name="focused_application_access",
                    success=False,
                    error_message="Frameworks not available",
                    check_duration_ms=(time.time() - start_time) * 1000,
                    metadata={}
                )
            
            # Get workspace for application information
            workspace = NSWorkspace.sharedWorkspace()
            if workspace is None:
                return PermissionCheckResult(
                    check_name="focused_application_access",
                    success=False,
                    error_message="Cannot access NSWorkspace",
                    check_duration_ms=(time.time() - start_time) * 1000,
                    metadata={'workspace': None}
                )
            
            # Get active application
            active_app = workspace.activeApplication()
            app_info = {}
            
            if active_app:
                app_info = {
                    'app_name': active_app.get('NSApplicationName', 'unknown'),
                    'bundle_id': active_app.get('NSApplicationBundleIdentifier', 'unknown'),
                    'pid': active_app.get('NSApplicationProcessIdentifier', -1)
                }
            
            # Try to access focused application via accessibility API
            system_wide = AXUIElementCreateSystemWide()
            if system_wide:
                try:
                    import objc
                    error = objc.NULL
                    focused_app = AXUIElementCopyAttributeValue(system_wide, kAXFocusedApplicationAttribute, error)
                    accessibility_access = focused_app is not None
                except Exception as e:
                    accessibility_access = False
                    accessibility_error = str(e)
                else:
                    accessibility_error = None
            else:
                accessibility_access = False
                accessibility_error = "No system-wide element"
            
            success = bool(active_app) and accessibility_access
            
            return PermissionCheckResult(
                check_name="focused_application_access",
                success=success,
                error_message=accessibility_error if not success else None,
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata={
                    'workspace_access': workspace is not None,
                    'active_app': app_info,
                    'accessibility_access': accessibility_access,
                    'accessibility_error': accessibility_error
                }
            )
            
        except Exception as e:
            return PermissionCheckResult(
                check_name="focused_application_access",
                success=False,
                error_message=f"Focused app access check failed: {str(e)}",
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata={'exception': str(e)}
            )
    
    def _check_process_trust_status(self) -> PermissionCheckResult:
        """Check detailed process trust status."""
        start_time = time.time()
        
        try:
            if not ACCESSIBILITY_FRAMEWORKS_AVAILABLE:
                return PermissionCheckResult(
                    check_name="process_trust_status",
                    success=False,
                    error_message="Frameworks not available",
                    check_duration_ms=(time.time() - start_time) * 1000,
                    metadata={}
                )
            
            # Check basic trust status
            is_trusted = AXIsProcessTrusted()
            
            # Check with prompt option (this tells us if we can request permissions)
            try:
                # Create options dictionary for permission request
                options = CFDictionaryCreateMutable(
                    None, 0,
                    kCFTypeDictionaryKeyCallBacks,
                    kCFTypeDictionaryValueCallBacks
                )
                
                # Add prompt option (but set to False to avoid showing dialog)
                prompt_key = CFStringCreateWithCString(None, "AXTrustedCheckOptionPrompt", kCFStringEncodingUTF8)
                CFDictionarySetValue(options, prompt_key, kCFBooleanTrue)
                
                # Check if we can request permissions
                can_request = AXIsProcessTrustedWithOptions(options)
                
            except Exception as e:
                can_request = False
                request_error = str(e)
            else:
                request_error = None
            
            return PermissionCheckResult(
                check_name="process_trust_status",
                success=bool(is_trusted),
                error_message=None if is_trusted else "Process not trusted",
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata={
                    'is_trusted': bool(is_trusted),
                    'can_request_permissions': bool(can_request),
                    'request_error': request_error
                }
            )
            
        except Exception as e:
            return PermissionCheckResult(
                check_name="process_trust_status",
                success=False,
                error_message=f"Process trust check failed: {str(e)}",
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata={'exception': str(e)}
            )
    
    def _check_system_preferences_accessibility(self) -> PermissionCheckResult:
        """Check if system preferences accessibility is properly configured."""
        start_time = time.time()
        
        try:
            # This is a heuristic check - we can't directly query system preferences
            # but we can infer from other checks
            
            metadata = {
                'system_version': self.system_info.get('macos_version', 'unknown'),
                'is_macos': self.system_info.get('is_macos', False),
                'apple_silicon': self.system_info.get('apple_silicon', False)
            }
            
            # On newer macOS versions, accessibility permissions are more strict
            macos_version = self.system_info.get('macos_version', '10.0')
            version_parts = macos_version.split('.')
            
            try:
                major_version = int(version_parts[0])
                minor_version = int(version_parts[1]) if len(version_parts) > 1 else 0
                
                # macOS 10.14+ requires explicit accessibility permissions
                requires_explicit_permissions = major_version >= 11 or (major_version == 10 and minor_version >= 14)
                
            except (ValueError, IndexError):
                requires_explicit_permissions = True  # Assume modern macOS
            
            metadata.update({
                'requires_explicit_permissions': requires_explicit_permissions,
                'macos_version_parsed': f"{major_version}.{minor_version}" if 'major_version' in locals() else 'unknown'
            })
            
            # Success is based on whether we expect explicit permissions to be required
            # This is more of an informational check
            success = True  # We can't actually fail this check
            
            return PermissionCheckResult(
                check_name="system_preferences_accessibility",
                success=success,
                error_message=None,
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata=metadata
            )
            
        except Exception as e:
            return PermissionCheckResult(
                check_name="system_preferences_accessibility",
                success=False,
                error_message=f"System preferences check failed: {str(e)}",
                check_duration_ms=(time.time() - start_time) * 1000,
                metadata={'exception': str(e)}
            )
    
    def _analyze_permission_results(self, checks: List[PermissionCheckResult]) -> PermissionStatus:
        """Analyze permission check results and create status."""
        
        # Categorize checks
        critical_checks = ['basic_accessibility_access', 'system_wide_element_access']
        important_checks = ['focused_application_access', 'process_trust_status']
        informational_checks = ['framework_availability', 'system_preferences_accessibility']
        
        # Count successes and failures
        critical_successes = sum(1 for check in checks if check.check_name in critical_checks and check.success)
        important_successes = sum(1 for check in checks if check.check_name in important_checks and check.success)
        total_critical = len([c for c in checks if c.check_name in critical_checks])
        total_important = len([c for c in checks if c.check_name in important_checks])
        
        # Determine permission level
        if critical_successes == total_critical and important_successes == total_important:
            permission_level = 'FULL'
            has_permissions = True
        elif critical_successes == total_critical:
            permission_level = 'PARTIAL'
            has_permissions = True
        elif critical_successes > 0:
            permission_level = 'PARTIAL'
            has_permissions = False  # Not sufficient for reliable operation
        else:
            permission_level = 'NONE'
            has_permissions = False
        
        # Collect missing and granted permissions
        missing_permissions = []
        granted_permissions = []
        
        for check in checks:
            if check.success:
                granted_permissions.append(check.check_name)
            else:
                missing_permissions.append(check.check_name)
        
        # Determine if we can request permissions
        can_request = False
        for check in checks:
            if check.check_name == 'process_trust_status':
                can_request = check.metadata.get('can_request_permissions', False)
                break
        
        # Generate recommendations
        recommendations = self._generate_recommendations(checks, permission_level)
        
        return PermissionStatus(
            has_permissions=has_permissions,
            permission_level=permission_level,
            missing_permissions=missing_permissions,
            granted_permissions=granted_permissions,
            can_request_permissions=can_request,
            system_version=self.system_info.get('macos_version', 'unknown'),
            recommendations=recommendations,
            timestamp=datetime.now(),
            check_duration_ms=0  # Will be set by caller
        )
    
    def _generate_recommendations(self, checks: List[PermissionCheckResult], permission_level: str) -> List[str]:
        """Generate actionable recommendations based on check results."""
        recommendations = []
        
        # Check for framework issues
        framework_check = next((c for c in checks if c.check_name == 'framework_availability'), None)
        if framework_check and not framework_check.success:
            recommendations.append("Install required PyObjC frameworks: pip install pyobjc-framework-AppKit pyobjc-framework-Accessibility")
        
        # Check for basic accessibility issues
        basic_check = next((c for c in checks if c.check_name == 'basic_accessibility_access'), None)
        if basic_check and not basic_check.success:
            recommendations.append("Grant accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility")
            recommendations.append("Add Terminal (or your Python IDE) to the accessibility permissions list")
        
        # Check for system-wide access issues
        system_check = next((c for c in checks if c.check_name == 'system_wide_element_access'), None)
        if system_check and not system_check.success:
            recommendations.append("Restart the application after granting accessibility permissions")
            recommendations.append("Ensure the application has full disk access if running on macOS 10.15+")
        
        # Check for focused app access issues
        focus_check = next((c for c in checks if c.check_name == 'focused_application_access'), None)
        if focus_check and not focus_check.success:
            recommendations.append("Verify that the application can access other applications' UI elements")
        
        # General recommendations based on permission level
        if permission_level == 'NONE':
            recommendations.append("Complete accessibility setup is required for AURA to function")
            recommendations.append("Follow the step-by-step permission guide")
        elif permission_level == 'PARTIAL':
            recommendations.append("Some accessibility features may not work reliably")
            recommendations.append("Consider granting full accessibility permissions for optimal performance")
        
        # macOS version specific recommendations
        macos_version = self.system_info.get('macos_version', '10.0')
        if macos_version.startswith('11.') or macos_version.startswith('12.') or macos_version.startswith('13.') or macos_version.startswith('14.'):
            recommendations.append("On macOS 11+, you may need to grant permissions multiple times")
            recommendations.append("Try restarting the application if permissions seem granted but don't work")
        
        return recommendations
    
    def guide_permission_setup(self) -> List[str]:
        """
        Provide step-by-step permission setup instructions.
        
        Returns:
            List of instructions for granting accessibility permissions
        """
        instructions = []
        
        # System-specific instructions
        if not self.system_info.get('is_macos', False):
            instructions.append("❌ AURA requires macOS for accessibility features")
            instructions.append("Current system is not macOS - accessibility features unavailable")
            return instructions
        
        # Check current status
        current_status = self.check_accessibility_permissions()
        
        if current_status.has_permissions and current_status.permission_level == 'FULL':
            instructions.append("✅ Accessibility permissions are already properly configured")
            return instructions
        
        # General setup instructions
        instructions.extend([
            "🔧 ACCESSIBILITY PERMISSION SETUP GUIDE",
            "=" * 50,
            "",
            "1. Open System Preferences (or System Settings on macOS 13+)",
            "   • Click the Apple menu → System Preferences",
            "   • Or press Cmd+Space and type 'System Preferences'",
            "",
            "2. Navigate to Privacy & Security settings",
            "   • Click 'Security & Privacy' (macOS 12 and earlier)",
            "   • Or click 'Privacy & Security' (macOS 13+)",
            "",
            "3. Go to Accessibility permissions",
            "   • Click 'Privacy' tab (if available)",
            "   • Select 'Accessibility' from the left sidebar",
            "",
            "4. Unlock settings (if locked)",
            "   • Click the lock icon in the bottom-left corner",
            "   • Enter your administrator password",
            "",
            "5. Add your application to the accessibility list",
        ])
        
        # Application-specific instructions
        python_executable = self._get_python_executable_info()
        if python_executable:
            instructions.extend([
                f"   • Click the '+' button to add an application",
                f"   • Navigate to and select: {python_executable['path']}",
                f"   • Or add your IDE/Terminal application if running from there",
                f"   • Ensure the checkbox next to the application is checked",
            ])
        else:
            instructions.extend([
                "   • Click the '+' button to add an application",
                "   • Add Terminal.app if running from Terminal",
                "   • Or add your Python IDE (PyCharm, VSCode, etc.)",
                "   • Ensure the checkbox next to the application is checked",
            ])
        
        instructions.extend([
            "",
            "6. Restart the application",
            "   • Close AURA completely",
            "   • Restart the application to apply new permissions",
            "",
            "7. Verify permissions",
            "   • Run AURA again",
            "   • Check that accessibility features work properly",
            ""
        ])
        
        # Troubleshooting section
        if current_status.permission_level in ['NONE', 'PARTIAL']:
            instructions.extend([
                "🔍 TROUBLESHOOTING TIPS",
                "=" * 30,
                "",
                "If permissions still don't work after following the steps above:",
                "",
                "• Remove and re-add the application in accessibility settings",
                "• Try adding both Terminal and your Python executable",
                "• Restart your Mac if permissions seem stuck",
                "• Check for macOS updates that might affect permissions",
                ""
            ])
        
        # Version-specific notes
        macos_version = self.system_info.get('macos_version', '10.0')
        if macos_version.startswith(('11.', '12.', '13.', '14.')):
            instructions.extend([
                "📝 MACOS 11+ SPECIFIC NOTES",
                "=" * 30,
                "",
                "• You may need to grant permissions multiple times",
                "• Some applications require 'Full Disk Access' in addition to Accessibility",
                "• Try running as administrator if normal permissions don't work",
                "• System may prompt for permissions during first use",
                ""
            ])
        
        return instructions
    
    def attempt_permission_request(self) -> bool:
        """
        Attempt to programmatically request accessibility permissions.
        
        Returns:
            True if permissions were granted, False otherwise
        """
        try:
            if not ACCESSIBILITY_FRAMEWORKS_AVAILABLE:
                raise PermissionRequestError("Accessibility frameworks not available")
            
            self.logger.info("Attempting to request accessibility permissions")
            
            # Create options dictionary for permission request
            options = CFDictionaryCreateMutable(
                None, 0,
                kCFTypeDictionaryKeyCallBacks,
                kCFTypeDictionaryValueCallBacks
            )
            
            # Add prompt option to show system dialog
            prompt_key = CFStringCreateWithCString(None, "AXTrustedCheckOptionPrompt", kCFStringEncodingUTF8)
            CFDictionarySetValue(options, prompt_key, kCFBooleanTrue)
            
            # Request permissions (this will show system dialog)
            result = AXIsProcessTrustedWithOptions(options)
            
            if result:
                self.logger.info("Accessibility permissions granted successfully")
                # Clear permission cache to force re-check
                self._clear_permission_cache()
                return True
            else:
                self.logger.warning("Accessibility permission request was denied or cancelled")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to request accessibility permissions: {e}")
            raise PermissionRequestError(f"Permission request failed: {str(e)}", str(e))
    
    def monitor_permission_changes(self) -> None:
        """Monitor for runtime permission changes and update capabilities."""
        if self.monitoring_active:
            self.logger.debug("Permission monitoring already active")
            return
        
        if not self.monitor_permission_changes_enabled:
            self.logger.debug("Permission monitoring disabled in configuration")
            return
        
        self.monitoring_active = True
        self.permission_monitor_thread = threading.Thread(
            target=self._permission_monitor_loop,
            daemon=True,
            name="permission_monitor"
        )
        self.permission_monitor_thread.start()
        self.logger.info("Started permission monitoring thread")
    
    def stop_permission_monitoring(self) -> None:
        """Stop permission monitoring."""
        self.monitoring_active = False
        if self.permission_monitor_thread and self.permission_monitor_thread.is_alive():
            self.permission_monitor_thread.join(timeout=5.0)
        self.logger.info("Stopped permission monitoring")
    
    def add_permission_change_callback(self, callback) -> None:
        """Add callback to be called when permissions change."""
        self.permission_change_callbacks.append(callback)
    
    def remove_permission_change_callback(self, callback) -> None:
        """Remove permission change callback."""
        if callback in self.permission_change_callbacks:
            self.permission_change_callbacks.remove(callback)
    
    def _permission_monitor_loop(self) -> None:
        """Main loop for permission monitoring."""
        last_status = None
        
        while self.monitoring_active:
            try:
                current_status = self.check_accessibility_permissions()
                
                # Check if status changed
                if last_status is None:
                    last_status = current_status
                elif self._has_permission_status_changed(last_status, current_status):
                    self.logger.info(f"Permission status changed: {last_status.permission_level} -> {current_status.permission_level}")
                    
                    # Notify callbacks
                    for callback in self.permission_change_callbacks:
                        try:
                            callback(last_status, current_status)
                        except Exception as e:
                            self.logger.error(f"Permission change callback failed: {e}")
                    
                    last_status = current_status
                
                # Sleep until next check
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"Permission monitoring error: {e}")
                time.sleep(self.monitor_interval)
    
    def _has_permission_status_changed(self, old_status: PermissionStatus, new_status: PermissionStatus) -> bool:
        """Check if permission status has meaningfully changed."""
        return (
            old_status.has_permissions != new_status.has_permissions or
            old_status.permission_level != new_status.permission_level or
            set(old_status.granted_permissions) != set(new_status.granted_permissions)
        )
    
    def _get_python_executable_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current Python executable."""
        try:
            import sys
            executable_path = sys.executable
            
            return {
                'path': executable_path,
                'version': sys.version,
                'executable': os.path.basename(executable_path)
            }
        except Exception as e:
            self.logger.debug(f"Could not get Python executable info: {e}")
            return None
    
    def _is_permission_cache_valid(self) -> bool:
        """Check if permission cache is still valid."""
        if not self.permission_cache:
            return False
        
        cache_time = self.permission_cache.get('timestamp', 0)
        return (time.time() - cache_time) < self.cache_ttl
    
    def _cache_permission_status(self, status: PermissionStatus) -> None:
        """Cache permission status."""
        self.permission_cache = {
            'status': status,
            'timestamp': time.time()
        }
    
    def _clear_permission_cache(self) -> None:
        """Clear permission cache."""
        self.permission_cache.clear()
    
    def _log_permission_check_results(self, status: PermissionStatus, checks: List[PermissionCheckResult]) -> None:
        """Log permission check results."""
        self.logger.info(f"Permission check completed: {status.get_summary()}")
        
        if self.debug_logging:
            self.logger.debug(f"Permission status: {status.to_dict()}")
            
            for check in checks:
                result_str = "✅ PASS" if check.success else "❌ FAIL"
                self.logger.debug(f"  {check.check_name}: {result_str} ({check.check_duration_ms:.1f}ms)")
                
                if check.error_message:
                    self.logger.debug(f"    Error: {check.error_message}")
                
                if check.metadata and self.debug_logging:
                    self.logger.debug(f"    Metadata: {check.metadata}")
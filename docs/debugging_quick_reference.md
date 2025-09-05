# AURA Debugging Quick Reference

Quick reference for AURA debugging commands, utilities, and common operations.

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Debug Commands](#debug-commands)
3. [Configuration Quick Reference](#configuration-quick-reference)
4. [Diagnostic Commands](#diagnostic-commands)
5. [Performance Monitoring](#performance-monitoring)
6. [Common Troubleshooting](#common-troubleshooting)
7. [Log Analysis](#log-analysis)

## Environment Setup

### Enable Debugging

```bash
# Set debug level
export AURA_DEBUG_LEVEL="DETAILED"  # BASIC, DETAILED, VERBOSE

# Enable debug mode
export AURA_DEBUG="true"

# Custom debug log file
export AURA_DEBUG_LOG_FILE="/path/to/debug.log"
```

### Quick Health Check

```bash
# Run comprehensive diagnostics
python -c "
from modules.diagnostic_tools import DiagnosticTools
report = DiagnosticTools().run_comprehensive_diagnostics()
print(f'Status: {report.overall_status}')
print(f'Success Rate: {report.success_rate:.1%}')
print(f'Issues: {len(report.detected_issues)}')
"
```

## Debug Commands

### Permission Validation

```bash
# Check accessibility permissions
python -c "
from modules.permission_validator import PermissionValidator
status = PermissionValidator().check_accessibility_permissions()
print(f'Permissions: {\"✅\" if status.has_permissions else \"❌\"}')
print(f'Level: {status.permission_level}')
"

# Get permission setup guide
python -c "
from modules.permission_validator import PermissionValidator
guide = PermissionValidator().guide_permission_setup()
for i, step in enumerate(guide, 1):
    print(f'{i}. {step}')
"
```

### Accessibility Tree Inspection

```bash
# Dump accessibility tree for current app
python -c "
from modules.accessibility_debugger import AccessibilityDebugger
tree = AccessibilityDebugger({}).dump_accessibility_tree()
print(f'Elements: {tree.total_elements}')
print(f'Clickable: {len(tree.clickable_elements)}')
"

# Dump tree for specific app
python debug_cli.py --dump-tree --app "Safari"

# Show clickable elements only
python -c "
from modules.accessibility_debugger import AccessibilityDebugger
tree = AccessibilityDebugger({}).dump_accessibility_tree('Safari')
for elem in tree.clickable_elements[:10]:
    print(f'  \"{elem.get(\"AXTitle\", \"No title\")}\" ({elem.get(\"AXRole\", \"Unknown\")})')
"
```

### Element Detection Testing

```bash
# Test element detection
python debug_cli.py --test-element "Sign In" --app "Safari"

# Test with different strategies
python debug_cli.py --test-element "Sign In" --app "Safari" --strategy "fuzzy_match"

# Test with custom threshold
python debug_cli.py --test-element "Sign In" --app "Safari" --threshold 0.5
```

### Interactive Debugging

```bash
# Start interactive debugging session
python debug_interactive.py

# Step-by-step debugging
python debug_step_by_step.py --command "Click on Sign In"
```

## Configuration Quick Reference

### Debug Levels

```python
# Basic debugging (minimal overhead)
DEBUG_LEVEL = "BASIC"

# Detailed debugging (moderate overhead)
DEBUG_LEVEL = "DETAILED"

# Verbose debugging (high overhead, maximum detail)
DEBUG_LEVEL = "VERBOSE"
```

### Common Configuration Patterns

#### Development Setup

```python
DEBUG_LEVEL = "DETAILED"
DEBUG_LOG_TO_CONSOLE = True
DEBUG_LOG_TO_FILE = True
TREE_INSPECTION_ENABLED = True
ELEMENT_ANALYSIS_ENABLED = True
INTERACTIVE_DEBUGGING_ENABLED = True
```

#### Production Setup

```python
DEBUG_LEVEL = "BASIC"
DEBUG_LOG_TO_CONSOLE = False
DEBUG_LOG_TO_FILE = True
DEBUG_SANITIZE_SENSITIVE_DATA = True
DIAGNOSTIC_AUTO_RUN = False
```

#### Performance Optimized

```python
DEBUG_LEVEL = "BASIC"
TREE_DUMP_CACHE_ENABLED = True
APPLICATION_STRATEGY_CACHING = True
ELEMENT_SEARCH_TIMEOUT = 1.0
DEBUG_PERFORMANCE_HISTORY_SIZE = 100
```

#### Troubleshooting Setup

```python
DEBUG_LEVEL = "VERBOSE"
TREE_INSPECTION_ENABLED = True
ELEMENT_ANALYSIS_ENABLED = True
FUZZY_MATCH_ANALYSIS_ENABLED = True
ERROR_RECOVERY_ENABLED = True
DIAGNOSTIC_TOOLS_ENABLED = True
```

### Key Configuration Variables

| Variable                        | Default   | Description                      |
| ------------------------------- | --------- | -------------------------------- |
| `DEBUG_LEVEL`                   | `"BASIC"` | Debug verbosity level            |
| `SIMILARITY_SCORE_THRESHOLD`    | `0.6`     | Fuzzy matching threshold         |
| `ELEMENT_SEARCH_TIMEOUT`        | `2.0`     | Element search timeout (seconds) |
| `TREE_DUMP_MAX_DEPTH`           | `10`      | Max tree traversal depth         |
| `ERROR_RECOVERY_MAX_RETRIES`    | `3`       | Max retry attempts               |
| `PERMISSION_VALIDATION_ENABLED` | `True`    | Enable permission checking       |

## Diagnostic Commands

### System Health

```bash
# Quick health check
python -c "
from modules.diagnostic_tools import DiagnosticTools
report = DiagnosticTools().run_comprehensive_diagnostics()
print('=== SYSTEM HEALTH ===')
print(f'Overall: {report.overall_status}')
print(f'Success Rate: {report.success_rate:.1%}')
for issue in report.detected_issues[:3]:
    print(f'Issue: {issue[\"description\"]}')
"

# Detailed diagnostic report
python demo_diagnostic_tools.py

# Export diagnostic report
python -c "
from modules.diagnostic_tools import DiagnosticTools
report = DiagnosticTools().run_comprehensive_diagnostics()
with open('diagnostic_report.json', 'w') as f:
    f.write(report.export_report('json'))
print('Report saved to diagnostic_report.json')
"
```

### Permission Diagnostics

```bash
# Check all permission types
python -c "
from modules.permission_validator import PermissionValidator
validator = PermissionValidator()
status = validator.check_accessibility_permissions()
print('=== PERMISSION STATUS ===')
print(f'Has Permissions: {status.has_permissions}')
print(f'Level: {status.permission_level}')
print(f'Missing: {status.missing_permissions}')
print(f'Granted: {status.granted_permissions}')
"
```

### Application Diagnostics

```bash
# Check application detection
python -c "
from modules.application_detector import ApplicationDetector
detector = ApplicationDetector()
app_type = detector.detect_application_type('Safari')
print(f'App Type: {app_type}')
strategy = detector.get_detection_strategy(app_type)
print(f'Strategy: {strategy}')
"

# Test application accessibility
python debug_cli.py --check-app "Safari"
```

## Performance Monitoring

### Real-time Performance

```bash
# Start performance monitoring
python demo_performance_monitoring.py

# Get performance summary
python -c "
from modules.fast_path_performance_monitor import FastPathPerformanceMonitor
monitor = FastPathPerformanceMonitor({})
summary = monitor.get_performance_summary()
print(f'Success Rate: {summary[\"success_rate\"]:.1%}')
print(f'Avg Time: {summary[\"average_execution_time\"]:.2f}s')
"
```

### Performance Analysis

```bash
# Analyze recent performance
python -c "
from modules.performance_reporting_system import PerformanceReportingSystem
reporter = PerformanceReportingSystem({})
report = reporter.generate_performance_report()
print(report.get_summary())
"

# Check for performance degradation
python -c "
from modules.fast_path_performance_monitor import FastPathPerformanceMonitor
monitor = FastPathPerformanceMonitor({})
if monitor.is_performance_degraded():
    print('⚠️  Performance degradation detected')
    print('Recommendations:', monitor.get_performance_recommendations())
else:
    print('✅ Performance is normal')
"
```

## Common Troubleshooting

### Quick Fixes

```bash
# Fix permission issues
python -c "
from modules.permission_validator import PermissionValidator
validator = PermissionValidator()
if not validator.check_accessibility_permissions().has_permissions:
    print('❌ Permissions missing')
    for step in validator.guide_permission_setup():
        print(f'  - {step}')
else:
    print('✅ Permissions OK')
"

# Clear caches
python -c "
import os
if os.path.exists('aura_debug.log'):
    os.remove('aura_debug.log')
    print('Debug log cleared')
# Clear other caches as needed
"

# Reset configuration to defaults
python -c "
import config
defaults = config.get_debugging_config_defaults()
print('Default configuration:')
for key, value in defaults.items():
    print(f'  {key}: {value}')
"
```

### Element Detection Issues

```bash
# Find available elements
python -c "
from modules.accessibility_debugger import AccessibilityDebugger
tree = AccessibilityDebugger({}).dump_accessibility_tree('YourApp')
print('Available clickable elements:')
for elem in tree.clickable_elements[:5]:
    print(f'  \"{elem.get(\"AXTitle\", \"No title\")}\"')
"

# Test fuzzy matching
python -c "
from modules.accessibility_debugger import AccessibilityDebugger
debugger = AccessibilityDebugger({})
analysis = debugger.analyze_element_detection_failure('Click on Sign In', 'Sign In')
print('Closest matches:')
for match in analysis.closest_matches[:3]:
    print(f'  \"{match[\"text\"]}\" (score: {match[\"score\"]:.2f})')
"
```

### Performance Issues

```bash
# Check for slow operations
grep -i "timeout\|slow" aura_debug.log | tail -5

# Monitor memory usage
python -c "
import psutil, os
process = psutil.Process(os.getpid())
memory_mb = process.memory_info().rss / 1024 / 1024
print(f'Memory usage: {memory_mb:.1f} MB')
"

# Optimize configuration for speed
python -c "
print('Speed optimization settings:')
print('ELEMENT_SEARCH_TIMEOUT = 1.0')
print('TREE_DUMP_CACHE_ENABLED = True')
print('DEBUG_LEVEL = \"BASIC\"')
print('TREE_INSPECTION_ENABLED = False')
"
```

## Log Analysis

### View Recent Logs

```bash
# View last 20 debug entries
tail -20 aura_debug.log

# Follow debug log in real-time
tail -f aura_debug.log

# View only errors
grep -i "error\|fail" aura_debug.log | tail -10

# View performance warnings
grep -i "performance\|slow\|timeout" aura_debug.log | tail -10
```

### Search Logs

```bash
# Search for specific element
grep -i "sign in" aura_debug.log | tail -5

# Search for permission issues
grep -i "permission\|denied" aura_debug.log

# Search for application-specific issues
grep -i "safari\|chrome" aura_debug.log | tail -10

# Search for fuzzy matching results
grep -i "fuzzy\|similarity\|score" aura_debug.log | tail -10
```

### Log Statistics

```bash
# Count success vs failures
echo "Successes: $(grep -c "success\|completed" aura_debug.log)"
echo "Failures: $(grep -c "error\|fail" aura_debug.log)"

# Count by debug category
echo "Accessibility: $(grep -c "\[accessibility\]" aura_debug.log)"
echo "Element Search: $(grep -c "\[element_search\]" aura_debug.log)"
echo "Performance: $(grep -c "\[performance\]" aura_debug.log)"

# Recent activity summary
echo "=== LAST HOUR ACTIVITY ==="
grep "$(date -v-1H '+%Y-%m-%d %H')" aura_debug.log | wc -l | xargs echo "Log entries:"
```

### Log Cleanup

```bash
# Archive old logs
mv aura_debug.log "aura_debug_$(date +%Y%m%d).log"

# Keep only recent entries
tail -1000 aura_debug.log > aura_debug_recent.log
mv aura_debug_recent.log aura_debug.log

# Remove very old logs
find . -name "aura_debug_*.log" -mtime +30 -delete
```

## Validation Commands

### Configuration Validation

```bash
# Validate current configuration
python -c "
import config
is_valid, errors, warnings = config.validate_debugging_config()
print(f'Valid: {is_valid}')
if errors:
    print('Errors:')
    for error in errors: print(f'  - {error}')
if warnings:
    print('Warnings:')
    for warning in warnings: print(f'  - {warning}')
"

# Get configuration summary
python -c "
import config, json
summary = config.get_config_summary()
print(json.dumps(summary['debugging'], indent=2))
"
```

### System Validation

```bash
# Validate Python environment
python -c "
import sys
print(f'Python: {sys.version}')
print(f'Executable: {sys.executable}')
"

# Validate dependencies
python -c "
try:
    import pyobjc
    print('✅ PyObjC available')
except ImportError:
    print('❌ PyObjC missing')

try:
    from ApplicationServices import AXIsProcessTrusted
    print('✅ Accessibility APIs available')
except ImportError:
    print('❌ Accessibility APIs missing')
"

# Validate AURA modules
python -c "
modules = ['accessibility', 'permission_validator', 'diagnostic_tools']
for module in modules:
    try:
        exec(f'from modules import {module}')
        print(f'✅ {module}')
    except ImportError as e:
        print(f'❌ {module}: {e}')
"
```

## Emergency Commands

### Reset Everything

```bash
# Reset to safe defaults
export AURA_DEBUG_LEVEL="BASIC"
export AURA_DEBUG="false"

# Clear all caches and logs
rm -f aura_debug.log*
rm -f diagnostic_report.*

# Restart with minimal debugging
python main.py
```

### Minimal Debug Mode

```bash
# Run with absolute minimum debugging
python -c "
import config
config.DEBUG_LEVEL = 'BASIC'
config.DEBUG_LOG_TO_CONSOLE = False
config.TREE_INSPECTION_ENABLED = False
config.ELEMENT_ANALYSIS_ENABLED = False
config.DIAGNOSTIC_TOOLS_ENABLED = False
print('Minimal debug mode configured')
"
```

### Get Help Information

```bash
# Show all available debug commands
python debug_cli.py --help

# Show interactive debugging help
python debug_interactive.py --help

# Show diagnostic tools help
python demo_diagnostic_tools.py --help
```

This quick reference provides immediate access to the most commonly used debugging commands and utilities in AURA. Keep this handy for rapid troubleshooting and system analysis.

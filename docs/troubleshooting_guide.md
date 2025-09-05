# AURA Troubleshooting Guide

This guide provides solutions to common issues encountered when using AURA's accessibility debugging features.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Permission Issues](#permission-issues)
3. [Element Detection Issues](#element-detection-issues)
4. [Performance Issues](#performance-issues)
5. [Application-Specific Issues](#application-specific-issues)
6. [Configuration Issues](#configuration-issues)
7. [System Issues](#system-issues)
8. [Advanced Troubleshooting](#advanced-troubleshooting)

## Quick Diagnostics

### Run Comprehensive Health Check

```bash
# Quick system health check
python -c "
from modules.diagnostic_tools import DiagnosticTools
diagnostics = DiagnosticTools()
report = diagnostics.run_comprehensive_diagnostics()
print('=== AURA HEALTH CHECK ===')
print(f'Overall Health: {\"GOOD\" if report.success_rate > 0.8 else \"NEEDS ATTENTION\"}')
print(f'Success Rate: {report.success_rate:.1%}')
print(f'Avg Response Time: {report.average_response_time:.2f}s')
print(f'Issues Found: {len(report.detected_issues)}')
if report.detected_issues:
    print('\\nTop Issues:')
    for issue in report.detected_issues[:3]:
        print(f'  - {issue[\"description\"]}')
print('\\nRecommendations:')
for rec in report.recommendations[:3]:
    print(f'  - {rec}')
"
```

### Check Configuration Validity

```bash
# Validate current configuration
python -c "
import config
is_valid, errors, warnings = config.validate_debugging_config()
print('Configuration Status:', 'VALID' if is_valid else 'INVALID')
if errors:
    print('Errors:')
    for error in errors:
        print(f'  ❌ {error}')
if warnings:
    print('Warnings:')
    for warning in warnings:
        print(f'  ⚠️  {warning}')
"
```

## Permission Issues

### Issue: "Permission denied accessing accessibility API"

**Symptoms**:

- Fast path always fails
- Error messages about permission denied
- No accessibility elements found

**Diagnosis**:

```bash
python -c "
from modules.permission_validator import PermissionValidator
validator = PermissionValidator()
status = validator.check_accessibility_permissions()
print('Has Permissions:', status.has_permissions)
print('Permission Level:', status.permission_level)
print('Missing:', status.missing_permissions)
"
```

**Solutions**:

1. **Grant Accessibility Permissions**:

   - Open System Preferences → Security & Privacy → Privacy → Accessibility
   - Click the lock icon and enter your password
   - Find your terminal application (Terminal, iTerm2, etc.) or Python interpreter
   - Check the box to enable accessibility access
   - Restart AURA

2. **Verify Python Interpreter Path**:

   ```bash
   which python  # Note the path
   # Add this exact path to accessibility permissions
   ```

3. **Use Permission Validator**:
   ```bash
   python -c "
   from modules.permission_validator import PermissionValidator
   validator = PermissionValidator()
   if not validator.check_accessibility_permissions().has_permissions:
       print('Setting up permissions...')
       instructions = validator.guide_permission_setup()
       for i, instruction in enumerate(instructions, 1):
           print(f'{i}. {instruction}')
   "
   ```

### Issue: "Permissions granted but still failing"

**Symptoms**:

- Accessibility permissions appear to be granted
- Still getting permission errors
- Intermittent permission failures

**Solutions**:

1. **Check Full Disk Access** (macOS Catalina+):

   - System Preferences → Security & Privacy → Privacy → Full Disk Access
   - Add your terminal application

2. **Restart Accessibility Services**:

   ```bash
   sudo launchctl unload /System/Library/LaunchAgents/com.apple.accessibility.AXVisualSupportAgent.plist
   sudo launchctl load /System/Library/LaunchAgents/com.apple.accessibility.AXVisualSupportAgent.plist
   ```

3. **Check for Multiple Python Installations**:

   ```bash
   # Check all Python paths
   which -a python
   which -a python3

   # Ensure the correct one has permissions
   python -c "import sys; print(sys.executable)"
   ```

## Element Detection Issues

### Issue: "Element not found" despite element being visible

**Symptoms**:

- Element is clearly visible on screen
- Fast path reports "element_not_found"
- Vision fallback works correctly

**Diagnosis**:

```bash
# Check what elements are actually available
python debug_cli.py --dump-tree --app "YourAppName"

# Test specific element detection
python debug_cli.py --test-element "Your Target Text" --app "YourAppName"
```

**Solutions**:

1. **Check Exact Text Match**:

   ```bash
   # See available clickable elements
   python -c "
   from modules.accessibility_debugger import AccessibilityDebugger
   debugger = AccessibilityDebugger({})
   tree = debugger.dump_accessibility_tree()
   print('Available clickable elements:')
   for elem in tree.clickable_elements[:10]:
       title = elem.get('AXTitle', 'No title')
       role = elem.get('AXRole', 'Unknown')
       print(f'  \"{title}\" ({role})')
   "
   ```

2. **Adjust Fuzzy Matching**:

   ```python
   # In config.py - Lower threshold for more matches
   SIMILARITY_SCORE_THRESHOLD = 0.4

   # Enable more search strategies
   ELEMENT_SEARCH_STRATEGIES = [
       "exact_match",
       "fuzzy_match",
       "partial_match",
       "role_based",
       "attribute_based"
   ]
   ```

3. **Check Element Attributes**:
   ```bash
   python -c "
   from modules.accessibility_debugger import AccessibilityDebugger
   debugger = AccessibilityDebugger({})
   tree = debugger.dump_accessibility_tree()
   # Look for elements with different attributes
   for elem in tree.clickable_elements:
       if 'sign' in str(elem.get('AXTitle', '')).lower():
           print('Found element:', elem)
   "
   ```

### Issue: "Enhanced role detection failed"

**Symptoms**:

- Message: "Enhanced role detection failed, falling back to button-only detection"
- Inconsistent element detection
- Some elements found, others not

**Solutions**:

1. **Enable Application-Specific Detection**:

   ```python
   # In config.py
   APPLICATION_DETECTION_ENABLED = True
   BROWSER_SPECIFIC_HANDLING = True  # For web apps
   NATIVE_APP_OPTIMIZATION = True   # For native apps
   ```

2. **Expand Clickable Roles**:

   ```python
   # In config.py - Add more element types
   CLICKABLE_ROLES = [
       "AXButton", "AXLink", "AXMenuItem",
       "AXCheckBox", "AXRadioButton",
       "AXTextField", "AXStaticText",  # Add these
       "AXImage", "AXGroup"           # And these
   ]
   ```

3. **Check Application Type Detection**:
   ```bash
   python -c "
   from modules.application_detector import ApplicationDetector
   detector = ApplicationDetector()
   app_type = detector.detect_application_type('YourAppName')
   print(f'Detected app type: {app_type}')
   strategy = detector.get_detection_strategy(app_type)
   print(f'Using strategy: {strategy}')
   "
   ```

### Issue: "Fuzzy matching produces low scores"

**Symptoms**:

- Debug logs show low similarity scores (< 0.6)
- Elements exist but aren't matched
- Exact text works, similar text doesn't

**Solutions**:

1. **Analyze Text Differences**:

   ```bash
   python -c "
   from modules.accessibility_debugger import AccessibilityDebugger
   debugger = AccessibilityDebugger({})
   analysis = debugger.analyze_element_detection_failure(
       'Click on Sign In', 'Sign In'
   )
   print('Closest matches:')
   for match in analysis.closest_matches:
       print(f'  \"{match[\"text\"]}\" (score: {match[\"score\"]:.2f})')
   "
   ```

2. **Adjust Fuzzy Matching Parameters**:

   ```python
   # In config.py
   SIMILARITY_SCORE_THRESHOLD = 0.3  # Much lower threshold
   FUZZY_MATCHING_TIMEOUT = 500      # More time for matching
   ```

3. **Enable Detailed Fuzzy Analysis**:
   ```python
   # In config.py
   FUZZY_MATCH_ANALYSIS_ENABLED = True
   LOG_FUZZY_MATCH_SCORES = True
   DEBUG_CATEGORIES["fuzzy_matching"] = True
   ```

## Performance Issues

### Issue: "Fast path is too slow"

**Symptoms**:

- Fast path takes > 3 seconds
- Performance warnings in logs
- Success rate is good but speed is poor

**Diagnosis**:

```bash
python demo_performance_monitoring.py
# Look for slow operations and bottlenecks
```

**Solutions**:

1. **Optimize Timeouts**:

   ```python
   # In config.py - Reduce timeouts
   ELEMENT_SEARCH_TIMEOUT = 1.0      # Faster search
   FAST_PATH_TIMEOUT = 1500          # Overall timeout
   ATTRIBUTE_CHECK_TIMEOUT = 200     # Faster attribute checks
   ```

2. **Enable Caching**:

   ```python
   # In config.py
   TREE_DUMP_CACHE_ENABLED = True
   TREE_DUMP_CACHE_TTL = 60          # Cache for 1 minute
   APPLICATION_STRATEGY_CACHING = True
   APPLICATION_STRATEGY_CACHE_TTL = 600  # Cache for 10 minutes
   ```

3. **Reduce Tree Inspection Depth**:
   ```python
   # In config.py
   TREE_DUMP_MAX_DEPTH = 5           # Shallower inspection
   TREE_DUMP_INCLUDE_HIDDEN = False  # Skip hidden elements
   ```

### Issue: "High memory usage during debugging"

**Symptoms**:

- AURA consuming excessive RAM
- System becomes slow during debugging
- Memory usage grows over time

**Solutions**:

1. **Reduce Debug History**:

   ```python
   # In config.py
   DEBUG_PERFORMANCE_HISTORY_SIZE = 50    # Smaller history
   PERFORMANCE_HISTORY_SIZE = 50          # Smaller performance history
   ```

2. **Disable Memory-Intensive Features**:

   ```python
   # In config.py
   TREE_DUMP_CACHE_ENABLED = False       # Disable caching
   INTERACTIVE_SESSION_RECORDING = False  # Disable recording
   DEBUG_LEVEL = "BASIC"                  # Less detailed logging
   ```

3. **Enable Garbage Collection**:
   ```python
   # Add to your debugging script
   import gc
   gc.collect()  # Force garbage collection periodically
   ```

### Issue: "Debug logs growing too large"

**Symptoms**:

- Debug log files consuming disk space
- Log rotation not working
- Difficulty finding recent entries

**Solutions**:

1. **Configure Log Rotation**:

   ```python
   # In config.py
   DEBUG_LOG_MAX_SIZE = 5 * 1024 * 1024  # 5MB max
   DEBUG_LOG_BACKUP_COUNT = 2            # Keep 2 backups
   ```

2. **Reduce Logging Verbosity**:

   ```python
   # In config.py
   DEBUG_LEVEL = "BASIC"                 # Less verbose
   DEBUG_LOG_TO_CONSOLE = False          # Console only when needed

   # Disable verbose categories
   DEBUG_CATEGORIES = {
       "accessibility": True,
       "permissions": True,
       "element_search": True,
       "performance": True,
       "error_recovery": False,          # Disable
       "application_detection": False,   # Disable
       "fuzzy_matching": False,          # Disable
       "tree_inspection": False,         # Disable
       "failure_analysis": True,
       "diagnostic_tools": True
   }
   ```

3. **Clean Up Old Logs**:

   ```bash
   # Remove old debug logs
   find . -name "aura_debug.log.*" -mtime +7 -delete

   # Truncate current log if too large
   tail -1000 aura_debug.log > aura_debug.log.tmp
   mv aura_debug.log.tmp aura_debug.log
   ```

## Application-Specific Issues

### Issue: "Safari/Chrome elements not detected"

**Symptoms**:

- Web browser elements not found
- Works in some websites, not others
- Inconsistent behavior across tabs

**Solutions**:

1. **Enable Browser-Specific Handling**:

   ```python
   # In config.py
   BROWSER_SPECIFIC_HANDLING = True
   WEB_APP_DETECTION = True
   ```

2. **Check Browser Accessibility Settings**:

   - **Safari**: Develop → Accessibility → Enable accessibility for assistive devices
   - **Chrome**: chrome://settings/accessibility → Enable accessibility features

3. **Test Browser Accessibility**:

   ```bash
   python test_browser_accessibility.py
   ```

4. **Use Browser-Specific Strategies**:
   ```python
   # In config.py
   ELEMENT_SEARCH_STRATEGIES = [
       "exact_match",
       "fuzzy_match",
       "partial_match",
       "role_based",
       "attribute_based"
   ]
   ```

### Issue: "Native macOS apps not working"

**Symptoms**:

- System apps (Finder, Mail, etc.) not responding
- Native app elements not detected
- Works with some apps, not others

**Solutions**:

1. **Enable Native App Optimization**:

   ```python
   # In config.py
   NATIVE_APP_OPTIMIZATION = True
   APPLICATION_DETECTION_ENABLED = True
   ```

2. **Check App-Specific Permissions**:

   ```bash
   # Some apps require additional permissions
   python -c "
   from modules.permission_validator import PermissionValidator
   validator = PermissionValidator()
   # Check if specific app needs permissions
   "
   ```

3. **Test with System Apps**:
   ```bash
   python debug_cli.py --test-element "Close" --app "Finder"
   ```

### Issue: "Electron apps not supported"

**Symptoms**:

- Electron-based apps (VS Code, Slack, etc.) not working
- Elements appear in tree but can't be clicked
- Inconsistent accessibility support

**Solutions**:

1. **Enable Electron App Detection**:

   ```python
   # Add to application detector
   ELECTRON_APP_HANDLING = True
   ```

2. **Check Electron Accessibility**:

   - Many Electron apps have accessibility settings
   - Look for "Enable screen reader support" or similar options

3. **Use Alternative Strategies**:
   ```python
   # In config.py - Try different approaches
   ELEMENT_SEARCH_STRATEGIES = [
       "attribute_based",  # Try this first for Electron
       "role_based",
       "fuzzy_match",
       "exact_match"
   ]
   ```

## Configuration Issues

### Issue: "Invalid configuration values"

**Symptoms**:

- Configuration validation errors
- AURA fails to start
- Unexpected behavior

**Diagnosis**:

```bash
python -c "
import config
is_valid, errors, warnings = config.validate_debugging_config()
if not is_valid:
    print('Configuration Errors:')
    for error in errors:
        print(f'  - {error}')
if warnings:
    print('Configuration Warnings:')
    for warning in warnings:
        print(f'  - {warning}')
"
```

**Solutions**:

1. **Reset to Defaults**:

   ```python
   # Get default values
   import config
   defaults = config.get_debugging_config_defaults()

   # Apply defaults to config.py
   DEBUG_LEVEL = defaults['debug_level']
   PERMISSION_VALIDATION_ENABLED = defaults['permission_validation_enabled']
   # ... etc
   ```

2. **Fix Common Configuration Errors**:

   ```python
   # Ensure valid debug level
   DEBUG_LEVEL = "BASIC"  # Must be BASIC, DETAILED, or VERBOSE

   # Ensure valid thresholds
   SIMILARITY_SCORE_THRESHOLD = 0.6  # Must be 0.0 to 1.0

   # Ensure positive timeouts
   ELEMENT_SEARCH_TIMEOUT = 2.0  # Must be > 0
   ```

### Issue: "Environment variables not working"

**Symptoms**:

- Environment variables ignored
- Configuration not updating
- Inconsistent behavior

**Solutions**:

1. **Check Environment Variable Names**:

   ```bash
   # Correct variable names
   export AURA_DEBUG_LEVEL="DETAILED"
   export AURA_DEBUG="true"

   # Verify they're set
   echo $AURA_DEBUG_LEVEL
   ```

2. **Restart Python Process**:

   ```bash
   # Environment variables are read at import time
   # Restart AURA after setting variables
   ```

3. **Check Variable Precedence**:
   ```python
   # Environment variables override config.py values
   import os
   print("Environment DEBUG_LEVEL:", os.getenv("AURA_DEBUG_LEVEL"))
   print("Config DEBUG_LEVEL:", config.DEBUG_LEVEL)
   ```

## System Issues

### Issue: "macOS version compatibility"

**Symptoms**:

- Accessibility APIs not working
- Permission dialogs not appearing
- System-specific errors

**Solutions**:

1. **Check macOS Version**:

   ```bash
   sw_vers
   # AURA requires macOS 10.14+ for full accessibility support
   ```

2. **Update System**:

   - Update to latest macOS version if possible
   - Some accessibility features require newer versions

3. **Use Compatibility Mode**:
   ```python
   # In config.py - For older systems
   NATIVE_APP_OPTIMIZATION = False
   BROWSER_SPECIFIC_HANDLING = False
   # Use more basic detection methods
   ```

### Issue: "Python version compatibility"

**Symptoms**:

- Import errors
- Syntax errors
- Missing features

**Solutions**:

1. **Check Python Version**:

   ```bash
   python --version  # Should be 3.11+
   ```

2. **Update Python**:

   ```bash
   # Using conda
   conda update python

   # Or create new environment
   conda create --name aura python=3.11 -y
   conda activate aura
   ```

### Issue: "Dependency conflicts"

**Symptoms**:

- Import errors for debugging modules
- Version conflicts
- Missing dependencies

**Solutions**:

1. **Check Dependencies**:

   ```bash
   pip list | grep -E "(pyobjc|accessibility)"
   ```

2. **Reinstall Dependencies**:

   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Clean Install**:
   ```bash
   # Remove and recreate environment
   conda deactivate
   conda remove --name aura --all
   conda create --name aura python=3.11 -y
   conda activate aura
   pip install -r requirements.txt
   ```

## Advanced Troubleshooting

### Debug with Python Debugger

```python
# Add to your debugging script
import pdb

# Set breakpoint before problematic code
pdb.set_trace()

# Or use ipdb for better interface
import ipdb
ipdb.set_trace()
```

### Profile Performance Issues

```python
# Profile slow operations
import cProfile
import pstats

def profile_accessibility():
    from modules.accessibility import AccessibilityModule
    module = AccessibilityModule()
    # Your problematic code here

if __name__ == "__main__":
    cProfile.run('profile_accessibility()', 'profile_stats')
    stats = pstats.Stats('profile_stats')
    stats.sort_stats('cumulative').print_stats(20)
```

### Memory Profiling

```python
# Check memory usage
import tracemalloc

tracemalloc.start()

# Your code here

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

### System Call Tracing

```bash
# Trace system calls (macOS)
sudo dtruss -p $(pgrep -f "python main.py") 2>&1 | grep -i accessibility

# Or use fs_usage for file system calls
sudo fs_usage -w -f pathname python
```

### Network Debugging

```bash
# Check if network issues affect API calls
netstat -an | grep 1234  # Check LM Studio connection
ping localhost           # Basic connectivity
```

## Getting Additional Help

### Collect Debug Information

When reporting issues, collect this information:

```bash
# System info
python -c "
import sys, platform, config
print('Python:', sys.version)
print('Platform:', platform.platform())
print('AURA Config Valid:', config.validate_debugging_config()[0])
"

# Permission status
python -c "
from modules.permission_validator import PermissionValidator
status = PermissionValidator().check_accessibility_permissions()
print('Permissions:', status.to_dict())
"

# Recent errors
grep -i error aura_debug.log | tail -10

# Configuration summary
python -c "
import config, json
summary = config.get_config_summary()
print(json.dumps(summary['debugging'], indent=2))
"
```

### Enable Maximum Debugging

```python
# In config.py - For comprehensive debugging
DEBUG_LEVEL = "VERBOSE"
DEBUG_CATEGORIES = {category: True for category in DEBUG_CATEGORIES}
TREE_INSPECTION_ENABLED = True
ELEMENT_ANALYSIS_ENABLED = True
ERROR_RECOVERY_ENABLED = True
DIAGNOSTIC_TOOLS_ENABLED = True
INTERACTIVE_DEBUGGING_ENABLED = True
```

This troubleshooting guide covers the most common issues encountered with AURA's debugging system. For issues not covered here, enable maximum debugging and collect the information listed above when seeking help.

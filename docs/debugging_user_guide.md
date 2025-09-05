# AURA Debugging User Guide

This guide helps users diagnose and resolve accessibility issues that cause AURA's fast path to fail and fall back to slower vision-based detection.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding Fast Path Failures](#understanding-fast-path-failures)
3. [Using Debugging Tools](#using-debugging-tools)
4. [Interpreting Debug Output](#interpreting-debug-output)
5. [Common Scenarios](#common-scenarios)
6. [Step-by-Step Troubleshooting](#step-by-step-troubleshooting)

## Quick Start

### Enable Basic Debugging

1. **Set debug level** in your environment:

   ```bash
   export AURA_DEBUG_LEVEL="DETAILED"
   ```

2. **Run AURA** with debugging enabled:

   ```bash
   python main.py
   ```

3. **Check debug logs** for issues:
   ```bash
   tail -f aura_debug.log
   ```

### Quick Health Check

Run the built-in diagnostic tools:

```bash
# Run comprehensive diagnostics
python -c "
from modules.diagnostic_tools import DiagnosticTools
diagnostics = DiagnosticTools()
report = diagnostics.run_comprehensive_diagnostics()
print(report.generate_summary())
"
```

## Understanding Fast Path Failures

### What is the Fast Path?

The fast path uses macOS accessibility APIs to directly find and interact with UI elements. It's much faster than vision-based detection but requires:

- Proper accessibility permissions
- Application accessibility support
- Correct element detection strategies

### Common Failure Messages

| Message                                                                 | Meaning                                        | Action                                         |
| ----------------------------------------------------------------------- | ---------------------------------------------- | ---------------------------------------------- |
| `Enhanced role detection failed, falling back to button-only detection` | Element role detection failed                  | Check application accessibility support        |
| `element_not_found`                                                     | Target element not found in accessibility tree | Verify element exists and is accessible        |
| `Permission denied`                                                     | Insufficient accessibility permissions         | Grant accessibility permissions                |
| `Timeout waiting for element`                                           | Element detection timed out                    | Increase timeout or check element availability |
| `Fuzzy matching failed`                                                 | Text matching couldn't find similar elements   | Check target text accuracy                     |

### Why Fast Path Fails

1. **Permission Issues**: Accessibility permissions not granted
2. **Application Issues**: App doesn't support accessibility properly
3. **Element Issues**: Target element not accessible or doesn't exist
4. **Timing Issues**: Element not ready when searched
5. **Text Matching Issues**: Target text doesn't match available elements

## Using Debugging Tools

### 1. Permission Validator

Check and fix accessibility permissions:

```bash
# Check current permissions
python -c "
from modules.permission_validator import PermissionValidator
validator = PermissionValidator()
status = validator.check_accessibility_permissions()
print(f'Permissions: {status.has_permissions}')
print(f'Level: {status.permission_level}')
if not status.has_permissions:
    print('Missing:', status.missing_permissions)
    print('Instructions:', validator.guide_permission_setup())
"
```

### 2. Accessibility Tree Inspector

Examine what elements are available:

```bash
# Dump accessibility tree for current application
python -c "
from modules.accessibility_debugger import AccessibilityDebugger
debugger = AccessibilityDebugger({})
tree = debugger.dump_accessibility_tree()
print(f'Found {tree.total_elements} elements')
print(f'Clickable elements: {len(tree.clickable_elements)}')
for element in tree.clickable_elements[:5]:  # Show first 5
    print(f'  - {element.get(\"AXTitle\", \"No title\")}: {element.get(\"AXRole\", \"Unknown role\")}')
"
```

### 3. Element Search Tester

Test element detection with different strategies:

```bash
# Test finding a specific element
python debug_cli.py --test-element "Sign In" --app "Safari"
```

### 4. Interactive Debugging

Start interactive debugging session:

```bash
# Start interactive debugging
python debug_interactive.py
```

This opens an interactive session where you can:

- Test commands in real-time
- Inspect accessibility trees
- Try different search strategies
- View detailed failure analysis

### 5. Performance Monitor

Monitor fast path performance:

```bash
# Run performance monitoring
python demo_performance_monitoring.py
```

## Interpreting Debug Output

### Debug Log Structure

Debug logs use structured format with these fields:

```
2024-01-15 10:30:45 - accessibility - INFO - [element_search] Found 15 clickable elements in Safari
2024-01-15 10:30:45 - accessibility - DEBUG - [fuzzy_matching] Comparing "Sign In" with "Sign in to your account" (score: 0.85)
2024-01-15 10:30:45 - accessibility - ERROR - [element_search] Element not found after 2.0s timeout
```

**Format**: `timestamp - module - level - [category] message`

### Debug Levels

#### BASIC Level Output

```
2024-01-15 10:30:45 - orchestrator - INFO - Command: "Click on Sign In"
2024-01-15 10:30:45 - accessibility - INFO - Fast path execution started
2024-01-15 10:30:47 - accessibility - ERROR - Fast path failed, falling back to vision
2024-01-15 10:30:50 - orchestrator - INFO - Command completed via vision fallback (3.2s)
```

#### DETAILED Level Output

```
2024-01-15 10:30:45 - orchestrator - INFO - Command: "Click on Sign In"
2024-01-15 10:30:45 - accessibility - INFO - Fast path execution started
2024-01-15 10:30:45 - accessibility - DEBUG - Application detected: Safari (browser)
2024-01-15 10:30:45 - accessibility - DEBUG - Using browser-specific detection strategy
2024-01-15 10:30:45 - accessibility - DEBUG - Searching for element with text: "Sign In"
2024-01-15 10:30:45 - accessibility - DEBUG - Found 12 clickable elements
2024-01-15 10:30:45 - accessibility - DEBUG - Fuzzy matching against: ["Sign in", "Sign up", "Continue", ...]
2024-01-15 10:30:45 - accessibility - DEBUG - Best match: "Sign in" (score: 0.95)
2024-01-15 10:30:45 - accessibility - INFO - Element found at coordinates (400, 300)
2024-01-15 10:30:45 - automation - INFO - Clicking at (400, 300)
2024-01-15 10:30:46 - orchestrator - INFO - Command completed via fast path (1.1s)
```

#### VERBOSE Level Output

Includes all DETAILED information plus:

- Complete accessibility tree dumps
- All element attributes
- API request/response details
- Performance metrics for each operation

### Key Indicators

#### Success Indicators

- `Fast path execution completed`
- `Element found at coordinates`
- `Command completed via fast path`
- High fuzzy matching scores (> 0.8)

#### Warning Indicators

- `Falling back to vision`
- `Low confidence match`
- `Timeout extended`
- `Using alternative strategy`

#### Error Indicators

- `Permission denied`
- `Element not found`
- `Timeout exceeded`
- `Application not responding`

## Common Scenarios

### Scenario 1: Permission Issues

**Symptoms**:

```
2024-01-15 10:30:45 - accessibility - ERROR - Permission denied accessing accessibility API
2024-01-15 10:30:45 - accessibility - INFO - Accessibility permissions not granted
```

**Solution**:

1. Check permissions:

   ```bash
   python -c "from modules.permission_validator import PermissionValidator; PermissionValidator().check_accessibility_permissions()"
   ```

2. Follow permission setup guide:

   - System Preferences → Security & Privacy → Privacy → Accessibility
   - Add Terminal or your Python interpreter
   - Enable the checkbox

3. Verify permissions:
   ```bash
   python -c "from modules.permission_validator import PermissionValidator; print(PermissionValidator().check_accessibility_permissions().has_permissions)"
   ```

### Scenario 2: Element Not Found

**Symptoms**:

```
2024-01-15 10:30:45 - accessibility - DEBUG - Searching for element with text: "Sign In"
2024-01-15 10:30:47 - accessibility - ERROR - Element not found after 2.0s timeout
2024-01-15 10:30:47 - accessibility - DEBUG - Available elements: ["Sign in", "Log in", "Continue"]
```

**Solution**:

1. Check available elements:

   ```bash
   python debug_cli.py --dump-tree --app "Safari"
   ```

2. Try exact text match:

   ```bash
   python debug_cli.py --test-element "Sign in" --app "Safari"
   ```

3. Adjust fuzzy matching threshold:
   ```python
   # In config.py
   SIMILARITY_SCORE_THRESHOLD = 0.5  # Lower threshold
   ```

### Scenario 3: Application Not Supported

**Symptoms**:

```
2024-01-15 10:30:45 - accessibility - DEBUG - Application detected: Unknown App
2024-01-15 10:30:45 - accessibility - DEBUG - Using generic detection strategy
2024-01-15 10:30:47 - accessibility - ERROR - No accessible elements found
```

**Solution**:

1. Check application accessibility:

   ```bash
   python debug_cli.py --check-app "Unknown App"
   ```

2. Try different detection strategies:

   ```python
   # In config.py
   ELEMENT_SEARCH_STRATEGIES = [
       "exact_match",
       "partial_match",  # Try partial matching
       "role_based",
       "attribute_based"
   ]
   ```

3. Enable browser-specific handling if it's a web app:
   ```python
   # In config.py
   BROWSER_SPECIFIC_HANDLING = True
   WEB_APP_DETECTION = True
   ```

### Scenario 4: Slow Performance

**Symptoms**:

```
2024-01-15 10:30:45 - performance - WARNING - Fast path execution time: 3.2s (threshold: 2.0s)
2024-01-15 10:30:45 - performance - INFO - Success rate: 65% (threshold: 70%)
```

**Solution**:

1. Check performance metrics:

   ```bash
   python demo_performance_monitoring.py
   ```

2. Optimize timeouts:

   ```python
   # In config.py
   ELEMENT_SEARCH_TIMEOUT = 1.5  # Reduce timeout
   FAST_PATH_TIMEOUT = 1500  # Reduce overall timeout
   ```

3. Enable caching:
   ```python
   # In config.py
   TREE_DUMP_CACHE_ENABLED = True
   APPLICATION_STRATEGY_CACHING = True
   ```

### Scenario 5: Intermittent Failures

**Symptoms**:

```
2024-01-15 10:30:45 - accessibility - INFO - Fast path succeeded
2024-01-15 10:31:15 - accessibility - ERROR - Fast path failed (same command)
2024-01-15 10:31:45 - accessibility - INFO - Fast path succeeded
```

**Solution**:

1. Enable error recovery:

   ```python
   # In config.py
   ERROR_RECOVERY_ENABLED = True
   ERROR_RECOVERY_MAX_RETRIES = 3
   ACCESSIBILITY_TREE_REFRESH_ENABLED = True
   ```

2. Monitor for application state changes:

   ```bash
   python debug_cli.py --monitor --app "Safari"
   ```

3. Increase retry delays:
   ```python
   # In config.py
   ERROR_RECOVERY_BASE_DELAY = 1.0  # Longer base delay
   ERROR_RECOVERY_MAX_DELAY = 10.0  # Longer max delay
   ```

## Step-by-Step Troubleshooting

### Step 1: Verify Basic Setup

1. **Check Python environment**:

   ```bash
   python --version  # Should be 3.11+
   conda info --envs  # Should show 'aura' environment
   ```

2. **Verify AURA installation**:

   ```bash
   python -c "import config; print('AURA config loaded successfully')"
   ```

3. **Test basic functionality**:
   ```bash
   python setup_check.py
   ```

### Step 2: Check Permissions

1. **Validate accessibility permissions**:

   ```bash
   python -c "
   from modules.permission_validator import PermissionValidator
   validator = PermissionValidator()
   status = validator.check_accessibility_permissions()
   if status.has_permissions:
       print('✅ Permissions OK')
   else:
       print('❌ Permissions missing:', status.missing_permissions)
       print('Instructions:')
       for instruction in validator.guide_permission_setup():
           print(f'  - {instruction}')
   "
   ```

2. **If permissions are missing**, follow the setup guide and restart AURA.

### Step 3: Test Element Detection

1. **Enable detailed debugging**:

   ```bash
   export AURA_DEBUG_LEVEL="DETAILED"
   ```

2. **Test with a simple command**:

   ```bash
   python main.py
   # Say: "Click on the close button"
   ```

3. **Check debug output**:
   ```bash
   tail -20 aura_debug.log
   ```

### Step 4: Analyze Failures

1. **Look for specific error patterns**:

   ```bash
   grep -i "error\|fail\|timeout" aura_debug.log | tail -10
   ```

2. **Check element availability**:

   ```bash
   python debug_cli.py --dump-tree --app "YourApp"
   ```

3. **Test element search**:
   ```bash
   python debug_cli.py --test-element "your target text" --app "YourApp"
   ```

### Step 5: Optimize Configuration

1. **Based on your findings**, adjust configuration:

   ```python
   # For permission issues
   PERMISSION_VALIDATION_ENABLED = True
   PERMISSION_GUIDE_ENABLED = True

   # For element detection issues
   SIMILARITY_SCORE_THRESHOLD = 0.5  # Lower for more matches
   ELEMENT_SEARCH_TIMEOUT = 3.0  # Higher for slow apps

   # For performance issues
   TREE_DUMP_CACHE_ENABLED = True
   APPLICATION_STRATEGY_CACHING = True
   ```

2. **Test the changes**:
   ```bash
   python main.py
   # Try the same command that was failing
   ```

### Step 6: Monitor and Iterate

1. **Enable performance monitoring**:

   ```python
   DEBUG_PERFORMANCE_TRACKING = True
   DEBUG_SUCCESS_RATE_TRACKING = True
   ```

2. **Monitor success rates**:

   ```bash
   python demo_performance_monitoring.py
   ```

3. **Adjust configuration** based on performance data.

## Getting Help

### Debug Information to Collect

When reporting issues, include:

1. **System information**:

   ```bash
   python -c "
   import config
   summary = config.get_config_summary()
   print('AURA Version:', summary['project']['version'])
   print('Python Version:', summary['system'])
   print('Debug Level:', summary['debugging']['debug_level'])
   "
   ```

2. **Permission status**:

   ```bash
   python -c "
   from modules.permission_validator import PermissionValidator
   status = PermissionValidator().check_accessibility_permissions()
   print('Permissions:', status.to_dict())
   "
   ```

3. **Recent debug logs**:

   ```bash
   tail -50 aura_debug.log
   ```

4. **Diagnostic report**:
   ```bash
   python -c "
   from modules.diagnostic_tools import DiagnosticTools
   report = DiagnosticTools().run_comprehensive_diagnostics()
   print(report.export_report('text'))
   "
   ```

### Common Solutions Summary

| Problem               | Quick Fix                                                |
| --------------------- | -------------------------------------------------------- |
| Permission denied     | Grant accessibility permissions in System Preferences    |
| Element not found     | Check available elements with `debug_cli.py --dump-tree` |
| Slow performance      | Enable caching and reduce timeouts                       |
| Intermittent failures | Enable error recovery and retries                        |
| App not supported     | Try different detection strategies                       |
| High memory usage     | Reduce debug level and disable tree caching              |

This user guide provides the essential information needed to diagnose and resolve most accessibility issues in AURA. For more advanced troubleshooting, refer to the developer documentation and troubleshooting guide.

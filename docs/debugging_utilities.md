# AURA Debugging Utilities Documentation

This document provides comprehensive documentation for AURA's debugging command-line tools and interactive debugging mode.

## Overview

AURA provides two main debugging utilities:

1. **debug_cli.py** - Standalone command-line debugging tools
2. **debug_interactive.py** - Interactive debugging mode with session recording

These tools help diagnose accessibility issues, test element detection, and troubleshoot fast path failures.

## Command-Line Debugging Tool (debug_cli.py)

### Installation and Setup

```bash
# Ensure you're in the AURA root directory
cd /path/to/aura

# Make the script executable
chmod +x debug_cli.py

# Run with Python
python debug_cli.py --help
```

### Available Commands

#### 1. Accessibility Tree Inspection

Dump and analyze the accessibility tree for any application:

```bash
# Dump tree for focused application (text format)
python debug_cli.py tree

# Dump tree for specific application
python debug_cli.py tree Safari

# Export tree as JSON
python debug_cli.py tree Chrome --output json --file chrome_tree.json

# Limit tree depth
python debug_cli.py tree Finder --depth 5
```

**Example Output:**

```
=== ACCESSIBILITY TREE: Safari ===
Generated: 2024-01-15 14:30:25
Total Elements: 1,247
Clickable Elements: 89
Tree Depth: 8
Generation Time: 156.3ms

--- Element Roles ---
AXStaticText: 423
AXButton: 67
AXLink: 45
AXTextField: 23
AXMenuItem: 18

--- Clickable Elements ---
 1. [AXButton] Back
 2. [AXButton] Forward
 3. [AXTextField] Address and Search
 4. [AXButton] Bookmarks
 5. [AXLink] Sign In
```

#### 2. Element Detection Testing

Test element detection with various search strategies:

```bash
# Test element detection with exact matching
python debug_cli.py element "Sign In" Safari

# Test with fuzzy matching
python debug_cli.py element "Sign In" Safari --fuzzy --threshold 70

# Export analysis as JSON
python debug_cli.py element "Search" --output json --file search_analysis.json
```

**Example Output:**

```
=== ELEMENT DETECTION ANALYSIS ===
Target: Sign In
Search Strategy: multi_strategy
Matches Found: 3
Search Time: 45.2ms

--- Best Match ---
Role: AXLink
Title: Sign In
Description: Sign in to your account
Match Score: 95.0%
Matched Text: Sign In

--- Recommendations ---
1. Element found with high confidence - fast path should work
2. Consider using exact text matching for better performance
3. Element is accessible and clickable
```

#### 3. System Health Check

Run comprehensive accessibility health diagnostics:

```bash
# Run basic health check
python debug_cli.py health

# Export detailed report as JSON
python debug_cli.py health --format json --output health_report.json
```

**Example Output:**

```
=== AURA Diagnostic Report ===
Generated: 2024-01-15 14:35:12
Overall Health Score: 85.0/100

Accessibility Permissions: ✅ Accessibility permissions granted (FULL)
Issues Found: 2 total
  - 0 CRITICAL issues
  - 1 HIGH priority issues
Performance Tests: 2/3 passed

Top Recommendations:
  1. Update Chrome to latest version for better accessibility support
  2. Consider restarting applications that show low detection rates
  3. Enable accessibility features in System Preferences for optimal performance
```

#### 4. Element Detection Capability Testing

Test element detection with known good elements:

```bash
# Test specific elements in an application
python debug_cli.py test Finder "New Folder,View,Go,Edit" --verbose

# Save results to file
python debug_cli.py test Safari "Back,Forward,Bookmarks" --output safari_test.json
```

**Example Output:**

```
=== ELEMENT DETECTION TEST RESULTS ===
Application: Finder
Elements Tested: 4
Elements Found: 3
Elements Not Found: 1
Detection Rate: 75.0%
Average Detection Time: 23.4ms

--- Detailed Results ---
✅ FOUND 'New Folder' (1 matches, 18.2ms)
    Best match: AXButton - New Folder (Score: 100.0%)
✅ FOUND 'View' (2 matches, 25.1ms)
    Best match: AXMenuBarItem - View (Score: 100.0%)
✅ FOUND 'Go' (1 matches, 19.8ms)
    Best match: AXMenuBarItem - Go (Score: 100.0%)
❌ NOT FOUND 'Edit' (0 matches, 30.5ms)
```

#### 5. Permission Management

Check and manage accessibility permissions:

```bash
# Check current permissions
python debug_cli.py permissions

# Request permissions (if possible)
python debug_cli.py permissions --request

# Monitor permission changes in real-time
python debug_cli.py permissions --monitor
```

**Example Output:**

```
=== ACCESSIBILITY PERMISSIONS ===
Status: ✅ Accessibility permissions granted (FULL)
Permission Level: FULL
System Version: 14.2.1
Can Request Permissions: True

--- Granted Permissions ---
✅ basic_accessibility_access
✅ system_wide_element_access
✅ focused_application_access
✅ process_trust_status

--- Recommendations ---
1. Permissions are properly configured
2. Fast path execution should work reliably
3. No action required
```

## Interactive Debugging Mode (debug_interactive.py)

### Starting Interactive Mode

```bash
# Start interactive debugging
python debug_interactive.py

# Start with session recording
python debug_interactive.py --record my_debug_session.json

# Playback a recorded session
python debug_interactive.py --playback previous_session.json
```

### Interactive Commands

Once in interactive mode, you can use these commands:

#### Basic Debugging Commands

```
(aura-debug) tree Safari
(aura-debug) element "Sign In" Chrome
(aura-debug) health
(aura-debug) permissions
```

#### Application Management

```
# List running applications
(aura-debug) apps

# Check focused application
(aura-debug) focus

# Set focus to specific app (manual focus required)
(aura-debug) focus Safari
```

#### Command Execution and Stepping

```
# Execute AURA command with debugging
(aura-debug) command "Click on Sign In button"

# Step through command execution
(aura-debug) step "Click on Search button"
```

#### Session Management

```
# Start recording
(aura-debug) record debug_session.json

# Save current session
(aura-debug) save my_session.json

# Load and playback session
(aura-debug) playback old_session.json

# Clear session history
(aura-debug) clear
```

#### System Information

```
# Show cache status
(aura-debug) cache

# Show configuration
(aura-debug) config

# Exit interactive mode
(aura-debug) quit
```

### Session Recording and Playback

Interactive mode supports recording debugging sessions for later analysis:

```bash
# Start recording
python debug_interactive.py --record troubleshooting_session.json

# In interactive mode, run commands:
(aura-debug) health
(aura-debug) tree Chrome
(aura-debug) element "Sign In"
(aura-debug) quit

# Later, playback the session:
python debug_interactive.py --playback troubleshooting_session.json
```

**Session File Format:**

```json
{
  "metadata": {
    "session_id": "debug_session_1705334125",
    "start_time": "2024-01-15T14:35:25.123456",
    "platform": "darwin",
    "python_version": "3.11.5"
  },
  "commands": [
    {
      "timestamp": "2024-01-15T14:35:30.456789",
      "command": "health",
      "args": [],
      "result": {
        "success": true,
        "health_score": 85.0,
        "execution_time_ms": 1234.5
      }
    }
  ],
  "end_time": "2024-01-15T14:40:15.789012",
  "total_commands": 5
}
```

## Common Use Cases

### 1. Troubleshooting Fast Path Failures

When commands consistently fall back to vision:

```bash
# 1. Check permissions
python debug_cli.py permissions

# 2. Run health check
python debug_cli.py health

# 3. Analyze specific failing element
python debug_cli.py element "problematic text" AppName --fuzzy

# 4. Dump tree to see available elements
python debug_cli.py tree AppName --output json --file debug_tree.json
```

### 2. Application-Specific Debugging

For applications with poor detection rates:

```bash
# 1. Test known elements
python debug_cli.py test AppName "Button1,Button2,Link1" --verbose

# 2. Interactive debugging
python debug_interactive.py --record app_debug.json
(aura-debug) tree AppName
(aura-debug) element "target text" AppName
(aura-debug) command "Click on target text"
```

### 3. Performance Analysis

To analyze detection performance:

```bash
# 1. Run comprehensive health check
python debug_cli.py health --output performance_report.json

# 2. Test multiple applications
for app in Safari Chrome Finder; do
    python debug_cli.py test $app "common,elements" --output ${app}_test.json
done
```

### 4. Permission Issues

When accessibility permissions are problematic:

```bash
# 1. Check detailed permission status
python debug_cli.py permissions

# 2. Monitor permission changes
python debug_cli.py permissions --monitor

# 3. Interactive permission debugging
python debug_interactive.py
(aura-debug) permissions
(aura-debug) health
```

## Advanced Usage

### Custom Configuration

Create a `debug_config.py` file to customize debugging behavior:

```python
# debug_config.py
DEBUG_LEVEL = 'VERBOSE'
MAX_TREE_DEPTH = 12
CACHE_TTL_SECONDS = 120
PERFORMANCE_TRACKING = True
AUTO_DIAGNOSTICS = True
INCLUDE_INVISIBLE_ELEMENTS = True

# Test applications for benchmarking
TEST_APPLICATIONS = [
    'Safari', 'Chrome', 'Firefox',
    'Finder', 'Mail', 'Messages',
    'System Preferences', 'Terminal'
]

# Known good elements for testing
KNOWN_GOOD_ELEMENTS = {
    'Safari': ['Back', 'Forward', 'Address and Search', 'Bookmarks'],
    'Chrome': ['Back', 'Forward', 'Address bar', 'Menu'],
    'Finder': ['New Folder', 'View', 'Go', 'Edit'],
    'Mail': ['Compose', 'Reply', 'Forward', 'Delete']
}
```

### Automation Scripts

Create automation scripts for regular debugging:

```bash
#!/bin/bash
# daily_health_check.sh

echo "Running daily AURA health check..."
python debug_cli.py health --output "health_$(date +%Y%m%d).json"

echo "Testing core applications..."
python debug_cli.py test Safari "Back,Forward,Bookmarks" --output safari_daily.json
python debug_cli.py test Chrome "Back,Forward,Menu" --output chrome_daily.json

echo "Checking permissions..."
python debug_cli.py permissions > permissions_daily.log

echo "Daily health check complete!"
```

### Integration with CI/CD

Use debugging tools in continuous integration:

```yaml
# .github/workflows/accessibility_test.yml
name: Accessibility Testing
on: [push, pull_request]

jobs:
  accessibility-test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run accessibility health check
        run: python debug_cli.py health --format json --output health_report.json
      - name: Upload health report
        uses: actions/upload-artifact@v2
        with:
          name: health-report
          path: health_report.json
```

## Troubleshooting

### Common Issues

1. **"Accessibility frameworks not available"**

   ```bash
   pip install pyobjc-framework-AppKit pyobjc-framework-Accessibility
   ```

2. **"Permission denied" errors**

   - Grant accessibility permissions in System Preferences
   - Restart Terminal/IDE after granting permissions

3. **"No focused application found"**

   - Ensure an application is focused
   - Use specific app name instead of relying on focus detection

4. **Slow performance**
   - Reduce tree depth: `--depth 5`
   - Use caching: avoid `--force-refresh`
   - Limit element search scope

### Debug Logging

Enable verbose logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:

```bash
export AURA_DEBUG=1
python debug_cli.py health
```

## Best Practices

1. **Regular Health Checks**: Run daily health checks to catch issues early
2. **Session Recording**: Record debugging sessions for complex issues
3. **Application Testing**: Test element detection for frequently used applications
4. **Permission Monitoring**: Monitor permission changes that might affect functionality
5. **Performance Tracking**: Track detection rates and performance over time
6. **Documentation**: Document application-specific issues and solutions

## Support

For additional help:

1. Check the main AURA documentation
2. Review logged error messages
3. Use interactive mode for step-by-step debugging
4. Record sessions for sharing with support team
5. Run health checks to identify system-level issues

## Examples Repository

See the `examples/debugging/` directory for:

- Sample debugging scripts
- Common troubleshooting workflows
- Application-specific debugging guides
- Performance optimization examples

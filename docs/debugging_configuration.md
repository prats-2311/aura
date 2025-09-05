# AURA Debugging Configuration Guide

This guide covers the comprehensive debugging configuration options available in AURA for troubleshooting accessibility issues and optimizing fast path performance.

## Table of Contents

1. [Overview](#overview)
2. [Debug Levels](#debug-levels)
3. [Configuration Categories](#configuration-categories)
4. [Environment Variables](#environment-variables)
5. [Best Practices](#best-practices)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

## Overview

AURA's debugging system provides comprehensive tools for diagnosing and resolving accessibility issues that cause fast path failures. The debugging configuration is centralized in `config.py` and can be customized through environment variables or direct configuration changes.

### Key Features

- **Multi-level debugging**: BASIC, DETAILED, and VERBOSE levels
- **Categorized logging**: Enable/disable specific debugging categories
- **Performance monitoring**: Track success rates and execution times
- **Automated diagnostics**: Health checks and issue detection
- **Interactive debugging**: Real-time troubleshooting tools
- **Secure logging**: Sanitization of sensitive data

## Debug Levels

### BASIC Level (Default)

- Essential failure information and timing
- Minimal performance impact
- Suitable for production environments

```python
DEBUG_LEVEL = "BASIC"
```

**What you get:**

- Command execution results (success/failure)
- Basic timing information
- Critical error messages
- Fast path vs vision fallback decisions

### DETAILED Level

- Element attributes, search parameters, and match scores
- Moderate performance impact
- Ideal for development and troubleshooting

```python
DEBUG_LEVEL = "DETAILED"
```

**What you get:**

- All BASIC level information
- Element detection attempts and results
- Fuzzy matching scores and comparisons
- Application detection strategies
- Error recovery attempts

### VERBOSE Level

- Complete accessibility tree dumps and all API interactions
- Higher performance impact
- Use for deep debugging and analysis

```python
DEBUG_LEVEL = "VERBOSE"
```

**What you get:**

- All DETAILED level information
- Complete accessibility tree structures
- All API request/response data
- Detailed performance metrics
- Stack traces for errors

## Configuration Categories

### Permission Validation

Controls accessibility permission checking and guidance.

```python
# Permission validation settings
PERMISSION_VALIDATION_ENABLED = True
PERMISSION_AUTO_REQUEST = False  # Automatically request permissions if missing
PERMISSION_VALIDATION_TIMEOUT = 5.0  # Seconds to wait for permission validation
PERMISSION_MONITORING_ENABLED = True  # Monitor for runtime permission changes
PERMISSION_GUIDE_ENABLED = True  # Show step-by-step permission setup guide
```

**Best Practice**: Keep `PERMISSION_AUTO_REQUEST = False` in production to avoid unexpected system dialogs.

### Tree Inspection

Controls accessibility tree dumping and analysis.

```python
# Accessibility tree inspection settings
TREE_INSPECTION_ENABLED = True
TREE_DUMP_MAX_DEPTH = 10  # Maximum depth for tree traversal
TREE_DUMP_INCLUDE_HIDDEN = False  # Include hidden elements in tree dumps
TREE_DUMP_CACHE_ENABLED = True  # Cache tree dumps for performance
TREE_DUMP_CACHE_TTL = 30  # Cache time-to-live in seconds
TREE_ELEMENT_ATTRIBUTE_FILTER = []  # Empty list means include all attributes
```

**Performance Note**: Higher `TREE_DUMP_MAX_DEPTH` values provide more detail but impact performance.

### Element Analysis

Controls element search and matching analysis.

```python
# Element analysis and search settings
ELEMENT_ANALYSIS_ENABLED = True
ELEMENT_SEARCH_TIMEOUT = 2.0  # Seconds for element search operations
ELEMENT_COMPARISON_ENABLED = True  # Enable element comparison for debugging
FUZZY_MATCH_ANALYSIS_ENABLED = True  # Detailed fuzzy matching analysis
SIMILARITY_SCORE_THRESHOLD = 0.6  # Minimum similarity score for matches
ELEMENT_SEARCH_STRATEGIES = [
    "exact_match",
    "fuzzy_match",
    "partial_match",
    "role_based",
    "attribute_based"
]
```

**Tuning Tip**: Adjust `SIMILARITY_SCORE_THRESHOLD` based on your application's UI consistency.

### Application Detection

Controls application-specific detection strategies.

```python
# Application detection and adaptation settings
APPLICATION_DETECTION_ENABLED = True
APPLICATION_STRATEGY_CACHING = True  # Cache detection strategies per application
APPLICATION_STRATEGY_CACHE_TTL = 300  # Cache TTL in seconds
BROWSER_SPECIFIC_HANDLING = True  # Enable browser-specific accessibility handling
NATIVE_APP_OPTIMIZATION = True  # Optimize for native macOS applications
WEB_APP_DETECTION = True  # Detect and handle web applications specially
```

### Error Recovery

Controls retry mechanisms and error handling.

```python
# Error recovery and retry settings
ERROR_RECOVERY_ENABLED = True
ERROR_RECOVERY_MAX_RETRIES = 3
ERROR_RECOVERY_BACKOFF_FACTOR = 2.0  # Exponential backoff multiplier
ERROR_RECOVERY_BASE_DELAY = 0.5  # Base delay in seconds
ERROR_RECOVERY_MAX_DELAY = 5.0  # Maximum delay in seconds
ACCESSIBILITY_TREE_REFRESH_ENABLED = True
ELEMENT_CACHE_INVALIDATION_ENABLED = True
```

**Formula**: Retry delay = `BASE_DELAY * (BACKOFF_FACTOR ^ retry_attempt)`, capped at `MAX_DELAY`

### Diagnostic Tools

Controls automated diagnostics and health checking.

```python
# Diagnostic tools configuration
DIAGNOSTIC_TOOLS_ENABLED = True
DIAGNOSTIC_AUTO_RUN = False  # Automatically run diagnostics on failures
DIAGNOSTIC_HEALTH_CHECK_INTERVAL = 300  # Seconds between automatic health checks
DIAGNOSTIC_REPORT_FORMAT = "json"  # json, html, text
DIAGNOSTIC_REPORT_INCLUDE_SCREENSHOTS = False  # Include screenshots in reports
DIAGNOSTIC_PERFORMANCE_BENCHMARKING = True
DIAGNOSTIC_ISSUE_PRIORITIZATION = True  # Prioritize issues by impact
```

### Performance Monitoring

Controls performance tracking and alerting.

```python
# Performance monitoring for debugging
DEBUG_PERFORMANCE_TRACKING = True
DEBUG_EXECUTION_TIME_LOGGING = True
DEBUG_SUCCESS_RATE_TRACKING = True
DEBUG_PERFORMANCE_ALERTS = True
DEBUG_PERFORMANCE_DEGRADATION_THRESHOLD = 0.7  # Alert if success rate drops below 70%
DEBUG_PERFORMANCE_HISTORY_SIZE = 1000  # Number of operations to track
```

### Interactive Debugging

Controls interactive debugging features.

```python
# Interactive debugging settings
INTERACTIVE_DEBUGGING_ENABLED = True
INTERACTIVE_SESSION_RECORDING = False  # Record debugging sessions
INTERACTIVE_STEP_BY_STEP = False  # Enable step-by-step debugging mode
INTERACTIVE_REAL_TIME_FEEDBACK = True  # Provide real-time feedback during debugging
```

### CLI Tools

Controls command-line debugging utilities.

```python
# Command-line debugging tools settings
CLI_DEBUGGING_TOOLS_ENABLED = True
CLI_TREE_INSPECTOR_ENABLED = True
CLI_ELEMENT_TESTER_ENABLED = True
CLI_DIAGNOSTIC_RUNNER_ENABLED = True
CLI_PERFORMANCE_MONITOR_ENABLED = True
```

### Security and Privacy

Controls data sanitization and privacy protection.

```python
# Security and privacy settings for debugging
DEBUG_SANITIZE_SENSITIVE_DATA = True  # Remove sensitive data from debug output
DEBUG_CONTENT_FILTERING = True  # Filter potentially sensitive content
DEBUG_PRIVACY_MODE = False  # Enhanced privacy mode for debugging
DEBUG_SECURE_LOG_HANDLING = True  # Secure handling of debug logs
```

## Environment Variables

You can override configuration settings using environment variables:

```bash
# Set debug level
export AURA_DEBUG_LEVEL="DETAILED"

# Enable/disable debugging
export AURA_DEBUG="true"

# Set custom debug log file
export AURA_DEBUG_LOG_FILE="/path/to/custom/debug.log"
```

### Available Environment Variables

| Variable              | Default          | Description                            |
| --------------------- | ---------------- | -------------------------------------- |
| `AURA_DEBUG_LEVEL`    | `BASIC`          | Debug level (BASIC, DETAILED, VERBOSE) |
| `AURA_DEBUG`          | `false`          | Enable/disable debug mode              |
| `AURA_DEBUG_LOG_FILE` | `aura_debug.log` | Debug log file path                    |

## Best Practices

### Development Environment

```python
# Recommended settings for development
DEBUG_LEVEL = "DETAILED"
DEBUG_LOG_TO_CONSOLE = True
DEBUG_LOG_TO_FILE = True
PERMISSION_VALIDATION_ENABLED = True
TREE_INSPECTION_ENABLED = True
ELEMENT_ANALYSIS_ENABLED = True
DIAGNOSTIC_TOOLS_ENABLED = True
DEBUG_PERFORMANCE_TRACKING = True
INTERACTIVE_DEBUGGING_ENABLED = True
```

### Production Environment

```python
# Recommended settings for production
DEBUG_LEVEL = "BASIC"
DEBUG_LOG_TO_CONSOLE = False
DEBUG_LOG_TO_FILE = True
PERMISSION_VALIDATION_ENABLED = True
TREE_INSPECTION_ENABLED = False  # Reduce overhead
ELEMENT_ANALYSIS_ENABLED = True
DIAGNOSTIC_AUTO_RUN = False  # Avoid automatic diagnostics
DEBUG_SANITIZE_SENSITIVE_DATA = True
DEBUG_SECURE_LOG_HANDLING = True
```

### Troubleshooting Environment

```python
# Recommended settings for intensive troubleshooting
DEBUG_LEVEL = "VERBOSE"
DEBUG_LOG_TO_CONSOLE = True
DEBUG_LOG_TO_FILE = True
TREE_INSPECTION_ENABLED = True
TREE_DUMP_MAX_DEPTH = 15  # Deeper inspection
ELEMENT_ANALYSIS_ENABLED = True
FUZZY_MATCH_ANALYSIS_ENABLED = True
ERROR_RECOVERY_ENABLED = True
DIAGNOSTIC_TOOLS_ENABLED = True
INTERACTIVE_DEBUGGING_ENABLED = True
```

### Performance Optimization

```python
# Settings optimized for performance
DEBUG_LEVEL = "BASIC"
TREE_DUMP_CACHE_ENABLED = True
TREE_DUMP_CACHE_TTL = 60  # Longer cache
APPLICATION_STRATEGY_CACHING = True
APPLICATION_STRATEGY_CACHE_TTL = 600  # Longer cache
ELEMENT_SEARCH_TIMEOUT = 1.0  # Shorter timeout
DEBUG_PERFORMANCE_HISTORY_SIZE = 100  # Smaller history
```

## Examples

### Example 1: Basic Debugging Setup

```python
# config.py - Basic debugging for everyday use
DEBUG_LEVEL = "BASIC"
DEBUG_CATEGORIES = {
    "accessibility": True,
    "permissions": True,
    "element_search": True,
    "performance": True,
    "error_recovery": False,  # Disable for less noise
    "application_detection": False,
    "fuzzy_matching": False,
    "tree_inspection": False,
    "failure_analysis": True,
    "diagnostic_tools": True
}
```

### Example 2: Troubleshooting Fast Path Failures

```python
# config.py - Detailed debugging for fast path issues
DEBUG_LEVEL = "DETAILED"
DEBUG_CATEGORIES = {
    "accessibility": True,
    "permissions": True,
    "element_search": True,
    "performance": True,
    "error_recovery": True,
    "application_detection": True,
    "fuzzy_matching": True,
    "tree_inspection": True,
    "failure_analysis": True,
    "diagnostic_tools": True
}

# Enhanced element analysis
ELEMENT_ANALYSIS_ENABLED = True
FUZZY_MATCH_ANALYSIS_ENABLED = True
SIMILARITY_SCORE_THRESHOLD = 0.5  # Lower threshold for more matches

# Detailed error recovery
ERROR_RECOVERY_ENABLED = True
ERROR_RECOVERY_MAX_RETRIES = 5
```

### Example 3: Application-Specific Debugging

```python
# config.py - Debugging for specific applications
DEBUG_LEVEL = "DETAILED"

# Focus on application detection
APPLICATION_DETECTION_ENABLED = True
BROWSER_SPECIFIC_HANDLING = True
NATIVE_APP_OPTIMIZATION = True
WEB_APP_DETECTION = True

# Enable tree inspection for app analysis
TREE_INSPECTION_ENABLED = True
TREE_DUMP_MAX_DEPTH = 12
TREE_DUMP_INCLUDE_HIDDEN = True  # Include hidden elements

# Application-specific categories
DEBUG_CATEGORIES = {
    "accessibility": True,
    "application_detection": True,
    "tree_inspection": True,
    "element_search": True,
    "fuzzy_matching": True,
    "failure_analysis": True,
    # Disable others for focus
    "permissions": False,
    "performance": False,
    "error_recovery": False,
    "diagnostic_tools": False
}
```

### Example 4: Performance Analysis

```python
# config.py - Performance monitoring and analysis
DEBUG_LEVEL = "BASIC"  # Keep overhead low

# Enable performance tracking
DEBUG_PERFORMANCE_TRACKING = True
DEBUG_EXECUTION_TIME_LOGGING = True
DEBUG_SUCCESS_RATE_TRACKING = True
DEBUG_PERFORMANCE_ALERTS = True
DEBUG_PERFORMANCE_DEGRADATION_THRESHOLD = 0.8  # Alert at 80%
DEBUG_PERFORMANCE_HISTORY_SIZE = 2000  # Larger history

# Focus on performance categories
DEBUG_CATEGORIES = {
    "performance": True,
    "failure_analysis": True,
    "diagnostic_tools": True,
    # Disable detailed logging for performance
    "accessibility": False,
    "tree_inspection": False,
    "element_search": False,
    "fuzzy_matching": False,
    "permissions": True,  # Keep for permission issues
    "error_recovery": True,
    "application_detection": False
}
```

## Troubleshooting

### Common Issues

#### 1. High Memory Usage

**Symptoms**: AURA consuming excessive memory during debugging

**Solutions**:

```python
# Reduce memory usage
TREE_DUMP_CACHE_ENABLED = False  # Disable caching
DEBUG_PERFORMANCE_HISTORY_SIZE = 50  # Smaller history
TREE_DUMP_MAX_DEPTH = 5  # Shallower tree dumps
DEBUG_LEVEL = "BASIC"  # Less detailed logging
```

#### 2. Slow Performance

**Symptoms**: Debugging causing significant slowdown

**Solutions**:

```python
# Optimize for speed
DEBUG_LOG_TO_CONSOLE = False  # Console output is slow
ELEMENT_SEARCH_TIMEOUT = 1.0  # Shorter timeouts
TREE_INSPECTION_ENABLED = False  # Disable tree dumps
INTERACTIVE_DEBUGGING_ENABLED = False  # Disable interactive features
```

#### 3. Log Files Growing Too Large

**Symptoms**: Debug log files consuming disk space

**Solutions**:

```python
# Control log file size
DEBUG_LOG_MAX_SIZE = 5 * 1024 * 1024  # 5MB limit
DEBUG_LOG_BACKUP_COUNT = 2  # Keep fewer backups
DEBUG_LEVEL = "BASIC"  # Less verbose logging

# Or disable file logging temporarily
DEBUG_LOG_TO_FILE = False
```

#### 4. Missing Debug Information

**Symptoms**: Not enough information to diagnose issues

**Solutions**:

```python
# Increase debug detail
DEBUG_LEVEL = "VERBOSE"
DEBUG_CATEGORIES = {category: True for category in DEBUG_CATEGORIES}
TREE_INSPECTION_ENABLED = True
ELEMENT_ANALYSIS_ENABLED = True
FUZZY_MATCH_ANALYSIS_ENABLED = True
```

#### 5. Permission Issues

**Symptoms**: Debugging tools can't access accessibility information

**Solutions**:

```python
# Enable permission validation and guidance
PERMISSION_VALIDATION_ENABLED = True
PERMISSION_GUIDE_ENABLED = True
PERMISSION_MONITORING_ENABLED = True

# Check permissions manually
python -c "import config; config.validate_config()"
```

### Validation Commands

```bash
# Validate current configuration
python -c "import config; is_valid, errors, warnings = config.validate_debugging_config(); print('Valid:', is_valid); print('Errors:', errors); print('Warnings:', warnings)"

# Get configuration summary
python -c "import config; import json; print(json.dumps(config.get_config_summary()['debugging'], indent=2))"

# Test specific debug level
AURA_DEBUG_LEVEL=VERBOSE python -c "import config; print('Debug level:', config.DEBUG_LEVEL)"
```

### Debug Log Analysis

```bash
# View recent debug entries
tail -f aura_debug.log

# Search for specific issues
grep -i "error\|fail\|timeout" aura_debug.log

# Count success vs failure rates
grep -c "success" aura_debug.log
grep -c "failure\|error" aura_debug.log

# Analyze performance
grep "execution_time" aura_debug.log | tail -20
```

## Configuration Validation

Always validate your configuration after making changes:

```python
# In Python
import config

# Validate debugging configuration
is_valid, errors, warnings = config.validate_debugging_config()

if not is_valid:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")

if warnings:
    print("Configuration warnings:")
    for warning in warnings:
        print(f"  - {warning}")

# Get default values for reference
defaults = config.get_debugging_config_defaults()
print("Default values:", defaults)
```

This comprehensive debugging configuration system provides the flexibility and power needed to diagnose and resolve accessibility issues in AURA while maintaining performance and security.

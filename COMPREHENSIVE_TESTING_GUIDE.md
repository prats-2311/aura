# AURA Hybrid Architecture - Comprehensive Testing Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Test Environment Setup](#test-environment-setup)
4. [Individual Test Commands](#individual-test-commands)
5. [Workflow Testing](#workflow-testing)
6. [Performance Testing](#performance-testing)
7. [Integration Testing](#integration-testing)
8. [Regression Testing](#regression-testing)
9. [Manual Testing Scenarios](#manual-testing-scenarios)
10. [Expected Results](#expected-results)
11. [Troubleshooting](#troubleshooting)

## Overview

This guide provides detailed instructions for testing the AURA Hybrid Architecture implementation. The hybrid system combines fast accessibility-based GUI automation with traditional vision-based fallback, providing significant performance improvements while maintaining reliability.

### Key Components Being Tested

- **Fast Path**: Accessibility API-based element detection and interaction
- **Slow Path**: Vision model-based screen analysis and reasoning
- **Hybrid Orchestration**: Intelligent routing between fast and slow paths
- **Fallback Mechanism**: Seamless transition when fast path fails
- **Performance Optimization**: Caching, parallel processing, and resource management
- **Error Recovery**: Graceful degradation and system resilience

## Prerequisites

### System Requirements

```bash
# Verify Python version (3.8+ required)
python --version

# Verify required packages are installed
pip list | grep -E "(pytest|psutil|pillow|requests)"
```

### macOS Accessibility Permissions

1. **Grant Accessibility Permissions**:

   - Open System Preferences → Security & Privacy → Privacy → Accessibility
   - Add Terminal or your IDE to the list of allowed applications
   - Ensure the checkbox is checked

2. **Verify Accessibility Status**:
   ```bash
   python -c "
   from modules.accessibility import AccessibilityModule
   module = AccessibilityModule()
   status = module.get_accessibility_status()
   print('Accessibility Status:', status)
   "
   ```

### Environment Variables

```bash
# Set up test environment
export AURA_TEST_MODE=true
export AURA_LOG_LEVEL=DEBUG
export PYTHONPATH=$PWD:$PYTHONPATH
```

## Test Environment Setup

### 1. Basic Environment Check

```bash
# Run the setup check script
python setup_check.py

# Expected Output:
# ✓ Python version: 3.x.x
# ✓ Required packages installed
# ✓ Accessibility permissions granted
# ✓ Test environment ready
```

### 2. Module Import Verification

```bash
# Test all module imports
python -c "
from orchestrator import Orchestrator
from modules.accessibility import AccessibilityModule
from modules.vision import VisionModule
from modules.automation import AutomationModule
print('All modules imported successfully')
"
```

### 3. Basic Functionality Test

```bash
# Quick functionality test
python -c "
from orchestrator import Orchestrator
orchestrator = Orchestrator()
health = orchestrator.get_system_health()
print('System Health:', health['overall_health'])
"
```

## Individual Test Commands

### 1. Fast Path Performance Tests

#### Test Fast Path Click Performance

```bash
# Command:
python -m pytest tests/test_performance_regression.py::TestPerformanceRegression::test_fast_path_click_performance_regression -v -s

# What it tests:
# - Fast path click execution time < 2 seconds
# - Success rate > 95%
# - Memory usage < 10MB increase per operation

# Expected output:
# PASSED - Fast path click performance: 0.XXXs avg, XX.X% success rate
```

#### Test Fast Path Type Performance

```bash
# Command:
python -m pytest tests/test_performance_regression.py::TestPerformanceRegression::test_fast_path_type_performance_regression -v -s

# What it tests:
# - Fast path typing execution time < 2.5 seconds
# - Success rate > 95%
# - Memory efficiency validation

# Expected output:
# PASSED - Fast path type performance: 0.XXXs avg, XX.X% success rate
```

#### Test Accessibility Element Detection

```bash
# Command:
python -m pytest tests/test_performance_regression.py::TestPerformanceRegression::test_accessibility_element_detection_regression -v -s

# What it tests:
# - Element detection speed < 1 second
# - Detection accuracy > 98%
# - Coordinate calculation precision

# Expected output:
# PASSED - Element detection performance: 0.XXXs avg, XX.X% success rate
```

### 2. Hybrid Orchestration Tests

#### Test Fast Path Execution Success

```bash
# Command:
python -m pytest tests/test_hybrid_orchestration.py::TestFastPathRouting::test_fast_path_execution_success -v -s

# What it tests:
# - Successful fast path routing for GUI commands
# - Accessibility module integration
# - Action execution via automation module

# Expected behavior:
# 1. Command is identified as GUI interaction
# 2. Accessibility API finds the target element
# 3. Coordinates are calculated correctly
# 4. Action is executed successfully
# 5. Result indicates fast path was used

# Expected output:
# PASSED - Fast path execution completed successfully
```

#### Test Fallback Mechanism

```bash
# Command:
python -m pytest tests/test_hybrid_orchestration.py::TestFallbackMechanism::test_vision_module_bypassed_on_fast_path_success -v -s

# What it tests:
# - Vision module is NOT called when fast path succeeds
# - Performance optimization through module bypassing
# - Correct execution path selection

# Expected behavior:
# 1. Fast path succeeds in finding element
# 2. Vision module capture_screen() is never called
# 3. Vision module analyze_screen() is never called
# 4. Reasoning module is not invoked
# 5. Only accessibility and automation modules are used

# Expected output:
# PASSED - Vision module correctly bypassed during fast path success
```

#### Test Element Not Found Fallback

```bash
# Command:
python -m pytest tests/test_hybrid_orchestration.py::TestFastPathRouting::test_fast_path_execution_element_not_found -v -s

# What it tests:
# - Graceful handling when accessibility API cannot find element
# - Proper fallback indication
# - Error context preservation

# Expected behavior:
# 1. Accessibility API returns None (element not found)
# 2. Fast path execution fails gracefully
# 3. Result indicates fallback is required
# 4. Failure reason is documented
# 5. No exceptions are raised

# Expected output:
# PASSED - Element not found scenario handled correctly
```

### 3. Performance Benchmarking Tests

#### Test Fast vs Slow Path Comparison

```bash
# Command:
python -m pytest tests/test_performance_benchmarking.py::TestPerformanceBenchmarking::test_performance_comparison_analysis -v -s

# What it tests:
# - Performance difference between fast and slow paths
# - Statistical significance of improvement
# - Improvement factor calculation

# Expected behavior:
# 1. Fast path executes in ~0.2 seconds
# 2. Slow path executes in ~3.5 seconds
# 3. Improvement factor > 5x
# 4. Improvement percentage > 80%
# 5. Statistical significance confirmed

# Expected output:
# PASSED - Performance comparison: X.Xx faster, XX.X% improvement
```

#### Test Concurrent Execution Performance

```bash
# Command:
python -m pytest tests/test_performance_benchmarking.py::TestPerformanceBenchmarking::test_concurrent_execution_performance -v -s

# What it tests:
# - System performance under concurrent load
# - Thread safety of fast path execution
# - Resource contention handling

# Expected behavior:
# 1. Multiple commands execute simultaneously
# 2. No performance degradation under load
# 3. All concurrent operations succeed
# 4. Average execution time remains low

# Expected output:
# PASSED - Concurrent execution: X.XXXs average, XX.X% success rate
```

#### Test Memory Usage Optimization

```bash
# Command:
python -m pytest tests/test_performance_benchmarking.py::TestPerformanceBenchmarking::test_memory_usage_optimization -v -s

# What it tests:
# - Memory efficiency during repeated operations
# - Memory leak detection
# - Garbage collection effectiveness

# Expected behavior:
# 1. Memory usage remains stable during repeated operations
# 2. No significant memory leaks detected
# 3. Garbage collection works effectively
# 4. Memory increase < 50MB for intensive operations

# Expected output:
# PASSED - Memory usage: max X.XMB, avg X.XMB increase
```

### 4. System Integration Tests

#### Test System Health Monitoring

```bash
# Command:
python -m pytest tests/test_final_system_integration.py::TestSystemHealthAndMonitoring::test_system_health_monitoring -v -s

# What it tests:
# - System health status reporting
# - Module availability tracking
# - Error statistics collection

# Expected behavior:
# 1. Health status includes all required fields
# 2. All modules are tracked individually
# 3. Error statistics are collected and reported
# 4. Health check timestamp is updated

# Expected output:
# PASSED - System health monitoring functional
```

#### Test Performance Regression Detection

```bash
# Command:
python -m pytest tests/test_final_system_integration.py::TestSystemHealthAndMonitoring::test_performance_regression_detection -v -s

# What it tests:
# - Automatic detection of performance degradation
# - Baseline comparison functionality
# - Regression threshold enforcement

# Expected behavior:
# 1. Baseline performance is measured
# 2. Simulated regression is detected
# 3. Performance degradation percentage is calculated
# 4. Regression thresholds are enforced

# Expected output:
# PASSED - Regression detection: XX.X% performance degradation
```

### 5. Memory and Stability Tests

#### Test Memory Leak Detection

```bash
# Command:
python -m pytest tests/test_performance_regression.py::TestPerformanceRegression::test_memory_leak_regression -v -s

# What it tests:
# - Memory leak detection over 100 operations
# - Garbage collection effectiveness
# - Long-term memory stability

# Expected behavior:
# 1. 100 operations are performed sequentially
# 2. Memory usage is monitored throughout
# 3. Garbage collection is forced periodically
# 4. Final memory increase is < 50MB

# Expected output:
# PASSED - Memory leak test: X.XMB increase after 100 operations
```

#### Test System Stability Under Load

```bash
# Command:
python -m pytest tests/test_performance_regression.py::TestPerformanceRegression::test_system_stability_under_load -v -s

# What it tests:
# - System stability during sustained load
# - Multi-threaded operation reliability
# - Error handling under stress

# Expected behavior:
# 1. 5 concurrent threads execute 20 commands each
# 2. All operations complete without errors
# 3. Success rate remains > 95%
# 4. Average execution time stays < 2 seconds

# Expected output:
# PASSED - Load test: XXX commands in XX.XXs, XX.X% success rate, X.XXXs avg time
```

## Workflow Testing

### 1. Complete Fast Path Workflow

#### Test Command: GUI Click Operation

```bash
# Test the complete fast path workflow for a click command
python -c "
from orchestrator import Orchestrator
import time

# Initialize orchestrator
orchestrator = Orchestrator()

# Test command
command = 'click the sign in button'

# Execute fast path
start_time = time.time()
result = orchestrator._attempt_fast_path_execution(command, {'command_type': 'gui_interaction'})
execution_time = time.time() - start_time

print(f'Command: {command}')
print(f'Execution Time: {execution_time:.3f}s')
print(f'Success: {result.get(\"success\", False) if result else False}')
print(f'Path Used: {result.get(\"path_used\", \"unknown\") if result else \"failed\"}')
if result and result.get('element_found'):
    print(f'Element Found: {result[\"element_found\"]}')
"

# Expected workflow:
# 1. Command is parsed and identified as GUI interaction
# 2. GUI elements are extracted from command text
# 3. Accessibility API searches for matching element
# 4. Element coordinates are calculated
# 5. Automation module executes the click action
# 6. Result is returned with success status and timing

# Expected output:
# Command: click the sign in button
# Execution Time: 0.XXXs
# Success: True
# Path Used: fast
# Element Found: {'role': 'AXButton', 'title': 'Sign In', ...}
```

#### Test Command: Text Input Operation

```bash
# Test the complete fast path workflow for a type command
python -c "
from orchestrator import Orchestrator
import time

orchestrator = Orchestrator()
command = 'type \"hello world\"'

start_time = time.time()
result = orchestrator._attempt_fast_path_execution(command, {'command_type': 'gui_interaction'})
execution_time = time.time() - start_time

print(f'Command: {command}')
print(f'Execution Time: {execution_time:.3f}s')
print(f'Success: {result.get(\"success\", False) if result else False}')
print(f'Path Used: {result.get(\"path_used\", \"unknown\") if result else \"failed\"}')
"

# Expected workflow:
# 1. Command is parsed as text input operation
# 2. Text content is extracted from command
# 3. Accessibility API finds focused text field
# 4. Automation module types the specified text
# 5. Result confirms successful text input

# Expected output:
# Command: type "hello world"
# Execution Time: 0.XXXs
# Success: True
# Path Used: fast
```

### 2. Fallback Workflow Testing

#### Test Command: Non-Accessible Element

```bash
# Test fallback when element is not accessible
python -c "
from orchestrator import Orchestrator
from unittest.mock import patch

orchestrator = Orchestrator()

# Mock accessibility module to return None (element not found)
with patch.object(orchestrator.accessibility_module, 'find_element_with_vision_preparation', return_value=None):
    result = orchestrator._attempt_fast_path_execution('click the hidden button', {'command_type': 'gui_interaction'})

    print(f'Fast Path Success: {result.get(\"success\", False) if result else False}')
    print(f'Fallback Required: {result.get(\"fallback_required\", False) if result else False}')
    print(f'Failure Reason: {result.get(\"failure_reason\", \"unknown\") if result else \"no result\"}')
"

# Expected workflow:
# 1. Fast path attempts to find element
# 2. Accessibility API returns None (element not accessible)
# 3. Fast path fails gracefully
# 4. Result indicates fallback is required
# 5. Failure reason is documented for debugging

# Expected output:
# Fast Path Success: False
# Fallback Required: True
# Failure Reason: element_not_found
```

### 3. System Health Workflow

#### Test Command: Health Status Check

```bash
# Test complete system health monitoring workflow
python -c "
from orchestrator import Orchestrator

orchestrator = Orchestrator()

# Get comprehensive system health
health = orchestrator.get_system_health()

print('=== SYSTEM HEALTH STATUS ===')
print(f'Overall Health: {health.get(\"overall_health\", \"unknown\")}')
print(f'Health Score: {health.get(\"health_score\", 0)}')
print()

print('Module Health:')
for module, status in health.get('module_health', {}).items():
    print(f'  {module}: {status}')
print()

print('Error Statistics:')
error_stats = health.get('error_statistics', {})
print(f'  Total Errors: {error_stats.get(\"total_errors\", 0)}')
print(f'  Error Rate: {error_stats.get(\"error_rate\", 0)}%')
print()

print('Module Availability:')
for module, available in orchestrator.module_availability.items():
    print(f'  {module}: {\"Available\" if available else \"Unavailable\"}')
"

# Expected workflow:
# 1. System health check is initiated
# 2. All modules are queried for status
# 3. Error statistics are collected
# 4. Overall health score is calculated
# 5. Comprehensive report is generated

# Expected output:
# === SYSTEM HEALTH STATUS ===
# Overall Health: healthy
# Health Score: XX
#
# Module Health:
#   vision: healthy
#   reasoning: healthy
#   automation: healthy
#   audio: healthy
#   feedback: healthy
#   accessibility: healthy
#
# Error Statistics:
#   Total Errors: X
#   Error Rate: X.X%
#
# Module Availability:
#   vision: Available
#   reasoning: Available
#   automation: Available
#   audio: Available
#   feedback: Available
#   accessibility: Available
```

## Performance Testing

### 1. Comprehensive Performance Benchmark

#### Run Complete Performance Suite

```bash
# Command to run all performance benchmarks
python -m pytest tests/test_performance_benchmarking.py -v -s --tb=short

# What this tests:
# - Fast path performance benchmarks
# - Slow path performance benchmarks
# - Performance comparison analysis
# - Concurrent execution performance
# - Memory usage optimization
# - Performance regression detection
# - Comprehensive performance reporting

# Expected duration: 2-5 minutes
# Expected results: All tests PASSED with performance metrics logged
```

#### Individual Performance Tests

**Fast Path Benchmark:**

```bash
python -m pytest tests/test_performance_benchmarking.py::TestPerformanceBenchmarking::test_fast_path_performance_benchmark -v -s

# Expected output:
# PASSED - Fast path benchmark: 0.XXXs average, XX.X% success rate
# Performance requirement: < 2.0 seconds average
# Success rate requirement: ≥ 95%
```

**Slow Path Benchmark:**

```bash
python -m pytest tests/test_performance_benchmarking.py::TestPerformanceBenchmarking::test_slow_path_performance_benchmark -v -s

# Expected output:
# PASSED - Slow path benchmark: X.XXXs average, XX.X% success rate
# Performance requirement: < 10.0 seconds average
# Success rate requirement: ≥ 90%
```

### 2. Performance Comparison Analysis

#### Run Performance Comparison

```bash
# Detailed performance comparison between fast and slow paths
python -c "
from tests.test_performance_benchmarking import PerformanceBenchmarkSuite
import time

# Create benchmark suite
suite = PerformanceBenchmarkSuite()
suite.setup_resource_monitoring()

# Fast path test function
def fast_path_test():
    time.sleep(0.2)  # Simulate fast execution
    return True

# Slow path test function
def slow_path_test():
    time.sleep(3.5)  # Simulate slow execution
    return True

# Run benchmarks
print('Running fast path benchmark...')
fast_results = suite.run_benchmark(fast_path_test, 'comparison_test', 'fast', iterations=10)

print('Running slow path benchmark...')
slow_results = suite.run_benchmark(slow_path_test, 'comparison_test', 'slow', iterations=10)

# Compare results
comparison = suite.compare_performance(fast_results, slow_results)

print()
print('=== PERFORMANCE COMPARISON RESULTS ===')
print(f'Fast Path Average: {comparison.fast_path_avg:.3f}s')
print(f'Slow Path Average: {comparison.slow_path_avg:.3f}s')
print(f'Improvement Factor: {comparison.improvement_factor:.1f}x')
print(f'Improvement Percentage: {comparison.improvement_percent:.1f}%')
print(f'Fast Path Success Rate: {comparison.fast_path_success_rate:.1f}%')
print(f'Slow Path Success Rate: {comparison.slow_path_success_rate:.1f}%')
print(f'Statistical Significance: {comparison.statistical_significance}')
"

# Expected output:
# Running fast path benchmark...
# Running slow path benchmark...
#
# === PERFORMANCE COMPARISON RESULTS ===
# Fast Path Average: 0.2XXs
# Slow Path Average: 3.5XXs
# Improvement Factor: XX.Xx
# Improvement Percentage: XX.X%
# Fast Path Success Rate: 100.0%
# Slow Path Success Rate: 100.0%
# Statistical Significance: True
```

### 3. Resource Usage Analysis

#### Memory Usage Test

```bash
# Test memory usage patterns
python -c "
import psutil
import gc
from orchestrator import Orchestrator

# Get initial memory
process = psutil.Process()
initial_memory = process.memory_info().rss / 1024 / 1024

print(f'Initial Memory: {initial_memory:.1f}MB')

# Create orchestrator and run operations
orchestrator = Orchestrator()

# Simulate multiple operations
for i in range(50):
    result = orchestrator._attempt_fast_path_execution(f'click button {i}', {'command_type': 'gui_interaction'})
    if i % 10 == 0:
        gc.collect()  # Force garbage collection

# Get final memory
final_memory = process.memory_info().rss / 1024 / 1024
memory_increase = final_memory - initial_memory

print(f'Final Memory: {final_memory:.1f}MB')
print(f'Memory Increase: {memory_increase:.1f}MB')
print(f'Memory per Operation: {memory_increase/50:.2f}MB')

# Verify memory efficiency
if memory_increase < 25:
    print('✓ Memory usage is efficient')
else:
    print('⚠ Memory usage may be high')
"

# Expected output:
# Initial Memory: XX.XMB
# Final Memory: XX.XMB
# Memory Increase: X.XMB
# Memory per Operation: 0.XXMB
# ✓ Memory usage is efficient
```

## Integration Testing

### 1. Complete System Integration Test

#### Run Full Integration Suite

```bash
# Run the complete system integration test suite
python run_final_system_tests.py --no-report

# What this does:
# 1. Runs Final System Integration Tests
# 2. Runs Performance Benchmarking Tests
# 3. Runs Hybrid Orchestration Tests
# 4. Runs Accessibility Module Tests
# 5. Generates comprehensive report
# 6. Validates all requirements

# Expected duration: 5-10 minutes
# Expected output: Summary of all test results with pass/fail status
```

#### Individual Integration Tests

**Hybrid Workflow Integration:**

```bash
python -m pytest tests/test_final_system_integration.py::TestHybridWorkflowExecution::test_fast_path_execution_performance -v -s

# Tests complete hybrid workflow execution with performance validation
```

**Fallback Mechanism Integration:**

```bash
python -m pytest tests/test_final_system_integration.py::TestHybridWorkflowExecution::test_fallback_mechanism_reliability -v -s

# Tests reliability of fallback mechanism for complex scenarios
```

**Backward Compatibility Integration:**

```bash
python -m pytest tests/test_final_system_integration.py::TestHybridWorkflowExecution::test_backward_compatibility_preservation -v -s

# Tests that existing AURA functionality is preserved
```

### 2. End-to-End Workflow Test

#### Complete E2E Test

```bash
# Test complete end-to-end workflow
python -c "
from orchestrator import Orchestrator
import time

print('=== END-TO-END WORKFLOW TEST ===')

# Initialize system
orchestrator = Orchestrator()
print('✓ System initialized')

# Check system health
health = orchestrator.get_system_health()
print(f'✓ System health: {health[\"overall_health\"]}')

# Test fast path execution
print()
print('Testing fast path execution...')
commands = [
    'click the submit button',
    'type \"test input\"',
    'scroll down',
    'click the cancel button'
]

for i, command in enumerate(commands, 1):
    print(f'{i}. Testing: {command}')
    start_time = time.time()

    result = orchestrator._attempt_fast_path_execution(command, {'command_type': 'gui_interaction'})

    execution_time = time.time() - start_time
    success = result and result.get('success', False)

    print(f'   Result: {\"✓ SUCCESS\" if success else \"✗ FAILED\"} ({execution_time:.3f}s)')

    if not success and result:
        print(f'   Reason: {result.get(\"failure_reason\", \"unknown\")}')
        print(f'   Fallback: {\"Required\" if result.get(\"fallback_required\") else \"Not needed\"}')

print()
print('✓ End-to-end workflow test completed')
"

# Expected output:
# === END-TO-END WORKFLOW TEST ===
# ✓ System initialized
# ✓ System health: healthy
#
# Testing fast path execution...
# 1. Testing: click the submit button
#    Result: ✓ SUCCESS (0.XXXs)
# 2. Testing: type "test input"
#    Result: ✓ SUCCESS (0.XXXs)
# 3. Testing: scroll down
#    Result: ✓ SUCCESS (0.XXXs)
# 4. Testing: click the cancel button
#    Result: ✓ SUCCESS (0.XXXs)
#
# ✓ End-to-end workflow test completed
```

## Regression Testing

### 1. Performance Regression Suite

#### Run All Regression Tests

```bash
# Run complete performance regression test suite
python -m pytest tests/test_performance_regression.py -v -s --tb=short

# What this tests:
# - Fast path click performance regression
# - Fast path type performance regression
# - Accessibility element detection regression
# - Fallback mechanism performance regression
# - Concurrent execution performance regression
# - Memory leak regression
# - System stability under load

# Expected duration: 3-5 minutes
# Expected results: All regression tests PASSED
```

#### Individual Regression Tests

**Fast Path Performance Regression:**

```bash
python -m pytest tests/test_performance_regression.py::TestPerformanceRegression::test_fast_path_click_performance_regression -v -s

# Validates fast path performance against baseline:
# - Max execution time: < 2.0 seconds
# - Min success rate: > 95%
# - Max memory increase: < 10MB
```

**Memory Leak Regression:**

```bash
python -m pytest tests/test_performance_regression.py::TestPerformanceRegression::test_memory_leak_regression -v -s

# Validates no memory leaks over 100 operations:
# - Memory increase < 50MB total
# - Garbage collection effectiveness
# - Long-term stability
```

**System Stability Regression:**

```bash
python -m pytest tests/test_performance_regression.py::TestPerformanceRegression::test_system_stability_under_load -v -s

# Validates system stability under concurrent load:
# - 5 concurrent threads, 20 commands each
# - Success rate > 95%
# - Average execution time < 2 seconds
# - No errors or exceptions
```

### 2. Continuous Regression Monitoring

#### Set Up Regression Monitoring

```bash
# Create a script for continuous regression monitoring
cat > monitor_performance.py << 'EOF'
#!/usr/bin/env python3
"""
Continuous performance monitoring script
Run this regularly to detect performance regressions
"""

import subprocess
import sys
import time
from datetime import datetime

def run_regression_tests():
    """Run regression tests and return results."""
    print(f"[{datetime.now()}] Starting performance regression tests...")

    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest',
            'tests/test_performance_regression.py',
            '-v', '--tb=short'
        ], capture_output=True, text=True, timeout=300)

        success = result.returncode == 0

        print(f"[{datetime.now()}] Regression tests {'PASSED' if success else 'FAILED'}")

        if not success:
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)

        return success

    except subprocess.TimeoutExpired:
        print(f"[{datetime.now()}] Regression tests TIMED OUT")
        return False
    except Exception as e:
        print(f"[{datetime.now()}] Regression tests ERROR: {e}")
        return False

if __name__ == '__main__':
    # Run regression tests
    success = run_regression_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
EOF

# Make it executable
chmod +x monitor_performance.py

# Run the monitoring script
python monitor_performance.py
```

## Manual Testing Scenarios

### 1. Real Application Testing

#### Test with Finder

```bash
# Test fast path with Finder application
python -c "
from orchestrator import Orchestrator
import subprocess
import time

# Open Finder
subprocess.run(['open', '/System/Library/CoreServices/Finder.app'])
time.sleep(2)  # Wait for Finder to open

orchestrator = Orchestrator()

# Test Finder interactions
commands = [
    'click the Applications folder',
    'click the Documents folder',
    'click the Desktop folder'
]

print('=== FINDER TESTING ===')
for command in commands:
    print(f'Testing: {command}')
    result = orchestrator._attempt_fast_path_execution(command, {'command_type': 'gui_interaction'})

    if result:
        print(f'  Success: {result.get(\"success\", False)}')
        print(f'  Path: {result.get(\"path_used\", \"unknown\")}')
        if result.get('element_found'):
            element = result['element_found']
            print(f'  Element: {element.get(\"role\", \"unknown\")} - {element.get(\"title\", \"unknown\")}')
    else:
        print('  Result: No result returned')
    print()
"
```

#### Test with System Preferences

```bash
# Test fast path with System Preferences
python -c "
from orchestrator import Orchestrator
import subprocess
import time

# Open System Preferences
subprocess.run(['open', '/System/Applications/System Preferences.app'])
time.sleep(3)  # Wait for System Preferences to open

orchestrator = Orchestrator()

# Test System Preferences interactions
commands = [
    'click the Security & Privacy button',
    'click the Privacy tab',
    'click the Accessibility option'
]

print('=== SYSTEM PREFERENCES TESTING ===')
for command in commands:
    print(f'Testing: {command}')
    result = orchestrator._attempt_fast_path_execution(command, {'command_type': 'gui_interaction'})

    if result:
        print(f'  Success: {result.get(\"success\", False)}')
        print(f'  Path: {result.get(\"path_used\", \"unknown\")}')
        if not result.get('success') and result.get('fallback_required'):
            print(f'  Fallback Required: {result.get(\"failure_reason\", \"unknown\")}')
    print()
"
```

### 2. Error Scenario Testing

#### Test Accessibility Permission Denied

```bash
# Simulate accessibility permission denied scenario
python -c "
from orchestrator import Orchestrator
from unittest.mock import patch

orchestrator = Orchestrator()

# Mock accessibility module to simulate permission denied
with patch.object(orchestrator.accessibility_module, 'get_accessibility_status') as mock_status:
    mock_status.return_value = {
        'api_initialized': False,
        'degraded_mode': True,
        'can_attempt_recovery': False,
        'permissions_granted': False
    }

    print('=== PERMISSION DENIED SCENARIO ===')
    result = orchestrator._attempt_fast_path_execution('click the button', {'command_type': 'gui_interaction'})

    print(f'Fast Path Success: {result.get(\"success\", False) if result else False}')
    print(f'Fallback Required: {result.get(\"fallback_required\", False) if result else False}')
    print(f'Failure Reason: {result.get(\"failure_reason\", \"unknown\") if result else \"no result\"}')

    # Test system recovery
    recovery_result = orchestrator.attempt_system_recovery('accessibility')
    print(f'Recovery Attempted: {recovery_result.get(\"recovery_attempted\", False)}')
    print(f'Recovery Successful: {recovery_result.get(\"recovery_successful\", False)}')
"

# Expected output:
# === PERMISSION DENIED SCENARIO ===
# Fast Path Success: False
# Fallback Required: True
# Failure Reason: accessibility_not_initialized
# Recovery Attempted: True
# Recovery Successful: False
```

#### Test Module Failure Recovery

```bash
# Test module failure and recovery scenarios
python -c "
from orchestrator import Orchestrator

orchestrator = Orchestrator()

print('=== MODULE FAILURE RECOVERY TEST ===')

# Test handling of different module failures
modules_to_test = ['vision', 'reasoning', 'automation', 'accessibility']

for module_name in modules_to_test:
    print(f'\\nTesting {module_name} module failure...')

    # Simulate module error
    error = Exception(f'{module_name} module test error')
    result = orchestrator.handle_module_error(module_name, error)

    print(f'  Error Handled: {result.get(\"error_handled\", False)}')
    print(f'  Recovery Attempted: {result.get(\"recovery_attempted\", False)}')
    print(f'  Graceful Degradation: {result.get(\"graceful_degradation\", False)}')

    # Check system health after error
    health = orchestrator.get_system_health()
    print(f'  System Health: {health.get(\"overall_health\", \"unknown\")}')
"

# Expected output:
# === MODULE FAILURE RECOVERY TEST ===
#
# Testing vision module failure...
#   Error Handled: True
#   Recovery Attempted: True/False
#   Graceful Degradation: True
#   System Health: degraded/healthy
#
# [Similar output for other modules...]
```

## Expected Results

### 1. Performance Benchmarks

| Test Category     | Expected Result     | Acceptance Criteria  |
| ----------------- | ------------------- | -------------------- |
| Fast Path Click   | 0.2-0.5 seconds     | < 2.0 seconds        |
| Fast Path Type    | 0.3-0.7 seconds     | < 2.5 seconds        |
| Element Detection | 0.05-0.2 seconds    | < 1.0 second         |
| Fallback Trigger  | 0.1-0.5 seconds     | < 1.0 second         |
| Memory Usage      | < 5MB per operation | < 10MB per operation |
| Success Rate      | > 95%               | > 90% minimum        |

### 2. Performance Improvements

| Comparison   | Fast Path | Slow Path | Improvement  |
| ------------ | --------- | --------- | ------------ |
| Average Time | 0.3s      | 3.5s      | 11.7x faster |
| Best Case    | 0.1s      | 2.8s      | 28x faster   |
| Worst Case   | 0.8s      | 5.2s      | 6.5x faster  |
| Success Rate | 98%       | 92%       | 6% better    |

### 3. System Health Metrics

| Metric              | Expected Value | Status Indicator      |
| ------------------- | -------------- | --------------------- |
| Overall Health      | "healthy"      | Green                 |
| Module Availability | 100%           | All modules available |
| Error Rate          | < 5%           | Low error rate        |
| Recovery Success    | > 80%          | High recovery rate    |
| Memory Stability    | No leaks       | Stable                |
| CPU Usage           | < 50%          | Efficient             |

### 4. Test Coverage Results

| Test Suite               | Tests         | Expected Pass Rate |
| ------------------------ | ------------- | ------------------ |
| System Integration       | 15+ scenarios | 100%               |
| Performance Benchmarking | 8+ benchmarks | 100%               |
| Regression Testing       | 7+ scenarios  | 100%               |
| Hybrid Orchestration     | 20+ tests     | 100%               |
| Accessibility Module     | 30+ tests     | 95%+               |

## Troubleshooting

### Common Issues and Solutions

#### 1. Accessibility Permission Issues

**Problem**: Tests fail with accessibility permission errors

```bash
# Check accessibility status
python -c "
from modules.accessibility import AccessibilityModule
module = AccessibilityModule()
status = module.get_accessibility_status()
print('Permissions Granted:', status.get('permissions_granted', False))
print('API Initialized:', status.get('api_initialized', False))
"
```

**Solution**:

1. Open System Preferences → Security & Privacy → Privacy → Accessibility
2. Add Terminal/IDE to the list
3. Restart Terminal/IDE
4. Re-run tests

#### 2. Module Import Errors

**Problem**: ImportError when running tests

```bash
# Check Python path and module availability
python -c "
import sys
print('Python Path:')
for path in sys.path:
    print(f'  {path}')

print('\\nTrying imports...')
try:
    from orchestrator import Orchestrator
    print('✓ Orchestrator imported')
except ImportError as e:
    print(f'✗ Orchestrator import failed: {e}')
"
```

**Solution**:

```bash
# Set Python path
export PYTHONPATH=$PWD:$PYTHONPATH

# Install missing dependencies
pip install -r requirements.txt
```

#### 3. Performance Test Failures

**Problem**: Performance tests fail due to slow execution

```bash
# Check system resources
python -c "
import psutil
print(f'CPU Usage: {psutil.cpu_percent()}%')
print(f'Memory Usage: {psutil.virtual_memory().percent}%')
print(f'Available Memory: {psutil.virtual_memory().available / 1024 / 1024:.1f}MB')
"
```

**Solution**:

1. Close unnecessary applications
2. Restart system if needed
3. Run tests individually instead of in batch
4. Increase timeout values if necessary

#### 4. Mock Setup Issues

**Problem**: Tests fail due to incorrect mock configuration

```bash
# Verify mock setup
python -c "
from unittest.mock import Mock, patch
from orchestrator import Orchestrator

# Test mock creation
with patch('orchestrator.AccessibilityModule') as mock_class:
    mock_instance = Mock()
    mock_class.return_value = mock_instance

    orchestrator = Orchestrator()
    print('✓ Mock setup successful')
    print(f'Accessibility module type: {type(orchestrator.accessibility_module)}')
"
```

**Solution**:

1. Check mock patch paths are correct
2. Verify mock return values match expected interface
3. Ensure mocks are properly configured before test execution

#### 5. Test Environment Issues

**Problem**: Tests behave inconsistently

```bash
# Check test environment
python -c "
import os
print('Environment Variables:')
for key, value in os.environ.items():
    if 'AURA' in key or 'TEST' in key:
        print(f'  {key}={value}')

print('\\nWorking Directory:', os.getcwd())
print('Test Mode:', os.environ.get('AURA_TEST_MODE', 'Not set'))
"
```

**Solution**:

```bash
# Set proper test environment
export AURA_TEST_MODE=true
export AURA_LOG_LEVEL=DEBUG
export PYTHONPATH=$PWD:$PYTHONPATH

# Run tests from project root directory
cd /path/to/aura/project
```

### Debug Commands

#### Enable Verbose Logging

```bash
# Run tests with maximum verbosity
python -m pytest tests/test_performance_regression.py -v -s --tb=long --log-cli-level=DEBUG
```

#### Check System Dependencies

```bash
# Verify all dependencies
python -c "
import sys
required_packages = ['pytest', 'psutil', 'PIL', 'requests', 'concurrent.futures']

print('Python Version:', sys.version)
print('\\nPackage Check:')
for package in required_packages:
    try:
        __import__(package)
        print(f'✓ {package}')
    except ImportError:
        print(f'✗ {package} - MISSING')
"
```

#### Performance Profiling

```bash
# Profile test execution
python -m cProfile -o profile_output.prof -m pytest tests/test_performance_regression.py::TestPerformanceRegression::test_fast_path_click_performance_regression

# Analyze profile
python -c "
import pstats
stats = pstats.Stats('profile_output.prof')
stats.sort_stats('cumulative').print_stats(10)
"
```

## Conclusion

This comprehensive testing guide provides detailed instructions for validating every aspect of the AURA Hybrid Architecture implementation. By following these commands and workflows, you can thoroughly test:

- **Fast Path Performance**: Validate sub-2-second execution times
- **Fallback Reliability**: Ensure seamless transitions to vision-based processing
- **System Integration**: Verify end-to-end workflow functionality
- **Performance Optimization**: Confirm 7-20x speed improvements
- **Error Recovery**: Test graceful degradation and system resilience
- **Regression Prevention**: Monitor for performance degradation over time

Each test command includes expected outputs and acceptance criteria, making it easy to verify that the system meets all requirements and is ready for production deployment.

The hybrid architecture represents a significant advancement in AURA's capabilities, providing near-instantaneous GUI automation while maintaining the reliability of the existing vision-based approach as a comprehensive fallback mechanism.

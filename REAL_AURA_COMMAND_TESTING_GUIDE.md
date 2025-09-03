# AURA Real Command Testing Guide

## Overview

This guide provides comprehensive instructions for testing AURA with real voice and text commands. AURA supports both voice activation (using wake words) and direct command execution, with the new hybrid architecture providing fast accessibility-based automation and vision-based fallback.

## Table of Contents

1. [Setup and Activation](#setup-and-activation)
2. [Wake Word Commands](#wake-word-commands)
3. [GUI Interaction Commands](#gui-interaction-commands)
4. [Screen Analysis Commands](#screen-analysis-commands)
5. [Form Filling Commands](#form-filling-commands)
6. [Navigation Commands](#navigation-commands)
7. [Application-Specific Commands](#application-specific-commands)
8. [Testing Workflows](#testing-workflows)
9. [Performance Validation](#performance-validation)
10. [Troubleshooting](#troubleshooting)

## Setup and Activation

### 1. Start AURA Application

#### Method 1: Voice-Activated Mode (Recommended)

```bash
# Start AURA with continuous wake word monitoring
python main.py

# Expected output:
# AURA Application initialized - Version X.X.X
# Starting AURA application...
# Step 1: Validating configuration...
# Step 2: Running startup checks...
# Step 3: Initializing core modules...
# Step 4: Verifying module initialization...
# Step 5: Starting health monitoring...
# Step 6: Startup completed successfully
# AURA is ready. Say 'computer' to activate.
```

#### Method 2: Direct Command Mode (For Testing)

```bash
# Start AURA in interactive mode for direct command testing
python -c "
from orchestrator import Orchestrator
import time

print('Initializing AURA for direct command testing...')
orchestrator = Orchestrator()

print('AURA ready for commands!')
print('Enter commands directly or type \"quit\" to exit')
print()

while True:
    try:
        command = input('AURA> ').strip()
        if command.lower() in ['quit', 'exit', 'q']:
            break
        if command:
            print(f'Executing: {command}')
            start_time = time.time()
            result = orchestrator.execute_command(command)
            execution_time = time.time() - start_time
            print(f'Result: {result.get(\"status\", \"unknown\")} ({execution_time:.3f}s)')
            if result.get('errors'):
                print(f'Errors: {result[\"errors\"]}')
            print()
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f'Error: {e}')

print('AURA session ended.')
"
```

### 2. Verify System Status

#### Check System Health

```bash
# Check AURA system health
python -c "
from orchestrator import Orchestrator
orchestrator = Orchestrator()
health = orchestrator.get_system_health()
print('=== AURA SYSTEM STATUS ===')
print(f'Overall Health: {health.get(\"overall_health\", \"unknown\")}')
print(f'Health Score: {health.get(\"health_score\", 0)}/100')
print()
print('Module Status:')
for module, status in health.get('module_health', {}).items():
    print(f'  {module}: {status}')
print()
print('Fast Path Available:', orchestrator.fast_path_enabled)
print('Accessibility Enabled:', orchestrator.accessibility_module.is_accessibility_enabled() if orchestrator.accessibility_module else False)
"
```

## Wake Word Commands

### Default Wake Word: "Computer"

AURA listens for the wake word "computer" by default. After saying the wake word, AURA will provide audio feedback and listen for your command.

#### Basic Wake Word Testing

**Test 1: Simple Wake Word Activation**

```
Say: "Computer"
Expected Response: Audio chime or "Yes?" or "I'm listening"
Then say: "What's on my screen?"
Expected: AURA analyzes and describes the current screen
```

**Test 2: Wake Word + Immediate Command**

```
Say: "Computer, click the Finder icon"
Expected: AURA activates, processes command, clicks Finder icon
```

**Test 3: Wake Word Sensitivity Test**

```
Try variations:
- "Computer" (clear pronunciation)
- "Computer" (whispered)
- "Computer" (with background noise)
- "Hey Computer" (with prefix)
```

## GUI Interaction Commands

### Click Commands (Fast Path Priority)

These commands use the fast accessibility-based path when possible, falling back to vision analysis when needed.

#### Basic Click Commands

```bash
# Test these commands with AURA running:

# Simple element clicks
"click the OK button"
"click the Cancel button"
"click the Submit button"
"press the Enter button"
"tap the Save button"

# Application launches
"click the Finder icon"
"click the Safari icon"
"click the System Preferences icon"
"open the Applications folder"
"launch Terminal"

# Menu interactions
"click the File menu"
"click the Edit menu"
"click the View menu"
"press the Help menu"

# Window controls
"click the close button"
"click the minimize button"
"click the maximize button"
"press the red button"  # Close button
"tap the green button"  # Maximize button
```

#### Advanced Click Commands

```bash
# Specific UI elements
"click the search field"
"click the address bar"
"click the login button"
"press the sign in button"
"tap the create account link"

# Form elements
"click the username field"
"click the password field"
"click the email input"
"press the submit form button"

# Navigation elements
"click the back button"
"click the forward button"
"click the home button"
"press the refresh button"

# Toolbar elements
"click the toolbar"
"press the settings icon"
"tap the preferences button"
```

### Type Commands (Text Input)

#### Basic Text Input

```bash
# Simple text entry
"type 'hello world'"
"enter 'test@example.com'"
"input 'my password'"
"write 'sample text'"

# Special characters
"type 'user@domain.com'"
"enter '123-456-7890'"
"input 'https://example.com'"

# Multi-word text
"type 'This is a longer sentence with spaces'"
"enter 'Multiple words with punctuation!'"
```

#### Form Field Input

```bash
# Specific field targeting
"type 'john.doe@email.com' in the email field"
"enter 'mypassword123' in the password field"
"input 'John Doe' in the name field"

# Sequential form filling
"click the first name field"
"type 'John'"
"click the last name field"
"type 'Doe'"
"click the email field"
"type 'john.doe@email.com'"
```

### Scroll Commands

#### Basic Scrolling

```bash
# Direction-based scrolling
"scroll up"
"scroll down"
"scroll left"
"scroll right"

# Page-based scrolling
"page up"
"page down"

# Amount-based scrolling
"scroll down 5"
"scroll up 3"
"scroll right 2"
```

## Screen Analysis Commands

### Basic Screen Description

#### Simple Analysis

```bash
# General screen description
"what's on my screen?"
"describe the screen"
"tell me what you see"
"analyze the current screen"

# Specific element queries
"what buttons are visible?"
"where is the search field?"
"find the login button"
"locate the menu bar"
```

#### Detailed Analysis

```bash
# Comprehensive screen analysis
"tell me what's on my screen in detail"
"describe my screen in detail"
"give me a detailed description of my screen"
"analyze my screen in detail"

# Element-specific analysis
"describe all the buttons on screen"
"tell me about the form fields"
"analyze the navigation elements"
"explain the menu options"
```

### Interactive Analysis

#### Question-Based Commands

```bash
# What questions
"what is the title of this window?"
"what application is currently open?"
"what options are in the menu?"

# Where questions
"where is the save button?"
"where can I find settings?"
"where is the search box?"

# How questions
"how do I close this window?"
"how can I access preferences?"
"how do I submit this form?"
```

## Form Filling Commands

### Automated Form Completion

#### Simple Form Commands

```bash
# Basic form operations
"fill out the form"
"complete the form"
"submit the form"

# Form field identification
"fill the registration form"
"complete the login form"
"fill out the contact form"
```

#### Step-by-Step Form Filling

```bash
# Sequential form completion
"click the first name field and type 'John'"
"move to the email field and enter 'john@example.com'"
"go to the password field and input 'securepass123'"
"click submit when done"
```

## Navigation Commands

### Window and Application Navigation

#### Application Management

```bash
# Opening applications
"open Finder"
"launch Safari"
"start System Preferences"
"open Terminal"
"launch TextEdit"

# Window management
"close this window"
"minimize the window"
"maximize the current window"
"switch to the next window"
```

#### Browser Navigation

```bash
# Web browser commands
"go back"
"go forward"
"refresh the page"
"reload this page"
"open a new tab"
"close this tab"

# Address bar interaction
"click the address bar"
"type 'google.com' in the address bar"
"navigate to 'apple.com'"
```

## Application-Specific Commands

### Finder Commands

#### File Management

```bash
# Folder navigation
"click the Applications folder"
"open the Documents folder"
"go to the Desktop folder"
"navigate to Downloads"

# File operations
"create a new folder"
"rename this file"
"move to trash"
"copy this file"
```

### Safari Commands

#### Web Browsing

```bash
# Navigation
"click the address bar"
"type 'apple.com'"
"press enter"
"click the search field"
"search for 'weather'"

# Page interaction
"scroll down to see more"
"click the first link"
"go back to previous page"
"bookmark this page"
```

### System Preferences Commands

#### Settings Navigation

```bash
# Main categories
"click Security & Privacy"
"open Network settings"
"go to Display preferences"
"access Sound settings"

# Specific settings
"click the Privacy tab"
"select Accessibility"
"enable screen recording"
"change display resolution"
```

## Testing Workflows

### 1. Complete Application Workflow Test

#### Finder File Management Workflow

```bash
# Start AURA and execute this sequence:

# Step 1: Open Finder
"Computer, open Finder"

# Step 2: Navigate to Applications
"click the Applications folder"

# Step 3: Find an application
"scroll down to see more applications"

# Step 4: Open an application
"click the TextEdit icon"

# Step 5: Verify success
"what's on my screen now?"
```

#### Web Browsing Workflow

```bash
# Complete web browsing test:

# Step 1: Open Safari
"Computer, launch Safari"

# Step 2: Navigate to a website
"click the address bar"
"type 'apple.com'"
"press enter"

# Step 3: Interact with the page
"scroll down"
"what's on my screen?"

# Step 4: Navigate back
"go back"
"close this tab"
```

### 2. Form Filling Workflow Test

#### Registration Form Test

```bash
# Test complete form filling:

# Step 1: Navigate to a form page
"open Safari"
"go to a registration page"

# Step 2: Fill form fields
"click the first name field"
"type 'John'"
"click the last name field"
"type 'Doe'"
"click the email field"
"type 'john.doe@example.com'"

# Step 3: Submit form
"click the submit button"
```

### 3. Multi-Application Workflow

#### Cross-Application Test

```bash
# Test switching between applications:

# Step 1: Open multiple applications
"open Finder"
"launch Safari"
"start TextEdit"

# Step 2: Switch between them
"click the Finder icon in dock"
"switch to Safari"
"go to TextEdit"

# Step 3: Perform actions in each
"type 'Hello World' in TextEdit"
"go to Safari and refresh page"
"create new folder in Finder"
```

## Performance Validation

### 1. Fast Path Performance Testing

#### Speed Test Commands

```bash
# Test fast path execution speed
# These should execute in < 2 seconds each:

"click the Finder icon"          # Should use fast path
"click the Safari icon"          # Should use fast path
"click the System Preferences"   # Should use fast path
"type 'test'"                    # Should use fast path
"scroll down"                    # Should use fast path
```

#### Fallback Testing

```bash
# Test commands that should trigger fallback to vision:

"click the drawing area"         # Complex UI element
"click the custom widget"        # Non-standard element
"interact with the canvas"       # HTML5 canvas element
```

### 2. Performance Monitoring

#### Real-Time Performance Check

```bash
# Monitor performance during command execution
python -c "
from orchestrator import Orchestrator
import time

orchestrator = Orchestrator()

# Test commands with timing
test_commands = [
    'click the Finder icon',
    'type \"hello world\"',
    'scroll down',
    'what\\'s on my screen?'
]

print('=== PERFORMANCE TEST ===')
for cmd in test_commands:
    print(f'Testing: {cmd}')
    start_time = time.time()
    result = orchestrator.execute_command(cmd)
    execution_time = time.time() - start_time

    print(f'  Time: {execution_time:.3f}s')
    print(f'  Status: {result.get(\"status\", \"unknown\")}')

    # Check if fast path was used
    if hasattr(orchestrator, '_last_execution_path'):
        print(f'  Path: {orchestrator._last_execution_path}')
    print()
"
```

## Command Categories and Examples

### 1. GUI Interaction Commands (Fast Path Priority)

#### Click Commands

| Command Pattern   | Example                 | Expected Behavior                            |
| ----------------- | ----------------------- | -------------------------------------------- |
| `click [element]` | `"click the OK button"` | Fast path finds button via accessibility API |
| `press [element]` | `"press the Enter key"` | Fast path executes key press                 |
| `tap [element]`   | `"tap the Save icon"`   | Fast path locates and clicks icon            |

#### Type Commands

| Command Pattern  | Example                    | Expected Behavior               |
| ---------------- | -------------------------- | ------------------------------- |
| `type "[text]"`  | `"type 'hello world'"`     | Fast path inputs text directly  |
| `enter "[text]"` | `"enter 'user@email.com'"` | Fast path types in active field |
| `input "[text]"` | `"input 'password123'"`    | Fast path handles text input    |

#### Scroll Commands

| Command Pattern      | Example         | Expected Behavior                  |
| -------------------- | --------------- | ---------------------------------- |
| `scroll [direction]` | `"scroll down"` | Fast path executes scroll action   |
| `page [direction]`   | `"page up"`     | Fast path performs page navigation |

### 2. Screen Analysis Commands (Vision Path)

#### Basic Analysis

| Command Pattern      | Example                  | Expected Behavior                 |
| -------------------- | ------------------------ | --------------------------------- |
| `what's on [screen]` | `"what's on my screen?"` | Vision analysis of current screen |
| `describe [screen]`  | `"describe the screen"`  | Detailed screen description       |
| `analyze [screen]`   | `"analyze my screen"`    | Comprehensive screen analysis     |

#### Detailed Analysis

| Command Pattern                      | Example      | Expected Behavior               |
| ------------------------------------ | ------------ | ------------------------------- |
| `tell me what's on screen in detail` | Full command | Comprehensive detailed analysis |
| `describe my screen in detail`       | Full command | In-depth screen description     |
| `give me a detailed analysis`        | Full command | Complete screen breakdown       |

### 3. Question Commands (Hybrid Path)

#### Information Queries

| Command Pattern             | Example                       | Expected Behavior             |
| --------------------------- | ----------------------------- | ----------------------------- |
| `what [is/are] [element]?`  | `"what is the title?"`        | Identifies specific elements  |
| `where [is/are] [element]?` | `"where is the save button?"` | Locates elements on screen    |
| `how [do/can] I [action]?`  | `"how do I close this?"`      | Provides interaction guidance |

### 4. Form Commands (Hybrid Path)

#### Form Operations

| Command Pattern   | Example                       | Expected Behavior         |
| ----------------- | ----------------------------- | ------------------------- |
| `fill [form]`     | `"fill out the form"`         | Automated form completion |
| `complete [form]` | `"complete the registration"` | Full form processing      |
| `submit [form]`   | `"submit the form"`           | Form submission           |

## Advanced Testing Scenarios

### 1. Error Recovery Testing

#### Accessibility Permission Test

```bash
# Test behavior when accessibility is disabled
# 1. Disable accessibility permissions in System Preferences
# 2. Try fast path commands:
"click the Finder icon"
# Expected: Graceful fallback to vision path

# 3. Re-enable accessibility permissions
# 4. Try same command:
"click the Finder icon"
# Expected: Fast path recovery and execution
```

#### Network Connectivity Test

```bash
# Test behavior with network issues
# 1. Disconnect from internet
# 2. Try vision-dependent commands:
"what's on my screen in detail"
# Expected: Local processing or graceful degradation

# 3. Reconnect to internet
# 4. Try same command:
"what's on my screen in detail"
# Expected: Full functionality restoration
```

### 2. Stress Testing

#### Rapid Command Sequence

```bash
# Test rapid command execution
python -c "
from orchestrator import Orchestrator
import time

orchestrator = Orchestrator()

commands = [
    'click the Finder icon',
    'scroll down',
    'type \"test\"',
    'scroll up',
    'click the close button'
]

print('=== RAPID COMMAND TEST ===')
start_time = time.time()

for i, cmd in enumerate(commands):
    print(f'{i+1}. {cmd}')
    result = orchestrator.execute_command(cmd)
    print(f'   Status: {result.get(\"status\", \"unknown\")}')

total_time = time.time() - start_time
print(f'Total time: {total_time:.3f}s')
print(f'Average per command: {total_time/len(commands):.3f}s')
"
```

#### Concurrent Command Test

```bash
# Test concurrent command handling
python -c "
from orchestrator import Orchestrator
import threading
import time

orchestrator = Orchestrator()

def execute_command(cmd, thread_id):
    print(f'Thread {thread_id}: Starting {cmd}')
    start_time = time.time()
    result = orchestrator.execute_command(cmd)
    execution_time = time.time() - start_time
    print(f'Thread {thread_id}: Completed {cmd} in {execution_time:.3f}s')

# Create multiple threads
threads = []
commands = [
    'what\\'s on my screen?',
    'click the Finder icon',
    'scroll down'
]

print('=== CONCURRENT COMMAND TEST ===')
for i, cmd in enumerate(commands):
    thread = threading.Thread(target=execute_command, args=(cmd, i+1))
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()

print('All concurrent commands completed')
"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Wake Word Not Detected

```bash
# Test microphone
python -c "
from modules.audio import AudioModule
audio = AudioModule()
test_result = audio.test_microphone(duration=3.0)
print('Microphone Test Results:')
print(f'  Success: {test_result[\"success\"]}')
print(f'  Volume RMS: {test_result[\"volume_rms\"]:.4f}')
print(f'  Peak Volume: {test_result[\"peak_volume\"]:.4f}')
if not test_result['success']:
    print(f'  Error: {test_result[\"error\"]}')
"

# Solutions:
# - Check microphone permissions in System Preferences
# - Adjust microphone volume
# - Speak closer to microphone
# - Reduce background noise
```

#### 2. Commands Not Executing

```bash
# Check system health
python -c "
from orchestrator import Orchestrator
orchestrator = Orchestrator()
health = orchestrator.get_system_health()
print('System Health Check:')
print(f'Overall Health: {health[\"overall_health\"]}')
for module, status in health['module_health'].items():
    if status != 'healthy':
        print(f'Issue with {module}: {status}')
"

# Solutions:
# - Restart AURA application
# - Check accessibility permissions
# - Verify network connectivity for cloud services
# - Check system resources (memory, CPU)
```

#### 3. Slow Performance

```bash
# Performance diagnostics
python -c "
from orchestrator import Orchestrator
import time

orchestrator = Orchestrator()

# Test fast path availability
print('Fast Path Status:')
print(f'  Enabled: {orchestrator.fast_path_enabled}')
if orchestrator.accessibility_module:
    print(f'  Accessibility Available: {orchestrator.accessibility_module.is_accessibility_enabled()}')

# Test command execution speed
test_cmd = 'click the Finder icon'
print(f'\\nTesting command: {test_cmd}')

start_time = time.time()
result = orchestrator.execute_command(test_cmd)
execution_time = time.time() - start_time

print(f'Execution time: {execution_time:.3f}s')
print(f'Status: {result.get(\"status\", \"unknown\")}')

if execution_time > 2.0:
    print('⚠ Performance is slower than expected')
    print('Possible causes:')
    print('- Fast path not available')
    print('- System resource constraints')
    print('- Network latency for cloud services')
else:
    print('✓ Performance is within expected range')
"
```

#### 4. Accessibility Issues

```bash
# Check accessibility permissions
python -c "
from modules.accessibility import AccessibilityModule
module = AccessibilityModule()
status = module.get_accessibility_status()

print('Accessibility Status:')
print(f'  Frameworks Available: {status[\"frameworks_available\"]}')
print(f'  API Initialized: {status[\"api_initialized\"]}')
print(f'  Permissions Granted: {status[\"permissions_granted\"]}')
print(f'  Degraded Mode: {status[\"degraded_mode\"]}')

if not status['permissions_granted']:
    print('\\n⚠ Accessibility permissions required:')
    print('1. Open System Preferences')
    print('2. Go to Security & Privacy > Privacy > Accessibility')
    print('3. Add Terminal (or your IDE) to the list')
    print('4. Ensure the checkbox is checked')
    print('5. Restart AURA')
"
```

## Command Reference Quick Guide

### Essential Commands for Testing

#### Basic Functionality Test

```bash
# Test these commands in order:
1. "what's on my screen?"           # Vision analysis
2. "click the Finder icon"          # Fast path click
3. "type 'hello'"                   # Fast path text input
4. "scroll down"                    # Fast path scroll
5. "describe the screen in detail"  # Detailed vision analysis
```

#### Application Launch Test

```bash
# Test application launching:
1. "open Finder"
2. "launch Safari"
3. "start System Preferences"
4. "open Terminal"
5. "launch TextEdit"
```

#### Form Interaction Test

```bash
# Test form interactions:
1. "click the search field"
2. "type 'test search'"
3. "press enter"
4. "click the username field"
5. "enter 'testuser'"
```

#### Navigation Test

```bash
# Test navigation commands:
1. "scroll up"
2. "scroll down"
3. "page up"
4. "page down"
5. "go back"
```

This comprehensive guide provides everything needed to thoroughly test AURA with real commands, validate the hybrid architecture performance, and ensure all functionality works as expected in real-world scenarios.

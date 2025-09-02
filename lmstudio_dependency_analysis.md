# AURA Commands: LM Studio Dependency Analysis

## Overview

AURA uses LM Studio for **vision analysis** (screen understanding) and Ollama Cloud for **reasoning** (action planning). Here's a breakdown of which commands require which services.

## Commands That REQUIRE LM Studio

### 1. **GUI Interaction Commands** (Vision-Dependent)

These commands need to "see" the screen to find elements:

#### Click/Activation Commands:

```bash
"click on the sign in button"
"press the submit button"
"tap on the menu"
"activate sign in"
"select the dropdown"
"choose the option"
"open the file menu"
```

**Why LM Studio is needed:** Must analyze screen to find button locations and coordinates.

#### Form Filling Commands:

```bash
"fill out the form"
"complete the registration form"
"submit the form"
"enter my email in the email field"
"provide my credentials"
```

**Why LM Studio is needed:** Must identify form fields, their types, and locations.

#### Visual Navigation Commands:

```bash
"scroll to find the save button"
"navigate to the settings menu"
"find the search box"
"look for the download link"
```

**Why LM Studio is needed:** Must analyze screen content to determine navigation strategy.

#### Context-Aware Commands:

```bash
"complete this task" (needs to see what "this" refers to)
"fix this error" (needs to see the error message)
"continue from here" (needs to understand current state)
```

**Why LM Studio is needed:** Requires visual context understanding.

### 2. **Screen Analysis Commands** (Vision-Dependent)

These commands explicitly ask about screen content:

#### Basic Screen Questions:

```bash
"what's on my screen?"
"describe what you see"
"what buttons are available?"
"what options do I have?"
```

#### Detailed Analysis:

```bash
"tell me what's on my screen in detail"
"analyze this screen in detail"
"give me a detailed description"
"examine this interface"
```

#### Specific Element Questions:

```bash
"where is the save button?"
"what does this error message say?"
"what's in this dialog box?"
"describe this form"
```

#### Troubleshooting Questions:

```bash
"what's wrong with this page?"
"why can't I submit this form?"
"what's causing this error?"
"help me understand this interface"
```

## Commands That DO NOT Require LM Studio

### 1. **Blind Automation Commands** (Coordinate-Based)

These work with predefined coordinates or keyboard shortcuts:

#### Direct Coordinate Actions:

```bash
"click at coordinates 500, 300"
"move mouse to 100, 200"
"right click at 400, 500"
```

**Why no LM Studio needed:** Uses exact coordinates, no vision required.

#### Keyboard-Only Commands:

```bash
"press enter"
"press escape"
"press ctrl+c"
"press cmd+s"
"type 'hello world'"
"press tab 3 times"
```

**Why no LM Studio needed:** Pure keyboard input, no screen analysis required.

#### System-Level Commands:

```bash
"press cmd+space" (open Spotlight on macOS)
"press alt+tab" (switch applications)
"press cmd+q" (quit application)
"press f11" (fullscreen toggle)
```

### 2. **Text-Only Input Commands** (No Visual Context)

When you know exactly what to type:

```bash
"type 'john.doe@email.com'"
"enter 'password123'"
"write 'Hello, this is a test message'"
"input 'My Name Here'"
```

**Why no LM Studio needed:** Direct text input without field identification.

### 3. **Simple Navigation Commands** (Direction-Based)

Basic directional movements:

```bash
"scroll down"
"scroll up 5 times"
"page down"
"scroll left"
"move cursor up"
"go back" (browser back button via keyboard)
```

**Why no LM Studio needed:** Uses standard scroll/navigation without needing to see content.

### 4. **Audio-Only Commands** (TTS Responses)

Commands that only require speech output:

```bash
"tell me the time"
"what's the date today?"
"read me the weather" (if data is available)
"say hello"
"speak the last message"
```

**Why no LM Studio needed:** Pure text-to-speech, no visual analysis.

### 5. **System Information Commands**

Commands about AURA itself or system status:

```bash
"what can you do?"
"help me with commands"
"what's your status?"
"are you working properly?"
"test your microphone"
"check your systems"
```

## Hybrid Commands (Partial LM Studio Dependency)

### 1. **Smart Fallback Commands**

These try vision first, fall back to alternatives:

```bash
"submit this form"
→ Tries to find submit button visually
→ Falls back to pressing Enter if vision fails

"go back"
→ Tries to find back button visually
→ Falls back to browser back shortcut (cmd+←)

"save this"
→ Tries to find save button visually
→ Falls back to save shortcut (cmd+s)
```

### 2. **Context-Adaptive Commands**

Behavior changes based on whether vision is available:

```bash
"complete this task"
→ With LM Studio: Analyzes screen and completes specific task
→ Without LM Studio: Asks user to be more specific

"navigate forward"
→ With LM Studio: Finds next button or appropriate navigation
→ Without LM Studio: Uses arrow keys or page down
```

## Graceful Degradation Strategy

### When LM Studio is Unavailable:

#### 1. **Inform User of Limitations**

```bash
User: "click on the sign in button"
AURA: "I can't see your screen right now. Please either:
       - Provide coordinates: 'click at 400, 300'
       - Use keyboard: 'press tab to navigate, then press enter'
       - Tell me the exact location: 'click on the top right corner'"
```

#### 2. **Suggest Alternative Commands**

```bash
User: "fill out the form"
AURA: "I can't analyze the form visually. Try:
       - 'press tab' to navigate between fields
       - 'type [text]' to enter specific information
       - 'press enter' to submit when ready"
```

#### 3. **Offer Keyboard-Based Workflows**

```bash
User: "find the save button"
AURA: "I can't see the screen. Try these common save shortcuts:
       - 'press cmd+s' (macOS)
       - 'press ctrl+s' (Windows/Linux)
       - 'press alt+f then s' (File menu → Save)"
```

## Configuration for LM Studio Dependency

### In `config.py`, add:

```python
# LM Studio dependency configuration
VISION_REQUIRED_COMMANDS = [
    'click', 'press', 'tap', 'activate', 'select', 'choose',
    'fill', 'complete', 'submit', 'find', 'locate',
    'what', 'where', 'describe', 'analyze', 'examine',
    'show', 'tell', 'explain', 'help'
]

VISION_OPTIONAL_COMMANDS = [
    'scroll', 'navigate', 'move', 'go', 'save', 'back', 'forward'
]

VISION_INDEPENDENT_COMMANDS = [
    'type', 'enter', 'input', 'write', 'press enter', 'press escape',
    'press tab', 'coordinates', 'keyboard shortcuts'
]

# Fallback strategies when vision is unavailable
VISION_FALLBACK_ENABLED = True
SUGGEST_ALTERNATIVES = True
KEYBOARD_WORKFLOW_HINTS = True
```

## Testing LM Studio Dependency

### Test Script Example:

```python
def test_lmstudio_dependency():
    """Test which commands work with/without LM Studio"""

    # Commands that should work WITHOUT LM Studio
    no_vision_commands = [
        "type 'hello world'",
        "press enter",
        "scroll down",
        "click at coordinates 500, 300",
        "press cmd+s"
    ]

    # Commands that REQUIRE LM Studio
    vision_required_commands = [
        "click on the sign in button",
        "what's on my screen?",
        "fill out the form",
        "find the save button"
    ]

    # Test with LM Studio disconnected
    print("Testing commands without LM Studio...")
    for cmd in no_vision_commands:
        result = test_command_without_vision(cmd)
        print(f"  {cmd}: {'✅ Works' if result else '❌ Fails'}")

    # Test vision-required commands (should gracefully degrade)
    for cmd in vision_required_commands:
        result = test_command_without_vision(cmd)
        print(f"  {cmd}: {'✅ Graceful fallback' if result else '❌ Hard failure'}")
```

## Summary

### **LM Studio Required (Vision-Dependent):**

- **GUI Interactions**: Click, tap, select buttons/elements
- **Form Operations**: Fill forms, find fields
- **Screen Analysis**: "What's on screen?", describe interface
- **Context-Aware Tasks**: "Complete this", "fix this error"
- **Visual Navigation**: Find specific elements

### **LM Studio NOT Required (Vision-Independent):**

- **Keyboard Shortcuts**: Ctrl+C, Cmd+S, Enter, Escape
- **Direct Coordinates**: "Click at 500, 300"
- **Text Input**: Type specific text without field targeting
- **Basic Navigation**: Scroll up/down, page navigation
- **System Commands**: Application switching, system shortcuts

### **Hybrid (Graceful Degradation):**

- **Smart Commands**: Try vision first, fall back to keyboard
- **Context-Adaptive**: Behavior changes based on vision availability
- **User Guidance**: Suggest alternatives when vision unavailable

This analysis helps users understand AURA's capabilities and limitations, and provides clear guidance on which commands will work in different scenarios.

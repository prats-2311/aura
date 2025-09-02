# AURA Command Reference by LM Studio Dependency

## 🟢 Commands That Work WITHOUT LM Studio

### Keyboard Shortcuts (Always Available)

```bash
# System shortcuts
"press cmd+space"          # Open Spotlight (macOS)
"press alt+tab"            # Switch applications
"press cmd+q"              # Quit current application
"press f11"                # Toggle fullscreen

# Text editing shortcuts
"press cmd+c"              # Copy
"press cmd+v"              # Paste
"press cmd+z"              # Undo
"press cmd+s"              # Save
"press cmd+a"              # Select all

# Navigation shortcuts
"press enter"              # Confirm/Submit
"press escape"             # Cancel/Close
"press tab"                # Next field
"press shift+tab"          # Previous field
"press arrow up"           # Move up
"press arrow down"         # Move down
```

### Direct Text Input

```bash
"type 'hello world'"       # Type exact text
"enter 'john@email.com'"   # Enter email
"input 'password123'"      # Input password
"write 'Dear Sir'"         # Write text
```

### Coordinate-Based Actions

```bash
"click at coordinates 500, 300"     # Click exact position
"double click at 400, 200"         # Double-click position
"right click at 600, 400"          # Right-click position
"move mouse to 100, 150"           # Move cursor
```

### Basic Navigation

```bash
"scroll down"              # Scroll down
"scroll up"                # Scroll up
"scroll left"              # Scroll left
"scroll right"             # Scroll right
"page down"                # Page down
"page up"                  # Page up
"scroll down 5"            # Scroll down 5 times
```

### Audio/System Commands

```bash
"what time is it?"         # Current time
"what's the date?"         # Current date
"test microphone"          # Test audio input
"check system status"      # AURA system status
"help with commands"       # Command help
```

## 🔴 Commands That REQUIRE LM Studio

### GUI Element Interaction

```bash
# Button interactions
"click on the sign in button"      # Find and click button
"press the submit button"          # Find and press button
"tap on the menu icon"             # Find and tap element
"activate the search box"          # Find and activate element

# Menu and navigation
"open the file menu"               # Find and open menu
"select settings from menu"        # Navigate menu options
"choose the save option"           # Select menu item
"access the preferences"           # Find preferences

# Links and elements
"click on the download link"       # Find and click link
"select the dropdown menu"         # Find dropdown
"choose option from list"          # Select from options
"activate the checkbox"            # Find and toggle checkbox
```

### Form Operations

```bash
# Form filling
"fill out the form"                # Analyze and fill form
"complete the registration"        # Complete registration form
"submit the contact form"          # Find and submit form
"enter email in email field"      # Find specific field

# Field interactions
"click on the name field"          # Find name input
"select the country dropdown"      # Find country selector
"check the terms checkbox"         # Find terms checkbox
"focus on the password field"      # Find password input
```

### Screen Analysis

```bash
# Basic screen questions
"what's on my screen?"             # Describe current screen
"what buttons are available?"      # List available buttons
"what options do I have?"          # Show available options
"describe this interface"          # Analyze interface

# Detailed analysis
"tell me what's on screen in detail"    # Comprehensive analysis
"analyze this screen thoroughly"        # Detailed examination
"give me a complete description"        # Full screen breakdown
"examine this page carefully"           # Thorough inspection

# Specific element questions
"where is the save button?"        # Locate specific element
"what does this error say?"        # Read error messages
"describe this dialog box"         # Analyze dialog
"what's in this form?"            # Analyze form structure
```

### Context-Aware Tasks

```bash
# Smart completion
"complete this task"               # Context-aware completion
"finish what I'm doing"            # Complete current activity
"submit this"                      # Submit current form/task
"save this work"                   # Save current document/work

# Problem solving
"fix this error"                   # Analyze and fix errors
"help me with this problem"        # Context-aware assistance
"what's wrong here?"              # Diagnose issues
"how do I proceed?"               # Next steps guidance
```

### Visual Navigation

```bash
# Element finding
"find the search box"              # Locate search functionality
"look for the download button"     # Find download option
"locate the settings menu"         # Find settings access
"search for the login area"        # Find login section

# Content navigation
"scroll to find more options"      # Scroll with purpose
"navigate to the bottom"           # Go to page bottom
"find the next page button"        # Locate pagination
"look for additional content"      # Search for more content
```

## 🟡 Hybrid Commands (Try Vision, Fall Back to Keyboard)

### Smart Shortcuts

```bash
# These try to find elements visually first, then use keyboard shortcuts
"save this"
→ With vision: Finds save button and clicks
→ Without vision: Uses Cmd+S shortcut

"go back"
→ With vision: Finds back button and clicks
→ Without vision: Uses browser back (Cmd+←)

"submit form"
→ With vision: Finds submit button and clicks
→ Without vision: Tries Enter key

"close this"
→ With vision: Finds close button and clicks
→ Without vision: Uses Escape or Cmd+W

"copy this"
→ With vision: Finds and selects content, then copies
→ Without vision: Uses Cmd+A then Cmd+C
```

### Adaptive Navigation

```bash
"navigate forward"
→ With vision: Finds next/forward button
→ Without vision: Uses arrow keys or page down

"go to next field"
→ With vision: Finds next input field
→ Without vision: Uses Tab key

"move to top"
→ With vision: Finds top navigation or scroll to top
→ Without vision: Uses Cmd+Home or Cmd+↑
```

## 🚨 What Happens When LM Studio is Down?

### Graceful Degradation Examples:

#### User Command: "click on the sign in button"

**AURA Response:**

```
"I can't see your screen right now because my vision system is unavailable.
Here are some alternatives:

1. Use keyboard navigation: 'press tab' to move between elements, then 'press enter'
2. If you know the location: 'click at coordinates X, Y'
3. Try a keyboard shortcut if this is a login form: 'press enter' might work
4. Tell me more specifically where it is: 'click in the top right corner'"
```

#### User Command: "fill out the form"

**AURA Response:**

```
"I can't analyze the form visually right now. Try these approaches:

1. Navigate with keyboard: 'press tab' to move between fields
2. Enter data directly: 'type your-email@domain.com' then 'press tab'
3. Use common shortcuts: 'press enter' to submit when ready
4. Tell me about the form structure and I can guide you through it"
```

#### User Command: "what's on my screen?"

**AURA Response:**

```
"My vision system is currently unavailable, so I can't see your screen.
I can still help you with:

1. Keyboard shortcuts and navigation
2. Typing specific text
3. Using coordinates if you can provide them
4. General computer tasks that don't require vision

Would you like help with any of these alternatives?"
```

## 🛠️ Troubleshooting Commands by Dependency

### When LM Studio is Working:

```bash
"diagnose this error message"      # Can read and analyze errors
"help me understand this interface" # Can analyze UI elements
"what should I click next?"        # Can provide visual guidance
"is this form filled correctly?"   # Can validate form completion
```

### When LM Studio is Down:

```bash
"test my keyboard shortcuts"       # Test keyboard functionality
"help me navigate with keyboard"   # Keyboard navigation guide
"what shortcuts work here?"        # Context-appropriate shortcuts
"guide me through this step by step" # Verbal guidance without vision
```

## 📋 Quick Reference Summary

| Command Type           | LM Studio Required | Example             | Fallback Available |
| ---------------------- | ------------------ | ------------------- | ------------------ |
| **Button Clicks**      | ✅ Yes             | "click sign in"     | ❌ No              |
| **Keyboard Shortcuts** | ❌ No              | "press cmd+s"       | N/A                |
| **Text Input**         | ❌ No              | "type 'hello'"      | N/A                |
| **Coordinates**        | ❌ No              | "click at 500,300"  | N/A                |
| **Screen Analysis**    | ✅ Yes             | "what's on screen?" | ❌ No              |
| **Form Filling**       | ✅ Yes             | "fill out form"     | ⚠️ Partial         |
| **Smart Navigation**   | ⚠️ Hybrid          | "save this"         | ✅ Yes             |
| **Basic Scrolling**    | ❌ No              | "scroll down"       | N/A                |
| **System Commands**    | ❌ No              | "press alt+tab"     | N/A                |

### Legend:

- ✅ **Required**: Command cannot work without LM Studio
- ❌ **Not Required**: Command works independently
- ⚠️ **Hybrid**: Tries vision first, falls back to alternatives

This reference helps users choose the right commands based on their current system status and needs.

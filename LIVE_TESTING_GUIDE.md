# Live Testing Guide: Explain Selected Text Feature

## Overview

This guide shows you how to test the explain selected text feature with real voice commands in the live AURA application, and how to monitor the performance optimizations we implemented.

## Prerequisites

### 1. Start AURA Application

```bash
# Make sure you're in the aura conda environment
conda activate aura

# Start AURA
python main.py
```

### 2. Ensure Accessibility Permissions

- Go to **System Preferences > Security & Privacy > Privacy > Accessibility**
- Make sure your terminal application (Terminal.app or iTerm2) is checked
- If AURA is running from an IDE, make sure that IDE has accessibility permissions too

## Voice Commands to Test

### Basic Explain Commands

Here are the voice commands you can say to AURA to test the explain selected text feature:

#### Primary Commands:

1. **"Explain this"** - Most common command
2. **"Explain the selected text"** - Explicit command
3. **"What does this mean?"** - Natural language variant
4. **"Tell me about this"** - Conversational variant
5. **"Define this"** - For definitions
6. **"Summarize this"** - For summaries

#### Context-Specific Commands:

1. **"Explain this code"** - For code snippets
2. **"What does this function do?"** - For programming
3. **"Break this down"** - For complex text
4. **"Simplify this"** - For technical content

## Step-by-Step Testing Process

### Test 1: Basic Text Explanation

1. **Open any text application** (TextEdit, Safari, Chrome, etc.)
2. **Select some text** by highlighting it with your mouse
3. **Say the wake word**: "Computer" (or your configured wake word)
4. **Give the command**: "Explain this"
5. **Listen for the response** - AURA should speak the explanation

### Test 2: Code Explanation

1. **Open a code editor** (VS Code, Xcode, etc.)
2. **Select a code snippet** (function, class, or code block)
3. **Say**: "Computer, explain this code"
4. **Listen for technical explanation**

### Test 3: Web Content Explanation

1. **Open a web browser** (Safari, Chrome, Firefox)
2. **Navigate to any article or webpage**
3. **Select a paragraph or sentence**
4. **Say**: "Computer, what does this mean?"
5. **Listen for contextual explanation**

### Test 4: PDF Content Explanation

1. **Open a PDF** (Preview, Adobe Reader, etc.)
2. **Select text from the PDF**
3. **Say**: "Computer, explain the selected text"
4. **Listen for explanation**

## Expected Behavior

### Successful Operation:

1. **Thinking Sound**: You should hear a brief "thinking" sound
2. **Processing**: AURA captures the selected text
3. **Explanation**: AURA speaks a clear, conversational explanation
4. **Completion**: Ready for next command

### Performance Indicators:

- **Fast Response**: Text capture should be < 500ms
- **Quick Explanation**: Total response < 5 seconds
- **High Success Rate**: Should work 95%+ of the time
- **Cache Benefits**: Repeated similar text should be faster

## Monitoring Performance (New Feature!)

### Real-Time Performance Monitoring

The performance monitoring system we implemented will automatically track:

1. **Text Capture Speed**: How fast AURA captures your selected text
2. **Explanation Generation Time**: How long it takes to generate explanations
3. **Success Rates**: How often the feature works correctly
4. **Cache Effectiveness**: How often cached results speed up responses

### Viewing Performance Data

To see the performance metrics in real-time, you can run this command in a separate terminal:

```bash
# In a new terminal window (while AURA is running)
python -c "
from modules.performance_monitor import get_performance_monitor
import time

monitor = get_performance_monitor()
print('🔍 AURA Performance Monitor - Live Stats')
print('=' * 50)

while True:
    try:
        summary = monitor.get_performance_summary()
        text_stats = monitor.get_operation_stats('text_capture')
        explanation_stats = monitor.get_operation_stats('explanation_generation')

        print(f'\\n📊 Live Performance Stats:')
        print(f'Total Operations: {summary.get(\"total_operations\", 0)}')
        print(f'Success Rate: {summary.get(\"success_rate\", 0):.1%}')
        print(f'Avg Duration: {summary.get(\"avg_duration_ms\", 0):.1f}ms')

        if text_stats:
            print(f'Text Capture: {text_stats[\"count\"]} ops, {text_stats[\"avg_duration_ms\"]:.1f}ms avg')
        if explanation_stats:
            print(f'Explanations: {explanation_stats[\"count\"]} ops, {explanation_stats[\"avg_duration_ms\"]:.1f}ms avg')

        time.sleep(5)  # Update every 5 seconds
    except KeyboardInterrupt:
        print('\\n👋 Monitoring stopped')
        break
    except Exception as e:
        print(f'Error: {e}')
        break
"
```

## Troubleshooting Common Issues

### Issue 1: "No text selected" Error

**Symptoms**: AURA says "I couldn't find any selected text"
**Solutions**:

1. Make sure text is actually highlighted (blue/selected)
2. Try selecting text again
3. Try in a different application
4. Check accessibility permissions

### Issue 2: Slow Response

**Symptoms**: Takes more than 5 seconds to respond
**Solutions**:

1. Check internet connection (for reasoning API)
2. Try with shorter text selections
3. Check performance monitor for bottlenecks

### Issue 3: Explanation Quality Issues

**Symptoms**: Poor or irrelevant explanations
**Solutions**:

1. Try more specific commands ("explain this code" vs "explain this")
2. Select more complete text (full sentences/paragraphs)
3. Provide context in your command

### Issue 4: Accessibility Permission Errors

**Symptoms**: "Accessibility permissions required" error
**Solutions**:

1. Go to System Preferences > Security & Privacy > Privacy > Accessibility
2. Add your terminal application or IDE
3. Restart AURA after granting permissions

## Performance Testing Scenarios

### Scenario 1: Speed Test

1. Select the same text multiple times
2. Use "explain this" command repeatedly
3. **Expected**: Second and subsequent requests should be faster (cache hit)

### Scenario 2: Different Applications Test

1. Test in Safari, Chrome, TextEdit, VS Code
2. Use same command in each app
3. **Expected**: Consistent performance across apps

### Scenario 3: Text Length Test

1. Test with short text (1 sentence)
2. Test with medium text (1 paragraph)
3. Test with long text (multiple paragraphs)
4. **Expected**: Longer text takes more time but stays under 5 seconds

### Scenario 4: Content Type Test

1. Test with regular text
2. Test with code snippets
3. Test with technical documentation
4. Test with foreign language text
5. **Expected**: Different content types get appropriate explanations

## Advanced Testing Commands

### Performance-Specific Commands:

- **"Computer, explain this quickly"** - Tests speed optimization
- **"Computer, explain this code in detail"** - Tests complex explanations
- **"Computer, what's the main point of this?"** - Tests summarization

### Fallback Testing:

- Try commands when no text is selected (should give helpful error)
- Try with very long text selections (should handle gracefully)
- Try with special characters or formatting (should work correctly)

## Success Metrics

### What Good Performance Looks Like:

- **Text Capture**: < 500ms consistently
- **Total Response Time**: < 5 seconds for most explanations
- **Success Rate**: > 95% of commands work correctly
- **Cache Hit Rate**: > 30% for repeated similar content
- **User Experience**: Smooth, natural interaction

### Performance Alerts to Watch For:

The system will automatically log warnings if:

- Operations take longer than 1.5 seconds (warning)
- Operations take longer than 3 seconds (critical)
- Success rate drops below expected levels
- Cache performance degrades

## Logging and Debugging

### Check AURA Logs:

```bash
# View recent logs
tail -f aura.log

# Search for explain-related logs
grep -i "explain" aura.log

# Search for performance logs
grep -i "performance" aura.log
```

### Enable Debug Mode:

```bash
# Set debug environment variable
export AURA_DEBUG=true

# Run AURA with debug logging
python main.py
```

## Real-World Testing Scenarios

### Scenario 1: Academic Paper

1. Open a research paper PDF
2. Select abstract or conclusion
3. Say: "Computer, summarize this"
4. **Expected**: Clear, accessible summary

### Scenario 2: Code Review

1. Open GitHub or code editor
2. Select a function or class
3. Say: "Computer, explain this code"
4. **Expected**: Technical explanation of functionality

### Scenario 3: News Article

1. Open news website
2. Select headline or paragraph
3. Say: "Computer, what does this mean?"
4. **Expected**: Contextual explanation

### Scenario 4: Technical Documentation

1. Open API docs or manual
2. Select technical description
3. Say: "Computer, break this down"
4. **Expected**: Simplified explanation

## Conclusion

The explain selected text feature should now work seamlessly across all macOS applications with significantly improved performance thanks to the monitoring and caching systems we implemented.

**Key Testing Points**:

1. ✅ Works across different applications
2. ✅ Fast response times (< 5 seconds)
3. ✅ High success rate (> 95%)
4. ✅ Intelligent caching for repeated content
5. ✅ Real-time performance monitoring
6. ✅ Automatic optimization recommendations

If you encounter any issues during testing, the performance monitoring system will help identify bottlenecks and provide optimization suggestions automatically!

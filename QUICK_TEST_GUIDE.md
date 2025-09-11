# Quick Test Guide: Explain Selected Text Feature

## ✅ AURA is Ready!

The performance monitoring system has been successfully integrated and AURA is ready to test.

## 🚀 How to Test the Explain Selected Text Feature

### Step 1: Start AURA

```bash
# Make sure you're in the aura conda environment
conda activate aura

# Start AURA with performance monitoring
python main.py --performance
```

### Step 2: Test Voice Commands

#### Basic Commands to Try:

1. **"Computer, explain this"** ← Primary command
2. **"Computer, what does this mean?"**
3. **"Computer, explain the selected text"**
4. **"Computer, tell me about this"**
5. **"Computer, define this"**

#### For Code:

- **"Computer, explain this code"**
- **"Computer, what does this function do?"**

### Step 3: Testing Process

1. **Open any application** (Safari, Chrome, TextEdit, VS Code, etc.)
2. **Select/highlight text** with your mouse (make sure it's blue/highlighted)
3. **Say the wake word**: "Computer"
4. **Wait for the beep** (indicates AURA is listening)
5. **Give your command**: "Explain this"
6. **Listen for the explanation**

### Step 4: Test Different Scenarios

#### Scenario 1: Web Article

- Open Safari/Chrome → Go to Wikipedia or news site
- Select a paragraph → Say: "Computer, what does this mean?"

#### Scenario 2: Code Snippet

- Open VS Code → Select a function
- Say: "Computer, explain this code"

#### Scenario 3: PDF Document

- Open a PDF in Preview → Select text
- Say: "Computer, explain the selected text"

## 📊 Performance Monitoring (NEW!)

The system now automatically tracks:

- **Text capture speed** (target: < 500ms)
- **Explanation generation time** (target: < 5 seconds)
- **Success rates** (target: > 95%)
- **Cache effectiveness** (improves with repeated use)

### View Live Performance Stats:

```bash
# In a separate terminal while AURA is running
python -c "
from modules.performance_monitor import get_performance_monitor
monitor = get_performance_monitor()
summary = monitor.get_performance_summary()
print(f'Operations: {summary.get(\"total_operations\", 0)}')
print(f'Success Rate: {summary.get(\"success_rate\", 0):.1%}')
print(f'Average Speed: {summary.get(\"avg_duration_ms\", 0):.1f}ms')
"
```

## ✅ Expected Results

### Good Performance:

- **Immediate response**: Thinking sound plays right away
- **Fast text capture**: < 500ms
- **Quick explanation**: Total response < 5 seconds
- **High success rate**: Works 95%+ of the time
- **Caching benefits**: Repeated similar text is faster

### What You'll Hear:

1. **"Computer"** → Beep sound (AURA is listening)
2. **"Explain this"** → Brief thinking sound
3. **Processing** → AURA captures selected text
4. **Explanation** → Clear spoken explanation
5. **Ready** → AURA is ready for next command

## 🔧 Troubleshooting

### "No text selected" Error:

- Make sure text is highlighted (blue/selected)
- Try selecting text again
- Check accessibility permissions

### Slow Response:

- Check internet connection
- Try shorter text selections
- Monitor performance logs

### Permission Issues:

- Go to **System Preferences > Security & Privacy > Privacy > Accessibility**
- Add **Terminal.app** (or your IDE)
- Restart AURA

## 🎯 Test Commands Summary

| Command                | Use Case       | Example             |
| ---------------------- | -------------- | ------------------- |
| "Explain this"         | General text   | Any selected text   |
| "What does this mean?" | Clarification  | Complex paragraphs  |
| "Explain this code"    | Programming    | Code snippets       |
| "Define this"          | Definitions    | Technical terms     |
| "Summarize this"       | Long text      | Articles, documents |
| "Tell me about this"   | Conversational | Any content         |

## 🚀 Performance Features (NEW!)

The explain selected text feature now includes:

- ✅ **Smart Caching**: Repeated explanations are faster
- ✅ **Real-time Monitoring**: Performance tracked automatically
- ✅ **Automatic Optimization**: System self-tunes for better performance
- ✅ **Fallback Mechanisms**: Multiple methods ensure high reliability
- ✅ **Performance Alerts**: Warns if operations are slow

## 🎉 Ready to Test!

AURA is now ready with the enhanced explain selected text feature. The performance monitoring system will automatically track and optimize the experience as you use it.

**Start testing now**: Select some text anywhere and say "Computer, explain this"!

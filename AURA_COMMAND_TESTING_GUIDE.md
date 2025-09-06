# AURA Command Testing Guide 🧪

## 🎯 **How to Use This Guide**

1. **Start AURA**: Run `python main.py` in your terminal
2. **Say "computer"**: Wait for the wake word detection
3. **Give Commands**: Try the commands below one by one
4. **Fill Feedback**: Use the feedback boxes to note what works/doesn't work
5. **Report Issues**: Document any problems for debugging

---

## 📋 **Command Categories**

### 🤖 **1. DEFERRED ACTION COMMANDS (Content Generation)**

_These commands generate content and wait for you to click where you want it placed_

#### **Code Generation Commands**

```
"Write me a Python function for fibonacci sequence"
```

**Expected**: Generates Python code, waits for click, types formatted code
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

it is working but the format is not current, the typed code is enclosed within ####. ###def fibonacci(n): if n <= 0: return [] if n == 1: return [0] seq = [0, 1] while len(seq) < n: seq.append(seq[-1] + seq[-2]) redef fibonacci(n):
if n <= 0:
return []
if n == 1:
return [0]
seq = [0, 1]
while len(seq) < n:
seq.append(seq[-1] + seq[-2])
return seq###

```
"Write me a JavaScript function to sort an array"
```

**Expected**: Generates JS code, waits for click, types formatted code
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Create a Python class for a calculator"
```

**Expected**: Generates class code, waits for click, types formatted code
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

#### **Text Generation Commands**

```
"Write me a small essay on climate change"
```

**Expected**: Generates essay text, waits for click, types formatted text
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Write me a professional email about project updates"
```

**Expected**: Generates email text, waits for click, types formatted text
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Create a list of 10 productivity tips"
```

**Expected**: Generates list, waits for click, types formatted list
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

#### **Concurrent Deferred Actions Test**

```
1. Say: "Write me a Python function for fibonacci"
2. Wait for "click where you want it placed"
3. Immediately say "computer" again (don't click yet)
4. Say: "Write me a small essay on AI"
5. Both should work without hanging
```

**Expected**: Second command processes while first waits for click
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

---

### 🖱️ **2. GUI INTERACTION COMMANDS**

_These commands interact with your screen elements_

#### **Click Commands**

```
"Click on the sign in button"
```

**Expected**: Analyzes screen, finds and clicks sign in button
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Click the submit button"
```

**Expected**: Finds and clicks submit button
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Press the OK button"
```

**Expected**: Finds and clicks OK button
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Click on the search box"
```

**Expected**: Finds and clicks search input field
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

#### **Typing Commands**

```
"Type 'hello world' in the text field"
```

**Expected**: Finds text field and types the text
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Enter my email address"
```

**Expected**: Types email in appropriate field
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

#### **Navigation Commands**

```
"Scroll down"
```

**Expected**: Scrolls the current window down
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Scroll up"
```

**Expected**: Scrolls the current window up
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Press enter"
```

**Expected**: Presses the enter key
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

---

### 💬 **3. CONVERSATIONAL CHAT COMMANDS**

_These commands engage in natural conversation_

#### **Greeting Commands**

```
"Hello, how are you today?"
```

**Expected**: Responds with friendly greeting
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Good morning AURA"
```

**Expected**: Responds appropriately to greeting
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

#### **General Chat Commands**

```
"Tell me a joke"
```

**Expected**: Responds with a joke
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"What's the weather like?"
```

**Expected**: Responds about weather (may indicate limitations)
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"How can you help me?"
```

**Expected**: Explains AURA's capabilities
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

---

### ❓ **4. QUESTION ANSWERING COMMANDS**

_These commands ask for information or analysis_

#### **Screen Analysis Commands**

```
"What's on my screen?"
```

**Expected**: Analyzes and describes current screen content
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Describe what you see"
```

**Expected**: Provides description of visible elements
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"What buttons are available?"
```

**Expected**: Lists clickable buttons on screen
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

#### **Knowledge Questions**

```
"What is Python programming?"
```

**Expected**: Provides explanation of Python
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"How do I create a function in JavaScript?"
```

**Expected**: Explains JavaScript function creation
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

```
"Explain machine learning"
```

**Expected**: Provides ML explanation
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

---

## 🔧 **System Testing Commands**

### **Audio System Test**

```
"Test audio feedback"
```

**Expected**: Plays confirmation sounds and speaks response
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

### **Wake Word Test**

```
1. Wait for AURA to go back to listening
2. Say "computer" clearly
3. Should hear confirmation sound
4. Give any command
```

**Expected**: Reliable wake word detection with audio feedback
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

### **Vision System Test**

```
"Take a screenshot and describe it"
```

**Expected**: Captures screen and provides detailed description
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

---

## 🚨 **Error Handling Tests**

### **Invalid Commands**

```
"Blah blah nonsense command"
```

**Expected**: Politely indicates it doesn't understand
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

### **Impossible Actions**

```
"Click on the invisible button"
```

**Expected**: Indicates it cannot find the element
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

### **Network Issues Test**

```
Disconnect internet, then try: "Write me a Python function"
```

**Expected**: Graceful error handling with helpful message
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

---

## 📊 **Performance Tests**

### **Response Time Test**

```
Time how long each command type takes:
- Simple chat: "Hello"
- GUI command: "Click button"
- Content generation: "Write code"
- Screen analysis: "What's on screen?"
```

**Expected Response Times**:

- Chat: < 3 seconds
- GUI: < 5 seconds
- Content: < 10 seconds
- Analysis: < 8 seconds

**Feedback Box**:

```
Chat: _____ seconds
GUI: _____ seconds
Content: _____ seconds
Analysis: _____ seconds
Notes:
```

### **Memory Usage Test**

```
Run multiple commands in sequence and monitor system resources
```

**Expected**: Stable memory usage, no significant leaks
**Feedback Box**:

```
✅ Stable | ❌ Memory Issues | ⚠️ Gradual Increase
Notes:
```

---

## 🔍 **Debugging Commands**

### **System Status**

```
"What's your current status?"
```

**Expected**: Reports system health and capabilities
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

### **Module Status**

```
"Check your modules"
```

**Expected**: Reports status of vision, reasoning, automation modules
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

---

## 📝 **Overall System Assessment**

### **Startup Test**

**Command**: `python main.py`
**Expected**: Clean startup with all modules initialized
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Startup Time: _____ seconds
Error Messages:
```

### **Shutdown Test**

**Command**: `Ctrl+C` to stop AURA
**Expected**: Clean shutdown with proper cleanup
**Feedback Box**:

```
✅ Working | ❌ Not Working | ⚠️ Partial
Notes:
```

### **Stability Test**

**Test**: Run AURA for 30+ minutes with various commands
**Expected**: Stable operation without crashes
**Feedback Box**:

```
✅ Stable | ❌ Crashes | ⚠️ Occasional Issues
Runtime: _____ minutes
Issues Encountered:
```

---

## 🎯 **Priority Issues to Report**

### **Critical Issues** (System Breaking)

- [ ] Application won't start
- [ ] Crashes during operation
- [ ] Wake word not working
- [ ] No audio feedback

### **High Priority Issues** (Core Functionality)

- [ ] Deferred actions not working
- [ ] GUI commands failing
- [ ] Content generation empty/wrong
- [ ] Second commands hanging

### **Medium Priority Issues** (User Experience)

- [ ] Slow response times
- [ ] Poor audio quality
- [ ] Inconsistent behavior
- [ ] Memory leaks

### **Low Priority Issues** (Nice to Have)

- [ ] Minor UI improvements
- [ ] Additional command variations
- [ ] Performance optimizations

---

## 📋 **Test Results Summary**

**Date**: \***\*\_\_\_\*\***  
**Tester**: \***\*\_\_\_\*\***  
**AURA Version**: 1.0.0  
**System**: macOS \***\*\_\_\_\*\***

### **Overall Assessment**

```
✅ Excellent | ✅ Good | ⚠️ Fair | ❌ Poor

Overall Rating: ___/10

Most Impressive Feature:

Biggest Issue:

Recommended Priority Fix:
```

### **Category Scores**

```
Deferred Actions: ___/10
GUI Interactions: ___/10
Conversational Chat: ___/10
Question Answering: ___/10
System Stability: ___/10
Performance: ___/10
```

### **Additional Notes**

```
Suggestions for Improvement:


Unexpected Behaviors:


Positive Surprises:


Would you recommend AURA to others? Yes/No
Why?
```

---

## 🚀 **Quick Start Testing Sequence**

**For rapid testing, try these commands in order:**

1. `"Hello AURA"` - Test conversational chat
2. `"What's on my screen?"` - Test vision analysis
3. `"Write me a Python hello world function"` - Test deferred action
4. `"Click on the [visible button]"` - Test GUI interaction
5. `"Write me a short poem"` - Test concurrent deferred actions

**Expected Total Time**: ~5 minutes  
**Success Criteria**: All 5 commands work without errors

**Quick Test Results**:

```
1. Chat: ✅/❌
2. Vision: ✅/❌
3. Code Gen: ✅/❌
4. GUI Click: ✅/❌
5. Text Gen: ✅/❌

Overall Quick Test: PASS/FAIL
```

---

_Happy Testing! 🧪 Your feedback helps make AURA better for everyone._

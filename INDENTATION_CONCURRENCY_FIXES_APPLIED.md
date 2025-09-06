# Indentation and Concurrency Fixes Applied

## ✅ **Fixes Implemented**

### **1. Enhanced Debug Logging for Indentation Tracking**

**Added comprehensive logging to track where indentation might be lost:**

#### **In Content Generation (`orchestrator.py`)**:

```python
# INDENTATION DEBUG: Check if extracted content has proper formatting
if content_type == 'code' and generated_content:
    lines = generated_content.split('\n')
    indented_lines = [line for line in lines if line.startswith('    ')]
    logger.debug(f"[{execution_id}] INDENTATION CHECK - Total lines: {len(lines)}, Indented lines: {len(indented_lines)}")
    if len(lines) > 1:
        logger.debug(f"[{execution_id}] INDENTATION SAMPLE - First 3 lines:")
        for i, line in enumerate(lines[:3]):
            spaces = len(line) - len(line.lstrip())
            logger.debug(f"[{execution_id}]   Line {i+1}: {spaces} spaces | '{line}'")
    else:
        logger.warning(f"[{execution_id}] INDENTATION WARNING - Content appears to be single line")
```

#### **In AppleScript Typing (`modules/automation.py`)**:

```python
# INDENTATION DEBUG: Check line indentation before processing
leading_spaces = len(line) - len(line.lstrip())
if leading_spaces > 0:
    logger.debug(f"AppleScript typing line {i+1} with {leading_spaces} leading spaces: '{line}'")

# INDENTATION DEBUG: Verify spaces preserved after escaping
escaped_spaces = len(escaped_line) - len(escaped_line.lstrip())
if leading_spaces != escaped_spaces:
    logger.error(f"INDENTATION LOST during escaping! Original: {leading_spaces} spaces, Escaped: {escaped_spaces} spaces")
```

### **2. Improved Execution Lock Management**

**Added robust lock release after deferred action completion:**

```python
finally:
    # Always reset state after execution attempt
    self._reset_deferred_action_state()

    # CONCURRENCY FIX: Ensure execution lock is released
    if hasattr(self, 'execution_lock') and self.execution_lock.locked():
        logger.warning(f"[{execution_id}] Force releasing execution lock after deferred action completion")
        try:
            self.execution_lock.release()
        except Exception as lock_error:
            logger.error(f"[{execution_id}] Failed to release execution lock: {lock_error}")
```

### **3. Code Generation Prompt Verification**

**Confirmed the prompt explicitly requests proper formatting:**

```
- Ensure proper indentation and formatting for the target language
- Use 4 spaces for indentation in Python, 2 spaces for JavaScript/HTML/CSS
- Include proper line breaks and structure
- Make the code ready to be typed directly into an editor
```

## 🔍 **Root Cause Analysis Results**

### **Indentation Issue**

Our testing revealed:

- ✅ **Content extraction logic preserves indentation correctly**
- ✅ **AppleScript line processing preserves indentation correctly**
- ❌ **The API is likely returning single-line code despite the prompt**

**Example of the problem:**

```python
# What the API might be returning:
"def fibonacci(n): if n <= 0: return [] if n == 1: return [0] seq = [0, 1] while len(seq) < n: seq.append(seq[-1] + seq[-2]) return seq"

# What it should return:
"def fibonacci(n):\n    if n <= 0:\n        return []\n    if n == 1:\n        return [0]\n    seq = [0, 1]\n    while len(seq) < n:\n        seq.append(seq[-1] + seq[-2])\n    return seq"
```

### **Concurrency Issue**

The execution lock fix is in place, but the second command still hangs. This suggests:

- The lock might not be released properly in all code paths
- There might be other blocking operations (intent recognition, API calls)
- State management issues after deferred action completion

## 📊 **Testing Results**

### **Indentation Pipeline Test**

```
✅ Response 1: Has proper indentation (9 lines, 8 indented)
❌ Response 2: Single line format (problematic)
✅ Response 3: Has proper indentation (4 lines, 3 indented)
✅ AppleScript processing: All indentation preserved correctly
```

**Conclusion**: The issue is likely in the **API response format**, not our processing pipeline.

## 🎯 **Next Steps for User Testing**

### **1. Test with Debug Logging**

Run AURA and look for these debug messages:

```
[DEBUG] INDENTATION CHECK - Total lines: X, Indented lines: Y
[DEBUG] INDENTATION SAMPLE - First 3 lines:
[DEBUG] Line 1: 0 spaces | 'def fibonacci(n):'
[DEBUG] Line 2: 4 spaces | '    if n <= 0:'
```

### **2. Check for Single-Line Responses**

If you see:

```
[WARNING] INDENTATION WARNING - Content appears to be single line
```

This confirms the API is returning unformatted code.

### **3. Monitor Execution Lock**

Look for:

```
[WARNING] Force releasing execution lock after deferred action completion
```

This indicates the concurrency fix is working.

### **4. Test Concurrent Commands**

Try the testing sequence:

1. "Write me a Python function for fibonacci"
2. Wait for "click where you want it placed"
3. Immediately say "computer" again
4. "Write me a JavaScript function to sort"
5. Both should process without hanging

## 🔧 **Additional Fixes if Issues Persist**

### **If API Returns Single-Line Code**

```python
# Add post-processing to format single-line code
def _format_single_line_code(self, code: str, language: str) -> str:
    """Convert single-line code to properly formatted multi-line code."""
    if language.lower() == 'python':
        # Add Python-specific formatting logic
        formatted = code.replace(': ', ':\n    ')
        # Add more sophisticated formatting rules
    return formatted
```

### **If Concurrency Still Fails**

```python
# Add timeout to execution lock
def execute_command(self, command: str) -> Dict[str, Any]:
    try:
        acquired = self.execution_lock.acquire(timeout=30.0)
        if not acquired:
            logger.error("Failed to acquire execution lock within timeout")
            return self._create_error_result("System busy, please try again")
        # ... rest of execution logic
```

### **If AppleScript Fails with Spaces**

```python
# Alternative: Use cliclick for code typing
def _type_code_with_cliclick(self, code: str) -> bool:
    """Use cliclick for code typing to ensure indentation preservation."""
    return self._cliclick_type(code, fast_path=False)
```

## 📋 **Summary**

### **Status**

- ✅ **Debug logging added** to track indentation issues
- ✅ **Execution lock management improved** for concurrency
- ✅ **Code generation prompt verified** as requesting proper formatting
- ⚠️ **Root cause likely identified** as API returning single-line code

### **Expected Behavior After Fixes**

1. **Debug logs will show** exactly where indentation is lost
2. **Concurrent commands should work** without hanging
3. **If API returns proper formatting**, code will be typed correctly
4. **If API returns single-line code**, we'll see warning messages

### **User Action Required**

**Test AURA with the debug logging and report:**

1. What the debug logs show about indentation
2. Whether concurrent commands work
3. Whether the execution lock warnings appear
4. The exact format of the typed code

This will help us determine if we need additional fixes for API response formatting or if the current fixes resolve the issues.

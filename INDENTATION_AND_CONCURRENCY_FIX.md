# Indentation and Concurrency Issues Fix

## 🚨 **Issues Identified**

### **Issue 1: Code Indentation Lost** ❌ Critical

Generated Python code is typed without proper indentation:

```python
# What should be generated:
def fibonacci(n):
    if n <= 0:
        return []
    if n == 1:
        return [0]

# What's actually typed:
def fibonacci(n): if n <= 0: return [] if n == 1: return [0]
```

### **Issue 2: Second Command Still Hanging** ❌ Critical

Second consecutive deferred action command hangs after starting execution:

```
2025-09-07 00:13:10,323 - orchestrator - INFO - Starting command execution [cmd_1757184190323]: 'Write me a JavaScript function to sort an array.'
# Then nothing... command never progresses
```

## 🔍 **Root Cause Analysis**

### **Indentation Issue Analysis**

Our tests show that:

- ✅ **Line splitting preserves indentation correctly**
- ✅ **AppleScript command generation includes proper spaces**
- ❌ **But the actual typed output loses formatting**

**Hypothesis**: The issue is likely in:

1. **Content generation** - API returning unformatted code
2. **Response extraction** - Losing formatting during parsing
3. **AppleScript execution** - System not handling spaces correctly

### **Concurrency Issue Analysis**

The execution lock fix is in place, but the second command still hangs. This suggests:

1. **Lock not being released properly** after first command completion
2. **Deadlock in intent recognition** or other shared resources
3. **State not being reset** after deferred action completion

## 🔧 **Proposed Fixes**

### **Fix 1: Enhanced Content Generation Debugging**

Add comprehensive logging to track where indentation is lost:

```python
# In content generation method
logger.debug(f"[{execution_id}] Raw API response: {response}")
logger.debug(f"[{execution_id}] Extracted content: {repr(generated_content)}")
logger.debug(f"[{execution_id}] After cleaning: {repr(cleaned_content)}")
```

### **Fix 2: Improved AppleScript Indentation Handling**

Ensure AppleScript properly handles leading whitespace:

```python
def _macos_type(self, text: str) -> bool:
    # Add explicit handling for indentation
    lines = text.split('\n')

    for i, line in enumerate(lines):
        if line:
            # Preserve leading whitespace explicitly
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces > 0:
                logger.debug(f"Line {i+1} has {leading_spaces} leading spaces")

            # Ensure spaces are properly escaped for AppleScript
            escaped_line = line.replace('\\', '\\\\').replace('"', '\\"')

            # Verify spaces are still there after escaping
            if leading_spaces > 0 and not escaped_line.startswith(' ' * leading_spaces):
                logger.error(f"Lost {leading_spaces} spaces during escaping!")
```

### **Fix 3: Alternative Typing Method for Code**

Use a different approach for code typing that guarantees indentation:

```python
def _type_code_with_indentation(self, code: str) -> bool:
    """Type code with guaranteed indentation preservation."""
    lines = code.split('\n')

    for i, line in enumerate(lines):
        if line.strip():  # Non-empty line
            # Count leading spaces
            leading_spaces = len(line) - len(line.lstrip())
            content = line.lstrip()

            # Type spaces first, then content
            if leading_spaces > 0:
                self._type_spaces(leading_spaces)
            self._type_content(content)

        # Add newline except for last line
        if i < len(lines) - 1:
            self._press_return()
```

### **Fix 4: Force Lock Release After Deferred Action**

Add explicit lock release after deferred action completion:

```python
def _trigger_deferred_action(self, execution_id: str, click_coordinates: Tuple[int, int]) -> None:
    try:
        # ... existing deferred action logic ...

        # Execute the action
        success = self._execute_pending_deferred_action(execution_id, click_coordinates)

        # Always reset state and release locks
        self._reset_deferred_action_state()

        # Explicitly release execution lock if still held
        if hasattr(self, 'execution_lock') and self.execution_lock.locked():
            logger.warning(f"[{execution_id}] Force releasing execution lock after deferred action")
            self.execution_lock.release()

    except Exception as e:
        # Ensure cleanup on error
        self._reset_deferred_action_state()
        if hasattr(self, 'execution_lock') and self.execution_lock.locked():
            self.execution_lock.release()
        raise
```

### **Fix 5: Content Generation Prompt Enhancement**

Improve the code generation prompt to explicitly request proper formatting:

```python
CODE_GENERATION_PROMPT = """
Generate clean, properly formatted {language} code for the following request:

Request: {request}

Requirements:
- Use proper indentation (4 spaces for Python, 2 spaces for JavaScript)
- Include proper line breaks and formatting
- Return ONLY the code, no explanations or markdown
- Ensure the code is syntactically correct and well-formatted

Code:
"""
```

## 🧪 **Testing Strategy**

### **Test 1: Content Generation Pipeline**

```python
def test_full_pipeline():
    # Test each stage of content generation
    1. Generate content
    2. Extract from response
    3. Clean content
    4. Type content
    # Verify indentation at each step
```

### **Test 2: Concurrent Execution**

```python
def test_concurrent_deferred_actions():
    # Start first deferred action
    # Immediately start second deferred action
    # Verify both complete without hanging
```

### **Test 3: Lock Management**

```python
def test_lock_release():
    # Monitor execution lock state
    # Verify proper release after deferred actions
    # Test edge cases and error scenarios
```

## 📋 **Implementation Priority**

### **High Priority (Fix Immediately)**

1. **Add debug logging** to track where indentation is lost
2. **Fix execution lock release** to prevent hanging
3. **Test with simple code examples** to isolate the issue

### **Medium Priority (Next Steps)**

1. **Improve AppleScript handling** of whitespace
2. **Enhance content generation prompts** for better formatting
3. **Add comprehensive error handling** for edge cases

### **Low Priority (Future Improvements)**

1. **Alternative typing methods** for different content types
2. **Performance optimizations** for large code blocks
3. **Support for different indentation styles** (tabs vs spaces)

## 🎯 **Expected Outcomes**

### **After Indentation Fix**

```python
# User says: "Write me a Python function for fibonacci"
# AURA should type:
def fibonacci(n):
    if n <= 0:
        return []
    if n == 1:
        return [0]
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq
```

### **After Concurrency Fix**

```
1. User: "Write me a Python function for fibonacci"
   → ✅ Generates code, waits for click
2. User: "Write me a JavaScript function to sort"
   → ✅ Processes immediately, doesn't hang
3. Both commands complete successfully
```

## 🚀 **Next Steps**

1. **Add comprehensive debug logging** to track the content pipeline
2. **Test with minimal examples** to isolate where formatting is lost
3. **Fix the execution lock issue** to enable concurrent commands
4. **Verify fixes with the testing guide** commands
5. **Document the solution** for future reference

This fix will ensure that AURA generates properly formatted code with correct indentation for all programming languages, maintaining professional development standards.

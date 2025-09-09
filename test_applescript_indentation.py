#!/usr/bin/env python3
"""
Test AppleScript indentation behavior to identify the auto-indentation issue.
"""

import subprocess
import time

def test_applescript_indentation():
    """Test if AppleScript is auto-indenting and causing exponential indentation growth."""
    
    print("🧪 Testing AppleScript Indentation Behavior")
    print("=" * 50)
    print("This will test if AppleScript auto-indents based on previous lines.")
    print("Open a text editor and focus on it, then press Enter...")
    input()
    
    # Test lines with specific indentation
    test_lines = [
        "def test():",           # 0 spaces
        "    line1 = 1",         # 4 spaces  
        "    line2 = 2",         # 4 spaces
        "        line3 = 3",     # 8 spaces
        "        line4 = 4",     # 8 spaces
        "    line5 = 5"          # 4 spaces (back to 4)
    ]
    
    print("Testing AppleScript typing with controlled indentation...")
    print("Watch for exponential indentation growth!")
    print()
    
    for i, line in enumerate(test_lines):
        spaces = len(line) - len(line.lstrip())
        print(f"Line {i+1}: {spaces} spaces - '{line}'")
        
        # Escape the line for AppleScript
        escaped_line = line.replace('"', '\\"')
        
        # Type using AppleScript
        applescript = f'''
        tell application "System Events"
            keystroke "{escaped_line}"
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"   ✅ Typed successfully")
            else:
                print(f"   ❌ Failed: {result.stderr}")
                continue
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            continue
        
        # Add Return key if not the last line
        if i < len(test_lines) - 1:
            return_script = '''
            tell application "System Events"
                key code 36
            end tell
            '''
            
            try:
                result = subprocess.run(
                    ['osascript', '-e', return_script],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    print(f"   ✅ Return key pressed")
                else:
                    print(f"   ❌ Return failed: {result.stderr}")
                    
            except Exception as e:
                print(f"   ❌ Return exception: {e}")
        
        time.sleep(0.5)  # Pause between lines
        print()
    
    print("Test completed!")
    print("Check your text editor:")
    print("- Does each line have the CORRECT indentation?")
    print("- Or does indentation grow exponentially?")
    print("- Line 1: 0 spaces")
    print("- Line 2: 4 spaces") 
    print("- Line 3: 4 spaces")
    print("- Line 4: 8 spaces")
    print("- Line 5: 8 spaces")
    print("- Line 6: 4 spaces")
    
    response = input("Did the indentation stay correct? (y/n): ").lower().strip()
    return response.startswith('y')

def test_smart_editor_behavior():
    """Test if the text editor is doing smart indentation."""
    
    print("\n🤖 Testing Smart Editor Auto-Indentation")
    print("=" * 50)
    print("Some editors auto-indent after colons (:) or other triggers.")
    print("Focus on your text editor and press Enter...")
    input()
    
    # Test with colon (triggers auto-indent in many editors)
    print("Testing colon-triggered auto-indentation...")
    
    colon_script = '''
    tell application "System Events"
        keystroke "def function():"
    end tell
    '''
    
    subprocess.run(['osascript', '-e', colon_script], capture_output=True, timeout=5)
    time.sleep(0.5)
    
    # Press Return
    return_script = '''
    tell application "System Events"
        key code 36
    end tell
    '''
    
    subprocess.run(['osascript', '-e', return_script], capture_output=True, timeout=5)
    time.sleep(0.5)
    
    # Type next line (should be auto-indented by editor)
    next_line_script = '''
    tell application "System Events"
        keystroke "print('hello')"
    end tell
    '''
    
    subprocess.run(['osascript', '-e', next_line_script], capture_output=True, timeout=5)
    
    print("Check your editor:")
    print("- Did the editor auto-indent after the colon?")
    print("- Is 'print('hello')' indented automatically?")
    
    auto_indented = input("Did the editor auto-indent? (y/n): ").lower().startswith('y')
    
    if auto_indented:
        print("\n🎯 FOUND THE ISSUE!")
        print("The text editor is auto-indenting, which explains the exponential growth:")
        print("1. AppleScript types a line with 4 spaces")
        print("2. Editor sees the colon and auto-indents the NEXT line")
        print("3. AppleScript types the next line with its OWN 4 spaces")
        print("4. Result: 4 (AppleScript) + 4 (auto-indent) = 8 spaces")
        print("5. This compounds with each line!")
    
    return auto_indented

def main():
    """Run AppleScript indentation tests."""
    
    indentation_correct = test_applescript_indentation()
    auto_indent_detected = test_smart_editor_behavior()
    
    print("\n" + "=" * 50)
    print("🎯 APPLESCRIPT INDENTATION TEST RESULTS")
    print("=" * 50)
    print(f"AppleScript preserves indentation: {'✅ YES' if indentation_correct else '❌ NO'}")
    print(f"Editor auto-indentation detected: {'⚠️ YES' if auto_indent_detected else '✅ NO'}")
    
    if indentation_correct and not auto_indent_detected:
        print("\n✅ AppleScript works correctly!")
        print("The issue must be elsewhere in AURA's implementation.")
    elif not indentation_correct or auto_indent_detected:
        print("\n❌ INDENTATION ISSUE IDENTIFIED!")
        if auto_indent_detected:
            print("🎯 ROOT CAUSE: Editor auto-indentation is interfering!")
            print("SOLUTION: Disable auto-indent or use different typing approach")
        else:
            print("🎯 ROOT CAUSE: AppleScript is not preserving indentation correctly")
            print("SOLUTION: Fix AppleScript indentation handling")
    
    return indentation_correct and not auto_indent_detected

if __name__ == "__main__":
    main()
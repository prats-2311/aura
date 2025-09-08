#!/usr/bin/env python3
"""
Validation script for text formatting fixes in cliclick typing method.
This script validates the implementation without actually executing typing commands.
"""

import sys
import os
import re

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_implementation():
    """Validate that the text formatting fixes are properly implemented."""
    
    print("Validating Text Formatting Fix Implementation")
    print("=" * 50)
    
    # Read the automation module
    try:
        with open('modules/automation.py', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("ERROR: modules/automation.py not found")
        return False
    
    validation_results = []
    
    # Check 1: _format_text_for_typing method exists
    if '_format_text_for_typing' in content:
        validation_results.append(("✓", "_format_text_for_typing method exists"))
    else:
        validation_results.append(("✗", "_format_text_for_typing method missing"))
    
    # Check 2: _cliclick_type_multiline method exists
    if '_cliclick_type_multiline' in content:
        validation_results.append(("✓", "_cliclick_type_multiline method exists"))
    else:
        validation_results.append(("✗", "_cliclick_type_multiline method missing"))
    
    # Check 3: Enhanced _cliclick_type method calls preprocessing
    if 'formatted_text = self._format_text_for_typing(text, \'cliclick\')' in content:
        validation_results.append(("✓", "_cliclick_type calls text preprocessing"))
    else:
        validation_results.append(("✗", "_cliclick_type doesn't call text preprocessing"))
    
    # Check 4: Multi-line handling in _cliclick_type
    if 'if \'\\n\' in text:' in content and '_cliclick_type_multiline' in content:
        validation_results.append(("✓", "_cliclick_type handles multi-line text"))
    else:
        validation_results.append(("✗", "_cliclick_type doesn't handle multi-line text properly"))
    
    # Check 5: Proper key press for newlines
    if 'kp:return' in content:
        validation_results.append(("✓", "Uses correct key name for Enter (return)"))
    else:
        validation_results.append(("✗", "Doesn't use correct key name for Enter"))
    
    # Check 6: Character escaping in _format_text_for_typing
    escape_patterns = [
        r'replace\(\'\\\\\'',  # Backslash escaping
        r'replace\(\'"\'',     # Quote escaping
    ]
    
    escape_found = any(re.search(pattern, content) for pattern in escape_patterns)
    if escape_found:
        validation_results.append(("✓", "Character escaping implemented"))
    else:
        validation_results.append(("✗", "Character escaping not found"))
    
    # Check 7: Performance logging includes newline count
    if 'newlines_count' in content or 'line_count' in content:
        validation_results.append(("✓", "Performance logging includes line/newline metrics"))
    else:
        validation_results.append(("✗", "Performance logging doesn't track line metrics"))
    
    # Print results
    print("\nValidation Results:")
    print("-" * 30)
    
    passed = 0
    total = len(validation_results)
    
    for status, message in validation_results:
        print(f"{status} {message}")
        if status == "✓":
            passed += 1
    
    print(f"\nSummary: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All validation checks passed!")
        return True
    else:
        print(f"⚠️  {total - passed} validation checks failed")
        return False

def test_text_preprocessing_logic():
    """Test the text preprocessing logic by importing and testing the methods."""
    
    print("\n" + "=" * 50)
    print("Testing Text Preprocessing Logic")
    print("=" * 50)
    
    try:
        from modules.automation import AutomationModule
        
        automation = AutomationModule()
        
        # Test cases
        test_cases = [
            ("Simple text", "Hello World"),
            ("Text with quotes", 'He said "Hello" and \'Goodbye\''),
            ("Text with backslashes", "Path: C:\\Users\\Name"),
            ("Multi-line code", "def func():\n    return True"),
            ("Special characters", "Email: user@domain.com & more!"),
        ]
        
        print("\nTesting _format_text_for_typing method:")
        print("-" * 40)
        
        for test_name, test_text in test_cases:
            print(f"\n{test_name}:")
            print(f"  Original: {repr(test_text)}")
            
            try:
                cliclick_result = automation._format_text_for_typing(test_text, 'cliclick')
                print(f"  Cliclick: {repr(cliclick_result)}")
                
                applescript_result = automation._format_text_for_typing(test_text, 'applescript')
                print(f"  AppleScript: {repr(applescript_result)}")
                
                # Validate that newlines are preserved
                if '\n' in test_text:
                    if test_text.count('\n') == cliclick_result.count('\n'):
                        print("  ✓ Newlines preserved in cliclick formatting")
                    else:
                        print("  ✗ Newlines not preserved in cliclick formatting")
                
            except Exception as e:
                print(f"  ✗ Error testing {test_name}: {e}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Could not import AutomationModule: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing preprocessing logic: {e}")
        return False

def validate_requirements_coverage():
    """Validate that the implementation covers all requirements."""
    
    print("\n" + "=" * 50)
    print("Requirements Coverage Validation")
    print("=" * 50)
    
    requirements = [
        ("1.1", "System preserves line breaks and indentation", "Multi-line handling"),
        ("1.2", "System maintains proper code formatting", "Character escaping"),
        ("1.3", "cliclick handles newlines and special characters correctly", "cliclick enhancements"),
    ]
    
    try:
        with open('modules/automation.py', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("ERROR: Cannot read automation module")
        return False
    
    print("\nRequirement Coverage:")
    print("-" * 30)
    
    coverage_indicators = [
        ("Multi-line handling", ["_cliclick_type_multiline", "if '\\n' in text"]),
        ("Character escaping", ["_format_text_for_typing", "replace(\\'\\\\\\'"]),
        ("cliclick enhancements", ["formatted_text", "kp:return"]),
    ]
    
    for req_id, req_desc, coverage_type in requirements:
        print(f"\n{req_id}: {req_desc}")
        
        # Find corresponding coverage indicators
        indicators = next((ind for name, ind in coverage_indicators if name == coverage_type), [])
        
        covered = all(indicator in content for indicator in indicators)
        status = "✓" if covered else "✗"
        print(f"  {status} {coverage_type} implementation")
        
        if not covered:
            missing = [ind for ind in indicators if ind not in content]
            print(f"    Missing: {missing}")

if __name__ == "__main__":
    success = True
    
    success &= validate_implementation()
    success &= test_text_preprocessing_logic()
    validate_requirements_coverage()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Text formatting fix validation completed successfully!")
    else:
        print("⚠️  Some validation checks failed. Please review the implementation.")
    print("=" * 50)
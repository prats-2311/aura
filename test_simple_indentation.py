#!/usr/bin/env python3
"""
Simple Indentation Test

Test the AppleScript line-by-line typing to see if it preserves indentation.
"""

import sys
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_line_splitting_with_indentation():
    """Test how our line splitting handles indented code."""
    logger.info("Testing line splitting with indentation...")
    
    # Test code with proper indentation
    test_code = """def fibonacci(n):
    if n <= 0:
        return []
    if n == 1:
        return [0]
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq"""
    
    logger.info("Original code:")
    for i, line in enumerate(test_code.split('\n')):
        spaces = len(line) - len(line.lstrip())
        logger.info(f"Line {i+1}: {spaces} spaces | '{line}'")
    
    # Simulate the AppleScript line processing
    lines = test_code.split('\n')
    
    logger.info("\nProcessing each line (as AppleScript would):")
    for i, line in enumerate(lines):
        if line:  # Only process non-empty lines
            # This is what AppleScript would receive
            escaped_line = line.replace('\\', '\\\\').replace('"', '\\"').replace('\r', '\\r')
            spaces = len(line) - len(line.lstrip())
            
            logger.info(f"Line {i+1}: {spaces} spaces | AppleScript will type: '{escaped_line}'")
            
            # Check if leading spaces are preserved
            if line.startswith('    ') and not escaped_line.startswith('    '):
                logger.error(f"❌ Line {i+1}: Lost leading spaces!")
                return False
            elif line.startswith('    ') and escaped_line.startswith('    '):
                logger.info(f"✅ Line {i+1}: Indentation preserved")
    
    logger.info("✅ Line splitting preserves indentation correctly")
    return True

def test_applescript_command_generation():
    """Test the actual AppleScript command generation."""
    logger.info("Testing AppleScript command generation...")
    
    # Test a single indented line
    test_line = "    if n <= 0:"
    
    # This is what our code does
    escaped_line = test_line.replace('\\', '\\\\').replace('"', '\\"').replace('\r', '\\r')
    
    applescript = f'''
    tell application "System Events"
        keystroke "{escaped_line}"
    end tell
    '''
    
    logger.info(f"Original line: '{test_line}'")
    logger.info(f"Escaped line: '{escaped_line}'")
    logger.info(f"AppleScript command:\n{applescript}")
    
    # Check if the spaces are preserved in the command
    if '    if n <= 0:' in applescript:
        logger.info("✅ AppleScript command contains proper indentation")
        return True
    else:
        logger.error("❌ AppleScript command lost indentation")
        return False

def main():
    """Run simple indentation tests."""
    logger.info("🧪 Testing Simple Indentation Preservation")
    logger.info("=" * 50)
    
    success1 = test_line_splitting_with_indentation()
    success2 = test_applescript_command_generation()
    
    if success1 and success2:
        logger.info("🎉 Simple indentation tests passed!")
        logger.info("The issue might be elsewhere in the pipeline.")
        return True
    else:
        logger.error("💥 Simple indentation tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
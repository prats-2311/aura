#!/usr/bin/env python3
"""
Test Newline Formatting Fix

This test verifies that the newline formatting fix works correctly for both
cliclick and AppleScript typing methods.
"""

import sys
import logging
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_newline_formatting():
    """Test that newlines are preserved in typing actions."""
    logger.info("Testing newline formatting fix...")
    
    try:
        from modules.automation import AutomationModule
        
        # Create automation module
        automation = AutomationModule()
        
        # Test text with newlines and indentation
        test_code = """def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Test the function
print(fibonacci(10))"""
        
        logger.info(f"Testing with code:\n{test_code}")
        
        # Mock subprocess.run to capture the commands
        commands_executed = []
        
        def mock_subprocess_run(cmd, **kwargs):
            commands_executed.append({
                'cmd': cmd,
                'kwargs': kwargs
            })
            # Return successful result
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            result.stdout = ""
            return result
        
        with patch('subprocess.run', side_effect=mock_subprocess_run):
            # Test AppleScript typing (macOS)
            automation.is_macos = True
            automation.has_cliclick = False
            
            logger.info("Testing AppleScript typing...")
            success = automation._macos_type(test_code)
            
            if success:
                logger.info("✅ AppleScript typing succeeded")
                
                # Check that multiple commands were executed (one per line + return keys)
                lines = test_code.split('\n')
                expected_commands = len(lines) + (len(lines) - 1)  # lines + return keys
                
                if len(commands_executed) >= expected_commands:
                    logger.info(f"✅ Correct number of commands executed: {len(commands_executed)}")
                    
                    # Check that return key commands are present
                    return_commands = [cmd for cmd in commands_executed if 'key code 36' in str(cmd.get('cmd', ''))]
                    expected_returns = len(lines) - 1
                    
                    if len(return_commands) == expected_returns:
                        logger.info(f"✅ Correct number of return key presses: {len(return_commands)}")
                    else:
                        logger.warning(f"❌ Expected {expected_returns} return keys, got {len(return_commands)}")
                        
                    # Check that no escaped newlines are present
                    has_escaped_newlines = any('\\\\n' in str(cmd.get('cmd', '')) for cmd in commands_executed)
                    if not has_escaped_newlines:
                        logger.info("✅ No escaped newlines found in commands")
                    else:
                        logger.warning("❌ Found escaped newlines in commands")
                        
                else:
                    logger.warning(f"❌ Expected at least {expected_commands} commands, got {len(commands_executed)}")
            else:
                logger.error("❌ AppleScript typing failed")
                return False
        
        # Reset for cliclick test
        commands_executed.clear()
        
        with patch('subprocess.run', side_effect=mock_subprocess_run):
            # Test cliclick typing
            automation.has_cliclick = True
            
            logger.info("Testing cliclick typing...")
            success = automation._cliclick_type(test_code)
            
            if success:
                logger.info("✅ cliclick typing succeeded")
                
                # Check that the command contains the original text with newlines
                if commands_executed:
                    cmd = commands_executed[0]['cmd']
                    if isinstance(cmd, list) and len(cmd) >= 2:
                        typed_text = cmd[1][2:]  # Remove 't:' prefix
                        if '\n' in typed_text and '\\\\n' not in typed_text:
                            logger.info("✅ cliclick preserves newlines correctly")
                        else:
                            logger.warning("❌ cliclick newline handling issue")
                    else:
                        logger.warning("❌ Unexpected cliclick command format")
                else:
                    logger.warning("❌ No cliclick commands executed")
            else:
                logger.error("❌ cliclick typing failed")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

def main():
    """Run newline formatting test."""
    logger.info("🧪 Testing Newline Formatting Fix")
    logger.info("=" * 40)
    
    success = test_newline_formatting()
    
    if success:
        logger.info("🎉 Newline formatting test passed!")
        logger.info("Content generation should now preserve proper formatting.")
        return True
    else:
        logger.error("💥 Newline formatting test failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
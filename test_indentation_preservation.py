#!/usr/bin/env python3
"""
Test Indentation Preservation

This test verifies that code indentation is properly preserved during:
1. Content generation
2. Content cleaning
3. Typing automation
"""

import sys
import logging
from unittest.mock import Mock, patch

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_content_cleaning_indentation():
    """Test that content cleaning preserves indentation."""
    logger.info("Testing content cleaning indentation preservation...")
    
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
    
    try:
        # Import the orchestrator to test content cleaning
        import sys
        sys.path.append('.')
        from orchestrator import Orchestrator
        
        # Create a mock orchestrator
        orchestrator = Mock()
        orchestrator._clean_generated_content = Orchestrator._clean_generated_content.__get__(orchestrator)
        
        # Test content cleaning
        cleaned_code = orchestrator._clean_generated_content(test_code, 'code')
        
        logger.info(f"Original code length: {len(test_code)} chars")
        logger.info(f"Cleaned code length: {len(cleaned_code)} chars")
        
        # Check if indentation is preserved
        original_lines = test_code.split('\n')
        cleaned_lines = cleaned_code.split('\n')
        
        logger.info("Checking line-by-line indentation:")
        indentation_preserved = True
        
        for i, (orig, clean) in enumerate(zip(original_lines, cleaned_lines)):
            orig_indent = len(orig) - len(orig.lstrip())
            clean_indent = len(clean) - len(clean.lstrip())
            
            logger.info(f"Line {i+1}: Original indent={orig_indent}, Cleaned indent={clean_indent}")
            
            if orig_indent != clean_indent:
                logger.warning(f"❌ Indentation mismatch on line {i+1}")
                indentation_preserved = False
            else:
                logger.info(f"✅ Line {i+1} indentation preserved")
        
        if indentation_preserved:
            logger.info("✅ Content cleaning preserves indentation correctly")
            return True
        else:
            logger.error("❌ Content cleaning damaged indentation")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

def test_applescript_indentation():
    """Test AppleScript typing with indented code."""
    logger.info("Testing AppleScript indentation handling...")
    
    # Test code with various indentation levels
    test_code = """def fibonacci(n):
    if n <= 0:
        return []
    else:
        seq = [0, 1]
        while len(seq) < n:
            seq.append(seq[-1] + seq[-2])
        return seq"""
    
    try:
        from modules.automation import AutomationModule
        
        # Create automation module
        automation = AutomationModule()
        
        # Mock subprocess.run to capture AppleScript commands
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
            # Test AppleScript typing
            success = automation._macos_type(test_code)
            
            if success:
                logger.info("✅ AppleScript typing succeeded")
                
                # Analyze the commands to see if indentation is preserved
                keystroke_commands = [cmd for cmd in commands_executed if 'keystroke' in str(cmd.get('cmd', ''))]
                
                logger.info(f"Generated {len(keystroke_commands)} keystroke commands")
                
                # Check if leading spaces are preserved in commands
                lines = test_code.split('\n')
                indented_lines = [line for line in lines if line.startswith('    ')]
                
                logger.info(f"Original code has {len(indented_lines)} indented lines")
                
                # Look for space characters in the commands
                space_preserved = False
                for cmd in keystroke_commands:
                    cmd_str = str(cmd.get('cmd', ''))
                    if '    ' in cmd_str:  # 4 spaces for Python indentation
                        space_preserved = True
                        logger.info("✅ Found indentation spaces in AppleScript commands")
                        break
                
                if not space_preserved:
                    logger.warning("❌ No indentation spaces found in AppleScript commands")
                    logger.info("Sample commands:")
                    for i, cmd in enumerate(keystroke_commands[:3]):
                        logger.info(f"  Command {i+1}: {cmd}")
                
                return space_preserved
            else:
                logger.error("❌ AppleScript typing failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

def test_cliclick_indentation():
    """Test cliclick typing with indented code."""
    logger.info("Testing cliclick indentation handling...")
    
    test_code = """def fibonacci(n):
    if n <= 0:
        return []
    return seq"""
    
    try:
        from modules.automation import AutomationModule
        
        automation = AutomationModule()
        
        # Mock subprocess.run for cliclick
        commands_executed = []
        
        def mock_subprocess_run(cmd, **kwargs):
            commands_executed.append({
                'cmd': cmd,
                'kwargs': kwargs
            })
            result = Mock()
            result.returncode = 0
            result.stderr = ""
            result.stdout = ""
            return result
        
        with patch('subprocess.run', side_effect=mock_subprocess_run):
            # Test cliclick typing
            success = automation._cliclick_type(test_code)
            
            if success:
                logger.info("✅ cliclick typing succeeded")
                
                # Check if the command preserves indentation
                if commands_executed:
                    cmd = commands_executed[0]['cmd']
                    if isinstance(cmd, list) and len(cmd) >= 2:
                        typed_text = cmd[1][2:]  # Remove 't:' prefix
                        
                        logger.info(f"cliclick command text length: {len(typed_text)} chars")
                        
                        # Check if indentation is preserved
                        if '    ' in typed_text and '\n' in typed_text:
                            logger.info("✅ cliclick preserves indentation and newlines")
                            return True
                        else:
                            logger.warning("❌ cliclick missing indentation or newlines")
                            logger.info(f"Sample text: {typed_text[:100]}...")
                            return False
                    else:
                        logger.warning("❌ Unexpected cliclick command format")
                        return False
                else:
                    logger.warning("❌ No cliclick commands executed")
                    return False
            else:
                logger.error("❌ cliclick typing failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

def main():
    """Run indentation preservation tests."""
    logger.info("🧪 Testing Code Indentation Preservation")
    logger.info("=" * 50)
    
    success1 = test_content_cleaning_indentation()
    success2 = test_applescript_indentation()
    success3 = test_cliclick_indentation()
    
    if success1 and success2 and success3:
        logger.info("🎉 All indentation preservation tests passed!")
        logger.info("Code formatting should be properly maintained.")
        return True
    else:
        logger.error("💥 Some indentation preservation tests failed!")
        logger.info("Issues found:")
        if not success1:
            logger.info("  ❌ Content cleaning damages indentation")
        if not success2:
            logger.info("  ❌ AppleScript doesn't preserve indentation")
        if not success3:
            logger.info("  ❌ cliclick doesn't preserve indentation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
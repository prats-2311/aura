#!/usr/bin/env python3
"""
Test Indentation Debug

This test simulates the content generation pipeline to see where indentation is lost.
"""

import sys
import logging

# Setup logging to match AURA's format
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_content_extraction():
    """Simulate the content extraction from API response."""
    logger.info("Simulating content extraction from API response...")
    
    # Simulate different response formats that might come from the API
    test_responses = [
        # OpenAI format with proper indentation
        {
            'choices': [
                {
                    'message': {
                        'content': 'def fibonacci(n):\n    if n <= 0:\n        return []\n    if n == 1:\n        return [0]\n    seq = [0, 1]\n    while len(seq) < n:\n        seq.append(seq[-1] + seq[-2])\n    return seq'
                    }
                }
            ]
        },
        # OpenAI format with single line (problematic)
        {
            'choices': [
                {
                    'message': {
                        'content': 'def fibonacci(n): if n <= 0: return [] if n == 1: return [0] seq = [0, 1] while len(seq) < n: seq.append(seq[-1] + seq[-2]) return seq'
                    }
                }
            ]
        },
        # Direct message format
        {
            'message': 'def fibonacci(n):\n    if n <= 0:\n        return []\n    return seq'
        }
    ]
    
    for i, response in enumerate(test_responses):
        logger.info(f"\n--- Testing Response Format {i+1} ---")
        
        # Simulate the extraction logic from orchestrator
        if isinstance(response, dict) and 'choices' in response:
            choices = response.get('choices', [])
            if choices and isinstance(choices, list) and len(choices) > 0:
                first_choice = choices[0]
                if isinstance(first_choice, dict) and 'message' in first_choice:
                    message = first_choice.get('message', {})
                    if isinstance(message, dict) and 'content' in message:
                        generated_content = message.get('content', '').strip()
                    else:
                        generated_content = str(message).strip()
                else:
                    generated_content = str(first_choice).strip()
            else:
                generated_content = str(response).strip()
        elif isinstance(response, dict) and 'message' in response:
            generated_content = response.get('message', '').strip()
        else:
            generated_content = str(response).strip()
        
        # Debug the extracted content
        logger.debug(f"Extracted content: {len(generated_content)} chars")
        
        # Check indentation
        if generated_content:
            lines = generated_content.split('\n')
            indented_lines = [line for line in lines if line.startswith('    ')]
            logger.debug(f"INDENTATION CHECK - Total lines: {len(lines)}, Indented lines: {len(indented_lines)}")
            
            if len(lines) > 1:
                logger.debug(f"INDENTATION SAMPLE - First 3 lines:")
                for j, line in enumerate(lines[:3]):
                    spaces = len(line) - len(line.lstrip())
                    logger.debug(f"  Line {j+1}: {spaces} spaces | '{line}'")
                    
                if len(indented_lines) > 0:
                    logger.info(f"✅ Response {i+1}: Has proper indentation")
                else:
                    logger.warning(f"❌ Response {i+1}: Missing indentation")
            else:
                logger.warning(f"❌ Response {i+1}: Single line format (problematic)")

def simulate_applescript_processing():
    """Simulate AppleScript line processing."""
    logger.info("\nSimulating AppleScript line processing...")
    
    # Test with properly formatted code
    test_code = """def fibonacci(n):
    if n <= 0:
        return []
    if n == 1:
        return [0]
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq"""
    
    logger.info("Processing code through AppleScript simulation:")
    
    lines = test_code.split('\n')
    
    for i, line in enumerate(lines):
        if line:  # Only process non-empty lines
            # Check line indentation before processing
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces > 0:
                logger.debug(f"AppleScript typing line {i+1} with {leading_spaces} leading spaces: '{line}'")
            
            # Escape special characters for AppleScript
            escaped_line = line.replace('\\', '\\\\').replace('"', '\\"').replace('\r', '\\r')
            
            # Verify spaces preserved after escaping
            escaped_spaces = len(escaped_line) - len(escaped_line.lstrip())
            if leading_spaces != escaped_spaces:
                logger.error(f"INDENTATION LOST during escaping! Original: {leading_spaces} spaces, Escaped: {escaped_spaces} spaces")
            else:
                if leading_spaces > 0:
                    logger.info(f"✅ Line {i+1}: Indentation preserved ({leading_spaces} spaces)")
        
        # Simulate return key press between lines
        if i < len(lines) - 1:
            logger.debug(f"Adding return key after line {i+1}")

def main():
    """Run indentation debugging simulation."""
    logger.info("🧪 Testing Indentation Debug Pipeline")
    logger.info("=" * 50)
    
    simulate_content_extraction()
    simulate_applescript_processing()
    
    logger.info("\n🎯 Summary:")
    logger.info("This test simulates the content generation pipeline.")
    logger.info("Run AURA with debug logging to see where indentation is actually lost.")
    logger.info("Look for 'INDENTATION CHECK' messages in the logs.")

if __name__ == "__main__":
    main()
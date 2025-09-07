#!/usr/bin/env python3
"""
Extract text content from any available browser

This script finds running browsers and extracts content from them,
even if they're not the currently active application.
"""

import sys
import os
import logging
import subprocess

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_running_browsers():
    """Find all running browser applications."""
    
    print("🔍 Searching for running browsers...")
    
    browsers = []
    
    # Common browser bundle IDs and names
    browser_info = [
        ("com.google.Chrome", "Google Chrome", "chrome"),
        ("com.apple.Safari", "Safari", "safari"),
        ("org.mozilla.firefox", "Firefox", "firefox"),
        ("com.microsoft.edgemac", "Microsoft Edge", "edge")
    ]
    
    try:
        # Get list of running applications
        result = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to get name of every process whose background only is false'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            running_apps = [app.strip() for app in result.stdout.split(',')]
            
            for bundle_id, app_name, browser_type in browser_info:
                if app_name in running_apps:
                    browsers.append({
                        'name': app_name,
                        'bundle_id': bundle_id,
                        'browser_type': browser_type
                    })
                    print(f"✓ Found {app_name}")
        
    except Exception as e:
        print(f"⚠️  Error finding browsers: {e}")
    
    return browsers

def get_browser_process_id(app_name):
    """Get process ID for a browser application."""
    
    try:
        result = subprocess.run(
            ["pgrep", "-f", app_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            return int(pids[0])  # Return first PID
    except:
        pass
    
    return None

def extract_chrome_content_applescript():
    """Extract content from Chrome using AppleScript directly."""
    
    print("\n📄 Extracting content from Chrome using AppleScript...")
    
    try:
        applescript = '''
        tell application "Google Chrome"
            if (count of windows) > 0 then
                tell active tab of front window
                    set pageTitle to title
                    set pageURL to URL
                    set pageText to execute javascript "
                        // Remove scripts and styles
                        var scripts = document.querySelectorAll('script, style, noscript');
                        for (var i = 0; i < scripts.length; i++) {
                            scripts[i].remove();
                        }
                        
                        // Get text content
                        var textContent = document.body.innerText || document.body.textContent || '';
                        
                        // Clean up whitespace
                        textContent = textContent.replace(/\\s+/g, ' ').trim();
                        
                        textContent;
                    "
                    return "TITLE: " & pageTitle & "\\nURL: " & pageURL & "\\nCONTENT: " & pageText
                end tell
            else
                return "No Chrome windows open"
            end if
        end tell
        '''
        
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0 and result.stdout.strip():
            content = result.stdout.strip()
            
            # Parse the result
            lines = content.split('\n', 2)
            if len(lines) >= 3:
                title = lines[0].replace('TITLE: ', '')
                url = lines[1].replace('URL: ', '')
                text_content = lines[2].replace('CONTENT: ', '')
                
                print(f"✓ Successfully extracted content from Chrome")
                print(f"  - Title: {title}")
                print(f"  - URL: {url}")
                print(f"  - Content length: {len(text_content)} characters")
                
                return {
                    'title': title,
                    'url': url,
                    'content': text_content,
                    'success': True
                }
            else:
                print(f"⚠️  Unexpected response format: {content}")
                return {'success': False, 'error': 'Unexpected response format'}
        else:
            print(f"❌ AppleScript failed: {result.stderr}")
            return {'success': False, 'error': result.stderr}
            
    except subprocess.TimeoutExpired:
        print("❌ AppleScript timed out")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        print(f"❌ Error running AppleScript: {e}")
        return {'success': False, 'error': str(e)}

def extract_safari_content_applescript():
    """Extract content from Safari using AppleScript directly."""
    
    print("\n📄 Extracting content from Safari using AppleScript...")
    
    try:
        applescript = '''
        tell application "Safari"
            if (count of windows) > 0 then
                tell front document
                    set pageTitle to name
                    set pageURL to URL
                    set pageText to do JavaScript "
                        // Remove scripts and styles
                        var scripts = document.querySelectorAll('script, style, noscript');
                        for (var i = 0; i < scripts.length; i++) {
                            scripts[i].remove();
                        }
                        
                        // Get text content
                        var textContent = document.body.innerText || document.body.textContent || '';
                        
                        // Clean up whitespace
                        textContent = textContent.replace(/\\\\s+/g, ' ').trim();
                        
                        textContent;
                    "
                    return "TITLE: " & pageTitle & "\\nURL: " & pageURL & "\\nCONTENT: " & pageText
                end tell
            else
                return "No Safari windows open"
            end if
        end tell
        '''
        
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0 and result.stdout.strip():
            content = result.stdout.strip()
            
            # Parse the result
            lines = content.split('\n', 2)
            if len(lines) >= 3:
                title = lines[0].replace('TITLE: ', '')
                url = lines[1].replace('URL: ', '')
                text_content = lines[2].replace('CONTENT: ', '')
                
                print(f"✓ Successfully extracted content from Safari")
                print(f"  - Title: {title}")
                print(f"  - URL: {url}")
                print(f"  - Content length: {len(text_content)} characters")
                
                return {
                    'title': title,
                    'url': url,
                    'content': text_content,
                    'success': True
                }
            else:
                print(f"⚠️  Unexpected response format: {content}")
                return {'success': False, 'error': 'Unexpected response format'}
        else:
            print(f"❌ AppleScript failed: {result.stderr}")
            return {'success': False, 'error': result.stderr}
            
    except subprocess.TimeoutExpired:
        print("❌ AppleScript timed out")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        print(f"❌ Error running AppleScript: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """Main extraction function."""
    
    print("=" * 60)
    print("Browser Content Extraction Tool")
    print("=" * 60)
    
    # Find running browsers
    browsers = find_running_browsers()
    
    if not browsers:
        print("❌ No browsers found running")
        print("Please open Chrome or Safari with a webpage and try again")
        return False
    
    print(f"\n✓ Found {len(browsers)} browser(s) running")
    
    results = []
    
    # Try to extract from each browser
    for browser in browsers:
        print(f"\n{'='*40}")
        print(f"Trying {browser['name']}")
        print(f"{'='*40}")
        
        if browser['name'] == 'Google Chrome':
            result = extract_chrome_content_applescript()
            if result['success']:
                results.append(('Chrome', result))
        
        elif browser['name'] == 'Safari':
            result = extract_safari_content_applescript()
            if result['success']:
                results.append(('Safari', result))
        
        else:
            print(f"⚠️  {browser['name']} extraction not implemented yet")
    
    # Display results
    if results:
        print("\n" + "=" * 60)
        print("EXTRACTION RESULTS")
        print("=" * 60)
        
        for browser_name, result in results:
            print(f"\n🌐 {browser_name}:")
            print(f"📄 Title: {result['title']}")
            print(f"🔗 URL: {result['url']}")
            print(f"📊 Content: {len(result['content'])} characters")
            
            if len(result['content']) > 100:
                print(f"\n📝 Content Preview:")
                print("-" * 40)
                print(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
                print("-" * 40)
            
            # Test our validation logic
            try:
                from handlers.question_answering_handler import QuestionAnsweringHandler
                from unittest.mock import Mock
                
                handler = QuestionAnsweringHandler(Mock())
                is_valid = handler._validate_browser_content(result['content'])
                print(f"✅ Content validation: {'PASSED' if is_valid else 'FAILED'}")
                
                if len(result['content']) > 50:
                    word_count = len(result['content'].split())
                    print(f"📈 Statistics: {word_count} words, {len(result['content'])} chars")
                
            except Exception as e:
                print(f"⚠️  Could not validate content: {e}")
        
        return True
    else:
        print("\n❌ No content could be extracted from any browser")
        print("\nTroubleshooting:")
        print("1. Make sure browsers have webpages loaded (not blank tabs)")
        print("2. Check accessibility permissions for Terminal/Python")
        print("3. Try refreshing the webpages")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
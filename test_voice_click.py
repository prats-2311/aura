#!/usr/bin/env python3
"""
Test the full AURA voice-to-click pipeline
"""

import subprocess
import time
import signal
import sys

def test_voice_click():
    """Test the complete voice-to-click functionality"""
    print("🎤 AURA Voice Click Test")
    print("=" * 30)
    
    print("📋 Test Instructions:")
    print("1. This will start AURA")
    print("2. Wait for 'AURA is ready' message")
    print("3. Say 'Computer' to activate")
    print("4. Say 'Click on the sign in button' (or any click command)")
    print("5. AURA will analyze the screen and attempt to click")
    print("6. Press Ctrl+C to stop when done")
    print()
    
    print("💡 Tips:")
    print("• Make sure your target webpage/app is visible")
    print("• Speak clearly after saying 'Computer'")
    print("• The click will happen where AURA thinks the button is")
    print()
    
    input("Press Enter to start AURA...")
    
    try:
        # Start AURA
        print("🚀 Starting AURA...")
        process = subprocess.Popen(
            ['python', 'main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("✅ AURA started! Monitoring output...")
        print("=" * 50)
        
        # Monitor output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                
                # Look for key events
                if "AURA is ready" in output:
                    print("\n🎉 AURA is ready! Say 'Computer' to activate")
                elif "Wake word detected" in output:
                    print("\n👂 Wake word detected! Now say your click command")
                elif "Successfully executed action: click" in output:
                    print("\n✅ CLICK EXECUTED! Check if it worked")
                elif "AppKit" in output or "NSEvent" in output:
                    print("\n❌ AppKit error detected!")
                    break
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping AURA...")
        process.terminate()
        process.wait()
        print("✅ AURA stopped")
    
    except Exception as e:
        print(f"\n❌ Error running AURA: {e}")

if __name__ == "__main__":
    test_voice_click()
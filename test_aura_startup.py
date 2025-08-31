#!/usr/bin/env python3
"""
Test AURA startup to check if the AppKit error is resolved.
"""

import sys
import time
import signal
from main import main as aura_main
import threading

def test_aura_startup():
    """Test AURA startup for AppKit errors"""
    print("🚀 Testing AURA startup...")
    
    # Set up a timeout
    def timeout_handler():
        print("\n⏰ Timeout reached - AURA startup test completed")
        sys.exit(0)
    
    # Start timeout timer
    timer = threading.Timer(10.0, timeout_handler)
    timer.start()
    
    try:
        # Try to start AURA
        aura_main()
    except KeyboardInterrupt:
        print("\n🛑 AURA startup interrupted")
    except Exception as e:
        if "AppKit" in str(e) or "NSEvent" in str(e):
            print(f"\n❌ AppKit error still present: {e}")
            return False
        else:
            print(f"\n⚠️  Other error (not AppKit): {e}")
    finally:
        timer.cancel()
    
    return True

if __name__ == "__main__":
    print("🧪 AURA Startup Test")
    print("=" * 30)
    
    success = test_aura_startup()
    
    if success:
        print("\n✅ No AppKit errors detected during startup!")
    else:
        print("\n❌ AppKit errors still present!")
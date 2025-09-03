#!/usr/bin/env python3
"""
Simple Accessibility Test Script
"""

def test_accessibility():
    print("🧪 Testing Accessibility API...")
    
    try:
        # Test PyObjC import
        import objc
        print("✅ PyObjC import: OK")
        
        # Test AppKit import
        from AppKit import NSWorkspace, AXUIElementCreateSystemWide
        print("✅ AppKit import: OK")
        
        # Test NSWorkspace
        workspace = NSWorkspace.sharedWorkspace()
        if workspace:
            print("✅ NSWorkspace: OK")
            
            # Get frontmost app
            app = workspace.frontmostApplication()
            if app:
                print(f"✅ Frontmost app: {app.localizedName()}")
            else:
                print("⚠️  No frontmost app detected")
        else:
            print("❌ NSWorkspace: Failed")
            return False
        
        # Test AXUIElement
        system_wide = AXUIElementCreateSystemWide()
        if system_wide:
            print("✅ AXUIElementCreateSystemWide: OK")
            print("🎉 Accessibility API is working!")
            return True
        else:
            print("❌ AXUIElementCreateSystemWide: Failed (permissions needed)")
            print("📋 Please grant accessibility permissions in System Preferences")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_accessibility()

#!/usr/bin/env python3
"""
Fixed Accessibility Module Test

This version uses the correct import paths for macOS accessibility functions.
"""

def test_accessibility_fixed():
    print("🧪 Testing Fixed Accessibility Implementation...")
    
    try:
        # Method 1: Import from ApplicationServices (correct way)
        try:
            from ApplicationServices import AXUIElementCreateSystemWide
            print("✅ Method 1: AXUIElementCreateSystemWide imported from ApplicationServices")
            
            # Test system-wide element creation
            system_wide = AXUIElementCreateSystemWide()
            if system_wide:
                print("✅ System-wide element created successfully!")
                print("🎉 Accessibility permissions are working!")
                return True
            else:
                print("❌ System-wide element creation returned None")
                print("📋 This means accessibility permissions are not granted")
                return False
                
        except ImportError:
            print("⚠️  Method 1 failed, trying Method 2...")
            
            # Method 2: Load bundle manually
            import objc
            bundle = objc.loadBundle('ApplicationServices', globals())
            
            if 'AXUIElementCreateSystemWide' in globals():
                print("✅ Method 2: AXUIElementCreateSystemWide loaded via bundle")
                
                system_wide = AXUIElementCreateSystemWide()
                if system_wide:
                    print("✅ System-wide element created successfully!")
                    print("🎉 Accessibility permissions are working!")
                    return True
                else:
                    print("❌ System-wide element creation returned None")
                    return False
            else:
                print("❌ Method 2: Could not load AXUIElementCreateSystemWide")
                return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_nsworkspace():
    print("\n🧪 Testing NSWorkspace...")
    
    try:
        from AppKit import NSWorkspace
        workspace = NSWorkspace.sharedWorkspace()
        
        if workspace:
            print("✅ NSWorkspace created successfully")
            
            # Get frontmost application
            app = workspace.frontmostApplication()
            if app:
                print(f"✅ Frontmost app: {app.localizedName()}")
            else:
                print("⚠️  No frontmost app detected")
            
            return True
        else:
            print("❌ NSWorkspace creation failed")
            return False
            
    except Exception as e:
        print(f"❌ NSWorkspace error: {e}")
        return False

def main():
    print("🔧 AURA Accessibility Fix Test")
    print("=" * 40)
    
    # Test accessibility
    accessibility_works = test_accessibility_fixed()
    
    # Test NSWorkspace
    nsworkspace_works = test_nsworkspace()
    
    print("\n" + "=" * 40)
    print("📊 RESULTS:")
    print(f"Accessibility API: {'✅ Working' if accessibility_works else '❌ Not Working'}")
    print(f"NSWorkspace API: {'✅ Working' if nsworkspace_works else '❌ Not Working'}")
    
    if accessibility_works and nsworkspace_works:
        print("\n🎉 All tests passed! AURA accessibility should work now.")
    elif nsworkspace_works:
        print("\n⚠️  NSWorkspace works but accessibility permissions needed.")
        print("Please grant accessibility permissions in System Preferences.")
    else:
        print("\n❌ Tests failed. PyObjC installation may need fixing.")

if __name__ == "__main__":
    main()

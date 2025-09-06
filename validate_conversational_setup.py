#!/usr/bin/env python3
"""
AURA Conversational Enhancement Setup Validation Script

This script validates that all dependencies and configuration settings
for the conversational enhancement features are properly set up.
"""

import sys
import os
import importlib
from pathlib import Path

def check_python_version():
    """Check if Python version meets requirements."""
    print("🔍 Checking Python version...")
    if sys.version_info >= (3, 11):
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - OK")
        return True
    else:
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - Requires 3.11+")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n🔍 Checking dependencies...")
    
    required_deps = [
        ('pynput', 'Global mouse and keyboard event handling'),
        ('requests', 'HTTP requests for API communication'),
        ('pygame', 'Audio playback for feedback'),
        ('pyttsx3', 'Text-to-speech for conversations'),
        ('ollama', 'Ollama Cloud API client'),
    ]
    
    optional_deps = [
        ('transformers', 'Hugging Face transformers'),
        ('torch', 'PyTorch for local inference'),
    ]
    
    all_good = True
    
    for dep_name, description in required_deps:
        try:
            importlib.import_module(dep_name)
            print(f"✅ {dep_name} - {description}")
        except ImportError:
            print(f"❌ {dep_name} - {description} (REQUIRED)")
            all_good = False
    
    print("\n📦 Optional dependencies:")
    for dep_name, description in optional_deps:
        try:
            importlib.import_module(dep_name)
            print(f"✅ {dep_name} - {description}")
        except ImportError:
            print(f"⚠️  {dep_name} - {description} (optional)")
    
    return all_good

def check_pynput_functionality():
    """Test pynput mouse and keyboard functionality."""
    print("\n🔍 Testing pynput functionality...")
    
    try:
        from pynput import mouse, keyboard
        print("✅ pynput mouse and keyboard modules imported")
        
        # Test mouse listener creation (don't start it)
        def dummy_callback(*args):
            pass
        
        listener = mouse.Listener(on_click=dummy_callback)
        print("✅ Mouse listener can be created")
        
        # Test keyboard listener creation (don't start it)
        kb_listener = keyboard.Listener(on_press=dummy_callback)
        print("✅ Keyboard listener can be created")
        
        return True
        
    except Exception as e:
        print(f"❌ pynput functionality test failed: {e}")
        return False

def check_config_file():
    """Check if config.py exists and can be imported."""
    print("\n🔍 Checking configuration file...")
    
    try:
        import config
        print("✅ config.py imported successfully")
        
        # Check for required configuration attributes
        required_attrs = [
            'INTENT_RECOGNITION_PROMPT',
            'CONVERSATIONAL_PROMPT', 
            'CODE_GENERATION_PROMPT',
            'DEFERRED_ACTION_TIMEOUT',
            'MOUSE_LISTENER_SENSITIVITY',
            'CONVERSATION_CONTEXT_SIZE',
            'INTENT_CONFIDENCE_THRESHOLD'
        ]
        
        missing_attrs = []
        for attr in required_attrs:
            if not hasattr(config, attr):
                missing_attrs.append(attr)
        
        if missing_attrs:
            print(f"❌ Missing configuration attributes: {missing_attrs}")
            return False
        else:
            print("✅ All required configuration attributes present")
            return True
            
    except ImportError as e:
        print(f"❌ Cannot import config.py: {e}")
        return False

def check_configuration_validation():
    """Run configuration validation functions."""
    print("\n🔍 Running configuration validation...")
    
    try:
        from config import validate_config, validate_conversational_config
        
        # Run main config validation
        config_result = validate_config()
        if isinstance(config_result, tuple) and len(config_result) == 3:
            config_valid, errors, warnings = config_result
        elif isinstance(config_result, tuple) and len(config_result) == 2:
            errors, warnings = config_result
            config_valid = len(errors) == 0
        else:
            config_valid = bool(config_result)
            errors, warnings = [], []
        
        # Run conversational config validation
        conv_errors, conv_warnings = validate_conversational_config()
        
        all_errors = errors + conv_errors
        all_warnings = warnings + conv_warnings
        
        if all_errors:
            print("❌ Configuration validation errors:")
            for error in all_errors:
                print(f"   - {error}")
            return False
        else:
            print("✅ Configuration validation passed")
        
        if all_warnings:
            print("⚠️  Configuration warnings:")
            for warning in all_warnings:
                print(f"   - {warning}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def check_file_structure():
    """Check if required files and directories exist."""
    print("\n🔍 Checking file structure...")
    
    required_files = [
        'config.py',
        'orchestrator.py',
        'requirements.txt',
        'modules/__init__.py',
        'utils/__init__.py',
    ]
    
    optional_files = [
        'utils/mouse_listener.py',
        'modules/reasoning.py',
        'assets/sounds/success.wav',
        'assets/sounds/failure.wav',
        'assets/sounds/thinking.wav',
    ]
    
    all_good = True
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (REQUIRED)")
            all_good = False
    
    print("\n📁 Optional files:")
    for file_path in optional_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"⚠️  {file_path} (optional)")
    
    return all_good

def check_permissions():
    """Check system permissions (platform-specific)."""
    print("\n🔍 Checking system permissions...")
    
    if sys.platform == 'darwin':  # macOS
        print("📱 macOS detected - checking accessibility permissions...")
        try:
            # Try to import macOS accessibility frameworks
            from AppKit import NSWorkspace
            print("✅ macOS accessibility frameworks available")
            
            # Note: Actual permission checking requires running the app
            print("ℹ️  Accessibility permissions will be checked when AURA runs")
            print("   If prompted, grant accessibility access in System Preferences")
            
        except ImportError:
            print("❌ macOS accessibility frameworks not available")
            print("   Install with: pip install pyobjc pyobjc-framework-ApplicationServices")
            return False
            
    elif sys.platform == 'win32':  # Windows
        print("🪟 Windows detected - checking Windows API access...")
        try:
            import win32api
            print("✅ Windows API access available")
        except ImportError:
            print("❌ Windows API not available")
            print("   Install with: pip install pywin32")
            return False
            
    elif sys.platform.startswith('linux'):  # Linux
        print("🐧 Linux detected - checking X11 libraries...")
        try:
            import Xlib
            print("✅ X11 libraries available")
        except ImportError:
            print("❌ X11 libraries not available")
            print("   Install with: pip install python-xlib")
            return False
    
    return True

def main():
    """Run all validation checks."""
    print("🚀 AURA Conversational Enhancement Setup Validation")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("pynput Functionality", check_pynput_functionality),
        ("Configuration File", check_config_file),
        ("Configuration Validation", check_configuration_validation),
        ("File Structure", check_file_structure),
        ("System Permissions", check_permissions),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed with exception: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print(f"\n📈 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All validation checks passed!")
        print("✅ Your system is ready for AURA conversational enhancement features")
        print("\nNext steps:")
        print("1. Run 'python main.py' to start AURA")
        print("2. Try conversational commands like 'hello' or 'how are you?'")
        print("3. Test deferred actions like 'write a python function to sort a list'")
        return True
    else:
        print(f"\n⚠️  {total - passed} validation checks failed")
        print("Please address the failed checks before using conversational features")
        print("\nFor help, see:")
        print("- CONVERSATIONAL_ENHANCEMENT_SETUP.md")
        print("- requirements.txt")
        print("- config.py")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Comprehensive Accessibility Permissions Diagnostic Tool

This tool will help identify exactly why accessibility permissions aren't working
despite being granted in System Preferences.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import json

def setup_logging():
    """Setup detailed logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_python_executable_info():
    """Get detailed information about the Python executable."""
    logger = logging.getLogger(__name__)
    
    info = {
        'sys_executable': sys.executable,
        'which_python': None,
        'which_python3': None,
        'real_path': None,
        'is_symlink': False,
        'conda_env': None,
        'virtual_env': None
    }
    
    # Get sys.executable info
    logger.info(f"sys.executable: {sys.executable}")
    
    # Check if it's a symlink
    if os.path.islink(sys.executable):
        info['is_symlink'] = True
        info['real_path'] = os.path.realpath(sys.executable)
        logger.info(f"Python executable is a symlink to: {info['real_path']}")
    else:
        info['real_path'] = sys.executable
        logger.info(f"Python executable is not a symlink")
    
    # Get which python
    try:
        result = subprocess.run(['which', 'python'], capture_output=True, text=True)
        if result.returncode == 0:
            info['which_python'] = result.stdout.strip()
            logger.info(f"which python: {info['which_python']}")
    except:
        pass
    
    # Get which python3
    try:
        result = subprocess.run(['which', 'python3'], capture_output=True, text=True)
        if result.returncode == 0:
            info['which_python3'] = result.stdout.strip()
            logger.info(f"which python3: {info['which_python3']}")
    except:
        pass
    
    # Check for conda environment
    if 'CONDA_DEFAULT_ENV' in os.environ:
        info['conda_env'] = os.environ['CONDA_DEFAULT_ENV']
        logger.info(f"Conda environment: {info['conda_env']}")
    
    # Check for virtual environment
    if 'VIRTUAL_ENV' in os.environ:
        info['virtual_env'] = os.environ['VIRTUAL_ENV']
        logger.info(f"Virtual environment: {info['virtual_env']}")
    
    return info

def check_accessibility_api_directly():
    """Check accessibility API directly using PyObjC."""
    logger = logging.getLogger(__name__)
    
    try:
        # Try to import PyObjC accessibility frameworks
        from ApplicationServices import AXIsProcessTrusted, AXIsProcessTrustedWithOptions
        from CoreFoundation import (
            kCFBooleanTrue,
            CFDictionaryCreateMutable,
            kCFTypeDictionaryKeyCallBacks,
            kCFTypeDictionaryValueCallBacks,
            CFDictionarySetValue,
            CFStringCreateWithCString,
            kCFStringEncodingUTF8
        )
        
        logger.info("✅ PyObjC accessibility frameworks imported successfully")
        
        # Check if process is trusted (basic check)
        is_trusted_basic = AXIsProcessTrusted()
        logger.info(f"AXIsProcessTrusted() result: {is_trusted_basic}")
        
        # Check with prompt option
        options = CFDictionaryCreateMutable(
            None, 0, 
            kCFTypeDictionaryKeyCallBacks, 
            kCFTypeDictionaryValueCallBacks
        )
        
        # Add kAXTrustedCheckOptionPrompt key
        prompt_key = CFStringCreateWithCString(None, "AXTrustedCheckOptionPrompt", kCFStringEncodingUTF8)
        CFDictionarySetValue(options, prompt_key, kCFBooleanTrue)
        
        is_trusted_with_prompt = AXIsProcessTrustedWithOptions(options)
        logger.info(f"AXIsProcessTrustedWithOptions() result: {is_trusted_with_prompt}")
        
        return {
            'pyobjc_available': True,
            'basic_check': is_trusted_basic,
            'prompt_check': is_trusted_with_prompt,
            'overall_trusted': is_trusted_basic and is_trusted_with_prompt
        }
        
    except ImportError as e:
        logger.error(f"❌ PyObjC accessibility frameworks not available: {e}")
        return {
            'pyobjc_available': False,
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"❌ Error checking accessibility API: {e}")
        return {
            'pyobjc_available': True,
            'error': str(e)
        }

def check_system_preferences_accessibility():
    """Check what's actually in System Preferences accessibility list."""
    logger = logging.getLogger(__name__)
    
    try:
        # Try to read accessibility database (this might require special permissions)
        result = subprocess.run([
            'sqlite3', 
            '/Library/Application Support/com.apple.TCC/TCC.db',
            'SELECT client FROM access WHERE service="kTCCServiceAccessibility" AND allowed=1;'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            allowed_clients = result.stdout.strip().split('\n')
            logger.info("Applications with accessibility permissions:")
            for client in allowed_clients:
                if client:
                    logger.info(f"  - {client}")
            return allowed_clients
        else:
            logger.warning("Could not read TCC database (requires special permissions)")
            return None
            
    except Exception as e:
        logger.warning(f"Could not check TCC database: {e}")
        return None

def test_accessibility_functions():
    """Test specific accessibility functions that AURA uses."""
    logger = logging.getLogger(__name__)
    
    try:
        from ApplicationServices import (
            AXUIElementCreateSystemWide,
            AXUIElementCopyAttributeValue,
            kAXFocusedApplicationAttribute
        )
        
        logger.info("Testing accessibility functions...")
        
        # Test system-wide element access
        system_element = AXUIElementCreateSystemWide()
        logger.info("✅ AXUIElementCreateSystemWide() successful")
        
        # Test getting focused application
        try:
            focused_app = AXUIElementCopyAttributeValue(system_element, kAXFocusedApplicationAttribute)
            logger.info("✅ AXUIElementCopyAttributeValue() for focused app successful")
            return True
        except Exception as e:
            logger.error(f"❌ AXUIElementCopyAttributeValue() failed: {e}")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Could not import accessibility functions: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing accessibility functions: {e}")
        return False

def generate_permission_commands():
    """Generate specific commands to add permissions."""
    logger = logging.getLogger(__name__)
    python_info = get_python_executable_info()
    
    logger.info("\n" + "="*60)
    logger.info("PERMISSION SETUP COMMANDS")
    logger.info("="*60)
    
    # All possible Python executables to add
    executables_to_add = set()
    
    if python_info['sys_executable']:
        executables_to_add.add(python_info['sys_executable'])
    if python_info['real_path'] and python_info['real_path'] != python_info['sys_executable']:
        executables_to_add.add(python_info['real_path'])
    if python_info['which_python']:
        executables_to_add.add(python_info['which_python'])
    if python_info['which_python3']:
        executables_to_add.add(python_info['which_python3'])
    
    logger.info("Add these executables to System Preferences > Security & Privacy > Accessibility:")
    for executable in executables_to_add:
        logger.info(f"  📁 {executable}")
    
    # Terminal applications to add
    logger.info("\nAlso add your Terminal application:")
    terminal_apps = [
        "/Applications/Terminal.app",
        "/Applications/iTerm.app",
        "/Applications/Utilities/Terminal.app"
    ]
    
    for terminal in terminal_apps:
        if os.path.exists(terminal):
            logger.info(f"  📁 {terminal}")
    
    # IDE applications (common ones)
    logger.info("\nIf running from an IDE, also add:")
    ide_apps = [
        "/Applications/Visual Studio Code.app",
        "/Applications/PyCharm CE.app",
        "/Applications/PyCharm.app",
        "/Applications/Sublime Text.app",
        "/Applications/Atom.app"
    ]
    
    for ide in ide_apps:
        if os.path.exists(ide):
            logger.info(f"  📁 {ide}")

def run_comprehensive_diagnosis():
    """Run comprehensive diagnosis of accessibility permissions."""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("COMPREHENSIVE ACCESSIBILITY PERMISSIONS DIAGNOSIS")
    logger.info("="*60)
    
    # Step 1: Python executable information
    logger.info("\n1. PYTHON EXECUTABLE ANALYSIS")
    logger.info("-" * 40)
    python_info = get_python_executable_info()
    
    # Step 2: Direct accessibility API check
    logger.info("\n2. ACCESSIBILITY API CHECK")
    logger.info("-" * 40)
    api_check = check_accessibility_api_directly()
    
    # Step 3: Test accessibility functions
    logger.info("\n3. ACCESSIBILITY FUNCTIONS TEST")
    logger.info("-" * 40)
    functions_work = test_accessibility_functions()
    
    # Step 4: Check system preferences
    logger.info("\n4. SYSTEM PREFERENCES CHECK")
    logger.info("-" * 40)
    tcc_clients = check_system_preferences_accessibility()
    
    # Step 5: Generate specific commands
    logger.info("\n5. PERMISSION SETUP COMMANDS")
    logger.info("-" * 40)
    generate_permission_commands()
    
    # Step 6: Advanced troubleshooting
    logger.info("\n6. ADVANCED TROUBLESHOOTING")
    logger.info("-" * 40)
    
    if not api_check.get('overall_trusted', False):
        logger.info("🔧 ADVANCED TROUBLESHOOTING STEPS:")
        logger.info("1. Remove ALL Python-related entries from Accessibility preferences")
        logger.info("2. Restart your Mac completely")
        logger.info("3. Re-add ONLY the main Python executable:")
        logger.info(f"   {python_info['sys_executable']}")
        logger.info("4. If using Terminal, also add Terminal.app")
        logger.info("5. Restart AURA")
        
        logger.info("\n🔧 ALTERNATIVE APPROACH:")
        logger.info("1. Try running AURA with sudo (temporarily for testing):")
        logger.info("   sudo python main.py")
        logger.info("2. If that works, the issue is definitely permissions")
        
        logger.info("\n🔧 NUCLEAR OPTION:")
        logger.info("1. Reset TCC database (requires admin):")
        logger.info("   sudo tccutil reset Accessibility")
        logger.info("2. Restart Mac")
        logger.info("3. Re-grant permissions when prompted")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("DIAGNOSIS SUMMARY")
    logger.info("="*60)
    logger.info(f"PyObjC Available: {'✅' if api_check.get('pyobjc_available') else '❌'}")
    logger.info(f"Basic Trust Check: {'✅' if api_check.get('basic_check') else '❌'}")
    logger.info(f"Prompt Trust Check: {'✅' if api_check.get('prompt_check') else '❌'}")
    logger.info(f"Functions Working: {'✅' if functions_work else '❌'}")
    
    if api_check.get('overall_trusted') and functions_work:
        logger.info("\n🎉 ACCESSIBILITY PERMISSIONS ARE WORKING!")
        logger.info("The issue might be elsewhere in the AURA code.")
    else:
        logger.info("\n❌ ACCESSIBILITY PERMISSIONS NEED FIXING")
        logger.info("Follow the troubleshooting steps above.")
    
    return {
        'python_info': python_info,
        'api_check': api_check,
        'functions_work': functions_work,
        'tcc_clients': tcc_clients
    }

if __name__ == "__main__":
    try:
        diagnosis = run_comprehensive_diagnosis()
        
        # Save diagnosis to file
        with open('accessibility_diagnosis.json', 'w') as f:
            json.dump(diagnosis, f, indent=2, default=str)
        
        print("\n📄 Diagnosis saved to: accessibility_diagnosis.json")
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        sys.exit(1)
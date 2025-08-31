#!/usr/bin/env python3
"""
AURA Environment Setup Checker

This script helps verify that your environment is set up correctly
according to the plan.md specifications.

Usage:
    python setup_check.py
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version meets requirements."""
    version = sys.version_info
    required = (3, 11)
    
    if version >= required:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (meets requirement: {required[0]}.{required[1]}+)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires: {required[0]}.{required[1]}+)")
        return False

def check_conda_environment():
    """Check if we're in the correct Conda environment."""
    conda_env = os.getenv('CONDA_DEFAULT_ENV')
    
    if conda_env == 'aura':
        print(f"✅ Conda environment: {conda_env}")
        return True
    else:
        print(f"❌ Conda environment: {conda_env or 'None'} (should be 'aura')")
        return False

def check_dependencies():
    """Check if key dependencies are installed."""
    required_packages = [
        'requests', 'mss', 'pyautogui', 'pygame', 
        'whisper', 'pvporcupine', 'torch'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (not installed)")
            missing.append(package)
    
    return len(missing) == 0

def check_api_keys():
    """Check if required API keys are set."""
    keys = {
        'REASONING_API_KEY': 'Cloud reasoning model API key',
        'PORCUPINE_API_KEY': 'Picovoice wake word detection key'
    }
    
    all_set = True
    for key, description in keys.items():
        value = os.getenv(key)
        if value and value != f"your_{key.lower()}_here":
            print(f"✅ {key} is set")
        else:
            print(f"❌ {key} not set ({description})")
            all_set = False
    
    return all_set

def check_project_structure():
    """Check if project structure matches plan.md."""
    required_files = [
        'config.py',
        'orchestrator.py', 
        'main.py',
        'requirements.txt',
        'README.md',
        'modules/__init__.py',
        'modules/vision.py',
        'modules/reasoning.py',
        'modules/audio.py',
        'modules/automation.py',
        'modules/feedback.py',
        'assets/sounds/success.wav',
        'assets/sounds/failure.wav',
        'assets/sounds/thinking.wav'
    ]
    
    missing = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (missing)")
            missing.append(file_path)
    
    return len(missing) == 0

def print_setup_commands():
    """Print the setup commands from plan.md."""
    print("\n" + "="*60)
    print("SETUP COMMANDS (from plan.md)")
    print("="*60)
    print("\n1. Create Conda Environment:")
    print("   conda create --name aura python=3.11 -y")
    print("\n2. Activate Environment:")
    print("   conda activate aura")
    print("\n3. Install Dependencies:")
    print("   pip install -r requirements.txt")
    print("\n4. Set API Keys:")
    print("   export REASONING_API_KEY='your_api_key_here'")
    print("   export PORCUPINE_API_KEY='your_porcupine_key_here'")
    print("\n5. Validate Setup:")
    print("   python config.py")
    print("\n6. Run AURA:")
    print("   python main.py")
    print("\n" + "="*60)

def main():
    """Run all setup checks."""
    print("AURA Environment Setup Checker")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Conda Environment", check_conda_environment),
        ("Project Structure", check_project_structure),
        ("Dependencies", check_dependencies),
        ("API Keys", check_api_keys)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        result = check_func()
        results.append((name, result))
    
    # Summary
    print("\n" + "="*40)
    print("SETUP SUMMARY")
    print("="*40)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All checks passed! AURA is ready to run.")
        print("Run: python main.py")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print_setup_commands()

if __name__ == "__main__":
    main()
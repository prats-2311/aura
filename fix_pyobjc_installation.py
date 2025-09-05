#!/usr/bin/env python3
"""
PyObjC Installation Fix for AURA

This script provides multiple methods to install PyObjC frameworks
for macOS accessibility support.
"""

import subprocess
import sys
import logging
import platform
import os

def setup_logging():
    """Setup logging for the installation process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_system_info():
    """Check system information for compatibility."""
    logger = logging.getLogger(__name__)
    
    logger.info("System Information:")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Architecture: {platform.machine()}")
    
    # Check if we're on macOS
    if platform.system() != 'Darwin':
        logger.error("This script is designed for macOS only!")
        return False
    
    return True

def run_command(command, description):
    """Run a shell command and return success status."""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Running: {description}")
    logger.info(f"Command: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                logger.debug(f"Output: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"❌ {description} - FAILED")
            logger.error(f"Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {description} - TIMEOUT")
        return False
    except Exception as e:
        logger.error(f"❌ {description} - EXCEPTION: {e}")
        return False

def method_1_pip_upgrade():
    """Method 1: Upgrade pip and install PyObjC."""
    logger = logging.getLogger(__name__)
    logger.info("\n=== Method 1: Upgrade pip and install PyObjC ===")
    
    commands = [
        ("python -m pip install --upgrade pip", "Upgrading pip"),
        ("pip install --upgrade setuptools wheel", "Upgrading setuptools and wheel"),
        ("pip install pyobjc", "Installing complete PyObjC framework"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def method_2_specific_frameworks():
    """Method 2: Install specific frameworks individually."""
    logger = logging.getLogger(__name__)
    logger.info("\n=== Method 2: Install specific frameworks ===")
    
    # Try the correct package names
    frameworks = [
        "pyobjc-core",
        "pyobjc-framework-Cocoa",
        "pyobjc-framework-ApplicationServices",
    ]
    
    for framework in frameworks:
        command = f"pip install {framework}"
        if not run_command(command, f"Installing {framework}"):
            logger.warning(f"Failed to install {framework}, continuing...")
    
    return True

def method_3_conda_forge():
    """Method 3: Use conda-forge if conda is available."""
    logger = logging.getLogger(__name__)
    logger.info("\n=== Method 3: Try conda-forge ===")
    
    # Check if conda is available
    if not run_command("conda --version", "Checking conda availability"):
        logger.info("Conda not available, skipping this method")
        return False
    
    commands = [
        ("conda install -c conda-forge pyobjc", "Installing PyObjC via conda-forge"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def method_4_homebrew_python():
    """Method 4: Use Homebrew Python if available."""
    logger = logging.getLogger(__name__)
    logger.info("\n=== Method 4: Try Homebrew Python ===")
    
    # Check if brew is available
    if not run_command("brew --version", "Checking Homebrew availability"):
        logger.info("Homebrew not available, skipping this method")
        return False
    
    commands = [
        ("brew install python", "Ensuring Homebrew Python is installed"),
        ("/opt/homebrew/bin/pip3 install pyobjc", "Installing PyObjC with Homebrew pip"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            logger.warning(f"Command failed: {description}")
    
    return True

def test_installation():
    """Test if PyObjC installation was successful."""
    logger = logging.getLogger(__name__)
    logger.info("\n=== Testing PyObjC Installation ===")
    
    test_imports = [
        ("import objc", "PyObjC core"),
        ("from AppKit import NSWorkspace", "AppKit framework"),
        ("from ApplicationServices import AXUIElementCreateSystemWide", "ApplicationServices framework"),
    ]
    
    success_count = 0
    
    for import_statement, description in test_imports:
        try:
            exec(import_statement)
            logger.info(f"✅ {description} - Import successful")
            success_count += 1
        except ImportError as e:
            logger.error(f"❌ {description} - Import failed: {e}")
        except Exception as e:
            logger.error(f"❌ {description} - Unexpected error: {e}")
    
    if success_count == len(test_imports):
        logger.info("🎉 All PyObjC frameworks installed successfully!")
        return True
    else:
        logger.warning(f"⚠️  Only {success_count}/{len(test_imports)} frameworks working")
        return False

def install_additional_dependencies():
    """Install additional dependencies for AURA."""
    logger = logging.getLogger(__name__)
    logger.info("\n=== Installing Additional Dependencies ===")
    
    dependencies = [
        ("thefuzz[speedup]", "Fuzzy string matching"),
        ("Levenshtein", "Fast string distance calculations"),
    ]
    
    for package, description in dependencies:
        command = f"pip install {package}"
        run_command(command, f"Installing {description}")

def main():
    """Main installation process."""
    logger = setup_logging()
    
    logger.info("PyObjC Installation Fix for AURA")
    logger.info("=" * 50)
    
    # Check system compatibility
    if not check_system_info():
        return False
    
    # Try different installation methods
    methods = [
        method_1_pip_upgrade,
        method_2_specific_frameworks,
        method_3_conda_forge,
        method_4_homebrew_python,
    ]
    
    for i, method in enumerate(methods, 1):
        logger.info(f"\n🔄 Trying installation method {i}...")
        
        try:
            method()
            
            # Test after each method
            if test_installation():
                logger.info(f"✅ Method {i} successful!")
                break
            else:
                logger.info(f"⚠️  Method {i} partially successful, trying next method...")
                
        except Exception as e:
            logger.error(f"❌ Method {i} failed with exception: {e}")
    
    # Final test
    logger.info("\n" + "=" * 50)
    logger.info("FINAL INSTALLATION TEST")
    logger.info("=" * 50)
    
    if test_installation():
        logger.info("🎉 PyObjC installation completed successfully!")
        
        # Install additional dependencies
        install_additional_dependencies()
        
        logger.info("\n📋 Next Steps:")
        logger.info("1. Grant accessibility permissions in System Preferences")
        logger.info("2. Run: python fix_gmail_click_issue.py")
        logger.info("3. Test Gmail click functionality")
        
        return True
    else:
        logger.error("❌ PyObjC installation failed with all methods")
        logger.info("\n🔧 Manual Installation Options:")
        logger.info("1. Try: pip install --no-cache-dir pyobjc")
        logger.info("2. Use system Python: /usr/bin/python3 -m pip install pyobjc")
        logger.info("3. Install Xcode Command Line Tools: xcode-select --install")
        logger.info("4. Check Python version compatibility")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
AURA Setup Wizard

Interactive setup wizard for configuring AURA system.
Guides users through installation, configuration, and validation.
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import requests
import time

# Setup logging for the wizard
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SetupWizard:
    """Interactive setup wizard for AURA."""
    
    def __init__(self):
        """Initialize the setup wizard."""
        self.config = {}
        self.errors = []
        self.warnings = []
        self.setup_steps = [
            ("Environment Check", self.check_environment),
            ("Python Dependencies", self.install_dependencies),
            ("API Configuration", self.configure_apis),
            ("Audio Setup", self.setup_audio),
            ("Service Validation", self.validate_services),
            ("Performance Optimization", self.optimize_performance),
            ("Final Validation", self.final_validation)
        ]
        
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("=" * 60)
        print("    AURA Setup Wizard")
        print("    Autonomous User-side Robotic Assistant")
        print("=" * 60)
        print(f"{Colors.ENDC}")
    
    def run(self) -> bool:
        """
        Run the complete setup wizard.
        
        Returns:
            True if setup completed successfully, False otherwise
        """
        try:
            print(f"\n{Colors.OKBLUE}Welcome to the AURA Setup Wizard!{Colors.ENDC}")
            print("This wizard will guide you through setting up AURA on your system.\n")
            
            # Run all setup steps
            for step_name, step_func in self.setup_steps:
                print(f"{Colors.BOLD}Step: {step_name}{Colors.ENDC}")
                print("-" * 40)
                
                try:
                    success = step_func()
                    if success:
                        print(f"{Colors.OKGREEN}✅ {step_name} completed successfully{Colors.ENDC}\n")
                    else:
                        print(f"{Colors.WARNING}⚠️  {step_name} completed with warnings{Colors.ENDC}\n")
                except Exception as e:
                    print(f"{Colors.FAIL}❌ {step_name} failed: {e}{Colors.ENDC}\n")
                    self.errors.append(f"{step_name}: {e}")
                    
                    # Ask if user wants to continue
                    if not self.ask_yes_no("Continue with setup despite this error?"):
                        return False
            
            # Show final results
            self.show_setup_summary()
            
            return len(self.errors) == 0
            
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Setup interrupted by user{Colors.ENDC}")
            return False
        except Exception as e:
            print(f"\n{Colors.FAIL}Setup failed with error: {e}{Colors.ENDC}")
            return False
    
    def check_environment(self) -> bool:
        """Check system environment and requirements."""
        print("Checking system environment...")
        
        success = True
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 11):
            self.errors.append(f"Python 3.11+ required. Current: {python_version.major}.{python_version.minor}")
            success = False
        else:
            print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check operating system
        import platform
        os_name = platform.system()
        print(f"✅ Operating system: {os_name} {platform.release()}")
        
        # Check available memory
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            if memory_gb < 4:
                self.warnings.append(f"Low memory: {memory_gb:.1f}GB (4GB+ recommended)")
            else:
                print(f"✅ Available memory: {memory_gb:.1f}GB")
        except ImportError:
            self.warnings.append("Could not check memory (psutil not available)")
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage('.')
            free_gb = free / (1024**3)
            if free_gb < 2:
                self.warnings.append(f"Low disk space: {free_gb:.1f}GB (2GB+ recommended)")
            else:
                print(f"✅ Available disk space: {free_gb:.1f}GB")
        except Exception as e:
            self.warnings.append(f"Could not check disk space: {e}")
        
        # Check conda environment
        conda_env = os.getenv('CONDA_DEFAULT_ENV')
        if conda_env != 'aura':
            self.warnings.append(f"Not in 'aura' conda environment. Current: {conda_env or 'None'}")
            print(f"⚠️  Conda environment: {conda_env or 'None'} (should be 'aura')")
        else:
            print(f"✅ Conda environment: {conda_env}")
        
        return success
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies."""
        print("Installing Python dependencies...")
        
        # Check if requirements.txt exists
        if not Path("requirements.txt").exists():
            self.errors.append("requirements.txt not found")
            return False
        
        try:
            # Install dependencies
            print("Running: pip install -r requirements.txt")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                self.errors.append(f"pip install failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.errors.append("Dependency installation timed out")
            return False
        except Exception as e:
            self.errors.append(f"Dependency installation failed: {e}")
            return False
    
    def configure_apis(self) -> bool:
        """Configure API keys and endpoints."""
        print("Configuring API keys and endpoints...")
        
        # Load current configuration
        try:
            from config import (
                REASONING_API_KEY, PORCUPINE_API_KEY,
                VISION_API_BASE, REASONING_API_BASE
            )
        except ImportError as e:
            self.errors.append(f"Could not load configuration: {e}")
            return False
        
        success = True
        
        # Check reasoning API key
        if REASONING_API_KEY == "your_ollama_cloud_api_key_here" or not REASONING_API_KEY:
            print(f"{Colors.WARNING}Reasoning API key not configured{Colors.ENDC}")
            
            if self.ask_yes_no("Would you like to configure the reasoning API key now?"):
                api_key = input("Enter your Ollama Cloud or OpenAI API key: ").strip()
                if api_key:
                    os.environ["REASONING_API_KEY"] = api_key
                    print("✅ Reasoning API key configured")
                else:
                    self.warnings.append("Reasoning API key not provided")
            else:
                self.warnings.append("Reasoning API key not configured")
        else:
            print("✅ Reasoning API key configured")
        
        # Check Porcupine API key
        if PORCUPINE_API_KEY == "your_porcupine_api_key_here" or not PORCUPINE_API_KEY:
            print(f"{Colors.WARNING}Porcupine API key not configured{Colors.ENDC}")
            
            if self.ask_yes_no("Would you like to configure the Porcupine API key now?"):
                api_key = input("Enter your Picovoice Porcupine API key: ").strip()
                if api_key:
                    os.environ["PORCUPINE_API_KEY"] = api_key
                    print("✅ Porcupine API key configured")
                else:
                    self.warnings.append("Porcupine API key not provided")
            else:
                self.warnings.append("Porcupine API key not configured")
        else:
            print("✅ Porcupine API key configured")
        
        return success
    
    def setup_audio(self) -> bool:
        """Setup and test audio devices."""
        print("Setting up audio devices...")
        
        try:
            import sounddevice as sd
            
            # List audio devices
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            output_devices = [d for d in devices if d['max_output_channels'] > 0]
            
            print(f"✅ Found {len(input_devices)} input devices")
            print(f"✅ Found {len(output_devices)} output devices")
            
            if len(input_devices) == 0:
                self.errors.append("No audio input devices found")
                return False
            
            if len(output_devices) == 0:
                self.errors.append("No audio output devices found")
                return False
            
            # Test audio input
            if self.ask_yes_no("Would you like to test audio input?"):
                print("Testing microphone... (speak for 3 seconds)")
                try:
                    import numpy as np
                    
                    # Record 3 seconds of audio
                    duration = 3
                    sample_rate = 16000
                    audio_data = sd.rec(
                        int(duration * sample_rate),
                        samplerate=sample_rate,
                        channels=1,
                        dtype=np.float32
                    )
                    sd.wait()
                    
                    # Check if audio was captured
                    volume = np.sqrt(np.mean(audio_data ** 2))
                    if volume > 0.001:  # Threshold for detecting audio
                        print(f"✅ Audio input test successful (volume: {volume:.4f})")
                    else:
                        self.warnings.append("Audio input test shows very low volume")
                        
                except Exception as e:
                    self.warnings.append(f"Audio input test failed: {e}")
            
            # Test audio output
            if self.ask_yes_no("Would you like to test audio output?"):
                print("Testing speakers... (you should hear a tone)")
                try:
                    import numpy as np
                    
                    # Generate a test tone
                    duration = 1
                    sample_rate = 44100
                    frequency = 440  # A4 note
                    t = np.linspace(0, duration, int(sample_rate * duration))
                    tone = 0.3 * np.sin(2 * np.pi * frequency * t)
                    
                    sd.play(tone, sample_rate)
                    sd.wait()
                    
                    if self.ask_yes_no("Did you hear the test tone?"):
                        print("✅ Audio output test successful")
                    else:
                        self.warnings.append("Audio output test failed (user did not hear tone)")
                        
                except Exception as e:
                    self.warnings.append(f"Audio output test failed: {e}")
            
            return True
            
        except ImportError:
            self.errors.append("sounddevice not available for audio testing")
            return False
        except Exception as e:
            self.errors.append(f"Audio setup failed: {e}")
            return False
    
    def validate_services(self) -> bool:
        """Validate external services connectivity."""
        print("Validating external services...")
        
        success = True
        
        # Test vision API (LM Studio)
        try:
            from config import VISION_API_BASE
            print(f"Testing vision API at {VISION_API_BASE}...")
            
            response = requests.get(f"{VISION_API_BASE}/models", timeout=10)
            if response.status_code == 200:
                print("✅ Vision API (LM Studio) is accessible")
            else:
                self.warnings.append(f"Vision API returned status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.warnings.append("Vision API (LM Studio) not accessible - make sure it's running")
        except Exception as e:
            self.warnings.append(f"Vision API test failed: {e}")
        
        # Test reasoning API
        try:
            from config import REASONING_API_BASE, REASONING_API_KEY
            print(f"Testing reasoning API at {REASONING_API_BASE}...")
            
            headers = {"Authorization": f"Bearer {REASONING_API_KEY}"}
            response = requests.get(f"{REASONING_API_BASE}/models", headers=headers, timeout=10)
            
            # Don't require 200 status, just that we can reach the endpoint
            print("✅ Reasoning API is reachable")
            
        except requests.exceptions.ConnectionError:
            self.warnings.append("Reasoning API not accessible - check internet connection")
        except Exception as e:
            self.warnings.append(f"Reasoning API test failed: {e}")
        
        return success
    
    def optimize_performance(self) -> bool:
        """Configure performance optimizations."""
        print("Configuring performance optimizations...")
        
        try:
            # Check if performance configuration exists
            if not Path("performance_config.py").exists():
                self.warnings.append("performance_config.py not found - using defaults")
                return True
            
            # Import performance configuration
            import performance_config
            
            print("✅ Performance configuration loaded")
            
            # Check system resources for optimization recommendations
            try:
                import psutil
                
                # CPU cores
                cpu_count = psutil.cpu_count()
                print(f"✅ CPU cores: {cpu_count}")
                
                # Recommend parallel worker count
                recommended_workers = min(4, max(2, cpu_count // 2))
                print(f"✅ Recommended parallel workers: {recommended_workers}")
                
                # Memory
                memory_gb = psutil.virtual_memory().total / (1024**3)
                
                # Recommend cache size based on memory
                if memory_gb >= 16:
                    recommended_cache_mb = 200
                elif memory_gb >= 8:
                    recommended_cache_mb = 100
                else:
                    recommended_cache_mb = 50
                
                print(f"✅ Recommended cache size: {recommended_cache_mb}MB")
                
            except ImportError:
                self.warnings.append("psutil not available for performance optimization")
            
            return True
            
        except Exception as e:
            self.warnings.append(f"Performance optimization failed: {e}")
            return True  # Non-critical
    
    def final_validation(self) -> bool:
        """Perform final validation of the complete setup."""
        print("Performing final validation...")
        
        try:
            # Import and validate configuration
            from config import validate_config
            
            if validate_config():
                print("✅ Configuration validation passed")
                return True
            else:
                self.errors.append("Configuration validation failed")
                return False
                
        except Exception as e:
            self.errors.append(f"Final validation failed: {e}")
            return False
    
    def show_setup_summary(self) -> None:
        """Show setup summary with results."""
        print(f"\n{Colors.BOLD}Setup Summary{Colors.ENDC}")
        print("=" * 40)
        
        if len(self.errors) == 0:
            print(f"{Colors.OKGREEN}✅ Setup completed successfully!{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ Setup completed with {len(self.errors)} errors{Colors.ENDC}")
        
        if self.warnings:
            print(f"{Colors.WARNING}⚠️  {len(self.warnings)} warnings{Colors.ENDC}")
        
        # Show errors
        if self.errors:
            print(f"\n{Colors.FAIL}Errors:{Colors.ENDC}")
            for error in self.errors:
                print(f"  - {error}")
        
        # Show warnings
        if self.warnings:
            print(f"\n{Colors.WARNING}Warnings:{Colors.ENDC}")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # Show next steps
        print(f"\n{Colors.BOLD}Next Steps:{Colors.ENDC}")
        if len(self.errors) == 0:
            print("1. Start AURA with: python main.py")
            print("2. Say the wake word 'computer' to activate")
            print("3. Give voice commands like 'click on the button'")
            print("4. Check the README.md for more usage examples")
        else:
            print("1. Fix the errors listed above")
            print("2. Run the setup wizard again: python setup_wizard.py")
            print("3. Check the troubleshooting section in README.md")
    
    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        """
        Ask a yes/no question.
        
        Args:
            question: Question to ask
            default: Default answer if user just presses Enter
            
        Returns:
            True for yes, False for no
        """
        default_str = "Y/n" if default else "y/N"
        while True:
            try:
                answer = input(f"{question} [{default_str}]: ").strip().lower()
                
                if not answer:
                    return default
                elif answer in ['y', 'yes']:
                    return True
                elif answer in ['n', 'no']:
                    return False
                else:
                    print("Please answer 'y' or 'n'")
            except KeyboardInterrupt:
                print("\nSetup interrupted")
                sys.exit(1)


def main():
    """Main entry point for the setup wizard."""
    wizard = SetupWizard()
    
    try:
        success = wizard.run()
        
        if success:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 AURA setup completed successfully!{Colors.ENDC}")
            print(f"{Colors.OKBLUE}You can now start AURA with: python main.py{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}❌ AURA setup failed{Colors.ENDC}")
            print(f"{Colors.WARNING}Please check the errors above and try again{Colors.ENDC}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Setup interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Setup failed with unexpected error: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
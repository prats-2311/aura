#!/bin/bash
# AURA Environment Setup Script
# Automated setup for AURA conda environment

set -e  # Exit on any error

echo "🚀 AURA Environment Setup"
echo "========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    print_error "Conda is not installed. Please install Anaconda or Miniconda first."
    echo "Download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

print_success "Conda found: $(conda --version)"

# Check if aura environment already exists
if conda env list | grep -q "^aura "; then
    print_warning "AURA environment already exists."
    read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing existing AURA environment..."
        conda env remove -n aura -y
    else
        print_status "Using existing environment. Updating packages..."
        conda activate aura
        pip install -r requirements.txt --upgrade
        print_success "Environment updated successfully!"
        exit 0
    fi
fi

# Create conda environment
print_status "Creating conda environment 'aura' with Python 3.11..."
conda create --name aura python=3.11 -y

# Activate environment
print_status "Activating AURA environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate aura

# Verify Python version
python_version=$(python --version)
print_success "Python version: $python_version"

# Install pip packages
print_status "Installing Python packages from requirements.txt..."
if [ -f "requirements-minimal.txt" ]; then
    print_status "Found minimal requirements. Installing essential packages first..."
    pip install -r requirements-minimal.txt
    
    read -p "Install full requirements? (includes all development tools) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installing full requirements..."
        pip install -r requirements.txt
    fi
else
    pip install -r requirements.txt
fi

# Install macOS-specific tools
if [[ "$OSTYPE" == "darwin"* ]]; then
    print_status "macOS detected. Installing cliclick for GUI automation..."
    if command -v brew &> /dev/null; then
        brew install cliclick
        print_success "cliclick installed successfully"
    else
        print_warning "Homebrew not found. Please install cliclick manually:"
        echo "  brew install cliclick"
        echo "  or download from: https://github.com/BlueM/cliclick"
    fi
fi

# Verify installation
print_status "Verifying installation..."
python -c "
import sys
print(f'Python: {sys.version}')

# Test core imports
try:
    import torch
    print('✅ PyTorch imported successfully')
except ImportError as e:
    print(f'❌ PyTorch import failed: {e}')

try:
    import whisper
    print('✅ Whisper imported successfully')
except ImportError as e:
    print(f'❌ Whisper import failed: {e}')

try:
    import sounddevice
    print('✅ SoundDevice imported successfully')
except ImportError as e:
    print(f'❌ SoundDevice import failed: {e}')

try:
    import pyautogui
    print('✅ PyAutoGUI imported successfully')
except ImportError as e:
    print(f'❌ PyAutoGUI import failed: {e}')

try:
    import pygame
    print('✅ Pygame imported successfully')
except ImportError as e:
    print(f'❌ Pygame import failed: {e}')

try:
    import fastapi
    print('✅ FastAPI imported successfully')
except ImportError as e:
    print(f'❌ FastAPI import failed: {e}')

try:
    import ollama
    print('✅ Ollama imported successfully')
except ImportError as e:
    print(f'❌ Ollama import failed: {e}')

if sys.platform == 'darwin':
    try:
        import objc
        print('✅ PyObjC imported successfully')
    except ImportError as e:
        print(f'❌ PyObjC import failed: {e}')
"

print_success "Environment setup completed!"
echo
echo "🎉 AURA is ready to use!"
echo
echo "Next steps:"
echo "1. Activate the environment: conda activate aura"
echo "2. Configure your API keys in config.py"
echo "3. Run AURA: python main.py"
echo
echo "For explain selected text feature:"
echo "1. Select text in any application"
echo "2. Say: 'Computer, explain this'"
echo
print_warning "Don't forget to grant accessibility permissions in System Preferences!"
echo "Go to: System Preferences > Security & Privacy > Privacy > Accessibility"
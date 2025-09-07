#!/usr/bin/env python3
"""
Task 4.0 Comprehensive Testing Runner

Simple script to execute all Task 4.0 comprehensive tests including:
- 4.0: Comprehensive unit test coverage
- 4.1: Backward compatibility and system integration validation  
- 4.2: Performance optimization and monitoring

Usage:
    python run_task_4_tests.py
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Run Task 4.0 comprehensive tests."""
    print("🚀 Starting Task 4.0 Comprehensive Testing Suite")
    print("=" * 60)
    
    # Add tests directory to Python path
    tests_dir = Path(__file__).parent / "tests"
    if tests_dir.exists():
        sys.path.insert(0, str(tests_dir))
    
    try:
        # Import and run the comprehensive test suite
        from tests.run_comprehensive_testing_suite import main as run_tests
        
        print("📋 Running comprehensive test suite...")
        exit_code = run_tests()
        
        if exit_code == 0:
            print("\n✅ Task 4.0 comprehensive testing completed successfully!")
            print("   All requirements have been satisfied.")
        elif exit_code == 1:
            print("\n⚠️  Task 4.0 testing completed with issues.")
            print("   Please review the test results and address failures.")
        else:
            print("\n❌ Task 4.0 testing failed due to critical errors.")
            print("   Please check the test setup and configuration.")
        
        return exit_code
        
    except ImportError as e:
        print(f"❌ Failed to import test modules: {e}")
        print("   Please ensure all test files are present in the tests/ directory.")
        return 2
    
    except Exception as e:
        print(f"❌ Unexpected error during test execution: {e}")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
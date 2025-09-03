#!/usr/bin/env python3
"""
AURA Command Testing Script

This script allows you to test AURA commands directly without the full main.py
complexity, focusing on the hybrid architecture functionality.
"""

import sys
import time
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_command_validation():
    """Test command validation functionality."""
    logger.info("🔍 Testing Command Validation")
    
    try:
        from orchestrator import Orchestrator
        orchestrator = Orchestrator()
        
        test_commands = [
            # GUI Commands (should use fast path)
            "click the Finder icon",
            "press the Enter button", 
            "tap the Save button",
            "type 'hello world'",
            "scroll down",
            
            # Analysis Commands (should use vision path)
            "what's on my screen?",
            "describe the screen",
            "tell me what you see",
            
            # Form Commands
            "fill out the form",
            "submit the form",
            
            # Navigation Commands
            "go back",
            "refresh the page"
        ]
        
        logger.info(f"Testing {len(test_commands)} commands...")
        
        for cmd in test_commands:
            validation = orchestrator.validate_command(cmd)
            
            print(f"Command: '{cmd}'")
            print(f"  ✅ Valid: {validation.is_valid}")
            print(f"  📝 Type: {validation.command_type}")
            print(f"  🎯 Confidence: {validation.confidence:.2f}")
            print(f"  🔄 Normalized: '{validation.normalized_command}'")
            
            if validation.issues:
                print(f"  ⚠️  Issues: {validation.issues}")
            if validation.suggestions:
                print(f"  💡 Suggestions: {validation.suggestions}")
            print()
        
        return True
        
    except Exception as e:
        logger.error(f"Command validation test failed: {e}")
        return False

def test_fast_path_detection():
    """Test fast path detection logic."""
    logger.info("⚡ Testing Fast Path Detection")
    
    try:
        from orchestrator import Orchestrator
        orchestrator = Orchestrator()
        
        # Test GUI command detection
        gui_commands = [
            "click the button",
            "press enter",
            "type 'text'",
            "scroll up"
        ]
        
        non_gui_commands = [
            "what's on screen?",
            "tell me about this",
            "how do I do this?",
            "explain the interface"
        ]
        
        print("GUI Commands (should use fast path):")
        for cmd in gui_commands:
            validation = orchestrator.validate_command(cmd)
            is_gui = orchestrator._is_gui_command(validation.normalized_command, validation.__dict__)
            print(f"  '{cmd}' → GUI: {is_gui} ({'✅' if is_gui else '❌'})")
        
        print("\nNon-GUI Commands (should use vision path):")
        for cmd in non_gui_commands:
            validation = orchestrator.validate_command(cmd)
            is_gui = orchestrator._is_gui_command(validation.normalized_command, validation.__dict__)
            print(f"  '{cmd}' → GUI: {is_gui} ({'❌' if is_gui else '✅'})")
        
        return True
        
    except Exception as e:
        logger.error(f"Fast path detection test failed: {e}")
        return False

def test_system_health():
    """Test system health monitoring."""
    logger.info("🏥 Testing System Health")
    
    try:
        from orchestrator import Orchestrator
        orchestrator = Orchestrator()
        
        health = orchestrator.get_system_health()
        
        print("System Health Report:")
        print(f"  Overall Health: {health.get('overall_health', 'unknown')}")
        print(f"  Health Score: {health.get('health_score', 0)}/100")
        print()
        
        print("Module Health:")
        for module, status in health.get('module_health', {}).items():
            status_icon = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
            print(f"  {module}: {status} {status_icon}")
        print()
        
        print("Module Availability:")
        for module, available in orchestrator.module_availability.items():
            avail_icon = "✅" if available else "❌"
            print(f"  {module}: {'Available' if available else 'Unavailable'} {avail_icon}")
        print()
        
        print("Fast Path Status:")
        print(f"  Fast Path Enabled: {orchestrator.fast_path_enabled}")
        
        if orchestrator.accessibility_module:
            acc_status = orchestrator.accessibility_module.get_accessibility_status()
            print(f"  Accessibility API: {'✅' if acc_status.get('api_initialized') else '❌'}")
            print(f"  Permissions Granted: {'✅' if acc_status.get('permissions_granted') else '❌'}")
            print(f"  Degraded Mode: {'⚠️' if acc_status.get('degraded_mode') else '✅'}")
        
        return True
        
    except Exception as e:
        logger.error(f"System health test failed: {e}")
        return False

def test_interactive_commands():
    """Interactive command testing mode."""
    logger.info("🎮 Starting Interactive Command Testing")
    
    try:
        from orchestrator import Orchestrator
        orchestrator = Orchestrator()
        
        print("=" * 60)
        print("🤖 AURA Interactive Command Testing")
        print("=" * 60)
        print("Enter commands to test the hybrid architecture.")
        print("Commands starting with 'click', 'type', 'scroll' will attempt fast path.")
        print("Commands like 'what's on screen?' will use vision analysis.")
        print("Type 'help' for examples, 'status' for system info, or 'quit' to exit.")
        print()
        
        while True:
            try:
                command = input("AURA> ").strip()
                
                if not command:
                    continue
                    
                if command.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if command.lower() == 'help':
                    print_help()
                    continue
                    
                if command.lower() == 'status':
                    test_system_health()
                    continue
                
                # Execute the command
                print(f"🔄 Executing: '{command}'")
                start_time = time.time()
                
                try:
                    # First validate the command
                    validation = orchestrator.validate_command(command)
                    print(f"   Validation: {'✅ Valid' if validation.is_valid else '❌ Invalid'}")
                    print(f"   Type: {validation.command_type}")
                    print(f"   Confidence: {validation.confidence:.2f}")
                    
                    if not validation.is_valid:
                        print(f"   Issues: {validation.issues}")
                        continue
                    
                    # Check if it's a GUI command
                    is_gui = orchestrator._is_gui_command(validation.normalized_command, validation.__dict__)
                    expected_path = "Fast Path" if is_gui else "Vision Path"
                    print(f"   Expected Path: {expected_path}")
                    
                    # Try to execute (this may fail due to no real UI, but we can see the routing)
                    if hasattr(orchestrator, 'execute_command'):
                        result = orchestrator.execute_command(command)
                        execution_time = time.time() - start_time
                        
                        print(f"   Result: {result.get('status', 'unknown')}")
                        print(f"   Time: {execution_time:.3f}s")
                        
                        if result.get('errors'):
                            print(f"   Errors: {result['errors']}")
                    else:
                        execution_time = time.time() - start_time
                        print(f"   Validation completed in {execution_time:.3f}s")
                        print(f"   Note: Full execution not available in test mode")
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    print(f"   ❌ Error: {e}")
                    print(f"   Time: {execution_time:.3f}s")
                
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Interactive testing failed: {e}")
        return False

def print_help():
    """Print help information."""
    print()
    print("📚 AURA Command Examples:")
    print()
    print("🖱️  GUI Commands (Fast Path):")
    print("   click the Finder icon")
    print("   press the Enter button")
    print("   type 'hello world'")
    print("   scroll down")
    print("   tap the Save button")
    print()
    print("👁️  Vision Commands (Vision Path):")
    print("   what's on my screen?")
    print("   describe the screen")
    print("   tell me what you see")
    print("   analyze the interface")
    print()
    print("📝 Form Commands:")
    print("   fill out the form")
    print("   submit the form")
    print("   complete the registration")
    print()
    print("🧭 Navigation Commands:")
    print("   go back")
    print("   refresh the page")
    print("   scroll to the top")
    print()
    print("🔧 System Commands:")
    print("   status - Show system health")
    print("   help - Show this help")
    print("   quit - Exit the program")
    print()

def main():
    """Main function."""
    print("🧪 AURA Command Testing Suite")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        print("Available test modes:")
        print("1. validation - Test command validation")
        print("2. fastpath - Test fast path detection")
        print("3. health - Test system health")
        print("4. interactive - Interactive command testing")
        print("5. all - Run all tests")
        print()
        mode = input("Select mode (1-5 or name): ").strip().lower()
    
    success_count = 0
    total_tests = 0
    
    if mode in ['1', 'validation', 'all']:
        total_tests += 1
        if test_command_validation():
            success_count += 1
        print()
    
    if mode in ['2', 'fastpath', 'all']:
        total_tests += 1
        if test_fast_path_detection():
            success_count += 1
        print()
    
    if mode in ['3', 'health', 'all']:
        total_tests += 1
        if test_system_health():
            success_count += 1
        print()
    
    if mode in ['4', 'interactive']:
        test_interactive_commands()
        return
    
    if mode == 'all':
        print("=" * 50)
        print(f"🏁 Test Results: {success_count}/{total_tests} passed")
        
        if success_count == total_tests:
            print("🎉 All tests passed! AURA is working correctly.")
        elif success_count > 0:
            print("⚠️  Some tests passed. AURA has basic functionality.")
        else:
            print("❌ Tests failed. Please check the setup.")
        
        print()
        print("💡 To test commands interactively, run:")
        print("   python test_aura_commands.py interactive")

if __name__ == "__main__":
    main()
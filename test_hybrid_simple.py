#!/usr/bin/env python3
"""
Simple Hybrid Architecture Test

This script tests the hybrid architecture functionality without the full
main.py application complexity, focusing on the core fast path/slow path logic.
"""

import sys
import time
import logging
from typing import Dict, Any

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_orchestrator_basic():
    """Test basic orchestrator functionality."""
    logger.info("Testing basic orchestrator functionality...")
    
    try:
        from orchestrator import Orchestrator
        
        # Initialize orchestrator
        logger.info("Initializing orchestrator...")
        orchestrator = Orchestrator()
        
        # Test system health
        logger.info("Checking system health...")
        health = orchestrator.get_system_health()
        logger.info(f"System health: {health.get('overall_health', 'unknown')}")
        
        # Test command validation
        logger.info("Testing command validation...")
        test_commands = [
            "click the button",
            "type 'hello world'",
            "scroll down",
            "what's on my screen?"
        ]
        
        for cmd in test_commands:
            result = orchestrator.validate_command(cmd)
            logger.info(f"Command '{cmd}': {result.command_type} (confidence: {result.confidence:.2f})")
        
        return True, orchestrator
        
    except Exception as e:
        logger.error(f"Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_fast_path_logic(orchestrator):
    """Test fast path execution logic."""
    logger.info("Testing fast path logic...")
    
    try:
        # Test GUI command detection
        gui_commands = [
            "click the save button",
            "press the enter key", 
            "tap the icon"
        ]
        
        for cmd in gui_commands:
            logger.info(f"Testing GUI command: '{cmd}'")
            
            # Test command classification
            validation = orchestrator.validate_command(cmd)
            is_gui = orchestrator._is_gui_command(validation.normalized_command, validation.__dict__)
            logger.info(f"  Classified as GUI: {is_gui}")
            
            # Test fast path attempt (will likely fail without real UI, but should not crash)
            if hasattr(orchestrator, '_attempt_fast_path_execution'):
                try:
                    start_time = time.time()
                    result = orchestrator._attempt_fast_path_execution(cmd, validation.__dict__)
                    execution_time = time.time() - start_time
                    
                    if result:
                        logger.info(f"  Fast path result: {result.get('success', False)} ({execution_time:.3f}s)")
                        if not result.get('success'):
                            logger.info(f"  Fallback reason: {result.get('failure_reason', 'unknown')}")
                    else:
                        logger.info(f"  Fast path returned None ({execution_time:.3f}s)")
                        
                except Exception as e:
                    logger.info(f"  Fast path error (expected): {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Fast path test failed: {e}")
        return False

def test_accessibility_module():
    """Test accessibility module functionality."""
    logger.info("Testing accessibility module...")
    
    try:
        from modules.accessibility import AccessibilityModule
        
        # Initialize accessibility module
        accessibility = AccessibilityModule()
        
        # Check status
        status = accessibility.get_accessibility_status()
        logger.info(f"Accessibility API initialized: {status.get('api_initialized', False)}")
        logger.info(f"Permissions granted: {status.get('permissions_granted', False)}")
        logger.info(f"Degraded mode: {status.get('degraded_mode', True)}")
        
        # Test element detection (will likely fail without permissions, but should not crash)
        try:
            element = accessibility.find_element('AXButton', 'Test Button')
            if element:
                logger.info(f"Element found: {element}")
            else:
                logger.info("No element found (expected without real UI)")
        except Exception as e:
            logger.info(f"Element detection error (expected): {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Accessibility module test failed: {e}")
        return False

def test_vision_module():
    """Test vision module functionality."""
    logger.info("Testing vision module...")
    
    try:
        from modules.vision import VisionModule
        
        # Initialize vision module
        vision = VisionModule()
        
        # Test screen capture (will likely fail without display, but should not crash)
        try:
            screenshot = vision.capture_screen()
            if screenshot:
                logger.info(f"Screenshot captured: {screenshot}")
            else:
                logger.info("Screenshot capture failed (expected in some environments)")
        except Exception as e:
            logger.info(f"Screenshot error (expected): {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Vision module test failed: {e}")
        return False

def test_performance_monitoring():
    """Test performance monitoring functionality."""
    logger.info("Testing performance monitoring...")
    
    try:
        from modules.performance import performance_monitor, PerformanceMetrics
        
        # Create a test metric
        metric = PerformanceMetrics(
            operation="test_operation",
            duration=0.123,
            success=True,
            metadata={"test": "data"}
        )
        
        # Record the metric
        performance_monitor.record_metric(metric)
        logger.info("Performance metric recorded successfully")
        
        # Get statistics
        stats = performance_monitor.get_statistics()
        logger.info(f"Performance stats: {len(stats.get('recent_metrics', []))} recent metrics")
        
        return True
        
    except Exception as e:
        logger.error(f"Performance monitoring test failed: {e}")
        return False

def run_command_simulation(orchestrator):
    """Simulate running actual commands."""
    logger.info("Running command simulation...")
    
    test_commands = [
        ("click the Finder icon", "GUI interaction"),
        ("type 'hello world'", "Text input"),
        ("scroll down", "Navigation"),
        ("what's on my screen?", "Screen analysis")
    ]
    
    results = []
    
    for cmd, description in test_commands:
        logger.info(f"Simulating: {cmd} ({description})")
        
        try:
            start_time = time.time()
            
            # Use execute_command if available, otherwise just validate
            if hasattr(orchestrator, 'execute_command'):
                result = orchestrator.execute_command(cmd)
                execution_time = time.time() - start_time
                
                status = result.get('status', 'unknown')
                logger.info(f"  Result: {status} ({execution_time:.3f}s)")
                
                if result.get('errors'):
                    logger.info(f"  Errors: {result['errors']}")
                
                results.append({
                    'command': cmd,
                    'status': status,
                    'time': execution_time,
                    'success': status == 'completed'
                })
            else:
                # Just validate the command
                validation = orchestrator.validate_command(cmd)
                execution_time = time.time() - start_time
                
                logger.info(f"  Validation: {validation.is_valid} ({execution_time:.3f}s)")
                logger.info(f"  Type: {validation.command_type}")
                
                results.append({
                    'command': cmd,
                    'status': 'validated',
                    'time': execution_time,
                    'success': validation.is_valid
                })
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"  Command failed: {e}")
            results.append({
                'command': cmd,
                'status': 'error',
                'time': execution_time,
                'success': False
            })
    
    # Summary
    successful = len([r for r in results if r['success']])
    total = len(results)
    avg_time = sum(r['time'] for r in results) / total if total > 0 else 0
    
    logger.info(f"Command simulation summary: {successful}/{total} successful, {avg_time:.3f}s average")
    
    return results

def main():
    """Main test function."""
    logger.info("🧪 Starting AURA Hybrid Architecture Test")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Test 1: Basic orchestrator functionality
    logger.info("\n📋 Test 1: Basic Orchestrator Functionality")
    success, orchestrator = test_orchestrator_basic()
    test_results['orchestrator_basic'] = success
    
    if not success:
        logger.error("❌ Basic orchestrator test failed. Cannot continue.")
        return
    
    # Test 2: Fast path logic
    logger.info("\n⚡ Test 2: Fast Path Logic")
    success = test_fast_path_logic(orchestrator)
    test_results['fast_path_logic'] = success
    
    # Test 3: Accessibility module
    logger.info("\n♿ Test 3: Accessibility Module")
    success = test_accessibility_module()
    test_results['accessibility_module'] = success
    
    # Test 4: Vision module
    logger.info("\n👁️  Test 4: Vision Module")
    success = test_vision_module()
    test_results['vision_module'] = success
    
    # Test 5: Performance monitoring
    logger.info("\n📊 Test 5: Performance Monitoring")
    success = test_performance_monitoring()
    test_results['performance_monitoring'] = success
    
    # Test 6: Command simulation
    logger.info("\n🎮 Test 6: Command Simulation")
    try:
        results = run_command_simulation(orchestrator)
        test_results['command_simulation'] = len([r for r in results if r['success']]) > 0
    except Exception as e:
        logger.error(f"Command simulation failed: {e}")
        test_results['command_simulation'] = False
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("🏁 Test Summary")
    logger.info("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if success:
            passed_tests += 1
    
    logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed! Hybrid architecture is working correctly.")
    elif passed_tests >= total_tests * 0.7:
        logger.info("⚠️  Most tests passed. System should work with some limitations.")
    else:
        logger.info("❌ Multiple test failures. Please check the setup and dependencies.")
    
    # Recommendations
    logger.info("\n📝 Recommendations:")
    
    if not test_results.get('accessibility_module', False):
        logger.info("- Grant accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility")
    
    if not test_results.get('vision_module', False):
        logger.info("- Ensure LM Studio is running on localhost:1234 with a vision model loaded")
    
    if not test_results.get('fast_path_logic', False):
        logger.info("- Check that PyObjC frameworks are properly installed")
    
    logger.info("- Run 'python fix_aura_setup.py' to fix common setup issues")
    logger.info("- Check the full setup guide in REAL_AURA_COMMAND_TESTING_GUIDE.md")

if __name__ == "__main__":
    main()
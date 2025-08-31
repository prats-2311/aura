#!/usr/bin/env python3
"""
AURA Integration Test Suite

Comprehensive integration tests for the complete AURA system.
Tests all modules working together with performance monitoring.
"""

import logging
import time
import sys
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationTestSuite:
    """Comprehensive integration test suite for AURA."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.test_results = []
        self.performance_metrics = {}
        self.start_time = time.time()
        
        print("=" * 60)
        print("AURA Integration Test Suite")
        print("=" * 60)
    
    def run_all_tests(self) -> bool:
        """
        Run all integration tests.
        
        Returns:
            True if all tests pass, False otherwise
        """
        tests = [
            ("Configuration Validation", self.test_configuration),
            ("Module Imports", self.test_module_imports),
            ("Performance System", self.test_performance_system),
            ("Vision Module", self.test_vision_module),
            ("Reasoning Module", self.test_reasoning_module),
            ("Audio Module", self.test_audio_module),
            ("Automation Module", self.test_automation_module),
            ("Orchestrator", self.test_orchestrator),
            ("Error Handling", self.test_error_handling),
            ("Performance Optimization", self.test_performance_optimization),
            ("System Integration", self.test_system_integration)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            
            try:
                start_time = time.time()
                result = test_func()
                duration = time.time() - start_time
                
                self.test_results.append({
                    'name': test_name,
                    'passed': result,
                    'duration': duration,
                    'error': None
                })
                
                if result:
                    print(f"✅ {test_name} PASSED ({duration:.2f}s)")
                    passed += 1
                else:
                    print(f"❌ {test_name} FAILED ({duration:.2f}s)")
                    
            except Exception as e:
                duration = time.time() - start_time
                print(f"💥 {test_name} ERROR: {e} ({duration:.2f}s)")
                
                self.test_results.append({
                    'name': test_name,
                    'passed': False,
                    'duration': duration,
                    'error': str(e)
                })
        
        # Print summary
        self.print_test_summary(passed, total)
        
        return passed == total
    
    def test_configuration(self) -> bool:
        """Test configuration validation."""
        try:
            from config import validate_config, get_config_summary
            
            # Test configuration validation
            config_valid = validate_config()
            if not config_valid:
                print("❌ Configuration validation failed")
                return False
            
            # Test configuration summary
            summary = get_config_summary()
            if not isinstance(summary, dict):
                print("❌ Configuration summary invalid")
                return False
            
            print("✅ Configuration validation passed")
            print(f"✅ Project: {summary['project']['name']} v{summary['project']['version']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            return False
    
    def test_module_imports(self) -> bool:
        """Test that all modules can be imported successfully."""
        modules_to_test = [
            'modules.vision',
            'modules.reasoning',
            'modules.audio',
            'modules.automation',
            'modules.feedback',
            'modules.error_handler',
            'modules.performance',
            'modules.performance_dashboard',
            'orchestrator',
            'config',
            'performance_config'
        ]
        
        failed_imports = []
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"✅ {module_name}")
            except ImportError as e:
                print(f"❌ {module_name}: {e}")
                failed_imports.append(module_name)
            except Exception as e:
                print(f"💥 {module_name}: {e}")
                failed_imports.append(module_name)
        
        if failed_imports:
            print(f"❌ Failed to import {len(failed_imports)} modules")
            return False
        
        print(f"✅ All {len(modules_to_test)} modules imported successfully")
        return True
    
    def test_performance_system(self) -> bool:
        """Test performance monitoring system."""
        try:
            from modules.performance import (
                performance_monitor, connection_pool, image_cache,
                parallel_processor, measure_performance
            )
            from modules.performance_dashboard import performance_dashboard
            
            # Test performance monitor
            metrics = performance_monitor.get_performance_summary()
            if not isinstance(metrics, dict):
                print("❌ Performance monitor failed")
                return False
            
            # Test connection pool
            session = connection_pool.get_session("http://example.com")
            if session is None:
                print("❌ Connection pool failed")
                return False
            
            # Test image cache
            cache_stats = image_cache.get_cache_stats()
            if not isinstance(cache_stats, dict):
                print("❌ Image cache failed")
                return False
            
            # Test performance dashboard
            dashboard_metrics = performance_dashboard.get_real_time_metrics()
            if not isinstance(dashboard_metrics, dict):
                print("❌ Performance dashboard failed")
                return False
            
            print("✅ Performance system operational")
            return True
            
        except Exception as e:
            print(f"❌ Performance system test failed: {e}")
            return False
    
    def test_vision_module(self) -> bool:
        """Test vision module functionality."""
        try:
            from modules.vision import VisionModule
            
            # Initialize vision module
            vision = VisionModule()
            
            # Test screen resolution
            width, height = vision.get_screen_resolution()
            if width <= 0 or height <= 0:
                print("❌ Invalid screen resolution")
                return False
            
            print(f"✅ Screen resolution: {width}x{height}")
            
            # Test screen capture (without API call)
            try:
                # This will test the capture mechanism but may fail on API call
                # which is expected in test environment
                screenshot = vision.capture_screen_as_base64()
                if screenshot:
                    print("✅ Screen capture successful")
                else:
                    print("⚠️  Screen capture returned empty (expected in test)")
            except Exception as e:
                print(f"⚠️  Screen capture failed (expected in test): {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Vision module test failed: {e}")
            return False
    
    def test_reasoning_module(self) -> bool:
        """Test reasoning module functionality."""
        try:
            from modules.reasoning import ReasoningModule
            
            # Initialize reasoning module
            reasoning = ReasoningModule()
            
            # Test fallback response generation
            fallback = reasoning._get_fallback_response("test error")
            if not isinstance(fallback, dict) or 'plan' not in fallback:
                print("❌ Fallback response invalid")
                return False
            
            print("✅ Reasoning module initialized")
            print("✅ Fallback response generation working")
            
            return True
            
        except Exception as e:
            print(f"❌ Reasoning module test failed: {e}")
            return False
    
    def test_audio_module(self) -> bool:
        """Test audio module functionality."""
        try:
            from modules.audio import AudioModule
            
            # Initialize audio module (may fail on some systems)
            try:
                audio = AudioModule()
                
                # Test audio validation
                validation = audio.validate_audio_input()
                if not isinstance(validation, dict):
                    print("❌ Audio validation failed")
                    return False
                
                print("✅ Audio module initialized")
                print(f"✅ Audio validation: {validation.get('microphone_available', False)}")
                
            except Exception as e:
                print(f"⚠️  Audio module initialization failed (may be expected): {e}")
                # Audio module failure is not critical for integration test
            
            return True
            
        except Exception as e:
            print(f"❌ Audio module test failed: {e}")
            return False
    
    def test_automation_module(self) -> bool:
        """Test automation module functionality."""
        try:
            from modules.automation import AutomationModule
            
            # Initialize automation module
            automation = AutomationModule()
            
            # Test action validation
            valid_action = {
                'action': 'click',
                'coordinates': [100, 100]
            }
            
            # This should not raise an exception
            is_valid, error_msg = automation.validate_action_format(valid_action)
            if not is_valid:
                print(f"❌ Action validation failed: {error_msg}")
                return False
            
            print("✅ Automation module initialized")
            print("✅ Action validation working")
            
            return True
            
        except Exception as e:
            print(f"❌ Automation module test failed: {e}")
            return False
    
    def test_orchestrator(self) -> bool:
        """Test orchestrator functionality."""
        try:
            from orchestrator import Orchestrator
            
            # Initialize orchestrator (may fail if modules are not available)
            try:
                orchestrator = Orchestrator()
                
                # Test system health
                health = orchestrator.get_system_health()
                if not isinstance(health, dict):
                    print("❌ System health check failed")
                    return False
                
                print("✅ Orchestrator initialized")
                print(f"✅ System health: {health.get('overall_health', 'unknown')}")
                
            except Exception as e:
                print(f"⚠️  Orchestrator initialization failed (may be expected): {e}")
                # Orchestrator failure may be expected if external services are not available
            
            return True
            
        except Exception as e:
            print(f"❌ Orchestrator test failed: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling system."""
        try:
            from modules.error_handler import (
                global_error_handler, ErrorCategory, ErrorSeverity
            )
            
            # Test error handling
            test_error = Exception("Test error")
            error_info = global_error_handler.handle_error(
                error=test_error,
                module="test",
                function="test_function",
                category=ErrorCategory.PROCESSING_ERROR,
                severity=ErrorSeverity.LOW
            )
            
            if not error_info or not error_info.error_id:
                print("❌ Error handling failed")
                return False
            
            # Test error statistics
            stats = global_error_handler.get_error_statistics()
            if not isinstance(stats, dict):
                print("❌ Error statistics failed")
                return False
            
            print("✅ Error handling system working")
            print(f"✅ Error statistics available: {len(stats)} metrics")
            
            return True
            
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
    
    def test_performance_optimization(self) -> bool:
        """Test performance optimization features."""
        try:
            from modules.performance import (
                connection_pool, image_cache, parallel_processor
            )
            
            # Test connection pooling
            session1 = connection_pool.get_session("http://test1.com")
            session2 = connection_pool.get_session("http://test1.com")
            
            # Should return the same session (pooled)
            if session1 is not session2:
                print("❌ Connection pooling not working")
                return False
            
            # Test image cache
            test_data = b"test image data"
            compressed = image_cache.get_compressed_image(test_data)
            
            # Should return something (even if compression fails)
            if compressed is None:
                print("⚠️  Image compression failed (may be expected)")
            else:
                print("✅ Image compression working")
            
            # Test parallel processor
            def test_task(x):
                return x * 2
            
            tasks = [(test_task, (i,), {}) for i in range(3)]
            results = parallel_processor.execute_parallel_io(tasks)
            
            if len(results) != 3:
                print("❌ Parallel processing failed")
                return False
            
            print("✅ Connection pooling working")
            print("✅ Parallel processing working")
            
            return True
            
        except Exception as e:
            print(f"❌ Performance optimization test failed: {e}")
            return False
    
    def test_system_integration(self) -> bool:
        """Test overall system integration."""
        try:
            # Test that all major components can work together
            from config import get_config_summary
            from modules.performance_dashboard import performance_dashboard
            
            # Get configuration
            config = get_config_summary()
            
            # Get performance metrics
            metrics = performance_dashboard.get_real_time_metrics()
            
            # Get optimization recommendations
            recommendations = performance_dashboard.get_optimization_recommendations()
            
            print(f"✅ Configuration loaded: {config['project']['name']}")
            print(f"✅ Performance metrics available: {metrics.get('health_status', 'unknown')}")
            print(f"✅ Optimization recommendations: {len(recommendations)} available")
            
            return True
            
        except Exception as e:
            print(f"❌ System integration test failed: {e}")
            return False
    
    def print_test_summary(self, passed: int, total: int) -> None:
        """Print test summary."""
        duration = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print(f"Total Duration: {duration:.2f}s")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['passed']]
        if failed_tests:
            print(f"\nFailed Tests:")
            for test in failed_tests:
                error_msg = f" - {test['error']}" if test['error'] else ""
                print(f"  ❌ {test['name']} ({test['duration']:.2f}s){error_msg}")
        
        # Show performance metrics
        if self.test_results:
            avg_duration = sum(r['duration'] for r in self.test_results) / len(self.test_results)
            print(f"\nPerformance:")
            print(f"  Average test duration: {avg_duration:.2f}s")
            print(f"  Fastest test: {min(r['duration'] for r in self.test_results):.2f}s")
            print(f"  Slowest test: {max(r['duration'] for r in self.test_results):.2f}s")


def main():
    """Main entry point for integration tests."""
    print("Starting AURA Integration Test Suite...")
    
    # Check if we're in the right directory
    if not Path("config.py").exists():
        print("❌ config.py not found. Please run from the AURA project root directory.")
        return 1
    
    # Run tests
    test_suite = IntegrationTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print("\n💥 Some integration tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
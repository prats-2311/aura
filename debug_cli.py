#!/usr/bin/env python3
"""
AURA Debugging Command-Line Interface

Standalone debugging utilities for accessibility tree inspection, element detection testing,
and comprehensive system health checking.

Usage:
    python debug_cli.py tree [app_name] [--output json|text] [--depth N]
    python debug_cli.py element <target_text> [app_name] [--fuzzy] [--threshold N]
    python debug_cli.py health [--format json|text] [--output file.json]
    python debug_cli.py test <app_name> <element1,element2,...> [--verbose]
    python debug_cli.py permissions [--request] [--monitor]
"""

import argparse
import sys
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Import AURA debugging modules
try:
    from modules.accessibility_debugger import AccessibilityDebugger
    from modules.diagnostic_tools import AccessibilityHealthChecker
    from modules.permission_validator import PermissionValidator
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Error: Could not import AURA modules: {e}")
    print("Make sure you're running from the AURA root directory")
    sys.exit(1)


class DebugCLI:
    """Command-line interface for AURA debugging tools."""
    
    def __init__(self):
        """Initialize the debug CLI."""
        self.setup_logging()
        
        # Initialize debugging components
        self.config = self.load_config()
        self.debugger = AccessibilityDebugger(self.config)
        self.health_checker = AccessibilityHealthChecker(self.config)
        self.permission_validator = PermissionValidator(self.config)
        
        print("AURA Debug CLI initialized")
    
    def setup_logging(self):
        """Setup logging for the CLI."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration for debugging tools."""
        try:
            # Try to load from config.py
            import config
            return {
                'debug_level': getattr(config, 'DEBUG_LEVEL', 'DETAILED'),
                'max_tree_depth': getattr(config, 'MAX_TREE_DEPTH', 8),
                'cache_ttl_seconds': getattr(config, 'CACHE_TTL_SECONDS', 60),
                'performance_tracking': True,
                'auto_diagnostics': True
            }
        except ImportError:
            # Use default configuration
            return {
                'debug_level': 'DETAILED',
                'max_tree_depth': 8,
                'cache_ttl_seconds': 60,
                'performance_tracking': True,
                'auto_diagnostics': True
            }
    
    def cmd_tree(self, args) -> int:
        """
        Dump accessibility tree for inspection and analysis.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            print(f"Dumping accessibility tree for: {args.app_name or 'focused application'}")
            print(f"Output format: {args.output}, Max depth: {args.depth}")
            
            # Generate tree dump
            start_time = time.time()
            tree_dump = self.debugger.dump_accessibility_tree(
                app_name=args.app_name,
                force_refresh=True
            )
            generation_time = (time.time() - start_time) * 1000
            
            print(f"Tree dump completed in {generation_time:.1f}ms")
            print(f"Found {tree_dump.total_elements} elements, {len(tree_dump.clickable_elements)} clickable")
            
            # Output results
            if args.output == 'json':
                output = tree_dump.to_json()
                if args.file:
                    with open(args.file, 'w') as f:
                        f.write(output)
                    print(f"Tree dump saved to: {args.file}")
                else:
                    print("\n=== ACCESSIBILITY TREE (JSON) ===")
                    print(output)
            else:
                # Text format output
                output = self._format_tree_text(tree_dump)
                if args.file:
                    with open(args.file, 'w') as f:
                        f.write(output)
                    print(f"Tree dump saved to: {args.file}")
                else:
                    print("\n=== ACCESSIBILITY TREE ===")
                    print(output)
            
            return 0
            
        except Exception as e:
            print(f"Error dumping accessibility tree: {e}")
            self.logger.error(f"Tree dump failed: {e}")
            return 1
    
    def cmd_element(self, args) -> int:
        """
        Test element detection with various search parameters.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            print(f"Analyzing element detection for target: '{args.target_text}'")
            print(f"Application: {args.app_name or 'focused application'}")
            print(f"Fuzzy matching: {args.fuzzy}, Threshold: {args.threshold}")
            
            # Analyze element detection
            start_time = time.time()
            analysis = self.debugger.analyze_element_detection_failure(
                command=f"find {args.target_text}",
                target=args.target_text,
                app_name=args.app_name
            )
            analysis_time = (time.time() - start_time) * 1000
            
            print(f"Analysis completed in {analysis_time:.1f}ms")
            
            # Display results
            print(f"\n=== ELEMENT DETECTION ANALYSIS ===")
            print(f"Target: {analysis.target_text}")
            print(f"Search Strategy: {analysis.search_strategy}")
            print(f"Matches Found: {analysis.matches_found}")
            print(f"Search Time: {analysis.search_time_ms:.1f}ms")
            
            if analysis.best_match:
                print(f"\n--- Best Match ---")
                match = analysis.best_match
                print(f"Role: {match.get('role', 'unknown')}")
                print(f"Title: {match.get('title', 'N/A')}")
                print(f"Description: {match.get('description', 'N/A')}")
                print(f"Match Score: {match.get('match_score', 0):.1f}%")
                print(f"Matched Text: {match.get('matched_text', 'N/A')}")
            
            if analysis.all_matches and len(analysis.all_matches) > 1:
                print(f"\n--- All Matches ({len(analysis.all_matches)}) ---")
                for i, match in enumerate(analysis.all_matches[:5], 1):  # Show top 5
                    print(f"{i}. {match.get('role', 'unknown')} - "
                          f"{match.get('title', 'N/A')} "
                          f"(Score: {match.get('match_score', 0):.1f}%)")
            
            if analysis.recommendations:
                print(f"\n--- Recommendations ---")
                for i, rec in enumerate(analysis.recommendations, 1):
                    print(f"{i}. {rec}")
            
            # Output JSON if requested
            if args.output == 'json':
                output = json.dumps(analysis.to_dict(), indent=2, default=str)
                if args.file:
                    with open(args.file, 'w') as f:
                        f.write(output)
                    print(f"\nAnalysis saved to: {args.file}")
                else:
                    print(f"\n=== JSON OUTPUT ===")
                    print(output)
            
            return 0
            
        except Exception as e:
            print(f"Error analyzing element detection: {e}")
            self.logger.error(f"Element analysis failed: {e}")
            return 1
    
    def cmd_health(self, args) -> int:
        """
        Run comprehensive system health check and diagnostics.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            print("Running comprehensive accessibility health check...")
            print("This may take a few moments...")
            
            # Run health check
            start_time = time.time()
            report = self.health_checker.run_comprehensive_health_check()
            check_time = (time.time() - start_time) * 1000
            
            print(f"Health check completed in {check_time:.1f}ms")
            
            # Display summary
            print(f"\n=== HEALTH CHECK SUMMARY ===")
            print(report.generate_summary())
            
            # Show detailed issues if any
            if report.detected_issues:
                print(f"\n=== DETECTED ISSUES ===")
                for issue in report.detected_issues:
                    print(f"\n[{issue.severity}] {issue.title}")
                    print(f"Category: {issue.category}")
                    print(f"Description: {issue.description}")
                    print(f"Impact: {issue.impact}")
                    if issue.remediation_steps:
                        print("Remediation Steps:")
                        for step in issue.remediation_steps:
                            print(f"  - {step}")
            
            # Show performance benchmarks
            if report.benchmark_results:
                print(f"\n=== PERFORMANCE BENCHMARKS ===")
                for benchmark in report.benchmark_results:
                    print(f"\nTest: {benchmark.test_name}")
                    print(f"Success Rate: {benchmark.success_rate:.1%}")
                    if benchmark.fast_path_time:
                        print(f"Fast Path Time: {benchmark.fast_path_time:.3f}s")
                    if benchmark.vision_fallback_time:
                        print(f"Vision Fallback Time: {benchmark.vision_fallback_time:.3f}s")
                    if benchmark.performance_ratio:
                        print(f"Performance Ratio: {benchmark.performance_ratio:.2f}x")
            
            # Output full report if requested
            if args.format == 'json' or args.output:
                output = report.export_report('JSON')
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(output)
                    print(f"\nFull report saved to: {args.output}")
                elif args.format == 'json':
                    print(f"\n=== FULL REPORT (JSON) ===")
                    print(output)
            
            # Return appropriate exit code based on health score
            if report.overall_health_score >= 80:
                return 0  # Good health
            elif report.overall_health_score >= 50:
                print(f"\nWarning: Health score is {report.overall_health_score:.1f}/100")
                return 0  # Acceptable but with warnings
            else:
                print(f"\nError: Poor health score {report.overall_health_score:.1f}/100")
                return 1  # Poor health
            
        except Exception as e:
            print(f"Error running health check: {e}")
            self.logger.error(f"Health check failed: {e}")
            return 1
    
    def cmd_test(self, args) -> int:
        """
        Test element detection capability with known elements.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            elements = [elem.strip() for elem in args.elements.split(',')]
            print(f"Testing element detection for {args.app_name}")
            print(f"Elements to test: {elements}")
            
            # Run element detection test
            start_time = time.time()
            results = self.health_checker.test_element_detection_capability(
                app_name=args.app_name,
                element_texts=elements
            )
            test_time = (time.time() - start_time) * 1000
            
            print(f"Test completed in {test_time:.1f}ms")
            
            # Display results
            print(f"\n=== ELEMENT DETECTION TEST RESULTS ===")
            print(f"Application: {results['app_name']}")
            print(f"Elements Tested: {results['total_elements_tested']}")
            print(f"Elements Found: {results['elements_found']}")
            print(f"Elements Not Found: {results['elements_not_found']}")
            print(f"Detection Rate: {results['detection_rate']:.1f}%")
            print(f"Average Detection Time: {results['avg_detection_time']:.1f}ms")
            
            if args.verbose and results['test_results']:
                print(f"\n--- Detailed Results ---")
                for result in results['test_results']:
                    status = "✅ FOUND" if result['found'] else "❌ NOT FOUND"
                    print(f"{status} '{result['element_text']}' "
                          f"({result['match_count']} matches, "
                          f"{result['detection_time_ms']:.1f}ms)")
                    
                    if result['found'] and result.get('best_match'):
                        match = result['best_match']
                        print(f"    Best match: {match.get('role', 'unknown')} - "
                              f"{match.get('title', 'N/A')} "
                              f"(Score: {match.get('match_score', 0):.1f}%)")
            
            if results['errors']:
                print(f"\n--- Errors ---")
                for error in results['errors']:
                    print(f"❌ {error}")
            
            # Output JSON if requested
            if args.output:
                output = json.dumps(results, indent=2, default=str)
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"\nTest results saved to: {args.output}")
            
            # Return success if detection rate is acceptable
            return 0 if results['detection_rate'] >= 50 else 1
            
        except Exception as e:
            print(f"Error running element detection test: {e}")
            self.logger.error(f"Element detection test failed: {e}")
            return 1
    
    def cmd_permissions(self, args) -> int:
        """
        Check and manage accessibility permissions.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            print("Checking accessibility permissions...")
            
            # Check current permissions
            start_time = time.time()
            status = self.permission_validator.check_accessibility_permissions()
            check_time = (time.time() - start_time) * 1000
            
            print(f"Permission check completed in {check_time:.1f}ms")
            
            # Display status
            print(f"\n=== ACCESSIBILITY PERMISSIONS ===")
            print(f"Status: {status.get_summary()}")
            print(f"Permission Level: {status.permission_level}")
            print(f"System Version: {status.system_version}")
            print(f"Can Request Permissions: {status.can_request_permissions}")
            
            if status.granted_permissions:
                print(f"\n--- Granted Permissions ---")
                for perm in status.granted_permissions:
                    print(f"✅ {perm}")
            
            if status.missing_permissions:
                print(f"\n--- Missing Permissions ---")
                for perm in status.missing_permissions:
                    print(f"❌ {perm}")
            
            if status.recommendations:
                print(f"\n--- Recommendations ---")
                for i, rec in enumerate(status.recommendations, 1):
                    print(f"{i}. {rec}")
            
            # Request permissions if requested
            if args.request and status.can_request_permissions:
                print(f"\nRequesting accessibility permissions...")
                try:
                    success = self.permission_validator.attempt_permission_request()
                    if success:
                        print("✅ Permission request successful")
                    else:
                        print("❌ Permission request failed or was denied")
                except Exception as e:
                    print(f"❌ Permission request error: {e}")
            
            # Start monitoring if requested
            if args.monitor:
                print(f"\nStarting permission monitoring...")
                print("Press Ctrl+C to stop monitoring")
                try:
                    self._monitor_permissions()
                except KeyboardInterrupt:
                    print("\nPermission monitoring stopped")
            
            # Return appropriate exit code
            return 0 if status.has_permissions else 1
            
        except Exception as e:
            print(f"Error checking permissions: {e}")
            self.logger.error(f"Permission check failed: {e}")
            return 1
    
    def _format_tree_text(self, tree_dump) -> str:
        """Format accessibility tree dump as readable text."""
        lines = []
        lines.append(f"=== ACCESSIBILITY TREE: {tree_dump.app_name} ===")
        lines.append(f"Generated: {tree_dump.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total Elements: {tree_dump.total_elements}")
        lines.append(f"Clickable Elements: {len(tree_dump.clickable_elements)}")
        lines.append(f"Tree Depth: {tree_dump.tree_depth}")
        lines.append(f"Generation Time: {tree_dump.generation_time_ms:.1f}ms")
        lines.append("")
        
        # Show element role distribution
        lines.append("--- Element Roles ---")
        for role, count in sorted(tree_dump.element_roles.items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"{role}: {count}")
        lines.append("")
        
        # Show clickable elements
        lines.append("--- Clickable Elements ---")
        for i, elem in enumerate(tree_dump.clickable_elements[:20], 1):  # Show top 20
            title = elem.get('title', 'N/A')
            role = elem.get('role', 'unknown')
            lines.append(f"{i:2d}. [{role}] {title}")
        
        if len(tree_dump.clickable_elements) > 20:
            lines.append(f"... and {len(tree_dump.clickable_elements) - 20} more")
        
        return "\n".join(lines)
    
    def _monitor_permissions(self):
        """Monitor permission changes in real-time."""
        last_status = None
        
        while True:
            try:
                current_status = self.permission_validator.check_accessibility_permissions()
                
                if last_status is None:
                    print(f"Initial status: {current_status.get_summary()}")
                elif current_status.has_permissions != last_status.has_permissions:
                    if current_status.has_permissions:
                        print(f"✅ Permissions granted: {current_status.get_summary()}")
                    else:
                        print(f"❌ Permissions revoked: {current_status.get_summary()}")
                elif current_status.permission_level != last_status.permission_level:
                    print(f"🔄 Permission level changed: {last_status.permission_level} → {current_status.permission_level}")
                
                last_status = current_status
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(10)  # Wait longer on error


def main():
    """Main entry point for the debug CLI."""
    parser = argparse.ArgumentParser(
        description="AURA Debugging Command-Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python debug_cli.py tree Safari --output json --file safari_tree.json
  python debug_cli.py element "Sign In" Chrome --fuzzy --threshold 70
  python debug_cli.py health --format json --output health_report.json
  python debug_cli.py test Finder "New Folder,View,Go" --verbose
  python debug_cli.py permissions --request --monitor
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Tree command
    tree_parser = subparsers.add_parser('tree', help='Dump accessibility tree')
    tree_parser.add_argument('app_name', nargs='?', help='Application name (default: focused app)')
    tree_parser.add_argument('--output', choices=['json', 'text'], default='text', help='Output format')
    tree_parser.add_argument('--depth', type=int, default=8, help='Maximum tree depth')
    tree_parser.add_argument('--file', help='Output file path')
    
    # Element command
    element_parser = subparsers.add_parser('element', help='Test element detection')
    element_parser.add_argument('target_text', help='Target element text to find')
    element_parser.add_argument('app_name', nargs='?', help='Application name (default: focused app)')
    element_parser.add_argument('--fuzzy', action='store_true', help='Use fuzzy matching')
    element_parser.add_argument('--threshold', type=float, default=70.0, help='Fuzzy match threshold')
    element_parser.add_argument('--output', choices=['json', 'text'], default='text', help='Output format')
    element_parser.add_argument('--file', help='Output file path')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Run system health check')
    health_parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    health_parser.add_argument('--output', help='Output file path')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test element detection capability')
    test_parser.add_argument('app_name', help='Application name to test')
    test_parser.add_argument('elements', help='Comma-separated list of element texts to find')
    test_parser.add_argument('--verbose', action='store_true', help='Show detailed results')
    test_parser.add_argument('--output', help='Output file path for JSON results')
    
    # Permissions command
    permissions_parser = subparsers.add_parser('permissions', help='Check and manage permissions')
    permissions_parser.add_argument('--request', action='store_true', help='Request permissions if possible')
    permissions_parser.add_argument('--monitor', action='store_true', help='Monitor permission changes')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize CLI and run command
    try:
        cli = DebugCLI()
        
        if args.command == 'tree':
            return cli.cmd_tree(args)
        elif args.command == 'element':
            return cli.cmd_element(args)
        elif args.command == 'health':
            return cli.cmd_health(args)
        elif args.command == 'test':
            return cli.cmd_test(args)
        elif args.command == 'permissions':
            return cli.cmd_permissions(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
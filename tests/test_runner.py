#!/usr/bin/env python3
"""
Automated Test Runner for AURA

This script provides automated test execution with coverage reporting,
performance benchmarking, and CI/CD integration capabilities.
"""

import sys
import os
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Optional


class TestRunner:
    """Automated test runner with coverage and reporting."""
    
    def __init__(self, project_root: str = None):
        """Initialize test runner."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.test_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "coverage"
        self.reports_dir = self.project_root / "test_reports"
        
        # Ensure directories exist
        self.coverage_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_unit_tests(self, verbose: bool = True, coverage: bool = True) -> Dict:
        """Run unit tests with optional coverage."""
        print("🧪 Running unit tests...")
        
        cmd = ["python", "-m", "pytest"]
        
        # Add test files
        cmd.extend([
            "tests/test_comprehensive_unit_coverage.py",
            "tests/test_comprehensive_unit_coverage_part2.py"
        ])
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=modules",
                "--cov=orchestrator",
                "--cov-report=html:coverage/unit",
                "--cov-report=json:coverage/unit_coverage.json",
                "--cov-report=term-missing"
            ])
        
        # Add markers
        cmd.extend(["-m", "unit"])
        
        # Add output options
        cmd.extend([
            "--tb=short",
            "--junit-xml=test_reports/unit_tests.xml"
        ])
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        end_time = time.time()
        
        return {
            "type": "unit",
            "success": result.returncode == 0,
            "duration": end_time - start_time,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    def run_integration_tests(self, verbose: bool = True) -> Dict:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        cmd = ["python", "-m", "pytest"]
        
        # Add test files
        cmd.extend([
            "tests/test_comprehensive_integration.py"
        ])
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        # Add markers
        cmd.extend(["-m", "integration"])
        
        # Add output options
        cmd.extend([
            "--tb=short",
            "--junit-xml=test_reports/integration_tests.xml"
        ])
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        end_time = time.time()
        
        return {
            "type": "integration",
            "success": result.returncode == 0,
            "duration": end_time - start_time,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    def run_end_to_end_tests(self, verbose: bool = True) -> Dict:
        """Run end-to-end tests."""
        print("🎯 Running end-to-end tests...")
        
        cmd = ["python", "-m", "pytest"]
        
        # Add test files
        cmd.extend([
            "tests/test_comprehensive_integration.py::TestEndToEndWorkflows"
        ])
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        # Add output options
        cmd.extend([
            "--tb=short",
            "--junit-xml=test_reports/e2e_tests.xml"
        ])
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        end_time = time.time()
        
        return {
            "type": "e2e",
            "success": result.returncode == 0,
            "duration": end_time - start_time,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    def run_performance_tests(self, verbose: bool = True) -> Dict:
        """Run performance benchmark tests."""
        print("⚡ Running performance tests...")
        
        cmd = ["python", "-m", "pytest"]
        
        # Add test files
        cmd.extend([
            "tests/test_comprehensive_integration.py::TestPerformanceBenchmarks"
        ])
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        # Add markers
        cmd.extend(["-m", "slow"])
        
        # Add output options
        cmd.extend([
            "--tb=short",
            "--junit-xml=test_reports/performance_tests.xml"
        ])
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        end_time = time.time()
        
        return {
            "type": "performance",
            "success": result.returncode == 0,
            "duration": end_time - start_time,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    def run_regression_tests(self, verbose: bool = True) -> Dict:
        """Run regression tests."""
        print("🔄 Running regression tests...")
        
        cmd = ["python", "-m", "pytest"]
        
        # Add test files
        cmd.extend([
            "tests/test_comprehensive_integration.py::TestRegressionScenarios"
        ])
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        # Add output options
        cmd.extend([
            "--tb=short",
            "--junit-xml=test_reports/regression_tests.xml"
        ])
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        end_time = time.time()
        
        return {
            "type": "regression",
            "success": result.returncode == 0,
            "duration": end_time - start_time,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    def run_all_tests(self, include_performance: bool = False, coverage: bool = True) -> Dict:
        """Run all test suites."""
        print("🚀 Running comprehensive test suite...")
        
        results = []
        
        # Run unit tests
        unit_result = self.run_unit_tests(coverage=coverage)
        results.append(unit_result)
        
        # Run integration tests
        integration_result = self.run_integration_tests()
        results.append(integration_result)
        
        # Run end-to-end tests
        e2e_result = self.run_end_to_end_tests()
        results.append(e2e_result)
        
        # Run regression tests
        regression_result = self.run_regression_tests()
        results.append(regression_result)
        
        # Optionally run performance tests
        if include_performance:
            performance_result = self.run_performance_tests()
            results.append(performance_result)
        
        # Calculate summary
        total_duration = sum(r["duration"] for r in results)
        successful_suites = sum(1 for r in results if r["success"])
        total_suites = len(results)
        
        summary = {
            "total_suites": total_suites,
            "successful_suites": successful_suites,
            "failed_suites": total_suites - successful_suites,
            "total_duration": total_duration,
            "overall_success": successful_suites == total_suites,
            "results": results
        }
        
        return summary
    
    def generate_coverage_report(self) -> Optional[Dict]:
        """Generate and parse coverage report."""
        coverage_file = self.coverage_dir / "unit_coverage.json"
        
        if not coverage_file.exists():
            print("⚠️  No coverage data found")
            return None
        
        try:
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            # Extract summary information
            summary = coverage_data.get("totals", {})
            
            coverage_report = {
                "total_statements": summary.get("num_statements", 0),
                "covered_statements": summary.get("covered_lines", 0),
                "missing_statements": summary.get("missing_lines", 0),
                "coverage_percentage": summary.get("percent_covered", 0.0),
                "files": {}
            }
            
            # Extract per-file coverage
            files = coverage_data.get("files", {})
            for file_path, file_data in files.items():
                file_summary = file_data.get("summary", {})
                coverage_report["files"][file_path] = {
                    "statements": file_summary.get("num_statements", 0),
                    "covered": file_summary.get("covered_lines", 0),
                    "missing": file_summary.get("missing_lines", 0),
                    "percentage": file_summary.get("percent_covered", 0.0)
                }
            
            return coverage_report
            
        except Exception as e:
            print(f"❌ Error parsing coverage report: {e}")
            return None
    
    def print_summary(self, results: Dict):
        """Print test results summary."""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        if results.get("overall_success"):
            print("✅ All test suites PASSED")
        else:
            print("❌ Some test suites FAILED")
        
        print(f"\n📈 Statistics:")
        print(f"   Total suites: {results['total_suites']}")
        print(f"   Successful: {results['successful_suites']}")
        print(f"   Failed: {results['failed_suites']}")
        print(f"   Total duration: {results['total_duration']:.2f}s")
        
        print(f"\n📋 Suite Results:")
        for result in results["results"]:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"   {result['type'].upper():12} {status} ({result['duration']:.2f}s)")
        
        # Print coverage if available
        coverage_report = self.generate_coverage_report()
        if coverage_report:
            print(f"\n📊 Code Coverage:")
            print(f"   Overall: {coverage_report['coverage_percentage']:.1f}%")
            print(f"   Statements: {coverage_report['covered_statements']}/{coverage_report['total_statements']}")
            
            # Show files with low coverage
            low_coverage_files = [
                (path, data) for path, data in coverage_report["files"].items()
                if data["percentage"] < 80.0 and data["statements"] > 0
            ]
            
            if low_coverage_files:
                print(f"\n⚠️  Files with <80% coverage:")
                for file_path, data in low_coverage_files[:5]:  # Show top 5
                    print(f"   {Path(file_path).name}: {data['percentage']:.1f}%")
        
        print("\n" + "="*60)
    
    def save_results(self, results: Dict, filename: str = "test_results.json"):
        """Save test results to file."""
        results_file = self.reports_dir / filename
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"💾 Results saved to {results_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def check_requirements(self) -> bool:
        """Check if all test requirements are installed."""
        required_packages = [
            "pytest",
            "pytest-cov",
            "pytest-mock",
            "pytest-xdist"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing required packages: {', '.join(missing_packages)}")
            print(f"   Install with: pip install {' '.join(missing_packages)}")
            return False
        
        return True


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="AURA Automated Test Runner")
    
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--regression", action="store_true", help="Run regression tests only")
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    parser.add_argument("--include-performance", action="store_true", help="Include performance tests in --all")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    parser.add_argument("--save-results", help="Save results to specified file")
    parser.add_argument("--project-root", help="Project root directory")
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner(project_root=args.project_root)
    
    # Check requirements
    if not runner.check_requirements():
        sys.exit(1)
    
    verbose = not args.quiet
    coverage = not args.no_coverage
    
    # Determine which tests to run
    if args.unit:
        results = runner.run_unit_tests(verbose=verbose, coverage=coverage)
    elif args.integration:
        results = runner.run_integration_tests(verbose=verbose)
    elif args.e2e:
        results = runner.run_end_to_end_tests(verbose=verbose)
    elif args.performance:
        results = runner.run_performance_tests(verbose=verbose)
    elif args.regression:
        results = runner.run_regression_tests(verbose=verbose)
    elif args.all:
        results = runner.run_all_tests(
            include_performance=args.include_performance,
            coverage=coverage
        )
    else:
        # Default: run unit and integration tests
        print("No specific test suite specified, running unit and integration tests...")
        unit_results = runner.run_unit_tests(verbose=verbose, coverage=coverage)
        integration_results = runner.run_integration_tests(verbose=verbose)
        
        results = {
            "total_suites": 2,
            "successful_suites": sum(1 for r in [unit_results, integration_results] if r["success"]),
            "failed_suites": sum(1 for r in [unit_results, integration_results] if not r["success"]),
            "total_duration": unit_results["duration"] + integration_results["duration"],
            "overall_success": unit_results["success"] and integration_results["success"],
            "results": [unit_results, integration_results]
        }
    
    # Print summary
    if isinstance(results, dict) and "results" in results:
        runner.print_summary(results)
    else:
        # Single test suite result
        status = "✅ PASSED" if results["success"] else "❌ FAILED"
        print(f"\n{results['type'].upper()} tests: {status} ({results['duration']:.2f}s)")
    
    # Save results if requested
    if args.save_results:
        runner.save_results(results, args.save_results)
    
    # Exit with appropriate code
    if isinstance(results, dict):
        success = results.get("overall_success", results.get("success", False))
    else:
        success = results.get("success", False)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
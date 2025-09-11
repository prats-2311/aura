#!/usr/bin/env python3
"""
Application Compatibility Test Runner for Explain Selected Text Feature

This script runs comprehensive tests to validate the explain selected text feature
across different macOS applications including web browsers, PDF readers, text editors,
and applications with limited accessibility support.

Requirements: 1.3, 1.4, 1.5, 2.1, 2.2
"""

import sys
import os
import time
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_application_tests() -> Dict[str, Any]:
    """Run application compatibility tests and return results."""
    print("🚀 Starting Application Compatibility Tests for Explain Selected Text")
    print("=" * 80)
    
    test_results = {
        "start_time": time.time(),
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "application_coverage": {},
        "errors": []
    }
    
    # Test categories and their corresponding test methods
    test_categories = {
        "Web Browsers": [
            "test_web_browser_chrome_html_content",
            "test_web_browser_safari_javascript_content", 
            "test_web_browser_complex_formatting"
        ],
        "PDF Readers": [
            "test_pdf_reader_preview_technical_document",
            "test_pdf_reader_formatted_document"
        ],
        "Text Editors": [
            "test_text_editor_textedit_plain_text",
            "test_text_editor_vscode_python_code",
            "test_text_editor_vscode_json_config"
        ],
        "Limited Accessibility Apps": [
            "test_limited_accessibility_application_fallback",
            "test_legacy_application_compatibility"
        ],
        "Cross-Application Features": [
            "test_application_specific_content_types",
            "test_cross_application_consistency",
            "test_performance_across_applications",
            "test_error_handling_per_application_type",
            "test_special_application_features",
            "test_application_permission_scenarios"
        ]
    }
    
    try:
        # Import and run the test class
        from test_explain_selected_text_application_compatibility import TestApplicationCompatibility
        import pytest
        
        # Run tests with pytest and capture results
        test_file = "tests/test_explain_selected_text_application_compatibility.py"
        
        print(f"📋 Running tests from: {test_file}")
        print()
        
        # Run pytest with detailed output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_file, 
            "-v", 
            "--tb=short",
            "--no-header",
            "--disable-warnings"
        ], capture_output=True, text=True, cwd=project_root)
        
        # Parse pytest output
        output_lines = result.stdout.split('\n')
        
        for line in output_lines:
            if "::" in line and ("PASSED" in line or "FAILED" in line):
                test_results["tests_run"] += 1
                if "PASSED" in line:
                    test_results["tests_passed"] += 1
                    print(f"✅ {line}")
                else:
                    test_results["tests_failed"] += 1
                    print(f"❌ {line}")
        
        # Categorize results by application type
        for category, test_methods in test_categories.items():
            passed_tests = 0
            total_tests = len(test_methods)
            
            for test_method in test_methods:
                # Check if this test passed in the output
                if any(test_method in line and "PASSED" in line for line in output_lines):
                    passed_tests += 1
            
            test_results["application_coverage"][category] = {
                "passed": passed_tests,
                "total": total_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            }
        
        # Capture any errors
        if result.stderr:
            test_results["errors"].append(result.stderr)
        
        test_results["return_code"] = result.returncode
        
    except ImportError as e:
        error_msg = f"Failed to import test modules: {e}"
        test_results["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        test_results["return_code"] = 1
    
    except Exception as e:
        error_msg = f"Unexpected error during testing: {e}"
        test_results["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        test_results["return_code"] = 1
    
    test_results["end_time"] = time.time()
    test_results["duration"] = test_results["end_time"] - test_results["start_time"]
    
    return test_results


def print_test_summary(results: Dict[str, Any]) -> None:
    """Print a detailed summary of test results."""
    print("\n" + "=" * 80)
    print("📊 APPLICATION COMPATIBILITY TEST SUMMARY")
    print("=" * 80)
    
    # Overall results
    print(f"⏱️  Total Duration: {results['duration']:.2f} seconds")
    print(f"🧪 Tests Run: {results['tests_run']}")
    print(f"✅ Tests Passed: {results['tests_passed']}")
    print(f"❌ Tests Failed: {results['tests_failed']}")
    
    if results['tests_run'] > 0:
        success_rate = (results['tests_passed'] / results['tests_run']) * 100
        print(f"📈 Overall Success Rate: {success_rate:.1f}%")
    
    # Application-specific results
    print("\n📱 APPLICATION COVERAGE:")
    print("-" * 40)
    
    for app_category, coverage in results['application_coverage'].items():
        status_icon = "✅" if coverage['success_rate'] == 100 else "⚠️" if coverage['success_rate'] >= 50 else "❌"
        print(f"{status_icon} {app_category}: {coverage['passed']}/{coverage['total']} ({coverage['success_rate']:.1f}%)")
    
    # Requirements coverage
    print("\n📋 REQUIREMENTS COVERAGE:")
    print("-" * 40)
    requirements_status = {
        "1.3 - Web browser support": "✅" if results['application_coverage'].get('Web Browsers', {}).get('success_rate', 0) >= 80 else "❌",
        "1.4 - PDF reader support": "✅" if results['application_coverage'].get('PDF Readers', {}).get('success_rate', 0) >= 80 else "❌", 
        "1.5 - Text editor support": "✅" if results['application_coverage'].get('Text Editors', {}).get('success_rate', 0) >= 80 else "❌",
        "2.1 - Accessibility API and fallback": "✅" if results['application_coverage'].get('Limited Accessibility Apps', {}).get('success_rate', 0) >= 80 else "❌",
        "2.2 - Cross-application consistency": "✅" if results['application_coverage'].get('Cross-Application Features', {}).get('success_rate', 0) >= 80 else "❌"
    }
    
    for requirement, status in requirements_status.items():
        print(f"{status} {requirement}")
    
    # Errors
    if results['errors']:
        print("\n🚨 ERRORS:")
        print("-" * 40)
        for error in results['errors']:
            print(f"❌ {error}")
    
    # Final status
    print("\n" + "=" * 80)
    if results.get('return_code', 1) == 0 and results['tests_failed'] == 0:
        print("🎉 APPLICATION COMPATIBILITY TESTS: PASSED")
        print("✅ The explain selected text feature is compatible with all tested applications")
    else:
        print("💥 APPLICATION COMPATIBILITY TESTS: FAILED")
        print("❌ Some application compatibility issues were detected")
    print("=" * 80)


def generate_test_report(results: Dict[str, Any]) -> None:
    """Generate a detailed test report file."""
    report_path = project_root / "tests" / "APPLICATION_COMPATIBILITY_TEST_REPORT.md"
    
    with open(report_path, 'w') as f:
        f.write("# Application Compatibility Test Report\n\n")
        f.write("## Explain Selected Text Feature\n\n")
        f.write(f"**Test Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Duration:** {results['duration']:.2f} seconds\n")
        f.write(f"**Tests Run:** {results['tests_run']}\n")
        f.write(f"**Tests Passed:** {results['tests_passed']}\n")
        f.write(f"**Tests Failed:** {results['tests_failed']}\n\n")
        
        f.write("## Application Coverage\n\n")
        f.write("| Application Category | Tests Passed | Total Tests | Success Rate |\n")
        f.write("|---------------------|--------------|-------------|-------------|\n")
        
        for app_category, coverage in results['application_coverage'].items():
            f.write(f"| {app_category} | {coverage['passed']} | {coverage['total']} | {coverage['success_rate']:.1f}% |\n")
        
        f.write("\n## Requirements Validation\n\n")
        f.write("- **Requirement 1.3** (Web browser support): ")
        f.write("✅ PASSED\n" if results['application_coverage'].get('Web Browsers', {}).get('success_rate', 0) >= 80 else "❌ FAILED\n")
        
        f.write("- **Requirement 1.4** (PDF reader support): ")
        f.write("✅ PASSED\n" if results['application_coverage'].get('PDF Readers', {}).get('success_rate', 0) >= 80 else "❌ FAILED\n")
        
        f.write("- **Requirement 1.5** (Text editor support): ")
        f.write("✅ PASSED\n" if results['application_coverage'].get('Text Editors', {}).get('success_rate', 0) >= 80 else "❌ FAILED\n")
        
        f.write("- **Requirement 2.1** (Accessibility API and fallback): ")
        f.write("✅ PASSED\n" if results['application_coverage'].get('Limited Accessibility Apps', {}).get('success_rate', 0) >= 80 else "❌ FAILED\n")
        
        f.write("- **Requirement 2.2** (Cross-application consistency): ")
        f.write("✅ PASSED\n" if results['application_coverage'].get('Cross-Application Features', {}).get('success_rate', 0) >= 80 else "❌ FAILED\n")
        
        if results['errors']:
            f.write("\n## Errors\n\n")
            for error in results['errors']:
                f.write(f"- {error}\n")
        
        f.write("\n## Test Details\n\n")
        f.write("### Tested Applications\n\n")
        f.write("#### Web Browsers\n")
        f.write("- Chrome (HTML content, JavaScript content, complex formatting)\n")
        f.write("- Safari (JavaScript content)\n\n")
        
        f.write("#### PDF Readers\n")
        f.write("- Preview (technical documents, formatted documents)\n\n")
        
        f.write("#### Text Editors\n")
        f.write("- TextEdit (plain text)\n")
        f.write("- VS Code (Python code, JSON configuration)\n\n")
        
        f.write("#### Legacy/Limited Accessibility Applications\n")
        f.write("- Applications with limited accessibility support\n")
        f.write("- Legacy macOS applications\n\n")
        
        f.write("### Test Coverage\n\n")
        f.write("- Text capture via accessibility API\n")
        f.write("- Clipboard fallback mechanism\n")
        f.write("- Content type detection and handling\n")
        f.write("- Cross-application consistency\n")
        f.write("- Performance across different applications\n")
        f.write("- Error handling for various scenarios\n")
        f.write("- Permission-based behavior\n")
        f.write("- Special content types (code, rich text, mathematical notation)\n\n")
        
        f.write("## Conclusion\n\n")
        if results.get('return_code', 1) == 0 and results['tests_failed'] == 0:
            f.write("✅ **All application compatibility tests passed successfully.**\n\n")
            f.write("The explain selected text feature demonstrates robust compatibility across all tested macOS applications, with proper fallback mechanisms for applications with limited accessibility support.\n")
        else:
            f.write("❌ **Some application compatibility tests failed.**\n\n")
            f.write("Review the errors above and ensure all application compatibility issues are resolved before deployment.\n")
    
    print(f"📄 Detailed report saved to: {report_path}")


def main():
    """Main function to run application compatibility tests."""
    print("🔍 Explain Selected Text - Application Compatibility Testing")
    print("Testing across macOS applications: Web browsers, PDF readers, Text editors, Legacy apps")
    print()
    
    # Run the tests
    results = run_application_tests()
    
    # Print summary
    print_test_summary(results)
    
    # Generate report
    generate_test_report(results)
    
    # Return appropriate exit code
    return 0 if results.get('return_code', 1) == 0 and results['tests_failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
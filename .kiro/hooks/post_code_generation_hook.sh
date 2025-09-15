#!/bin/bash
# This hook runs after Kiro generates or modifies code.
echo "🔧 AURA Hook: Post-code generation testing started at $(date)"
echo "📁 Working directory: $(pwd)"
echo "🧪 Running targeted test suite..."

# Log to a file for debugging
echo "$(date): Hook triggered" >> .kiro/hook_execution.log

# Run tests from the tests directory with verbose output
pytest tests/ -v --tb=short --disable-warnings

echo "✅ AURA Hook: Testing completed at $(date)"
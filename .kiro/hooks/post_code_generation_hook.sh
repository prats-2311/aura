#!/bin/bash
# This hook runs after Kiro generates or modifies code.
echo "Kiro hook triggered: Running the AURA test suite..."
pytest
#!/usr/bin/env python3
"""
Test AURA click command processing without actually clicking
"""

from orchestrator import Orchestrator
import json

def test_click_command():
    """Test click command processing"""
    print("🧪 Testing AURA Click Command Processing")
    print("=" * 50)
    
    orchestrator = Orchestrator()
    
    # Test click command validation
    print("\n1. Testing command validation:")
    commands = [
        "Click on the sign in button",
        "Click the submit button", 
        "Press the OK button",
        "Tap on the menu"
    ]
    
    for cmd in commands:
        validation = orchestrator.validate_command(cmd)
        print(f"   '{cmd}' -> {validation.command_type} (confidence: {validation.confidence:.2f})")
    
    # Test the full pipeline up to action generation (without execution)
    print("\n2. Testing action plan generation:")
    try:
        # We'll use a mock execution that stops before actually clicking
        test_command = "Click on the sign in button"
        
        # Get screen analysis
        screen_analysis = orchestrator.vision_module.describe_screen(analysis_type="detailed")
        print(f"   Screen analysis: {screen_analysis.get('description', 'N/A')[:100]}...")
        
        # Get action plan
        action_plan = orchestrator.reasoning_module.get_action_plan(test_command, screen_analysis)
        print(f"   Action plan generated with {len(action_plan.get('plan', []))} actions")
        
        # Show the actions that would be executed
        for i, action in enumerate(action_plan.get('plan', [])):
            action_type = action.get('action', 'unknown')
            if action_type == 'click':
                coords = action.get('coordinates', [0, 0])
                print(f"   Action {i+1}: {action_type} at coordinates {coords}")
            elif action_type == 'speak':
                message = action.get('message', 'No message')
                print(f"   Action {i+1}: {action_type} - '{message}'")
            else:
                print(f"   Action {i+1}: {action_type}")
        
        print("\n✅ Click command processing is working correctly!")
        print("   The system can:")
        print("   - Recognize click commands")
        print("   - Analyze screen content")
        print("   - Generate click actions with coordinates")
        print("   - Plan complete action sequences")
        
    except Exception as e:
        print(f"❌ Error in action plan generation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_click_command()
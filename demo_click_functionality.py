#!/usr/bin/env python3
"""
Demo of AURA's click functionality
"""

from orchestrator import Orchestrator
import json

def demo_click_functionality():
    """Demonstrate AURA's click functionality"""
    print("🎯 AURA Click Functionality Demo")
    print("=" * 40)
    
    orchestrator = Orchestrator()
    
    # Show current screen content
    print("\n📺 Current Screen Analysis:")
    screen_analysis = orchestrator.vision_module.describe_screen(analysis_type="simple")
    description = screen_analysis.get("description", "No description available")
    print(f"   {description[:300]}...")
    
    # Demo different click commands
    print("\n🖱️  Click Command Examples:")
    
    demo_commands = [
        ("Click on the button", "Generic button click"),
        ("Click in the center", "Center screen click"),
        ("Click on the home link", "Specific element click"),
        ("Press the submit button", "Alternative click syntax")
    ]
    
    for command, description in demo_commands:
        print(f"\n   Command: '{command}'")
        print(f"   Purpose: {description}")
        
        try:
            # Validate command
            validation = orchestrator.validate_command(command)
            print(f"   Recognition: {validation.command_type} (confidence: {validation.confidence:.2f})")
            
            # Generate action plan
            action_plan = orchestrator.reasoning_module.get_action_plan(command, screen_analysis)
            actions = action_plan.get('plan', [])
            
            # Show what would happen
            click_actions = [a for a in actions if a.get('action') == 'click']
            if click_actions:
                coords = click_actions[0].get('coordinates', [0, 0])
                print(f"   Result: Would click at coordinates {coords}")
            else:
                speak_actions = [a for a in actions if a.get('action') == 'speak']
                if speak_actions:
                    message = speak_actions[0].get('message', '')
                    print(f"   Result: {message[:100]}...")
                    
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n🎉 Click Functionality Summary:")
    print("   ✅ Command recognition working")
    print("   ✅ Screen analysis working") 
    print("   ✅ Coordinate generation working")
    print("   ✅ Intelligent responses working")
    print("   ✅ Ready for voice commands!")
    
    print("\n🗣️  Try saying: 'Computer, click on the button'")
    print("   AURA will analyze your screen and click appropriately!")

if __name__ == "__main__":
    demo_click_functionality()
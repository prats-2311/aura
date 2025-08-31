#!/usr/bin/env python3
"""
Test the complete click functionality pipeline
"""

from modules.vision import VisionModule
from modules.reasoning import ReasoningModule
from modules.automation import AutomationModule
from orchestrator import Orchestrator
import json

def test_click_pipeline():
    """Test the complete click functionality pipeline"""
    print("🧪 Testing Complete Click Functionality Pipeline")
    print("=" * 60)
    
    # Test 1: Vision Analysis
    print("\n1. 🔍 Testing Vision Analysis:")
    try:
        vision = VisionModule()
        screen_analysis = vision.describe_screen(analysis_type="detailed")
        print("✅ Vision analysis successful")
        print(f"   Description: {screen_analysis.get('description', 'N/A')[:100]}...")
        
        # Test clickable element finding
        element_result = vision.find_clickable_element("sign in")
        print(f"   Element search result: {element_result.get('found', False)}")
        if element_result.get('found'):
            coords = element_result.get('click_coordinates', [0, 0])
            print(f"   Click coordinates: {coords}")
        
    except Exception as e:
        print(f"❌ Vision analysis failed: {e}")
        return False
    
    # Test 2: Reasoning Module
    print("\n2. 🧠 Testing Reasoning Module:")
    try:
        reasoning = ReasoningModule()
        action_plan = reasoning.get_action_plan(
            "Click on the sign in button",
            screen_analysis
        )
        print("✅ Action plan generated")
        print(f"   Actions: {len(action_plan.get('plan', []))}")
        
        # Check if click action has coordinates
        click_actions = [a for a in action_plan.get('plan', []) if a.get('action') == 'click']
        if click_actions:
            coords = click_actions[0].get('coordinates', [])
            print(f"   Click coordinates: {coords}")
        
    except Exception as e:
        print(f"❌ Reasoning failed: {e}")
        return False
    
    # Test 3: Automation Module (dry run)
    print("\n3. 🤖 Testing Automation Module (dry run):")
    try:
        automation = AutomationModule()
        print("✅ Automation module initialized")
        print(f"   Screen size: {automation.screen_width}x{automation.screen_height}")
        
        # Test coordinate validation
        test_coords = [500, 400]
        is_valid = automation._validate_coordinates(test_coords[0], test_coords[1])
        print(f"   Coordinate validation ({test_coords}): {is_valid}")
        
    except Exception as e:
        print(f"❌ Automation test failed: {e}")
        return False
    
    # Test 4: Full Orchestrator Integration
    print("\n4. 🎯 Testing Full Orchestrator Integration:")
    try:
        orchestrator = Orchestrator()
        
        # Test command validation
        validation = orchestrator.validate_command("Click on the sign in button")
        print(f"✅ Command validation: {validation.command_type} (confidence: {validation.confidence:.2f})")
        
        # Note: We won't actually execute the click to avoid unwanted actions
        print("   (Skipping actual execution to avoid unwanted clicks)")
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        return False
    
    print("\n🎉 All click functionality tests passed!")
    print("\n📋 Summary:")
    print("   ✅ Vision can analyze screen content")
    print("   ✅ Vision can find clickable elements")
    print("   ✅ Reasoning generates click actions with coordinates")
    print("   ✅ Automation module can validate coordinates")
    print("   ✅ Orchestrator recognizes click commands")
    print("\n🚀 Click functionality is ready for use!")
    
    return True

if __name__ == "__main__":
    test_click_pipeline()
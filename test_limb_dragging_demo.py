#!/usr/bin/env python3
"""
Demo script to showcase individual limb/ear dragging functionality.
This demonstrates the new features without requiring the full GUI.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.features.panda_character import PandaCharacter


def demo_body_part_detection():
    """Demonstrate enhanced body part detection."""
    print("\n=== Body Part Detection Demo ===")
    panda = PandaCharacter()
    
    test_positions = [
        (0.05, 0.05, "Top left corner"),
        (0.05, 0.95, "Top right corner"),
        (0.20, 0.35, "Left eye area"),
        (0.20, 0.65, "Right eye area"),
        (0.28, 0.5, "Nose area"),
        (0.4, 0.1, "Left arm area"),
        (0.4, 0.9, "Right arm area"),
        (0.4, 0.5, "Body center"),
        (0.9, 0.3, "Left leg area"),
        (0.9, 0.7, "Right leg area"),
    ]
    
    for rel_y, rel_x, description in test_positions:
        part = panda.get_body_part_at_position(rel_y, rel_x)
        print(f"  {description:20} → {part}")


def demo_drag_responses():
    """Demonstrate individual limb drag responses."""
    print("\n=== Individual Limb Drag Responses ===")
    panda = PandaCharacter()
    
    parts = [
        'left_arm', 'right_arm', 'left_leg', 'right_leg',
        'left_ear', 'right_ear', 'head', 'body', 'butt'
    ]
    
    for part in parts:
        response = panda.on_drag(grabbed_part=part)
        print(f"  Drag by {part:12} → {response}")


def demo_click_responses():
    """Demonstrate nose and eye click responses."""
    print("\n=== Nose & Eye Click Responses ===")
    panda = PandaCharacter()
    
    parts = ['nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear']
    
    for part in parts:
        response = panda.on_body_part_click(part)
        print(f"  Click on {part:12} → {response}")


def demo_limb_specific_features():
    """Demonstrate that each limb has unique behavior."""
    print("\n=== Limb-Specific Features ===")
    panda = PandaCharacter()
    
    # Show that left and right limbs are tracked separately
    print("\n  Left vs Right Arm:")
    for _ in range(2):
        left_resp = panda.on_drag(grabbed_part='left_arm')
        right_resp = panda.on_drag(grabbed_part='right_arm')
        print(f"    Left: {left_resp}")
        print(f"    Right: {right_resp}")
    
    # Show ear-specific responses
    print("\n  Left vs Right Ear (painful!):")
    for _ in range(2):
        left_resp = panda.on_drag(grabbed_part='left_ear')
        right_resp = panda.on_drag(grabbed_part='right_ear')
        print(f"    Left: {left_resp}")
        print(f"    Right: {right_resp}")
    
    # Show leg responses (upside down!)
    print("\n  Leg Drags (upside-down orientation):")
    for _ in range(2):
        left_resp = panda.on_drag(grabbed_part='left_leg')
        right_resp = panda.on_drag(grabbed_part='right_leg')
        print(f"    Left: {left_resp}")
        print(f"    Right: {right_resp}")


def demo_key_features():
    """Show key improvements in the new system."""
    print("\n=== Key Features Summary ===")
    print("""
  ✓ Individual limb detection: left_arm, right_arm, left_leg, right_leg
  ✓ Individual ear detection: left_ear, right_ear
  ✓ Nose and eye detection: nose, left_eye, right_eye
  ✓ Limb-specific drag responses for each body part
  ✓ Individual limb dangle physics (non-grabbed limbs dangle)
  ✓ Upside-down flip when dragged by legs upward
  ✓ Spin/shake disabled when grabbed by head, limbs, or ears
  ✓ Spin/shake only active when grabbed by body/belly/butt
  ✓ Each limb and ear has unique click and drag responses
    """)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Individual Limb/Ear Dragging Demo")
    print("  PS2 Texture Sorter - Panda Companion")
    print("="*60)
    
    demo_key_features()
    demo_body_part_detection()
    demo_drag_responses()
    demo_click_responses()
    demo_limb_specific_features()
    
    print("\n" + "="*60)
    print("  Demo Complete!")
    print("  The panda can now be dragged by individual limbs and ears!")
    print("="*60 + "\n")

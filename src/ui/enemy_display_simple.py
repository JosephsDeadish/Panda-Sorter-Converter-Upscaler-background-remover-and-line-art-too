"""
Simple enemy display using Tkinter widgets instead of canvas drawing.
"""

import tkinter as tk
from typing import Any

def create_enemy_display(parent_frame, enemy: Any) -> tk.Frame:
    """
    Create a simple enemy display using Tkinter widgets.
    
    Args:
        parent_frame: Parent frame to place the display in
        enemy: Enemy object with name, icon, level attributes
        
    Returns:
        Frame containing the enemy display
    """
    # Create main frame
    display_frame = tk.Frame(parent_frame, bg='#2b2b2b', width=200, height=200)
    
    # Get enemy info
    enemy_name = enemy.name if hasattr(enemy, 'name') else 'Enemy'
    enemy_icon = enemy.icon if hasattr(enemy, 'icon') else '👹'
    enemy_level = enemy.level if hasattr(enemy, 'level') else 1
    
    # Get enemy color based on type
    enemy_color = '#888888'  # Default gray
    if hasattr(enemy, 'template') and hasattr(enemy.template, 'enemy_type'):
        from src.features.enemy_templates import EnemyType
        type_colors = {
            EnemyType.SLIME: '#00FF00',
            EnemyType.GOBLIN: '#00AA00',
            EnemyType.ORC: '#AA0000',
            EnemyType.DRAGON: '#FF0000',
            EnemyType.WOLF: '#888888',
            EnemyType.SKELETON: '#F5F5DC',
        }
        enemy_color = type_colors.get(enemy.template.enemy_type, '#888888')
    
    # Create circular background
    canvas = tk.Canvas(display_frame, width=200, height=200, 
                      bg='#2b2b2b', highlightthickness=0)
    canvas.pack()
    
    # Draw circle
    canvas.create_oval(50, 30, 150, 130, fill=enemy_color, outline='#404040', width=3)
    
    # Large emoji in center
    canvas.create_text(100, 80, text=enemy_icon, 
                      font=('Arial', 48), fill='white')
    
    # Name below
    canvas.create_text(100, 150, text=enemy_name,
                      font=('Arial', 14, 'bold'), fill='white')
    
    # Level indicator
    canvas.create_text(100, 170, text=f"Level {enemy_level}",
                      font=('Arial', 10), fill='#aaaaaa')
    
    return display_frame

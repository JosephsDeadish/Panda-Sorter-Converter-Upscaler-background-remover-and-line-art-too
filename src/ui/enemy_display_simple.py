"""
Simple enemy display using Tkinter widgets - NO CANVAS.
"""

import tkinter as tk
from typing import Any

def create_enemy_display(parent_frame, enemy: Any) -> tk.Frame:
    """
    Create a simple enemy display using Tkinter labels - NO CANVAS.
    
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
    
    # NO CANVAS - use Labels instead
    # Create circular-looking background with label
    circle_frame = tk.Frame(display_frame, bg=enemy_color, width=100, height=100)
    circle_frame.pack(pady=20)
    circle_frame.pack_propagate(False)
    
    # Large emoji in center
    icon_label = tk.Label(circle_frame, text=enemy_icon, 
                         font=('Arial', 48), fg='white', bg=enemy_color)
    icon_label.pack(expand=True)
    
    # Name below
    name_label = tk.Label(display_frame, text=enemy_name,
                         font=('Arial', 14, 'bold'), fg='white', bg='#2b2b2b')
    name_label.pack()
    
    # Level indicator
    level_label = tk.Label(display_frame, text=f"Level {enemy_level}",
                          font=('Arial', 10), fg='#aaaaaa', bg='#2b2b2b')
    level_label.pack()
    
    return display_frame


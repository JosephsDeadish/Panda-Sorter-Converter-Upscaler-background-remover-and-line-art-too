"""
Simple achievement display that works with existing Tkinter code.
This is a minimal bridge to show achievements without breaking existing code.
"""

import tkinter as tk
from typing import Any, Optional

def show_achievement_simple(root, achievement: Any, accent_color: str = '#ffd700', bg_color: str = '#ffd700'):
    """
    Display achievement popup using simple Tkinter (not Qt).
    This maintains compatibility with existing Tkinter code.
    
    Args:
        root: The Tkinter root window
        achievement: Achievement object with name, description, icon, reward attributes
        accent_color: Accent color for the popup
        bg_color: Background accent color
    """
    # Create popup window
    popup = tk.Toplevel(root)
    popup.title('')
    popup.overrideredirect(True)
    popup.wm_attributes('-topmost', True)
    
    # Make slightly transparent
    try:
        popup.wm_attributes('-alpha', 0.95)
    except:
        pass
    
    # Size and position
    popup_w, popup_h = 340, 110
    root.update_idletasks()
    rx = root.winfo_rootx() + root.winfo_width() - popup_w - 20
    ry = root.winfo_rooty() + 20
    popup.geometry(f"{popup_w}x{popup_h}+{rx}+{ry}")
    
    # Create a frame with better styling
    main_frame = tk.Frame(popup, bg='#1e1e2e', relief='solid', bd=2)
    main_frame.pack(fill='both', expand=True, padx=1, pady=1)
    
    # Left accent bar
    accent_bar = tk.Frame(main_frame, bg=bg_color, width=5)
    accent_bar.pack(side='left', fill='y', padx=(0, 10))
    
    # Content frame
    content_frame = tk.Frame(main_frame, bg='#1e1e2e')
    content_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
    
    # Icon and title in top row
    top_frame = tk.Frame(content_frame, bg='#1e1e2e')
    top_frame.pack(fill='x')
    
    # Icon
    icon_label = tk.Label(top_frame, text=achievement.icon if hasattr(achievement, 'icon') else '🏆',
                          font=('Arial', 24), bg='#1e1e2e', fg='white')
    icon_label.pack(side='left', padx=(0, 10))
    
    # Text content
    text_frame = tk.Frame(top_frame, bg='#1e1e2e')
    text_frame.pack(side='left', fill='both', expand=True)
    
    # "Achievement Unlocked!" header
    header_label = tk.Label(text_frame, text='Achievement Unlocked!',
                           font=('Arial', 10, 'bold'), bg='#1e1e2e', fg=bg_color, anchor='w')
    header_label.pack(fill='x')
    
    # Achievement name
    name_text = achievement.name if hasattr(achievement, 'name') else 'Achievement'
    if len(name_text) > 32:
        name_text = name_text[:30] + '…'
    name_label = tk.Label(text_frame, text=name_text,
                         font=('Arial', 13, 'bold'), bg='#1e1e2e', fg='white', anchor='w')
    name_label.pack(fill='x')
    
    # Description
    desc_text = achievement.description if hasattr(achievement, 'description') else ''
    if len(desc_text) > 42:
        desc_text = desc_text[:40] + '…'
    if desc_text:
        desc_label = tk.Label(text_frame, text=desc_text,
                            font=('Arial', 9), bg='#1e1e2e', fg='#aaaaaa', anchor='w')
        desc_label.pack(fill='x')
    
    # Reward line
    if hasattr(achievement, 'reward') and achievement.reward:
        reward_text = f"🎁 {achievement.reward.get('description', '')}"
        if len(reward_text) > 45:
            reward_text = reward_text[:43] + '…'
        if reward_text:
            reward_label = tk.Label(content_frame, text=reward_text,
                                   font=('Arial', 9, 'italic'), bg='#1e1e2e', fg=bg_color, anchor='w')
            reward_label.pack(fill='x', pady=(5, 0))
    
    # Auto-close after 5 seconds with fade
    def _fade_out(alpha=1.0):
        try:
            if alpha <= 0:
                popup.destroy()
                return
            popup.wm_attributes('-alpha', alpha)
            popup.after(50, lambda: _fade_out(alpha - 0.05))
        except Exception:
            popup.destroy()
    
    popup.after(5000, lambda: _fade_out())
    
    # Click to close
    def _close(event=None):
        try:
            popup.destroy()
        except:
            pass
    
    popup.bind('<Button-1>', _close)
    main_frame.bind('<Button-1>', _close)

"""
Integrated Dungeon Demo - Full game experience.
Shows enhanced visuals, enemy spawning, combat, loot, and navigation.
"""

import tkinter as tk
from src.features.integrated_dungeon import IntegratedDungeon
from src.ui.enhanced_dungeon_renderer import EnhancedDungeonRenderer


class IntegratedDungeonDemo:
    """Complete dungeon game demo with all systems integrated."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Integrated Dungeon System - HD Visuals + Full Combat")
        
        # Create main frame
        main_frame = tk.Frame(root, bg='#0a0a0a')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for dungeon
        self.canvas = tk.Canvas(
            main_frame,
            width=800,
            height=600,
            bg='#000000',
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Create control panel
        control_frame = tk.Frame(main_frame, bg='#1a1a1a', width=280)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        # Initialize dungeon system
        self.dungeon = IntegratedDungeon(width=80, height=80, num_floors=5)
        self.renderer = EnhancedDungeonRenderer(self.canvas, self.dungeon.dungeon)
        
        # Set player to spawn point
        self.dungeon.teleport_to_spawn()
        self.renderer.center_camera_on_tile(self.dungeon.player_x, self.dungeon.player_y)
        self.renderer.mark_explored(self.dungeon.player_x, self.dungeon.player_y, radius=5)
        
        # UI state
        self.show_fog = True
        self.show_minimap = True
        self.auto_update = False
        
        # Setup UI
        self._setup_ui(control_frame)
        
        # Bind keys
        self.root.bind('<KeyPress>', self._on_key_press)
        
        # Start render loop
        self._update_loop()
    
    def _setup_ui(self, frame):
        """Setup the UI control panel."""
        # Title
        title = tk.Label(
            frame,
            text="🏰 Integrated Dungeon",
            font=('Arial', 14, 'bold'),
            bg='#1a1a1a',
            fg='#ffd700'
        )
        title.pack(pady=10)
        
        # Player Stats
        stats_frame = tk.LabelFrame(
            frame,
            text="Player Status",
            bg='#2a2a2a',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        stats_frame.pack(pady=5, padx=10, fill=tk.X)
        
        self.health_label = tk.Label(
            stats_frame,
            text="Health: 100/100",
            bg='#2a2a2a',
            fg='#4aff4a',
            font=('Arial', 10)
        )
        self.health_label.pack(pady=2)
        
        self.position_label = tk.Label(
            stats_frame,
            text="Position: (0, 0)",
            bg='#2a2a2a',
            fg='white',
            font=('Arial', 9)
        )
        self.position_label.pack(pady=2)
        
        self.floor_label = tk.Label(
            stats_frame,
            text="Floor: 1/5",
            bg='#2a2a2a',
            fg='white',
            font=('Arial', 9)
        )
        self.floor_label.pack(pady=2)
        
        # Statistics
        stats_frame2 = tk.LabelFrame(
            frame,
            text="Statistics",
            bg='#2a2a2a',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        stats_frame2.pack(pady=5, padx=10, fill=tk.X)
        
        self.enemies_label = tk.Label(
            stats_frame2,
            text="Enemies Killed: 0",
            bg='#2a2a2a',
            fg='#ff6666',
            font=('Arial', 9)
        )
        self.enemies_label.pack(pady=2)
        
        self.loot_label = tk.Label(
            stats_frame2,
            text="Loot Collected: 0",
            bg='#2a2a2a',
            fg='#ffd700',
            font=('Arial', 9)
        )
        self.loot_label.pack(pady=2)
        
        # Controls info
        tk.Label(
            frame,
            text="Controls",
            font=('Arial', 12, 'bold'),
            bg='#1a1a1a',
            fg='white'
        ).pack(pady=10)
        
        controls_text = """
WASD or Arrows: Move
Space: Attack nearby enemies
E: Use stairs (when on them)
F: Toggle fog of war
M: Toggle minimap
N: New dungeon
"""
        tk.Label(
            frame,
            text=controls_text,
            bg='#1a1a1a',
            fg='#cccccc',
            font=('Arial', 9),
            justify=tk.LEFT
        ).pack(pady=5)
        
        # Action buttons
        tk.Button(
            frame,
            text="⚔️ Attack",
            command=self._attack,
            bg='#ff4444',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=20
        ).pack(pady=3)
        
        tk.Button(
            frame,
            text="🔼 Use Stairs Up",
            command=lambda: self._use_stairs(True),
            bg='#4a9fff',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=20
        ).pack(pady=3)
        
        tk.Button(
            frame,
            text="🔽 Use Stairs Down",
            command=lambda: self._use_stairs(False),
            bg='#ff9f4a',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=20
        ).pack(pady=3)
        
        tk.Button(
            frame,
            text="🔄 Generate New Dungeon",
            command=self._generate_new,
            bg='#4aff4a',
            fg='black',
            font=('Arial', 10, 'bold'),
            width=20
        ).pack(pady=10)
        
        # Checkboxes
        self.fog_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            frame,
            text="Fog of War",
            variable=self.fog_var,
            command=self._toggle_fog,
            bg='#1a1a1a',
            fg='white',
            selectcolor='#2a2a2a',
            font=('Arial', 9)
        ).pack(pady=2)
        
        self.minimap_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            frame,
            text="Show Minimap",
            variable=self.minimap_var,
            command=self._toggle_minimap,
            bg='#1a1a1a',
            fg='white',
            selectcolor='#2a2a2a',
            font=('Arial', 9)
        ).pack(pady=2)
    
    def _update_ui(self):
        """Update UI labels with current state."""
        state = self.dungeon.get_player_state()
        
        self.health_label.config(
            text=f"Health: {state['health']}/{state['max_health']}"
        )
        self.position_label.config(
            text=f"Position: ({state['x']}, {state['y']})"
        )
        self.floor_label.config(
            text=f"Floor: {state['floor'] + 1}/5"
        )
        self.enemies_label.config(
            text=f"Enemies Killed: {state['enemies_killed']}"
        )
        self.loot_label.config(
            text=f"Loot Collected: {state['loot_collected']}"
        )
    
    def _on_key_press(self, event):
        """Handle key press events."""
        key = event.keysym.lower()
        
        # Movement
        if key in ['w', 'up']:
            self.dungeon.move_player(0, -1)
        elif key in ['s', 'down']:
            self.dungeon.move_player(0, 1)
        elif key in ['a', 'left']:
            self.dungeon.move_player(-1, 0)
        elif key in ['d', 'right']:
            self.dungeon.move_player(1, 0)
        
        # Actions
        elif key == 'space':
            self._attack()
        elif key == 'e':
            self._try_use_stairs()
        elif key == 'f':
            self.fog_var.set(not self.fog_var.get())
            self._toggle_fog()
        elif key == 'm':
            self.minimap_var.set(not self.minimap_var.get())
            self._toggle_minimap()
        elif key == 'n':
            self._generate_new()
        
        # Update camera and exploration
        self.renderer.center_camera_on_tile(self.dungeon.player_x, self.dungeon.player_y)
        self.renderer.mark_explored(self.dungeon.player_x, self.dungeon.player_y, radius=5)
    
    def _attack(self):
        """Player attacks nearby enemies."""
        self.dungeon.player_attack_nearby_enemies(weapon_damage=25)
    
    def _use_stairs(self, going_up: bool):
        """Use stairs."""
        if self.dungeon.use_stairs(going_up):
            self.renderer.set_floor(self.dungeon.player_floor)
            self.renderer.center_camera_on_tile(self.dungeon.player_x, self.dungeon.player_y)
            self.renderer.mark_explored(self.dungeon.player_x, self.dungeon.player_y, radius=5)
    
    def _try_use_stairs(self):
        """Try to use stairs based on current position."""
        floor = self.dungeon.dungeon.get_floor(self.dungeon.player_floor)
        if not floor:
            return
        
        pos = (self.dungeon.player_x, self.dungeon.player_y)
        
        if pos in floor.stairs_up:
            self._use_stairs(True)
        elif pos in floor.stairs_down:
            self._use_stairs(False)
    
    def _toggle_fog(self):
        """Toggle fog of war."""
        self.show_fog = self.fog_var.get()
    
    def _toggle_minimap(self):
        """Toggle minimap."""
        self.show_minimap = self.minimap_var.get()
    
    def _generate_new(self):
        """Generate a new dungeon."""
        self.dungeon = IntegratedDungeon(width=80, height=80, num_floors=5)
        self.renderer = EnhancedDungeonRenderer(self.canvas, self.dungeon.dungeon)
        self.dungeon.teleport_to_spawn()
        self.renderer.center_camera_on_tile(self.dungeon.player_x, self.dungeon.player_y)
        self.renderer.mark_explored(self.dungeon.player_x, self.dungeon.player_y, radius=5)
    
    def _update_loop(self):
        """Main update loop."""
        # Update enemies
        self.dungeon.update_enemies(0.016)  # ~60 FPS
        
        # Render dungeon
        self.renderer.set_floor(self.dungeon.player_floor)
        self.renderer.render(show_fog=self.show_fog)
        
        # Render entities
        # Render player
        self.renderer.render_entity(
            self.dungeon.player_x,
            self.dungeon.player_y,
            '🐼',
            size=24
        )
        
        # Render enemies
        for enemy in self.dungeon.get_enemies_on_current_floor():
            self.renderer.render_entity(
                enemy.x,
                enemy.y,
                enemy.enemy.icon,
                size=20
            )
        
        # Render loot
        for loot in self.dungeon.get_loot_on_current_floor():
            loot_icon = {
                'health': '❤️',
                'weapon': '⚔️',
                'gold': '💰',
                'key': '🔑'
            }.get(loot.item_type, '📦')
            
            self.renderer.render_entity(
                loot.x,
                loot.y,
                loot_icon,
                size=16
            )
        
        # Render minimap
        if self.show_minimap:
            self.renderer.render_minimap(640, 10, size=150)
            
            # Mark player position on minimap
            state = self.dungeon.get_player_state()
            floor = self.dungeon.dungeon.get_floor(state['floor'])
            if floor:
                scale = 150 / max(floor.width, floor.height)
                px = 640 + int(state['x'] * scale)
                py = 10 + int(state['y'] * scale)
                self.canvas.create_oval(
                    px - 3, py - 3, px + 3, py + 3,
                    fill='red', outline='white', width=2,
                    tags='minimap'
                )
        
        # Update UI
        self._update_ui()
        
        # Schedule next update
        self.root.after(50, self._update_loop)


if __name__ == '__main__':
    root = tk.Tk()
    demo = IntegratedDungeonDemo(root)
    root.mainloop()

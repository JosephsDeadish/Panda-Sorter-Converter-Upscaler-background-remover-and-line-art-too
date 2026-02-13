"""
Interactive Dungeon Demo - Procedurally Generated Labyrinth
Shows dungeon generation, rendering, collision, and navigation.
"""

import tkinter as tk
from src.features.dungeon_generator import DungeonGenerator
from src.ui.dungeon_renderer import DungeonRenderer


class DungeonDemo:
    """Interactive dungeon exploration demo."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Procedural Dungeon Demo - Gauntlet Legends Style")
        
        # Create main frame
        main_frame = tk.Frame(root, bg='#1a1a1a')
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
        control_frame = tk.Frame(main_frame, bg='#2a2a2a', width=250)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        # Title
        title = tk.Label(
            control_frame,
            text="Dungeon Controls",
            font=('Arial', 14, 'bold'),
            bg='#2a2a2a',
            fg='white'
        )
        title.pack(pady=10)
        
        # Generate new dungeon button
        tk.Button(
            control_frame,
            text="Generate New Dungeon",
            command=self.generate_new_dungeon,
            bg='#4a9fff',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.RAISED,
            padx=10,
            pady=5
        ).pack(pady=5)
        
        # Floor controls
        floor_frame = tk.Frame(control_frame, bg='#2a2a2a')
        floor_frame.pack(pady=10)
        
        tk.Label(
            floor_frame,
            text="Floor:",
            bg='#2a2a2a',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.LEFT)
        
        tk.Button(
            floor_frame,
            text="↑ Up",
            command=self.go_up,
            bg='#4a9fff',
            fg='white',
            width=5
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            floor_frame,
            text="↓ Down",
            command=self.go_down,
            bg='#ff9f4a',
            fg='white',
            width=5
        ).pack(side=tk.LEFT, padx=2)
        
        # Panda movement controls
        tk.Label(
            control_frame,
            text="Panda Movement",
            font=('Arial', 12, 'bold'),
            bg='#2a2a2a',
            fg='white'
        ).pack(pady=10)
        
        move_frame = tk.Frame(control_frame, bg='#2a2a2a')
        move_frame.pack()
        
        # Arrow keys grid
        tk.Button(
            move_frame,
            text="↑",
            command=lambda: self.move_panda(0, -1),
            bg='#4a4a4a',
            fg='white',
            width=3
        ).grid(row=0, column=1)
        
        tk.Button(
            move_frame,
            text="←",
            command=lambda: self.move_panda(-1, 0),
            bg='#4a4a4a',
            fg='white',
            width=3
        ).grid(row=1, column=0)
        
        tk.Button(
            move_frame,
            text="→",
            command=lambda: self.move_panda(1, 0),
            bg='#4a4a4a',
            fg='white',
            width=3
        ).grid(row=1, column=2)
        
        tk.Button(
            move_frame,
            text="↓",
            command=lambda: self.move_panda(0, 1),
            bg='#4a4a4a',
            fg='white',
            width=3
        ).grid(row=2, column=1)
        
        # Options
        self.fog_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            control_frame,
            text="Fog of War",
            variable=self.fog_var,
            command=self.render_dungeon,
            bg='#2a2a2a',
            fg='white',
            selectcolor='#1a1a1a',
            font=('Arial', 10)
        ).pack(pady=5)
        
        self.minimap_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            control_frame,
            text="Show Minimap",
            variable=self.minimap_var,
            command=self.render_dungeon,
            bg='#2a2a2a',
            fg='white',
            selectcolor='#1a1a1a',
            font=('Arial', 10)
        ).pack(pady=5)
        
        # Stats display
        self.stats_label = tk.Label(
            control_frame,
            text="",
            bg='#2a2a2a',
            fg='white',
            font=('Arial', 9),
            justify=tk.LEFT
        )
        self.stats_label.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(
            control_frame,
            text="\nInstructions:\n\n"
                 "• Use arrow buttons or WASD\n"
                 "• Explore the dungeon\n"
                 "• Find stairs (↑↓) to change floors\n"
                 "• 🟢 Spawn room\n"
                 "• 🟨 Treasure room\n"
                 "• 🔺 Boss room\n"
                 "• Camera follows panda\n"
                 "• Collision prevents wall walking",
            bg='#2a2a2a',
            fg='#aaaaaa',
            font=('Arial', 8),
            justify=tk.LEFT
        )
        instructions.pack(side=tk.BOTTOM, pady=10)
        
        # Generate initial dungeon
        self.dungeon = None
        self.renderer = None
        self.panda_x = 0
        self.panda_y = 0
        self.generate_new_dungeon()
        
        # Keyboard bindings
        self.root.bind('<w>', lambda e: self.move_panda(0, -1))
        self.root.bind('<s>', lambda e: self.move_panda(0, 1))
        self.root.bind('<a>', lambda e: self.move_panda(-1, 0))
        self.root.bind('<d>', lambda e: self.move_panda(1, 0))
        self.root.bind('<Up>', lambda e: self.move_panda(0, -1))
        self.root.bind('<Down>', lambda e: self.move_panda(0, 1))
        self.root.bind('<Left>', lambda e: self.move_panda(-1, 0))
        self.root.bind('<Right>', lambda e: self.move_panda(1, 0))
    
    def generate_new_dungeon(self):
        """Generate a new procedural dungeon."""
        import random
        seed = random.randint(1, 999999)
        
        # Generate dungeon with 5 floors
        self.dungeon = DungeonGenerator(
            width=80,
            height=80,
            num_floors=5,
            seed=seed
        )
        
        # Create renderer
        self.renderer = DungeonRenderer(self.canvas, self.dungeon)
        self.renderer.viewport_width = 800
        self.renderer.viewport_height = 600
        
        # Start at spawn point
        floor = self.dungeon.get_floor(0)
        if floor and floor.spawn_point:
            self.panda_x, self.panda_y = floor.spawn_point
            self.renderer.mark_explored(self.panda_x, self.panda_y, radius=5)
        
        self.update_stats()
        self.render_dungeon()
    
    def render_dungeon(self):
        """Render the dungeon with current camera position."""
        # Center camera on panda
        self.renderer.center_camera_on_tile(self.panda_x, self.panda_y)
        
        # Render dungeon
        self.renderer.render(show_fog=self.fog_var.get())
        
        # Render panda
        self.renderer.render_entity(self.panda_x, self.panda_y, '🐼', size=28)
        
        # Render minimap if enabled
        if self.minimap_var.get():
            self.renderer.render_minimap(640, 10, size=150)
            
            # Mark panda position on minimap
            floor = self.dungeon.get_floor(self.renderer.current_floor)
            if floor:
                scale = min(150 / floor.width, 150 / floor.height)
                px = 640 + int(self.panda_x * scale)
                py = 10 + int(self.panda_y * scale)
                self.canvas.create_oval(
                    px - 3, py - 3, px + 3, py + 3,
                    fill='red', outline='white', width=1,
                    tags='minimap'
                )
    
    def move_panda(self, dx: int, dy: int):
        """Move the panda, checking collisions."""
        new_x = self.panda_x + dx
        new_y = self.panda_y + dy
        
        # Check if walkable
        if self.dungeon.is_walkable(self.renderer.current_floor, new_x, new_y):
            self.panda_x = new_x
            self.panda_y = new_y
            
            # Mark as explored
            self.renderer.mark_explored(self.panda_x, self.panda_y, radius=5)
            
            # Check for stairs
            self._check_stairs()
            
            self.update_stats()
            self.render_dungeon()
    
    def _check_stairs(self):
        """Check if panda is on stairs."""
        floor = self.dungeon.get_floor(self.renderer.current_floor)
        if not floor:
            return
        
        pos = (self.panda_x, self.panda_y)
        
        # Check stairs up
        if pos in floor.stairs_up:
            self.stats_label.config(text="Standing on stairs UP!\nPress ↑ to ascend")
        # Check stairs down
        elif pos in floor.stairs_down:
            self.stats_label.config(text="Standing on stairs DOWN!\nPress ↓ to descend")
    
    def go_up(self):
        """Go up one floor if on stairs."""
        floor = self.dungeon.get_floor(self.renderer.current_floor)
        if not floor:
            return
        
        pos = (self.panda_x, self.panda_y)
        if pos in floor.stairs_up and self.renderer.current_floor > 0:
            # Move up
            self.renderer.set_floor(self.renderer.current_floor - 1)
            # Find stairs down on new floor to teleport to
            new_floor = self.dungeon.get_floor(self.renderer.current_floor)
            if new_floor and new_floor.stairs_down:
                self.panda_x, self.panda_y = new_floor.stairs_down[0]
                self.renderer.mark_explored(self.panda_x, self.panda_y, radius=5)
            self.update_stats()
            self.render_dungeon()
    
    def go_down(self):
        """Go down one floor if on stairs."""
        floor = self.dungeon.get_floor(self.renderer.current_floor)
        if not floor:
            return
        
        pos = (self.panda_x, self.panda_y)
        if pos in floor.stairs_down and self.renderer.current_floor < len(self.dungeon.floors) - 1:
            # Move down
            self.renderer.set_floor(self.renderer.current_floor + 1)
            # Find stairs up on new floor to teleport to
            new_floor = self.dungeon.get_floor(self.renderer.current_floor)
            if new_floor and new_floor.stairs_up:
                self.panda_x, self.panda_y = new_floor.stairs_up[0]
                self.renderer.mark_explored(self.panda_x, self.panda_y, radius=5)
            self.update_stats()
            self.render_dungeon()
    
    def update_stats(self):
        """Update stats display."""
        floor = self.dungeon.get_floor(self.renderer.current_floor)
        if not floor:
            return
        
        # Count explored tiles
        explored_count = len([1 for (x, y) in self.renderer.explored 
                             if 0 <= x < floor.width and 0 <= y < floor.height])
        
        # Count total walkable tiles
        walkable_count = sum(1 for row in floor.collision_map for tile in row if tile == 0)
        
        explored_percent = (explored_count / walkable_count * 100) if walkable_count > 0 else 0
        
        stats_text = f"Floor: {floor.floor_number + 1} / {len(self.dungeon.floors)}\n"
        stats_text += f"Position: ({self.panda_x}, {self.panda_y})\n"
        stats_text += f"Rooms: {len(floor.rooms)}\n"
        stats_text += f"Explored: {explored_percent:.1f}%\n"
        stats_text += f"({explored_count}/{walkable_count} tiles)"
        
        self.stats_label.config(text=stats_text)


def main():
    """Run the dungeon demo."""
    root = tk.Tk()
    root.geometry("1070x620")
    root.resizable(False, False)
    demo = DungeonDemo(root)
    root.mainloop()


if __name__ == '__main__':
    main()

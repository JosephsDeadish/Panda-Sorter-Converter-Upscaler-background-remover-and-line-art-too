"""
Dungeon Renderer for visualizing procedurally generated dungeons.
Renders tiles, walls, floors, stairs, and entities.
"""

import tkinter as tk
from typing import Tuple, Optional, List
from src.features.dungeon_generator import DungeonGenerator, DungeonFloor, Room


class DungeonRenderer:
    """Renders dungeons using tkinter canvas."""
    
    # Tile size in pixels
    TILE_SIZE = 32
    
    # Colors for different tile types
    COLORS = {
        'wall': '#3a3a3a',
        'floor': '#8b7355',
        'corridor': '#7a6545',
        'stairs_up': '#4a9fff',
        'stairs_down': '#ff9f4a',
        'spawn': '#4aff4a',
        'treasure': '#ffd700',
        'boss': '#ff4a4a',
        'explored': '#6a5a45',
        'unexplored': '#1a1a1a'
    }
    
    def __init__(self, canvas: tk.Canvas, dungeon: DungeonGenerator):
        """
        Initialize the renderer.
        
        Args:
            canvas: Tkinter canvas to draw on
            dungeon: Dungeon generator instance
        """
        self.canvas = canvas
        self.dungeon = dungeon
        self.current_floor = 0
        
        # Camera position (in pixels)
        self.camera_x = 0
        self.camera_y = 0
        
        # Fog of war (explored tiles)
        self.explored = set()
        
        # Viewport size
        self.viewport_width = 800
        self.viewport_height = 600
    
    def set_floor(self, floor_num: int):
        """Change the current floor being rendered."""
        if 0 <= floor_num < len(self.dungeon.floors):
            self.current_floor = floor_num
            self.explored.clear()  # Reset fog of war
    
    def set_camera(self, x: int, y: int):
        """Set camera position (in pixels)."""
        self.camera_x = x
        self.camera_y = y
    
    def center_camera_on_tile(self, tile_x: int, tile_y: int):
        """Center camera on a specific tile."""
        pixel_x = tile_x * self.TILE_SIZE
        pixel_y = tile_y * self.TILE_SIZE
        self.camera_x = pixel_x - self.viewport_width // 2
        self.camera_y = pixel_y - self.viewport_height // 2
    
    def mark_explored(self, tile_x: int, tile_y: int, radius: int = 5):
        """Mark tiles as explored (for fog of war)."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    self.explored.add((tile_x + dx, tile_y + dy))
    
    def render(self, show_fog: bool = True):
        """
        Render the current floor.
        
        Args:
            show_fog: Whether to apply fog of war
        """
        self.canvas.delete('all')
        
        floor = self.dungeon.get_floor(self.current_floor)
        if not floor:
            return
        
        # Calculate visible tile range
        start_tile_x = max(0, self.camera_x // self.TILE_SIZE)
        start_tile_y = max(0, self.camera_y // self.TILE_SIZE)
        end_tile_x = min(floor.width, (self.camera_x + self.viewport_width) // self.TILE_SIZE + 1)
        end_tile_y = min(floor.height, (self.camera_y + self.viewport_height) // self.TILE_SIZE + 1)
        
        # Render tiles
        for tile_y in range(start_tile_y, end_tile_y):
            for tile_x in range(start_tile_x, end_tile_x):
                self._render_tile(floor, tile_x, tile_y, show_fog)
        
        # Render stairs
        self._render_stairs(floor, show_fog)
        
        # Render room markers
        self._render_room_markers(floor, show_fog)
        
        # Render floor info
        self._render_floor_info(floor)
    
    def _render_tile(self, floor: DungeonFloor, tile_x: int, tile_y: int, show_fog: bool):
        """Render a single tile."""
        # Check fog of war
        if show_fog and (tile_x, tile_y) not in self.explored:
            color = self.COLORS['unexplored']
        else:
            # Determine tile color
            is_wall = floor.collision_map[tile_y][tile_x] == 1
            color = self.COLORS['wall'] if is_wall else self.COLORS['floor']
        
        # Convert to screen coordinates
        screen_x = tile_x * self.TILE_SIZE - self.camera_x
        screen_y = tile_y * self.TILE_SIZE - self.camera_y
        
        # Draw tile
        self.canvas.create_rectangle(
            screen_x, screen_y,
            screen_x + self.TILE_SIZE, screen_y + self.TILE_SIZE,
            fill=color, outline='#2a2a2a', width=1,
            tags='tile'
        )
    
    def _render_stairs(self, floor: DungeonFloor, show_fog: bool):
        """Render stairs."""
        # Stairs up
        for tile_x, tile_y in floor.stairs_up:
            if not show_fog or (tile_x, tile_y) in self.explored:
                screen_x = tile_x * self.TILE_SIZE - self.camera_x
                screen_y = tile_y * self.TILE_SIZE - self.camera_y
                
                # Draw stair marker
                self.canvas.create_rectangle(
                    screen_x + 4, screen_y + 4,
                    screen_x + self.TILE_SIZE - 4, screen_y + self.TILE_SIZE - 4,
                    fill=self.COLORS['stairs_up'], outline='white', width=2,
                    tags='stairs'
                )
                self.canvas.create_text(
                    screen_x + self.TILE_SIZE // 2, screen_y + self.TILE_SIZE // 2,
                    text='↑', fill='white', font=('Arial', 16, 'bold'),
                    tags='stairs'
                )
        
        # Stairs down
        for tile_x, tile_y in floor.stairs_down:
            if not show_fog or (tile_x, tile_y) in self.explored:
                screen_x = tile_x * self.TILE_SIZE - self.camera_x
                screen_y = tile_y * self.TILE_SIZE - self.camera_y
                
                # Draw stair marker
                self.canvas.create_rectangle(
                    screen_x + 4, screen_y + 4,
                    screen_x + self.TILE_SIZE - 4, screen_y + self.TILE_SIZE - 4,
                    fill=self.COLORS['stairs_down'], outline='white', width=2,
                    tags='stairs'
                )
                self.canvas.create_text(
                    screen_x + self.TILE_SIZE // 2, screen_y + self.TILE_SIZE // 2,
                    text='↓', fill='white', font=('Arial', 16, 'bold'),
                    tags='stairs'
                )
    
    def _render_room_markers(self, floor: DungeonFloor, show_fog: bool):
        """Render special room markers."""
        for room in floor.rooms:
            cx, cy = room.center
            if not show_fog or (cx, cy) in self.explored:
                screen_x = cx * self.TILE_SIZE - self.camera_x
                screen_y = cy * self.TILE_SIZE - self.camera_y
                
                # Draw marker based on room type
                if room.room_type == 'spawn':
                    self.canvas.create_oval(
                        screen_x - 8, screen_y - 8,
                        screen_x + 8, screen_y + 8,
                        fill=self.COLORS['spawn'], outline='white', width=2,
                        tags='marker'
                    )
                elif room.room_type == 'treasure':
                    self.canvas.create_rectangle(
                        screen_x - 6, screen_y - 6,
                        screen_x + 6, screen_y + 6,
                        fill=self.COLORS['treasure'], outline='white', width=2,
                        tags='marker'
                    )
                elif room.room_type == 'boss':
                    self.canvas.create_polygon(
                        screen_x, screen_y - 10,
                        screen_x + 8, screen_y + 6,
                        screen_x - 8, screen_y + 6,
                        fill=self.COLORS['boss'], outline='white', width=2,
                        tags='marker'
                    )
    
    def _render_floor_info(self, floor: DungeonFloor):
        """Render floor information overlay."""
        info_text = f"Floor {floor.floor_number + 1} / {len(self.dungeon.floors)}"
        self.canvas.create_rectangle(
            10, 10, 150, 40,
            fill='#2a2a2a', outline='white', width=2,
            tags='ui'
        )
        self.canvas.create_text(
            80, 25,
            text=info_text, fill='white', font=('Arial', 12, 'bold'),
            tags='ui'
        )
    
    def render_entity(self, tile_x: int, tile_y: int, emoji: str, size: int = 24):
        """
        Render an entity (panda, enemy) at a tile position.
        
        Args:
            tile_x, tile_y: Tile coordinates
            emoji: Emoji to display
            size: Font size
        """
        screen_x = tile_x * self.TILE_SIZE - self.camera_x + self.TILE_SIZE // 2
        screen_y = tile_y * self.TILE_SIZE - self.camera_y + self.TILE_SIZE // 2
        
        self.canvas.create_text(
            screen_x, screen_y,
            text=emoji, fill='white', font=('Arial', size),
            tags='entity'
        )
    
    def render_minimap(self, x: int, y: int, size: int = 150):
        """
        Render a minimap of the current floor.
        
        Args:
            x, y: Position for minimap
            size: Size of minimap in pixels
        """
        floor = self.dungeon.get_floor(self.current_floor)
        if not floor:
            return
        
        # Draw minimap background
        self.canvas.create_rectangle(
            x, y, x + size, y + size,
            fill='#1a1a1a', outline='white', width=2,
            tags='minimap'
        )
        
        # Calculate scale
        scale_x = size / floor.width
        scale_y = size / floor.height
        scale = min(scale_x, scale_y)
        
        # Draw rooms
        for room in floor.rooms:
            mx = x + int(room.x * scale)
            my = y + int(room.y * scale)
            mw = max(2, int(room.width * scale))
            mh = max(2, int(room.height * scale))
            
            # Color based on room type
            if room.room_type == 'spawn':
                color = self.COLORS['spawn']
            elif room.room_type == 'treasure':
                color = self.COLORS['treasure']
            elif room.room_type == 'boss':
                color = self.COLORS['boss']
            else:
                color = self.COLORS['floor']
            
            self.canvas.create_rectangle(
                mx, my, mx + mw, my + mh,
                fill=color, outline='', tags='minimap'
            )
        
        # Draw corridors
        for corridor in floor.corridors:
            for cx, cy in corridor.path:
                mx = x + int(cx * scale)
                my = y + int(cy * scale)
                pw = max(1, int(scale))
                
                self.canvas.create_rectangle(
                    mx, my, mx + pw, my + pw,
                    fill=self.COLORS['corridor'], outline='', tags='minimap'
                )
    
    def world_to_screen(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates (pixels) to screen coordinates."""
        return (world_x - self.camera_x, world_y - self.camera_y)
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert screen coordinates to world coordinates (pixels)."""
        return (screen_x + self.camera_x, screen_y + self.camera_y)
    
    def screen_to_tile(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert screen coordinates to tile coordinates."""
        world_x, world_y = self.screen_to_world(screen_x, screen_y)
        return (world_x // self.TILE_SIZE, world_y // self.TILE_SIZE)

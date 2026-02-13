"""
Enhanced Dungeon Renderer with HD textures and realistic visuals.
Provides improved visual fidelity for procedurally generated dungeons.
"""

import tkinter as tk
import math
import random
from typing import Tuple, Optional, List, Dict
from src.features.dungeon_generator import DungeonGenerator, DungeonFloor, Room


class EnhancedDungeonRenderer:
    """Renders dungeons with enhanced HD textures and realistic visuals."""
    
    # Tile size in pixels
    TILE_SIZE = 32
    
    # Enhanced color palettes for realistic textures
    STONE_COLORS = ['#4a4a4a', '#525252', '#3a3a3a', '#454545', '#484848']
    FLOOR_COLORS = ['#6b5a45', '#7a6545', '#8b7355', '#755d47', '#6a5742']
    CORRIDOR_COLORS = ['#5a4a35', '#6a5545', '#7a6545']
    
    def __init__(self, canvas: tk.Canvas, dungeon: DungeonGenerator):
        """
        Initialize the enhanced renderer.
        
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
        
        # Lighting/ambient effects
        self.torch_flicker_offset = 0
        
        # Texture cache for consistent patterns
        self.texture_cache: Dict[Tuple[int, int], str] = {}
    
    def set_floor(self, floor_num: int):
        """Change the current floor being rendered."""
        if 0 <= floor_num < len(self.dungeon.floors):
            self.current_floor = floor_num
            self.explored.clear()  # Reset fog of war
            self.texture_cache.clear()  # Clear texture cache
    
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
        Render the current floor with enhanced visuals.
        
        Args:
            show_fog: Whether to apply fog of war
        """
        self.canvas.delete('all')
        
        floor = self.dungeon.get_floor(self.current_floor)
        if not floor:
            return
        
        # Update torch flicker
        self.torch_flicker_offset = (self.torch_flicker_offset + 1) % 20
        
        # Calculate visible tile range
        start_tile_x = max(0, self.camera_x // self.TILE_SIZE)
        start_tile_y = max(0, self.camera_y // self.TILE_SIZE)
        end_tile_x = min(floor.width, (self.camera_x + self.viewport_width) // self.TILE_SIZE + 1)
        end_tile_y = min(floor.height, (self.camera_y + self.viewport_height) // self.TILE_SIZE + 1)
        
        # Render tiles with enhanced textures
        for tile_y in range(start_tile_y, end_tile_y):
            for tile_x in range(start_tile_x, end_tile_x):
                self._render_enhanced_tile(floor, tile_x, tile_y, show_fog)
        
        # Add decorative elements
        self._render_decorations(floor, show_fog, start_tile_x, start_tile_y, end_tile_x, end_tile_y)
        
        # Render stairs with enhanced visuals
        self._render_enhanced_stairs(floor, show_fog)
        
        # Render room markers
        self._render_room_markers(floor, show_fog)
        
        # Render floor info
        self._render_floor_info(floor)
    
    def _get_tile_texture(self, tile_x: int, tile_y: int, is_wall: bool) -> str:
        """Get consistent texture color for a tile using hash-based selection."""
        key = (tile_x, tile_y)
        if key not in self.texture_cache:
            # Use hash for consistent color selection (no seed manipulation)
            hash_val = hash(key) % 100
            colors = self.STONE_COLORS if is_wall else self.FLOOR_COLORS
            color_index = hash_val % len(colors)
            self.texture_cache[key] = colors[color_index]
        return self.texture_cache[key]
    
    def _render_enhanced_tile(self, floor: DungeonFloor, tile_x: int, tile_y: int, show_fog: bool):
        """Render a single tile with enhanced textures."""
        # Check fog of war
        is_explored = (tile_x, tile_y) in self.explored
        is_wall = floor.collision_map[tile_y][tile_x] == 1
        
        # Convert to screen coordinates
        screen_x = tile_x * self.TILE_SIZE - self.camera_x
        screen_y = tile_y * self.TILE_SIZE - self.camera_y
        
        if show_fog and not is_explored:
            # Unexplored - draw black
            self.canvas.create_rectangle(
                screen_x, screen_y,
                screen_x + self.TILE_SIZE, screen_y + self.TILE_SIZE,
                fill='#0a0a0a', outline='',
                tags='tile'
            )
        else:
            # Get texture color
            base_color = self._get_tile_texture(tile_x, tile_y, is_wall)
            
            if is_wall:
                self._render_wall_tile(screen_x, screen_y, base_color)
            else:
                self._render_floor_tile(screen_x, screen_y, base_color, tile_x, tile_y)
    
    def _render_wall_tile(self, screen_x: int, screen_y: int, base_color: str):
        """Render a wall tile with stone texture."""
        # Main wall block
        self.canvas.create_rectangle(
            screen_x, screen_y,
            screen_x + self.TILE_SIZE, screen_y + self.TILE_SIZE,
            fill=base_color, outline='#2a2a2a', width=1,
            tags='tile'
        )
        
        # Add stone brick pattern
        # Horizontal mortar line
        self.canvas.create_line(
            screen_x, screen_y + self.TILE_SIZE // 2,
            screen_x + self.TILE_SIZE, screen_y + self.TILE_SIZE // 2,
            fill='#2a2a2a', width=1,
            tags='tile'
        )
        
        # Add subtle 3D depth effect (highlight)
        self.canvas.create_line(
            screen_x + 1, screen_y + 1,
            screen_x + self.TILE_SIZE - 2, screen_y + 1,
            fill='#5a5a5a', width=1,
            tags='tile'
        )
        self.canvas.create_line(
            screen_x + 1, screen_y + 1,
            screen_x + 1, screen_y + self.TILE_SIZE - 2,
            fill='#5a5a5a', width=1,
            tags='tile'
        )
        
        # Add shadow for depth
        self.canvas.create_line(
            screen_x + self.TILE_SIZE - 2, screen_y + 2,
            screen_x + self.TILE_SIZE - 2, screen_y + self.TILE_SIZE - 1,
            fill='#2a2a2a', width=1,
            tags='tile'
        )
        self.canvas.create_line(
            screen_x + 2, screen_y + self.TILE_SIZE - 2,
            screen_x + self.TILE_SIZE - 1, screen_y + self.TILE_SIZE - 2,
            fill='#2a2a2a', width=1,
            tags='tile'
        )
    
    def _render_floor_tile(self, screen_x: int, screen_y: int, base_color: str, tile_x: int, tile_y: int):
        """Render a floor tile with stone floor texture."""
        # Main floor
        self.canvas.create_rectangle(
            screen_x, screen_y,
            screen_x + self.TILE_SIZE, screen_y + self.TILE_SIZE,
            fill=base_color, outline='#5a4a35', width=1,
            tags='tile'
        )
        
        # Add cracks and details using hash for consistency
        hash_val = hash((tile_x, tile_y))
        
        if (hash_val % 100) < 15:  # 15% chance of crack
            # Draw a crack
            cx1 = screen_x + ((hash_val % 20) + 5)
            cy1 = screen_y + (((hash_val // 100) % 20) + 5)
            cx2 = cx1 + ((hash_val % 17) - 8)
            cy2 = cy1 + (((hash_val // 1000) % 17) - 8)
            self.canvas.create_line(
                cx1, cy1, cx2, cy2,
                fill='#4a3a25', width=1,
                tags='tile'
            )
        
        if (hash_val % 100) < 10:  # 10% chance of spot
            # Draw a worn spot
            sx = screen_x + ((hash_val % 16) + 8)
            sy = screen_y + (((hash_val // 100) % 16) + 8)
            self.canvas.create_oval(
                sx - 2, sy - 2, sx + 2, sy + 2,
                fill='#5a4530', outline='',
                tags='tile'
            )
    
    def _render_decorations(self, floor: DungeonFloor, show_fog: bool, 
                          start_x: int, start_y: int, end_x: int, end_y: int):
        """Render decorative elements like torches and columns."""
        # Add torches near walls
        for room in floor.rooms:
            # Only render if room is in view
            if room.x > end_x or room.x + room.width < start_x:
                continue
            if room.y > end_y or room.y + room.height < start_y:
                continue
            
            # Place torches in corners
            corners = [
                (room.x + 1, room.y + 1),
                (room.x + room.width - 2, room.y + 1),
                (room.x + 1, room.y + room.height - 2),
                (room.x + room.width - 2, room.y + room.height - 2)
            ]
            
            for cx, cy in corners:
                if show_fog and (cx, cy) not in self.explored:
                    continue
                
                # Draw torch
                screen_x = cx * self.TILE_SIZE - self.camera_x + self.TILE_SIZE // 2
                screen_y = cy * self.TILE_SIZE - self.camera_y + self.TILE_SIZE // 2
                
                # Torch holder (brown stick)
                self.canvas.create_rectangle(
                    screen_x - 1, screen_y - 6,
                    screen_x + 1, screen_y + 6,
                    fill='#5a3a1a', outline='',
                    tags='decoration'
                )
                
                # Flickering flame effect
                flicker = math.sin(self.torch_flicker_offset / 3) * 2
                flame_colors = ['#ff8800', '#ffaa00', '#ff6600']
                flame_color = flame_colors[self.torch_flicker_offset % 3]
                
                self.canvas.create_oval(
                    screen_x - 4, screen_y - 10 + flicker,
                    screen_x + 4, screen_y - 2 + flicker,
                    fill=flame_color, outline='#ffaa00',
                    tags='decoration'
                )
                
                # Glow effect
                self.canvas.create_oval(
                    screen_x - 6, screen_y - 12 + flicker,
                    screen_x + 6, screen_y + flicker,
                    fill='', outline='#ffdd00', width=1,
                    tags='decoration'
                )
    
    def _render_enhanced_stairs(self, floor: DungeonFloor, show_fog: bool):
        """Render stairs with enhanced visuals."""
        # Stairs up
        for tile_x, tile_y in floor.stairs_up:
            if not show_fog or (tile_x, tile_y) in self.explored:
                screen_x = tile_x * self.TILE_SIZE - self.camera_x
                screen_y = tile_y * self.TILE_SIZE - self.camera_y
                
                # Draw stair structure
                for i in range(4):
                    offset = i * 6
                    self.canvas.create_rectangle(
                        screen_x + offset, screen_y + offset,
                        screen_x + self.TILE_SIZE - offset, screen_y + 8 + offset,
                        fill='#6a7a9a', outline='#4a5a7a', width=1,
                        tags='stairs'
                    )
                
                # Arrow indicator
                self.canvas.create_text(
                    screen_x + self.TILE_SIZE // 2, screen_y + self.TILE_SIZE // 2,
                    text='↑', fill='white', font=('Arial', 18, 'bold'),
                    tags='stairs'
                )
        
        # Stairs down
        for tile_x, tile_y in floor.stairs_down:
            if not show_fog or (tile_x, tile_y) in self.explored:
                screen_x = tile_x * self.TILE_SIZE - self.camera_x
                screen_y = tile_y * self.TILE_SIZE - self.camera_y
                
                # Draw stair structure (descending)
                for i in range(4):
                    offset = i * 6
                    self.canvas.create_rectangle(
                        screen_x + offset, screen_y + self.TILE_SIZE - 8 - offset,
                        screen_x + self.TILE_SIZE - offset, screen_y + self.TILE_SIZE - offset,
                        fill='#8a6a4a', outline='#6a4a2a', width=1,
                        tags='stairs'
                    )
                
                # Arrow indicator
                self.canvas.create_text(
                    screen_x + self.TILE_SIZE // 2, screen_y + self.TILE_SIZE // 2,
                    text='↓', fill='white', font=('Arial', 18, 'bold'),
                    tags='stairs'
                )
    
    def _render_room_markers(self, floor: DungeonFloor, show_fog: bool):
        """Render special room markers with enhanced visuals."""
        for room in floor.rooms:
            cx, cy = room.center
            if not show_fog or (cx, cy) in self.explored:
                screen_x = cx * self.TILE_SIZE - self.camera_x
                screen_y = cy * self.TILE_SIZE - self.camera_y
                
                # Draw marker based on room type
                if room.room_type == 'spawn':
                    # Spawn point - glowing green circle
                    self.canvas.create_oval(
                        screen_x - 10, screen_y - 10,
                        screen_x + 10, screen_y + 10,
                        fill='#2aff2a', outline='#1aff1a', width=3,
                        tags='marker'
                    )
                    self.canvas.create_oval(
                        screen_x - 6, screen_y - 6,
                        screen_x + 6, screen_y + 6,
                        fill='#4aff4a', outline='',
                        tags='marker'
                    )
                elif room.room_type == 'treasure':
                    # Treasure chest
                    self.canvas.create_rectangle(
                        screen_x - 8, screen_y - 4,
                        screen_x + 8, screen_y + 6,
                        fill='#8b6914', outline='#5a4510', width=2,
                        tags='marker'
                    )
                    self.canvas.create_arc(
                        screen_x - 8, screen_y - 8,
                        screen_x + 8, screen_y + 4,
                        start=0, extent=180,
                        fill='#8b6914', outline='#5a4510', width=2,
                        tags='marker'
                    )
                    # Gold shine
                    self.canvas.create_rectangle(
                        screen_x - 2, screen_y,
                        screen_x + 2, screen_y + 3,
                        fill='#ffd700', outline='',
                        tags='marker'
                    )
                elif room.room_type == 'boss':
                    # Boss skull
                    self.canvas.create_oval(
                        screen_x - 8, screen_y - 8,
                        screen_x + 8, screen_y + 6,
                        fill='#ff4a4a', outline='#aa0000', width=2,
                        tags='marker'
                    )
                    # Eyes
                    self.canvas.create_oval(
                        screen_x - 5, screen_y - 4,
                        screen_x - 2, screen_y - 1,
                        fill='#000000', outline='',
                        tags='marker'
                    )
                    self.canvas.create_oval(
                        screen_x + 2, screen_y - 4,
                        screen_x + 5, screen_y - 1,
                        fill='#000000', outline='',
                        tags='marker'
                    )
    
    def _render_floor_info(self, floor: DungeonFloor):
        """Render floor information overlay."""
        info_text = f"Floor {floor.floor_number + 1} / {len(self.dungeon.floors)}"
        
        # Background panel
        self.canvas.create_rectangle(
            10, 10, 180, 45,
            fill='#1a1a1a', outline='#4a4a4a', width=2,
            tags='ui'
        )
        
        # Text with shadow
        self.canvas.create_text(
            96, 29,
            text=info_text, fill='#888888', font=('Arial', 12, 'bold'),
            tags='ui'
        )
        self.canvas.create_text(
            95, 28,
            text=info_text, fill='#ffffff', font=('Arial', 12, 'bold'),
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
        
        # Shadow
        self.canvas.create_oval(
            screen_x - 8, screen_y + 8,
            screen_x + 8, screen_y + 12,
            fill='#000000', outline='', stipple='gray50',
            tags='entity'
        )
        
        # Entity
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
        
        # Draw minimap background with border
        self.canvas.create_rectangle(
            x, y, x + size, y + size,
            fill='#0a0a0a', outline='#4a4a4a', width=3,
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
                color = '#2aff2a'
            elif room.room_type == 'treasure':
                color = '#ffd700'
            elif room.room_type == 'boss':
                color = '#ff4a4a'
            else:
                color = '#6a5a45'
            
            self.canvas.create_rectangle(
                mx, my, mx + mw, my + mh,
                fill=color, outline='#4a4a4a', tags='minimap'
            )
        
        # Draw corridors
        for corridor in floor.corridors:
            for cx, cy in corridor.path:
                mx = x + int(cx * scale)
                my = y + int(cy * scale)
                pw = max(1, int(scale * 1.5))
                
                self.canvas.create_rectangle(
                    mx, my, mx + pw, my + pw,
                    fill='#5a4a35', outline='', tags='minimap'
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

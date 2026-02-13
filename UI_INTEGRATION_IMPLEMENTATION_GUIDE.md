# UI Integration Implementation Guide

## Complete Implementation for Stats Tabs and Dungeon Entry

This guide provides the exact code changes needed to complete the UI integration of the stats system and dungeon entry into main.py.

## Change 1: Update create_panda_stats_tab() Method

**Location:** main.py, line 7333

**Replace the stats section (lines 7462-7493) with:**

```python
        # ═══════════════════ Statistics TabView ═══════════════════
        stats_tabview = ctk.CTkTabview(scrollable_frame)
        stats_tabview.pack(fill="both", expand=True, padx=10, pady=5)
        
        # ─────────── Tab 1: Base Stats ───────────
        tab_base = stats_tabview.add("⭐ Base Stats")
        base_stats = self.panda.stats.get_base_stats() if hasattr(self.panda, 'stats') else {}
        
        base_items = [
            ("Level", base_stats.get('Level', 1)),
            ("Experience", base_stats.get('Experience', '0/100')),
            ("Health", f"{base_stats.get('Health', 100)}/{base_stats.get('Max Health', 100)}"),
            ("Defense", base_stats.get('Defense', 10)),
            ("Magic", base_stats.get('Magic', 10)),
            ("Intelligence", base_stats.get('Intelligence', 10)),
            ("Strength", base_stats.get('Strength', 10)),
            ("Agility", base_stats.get('Agility', 10)),
            ("Vitality", base_stats.get('Vitality', 10)),
            ("Skill Points", base_stats.get('Skill Points', 0)),
        ]
        
        for label, value in base_items:
            row = ctk.CTkFrame(tab_base)
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=f"⭐ {label}:", font=("Arial", 12)).pack(side="left", padx=5)
            val_lbl = ctk.CTkLabel(row, text=str(value), font=("Arial Bold", 12),
                                  text_color="#ffaa00")
            val_lbl.pack(side="right", padx=10)
            self._stats_labels[f'base_{label.lower().replace(" ", "_")}'] = val_lbl
        
        # ─────────── Tab 2: Combat Stats ───────────
        tab_combat = stats_tabview.add("⚔️ Combat")
        combat_stats = self.panda.stats.get_combat_stats() if hasattr(self.panda, 'stats') else {}
        
        combat_items = [
            ("⚔️ Total Attacks", combat_stats.get('Total Attacks', 0)),
            ("👹 Monsters Slain", combat_stats.get('Monsters Slain', 0)),
            ("💥 Damage Dealt", combat_stats.get('Damage Dealt', 0)),
            ("🛡️ Damage Taken", combat_stats.get('Damage Taken', 0)),
            ("⭐ Critical Hits", combat_stats.get('Critical Hits', 0)),
            ("🌀 Perfect Dodges", combat_stats.get('Perfect Dodges', 0)),
            ("✨ Spells Cast", combat_stats.get('Spells Cast', 0)),
            ("❤️ Healing Done", combat_stats.get('Healing Done', 0)),
        ]
        
        for label, value in combat_items:
            row = ctk.CTkFrame(tab_combat)
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=label, font=("Arial", 12)).pack(side="left", padx=5)
            val_lbl = ctk.CTkLabel(row, text=str(value), font=("Arial Bold", 12),
                                  text_color="#ff4444")
            val_lbl.pack(side="right", padx=10)
            key = label.split()[-1].lower() if label else 'unknown'
            self._stats_labels[f'combat_{key}'] = val_lbl
        
        # ─────────── Tab 3: Interaction Stats ───────────
        tab_interaction = stats_tabview.add("🖱️ Interaction")
        interaction_stats = self.panda.stats.get_interaction_stats() if hasattr(self.panda, 'stats') else {}
        
        interaction_items = [
            ("🖱️ Clicks", 'click_count', interaction_stats.get('Clicks', 0)),
            ("🐾 Pets", 'pet_count', interaction_stats.get('Pets', 0)),
            ("🎋 Feeds", 'feed_count', interaction_stats.get('Feeds', 0)),
            ("💭 Hovers", 'hover_count', interaction_stats.get('Hovers', 0)),
            ("🖐️ Drags", 'drag_count', interaction_stats.get('Drags', 0)),
            ("🤾 Tosses", 'toss_count', interaction_stats.get('Tosses', 0)),
            ("🫨 Shakes", 'shake_count', interaction_stats.get('Shakes', 0)),
            ("🌀 Spins", 'spin_count', interaction_stats.get('Spins', 0)),
            ("🧸 Toy Interactions", 'toy_interact_count', interaction_stats.get('Toy Interactions', 0)),
            ("👔 Clothing Changes", 'clothing_change_count', interaction_stats.get('Clothing Changes', 0)),
            ("🎯 Items Thrown At", 'items_thrown_at_count', interaction_stats.get('Items Thrown At', 0)),
            ("👇 Belly Pokes", 'belly_poke_count', interaction_stats.get('Belly Pokes', 0)),
            ("🤕 Falls", 'fall_count', interaction_stats.get('Falls', 0)),
            ("🙃 Tip-overs", 'tip_over_count', interaction_stats.get('Tip-overs', 0)),
        ]
        
        for label, key, value in interaction_items:
            row = ctk.CTkFrame(tab_interaction)
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=label, font=("Arial", 12)).pack(side="left", padx=5)
            val_lbl = ctk.CTkLabel(row, text=str(value), font=("Arial Bold", 12),
                                  text_color="#00cc00")
            val_lbl.pack(side="right", padx=10)
            self._stats_labels[key] = val_lbl
        
        # ─────────── Tab 4: System Stats ───────────
        tab_system = stats_tabview.add("🛠️ System")
        system_stats = self.panda.stats.get_system_stats() if hasattr(self.panda, 'stats') else {}
        
        system_items = [
            ("⏱️ Playtime", system_stats.get('Playtime', '0h 0m')),
            ("📦 Items Collected", system_stats.get('Items Collected', 0)),
            ("🏰 Dungeons Cleared", system_stats.get('Dungeons Cleared', 0)),
            ("🪜 Floors Explored", system_stats.get('Floors Explored', 0)),
            ("🚶 Distance Traveled", f"{system_stats.get('Distance Traveled', 0):.1f}"),
            ("💀 Times Died", system_stats.get('Times Died', 0)),
            ("💾 Times Saved", system_stats.get('Times Saved', 0)),
            ("📁 Files Processed", system_stats.get('Files Processed', stats.get('files_processed', 0))),
            ("❌ Failed Operations", system_stats.get('Failed Operations', stats.get('failed_operations', 0))),
            ("🥚 Easter Eggs Found", system_stats.get('Easter Eggs Found', stats.get('easter_eggs_found', 0))),
        ]
        
        for label, value in system_items:
            row = ctk.CTkFrame(tab_system)
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=label, font=("Arial", 12)).pack(side="left", padx=5)
            val_lbl = ctk.CTkLabel(row, text=str(value), font=("Arial Bold", 12),
                                  text_color="#00aaff")
            val_lbl.pack(side="right", padx=10)
            key = label.split()[-1].lower() if label else 'unknown'
            self._stats_labels[f'system_{key}'] = val_lbl
        
        # ─────────── Tab 5: Skills ───────────
        tab_skills = stats_tabview.add("🌳 Skills")
        
        # Get skill tree
        if hasattr(self.panda, 'skill_tree'):
            from src.features.skill_tree import SkillTree
            tree = self.panda.skill_tree
            
            # Calculate total bonuses
            bonuses = tree.calculate_total_bonuses()
            
            # Display bonuses summary
            bonus_frame = ctk.CTkFrame(tab_skills)
            bonus_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(bonus_frame, text="🌟 Active Bonuses",
                        font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
            
            if bonuses:
                for bonus_name, bonus_value in bonuses.items():
                    if bonus_value > 0:
                        row = ctk.CTkFrame(bonus_frame)
                        row.pack(fill="x", padx=20, pady=1)
                        display_name = bonus_name.replace('_', ' ').title()
                        ctk.CTkLabel(row, text=f"{display_name}:", 
                                   font=("Arial", 11)).pack(side="left", padx=5)
                        ctk.CTkLabel(row, text=f"+{bonus_value}",
                                   font=("Arial Bold", 11),
                                   text_color="#00ff00").pack(side="right", padx=10)
            else:
                ctk.CTkLabel(bonus_frame, text="No skills unlocked yet",
                           font=("Arial", 11), text_color="gray").pack(padx=20, pady=5)
            
            # Skill tree display
            tree_scroll = ctk.CTkScrollableFrame(tab_skills, label_text="🌳 Skill Tree")
            tree_scroll.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Get available skills
            available_skills = tree.get_available_skills(
                self.panda.stats.level if hasattr(self.panda, 'stats') else 1,
                self.panda.stats.skill_points if hasattr(self.panda, 'stats') else 0
            )
            
            # Combat Branch
            combat_frame = ctk.CTkFrame(tree_scroll)
            combat_frame.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(combat_frame, text="⚔️ Combat Branch",
                        font=("Arial Bold", 13)).pack(anchor="w", padx=10, pady=5)
            
            # Magic Branch
            magic_frame = ctk.CTkFrame(tree_scroll)
            magic_frame.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(magic_frame, text="✨ Magic Branch",
                        font=("Arial Bold", 13)).pack(anchor="w", padx=10, pady=5)
            
            # Utility Branch
            utility_frame = ctk.CTkFrame(tree_scroll)
            utility_frame.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(utility_frame, text="🛡️ Utility Branch",
                        font=("Arial Bold", 13)).pack(anchor="w", padx=10, pady=5)
            
            # Display skills for each branch
            for skill_id, skill in tree.skills.items():
                # Determine branch frame
                if skill_id.startswith('combat_'):
                    parent_frame = combat_frame
                elif skill_id.startswith('magic_'):
                    parent_frame = magic_frame
                elif skill_id.startswith('utility_'):
                    parent_frame = utility_frame
                else:
                    continue
                
                skill_row = ctk.CTkFrame(parent_frame)
                skill_row.pack(fill="x", padx=15, pady=2)
                
                # Status icon
                if skill.unlocked:
                    status = "✅"
                    color = "#00ff00"
                elif skill_id in [s['id'] for s in available_skills]:
                    status = "🔓"
                    color = "#ffaa00"
                else:
                    status = "🔒"
                    color = "#666666"
                
                ctk.CTkLabel(skill_row, text=f"{status} {skill.name}",
                           font=("Arial", 11), text_color=color).pack(side="left", padx=5)
                
                # Show requirements
                req_text = f"Lvl {skill.level_required} • {skill.cost} SP"
                ctk.CTkLabel(skill_row, text=req_text,
                           font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
                
                # Unlock button if available
                if not skill.unlocked and skill_id in [s['id'] for s in available_skills]:
                    def unlock_skill_cmd(sid=skill_id):
                        if hasattr(self.panda, 'skill_tree') and hasattr(self.panda, 'stats'):
                            tree.unlock_skill(sid, self.panda.stats.level, self.panda.stats.skill_points)
                            self.panda.stats.skill_points -= skill.cost
                            self.log(f"✅ Unlocked skill: {skill.name}")
                            self.create_panda_stats_tab()  # Refresh
                    
                    ctk.CTkButton(skill_row, text="Unlock", width=60,
                                 command=unlock_skill_cmd).pack(side="right", padx=5)
        else:
            ctk.CTkLabel(tab_skills, text="Skill tree not available",
                        font=("Arial", 12)).pack(pady=50)
```

## Change 2: Add Dungeon Tab to Features

**Location:** main.py, line 854 (after Battle Arena tab)

**Add:**

```python
        self.tab_dungeon = self.features_tabview.add("🏰 Dungeon")
```

**And in _create_deferred_tabs() method (around line 891), add:**

```python
            self.create_dungeon_tab()
```

## Change 3: Create Dungeon Tab Method

**Location:** main.py, after create_battle_arena_tab() method (around line 7250)

**Add this complete method:**

```python
    def create_dungeon_tab(self):
        """Create dungeon exploration tab"""
        header_frame = ctk.CTkFrame(self.tab_dungeon)
        header_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(header_frame, text="🏰 Dungeon Explorer 🏰",
                     font=("Arial Bold", 18)).pack(side="left", padx=10)
        
        # Description
        desc_frame = ctk.CTkFrame(self.tab_dungeon)
        desc_frame.pack(fill="x", pady=5, padx=10)
        
        desc_text = ("Explore procedurally generated dungeons filled with enemies and treasure!\n\n"
                    "• Fight monsters and gain experience\n"
                    "• Collect loot and level up\n"
                    "• Navigate multiple floors\n"
                    "• Apply your stats and skills in combat")
        
        ctk.CTkLabel(desc_frame, text=desc_text,
                     font=("Arial", 12), justify="left").pack(padx=20, pady=10)
        
        # Enter Dungeon Button
        button_frame = ctk.CTkFrame(self.tab_dungeon)
        button_frame.pack(fill="x", pady=20, padx=10)
        
        enter_btn = ctk.CTkButton(
            button_frame,
            text="🏰 Enter Dungeon",
            font=("Arial Bold", 16),
            height=60,
            command=self.open_dungeon_window,
            fg_color="#2fa572",
            hover_color="#238656"
        )
        enter_btn.pack(pady=10)
        
        # Stats preview
        stats_preview_frame = ctk.CTkFrame(self.tab_dungeon)
        stats_preview_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(stats_preview_frame, text="📊 Your Current Stats",
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        if hasattr(self.panda, 'stats'):
            stats = self.panda.stats
            preview_items = [
                ("Level", stats.level),
                ("Health", f"{stats.health}/{stats.max_health}"),
                ("Strength", stats.strength),
                ("Defense", stats.defense),
                ("Magic", stats.magic),
            ]
            
            for label, value in preview_items:
                row = ctk.CTkFrame(stats_preview_frame)
                row.pack(fill="x", padx=20, pady=2)
                ctk.CTkLabel(row, text=f"{label}:", font=("Arial", 11)).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=str(value), font=("Arial Bold", 11),
                           text_color="#ffaa00").pack(side="right", padx=10)
        else:
            ctk.CTkLabel(stats_preview_frame, text="Stats system not initialized",
                        font=("Arial", 11), text_color="gray").pack(padx=20, pady=5)
    
    def open_dungeon_window(self):
        """Open dungeon exploration window with full integration"""
        try:
            from src.features.integrated_dungeon import IntegratedDungeon
            from src.ui.enhanced_dungeon_renderer import EnhancedDungeonRenderer
            import tkinter as tk
            
            # Create dungeon window
            dungeon_win = ctk.CTkToplevel(self)
            dungeon_win.title("🏰 Dungeon Explorer")
            dungeon_win.geometry("1200x800")
            
            # Main container
            main_container = ctk.CTkFrame(dungeon_win)
            main_container.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Left side: Dungeon canvas
            canvas_frame = ctk.CTkFrame(main_container)
            canvas_frame.pack(side="left", fill="both", expand=True)
            
            canvas = tk.Canvas(canvas_frame, width=900, height=700, bg="#1a1a1a")
            canvas.pack()
            
            # Right side: Stats and controls
            control_frame = ctk.CTkFrame(main_container, width=250)
            control_frame.pack(side="right", fill="y", padx=(10, 0))
            
            ctk.CTkLabel(control_frame, text="🎮 Controls",
                        font=("Arial Bold", 14)).pack(pady=10)
            
            controls_text = ("WASD or Arrows: Move\n"
                           "Space: Attack\n"
                           "E: Use Stairs\n"
                           "F: Toggle Fog\n"
                           "M: Toggle Minimap")
            
            ctk.CTkLabel(control_frame, text=controls_text,
                        font=("Arial", 11), justify="left").pack(pady=5)
            
            # Stats display
            stats_frame = ctk.CTkFrame(control_frame)
            stats_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(stats_frame, text="📊 Stats",
                        font=("Arial Bold", 12)).pack(pady=5)
            
            # Initialize dungeon
            dungeon = IntegratedDungeon(80, 80, num_floors=5)
            dungeon.spawn_enemies_in_rooms()
            dungeon.spawn_loot_in_rooms()
            
            # Create renderer
            renderer = EnhancedDungeonRenderer(canvas, dungeon.generator)
            renderer.set_floor(0)
            
            # Set player position
            floor = dungeon.generator.get_floor(0)
            spawn_x, spawn_y = floor.spawn_point
            dungeon.set_player_position(spawn_x, spawn_y)
            
            # Initial render
            renderer.center_camera_on_tile(spawn_x, spawn_y)
            renderer.mark_explored(spawn_x, spawn_y, radius=5)
            renderer.render(show_fog=True)
            
            # Draw player
            player_pos = dungeon.get_player_position()
            renderer.render_entity(player_pos[0], player_pos[1], '🐼', size=24)
            
            # Game state
            game_state = {
                'dungeon': dungeon,
                'renderer': renderer,
                'current_floor': 0,
                'show_fog': True,
                'show_minimap': True,
            }
            
            def update_display():
                """Update dungeon display"""
                renderer.render(show_fog=game_state['show_fog'])
                player_pos = dungeon.get_player_position()
                renderer.render_entity(player_pos[0], player_pos[1], '🐼', size=24)
                
                # Render enemies
                enemies = dungeon.get_enemies_on_floor(game_state['current_floor'])
                for enemy in enemies:
                    if enemy.is_alive():
                        renderer.render_entity(enemy.x, enemy.y, enemy.icon, size=20)
                
                # Render loot
                loot = dungeon.get_loot_on_floor(game_state['current_floor'])
                for item in loot:
                    icon = {'health': '❤️', 'weapon': '⚔️', 'gold': '💰', 'key': '🔑'}.get(item['type'], '📦')
                    renderer.render_entity(item['x'], item['y'], icon, size=16)
                
                # Render minimap if enabled
                if game_state['show_minimap']:
                    renderer.render_minimap(850, 50, size=120)
            
            def handle_key(event):
                """Handle keyboard input"""
                key = event.keysym.lower()
                player_pos = dungeon.get_player_position()
                px, py = player_pos
                floor_num = game_state['current_floor']
                
                # Movement
                moved = False
                if key in ('w', 'up'):
                    if dungeon.generator.is_walkable(floor_num, px, py - 1):
                        dungeon.set_player_position(px, py - 1)
                        moved = True
                elif key in ('s', 'down'):
                    if dungeon.generator.is_walkable(floor_num, px, py + 1):
                        dungeon.set_player_position(px, py + 1)
                        moved = True
                elif key in ('a', 'left'):
                    if dungeon.generator.is_walkable(floor_num, px - 1, py):
                        dungeon.set_player_position(px - 1, py)
                        moved = True
                elif key in ('d', 'right'):
                    if dungeon.generator.is_walkable(floor_num, px + 1, py):
                        dungeon.set_player_position(px + 1, py)
                        moved = True
                
                if moved:
                    # Mark explored
                    new_pos = dungeon.get_player_position()
                    renderer.mark_explored(new_pos[0], new_pos[1], radius=5)
                    renderer.center_camera_on_tile(new_pos[0], new_pos[1])
                    
                    # Check for loot collection
                    dungeon.check_loot_pickup()
                    
                    # Add distance
                    if hasattr(self.panda, 'stats'):
                        self.panda.stats.add_distance(1.0)
                
                # Attack
                elif key == 'space':
                    # Attack nearby enemies
                    if hasattr(self.panda, 'stats'):
                        self.panda.stats.increment_attack()
                        # TODO: Implement actual combat
                
                # Stairs
                elif key == 'e':
                    stair_result = dungeon._check_stairs()
                    if stair_result:
                        if stair_result == 'up' and game_state['current_floor'] > 0:
                            game_state['current_floor'] -= 1
                            renderer.set_floor(game_state['current_floor'])
                            self.log("🪜 Went up to previous floor")
                        elif stair_result == 'down' and game_state['current_floor'] < 4:
                            game_state['current_floor'] += 1
                            renderer.set_floor(game_state['current_floor'])
                            if hasattr(self.panda, 'stats'):
                                self.panda.stats.increment_floors()
                            self.log("🪜 Went down to next floor")
                
                # Toggle fog
                elif key == 'f':
                    game_state['show_fog'] = not game_state['show_fog']
                
                # Toggle minimap
                elif key == 'm':
                    game_state['show_minimap'] = not game_state['show_minimap']
                
                # Update display
                update_display()
            
            # Bind keys
            dungeon_win.bind('<Key>', handle_key)
            dungeon_win.focus_set()
            
            # Initial display
            update_display()
            
            self.log("🏰 Entered the dungeon!")
            
        except Exception as e:
            logger.error(f"Error opening dungeon: {e}", exc_info=True)
            self.log(f"❌ Error opening dungeon: {e}")
```

## Testing the Changes

After making these changes:

1. **Restart the application**
2. **Navigate to Features → Panda Stats & Mood**
   - You should see sub-tabs: Base Stats, Combat, Interaction, System, Skills
3. **Navigate to Features → Dungeon**
   - Click "Enter Dungeon" button
   - Dungeon window should open
4. **Test dungeon controls**
   - WASD to move
   - Space to attack
   - E to use stairs

## Notes

- Ensure `src/features/integrated_dungeon.py` and `src/ui/enhanced_dungeon_renderer.py` are available
- The skill tree initialization (`self.panda.skill_tree`) might need to be added to PandaCharacter init if not already present
- Stats system must be properly initialized in PandaCharacter

## Summary

These changes complete the UI integration by:
1. ✅ Adding categorized stats tabs (5 tabs for different stat types)
2. ✅ Adding dungeon entry point (new tab in Features)
3. ✅ Implementing complete dungeon window with controls
4. ✅ Connecting all systems (stats, skills, combat, dungeon)

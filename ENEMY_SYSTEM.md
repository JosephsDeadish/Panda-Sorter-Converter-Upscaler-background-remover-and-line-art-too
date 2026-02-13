# Enemy System Documentation

## Overview

The Enemy System provides animated enemy widgets that autonomously move toward the panda to attack, with pathfinding and collision detection. Enemies are rendered in their own transparent Toplevel windows and move independently across the screen.

## Architecture

### Core Components

1. **Enemy** (`src/features/enemy_system.py`)
   - Enemy instances with stats, behavior, and combat mechanics
   - 6 enemy types: Slime, Goblin, Skeleton, Wolf, Orc, Dragon
   - Level scaling for stats and XP rewards
   - AI behaviors: Passive, Aggressive, Defensive, Tactical, Berserker

2. **EnemyWidget** (`src/ui/enemy_widget.py`)
   - Visual representation of enemies
   - Autonomous movement toward panda
   - Attack range detection and triggering
   - Health bar and level display
   - Death animations and callbacks

3. **EnemyManager** (`src/features/enemy_manager.py`)
   - Manages multiple enemy instances
   - Auto-spawning system
   - Wave spawning
   - Statistics tracking

## Features

### Autonomous Movement
- Enemies move directly toward the panda in a straight line
- Movement speed varies by enemy type:
  - **Slime**: 70% speed (slow)
  - **Goblin**: 100% speed (normal)
  - **Skeleton**: 90% speed
  - **Wolf**: 150% speed (fast)
  - **Orc**: 80% speed
  - **Dragon**: 120% speed

### Pathfinding
- Simple direct pathfinding (moves in straight line to target)
- Collision detection with window bounds
- Stops when reaching attack range (80 pixels)

### Attack System
- Attacks trigger when enemy reaches panda (within 80px)
- 2-second cooldown between attacks
- Callback system for damage integration
- Visual attack indication (stops moving)

### Visual Features
- Emoji-based enemy rendering with bounce animation
- Health bar (red/green)
- Level indicator
- Transparent background (Windows) or blended (other platforms)
- Always-on-top rendering

## Usage

### Basic Spawning

```python
from src.features.enemy_system import EnemyCollection
from src.features.enemy_manager import EnemyManager
from src.ui.panda_widget import PandaWidget

# Initialize
enemy_collection = EnemyCollection()
panda_widget = PandaWidget(parent, panda_character)

# Create manager
enemy_manager = EnemyManager(
    parent,
    panda_widget,
    enemy_collection,
    on_panda_attacked=handle_attack
)

# Spawn enemies
enemy_manager.spawn_enemy('goblin', level=5)
enemy_manager.spawn_wave(3)  # Spawn 3 random enemies

# Enable auto-spawning
enemy_manager.enable_auto_spawn(True)
enemy_manager.set_spawn_cooldown(5.0)  # 5 seconds between spawns
enemy_manager.set_max_enemies(10)

# Update loop (call periodically)
def update():
    enemy_manager.update()
    root.after(100, update)
```

### Individual Enemy Widget

```python
from src.ui.enemy_widget import EnemyWidget

# Create enemy instance
enemy = enemy_collection.create_enemy('wolf', level=3)

# Create widget
enemy_widget = EnemyWidget(
    parent,
    enemy,
    panda_widget,
    on_attack=lambda e: print(f"{e.name} attacks!"),
    on_death=lambda e: print(f"{e.name} defeated!")
)

# Damage enemy
enemy_widget.take_damage(20)
```

### Attack Callback

```python
def handle_panda_attacked(enemy):
    """Called when enemy attacks panda."""
    damage, is_crit = enemy.attack(panda_defense)
    panda.take_damage(damage)
    print(f"Panda took {damage} damage!")
```

## Enemy Types

### Slime 🟢
- **Level 1 Stats**: 30 HP, 5 ATK, 2 DEF
- **Behavior**: Passive (only attacks when provoked)
- **Speed**: Slow (0.7x)
- **Loot**: Slime Gel (50% chance)

### Goblin 👺
- **Level 1 Stats**: 50 HP, 10 ATK, 5 DEF
- **Behavior**: Aggressive (attacks on sight)
- **Speed**: Normal (1.0x)
- **Loot**: Goblin Ear (30%), Gold Coin (80%)

### Skeleton 💀
- **Level 1 Stats**: 60 HP, 12 ATK, 10 DEF
- **Behavior**: Defensive (attacks when approached)
- **Speed**: Slow (0.9x)
- **Loot**: Bone (70%), Rusty Sword (20%)

### Wolf 🐺
- **Level 1 Stats**: 55 HP, 15 ATK, 6 DEF, 15% Crit, 10% Evasion
- **Behavior**: Aggressive
- **Speed**: Fast (1.5x)
- **Loot**: Wolf Fur (60%), Wolf Fang (40%)

### Orc 👹
- **Level 1 Stats**: 100 HP, 20 ATK, 15 DEF
- **Behavior**: Tactical (uses abilities strategically)
- **Speed**: Slow (0.8x)
- **Abilities**: Power Strike, War Cry
- **Loot**: Orc Tusk (50%), Iron Ore (60%), Health Potion (30%)

### Dragon 🐉
- **Level 1 Stats**: 500 HP, 50 ATK, 30 DEF, 200 MP, 60 MAG, 15% Crit
- **Behavior**: Tactical (boss enemy)
- **Speed**: Fast (1.2x)
- **Abilities**: Fire Breath, Tail Swipe, Roar
- **Loot**: Dragon Scale (90%), Dragon Claw (70%), Legendary Gem (30%)

## Configuration

### Movement Constants (EnemyWidget)
- `MOVEMENT_INTERVAL`: 50ms (20 FPS movement updates)
- `MOVE_SPEED_BASE`: 2.0 pixels per frame
- `ATTACK_RANGE`: 80 pixels
- `COLLISION_RADIUS`: 40 pixels

### Animation Constants
- `ANIMATION_INTERVAL`: 100ms (10 FPS animations)
- `BOUNCE_AMPLITUDE`: 5 pixels

### Manager Settings
- `max_enemies`: 5 (default)
- `spawn_cooldown`: 5.0 seconds
- `auto_spawn`: False (default)

## Testing

Run the test suite:
```bash
python test_enemy_widget.py
```

Run the demo application:
```bash
python demo_enemy_system.py
```

## Integration Example

```python
# In your main application
from src.features.enemy_manager import EnemyManager

class GameApp:
    def __init__(self):
        # ... setup code ...
        
        # Create enemy manager
        self.enemy_manager = EnemyManager(
            self.main_frame,
            self.panda_widget,
            self.enemy_collection,
            on_panda_attacked=self.handle_attack
        )
        
        # Start with some enemies
        self.enemy_manager.spawn_wave(3, level=1)
        
        # Start update loop
        self.update_enemies()
    
    def update_enemies(self):
        """Update enemies periodically."""
        self.enemy_manager.update()
        self.root.after(100, self.update_enemies)
    
    def handle_attack(self, enemy):
        """Handle enemy attacking panda."""
        damage, is_crit = enemy.attack(self.panda.defense)
        self.panda.take_damage(damage)
        
        if is_crit:
            print(f"CRITICAL HIT! {damage} damage!")
```

## Performance Notes

- Each enemy runs in its own Toplevel window for smooth independent movement
- Movement updates run at 20 FPS (50ms intervals)
- Recommended max 10-15 simultaneous enemies for smooth performance
- Transparent background on Windows uses colorkey technique
- Cleanup is automatic when enemies die or are cleared

## Future Enhancements

Potential improvements:
- A* pathfinding around obstacles
- Formation movement for groups
- Advanced AI behaviors (flanking, retreating)
- Area-of-effect attacks
- Enemy collision with each other
- Patrol routes for idle enemies
- Special abilities with visual effects

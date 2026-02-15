# Visual Integration Guide

## Overview

This guide explains how to integrate the combat and damage systems with visual rendering in the panda game.

## What's Been Implemented

### Core Systems (Complete)
1. **Damage System** - 12-stage damage tracking for 12 categories
2. **Projectile System** - Full physics with 8 projectile types
3. **Visual Effects Renderer** - Rendering helpers for all effects
4. **Combat Demo** - Interactive demonstration

### Integration Points

The systems are designed to plug into existing enemy and panda widgets through their canvas rendering.

## Quick Start

### 1. Basic Damage Rendering

```python
from src.features.damage_system import DamageTracker, DamageCategory, LimbType
from src.ui.visual_effects_renderer import VisualEffectsRenderer

# In your widget class
def __init__(self):
    self.damage_tracker = DamageTracker()
    self.vfx_renderer = VisualEffectsRenderer()

def take_damage(self, amount, category, limb):
    """Handle taking damage."""
    result = self.damage_tracker.apply_damage(limb, category, amount)
    if result['severed']:
        self._handle_limb_severed(limb)
    self._redraw()

def _draw(self):
    """Draw the widget with damage effects."""
    # Draw base character
    self._draw_character()
    
    # Draw damage effects
    wounds = self.damage_tracker.get_all_wounds()
    self.vfx_renderer.render_wounds(self.canvas, wounds, 
                                    self.center_x, self.center_y)
    
    # Draw stuck projectiles
    projectiles = self.damage_tracker.get_stuck_projectiles()
    self.vfx_renderer.render_stuck_projectiles(self.canvas, projectiles,
                                               self.center_x, self.center_y)
```

### 2. Projectile Integration

```python
from src.features.projectile_system import ProjectileManager, ProjectileType

# In your game/scene class
def __init__(self):
    self.projectile_manager = ProjectileManager()
    self.vfx_renderer = VisualEffectsRenderer()

def fire_weapon(self, weapon):
    """Fire a weapon (bow/gun)."""
    if weapon.type == "bow":
        self.projectile_manager.spawn_projectile(
            x=player.x, y=player.y,
            angle=aim_angle,
            projectile_type=ProjectileType.ARROW,
            damage=weapon.damage,
            owner=player,
            on_hit=self._on_projectile_hit
        )

def _on_projectile_hit(self, target, projectile, limb):
    """Handle projectile hitting target."""
    if projectile.projectile_type == ProjectileType.ARROW:
        # Arrow sticks in body
        target.damage_tracker.add_stuck_projectile(
            "arrow", 
            (projectile.x - target.x, projectile.y - target.y),
            limb
        )
    
    # Apply damage
    target.damage_tracker.apply_damage(limb, DamageCategory.ARROW, projectile.damage)

def update(self, delta_time):
    """Update game state."""
    # Update projectile physics
    self.projectile_manager.update(delta_time)
    
    # Check collisions
    self.projectile_manager.check_collisions(
        targets=self.enemies,
        get_position_func=lambda e: e.get_position(),
        get_radius_func=lambda e: 40,
        on_hit_func=self._on_projectile_hit
    )
    
    # Render projectiles
    for proj in self.projectile_manager.get_active_projectiles():
        self.vfx_renderer.render_projectile(self.canvas, proj)
```

### 3. Enemy Widget Integration

To add damage effects to `EnemyWidget`:

```python
# In src/ui/enemy_widget.py

from src.features.damage_system import DamageTracker, DamageCategory, LimbType
from src.ui.visual_effects_renderer import VisualEffectsRenderer

class EnemyWidget:
    def __init__(self, ...):
        # ... existing init ...
        self.damage_tracker = DamageTracker()
        self.vfx_renderer = VisualEffectsRenderer()
    
    def take_damage(self, damage, category=DamageCategory.PHYSICAL):
        """Enemy takes damage."""
        # Determine which limb was hit (simple: random or based on position)
        import random
        limbs = list(LimbType)
        limb = random.choice(limbs)
        
        result = self.damage_tracker.apply_damage(limb, category, damage)
        
        # Check for death
        if self.damage_tracker.is_decapitated():
            self._on_death()
        elif not self.enemy.is_alive():
            self._on_death()
        
        return result
    
    def _draw_enemy(self):
        """Draw enemy with damage effects using QGraphicsScene."""
        scene = self.enemy_scene
        scene.clear()
        
        # Draw base enemy
        # ... existing drawing code ...
        
        # Draw damage effects using QGraphicsScene methods
        # Note: Use standard methods (no _gl suffix) for QGraphicsView rendering
        cx = ENEMY_VIEW_W // 2
        cy = ENEMY_VIEW_H // 2
        
        wounds = self.damage_tracker.get_all_wounds()
        self.vfx_renderer.render_wounds(scene, wounds, cx, cy, scale=0.5)
        
        projectiles = self.damage_tracker.get_stuck_projectiles()
        self.vfx_renderer.render_stuck_projectiles(scene, projectiles, cx, cy, scale=0.5)
        
        # Draw bleeding effect if bleeding
        if self.damage_tracker.total_bleeding_rate > 0:
            self.vfx_renderer.render_bleeding_effect(
                scene, cx, cy + 30,
                self.damage_tracker.total_bleeding_rate,
                self.animation_frame
            )
```

### 4. Panda Widget Integration

To add damage effects to `PandaWidget`:

```python
# In src/ui/panda_widget.py

from src.features.damage_system import DamageTracker, DamageCategory, LimbType
from src.ui.visual_effects_renderer import VisualEffectsRenderer

class PandaWidget:
    def __init__(self, ...):
        # ... existing init ...
        self.damage_tracker = DamageTracker()
        self.vfx_renderer = VisualEffectsRenderer()
    
    def take_damage(self, damage, category, limb=None):
        """Panda takes damage."""
        if limb is None:
            # Random limb if not specified
            import random
            limb = random.choice(list(LimbType))
        
        result = self.damage_tracker.apply_damage(limb, category, damage)
        
        # Play damage reaction animation
        if result['stage'] > 6:
            self.play_animation_once('hurt')
        
        # Apply movement penalty
        move_penalty = self.damage_tracker.get_movement_penalty()
        self.speed_multiplier = 1.0 - move_penalty
        
        return result
    
    def paintGL(self):
        """Draw panda with damage effects in OpenGL."""
        # ... existing panda OpenGL rendering code ...
        
        # Draw damage effects as 2D overlay using OpenGL methods
        # Note: Use _gl suffix methods for OpenGL widget rendering
        cx = PANDA_WIDTH // 2
        cy = PANDA_HEIGHT // 2
        
        wounds = self.damage_tracker.get_all_wounds()
        self.vfx_renderer.render_wounds_gl(wounds, cx, cy)
        
        projectiles = self.damage_tracker.get_stuck_projectiles()
        self.vfx_renderer.render_stuck_projectiles_gl(projectiles, cx, cy)
```

## Weapon Integration

### Connecting Weapon Types to Damage Categories

```python
from src.features.weapon_system import WeaponType
from src.features.damage_system import DamageCategory

# Map weapon types to damage categories
WEAPON_DAMAGE_MAP = {
    'sword': DamageCategory.SHARP,
    'axe': DamageCategory.SHARP,
    'knife': DamageCategory.SHARP,
    'hammer': DamageCategory.BLUNT,
    'club': DamageCategory.BLUNT,
    'mace': DamageCategory.BLUNT,
    'bow': DamageCategory.ARROW,
    'crossbow': DamageCategory.ARROW,
    'gun': DamageCategory.BULLET,
}

def apply_weapon_damage(weapon, target, is_critical=False):
    """Apply damage from weapon hit."""
    damage_category = WEAPON_DAMAGE_MAP.get(weapon.id, DamageCategory.SHARP)
    
    # Determine hit limb (based on attack direction, target position, etc.)
    limb = determine_hit_limb(target)
    
    result = target.damage_tracker.apply_damage(
        limb=limb,
        category=damage_category,
        amount=weapon.stats.damage,
        can_sever=is_critical  # Critical hits can sever
    )
    
    return result
```

### Projectile Weapons

```python
def fire_bow(bow, angle, owner):
    """Fire an arrow from bow."""
    return projectile_manager.spawn_projectile(
        x=owner.x, y=owner.y,
        angle=angle,
        projectile_type=ProjectileType.ARROW,
        damage=bow.stats.damage,
        physics=ProjectilePhysics(
            speed=800,  # Fast arrow
            gravity=300,  # Affected by gravity
            air_resistance=0.99
        ),
        owner=owner
    )

def fire_gun(gun, angle, owner):
    """Fire a bullet from gun."""
    return projectile_manager.spawn_projectile(
        x=owner.x, y=owner.y,
        angle=angle,
        projectile_type=ProjectileType.BULLET,
        damage=gun.stats.damage,
        physics=ProjectilePhysics(
            speed=2000,  # Very fast bullet
            gravity=50,  # Minimal gravity
            air_resistance=0.99
        ),
        owner=owner
    )
```

## Animation Enhancement

### Damage Reactions

```python
def play_damage_reaction(character, damage_category, severity):
    """Play appropriate damage reaction animation."""
    if damage_category == DamageCategory.SHARP:
        if severity > 8:
            character.play_animation_once('critical_hit')
        else:
            character.play_animation_once('hit')
    elif damage_category == DamageCategory.BLUNT:
        character.play_animation_once('stagger')
    elif damage_category == DamageCategory.FIRE:
        character.play_animation_once('burning')
```

### Limb Severing Animation

```python
def handle_limb_severed(character, limb):
    """Handle limb severing event."""
    if limb == LimbType.HEAD:
        # Decapitation - instant death
        character.play_animation_once('decapitated')
        character.die()
    elif limb in [LimbType.LEFT_LEG, LimbType.RIGHT_LEG]:
        # Severed leg - fall down
        character.play_animation_once('leg_severed')
        character.movement_enabled = False
    elif limb in [LimbType.LEFT_ARM, LimbType.RIGHT_ARM]:
        # Severed arm - can't use two-handed weapons
        character.play_animation_once('arm_severed')
        character.can_use_two_handed = False
```

## Performance Optimization

### Culling Wounds

```python
def render_wounds_optimized(canvas, wounds, max_wounds=50):
    """Render wounds with culling for performance."""
    # Only render most recent/severe wounds
    if len(wounds) > max_wounds:
        # Sort by severity and creation time
        sorted_wounds = sorted(wounds, 
                              key=lambda w: (w.severity, w.creation_time),
                              reverse=True)
        wounds = sorted_wounds[:max_wounds]
    
    renderer.render_wounds(canvas, wounds, cx, cy)
```

### Projectile Pooling

```python
class OptimizedProjectileManager(ProjectileManager):
    """Projectile manager with pooling."""
    
    def __init__(self, max_active=100):
        super().__init__()
        self.max_active = max_active
    
    def spawn_projectile(self, *args, **kwargs):
        """Spawn with limit."""
        if len(self.projectiles) >= self.max_active:
            # Remove oldest inactive
            self.projectiles = [p for p in self.projectiles if p.active][-self.max_active:]
        
        return super().spawn_projectile(*args, **kwargs)
```

## Testing

### Unit Tests

```python
def test_damage_integration():
    """Test damage system integration."""
    tracker = DamageTracker()
    renderer = VisualEffectsRenderer()
    
    # Apply damage
    tracker.apply_damage(LimbType.TORSO, DamageCategory.SHARP, 50)
    
    # Verify renderable data
    wounds = tracker.get_all_wounds()
    assert len(wounds) > 0
    
    # Mock scene for rendering test
    from PyQt6.QtWidgets import QGraphicsScene
    scene = QGraphicsScene()
    
    # Should not crash
    renderer.render_wounds(scene, wounds, 100, 100)
```

## Demo Application

Run the interactive demo:

```bash
python demo_combat_visual.py
```

This shows:
- Damage application and accumulation
- Wound rendering (gashes, bruises, burns)
- Projectile physics and collision
- Stuck projectiles (arrows in body)
- Bleeding animation
- Real-time penalty calculation

## Future Enhancements

### Advanced Features

1. **Wound Healing**
   ```python
   def heal_damage(tracker, amount):
       """Heal wounds gradually."""
       for limb_damages in tracker.limb_damage.values():
           for damage in limb_damages:
               if damage.stage > 0:
                   damage.stage = max(0, damage.stage - 1)
   ```

2. **Scar System**
   ```python
   def convert_to_scar(wound):
       """Convert healed wound to permanent scar."""
       return VisualWound(
           wound_type="scar",
           position=wound.position,
           size=wound.size * 0.5,
           severity=1,
           color="#FFEBCD",  # Lighter color
           limb=wound.limb
       )
   ```

3. **Blood Splatter**
   ```python
   def create_blood_splatter(x, y, velocity):
       """Create blood particle effect."""
       particles = []
       for i in range(10):
           angle = random.uniform(0, 2*math.pi)
           speed = random.uniform(50, 150)
           particles.append(BloodParticle(x, y, angle, speed))
       return particles
   ```

## Troubleshooting

### Wounds Not Appearing
- Check that `render_wounds()` is called after character drawing
- Verify offset positions are correct
- Ensure wounds list is not empty

### Projectiles Not Colliding
- Verify `check_collisions()` is called each frame
- Check collision radius values
- Ensure target positions are in world coordinates

### Performance Issues
- Limit active projectiles to 50-100
- Cull old wounds (keep most recent 50)
- Use lower update frequency for effects (30 FPS instead of 60)

## Conclusion

The combat system foundation is complete and ready for visual integration. All data structures, rendering helpers, and integration points are documented and tested. The remaining work involves connecting these systems to the existing widget rendering code.

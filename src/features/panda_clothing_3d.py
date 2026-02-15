"""
Advanced 3D Clothing System for Panda

Provides mesh-based clothing, sprite accessories, physics simulation,
and skeletal attachment for the interactive panda.

Features:
    - 3D mesh clothing (shirts, pants, jackets)
    - 2D sprite accessories (bow, scarf, glasses)
    - Physics simulation (fluttering, bouncing)
    - Skeletal bone hierarchy
    - LOD (Level of Detail) system
    - Dynamic animations (tilt, squash, stretch)
"""

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    import numpy as np
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False

import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional


class BoneType(Enum):
    """Panda skeleton bones."""
    ROOT = "root"
    TORSO = "torso"
    HEAD = "head"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"


class ClothingType(Enum):
    """Types of clothing."""
    SHIRT = "shirt"
    PANTS = "pants"
    JACKET = "jacket"
    HAT = "hat"
    SHOES = "shoes"


class AccessoryType(Enum):
    """Types of sprite accessories."""
    BOW = "bow"
    SCARF = "scarf"
    GLASSES = "glasses"
    EARRINGS = "earrings"
    NECKLACE = "necklace"


class LODLevel(Enum):
    """Level of Detail settings."""
    HIGH = 3  # Full detail, all physics
    MEDIUM = 2  # Simplified meshes, limited physics
    LOW = 1  # Basic shapes, no physics
    MINIMAL = 0  # Flat colors only


@dataclass
class Bone:
    """Skeleton bone with transformation."""
    name: str
    bone_type: BoneType
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float]  # Euler angles
    scale: Tuple[float, float, float]
    parent: Optional['Bone'] = None
    children: List['Bone'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    def get_world_transform(self):
        """Get world space transformation matrix."""
        # Build local transform
        local_transform = self._build_transform_matrix()
        
        # Apply parent transform if exists
        if self.parent:
            parent_transform = self.parent.get_world_transform()
            return np.dot(parent_transform, local_transform)
        
        return local_transform
    
    def _build_transform_matrix(self):
        """Build 4x4 transformation matrix."""
        # Translation
        T = np.eye(4)
        T[0:3, 3] = self.position
        
        # Rotation (simplified, would use quaternions in production)
        Rx = self._rotation_matrix_x(self.rotation[0])
        Ry = self._rotation_matrix_y(self.rotation[1])
        Rz = self._rotation_matrix_z(self.rotation[2])
        R = np.dot(Rx, np.dot(Ry, Rz))
        
        # Scale
        S = np.eye(4)
        S[0, 0] = self.scale[0]
        S[1, 1] = self.scale[1]
        S[2, 2] = self.scale[2]
        
        # Combine: T * R * S
        return np.dot(T, np.dot(R, S))
    
    def _rotation_matrix_x(self, angle):
        """X-axis rotation matrix."""
        c, s = math.cos(angle), math.sin(angle)
        return np.array([
            [1, 0, 0, 0],
            [0, c, -s, 0],
            [0, s, c, 0],
            [0, 0, 0, 1]
        ])
    
    def _rotation_matrix_y(self, angle):
        """Y-axis rotation matrix."""
        c, s = math.cos(angle), math.sin(angle)
        return np.array([
            [c, 0, s, 0],
            [0, 1, 0, 0],
            [-s, 0, c, 0],
            [0, 0, 0, 1]
        ])
    
    def _rotation_matrix_z(self, angle):
        """Z-axis rotation matrix."""
        c, s = math.cos(angle), math.sin(angle)
        return np.array([
            [c, -s, 0, 0],
            [s, c, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])


@dataclass
class ClothingMesh:
    """3D mesh clothing item."""
    name: str
    clothing_type: ClothingType
    attached_bone: BoneType
    vertices: np.ndarray  # Nx3 array
    indices: np.ndarray  # Triangles
    normals: np.ndarray  # Normal vectors
    tex_coords: Optional[np.ndarray] = None
    color: Tuple[float, float, float] = (0.5, 0.5, 1.0)
    
    # Animation properties
    squash_factor: float = 1.0
    rotation_offset: Tuple[float, float, float] = (0, 0, 0)
    
    def render(self, bone_transform, lod_level=LODLevel.HIGH):
        """Render the mesh clothing."""
        if not OPENGL_AVAILABLE:
            return
        
        glPushMatrix()
        
        # Apply bone transformation
        glMultMatrixf(bone_transform.T.flatten())
        
        # Apply animation offsets
        glRotatef(self.rotation_offset[0], 1, 0, 0)
        glRotatef(self.rotation_offset[1], 0, 1, 0)
        glRotatef(self.rotation_offset[2], 0, 0, 1)
        
        # Apply squash factor
        glScalef(1.0, self.squash_factor, 1.0)
        
        # Set material color
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (*self.color, 1.0))
        
        # Render based on LOD
        if lod_level == LODLevel.HIGH or lod_level == LODLevel.MEDIUM:
            self._render_mesh()
        else:
            self._render_simplified()
        
        glPopMatrix()
    
    def _render_mesh(self):
        """Render full mesh."""
        glBegin(GL_TRIANGLES)
        for i in range(0, len(self.indices), 3):
            # Get triangle indices
            i1, i2, i3 = self.indices[i:i+3]
            
            # Normal
            if self.normals is not None:
                glNormal3fv(self.normals[i1])
            
            # Vertices
            glVertex3fv(self.vertices[i1])
            glVertex3fv(self.vertices[i2])
            glVertex3fv(self.vertices[i3])
        glEnd()
    
    def _render_simplified(self):
        """Render simplified version (cube/sphere)."""
        if self.clothing_type == ClothingType.SHIRT:
            # Simple cube for shirt
            self._draw_cube(0.3, 0.4, 0.2)
        elif self.clothing_type == ClothingType.PANTS:
            # Two cylinders for pants
            self._draw_cube(0.25, 0.4, 0.2)


    def _draw_cube(self, sx, sy, sz):
        """Draw a simple cube."""
        glBegin(GL_QUADS)
        # Front
        glVertex3f(-sx, -sy, sz)
        glVertex3f(sx, -sy, sz)
        glVertex3f(sx, sy, sz)
        glVertex3f(-sx, sy, sz)
        # Back
        glVertex3f(-sx, -sy, -sz)
        glVertex3f(-sx, sy, -sz)
        glVertex3f(sx, sy, -sz)
        glVertex3f(sx, -sy, -sz)
        # ... (other faces omitted for brevity)
        glEnd()


@dataclass
class SpriteAccessory:
    """2D sprite accessory with billboard rendering."""
    name: str
    accessory_type: AccessoryType
    attached_bone: BoneType
    offset: Tuple[float, float, float]
    size: float
    texture_id: Optional[int] = None
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    
    # Physics properties
    velocity: Tuple[float, float, float] = (0, 0, 0)
    angular_velocity: float = 0.0
    rotation: float = 0.0
    
    # Spring physics
    spring_strength: float = 0.5
    damping: float = 0.8
    
    def update_physics(self, delta_time, panda_velocity, wind_force=(0, 0, 0)):
        """Update physics simulation."""
        # Convert to mutable
        vx, vy, vz = self.velocity
        
        # Apply wind force (for scarves, bows)
        if self.accessory_type in [AccessoryType.SCARF, AccessoryType.BOW]:
            vx += wind_force[0] * delta_time
            vy += wind_force[1] * delta_time
            vz += wind_force[2] * delta_time
        
        # Spring force back to rest position
        spring_force = -self.spring_strength * np.array([vx, vy, vz])
        vx += spring_force[0] * delta_time
        vy += spring_force[1] * delta_time
        vz += spring_force[2] * delta_time
        
        # Damping
        vx *= self.damping
        vy *= self.damping
        vz *= self.damping
        
        # Update rotation (for hats bouncing)
        if self.accessory_type == AccessoryType.EARRINGS:
            self.angular_velocity += -0.1 * self.rotation * delta_time
            self.angular_velocity *= 0.95
            self.rotation += self.angular_velocity * delta_time
        
        self.velocity = (vx, vy, vz)
    
    def render(self, bone_transform, camera_matrix, lod_level=LODLevel.HIGH):
        """Render sprite as billboard."""
        if not OPENGL_AVAILABLE:
            return
        
        if lod_level == LODLevel.MINIMAL:
            return  # Skip accessories on minimal detail
        
        glPushMatrix()
        
        # Apply bone transformation
        glMultMatrixf(bone_transform.T.flatten())
        
        # Apply offset
        glTranslatef(*self.offset)
        
        # Add physics displacement
        glTranslatef(*self.velocity)
        
        # Billboard: face camera
        self._apply_billboard_rotation(camera_matrix)
        
        # Apply rotation (for physics)
        glRotatef(math.degrees(self.rotation), 0, 0, 1)
        
        # Render sprite quad
        self._render_sprite()
        
        glPopMatrix()
    
    def _apply_billboard_rotation(self, camera_matrix):
        """Make sprite face camera."""
        # Extract camera rotation and apply inverse
        # (Simplified - in production, extract from camera matrix)
        pass
    
    def _render_sprite(self):
        """Render sprite quad."""
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Set color
        glColor4f(*self.color, 1.0)
        
        # Draw quad
        s = self.size / 2
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-s, -s, 0)
        glTexCoord2f(1, 0); glVertex3f(s, -s, 0)
        glTexCoord2f(1, 1); glVertex3f(s, s, 0)
        glTexCoord2f(0, 1); glVertex3f(-s, s, 0)
        glEnd()
        
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)


class PandaSkeleton:
    """Panda skeleton with bone hierarchy."""
    
    def __init__(self):
        # Create bone hierarchy
        self.root = Bone(
            name="root",
            bone_type=BoneType.ROOT,
            position=(0, 0, 0),
            rotation=(0, 0, 0),
            scale=(1, 1, 1)
        )
        
        self.torso = Bone(
            name="torso",
            bone_type=BoneType.TORSO,
            position=(0, 0, 0),
            rotation=(0, 0, 0),
            scale=(1, 1, 1),
            parent=self.root
        )
        
        self.head = Bone(
            name="head",
            bone_type=BoneType.HEAD,
            position=(0, 0.4, 0),
            rotation=(0, 0, 0),
            scale=(1, 1, 1),
            parent=self.torso
        )
        
        self.left_arm = Bone(
            name="left_arm",
            bone_type=BoneType.LEFT_ARM,
            position=(-0.25, 0.05, 0),
            rotation=(0, 0, 0),
            scale=(1, 1, 1),
            parent=self.torso
        )
        
        self.right_arm = Bone(
            name="right_arm",
            bone_type=BoneType.RIGHT_ARM,
            position=(0.25, 0.05, 0),
            rotation=(0, 0, 0),
            scale=(1, 1, 1),
            parent=self.torso
        )
        
        self.left_leg = Bone(
            name="left_leg",
            bone_type=BoneType.LEFT_LEG,
            position=(-0.15, -0.2, 0.1),
            rotation=(0, 0, 0),
            scale=(1, 1, 1),
            parent=self.torso
        )
        
        self.right_leg = Bone(
            name="right_leg",
            bone_type=BoneType.RIGHT_LEG,
            position=(0.15, -0.2, 0.1),
            rotation=(0, 0, 0),
            scale=(1, 1, 1),
            parent=self.torso
        )
        
        # Bone lookup
        self.bones = {
            BoneType.ROOT: self.root,
            BoneType.TORSO: self.torso,
            BoneType.HEAD: self.head,
            BoneType.LEFT_ARM: self.left_arm,
            BoneType.RIGHT_ARM: self.right_arm,
            BoneType.LEFT_LEG: self.left_leg,
            BoneType.RIGHT_LEG: self.right_leg,
        }
    
    def update_animation(self, animation_state, animation_phase):
        """Update bone rotations based on animation."""
        if animation_state == 'walking':
            # Swing arms and legs
            swing = math.sin(animation_phase) * 0.3
            self.left_arm.rotation = (swing, 0, 0)
            self.right_arm.rotation = (-swing, 0, 0)
            self.left_leg.rotation = (-swing, 0, 0)
            self.right_leg.rotation = (swing, 0, 0)
        
        elif animation_state == 'jumping':
            # Arms up, legs together
            self.left_arm.rotation = (-1.5, 0, 0)
            self.right_arm.rotation = (-1.5, 0, 0)
            self.left_leg.rotation = (0, 0, 0.2)
            self.right_leg.rotation = (0, 0, -0.2)
        
        else:  # idle
            # Reset to neutral
            self.left_arm.rotation = (0, 0, 0)
            self.right_arm.rotation = (0, 0, 0)
            self.left_leg.rotation = (0, 0, 0)
            self.right_leg.rotation = (0, 0, 0)
    
    def get_bone(self, bone_type):
        """Get bone by type."""
        return self.bones.get(bone_type)


class ClothingSystem:
    """Complete clothing system with meshes, accessories, and physics."""
    
    def __init__(self, skeleton: PandaSkeleton):
        self.skeleton = skeleton
        
        # Clothing storage
        self.mesh_clothing: List[ClothingMesh] = []
        self.sprite_accessories: List[SpriteAccessory] = []
        
        # LOD settings
        self.lod_level = LODLevel.HIGH
        self.auto_lod = True
        
        # Physics settings
        self.physics_enabled = True
        self.wind_force = (0, 0, 0)
        
        # Animation state
        self.last_velocity = (0, 0, 0)
    
    def equip_mesh_clothing(self, clothing: ClothingMesh):
        """Equip mesh-based clothing."""
        # Remove existing of same type
        self.mesh_clothing = [c for c in self.mesh_clothing 
                             if c.clothing_type != clothing.clothing_type]
        self.mesh_clothing.append(clothing)
    
    def equip_sprite_accessory(self, accessory: SpriteAccessory):
        """Equip sprite accessory."""
        # Remove existing of same type
        self.sprite_accessories = [a for a in self.sprite_accessories 
                                  if a.accessory_type != accessory.accessory_type]
        self.sprite_accessories.append(accessory)
    
    def update(self, delta_time, panda_velocity, animation_state, animation_phase):
        """Update clothing system."""
        # Update skeleton animation
        self.skeleton.update_animation(animation_state, animation_phase)
        
        # Update LOD if auto
        if self.auto_lod:
            self._update_lod()
        
        # Update physics for accessories
        if self.physics_enabled and self.lod_level.value >= LODLevel.MEDIUM.value:
            for accessory in self.sprite_accessories:
                accessory.update_physics(delta_time, panda_velocity, self.wind_force)
        
        # Update dynamic clothing animations
        self._update_clothing_animations(animation_state, animation_phase, panda_velocity)
        
        self.last_velocity = panda_velocity
    
    def _update_lod(self):
        """Auto-update LOD based on performance."""
        # Would check frame rate, distance, etc.
        # For now, keep HIGH
        pass
    
    def _update_clothing_animations(self, animation_state, animation_phase, velocity):
        """Update clothing squash/stretch/rotation."""
        for clothing in self.mesh_clothing:
            if animation_state == 'jumping':
                # Squash on landing
                clothing.squash_factor = 0.9
            elif animation_state == 'walking':
                # Slight bob
                clothing.squash_factor = 1.0 + 0.05 * math.sin(animation_phase)
            else:
                # Return to normal
                clothing.squash_factor += (1.0 - clothing.squash_factor) * 0.1
            
            # Hat tilt
            if clothing.clothing_type == ClothingType.HAT:
                # Tilt based on movement
                tilt_x = velocity[0] * 10
                tilt_z = velocity[2] * 10
                clothing.rotation_offset = (tilt_x, 0, tilt_z)
    
    def render(self, camera_matrix):
        """Render all clothing."""
        # Render mesh clothing
        for clothing in self.mesh_clothing:
            bone = self.skeleton.get_bone(clothing.attached_bone)
            if bone:
                transform = bone.get_world_transform()
                clothing.render(transform, self.lod_level)
        
        # Render sprite accessories
        for accessory in self.sprite_accessories:
            bone = self.skeleton.get_bone(accessory.attached_bone)
            if bone:
                transform = bone.get_world_transform()
                accessory.render(transform, camera_matrix, self.lod_level)
    
    def set_lod_level(self, level: LODLevel):
        """Manually set LOD level."""
        self.lod_level = level
        self.auto_lod = False
    
    def enable_physics(self, enabled: bool):
        """Enable/disable physics simulation."""
        self.physics_enabled = enabled
    
    def set_wind(self, wind_force):
        """Set wind force for accessories."""
        self.wind_force = wind_force


# Factory functions for common clothing items

def create_shirt(color=(0.8, 0.2, 0.2)):
    """Create a simple shirt mesh."""
    # Simplified shirt vertices (torso-shaped)
    vertices = np.array([
        # Front
        [-0.25, -0.3, 0.15],
        [0.25, -0.3, 0.15],
        [0.25, 0.3, 0.15],
        [-0.25, 0.3, 0.15],
        # Back
        [-0.25, -0.3, -0.15],
        [0.25, -0.3, -0.15],
        [0.25, 0.3, -0.15],
        [-0.25, 0.3, -0.15],
    ], dtype=np.float32)
    
    # Triangle indices
    indices = np.array([
        0, 1, 2, 0, 2, 3,  # Front
        4, 6, 5, 4, 7, 6,  # Back
        0, 4, 5, 0, 5, 1,  # Bottom
        2, 6, 7, 2, 7, 3,  # Top
        0, 3, 7, 0, 7, 4,  # Left
        1, 5, 6, 1, 6, 2,  # Right
    ], dtype=np.uint32)
    
    # Simple normals
    normals = np.array([[0, 0, 1]] * len(vertices), dtype=np.float32)
    
    return ClothingMesh(
        name="Basic Shirt",
        clothing_type=ClothingType.SHIRT,
        attached_bone=BoneType.TORSO,
        vertices=vertices,
        indices=indices,
        normals=normals,
        color=color
    )


def create_scarf_accessory(color=(1.0, 0.5, 0.0)):
    """Create a fluttering scarf sprite accessory."""
    return SpriteAccessory(
        name="Scarf",
        accessory_type=AccessoryType.SCARF,
        attached_bone=BoneType.TORSO,
        offset=(0, 0.2, -0.2),
        size=0.3,
        color=color,
        spring_strength=0.3,
        damping=0.7
    )


def create_glasses_accessory():
    """Create glasses sprite accessory."""
    return SpriteAccessory(
        name="Glasses",
        accessory_type=AccessoryType.GLASSES,
        attached_bone=BoneType.HEAD,
        offset=(0, 0.4, 0.22),
        size=0.15,
        color=(0.1, 0.1, 0.1),
        spring_strength=0.8,
        damping=0.9
    )

"""
Texture Sorter - Organization Styles
Author: Dead On The Inside / JosephsDeadish

Implementation of all 9 organization style presets for sorting textures.
"""

import re as _re
from pathlib import Path
from .organization_engine import OrganizationStyle, TextureInfo


def _has_kw(text: str, keywords) -> bool:
    """Return True if *any* keyword appears as a whole token in *text*.

    Splits on non-alphanumeric characters so that e.g. ``'iron'`` does NOT
    match ``'environment'`` (which contains the *substring* "iron" inside
    "env**iron**ment" but NOT as a standalone word/token).  Without this guard
    every texture with category ``'environment'`` was misclassified as
    ``Metal_Surfaces`` because ``'iron' in 'environment'`` is True in Python.
    """
    tokens = set(_re.split(r'[^a-z0-9]', text))
    return any(kw in tokens for kw in keywords)


class ByAppearanceStyle(OrganizationStyle):
    """
    By Appearance: organises textures by visual traits detected in the image.
    Folder structure: AppearanceType/Subtype/filename
    Example: Skin_Tones/Dark/face_skin_dark.dds
    """

    def get_name(self) -> str:
        return "By Appearance"

    def get_description(self) -> str:
        return (
            "Groups textures by what they look like visually: skin tones, surface materials, "
            "patterns, colours. Best for character/NPC texture sets with many visual variants. "
            "Folders reflect visual traits, not asset function. "
            "Example: Skin_Tones/Tan/, Metal_Surfaces/Polished/, Fabric/Striped/"
        )

    def get_target_path(self, texture: TextureInfo) -> str:
        name = texture.filename.lower()
        cat = texture.category.lower()

        # Skin/body tones
        if _has_kw(name, ['skin', 'body', 'torso', 'arm', 'leg', 'face', 'head']) or \
                _has_kw(cat, ['skin', 'body', 'torso', 'arm', 'leg', 'face', 'head']):
            tone = 'Neutral'
            for t in [('dark', 'Dark'), ('black', 'Dark'), ('brown', 'Brown'),
                       ('tan', 'Tan'), ('light', 'Light'), ('pale', 'Light'), ('white', 'Light')]:
                if t[0] in name:
                    tone = t[1]
                    break
            return str(Path('Skin_Tones', tone, texture.filename))

        # Metal surfaces — use _has_kw to avoid 'iron' matching 'environment'
        if _has_kw(name, ['metal', 'steel', 'iron', 'chrome', 'gold', 'silver', 'armor']) or \
                _has_kw(cat, ['metal', 'steel', 'iron', 'chrome', 'gold', 'silver', 'armor']):
            sub = 'Polished' if any(k in name for k in ['polish', 'shiny', 'clean']) else 'Rough'
            return str(Path('Metal_Surfaces', sub, texture.filename))

        # Stone / rock / concrete
        if _has_kw(name, ['stone', 'rock', 'concrete', 'brick', 'cobble', 'gravel']) or \
                _has_kw(cat, ['stone', 'rock', 'concrete', 'brick', 'cobble', 'gravel']):
            return str(Path('Stone_Surfaces', texture.filename))

        # Wood
        if _has_kw(name, ['wood', 'plank', 'timber', 'bark', 'log']) or \
                _has_kw(cat, ['wood', 'plank', 'timber', 'bark', 'log']):
            return str(Path('Wood_Surfaces', texture.filename))

        # Fabric / cloth
        if _has_kw(name, ['cloth', 'fabric', 'textile', 'shirt', 'pants', 'dress', 'outfit']) or \
                _has_kw(cat, ['cloth', 'fabric', 'textile', 'shirt', 'pants', 'dress', 'outfit']):
            return str(Path('Fabric', texture.filename))

        # Nature / organic
        if _has_kw(name, ['grass', 'leaf', 'moss', 'dirt', 'mud', 'sand', 'nature']) or \
                _has_kw(cat, ['grass', 'leaf', 'moss', 'dirt', 'mud', 'sand', 'nature']):
            return str(Path('Natural_Surfaces', texture.filename))

        # Transparent / alpha / glass
        if _has_kw(name, ['glass', 'window', 'transparent', 'alpha', 'crystal']) or \
                _has_kw(cat, ['glass', 'window', 'transparent', 'alpha', 'crystal']):
            return str(Path('Transparent', texture.filename))

        # Glow / energy
        if _has_kw(name, ['glow', 'light', 'neon', 'energy', 'fire', 'flame', 'electric']) or \
                _has_kw(cat, ['glow', 'light', 'neon', 'energy', 'fire', 'flame', 'electric']):
            return str(Path('Glowing_Energy', texture.filename))

        # Fall back to category
        top = texture.category.replace('/', '_') or 'Other'
        return str(Path(top, texture.filename))


class ByTypeStyle(OrganizationStyle):
    """
    By Type: Category/BaseType/Individual
    Groups each texture by its content category, then by the base asset type,
    then the individual file.
    Example: Characters/warrior/warrior_red.dds
    """

    def get_name(self) -> str:
        return "By Type"

    def get_description(self) -> str:
        return ("Sorts by content type then by the specific asset sub-type. "
                "Ideal for large sets with many distinct subtypes (creatures, items, props). "
                "Hierarchy: Category → Base Type → Individual File. "
                "Example: Characters/warrior/warrior_red.dds")
    
    def get_target_path(self, texture: TextureInfo) -> str:
        parts = []
        
        # Main category
        parts.append(texture.category)
        
        # Detect type (base name without variant)
        base_name = texture.filename.rsplit('_', 1)[0] if '_' in texture.filename else texture.filename
        base_name = base_name.split('.')[0]  # Remove extension
        parts.append(base_name)
        
        # LODs in same folder with file
        parts.append(texture.filename)
        
        return str(Path(*parts))


class FlatStyle(OrganizationStyle):
    """
    Flat Style: All LODs in category root
    Example: Characters/character_lod0.dds, Characters/character_lod1.dds
    """
    
    def get_name(self) -> str:
        return "Flat Style"
    
    def get_description(self) -> str:
        return ("Simple single-level sorting with no nesting. "
                "Best for: quick browsing, small texture sets, or when deep folders are unwanted. "
                "All files of the same category land in one folder, LODs included. "
                "Example: Characters/character_lod0.dds, Characters/character_lod1.dds")
    
    def get_target_path(self, texture: TextureInfo) -> str:
        # Just category and filename - no subdirectories
        return str(Path(texture.category) / texture.filename)


class ByLocationStyle(OrganizationStyle):
    """
    By Location: organises by detected scene/area context, then asset type.
    Example: Outdoor/Urban/Buildings/shop_front.dds
    """

    def get_name(self) -> str:
        return "By Location"

    def get_description(self) -> str:
        return (
            "Groups textures by the scene or location they belong to. "
            "Automatically detects indoor vs outdoor, environment zone, and area type. "
            "Hierarchy: Zone → Area → Category → File. "
            "Example: Outdoor/Urban/Buildings/shop_front.dds, Indoor/Residential/Floors/floor_wood.dds"
        )

    # Zone keywords → (zone_folder, area_folder)
    _ZONES = [
        # Outdoor areas
        (['city', 'urban', 'street', 'road', 'sidewalk', 'downtown', 'alley'], ('Outdoor', 'Urban')),
        (['residential', 'suburb', 'house', 'home', 'garden', 'yard', 'fence'], ('Outdoor', 'Residential')),
        (['industrial', 'factory', 'warehouse', 'pipe', 'machinery', 'plant'], ('Outdoor', 'Industrial')),
        (['nature', 'forest', 'jungle', 'swamp', 'marsh', 'woodland', 'tree'], ('Outdoor', 'Nature')),
        (['desert', 'sand', 'dune', 'arid', 'wasteland'], ('Outdoor', 'Desert')),
        (['snow', 'ice', 'arctic', 'tundra', 'frozen'], ('Outdoor', 'Arctic')),
        (['ocean', 'sea', 'beach', 'coast', 'shore', 'water', 'river', 'lake'], ('Outdoor', 'Water')),
        (['mountain', 'cliff', 'canyon', 'rock', 'cave', 'cavern'], ('Outdoor', 'Rocky')),
        # Indoor areas
        (['interior', 'indoor', 'room', 'corridor', 'hall', 'lobby', 'office', 'apartment'], ('Indoor', 'General')),
        (['kitchen', 'bathroom', 'bedroom', 'living'], ('Indoor', 'Residential')),
        (['dungeon', 'prison', 'cell', 'sewer'], ('Indoor', 'Underground')),
        (['castle', 'church', 'cathedral', 'ruin', 'temple', 'shrine'], ('Indoor', 'Historic')),
        (['sci', 'futur', 'space', 'station', 'lab', 'tech', 'cyber'], ('Indoor', 'SciFi')),
    ]

    def get_target_path(self, texture: TextureInfo) -> str:
        name_lower = texture.filename.lower()
        cat_lower = texture.category.lower()
        combined = name_lower + ' ' + cat_lower

        zone = 'Outdoor'
        area = 'General'

        for keywords, (z, a) in self._ZONES:
            if any(kw in combined for kw in keywords):
                zone, area = z, a
                break

        return str(Path(zone, area, texture.category or 'Misc', texture.filename))


class ByResolutionStyle(OrganizationStyle):
    """
    By Resolution: Category/Resolution/Format — groups by texture size and file format.
    Example: Characters/2K/DDS/head_texture.dds
    """

    def get_name(self) -> str:
        return "By Resolution"

    def get_description(self) -> str:
        return (
            "Groups by content type, then resolution tier, then file format. "
            "Resolution is read from image metadata when available; otherwise inferred from filename keywords. "
            "Hierarchy: Category → Resolution (4K/2K/1K/512/Low) → Format → File. "
            "Example: Characters/2K/DDS/head_texture.dds, Environment/4K/PNG/ground_rock.png"
        )

    @staticmethod
    def _res_tier_from_dims(dims):
        w, h = dims
        m = max(w, h)
        if m >= 4096:   return '4K+'
        if m >= 2048:   return '2K'
        if m >= 1024:   return '1K'
        if m >= 512:    return '512'
        return 'Low'

    @staticmethod
    def _res_tier_from_name(name: str) -> str:
        """Infer resolution tier from filename keywords."""
        n = name.lower()
        if '4k' in n or '4096' in n: return '4K+'
        if '2k' in n or '2048' in n: return '2K'
        if '1k' in n or '1024' in n: return '1K'
        if '512' in n:               return '512'
        if 'hd' in n or 'high' in n: return '2K'
        if 'low' in n or 'lod' in n: return 'Low'
        return '1K'  # 1K is the most common texture resolution in game assets

    def get_target_path(self, texture: TextureInfo) -> str:
        res_tier = (self._res_tier_from_dims(texture.dimensions)
                    if texture.dimensions else
                    self._res_tier_from_name(texture.filename))
        fmt = (texture.format.upper() if texture.format else
               Path(texture.filename).suffix.lstrip('.').upper() or 'Unknown')
        lod = f"LOD{texture.lod_level}" if texture.lod_level is not None else None
        parts = [texture.category or 'Misc', res_tier, fmt]
        if lod:
            parts.append(lod)
        parts.append(texture.filename)
        return str(Path(*parts))


class BySystemStyle(OrganizationStyle):
    """
    By System: groups textures by the functional system they serve
    (Characters, Vehicles, UI, Items, Environment, etc.)
    Example: Characters/Body/head_texture.dds
    """

    def get_name(self) -> str:
        return "By System"

    def get_description(self) -> str:
        return (
            "Groups textures by their functional role in the project: Characters, Vehicles, UI, "
            "Weapons, Environment, Effects, Props. "
            "Best for large diverse sets with many asset types. "
            "Hierarchy: System → Sub-category → File. "
            "Example: Characters/Body/head_texture.dds, Vehicles/Cars/sedan_body.dds"
        )

    # (keywords_in_category_or_filename) → system folder
    _SYSTEMS = [
        (['character', 'npc', 'player', 'body', 'face', 'hair', 'skin', 'outfit', 'cloth'], 'Characters'),
        (['vehicle', 'car', 'bike', 'plane', 'boat', 'truck', 'van', 'bus', 'moto'],       'Vehicles'),
        (['weapon', 'gun', 'sword', 'blade', 'rifle', 'pistol', 'axe', 'bow', 'ammo'],     'Weapons'),
        (['ui', 'hud', 'menu', 'button', 'icon', 'cursor', 'interface', 'font'],            'UI'),
        (['effect', 'particle', 'smoke', 'fire', 'glow', 'spark', 'decal', 'splash'],      'Effects'),
        (['env', 'environment', 'ground', 'floor', 'wall', 'ceiling', 'sky', 'terrain',
          'grass', 'tree', 'nature', 'rock', 'water', 'ocean', 'sand', 'snow'],            'Environment'),
        (['prop', 'furniture', 'food', 'plant', 'sign', 'box', 'crate', 'barrel'],         'Props'),
        (['animal', 'creature', 'monster', 'beast', 'wildlife'],                             'Creatures'),
    ]

    def get_target_path(self, texture: TextureInfo) -> str:
        combined = (texture.category + ' ' + texture.filename).lower()
        system = 'Props'   # default
        for keywords, sys_folder in self._SYSTEMS:
            if any(kw in combined for kw in keywords):
                system = sys_folder
                break
        # Sub-category: first part of the AI-classified category (e.g. "Characters/Skin" → "Skin")
        parts_cat = texture.category.split('/')
        sub = parts_cat[1] if len(parts_cat) > 1 else (parts_cat[0] if parts_cat else 'General')
        return str(Path(system, sub, texture.filename))


class MinimalistStyle(OrganizationStyle):
    """
    Minimalist Style: Simple categories only
    Example: Characters/texture.dds, UI/icon.png
    """
    
    def get_name(self) -> str:
        return "Minimalist Style"
    
    def get_description(self) -> str:
        return ("Ultra-simple one-level sorting with zero nesting. "
                "Best for: tiny texture sets, quick previews, or when you just want files grouped by type. "
                "Each category is a single folder with all its files inside. "
                "Example: Characters/texture.dds, UI/icon.png")
    
    def get_target_path(self, texture: TextureInfo) -> str:
        # Most minimal - just category folder
        return str(Path(texture.category) / texture.filename)


class MaximumDetailStyle(OrganizationStyle):
    """
    Maximum Detail Style: Deep nested hierarchies
    Example: Characters/Male/Adult/Casual/Shirt/Blue/LOD0/shirt_blue_lod0.dds
    """
    
    def get_name(self) -> str:
        return "Maximum Detail Style"
    
    def get_description(self) -> str:
        return ("Deep multi-level sorting with every possible attribute as a folder. "
                "Best for: large HD texture packs, comprehensive modding archives, or research. "
                "Sorts by category, gender, age, style, item type, color, format, resolution, and LOD. "
                "Example: Characters/Male/Adult/Casual/Shirt/Blue/HighRes/LOD0/shirt_blue_lod0.dds")
    
    def get_target_path(self, texture: TextureInfo) -> str:
        parts = []
        
        # Category
        parts.append(texture.category)
        
        # Gender if detected
        gender = self.detect_variant(texture.filename)
        if gender in ['Male', 'Female']:
            parts.append(gender)
        
        # Age group (if detectable)
        filename_lower = texture.filename.lower()
        if 'child' in filename_lower or 'kid' in filename_lower:
            parts.append('Child')
        elif 'teen' in filename_lower:
            parts.append('Teen')
        else:
            parts.append('Adult')
        
        # Style/Type (detect common descriptors)
        for style in ['Casual', 'Formal', 'Sports', 'Military', 'Fantasy']:
            if style.lower() in filename_lower:
                parts.append(style)
                break
        
        # Specific item type (try to extract from filename)
        for item in ['Shirt', 'Pants', 'Shoes', 'Hat', 'Jacket', 'Dress']:
            if item.lower() in filename_lower:
                parts.append(item)
                break
        
        # Color variant
        variant = self.detect_variant(texture.filename)
        if variant and variant not in ['Male', 'Female']:
            parts.append(variant)
        
        # Format
        if texture.format:
            parts.append(texture.format.upper())
        
        # Resolution tier
        if texture.dimensions:
            width, height = texture.dimensions
            max_dim = max(width, height)
            if max_dim >= 2048:
                parts.append('HighRes')
            elif max_dim >= 1024:
                parts.append('MedRes')
            else:
                parts.append('LowRes')
        
        # LOD level
        if texture.lod_level is not None:
            parts.append(f"LOD{texture.lod_level}")
        
        # Filename
        parts.append(texture.filename)
        
        return str(Path(*parts))


class CustomStyle(OrganizationStyle):
    """
    Custom Style: User-defined hierarchy rules
    Configurable through a hierarchy template
    """
    
    def __init__(self, hierarchy_template: list = None):
        """
        Initialize with custom hierarchy template.
        
        Args:
            hierarchy_template: List of hierarchy levels, e.g.,
                ['category', 'format', 'resolution', 'filename']
        """
        self.hierarchy_template = hierarchy_template or ['category', 'filename']
    
    def get_name(self) -> str:
        return "Custom Style"
    
    def get_description(self) -> str:
        return ("Fully customizable hierarchy using a user-defined template. "
                "Best for: advanced users who need a specific folder structure. "
                "Configure levels from: category, format, resolution, lod, variant, filename. "
                "Example template ['category', 'format', 'filename'] → Characters/DDS/texture.dds")
    
    def get_target_path(self, texture: TextureInfo) -> str:
        parts = []
        
        for level in self.hierarchy_template:
            if level == 'category':
                parts.append(texture.category)
            elif level == 'format':
                parts.append(texture.format.upper() if texture.format else 'Unknown')
            elif level == 'resolution':
                if texture.dimensions:
                    width, height = texture.dimensions
                    parts.append(f"{width}x{height}")
                else:
                    parts.append('Unknown_Res')
            elif level == 'lod':
                if texture.lod_level is not None:
                    parts.append(f"LOD{texture.lod_level}")
            elif level == 'variant':
                variant = self.detect_variant(texture.filename)
                if variant:
                    parts.append(variant)
            elif level == 'filename':
                parts.append(texture.filename)
        
        # Always ensure filename is at the end
        if 'filename' not in self.hierarchy_template:
            parts.append(texture.filename)
        
        return str(Path(*parts))


# Dictionary of all available organization styles
# Keys are the internal identifiers used by the UI combos and config files.
ORGANIZATION_STYLES = {
    'by_appearance': ByAppearanceStyle,
    'by_type': ByTypeStyle,
    'flat': FlatStyle,
    'by_location': ByLocationStyle,
    'by_resolution': ByResolutionStyle,
    'by_system': BySystemStyle,
    'minimalist': MinimalistStyle,
    'maximum_detail': MaximumDetailStyle,
    'custom': CustomStyle,
    # Legacy key aliases so old saved configs still load
    'sims': ByAppearanceStyle,
    'neopets': ByTypeStyle,
    'game_area': ByLocationStyle,
    'asset_pipeline': ByResolutionStyle,
    'modular': BySystemStyle,
}

# Legacy class-name aliases — kept so old imports (e.g. organizer/__init__.py) don't break
SimsStyle = ByAppearanceStyle
NeopetsStyle = ByTypeStyle
GameAreaStyle = ByLocationStyle
AssetPipelineStyle = ByResolutionStyle
ModularStyle = BySystemStyle

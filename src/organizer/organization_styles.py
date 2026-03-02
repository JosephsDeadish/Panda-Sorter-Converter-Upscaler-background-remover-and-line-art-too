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


# ── Game-console presets ─────────────────────────────────────────────────────
# Optimised for the small, compressed texture libraries produced by classic
# console games.  Each preset:
#   • Detects the most common map type from the filename suffix / keyword
#     (_d / diffuse, _n / normal, _s / specular, _e / emissive, _a / alpha)
#   • Assigns a content category (Characters, Environments, Items, UI, …)
#   • Keeps a resolution sub-tier so CI/CD pipelines can distinguish LOD layers
#     common in console ports (e.g. 16px icon sprites vs. 256px character maps)

def _console_map_type(name: str) -> str:
    """Derive map-type folder from filename suffixes / keywords."""
    n = name.lower()
    if any(s in n for s in ('_nrm', '_norm', '_n.', '_n_', 'normal')):
        return 'Normal'
    if any(s in n for s in ('_spc', '_spec', '_s.', '_s_', 'specular', 'gloss')):
        return 'Specular'
    if any(s in n for s in ('_emi', '_emis', '_e.', '_e_', 'emissive', 'glow')):
        return 'Emissive'
    if any(s in n for s in ('_alp', '_a.', '_a_', 'alpha', '_msk', 'mask')):
        return 'Alpha'
    # Default → diffuse
    return 'Diffuse'


def _console_content_cat(name: str) -> str:
    """Map filename keywords → broad content category."""
    n = name.lower()
    if any(k in n for k in ('chr', 'char', 'npc', 'player', 'ply', 'face', 'head',
                              'body', 'skin', 'hair', 'hand', 'arm', 'leg')):
        return 'Characters'
    if any(k in n for k in ('wpn', 'weap', 'gun', 'sword', 'blade', 'knife',
                              'rifle', 'bow', 'item', 'itm')):
        return 'Items'
    if any(k in n for k in ('ui', 'hud', 'font', 'icon', 'btn', 'menu', 'cursor',
                              'button', 'iface', 'interface')):
        return 'UI'
    if any(k in n for k in ('fx', 'eff', 'smoke', 'fire', 'spark', 'glow',
                              'particle', 'decal', 'blood', 'hit')):
        return 'Effects'
    if any(k in n for k in ('sky', 'cloud', 'sun', 'moon', 'star', 'bg', 'background')):
        return 'Sky'
    # Default → Environments
    return 'Environments'


def _console_res_tier(dims, max_typical: int) -> str:
    """Return a size-tier folder name.  *max_typical* is the console's normal max."""
    if dims is None:
        return 'Unknown'
    w, h = dims
    p = max(w, h)
    if p <= 16:
        return 'Tiny_16'
    if p <= 32:
        return 'Small_32'
    if p <= 64:
        return 'Med_64'
    if p <= 128:
        return 'Large_128'
    if p <= 256:
        return 'XL_256'
    if p <= 512:
        return 'XXL_512'
    return f'Huge_{p}'   # e.g. Huge_1024 — above typical console maximum


class PS2Style(OrganizationStyle):
    """PlayStation 2 texture preset.

    Recommended for PS2 game texture dumps and mod projects.
    Sorts by content category → map type → resolution tier, reflecting the
    small (4–256 px) textures typical of PS2 titles.
    Example: Characters/Diffuse/Med_64/chr_link_body.tga
    """

    def get_name(self) -> str:
        return "PlayStation 2"

    def get_description(self) -> str:
        return (
            "Optimised for PlayStation 2 texture libraries. "
            "Sorts by content (Characters, Environments, Items, UI, Effects) → "
            "map type (Diffuse, Normal, Specular, Alpha) → resolution tier (up to 256 px). "
            "Example: Characters/Diffuse/Med_64/chr_link_body.tga"
        )

    def get_target_path(self, texture: TextureInfo) -> str:
        cat  = _console_content_cat(texture.filename)
        mtype = _console_map_type(texture.filename)
        tier  = _console_res_tier(texture.dimensions, 256)
        return str(Path(cat, mtype, tier, texture.filename))


class PSPStyle(OrganizationStyle):
    """PlayStation Portable texture preset.

    Textures on PSP are even smaller than PS2 (rarely exceed 128×128).
    Sorts by category → map type, omitting the resolution tier to avoid
    a proliferation of near-empty folders for tiny icon sprites.
    Example: Characters/Diffuse/chr_npc_guard_d.gim
    """

    def get_name(self) -> str:
        return "PlayStation Portable (PSP)"

    def get_description(self) -> str:
        return (
            "Optimised for PSP texture libraries (GIM, TGA, PNG). "
            "Two-level hierarchy: content category → map type. "
            "Resolution tier is omitted because PSP textures rarely exceed 128 px. "
            "Example: Characters/Diffuse/chr_guard_d.gim"
        )

    def get_target_path(self, texture: TextureInfo) -> str:
        cat   = _console_content_cat(texture.filename)
        mtype = _console_map_type(texture.filename)
        return str(Path(cat, mtype, texture.filename))


class GameCubeStyle(OrganizationStyle):
    """Nintendo GameCube / Wii texture preset.

    GameCube and Wii textures are extracted from TPL containers and span a
    wider resolution range (4–1024 px) than PS2/PSP.  This preset sorts by
    category → map type → resolution tier with GC-friendly tier labels.
    Example: Environments/Diffuse/XL_256/stage_lava_floor_d.png
    """

    def get_name(self) -> str:
        return "GameCube / Wii"

    def get_description(self) -> str:
        return (
            "Optimised for GameCube and Wii texture libraries (TPL-extracted PNG/TGA). "
            "Sorts by category → map type → resolution tier (4–1024 px range). "
            "Example: Environments/Diffuse/XL_256/stage_lava_d.png"
        )

    def get_target_path(self, texture: TextureInfo) -> str:
        cat   = _console_content_cat(texture.filename)
        mtype = _console_map_type(texture.filename)
        tier  = _console_res_tier(texture.dimensions, 1024)
        return str(Path(cat, mtype, tier, texture.filename))


class N64Style(OrganizationStyle):
    """Nintendo 64 texture preset.

    N64 textures are notoriously tiny (most are 32×32 or 64×64; 16-bit colour).
    This preset uses a flat two-level hierarchy (category → filename) to avoid
    creating dozens of near-empty resolution-tier folders for micro-textures.
    Example: Environments/tex_field_grass.png
    """

    def get_name(self) -> str:
        return "Nintendo 64"

    def get_description(self) -> str:
        return (
            "Optimised for N64 texture libraries (PNG extracts from CI4/RGBA16/RGBA32). "
            "Flat two-level hierarchy: content category → filename. "
            "Resolution tiers are omitted because N64 textures rarely exceed 64 px. "
            "Example: Environments/tex_field_grass.png"
        )

    def get_target_path(self, texture: TextureInfo) -> str:
        cat = _console_content_cat(texture.filename)
        return str(Path(cat, texture.filename))


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
    # ── Game-console presets ──────────────────────────────────────────────
    'ps2':      PS2Style,
    'psp':      PSPStyle,
    'gamecube': GameCubeStyle,
    'n64':      N64Style,
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

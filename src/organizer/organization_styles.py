"""
Game Texture Sorter - Organization Styles
Author: Dead On The Inside / JosephsDeadish

Implementation of all 9 organization style presets for sorting textures.
"""

from pathlib import Path
from .organization_engine import OrganizationStyle, TextureInfo


class SimsStyle(OrganizationStyle):
    """
    The Sims Style: Gender/Skin/BodyPart/Variant
    Example: Male/DarkSkin/Head/variant_01.dds
    """
    
    def get_name(self) -> str:
        return "The Sims Style"
    
    def get_description(self) -> str:
        return ("Character-focused sorting by physical traits. "
                "Best for: games with character customization (The Sims, Saints Row, WWE). "
                "Hierarchy: Gender → Skin Tone → Body Part → Variant. "
                "Example: Male/Skin_Tan/Head/head_variant_01.dds")
    
    def get_target_path(self, texture: TextureInfo) -> str:
        parts = []
        
        # Detect gender
        gender = self.detect_variant(texture.filename)
        if gender in ['Male', 'Female']:
            parts.append(gender)
        else:
            parts.append('Unisex')
        
        # Detect skin/color variant (for character textures)
        if 'character' in texture.category.lower() or 'skin' in texture.category.lower():
            skin_tone = 'Default'
            for tone in ['Black', 'White', 'Brown', 'Tan']:
                if tone.lower() in texture.filename.lower():
                    skin_tone = tone
                    break
            parts.append(f"Skin_{skin_tone}")
        
        # Add category as body part
        parts.append(texture.category)
        
        # Add LOD folder if applicable
        if texture.lod_group:
            parts.append(f"LOD_{texture.lod_level if texture.lod_level is not None else 'unknown'}")
        
        # Final filename
        parts.append(texture.filename)
        
        return str(Path(*parts))


class NeopetsStyle(OrganizationStyle):
    """
    Neopets Style: Category/Type/Individual
    Example: Pets/Blumaroo/blumaroo_red.dds
    """
    
    def get_name(self) -> str:
        return "Neopets Style"
    
    def get_description(self) -> str:
        return ("Collectible-style sorting by species/type then individual. "
                "Best for: games with many distinct creature or item types (Neopets, Pokemon, Monster Hunter). "
                "Hierarchy: Category → Base Type → Individual File. "
                "Example: Pets/Blumaroo/blumaroo_red.dds")
    
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


class GameAreaStyle(OrganizationStyle):
    """
    Game Area Style: Level/Area/Type/Asset
    Example: Level_01/Downtown/Buildings/shop_front.dds
    """
    
    def get_name(self) -> str:
        return "Game Area Style"
    
    def get_description(self) -> str:
        return ("Level/area-based sorting for open-world and stage-based games. "
                "Best for: GTA, God of War, Kingdom Hearts, or any game organized by locations. "
                "Hierarchy: Level → Area → Asset Type → File. "
                "Example: Level_01/Downtown/Buildings/shop_front.dds")
    
    def get_target_path(self, texture: TextureInfo) -> str:
        parts = []
        
        # Try to detect level/area from filename
        filename_lower = texture.filename.lower()
        
        # Level detection
        level = 'General'
        for i in range(1, 20):
            if f'level{i}' in filename_lower or f'lvl{i}' in filename_lower or f'l{i}_' in filename_lower:
                level = f"Level_{i:02d}"
                break
        parts.append(level)
        
        # Area detection (common game areas)
        area = 'Common'
        area_keywords = {
            'Downtown': ['downtown', 'city', 'urban'],
            'Residential': ['residential', 'house', 'home'],
            'Industrial': ['industrial', 'factory', 'warehouse'],
            'Park': ['park', 'garden', 'outdoor'],
            'Interior': ['interior', 'indoor', 'inside']
        }
        
        for area_name, keywords in area_keywords.items():
            if any(kw in filename_lower for kw in keywords):
                area = area_name
                break
        parts.append(area)
        
        # Type is category
        parts.append(texture.category)
        
        # Filename
        parts.append(texture.filename)
        
        return str(Path(*parts))


class AssetPipelineStyle(OrganizationStyle):
    """
    Asset Pipeline Style: Type/Resolution/Format
    Example: Textures/2K/DDS/building_wall.dds
    """
    
    def get_name(self) -> str:
        return "Asset Pipeline Style"
    
    def get_description(self) -> str:
        return ("Production-pipeline sorting by type, resolution, and format. "
                "Best for: modding workflows, HD texture packs, or export/import pipelines. "
                "Groups textures by resolution tier and file format for batch processing. "
                "Example: Textures/2K/DDS/building_wall.dds")
    
    def get_target_path(self, texture: TextureInfo) -> str:
        parts = []
        
        # Type is category
        parts.append(texture.category)
        
        # Resolution tier
        if texture.dimensions:
            width, height = texture.dimensions
            max_dim = max(width, height)
            
            if max_dim >= 4096:
                res_tier = '4K+'
            elif max_dim >= 2048:
                res_tier = '2K'
            elif max_dim >= 1024:
                res_tier = '1K'
            elif max_dim >= 512:
                res_tier = '512'
            else:
                res_tier = 'Low'
            parts.append(res_tier)
        else:
            parts.append('Unknown_Res')
        
        # Format
        parts.append(texture.format.upper() if texture.format else 'Unknown')
        
        # LOD if applicable
        if texture.lod_level is not None:
            parts.append(f"LOD{texture.lod_level}")
        
        # Filename
        parts.append(texture.filename)
        
        return str(Path(*parts))


class ModularStyle(OrganizationStyle):
    """
    Modular Style: Character/Vehicle/Environment/UI
    Example: Characters/Body/head_texture.dds
    """
    
    def get_name(self) -> str:
        return "Modular Style"
    
    def get_description(self) -> str:
        return ("Module-based sorting by gameplay system (characters, vehicles, UI, items, environment). "
                "Best for: action games with diverse asset types (GTA, Gran Turismo, Final Fantasy). "
                "Groups textures by the game system they belong to. "
                "Example: Characters/Body/head_texture.dds, Vehicles/Cars/sedan_body.dds")
    
    def get_target_path(self, texture: TextureInfo) -> str:
        parts = []
        
        # Determine module type from category
        category_lower = texture.category.lower()
        
        if any(kw in category_lower for kw in ['character', 'npc', 'player', 'body', 'face', 'hair', 'skin']):
            module = 'Characters'
        elif any(kw in category_lower for kw in ['vehicle', 'car', 'bike', 'plane', 'boat']):
            module = 'Vehicles'
        elif any(kw in category_lower for kw in ['ui', 'hud', 'menu', 'button', 'icon', 'interface']):
            module = 'UI'
        elif any(kw in category_lower for kw in ['weapon', 'gun', 'sword', 'item']):
            module = 'Items'
        else:
            module = 'Environment'
        
        parts.append(module)
        
        # Category
        parts.append(texture.category)
        
        # Variant folder if detected
        variant = self.detect_variant(texture.filename)
        if variant and variant not in ['Variant_01', 'Variant_02']:  # Skip generic numeric variants
            parts.append(variant)
        
        # Filename
        parts.append(texture.filename)
        
        return str(Path(*parts))


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
ORGANIZATION_STYLES = {
    'sims': SimsStyle,
    'neopets': NeopetsStyle,
    'flat': FlatStyle,
    'game_area': GameAreaStyle,
    'asset_pipeline': AssetPipelineStyle,
    'modular': ModularStyle,
    'minimalist': MinimalistStyle,
    'maximum_detail': MaximumDetailStyle,
    'custom': CustomStyle
}

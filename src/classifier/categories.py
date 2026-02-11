"""
Texture Categories Definition
Comprehensive list of 50+ texture categories for PS2 texture classification
"""

# Character/Organic Categories
CHARACTER_ORGANIC = {
    "eyes": {
        "name": "Eyes",
        "keywords": ["eye", "eyeball", "pupil", "iris", "eyelid", "eyelash"],
        "group": "Character/Organic"
    },
    "hair": {
        "name": "Hair",
        "keywords": ["hair", "hairdo", "haircut", "hairstyle", "ponytail", "braid",
                     "hairtex", "fur", "mane", "wig"],
        "group": "Character/Organic"
    },
    "face": {
        "name": "Face",
        "keywords": ["face", "facial", "cheek", "chin", "forehead", "nose", "mouth", "lip",
                     "head", "headtex", "face_tex", "expression"],
        "group": "Character/Organic"
    },
    "skin1": {
        "name": "Skin1",
        "keywords": ["skin", "skin1", "flesh", "body", "bodytex", "skintex", "skin_color",
                     "skin_diffuse", "skin_diff"],
        "group": "Character/Organic"
    },
    "skin2": {
        "name": "Skin2",
        "keywords": ["skin2", "skintone"],
        "group": "Character/Organic"
    },
    "sunburnt": {
        "name": "Sunburnt",
        "keywords": ["sunburn", "sunburnt", "burnt", "tan", "tanned"],
        "group": "Character/Organic"
    },
    "teeth": {
        "name": "Teeth",
        "keywords": ["teeth", "tooth", "dental", "fang"],
        "group": "Character/Organic"
    },
    "nails": {
        "name": "Nails",
        "keywords": ["nail", "finger", "fingernail", "claw"],
        "group": "Character/Organic"
    },
    "tattoos": {
        "name": "Tattoos",
        "keywords": ["tattoo", "ink", "bodypaint", "marking"],
        "group": "Character/Organic"
    },
    "person": {
        "name": "Person",
        "keywords": ["person", "human", "character", "body", "fullbody", "char", "player", "hero",
                     "npc_body", "protagonist", "avatar", "model", "humanoid", "unwrap", "uv_body",
                     "bodymesh", "char_body", "playerbody"],
        "group": "Character/Organic"
    },
    "animals": {
        "name": "Animals",
        "keywords": ["animal", "beast", "creature", "pet", "dog", "cat", "bird",
                     "horse", "wolf", "bear", "snake", "fish", "dragon", "spider",
                     "insect", "rat", "bat", "deer", "lion", "tiger"],
        "group": "Character/Organic"
    },
    "creatures": {
        "name": "Creatures",
        "keywords": ["creature", "monster", "beast", "alien"],
        "group": "Character/Organic"
    },
    "monsters": {
        "name": "Monsters",
        "keywords": ["monster", "demon", "fiend", "enemy"],
        "group": "Character/Organic"
    },
    "npcs": {
        "name": "NPCs",
        "keywords": ["npc", "vendor", "civilian", "townfolk"],
        "group": "Character/Organic"
    }
}

# Clothing/Wearables Categories
CLOTHING_WEARABLES = {
    "shirts": {
        "name": "Shirts",
        "keywords": ["shirt", "top", "blouse", "tshirt", "tunic"],
        "group": "Clothing/Wearables"
    },
    "pants": {
        "name": "Pants",
        "keywords": ["pants", "trousers", "jeans", "slacks", "bottoms"],
        "group": "Clothing/Wearables"
    },
    "shoes": {
        "name": "Shoes",
        "keywords": ["shoe", "boot", "sandal", "sneaker", "footwear"],
        "group": "Clothing/Wearables"
    },
    "gloves": {
        "name": "Gloves",
        "keywords": ["glove", "gauntlet", "mitt", "handwear"],
        "group": "Clothing/Wearables"
    },
    "hats": {
        "name": "Hats",
        "keywords": ["hat", "cap", "beanie", "headwear"],
        "group": "Clothing/Wearables"
    },
    "helmets": {
        "name": "Helmets",
        "keywords": ["helmet", "headgear", "hardhat"],
        "group": "Clothing/Wearables"
    },
    "armor": {
        "name": "Armor",
        "keywords": ["armor", "armour", "plate", "chainmail", "protection", "shield",
                     "breastplate", "pauldron", "greave", "vambrace", "cuirass", "chestplate"],
        "group": "Clothing/Wearables"
    },
    "accessories": {
        "name": "Accessories",
        "keywords": ["accessory", "belt", "scarf", "tie"],
        "group": "Clothing/Wearables"
    },
    "jewelry": {
        "name": "Jewelry",
        "keywords": ["jewelry", "jewellery", "ring", "necklace", "earring", "bracelet"],
        "group": "Clothing/Wearables"
    },
    "bags": {
        "name": "Bags",
        "keywords": ["bag", "backpack", "satchel", "pouch", "purse"],
        "group": "Clothing/Wearables"
    }
}

# Vehicle Categories
VEHICLES = {
    "cars": {
        "name": "Cars",
        "keywords": ["car", "auto", "automobile", "sedan", "coupe"],
        "group": "Vehicles"
    },
    "trucks": {
        "name": "Trucks",
        "keywords": ["truck", "pickup", "lorry", "van"],
        "group": "Vehicles"
    },
    "trains": {
        "name": "Trains",
        "keywords": ["train", "locomotive", "railway", "subway"],
        "group": "Vehicles"
    },
    "boats": {
        "name": "Boats",
        "keywords": ["boat", "ship", "vessel", "yacht", "sailboat"],
        "group": "Vehicles"
    },
    "aircraft": {
        "name": "Aircraft",
        "keywords": ["aircraft", "plane", "airplane", "jet", "helicopter"],
        "group": "Vehicles"
    },
    "bikes": {
        "name": "Bikes",
        "keywords": ["bike", "bicycle", "cycle"],
        "group": "Vehicles"
    },
    "motorcycles": {
        "name": "Motorcycles",
        "keywords": ["motorcycle", "motorbike", "chopper", "scooter"],
        "group": "Vehicles"
    },
    "vehicle_interiors": {
        "name": "Vehicle Interiors",
        "keywords": ["interior", "dashboard", "cockpit", "cabin"],
        "group": "Vehicles"
    },
    "vehicle_parts": {
        "name": "Vehicle Parts",
        "keywords": ["engine", "motor", "transmission", "exhaust"],
        "group": "Vehicles"
    },
    "wheels_tires": {
        "name": "Wheels/Tires",
        "keywords": ["wheel", "tire", "tyre", "rim", "hubcap"],
        "group": "Vehicles"
    }
}

# Environment - Natural Categories
ENVIRONMENT_NATURAL = {
    "trees": {"name": "Trees", "keywords": ["tree", "trunk", "treebark"], "group": "Environment/Natural"},
    "plants": {"name": "Plants", "keywords": ["plant", "vegetation", "flora"], "group": "Environment/Natural"},
    "flowers": {"name": "Flowers", "keywords": ["flower", "bloom", "blossom", "petal"], "group": "Environment/Natural"},
    "grass": {"name": "Grass", "keywords": ["grass", "lawn", "turf"], "group": "Environment/Natural"},
    "bushes": {"name": "Bushes", "keywords": ["bush", "shrub", "hedge"], "group": "Environment/Natural"},
    "leaves": {"name": "Leaves", "keywords": ["leaf", "leaves", "foliage"], "group": "Environment/Natural"},
    "wood": {"name": "Wood", "keywords": ["wood", "wooden", "timber", "lumber"], "group": "Environment/Natural"},
    "bark": {"name": "Bark", "keywords": ["bark", "treebark"], "group": "Environment/Natural"},
    "water": {"name": "Water", "keywords": ["water", "ocean", "sea", "lake", "river", "pond"], "group": "Environment/Natural"},
    "ice": {"name": "Ice", "keywords": ["ice", "frozen", "glacier", "icicle"], "group": "Environment/Natural"},
    "snow": {"name": "Snow", "keywords": ["snow", "snowy", "snowflake"], "group": "Environment/Natural"},
    "sand": {"name": "Sand", "keywords": ["sand", "sandy", "beach", "dune"], "group": "Environment/Natural"},
    "dirt": {"name": "Dirt", "keywords": ["dirt", "soil", "earth", "ground"], "group": "Environment/Natural"},
    "mud": {"name": "Mud", "keywords": ["mud", "muddy", "swamp"], "group": "Environment/Natural"},
    "rocks": {"name": "Rocks", "keywords": ["rock", "boulder", "stone", "rocky"], "group": "Environment/Natural"},
    "stones": {"name": "Stones", "keywords": ["stone", "pebble", "cobblestone"], "group": "Environment/Natural"},
    "marble": {"name": "Marble", "keywords": ["marble", "marbled", "marble_tex", "marble_floor", "marble_wall"], "group": "Environment/Natural"},
    "ground": {"name": "Ground", "keywords": ["ground", "terrain", "floor_ground", "groundtex", "ground_dirt"], "group": "Environment/Natural"},
    "mountains": {"name": "Mountains", "keywords": ["mountain", "cliff", "peak", "hill"], "group": "Environment/Natural"},
    "sky": {"name": "Sky", "keywords": ["sky", "skybox", "horizon"], "group": "Environment/Natural"},
    "clouds": {"name": "Clouds", "keywords": ["cloud", "cloudy"], "group": "Environment/Natural"},
    "weather": {"name": "Weather Effects", "keywords": ["rain", "storm", "fog", "mist", "lightning"], "group": "Environment/Natural"}
}

# Environment - Man-made Categories
ENVIRONMENT_MANMADE = {
    "buildings": {"name": "Buildings", "keywords": ["building", "structure", "construction"], "group": "Environment/Man-made"},
    "houses": {"name": "Houses", "keywords": ["house", "home", "dwelling"], "group": "Environment/Man-made"},
    "walls_interior": {"name": "Walls (Interior)", "keywords": ["wall", "wallpaper", "interior"], "group": "Environment/Man-made"},
    "walls_exterior": {"name": "Walls (Exterior)", "keywords": ["wall", "exterior", "facade"], "group": "Environment/Man-made"},
    "floors": {"name": "Floors", "keywords": ["floor", "flooring", "tile", "carpet"], "group": "Environment/Man-made"},
    "ceilings": {"name": "Ceilings", "keywords": ["ceiling", "roof_interior"], "group": "Environment/Man-made"},
    "roofs": {"name": "Roofs", "keywords": ["roof", "rooftop", "shingle"], "group": "Environment/Man-made"},
    "roads": {"name": "Roads", "keywords": ["road", "street", "highway", "asphalt"], "group": "Environment/Man-made"},
    "paths": {"name": "Paths", "keywords": ["path", "pathway", "trail"], "group": "Environment/Man-made"},
    "sidewalks": {"name": "Sidewalks", "keywords": ["sidewalk", "pavement", "walkway"], "group": "Environment/Man-made"},
    "rails": {"name": "Rails", "keywords": ["rail", "track", "railroad"], "group": "Environment/Man-made"},
    "railings": {"name": "Railings", "keywords": ["railing", "handrail", "banister"], "group": "Environment/Man-made"},
    "fences": {"name": "Fences", "keywords": ["fence", "fencing"], "group": "Environment/Man-made"},
    "gates": {"name": "Gates", "keywords": ["gate", "door", "entrance"], "group": "Environment/Man-made"},
    "bridges": {"name": "Bridges", "keywords": ["bridge", "overpass"], "group": "Environment/Man-made"},
    "signs": {"name": "Signs", "keywords": ["sign", "signage"], "group": "Environment/Man-made"},
    "billboards": {"name": "Billboards", "keywords": ["billboard", "advertisement"], "group": "Environment/Man-made"},
    "posters": {"name": "Posters", "keywords": ["poster", "flyer"], "group": "Environment/Man-made"},
    "graffiti": {"name": "Graffiti", "keywords": ["graffiti", "spraypaint", "tag"], "group": "Environment/Man-made"},
    "decals": {"name": "Decals", "keywords": ["decal", "sticker", "marking"], "group": "Environment/Man-made"}
}

# UI/HUD Categories
UI_HUD = {
    "ui_elements": {"name": "UI Elements", "keywords": ["ui", "interface", "panel", "window"], "group": "UI/HUD"},
    "hud": {"name": "HUD", "keywords": ["hud", "overlay", "heads_up"], "group": "UI/HUD"},
    "menus": {"name": "Menus", "keywords": ["menu", "dropdown", "context"], "group": "UI/HUD"},
    "icons": {"name": "Icons", "keywords": ["icon", "symbol", "badge"], "group": "UI/HUD"},
    "buttons": {"name": "Buttons", "keywords": ["button", "btn"], "group": "UI/HUD"},
    "text": {"name": "Text", "keywords": ["text", "label", "caption"], "group": "UI/HUD"},
    "fonts": {"name": "Fonts", "keywords": ["font", "typeface", "letter"], "group": "UI/HUD"},
    "cursors": {"name": "Cursors", "keywords": ["cursor", "pointer", "crosshair"], "group": "UI/HUD"},
    "minimap": {"name": "Minimap", "keywords": ["minimap", "map", "radar"], "group": "UI/HUD"}
}

# Effects Categories
EFFECTS = {
    "particles": {"name": "Particles", "keywords": ["particle", "particlefx", "emitter"], "group": "Effects"},
    "fire": {"name": "Fire", "keywords": ["fire", "flame", "burning", "blaze", "inferno", "lava", "magma"], "group": "Effects"},
    "smoke": {"name": "Smoke", "keywords": ["smoke", "vapor", "steam", "haze", "smog"], "group": "Effects"},
    "explosions": {"name": "Explosions", "keywords": ["explosion", "blast", "boom", "detonate", "burst", "explode", "shockwave"], "group": "Effects"},
    "lightning": {"name": "Lightning", "keywords": ["lightning", "electric", "spark", "thunder", "volt", "electricity"], "group": "Effects"},
    "magic": {"name": "Magic Effects", "keywords": ["magic", "spell", "enchant", "mystical", "aura", "rune", "arcane"], "group": "Effects"},
    "lighting": {"name": "Lighting", "keywords": ["light", "lighting", "illumination", "lamp", "glow_light"], "group": "Effects"},
    "shadows": {"name": "Shadows", "keywords": ["shadow", "shade", "dark_shadow"], "group": "Effects"},
    "reflections": {"name": "Reflections", "keywords": ["reflection", "mirror", "reflect", "shiny", "glossy"], "group": "Effects"},
    "glow": {"name": "Glow", "keywords": ["glow", "glowing", "luminous", "radiant", "gleam"], "group": "Effects"},
    "energy": {"name": "Energy", "keywords": ["energy", "plasma", "beam", "laser", "power", "force_field"], "group": "Effects"},
    "debris": {"name": "Debris", "keywords": ["debris", "rubble", "wreckage", "shrapnel", "fragment"], "group": "Effects"}
}

# Objects/Props Categories
OBJECTS_PROPS = {
    "furniture": {"name": "Furniture", "keywords": ["furniture", "chair", "table", "desk", "bed", "sofa"], "group": "Objects/Props"},
    "decorations": {"name": "Decorations", "keywords": ["decoration", "ornament", "decor"], "group": "Objects/Props"},
    "containers": {"name": "Containers", "keywords": ["container", "box", "chest"], "group": "Objects/Props"},
    "crates": {"name": "Crates", "keywords": ["crate", "woodbox"], "group": "Objects/Props"},
    "barrels": {"name": "Barrels", "keywords": ["barrel", "drum", "keg"], "group": "Objects/Props"},
    "weapons": {"name": "Weapons", "keywords": ["weapon", "gun", "sword", "knife", "blade", "axe",
                "rifle", "pistol", "shotgun", "bow", "arrow", "staff", "wand", "spear", "mace",
                "dagger", "shield", "grenade", "rocket_launcher", "sniper", "smg", "assault"],
                "group": "Objects/Props"},
    "tools": {"name": "Tools", "keywords": ["tool", "hammer", "wrench", "screwdriver"], "group": "Objects/Props"},
    "items": {"name": "Items", "keywords": ["item", "object", "prop"], "group": "Objects/Props"},
    "food": {"name": "Food", "keywords": ["food", "meal", "snack"], "group": "Objects/Props"},
    "drinks": {"name": "Drinks", "keywords": ["drink", "beverage", "bottle"], "group": "Objects/Props"}
}

# Technical Textures Categories
TECHNICAL = {
    "normal_maps": {"name": "Normal Maps", "keywords": ["normal", "normalmap", "_n", "_normal"], "group": "Technical"},
    "specular_maps": {"name": "Specular Maps", "keywords": ["specular", "spec", "_s", "_specular"], "group": "Technical"},
    "bump_maps": {"name": "Bump Maps", "keywords": ["bump", "bumpmap", "_b"], "group": "Technical"},
    "displacement_maps": {"name": "Displacement Maps", "keywords": ["displacement", "disp", "_d"], "group": "Technical"},
    "alpha_masks": {"name": "Alpha Masks", "keywords": ["alpha", "mask", "_a", "_mask"], "group": "Technical"},
    "emission_maps": {"name": "Emission Maps", "keywords": ["emission", "emissive", "_e"], "group": "Technical"},
    "roughness_maps": {"name": "Roughness Maps", "keywords": ["roughness", "rough", "_r"], "group": "Technical"}
}

# Misc Categories
MISC = {
    "generic": {"name": "Generic", "keywords": ["generic", "misc", "other"], "group": "Misc"},
    "unclassified": {"name": "Unclassified", "keywords": [], "group": "Misc"}
}

# Combine all categories
ALL_CATEGORIES = {}
for category_group in [CHARACTER_ORGANIC, CLOTHING_WEARABLES, VEHICLES, 
                       ENVIRONMENT_NATURAL, ENVIRONMENT_MANMADE, UI_HUD, 
                       EFFECTS, OBJECTS_PROPS, TECHNICAL, MISC]:
    ALL_CATEGORIES.update(category_group)

# Category groups for organization
CATEGORY_GROUPS = {
    "Character/Organic": CHARACTER_ORGANIC,
    "Clothing/Wearables": CLOTHING_WEARABLES,
    "Vehicles": VEHICLES,
    "Environment/Natural": ENVIRONMENT_NATURAL,
    "Environment/Man-made": ENVIRONMENT_MANMADE,
    "UI/HUD": UI_HUD,
    "Effects": EFFECTS,
    "Objects/Props": OBJECTS_PROPS,
    "Technical": TECHNICAL,
    "Misc": MISC
}

def get_category_names():
    """Get list of all category names"""
    return list(ALL_CATEGORIES.keys())

def get_category_info(category_id):
    """Get information about a specific category"""
    return ALL_CATEGORIES.get(category_id, MISC["unclassified"])

def get_categories_by_group(group_name):
    """Get all categories in a specific group"""
    return CATEGORY_GROUPS.get(group_name, {})

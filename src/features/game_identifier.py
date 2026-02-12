"""
Game Identification System
Identifies PS2 games using Serial codes (SLUS/SCUS) and PCSX2 CRCs
Author: Dead On The Inside / JosephsDeadish
"""

import re
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Try to import YAML support for GameIndex.yaml
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    logger.warning("PyYAML not available. GameIndex.yaml support disabled.")


@dataclass
class GameInfo:
    """Information about an identified PS2 game."""
    serial: str = ""  # e.g., SLUS-12345
    crc: str = ""  # PCSX2 CRC hash
    title: str = ""  # Game title
    region: str = ""  # NTSC-U, PAL, NTSC-J, etc.
    confidence: float = 0.0  # Detection confidence (0-1)
    source: str = ""  # Detection source: serial, crc, folder, gameindex
    
    # Game-specific texture profile data
    texture_profile: Dict[str, Any] = field(default_factory=dict)


class GameIdentifier:
    """
    Identifies PS2 games from folder names, file paths, and CRC hashes.
    
    Supports:
    - Serial detection: SLUS-xxxxx, SCUS-xxxxx, SLES-xxxxx, etc.
    - CRC detection from folder names
    - GameIndex.yaml lookups (PCSX2 format)
    - Manual game database with texture profiles
    """
    
    # PS2 Serial patterns by region
    SERIAL_PATTERNS = {
        'NTSC-U': [
            r'SLUS[-_]?(\d{5})',  # Sony Licensed US
            r'SCUS[-_]?(\d{5})',  # Sony Computer Entertainment US
        ],
        'NTSC-J': [
            r'SLPS[-_]?(\d{5})',  # Sony Licensed Japan
            r'SCPS[-_]?(\d{5})',  # Sony Computer Entertainment Japan
            r'SLPM[-_]?(\d{5})',  # Sony Licensed PlayStation Japan
        ],
        'PAL': [
            r'SLES[-_]?(\d{5})',  # Sony Licensed Europe
            r'SCES[-_]?(\d{5})',  # Sony Computer Entertainment Europe
        ],
        'NTSC-K': [
            r'SLKA[-_]?(\d{5})',  # Sony Licensed Korea
            r'SCKA[-_]?(\d{5})',  # Sony Computer Entertainment Korea
        ]
    }
    
    # CRC pattern (8 hex characters)
    CRC_PATTERN = r'[0-9A-Fa-f]{8}'
    
    # Known games database with texture profile hints
    KNOWN_GAMES = {
        # God of War Series
        'SLUS-20917': {
            'title': 'God of War II',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'environment', 'ui'],
                'icon_shapes': 'square',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['kratos', 'olympus', 'weapon']
            }
        },
        'SLUS-20778': {
            'title': 'God of War',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'environment', 'ui'],
                'icon_shapes': 'square',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['kratos', 'blade']
            }
        },
        # Jak & Daxter Series
        'SLUS-20584': {
            'title': 'Jak 3',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'vehicles', 'environment'],
                'icon_shapes': 'circular',
                'atlas_layout': 'varied',
                'common_prefixes': ['jak', 'daxter', 'precursor']
            }
        },
        'SLUS-20065': {
            'title': 'Jak and Daxter: The Precursor Legacy',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'collectibles'],
                'icon_shapes': 'circular',
                'atlas_layout': 'varied',
                'common_prefixes': ['jak', 'daxter', 'eco']
            }
        },
        'SLUS-20472': {
            'title': 'Jak II',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'vehicles', 'weapons', 'environment'],
                'icon_shapes': 'circular',
                'atlas_layout': 'varied',
                'common_prefixes': ['jak', 'daxter', 'gun']
            }
        },
        # GTA Series
        'SLUS-20946': {
            'title': 'Grand Theft Auto: San Andreas',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['vehicles', 'characters', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['vehicle', 'ped', 'building', 'hud']
            }
        },
        # Kingdom Hearts Series
        'SLUS-20370': {
            'title': 'Kingdom Hearts',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'environment', 'ui', 'effects'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['sora', 'keyblade', 'heartless', 'disney']
            }
        },
        'SLUS-21005': {
            'title': 'Kingdom Hearts II',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'environment', 'ui', 'effects'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['sora', 'keyblade', 'nobody', 'org13']
            }
        },
        # Metal Gear Solid Series
        'SLUS-20144': {
            'title': 'Metal Gear Solid 2: Sons of Liberty',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'environment', 'ui'],
                'icon_shapes': 'rectangular',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['snake', 'raiden', 'weapon', 'codec']
            }
        },
        'SLUS-20565': {
            'title': 'Metal Gear Solid 3: Snake Eater',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'environment', 'ui', 'animals'],
                'icon_shapes': 'rectangular',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['snake', 'weapon', 'camo', 'food']
            }
        },
        # Final Fantasy Series
        'SLUS-20312': {
            'title': 'Final Fantasy X',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'magic', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['tidus', 'yuna', 'aeon', 'sphere']
            }
        },
        'SLUS-20672': {
            'title': 'Final Fantasy X-2',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'magic', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['yuna', 'rikku', 'paine', 'dressphere']
            }
        },
        'SLUS-20963': {
            'title': 'Final Fantasy XII',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'magic', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['vaan', 'ashe', 'esper', 'ivalice']
            }
        },
        # Ratchet & Clank Series
        'SLUS-20226': {
            'title': 'Ratchet & Clank',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'vehicles', 'environment'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['ratchet', 'clank', 'weapon', 'gadget']
            }
        },
        'SLUS-20638': {
            'title': 'Ratchet & Clank: Going Commando',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'vehicles', 'environment'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['ratchet', 'clank', 'weapon', 'gadget']
            }
        },
        'SLUS-20896': {
            'title': 'Ratchet & Clank: Up Your Arsenal',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'vehicles', 'environment'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['ratchet', 'clank', 'weapon', 'gadget']
            }
        },
        # Grand Theft Auto Series
        'SLUS-20552': {
            'title': 'Grand Theft Auto: Vice City',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['vehicles', 'characters', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['vehicle', 'ped', 'building', 'hud']
            }
        },
        'SLUS-20062': {
            'title': 'Grand Theft Auto III',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['vehicles', 'characters', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['vehicle', 'ped', 'building', 'hud']
            }
        },
        # Resident Evil Series
        'SLUS-20184': {
            'title': 'Resident Evil Code: Veronica X',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'enemies', 'environment', 'ui'],
                'icon_shapes': 'square',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['chris', 'claire', 'zombie', 'weapon']
            }
        },
        'SLUS-20770': {
            'title': 'Resident Evil 4',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'enemies', 'environment', 'ui'],
                'icon_shapes': 'square',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['leon', 'ashley', 'ganado', 'weapon']
            }
        },
        # Tekken Series
        'SLUS-20001': {
            'title': 'Tekken Tag Tournament',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'stages', 'ui'],
                'icon_shapes': 'square',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['char', 'stage', 'effect']
            }
        },
        'SLUS-20718': {
            'title': 'Tekken 4',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'stages', 'ui'],
                'icon_shapes': 'square',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['char', 'stage', 'effect']
            }
        },
        'SLUS-21059': {
            'title': 'Tekken 5',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'stages', 'ui'],
                'icon_shapes': 'square',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['char', 'stage', 'effect']
            }
        },
        # Sly Cooper Series
        'SLUS-20289': {
            'title': 'Sly Cooper and the Thievius Raccoonus',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'collectibles', 'ui'],
                'icon_shapes': 'circular',
                'atlas_layout': 'varied',
                'common_prefixes': ['sly', 'bentley', 'murray', 'enemy']
            }
        },
        'SLUS-20833': {
            'title': 'Sly 2: Band of Thieves',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'collectibles', 'ui'],
                'icon_shapes': 'circular',
                'atlas_layout': 'varied',
                'common_prefixes': ['sly', 'bentley', 'murray', 'enemy']
            }
        },
        'SLUS-21284': {
            'title': 'Sly 3: Honor Among Thieves',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'collectibles', 'ui'],
                'icon_shapes': 'circular',
                'atlas_layout': 'varied',
                'common_prefixes': ['sly', 'bentley', 'murray', 'enemy']
            }
        },
        # Shadow of the Colossus & ICO
        'SLUS-21287': {
            'title': 'Shadow of the Colossus',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'colossus', 'environment', 'effects'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['wander', 'agro', 'colossus', 'terrain']
            }
        },
        'SLUS-20067': {
            'title': 'ICO',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'effects'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['ico', 'yorda', 'castle', 'shadow']
            }
        },
        # Devil May Cry Series
        'SLUS-20216': {
            'title': 'Devil May Cry',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'enemies', 'environment', 'effects'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['dante', 'weapon', 'demon', 'effect']
            }
        },
        'SLUS-20484': {
            'title': 'Devil May Cry 2',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'enemies', 'environment', 'effects'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['dante', 'lucia', 'weapon', 'demon']
            }
        },
        'SLUS-20964': {
            'title': 'Devil May Cry 3: Dante\'s Awakening',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'enemies', 'environment', 'effects'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['dante', 'vergil', 'weapon', 'demon']
            }
        },
        # Dragon Quest VIII
        'SLUS-21207': {
            'title': 'Dragon Quest VIII: Journey of the Cursed King',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'monsters', 'items', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['hero', 'yangus', 'jessica', 'monster']
            }
        },
        # Persona Series
        'SLUS-21621': {
            'title': 'Shin Megami Tensei: Persona 3',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'personas', 'ui', 'environment'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['char', 'persona', 'shadow', 'menu']
            }
        },
        'SLUS-21782': {
            'title': 'Shin Megami Tensei: Persona 4',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'personas', 'ui', 'environment'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['char', 'persona', 'shadow', 'menu']
            }
        },
        # Tony Hawk Series
        'SLUS-20013': {
            'title': 'Tony Hawk\'s Pro Skater 3',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['skater', 'board', 'level', 'graffiti']
            }
        },
        'SLUS-20731': {
            'title': 'Tony Hawk\'s Underground',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['skater', 'board', 'level', 'graffiti']
            }
        },
        # Need for Speed Series
        'SLUS-20362': {
            'title': 'Need for Speed: Hot Pursuit 2',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['vehicles', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['car', 'track', 'effect', 'ui']
            }
        },
        'SLUS-20811': {
            'title': 'Need for Speed: Underground',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['vehicles', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['car', 'track', 'effect', 'ui']
            }
        },
        'SLUS-21065': {
            'title': 'Need for Speed: Underground 2',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['vehicles', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['car', 'track', 'effect', 'ui']
            }
        },
        # Burnout Series
        'SLUS-20497': {
            'title': 'Burnout 2: Point of Impact',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['vehicles', 'environment', 'effects', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['car', 'track', 'crash', 'effect']
            }
        },
        'SLUS-20966': {
            'title': 'Burnout 3: Takedown',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['vehicles', 'environment', 'effects', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['car', 'track', 'crash', 'effect']
            }
        },
        # SSX Series
        'SLUS-20011': {
            'title': 'SSX',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'effects', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['rider', 'board', 'mountain', 'snow']
            }
        },
        'SLUS-20326': {
            'title': 'SSX Tricky',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'effects', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['rider', 'board', 'mountain', 'snow']
            }
        },
        # Okami
        'SLUS-21410': {
            'title': 'Okami',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'effects', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['amaterasu', 'issun', 'brush', 'demon']
            }
        },
        # Silent Hill Series
        'SLUS-20228': {
            'title': 'Silent Hill 2',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'enemies', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['james', 'maria', 'monster', 'fog']
            }
        },
        'SLUS-20732': {
            'title': 'Silent Hill 3',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'enemies', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['heather', 'monster', 'otherworld']
            }
        },
        # Katamari Damacy
        'SLUS-21008': {
            'title': 'Katamari Damacy',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['objects', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['prince', 'king', 'object', 'star']
            }
        },
        'SLUS-21230': {
            'title': 'We Love Katamari',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['objects', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['prince', 'king', 'object', 'star']
            }
        },
        # Ace Combat Series
        'SLUS-20152': {
            'title': 'Ace Combat 04: Shattered Skies',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['aircraft', 'environment', 'weapons', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['plane', 'sky', 'missile', 'hud']
            }
        },
        'SLUS-20851': {
            'title': 'Ace Combat 5: The Unsung War',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['aircraft', 'environment', 'weapons', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['plane', 'sky', 'missile', 'hud']
            }
        },
        # Zone of the Enders
        'SLUS-20148': {
            'title': 'Zone of the Enders',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['mecha', 'environment', 'weapons', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['jehuty', 'orbital', 'weapon', 'hud']
            }
        },
        'SLUS-20680': {
            'title': 'Zone of the Enders: The 2nd Runner',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['mecha', 'environment', 'weapons', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['jehuty', 'orbital', 'weapon', 'hud']
            }
        },
        # Dark Cloud Series
        'SLUS-20041': {
            'title': 'Dark Cloud',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'items', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['toan', 'weapon', 'georama', 'monster']
            }
        },
        'SLUS-20357': {
            'title': 'Dark Chronicle',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'items', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['max', 'monica', 'weapon', 'georama']
            }
        },
        # Onimusha Series
        'SLUS-20018': {
            'title': 'Onimusha: Warlords',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'enemies', 'environment'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['samanosuke', 'demon', 'sword', 'magic']
            }
        },
        'SLUS-20419': {
            'title': 'Onimusha 2: Samurai\'s Destiny',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'enemies', 'environment'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['jubei', 'demon', 'sword', 'magic']
            }
        },
        'SLUS-20781': {
            'title': 'Onimusha 3: Demon Siege',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'enemies', 'environment'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['samanosuke', 'jacques', 'demon', 'sword']
            }
        },
        # Star Wars Series
        'SLUS-20044': {
            'title': 'Star Wars: Bounty Hunter',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'vehicles', 'environment'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['jango', 'bounty', 'weapon', 'ship']
            }
        },
        'SLUS-20389': {
            'title': 'Star Wars: Battlefront',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'vehicles', 'environment'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['trooper', 'vehicle', 'weapon', 'planet']
            }
        },
        'SLUS-21240': {
            'title': 'Star Wars: Battlefront II',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'vehicles', 'environment'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['trooper', 'vehicle', 'weapon', 'planet']
            }
        },
        # Crash Bandicoot Series
        'SLUS-20238': {
            'title': 'Crash Bandicoot: The Wrath of Cortex',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'collectibles'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['crash', 'cortex', 'wumpa', 'crate']
            }
        },
        # TimeSplitters Series
        'SLUS-20090': {
            'title': 'TimeSplitters',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['char', 'weapon', 'level', 'hud']
            }
        },
        'SLUS-20314': {
            'title': 'TimeSplitters 2',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['char', 'weapon', 'level', 'hud']
            }
        },
        'SLUS-21148': {
            'title': 'TimeSplitters: Future Perfect',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'weapons', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'power_of_two',
                'common_prefixes': ['char', 'weapon', 'level', 'hud']
            }
        },
        # The Simpsons Games
        'SLUS-20604': {
            'title': 'The Simpsons: Hit & Run',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'vehicles', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['homer', 'bart', 'car', 'springfield']
            }
        },
        # Bully
        'SLUS-21269': {
            'title': 'Bully',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'mixed',
                'common_prefixes': ['jimmy', 'student', 'school', 'town']
            }
        },
        # Psychonauts
        'SLUS-21120': {
            'title': 'Psychonauts',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'environment', 'effects', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['raz', 'brain', 'mental', 'figment']
            }
        },
        # Beyond Good & Evil
        'SLUS-20852': {
            'title': 'Beyond Good & Evil',
            'region': 'NTSC-U',
            'texture_profile': {
                'common_categories': ['character', 'vehicles', 'environment', 'ui'],
                'icon_shapes': 'varied',
                'atlas_layout': 'varied',
                'common_prefixes': ['jade', 'peyj', 'vehicle', 'hillys']
            }
        },
    }
    
    def __init__(self, gameindex_path: Optional[Path] = None):
        """
        Initialize game identifier.
        
        Args:
            gameindex_path: Optional path to GameIndex.yaml file
        """
        self.gameindex_path = gameindex_path
        self.gameindex_db: Dict[str, Dict[str, Any]] = {}
        
        if gameindex_path and gameindex_path.exists():
            self.load_gameindex(gameindex_path)
    
    def load_gameindex(self, path: Path) -> bool:
        """
        Load PCSX2 GameIndex.yaml file.
        
        Args:
            path: Path to GameIndex.yaml
            
        Returns:
            True if loaded successfully
        """
        if not HAS_YAML:
            logger.warning("PyYAML not available. Cannot load GameIndex.yaml")
            return False
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning("GameIndex.yaml is empty or invalid")
                return False
            
            # Parse GameIndex format
            # Format: Serial: {name: "Game Title", region: "NTSC-U", ...}
            self.gameindex_db = {}
            for serial, info in data.items():
                if isinstance(info, dict):
                    self.gameindex_db[serial] = info
            
            logger.info(f"Loaded {len(self.gameindex_db)} games from GameIndex.yaml")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load GameIndex.yaml: {e}", exc_info=True)
            return False
    
    def detect_serial_from_path(self, path: Path) -> Optional[Tuple[str, str]]:
        """
        Detect PS2 serial from folder or file path.
        
        Args:
            path: Path to check (folder or file)
            
        Returns:
            Tuple of (serial, region) if found, None otherwise
        """
        # Check the path string for serial patterns
        path_str = str(path)
        
        for region, patterns in self.SERIAL_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, path_str, re.IGNORECASE)
                if match:
                    # Extract serial code
                    prefix = pattern.split('(')[0].replace('[-_]?', '-')
                    number = match.group(1)
                    serial = f"{prefix}{number}".upper()
                    
                    logger.info(f"Detected serial: {serial} (Region: {region})")
                    return (serial, region)
        
        return None
    
    def detect_crc_from_path(self, path: Path) -> Optional[str]:
        """
        Detect CRC hash from folder or file path.
        
        Args:
            path: Path to check
            
        Returns:
            CRC string if found, None otherwise
        """
        path_str = str(path)
        
        # Look for 8-character hex strings (CRC format)
        matches = re.findall(self.CRC_PATTERN, path_str)
        
        if matches:
            # Return the first match (usually the game CRC)
            crc = matches[0].upper()
            logger.info(f"Detected CRC: {crc}")
            return crc
        
        return None
    
    def calculate_file_crc(self, file_path: Path, algorithm: str = 'crc32') -> str:
        """
        Calculate CRC hash of a file.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('crc32' or 'md5')
            
        Returns:
            CRC hash string
        """
        try:
            if algorithm == 'crc32':
                import zlib
                with open(file_path, 'rb') as f:
                    crc = 0
                    while chunk := f.read(8192):
                        crc = zlib.crc32(chunk, crc)
                return f"{crc & 0xFFFFFFFF:08X}"
            
            elif algorithm == 'md5':
                md5 = hashlib.md5()
                with open(file_path, 'rb') as f:
                    while chunk := f.read(8192):
                        md5.update(chunk)
                return md5.hexdigest()[:8].upper()
            
        except Exception as e:
            logger.error(f"Failed to calculate CRC for {file_path}: {e}")
            return ""
    
    def lookup_by_serial(self, serial: str) -> Optional[GameInfo]:
        """
        Look up game info by serial code.
        
        Args:
            serial: PS2 serial code (e.g., SLUS-12345)
            
        Returns:
            GameInfo if found, None otherwise
        """
        # Normalize serial format
        serial = serial.upper().replace('_', '-')
        
        # Check local database first
        if serial in self.KNOWN_GAMES:
            game_data = self.KNOWN_GAMES[serial]
            return GameInfo(
                serial=serial,
                title=game_data['title'],
                region=game_data['region'],
                texture_profile=game_data.get('texture_profile', {}),
                confidence=1.0,
                source='known_database'
            )
        
        # Check GameIndex.yaml
        if serial in self.gameindex_db:
            game_data = self.gameindex_db[serial]
            return GameInfo(
                serial=serial,
                title=game_data.get('name', 'Unknown'),
                region=game_data.get('region', 'Unknown'),
                confidence=0.9,
                source='gameindex'
            )
        
        return None
    
    def lookup_by_crc(self, crc: str) -> Optional[GameInfo]:
        """
        Look up game info by CRC hash.
        
        Args:
            crc: CRC hash string
            
        Returns:
            GameInfo if found, None otherwise
        """
        crc = crc.upper()
        
        # Search GameIndex.yaml for CRC
        if self.gameindex_db:
            for serial, game_data in self.gameindex_db.items():
                # Check if CRC is in the game data
                if isinstance(game_data, dict):
                    game_crcs = game_data.get('crc', [])
                    if isinstance(game_crcs, str):
                        game_crcs = [game_crcs]
                    
                    if crc in [c.upper() for c in game_crcs]:
                        return GameInfo(
                            serial=serial,
                            crc=crc,
                            title=game_data.get('name', 'Unknown'),
                            region=game_data.get('region', 'Unknown'),
                            confidence=0.95,
                            source='gameindex_crc'
                        )
        
        return None
    
    def identify_game(self, path: Path, scan_files: bool = False) -> Optional[GameInfo]:
        """
        Identify game from a directory path.
        
        Args:
            path: Directory path to scan
            scan_files: If True, also scan files for additional clues
            
        Returns:
            GameInfo if identified, None otherwise
        """
        game_info = None
        best_confidence = 0.0
        
        # Method 1: Detect serial from path
        serial_result = self.detect_serial_from_path(path)
        if serial_result:
            serial, region = serial_result
            game_info = self.lookup_by_serial(serial)
            if game_info:
                best_confidence = game_info.confidence
        
        # Method 2: Detect CRC from path
        crc = self.detect_crc_from_path(path)
        if crc:
            crc_info = self.lookup_by_crc(crc)
            if crc_info and crc_info.confidence > best_confidence:
                game_info = crc_info
                best_confidence = crc_info.confidence
        
        # Method 3: Scan files if requested (optional)
        if scan_files and path.is_dir():
            # Look for common PS2 files like SYSTEM.CNF
            system_cnf = path / "SYSTEM.CNF"
            if system_cnf.exists():
                try:
                    with open(system_cnf, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # SYSTEM.CNF contains BOOT2 = cdrom0:\SLUS_123.45;1
                        serial_match = re.search(r'BOOT2?\s*=.*?([A-Z]{4}[_-]?\d{3}\.\d{2})', content, re.IGNORECASE)
                        if serial_match:
                            serial = serial_match.group(1).replace('_', '-').replace('.', '')
                            info = self.lookup_by_serial(serial)
                            if info and info.confidence > best_confidence:
                                game_info = info
                                best_confidence = info.confidence
                except Exception as e:
                    logger.debug(f"Failed to read SYSTEM.CNF: {e}")
        
        if game_info:
            logger.info(
                f"Identified game: {game_info.title} "
                f"(Serial: {game_info.serial}, "
                f"Confidence: {game_info.confidence:.0%}, "
                f"Source: {game_info.source})"
            )
        else:
            logger.info("No game identified from path")
        
        return game_info
    
    def get_texture_profile(self, game_info: GameInfo) -> Dict[str, Any]:
        """
        Get texture profile for a game.
        
        Args:
            game_info: Identified game information
            
        Returns:
            Dictionary with texture profile settings
        """
        if game_info.texture_profile:
            return game_info.texture_profile
        
        # Return default profile
        return {
            'common_categories': ['character', 'environment', 'ui', 'effects'],
            'icon_shapes': 'varied',
            'atlas_layout': 'varied',
            'common_prefixes': []
        }
    
    def add_known_game(
        self,
        serial: str,
        title: str,
        region: str = 'NTSC-U',
        texture_profile: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a game to the known games database.
        
        Args:
            serial: PS2 serial code
            title: Game title
            region: Game region
            texture_profile: Optional texture profile data
            
        Returns:
            True if added successfully
        """
        try:
            serial = serial.upper().replace('_', '-')
            
            self.KNOWN_GAMES[serial] = {
                'title': title,
                'region': region,
                'texture_profile': texture_profile or {}
            }
            
            logger.info(f"Added known game: {serial} - {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add known game: {e}")
            return False
    
    def get_all_known_games(self) -> List[Dict[str, str]]:
        """
        Get list of all known games.
        
        Returns:
            List of dictionaries with game info (serial, title, region)
        """
        games = []
        for serial, info in self.KNOWN_GAMES.items():
            games.append({
                'serial': serial,
                'title': info['title'],
                'region': info['region']
            })
        
        # Sort by title
        games.sort(key=lambda x: x['title'])
        return games

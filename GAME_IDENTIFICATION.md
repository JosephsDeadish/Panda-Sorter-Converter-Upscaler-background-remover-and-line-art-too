# Game Identification & Per-Game Texture Profiles

## Overview

This feature automatically identifies PS2 games and applies game-specific texture classification profiles to improve sorting accuracy. The system detects games based on serial codes, CRC hashes, and folder names, then uses customized keyword matching for each game.

## Features

### 1. Automatic Game Detection

The system can identify PS2 games using multiple methods:

- **Serial Detection**: Detects standard PS2 serial codes in folder paths
  - NTSC-U: SLUS-xxxxx, SCUS-xxxxx
  - PAL: SLES-xxxxx, SCES-xxxxx
  - NTSC-J: SLPS-xxxxx, SCPS-xxxxx, SLPM-xxxxx
  - NTSC-K: SLKA-xxxxx, SCKA-xxxxx

- **CRC Detection**: Identifies 8-character hex CRC hashes in folder names
  - Commonly used by PCSX2 texture dumping

- **GameIndex.yaml Support**: Can load game database from PCSX2's GameIndex.yaml
  - Maps CRC hashes to game titles and metadata

- **SYSTEM.CNF Parsing**: Reads PS2 disc metadata files when available

### 2. Game-Specific Texture Profiles

Each game profile includes:

- **Common Categories**: Texture categories specific to that game
- **Common Prefixes**: Game-specific filename prefixes (e.g., "kratos", "blade")
- **Icon Shapes**: UI icon conventions (square, circular, rectangular, varied)
- **Atlas Layout**: Texture atlas organization (power_of_two, varied, mixed)
- **Prefix Mappings**: Optional explicit prefix-to-category mappings

### 3. Enhanced Classification

When a game is identified:

1. Game-specific keywords are prioritized over generic patterns
2. Prefix matching uses intelligent category inference
3. Classification confidence increases for game-specific textures
4. Custom categories relevant to the game are highlighted

## Supported Games

The system includes built-in profiles for 10+ popular PS2 games:

### God of War Series
- **God of War** (SLUS-20778)
- **God of War II** (SLUS-20917)

### Jak & Daxter Series
- **Jak and Daxter: The Precursor Legacy** (SLUS-20065)
- **Jak II** (SLUS-20472)
- **Jak 3** (SLUS-20584)

### Kingdom Hearts Series
- **Kingdom Hearts** (SLUS-20370)
- **Kingdom Hearts II** (SLUS-21005)

### Metal Gear Solid Series
- **Metal Gear Solid 2: Sons of Liberty** (SLUS-20144)
- **Metal Gear Solid 3: Snake Eater** (SLUS-20565)

### Final Fantasy Series
- **Final Fantasy X** (SLUS-20312)
- **Final Fantasy X-2** (SLUS-20672)
- **Final Fantasy XII** (SLUS-20963)

### Other Popular Games
- **Grand Theft Auto: San Andreas** (SLUS-20946)
- **Ratchet & Clank** (SLUS-20226)

## Usage

### Automatic Detection

1. Open the **File Browser** tab
2. Click **Browse** and select a directory containing PS2 textures
3. The system automatically detects the game from folder names
4. Game information is displayed in the browser header

Example folder paths that will be detected:
```
/textures/SLUS-20917/dump
/PCSX2/textures/God_of_War_II_SLUS-20917
/games/ABCD1234/textures
```

### Manual Game Selection

1. Open the **File Browser** tab
2. Click **🎮 Select Game** button
3. Choose a game from the list of known games
4. The game profile is immediately applied

### During Sorting

1. Browse to or manually select a game in the File Browser
2. Set input/output directories on the Sorting tab
3. Click **Start Sorting**
4. The game-specific profile is automatically applied during classification

## For Developers

### Adding New Games

To add a new game to the database, edit `src/features/game_identifier.py`:

```python
'SLUS-XXXXX': {
    'title': 'Game Title',
    'region': 'NTSC-U',  # or PAL, NTSC-J, etc.
    'texture_profile': {
        'common_categories': ['character', 'weapons', 'environment', 'ui'],
        'icon_shapes': 'square',  # square, circular, rectangular, varied
        'atlas_layout': 'power_of_two',  # power_of_two, varied, mixed
        'common_prefixes': ['hero', 'enemy', 'item'],
        # Optional: explicit prefix-to-category mappings
        'prefix_mappings': {
            'hero': 'character',
            'weapon': 'weapons',
            'ui': 'ui'
        }
    }
}
```

### Texture Profile Structure

A texture profile is a dictionary with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `common_categories` | List[str] | Categories commonly found in this game |
| `icon_shapes` | str | UI icon shape convention (square/circular/rectangular/varied) |
| `atlas_layout` | str | Texture atlas organization (power_of_two/varied/mixed) |
| `common_prefixes` | List[str] | Game-specific filename prefixes |
| `prefix_mappings` | Dict[str, str] | Optional explicit prefix→category mappings |

### Using GameIndex.yaml

To use PCSX2's GameIndex.yaml:

```python
from src.features.game_identifier import GameIdentifier
from pathlib import Path

# Load GameIndex.yaml
gameindex_path = Path("/path/to/GameIndex.yaml")
identifier = GameIdentifier(gameindex_path=gameindex_path)

# Identify game
game_info = identifier.identify_game(Path("/textures/game_folder"))
```

### API Reference

#### GameIdentifier

```python
class GameIdentifier:
    def __init__(self, gameindex_path: Optional[Path] = None)
    
    def detect_serial_from_path(self, path: Path) -> Optional[Tuple[str, str]]
    def detect_crc_from_path(self, path: Path) -> Optional[str]
    def lookup_by_serial(self, serial: str) -> Optional[GameInfo]
    def lookup_by_crc(self, crc: str) -> Optional[GameInfo]
    def identify_game(self, path: Path, scan_files: bool = False) -> Optional[GameInfo]
    def get_texture_profile(self, game_info: GameInfo) -> Dict[str, Any]
    def add_known_game(self, serial: str, title: str, region: str, texture_profile: Dict) -> bool
    def get_all_known_games(self) -> List[Dict[str, str]]
```

#### GameInfo

```python
@dataclass
class GameInfo:
    serial: str           # PS2 serial (e.g., SLUS-20917)
    crc: str             # CRC hash
    title: str           # Game title
    region: str          # NTSC-U, PAL, NTSC-J, etc.
    confidence: float    # Detection confidence (0.0-1.0)
    source: str          # Detection source (serial/crc/gameindex/manual)
    texture_profile: Dict[str, Any]  # Game-specific profile
```

#### TextureClassifier

```python
class TextureClassifier:
    def __init__(self, config=None, model_manager=None, game_profile=None)
    
    def set_game_profile(self, game_profile: Dict[str, Any])
    def classify_texture(self, file_path: Path, use_image_analysis: bool = True) -> Tuple[str, float]
```

## Technical Details

### Detection Priority

When identifying a game, the system uses this priority order:

1. **Serial Detection** (confidence: 1.0 for known games, 0.9 for GameIndex)
2. **CRC Lookup** (confidence: 0.95)
3. **SYSTEM.CNF Parsing** (confidence: 0.9)
4. **Manual Selection** (confidence: 1.0)

### Classification Priority

During texture classification, keyword matching priority is:

1. **Game-specific prefix mappings** (confidence boost: 0.95-1.0)
2. **Game-specific prefixes with inferred categories** (confidence boost: 0.90-0.95)
3. **Standard category keywords** (confidence: variable)
4. **AI model predictions** (confidence: model-dependent)

### Performance

- Game detection: < 10ms (without file scanning)
- Profile application: Instantaneous (affects classification only)
- Memory overhead: ~1KB per game profile
- No impact on classification speed

## Troubleshooting

### Game Not Detected

**Problem**: Directory browsing doesn't detect the game

**Solutions**:
1. Ensure folder name includes the serial code (e.g., SLUS-20917)
2. Try manual game selection with the **🎮 Select Game** button
3. Check if the game is in the known games database
4. Verify serial format matches PS2 standards

### Wrong Game Detected

**Problem**: System identifies the wrong game

**Solutions**:
1. Use manual game selection to override
2. Rename folder to include correct serial code
3. Check for CRC conflicts in folder name

### Profile Not Applied

**Problem**: Classification doesn't use game-specific profile

**Solutions**:
1. Verify game info is displayed in File Browser
2. Check that game has a texture_profile in the database
3. Ensure you start sorting after game detection
4. Review logs for profile application messages

## Examples

### Example 1: God of War II Textures

```
Folder: /textures/SLUS-20917/dump/

Detected:
- Serial: SLUS-20917
- Game: God of War II
- Region: NTSC-U

Profile Applied:
- Common prefixes: kratos, olympus, weapon
- Categories: character, weapons, environment, ui
- Icon shape: square
- Atlas layout: power_of_two

Files:
- kratos_body.dds → character (high confidence)
- olympus_sky.png → environment (high confidence)
- weapon_blade.dds → weapons (high confidence)
```

### Example 2: Kingdom Hearts Textures

```
Folder: /PCSX2/textures/Kingdom_Hearts_SLUS-20370/

Detected:
- Serial: SLUS-20370
- Game: Kingdom Hearts
- Region: NTSC-U

Profile Applied:
- Common prefixes: sora, keyblade, heartless, disney
- Categories: character, weapons, environment, ui, effects
- Icon shape: varied
- Atlas layout: varied

Files:
- sora_face.png → character (high confidence)
- keyblade_kingdom.dds → weapons (high confidence)
- heartless_shadow.png → character (high confidence)
```

## Future Enhancements

Planned improvements for this feature:

1. **Texture Hash Database**: Per-game texture fingerprinting for exact matching
2. **GameIndex Auto-Update**: Automatic download of latest PCSX2 GameIndex.yaml
3. **Profile Import/Export**: Share custom game profiles with other users
4. **Community Profiles**: Repository of community-contributed game profiles
5. **Auto-Learning**: Machine learning to improve profiles based on usage
6. **Redump Database**: Integration with Redump.org database for additional metadata

## Credits

- Game serial database structure based on PS2 Redump naming conventions
- GameIndex.yaml format compatible with PCSX2 emulator
- Implementation by: Dead On The Inside / JosephsDeadish

## License

This feature is part of the Game Texture Sorter project.
See main README.md for license information.

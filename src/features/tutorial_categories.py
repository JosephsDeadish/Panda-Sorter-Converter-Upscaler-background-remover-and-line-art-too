"""
Tutorial Categories - Organized tutorial system
Provides categorized tutorials for different feature areas
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class TutorialCategory(Enum):
    """Categories for organizing tutorials"""
    GETTING_STARTED = "getting_started"
    BASIC_TOOLS = "basic_tools"
    ADVANCED_TOOLS = "advanced_tools"
    AI_FEATURES = "ai_features"
    CUSTOMIZATION = "customization"
    PANDA_FEATURES = "panda_features"
    TROUBLESHOOTING = "troubleshooting"

@dataclass
class CategorizedTutorialStep:
    """A tutorial step with category information"""
    title: str
    message: str
    category: TutorialCategory
    target_widget: Optional[str] = None
    highlight_mode: str = "border"
    arrow_direction: Optional[str] = None
    show_back: bool = True
    show_skip: bool = True
    button_text: str = "Next"
    celebration: bool = False
    order: int = 0  # Order within category

def get_categorized_tutorials() -> dict:
    """Get all tutorials organized by category"""
    
    tutorials = {
        TutorialCategory.GETTING_STARTED: [
            CategorizedTutorialStep(
                title="Welcome to Panda Sorter Converter Upscaler! 🐼",
                message=(
                    "Welcome! This quick tutorial will show you how to use the application.\n\n"
                    "Panda Sorter Converter Upscaler helps you organize, convert, upscale and process images "
                    "with intelligent AI classification, upscaling, background removal and line art conversion.\n\n"
                    "Let's get started!"
                ),
                category=TutorialCategory.GETTING_STARTED,
                target_widget=None,
                show_back=False,
                show_skip=True,
                celebration=False,
                order=0
            ),
            CategorizedTutorialStep(
                title="Step 1: Select Input Directory",
                message=(
                    "First, you need to select the folder containing your texture files.\n\n"
                    "Click the 'Browse' button next to 'Input Directory' to choose "
                    "the folder with your unsorted textures.\n\n"
                    "Supported formats: DDS, PNG, JPG, BMP, TGA"
                ),
                category=TutorialCategory.GETTING_STARTED,
                target_widget="input_browse",
                highlight_mode="border",
                arrow_direction="down",
                order=1
            ),
            CategorizedTutorialStep(
                title="Step 2: Organization Style",
                message=(
                    "Choose how you want your textures organized:\n\n"
                    "• By Category: Groups by type (UI, Characters, etc.)\n"
                    "• By Size: Organizes by texture dimensions\n"
                    "• Flat: Keeps everything in one folder\n"
                    "• Hierarchical: Creates nested category folders\n\n"
                    "The default 'By Category' works great for most users!"
                ),
                category=TutorialCategory.GETTING_STARTED,
                target_widget="style_dropdown",
                highlight_mode="border",
                arrow_direction="left",
                order=2
            ),
        ],
        
        TutorialCategory.BASIC_TOOLS: [
            CategorizedTutorialStep(
                title="Texture Sorting Basics",
                message=(
                    "Ready to organize your textures?\n\n"
                    "1. Make sure input and output directories are set\n"
                    "2. Choose your preferred organization style\n"
                    "3. Click 'Start Sorting' to begin!\n\n"
                    "The app will:\n"
                    "• Scan all texture files\n"
                    "• Classify them automatically\n"
                    "• Organize them into folders\n"
                    "• Show progress in real-time"
                ),
                category=TutorialCategory.BASIC_TOOLS,
                target_widget="start_button",
                highlight_mode="border",
                arrow_direction="down",
                order=0
            ),
            CategorizedTutorialStep(
                title="Categories & LOD Detection",
                message=(
                    "The app automatically detects texture types:\n\n"
                    "• UI Elements (buttons, icons)\n"
                    "• Characters (player models, NPCs)\n"
                    "• Environment (terrain, buildings)\n"
                    "• Effects (particles, lighting)\n\n"
                    "LOD Detection groups textures by detail level:\n"
                    "LOD0 (highest detail) → LOD1 → LOD2 → LOD3 (lowest detail)"
                ),
                category=TutorialCategory.BASIC_TOOLS,
                target_widget="detect_lods",
                highlight_mode="border",
                arrow_direction="up",
                order=1
            ),
        ],
        
        TutorialCategory.ADVANCED_TOOLS: [
            CategorizedTutorialStep(
                title="Image Upscaler Tool 🔍",
                message=(
                    "Need bigger textures? The Image Upscaler has you covered!\n\n"
                    "Features:\n"
                    "• Batch upscale with 6 quality filters (Lanczos, Bicubic, etc.)\n"
                    "• Scale 2x, 4x, or 8x — preserves alpha channels\n"
                    "• Import from and export to ZIP archives\n"
                    "• Live before/after preview\n"
                    "• Send results straight to the Sort Textures tab\n\n"
                    "Find it under 🔧 Tools → 🔍 Image Upscaler"
                ),
                category=TutorialCategory.ADVANCED_TOOLS,
                target_widget=None,
                celebration=False,
                order=0
            ),
            CategorizedTutorialStep(
                title="Batch Rename Tool 📝",
                message=(
                    "Rename multiple files with powerful patterns!\n\n"
                    "Features:\n"
                    "• Date-based naming (creation, modification, EXIF)\n"
                    "• Resolution-based naming (1024x1024_texture.png)\n"
                    "• Custom templates with variables\n"
                    "• Metadata injection (copyright, author)\n"
                    "• Preview before renaming\n"
                    "• Undo support\n\n"
                    "Find it under 🔧 Tools → 📝 Batch Rename"
                ),
                category=TutorialCategory.ADVANCED_TOOLS,
                target_widget=None,
                celebration=False,
                order=1
            ),
            CategorizedTutorialStep(
                title="Color Correction Tool 🎨",
                message=(
                    "Adjust colors and enhance your images!\n\n"
                    "Features:\n"
                    "• Auto white balance\n"
                    "• Exposure correction (-3 to +3 EV)\n"
                    "• Vibrance and clarity enhancement\n"
                    "• LUT support (.cube files)\n"
                    "• Adjustable LUT strength\n"
                    "• Live before/after preview\n\n"
                    "Find it under 🔧 Tools → 🎨 Color Correction"
                ),
                category=TutorialCategory.ADVANCED_TOOLS,
                target_widget=None,
                celebration=False,
                order=2
            ),
            CategorizedTutorialStep(
                title="Image Repair Tool 🔧",
                message=(
                    "Fix corrupted or damaged image files!\n\n"
                    "Features:\n"
                    "• PNG repair (chunk validation, CRC fixing)\n"
                    "• JPEG repair (marker validation, EOI fixing)\n"
                    "• Diagnostic reports\n"
                    "• Partial image recovery\n"
                    "• Batch repair support\n\n"
                    "Find it under 🔧 Tools → 🔧 Image Repair"
                ),
                category=TutorialCategory.ADVANCED_TOOLS,
                target_widget=None,
                celebration=False,
                order=3
            ),
        ],
        
        TutorialCategory.AI_FEATURES: [
            CategorizedTutorialStep(
                title="AI Learning & Feedback 🧠",
                message=(
                    "The AI gets smarter the more you use it!\n\n"
                    "• Give 👎 feedback on bad suggestions to improve accuracy\n"
                    "• The AI learns when you change its category picks\n"
                    "• Export/Import training data to share with others\n"
                    "• Each correction makes future sorting better\n\n"
                    "Find AI settings in the Settings → AI tab"
                ),
                category=TutorialCategory.AI_FEATURES,
                target_widget=None,
                celebration=False,
                order=0
            ),
            CategorizedTutorialStep(
                title="Background Remover 🎭",
                message=(
                    "Remove backgrounds with AI-powered tools!\n\n"
                    "Features:\n"
                    "• 8 alpha presets (PS2, Gaming, Art, Photography, etc.)\n"
                    "• Object remover mode with 4 selection tools\n"
                    "• Brush with opacity control (10-100%)\n"
                    "• Rectangle, Lasso, Magic Wand selection\n"
                    "• Undo/redo support\n"
                    "• Live preview\n\n"
                    "Find it under 🔧 Tools → 🎭 Background Remover"
                ),
                category=TutorialCategory.AI_FEATURES,
                target_widget=None,
                celebration=False,
                order=1
            ),
        ],
        
        TutorialCategory.CUSTOMIZATION: [
            CategorizedTutorialStep(
                title="Sound & Audio Settings 🔊",
                message=(
                    "Customize every sound in the app!\n\n"
                    "• Choose different sounds for system events (clicks, alerts)\n"
                    "• Select unique sounds for each panda action\n"
                    "• Purchase premium sound packs in the Shop\n"
                    "• Test sounds before applying them\n\n"
                    "Access via Settings → Customization → 🔊 Sound tab"
                ),
                category=TutorialCategory.CUSTOMIZATION,
                target_widget=None,
                celebration=False,
                order=0
            ),
        ],
        
        TutorialCategory.PANDA_FEATURES: [
            CategorizedTutorialStep(
                title="Meet Your Panda Companion! 🐼",
                message=(
                    "Your panda companion is always here!\n\n"
                    "Your panda features:\n"
                    "• Animated panda companion on your screen\n"
                    "• Fun (and sometimes vulgar) tooltips\n"
                    "• Easter eggs and achievements\n"
                    "• Mood-based reactions\n\n"
                    "Customize your panda in Settings → Customization"
                ),
                category=TutorialCategory.PANDA_FEATURES,
                target_widget=None,
                celebration=False,
                order=0
            ),
        ],
        
        TutorialCategory.TROUBLESHOOTING: [
            CategorizedTutorialStep(
                title="Getting Help ❓",
                message=(
                    "Need assistance? We've got you covered!\n\n"
                    "• Press F1 anytime for context-sensitive help\n"
                    "• Check the FAQ in the documentation\n"
                    "• Use the Help menu for specific topics\n"
                    "• Performance Dashboard shows system metrics\n"
                    "• Auto Backup protects your work\n\n"
                    "Remember: The app auto-saves and has crash recovery!"
                ),
                category=TutorialCategory.TROUBLESHOOTING,
                target_widget=None,
                celebration=False,
                order=0
            ),
        ],
    }
    
    return tutorials

def get_category_description(category: TutorialCategory) -> str:
    """Get a description for each tutorial category"""
    descriptions = {
        TutorialCategory.GETTING_STARTED: "Learn the basics of texture sorting",
        TutorialCategory.BASIC_TOOLS: "Essential tools for texture management",
        TutorialCategory.ADVANCED_TOOLS: "Powerful tools for advanced workflows",
        TutorialCategory.AI_FEATURES: "AI-powered image processing features",
        TutorialCategory.CUSTOMIZATION: "Personalize your experience",
        TutorialCategory.PANDA_FEATURES: "All about your panda companion",
        TutorialCategory.TROUBLESHOOTING: "Solutions and help resources",
    }
    return descriptions.get(category, "")

def get_tutorial_sequence() -> List[CategorizedTutorialStep]:
    """Get all tutorials in a flat sequence, ordered by category and order"""
    tutorials_dict = get_categorized_tutorials()
    all_steps = []
    
    # Define category order for the sequence
    category_order = [
        TutorialCategory.GETTING_STARTED,
        TutorialCategory.BASIC_TOOLS,
        TutorialCategory.PANDA_FEATURES,
        TutorialCategory.ADVANCED_TOOLS,
        TutorialCategory.AI_FEATURES,
        TutorialCategory.CUSTOMIZATION,
        TutorialCategory.TROUBLESHOOTING,
    ]
    
    for category in category_order:
        if category in tutorials_dict:
            steps = sorted(tutorials_dict[category], key=lambda x: x.order)
            all_steps.extend(steps)
    
    # Add final completion step
    all_steps.append(
        CategorizedTutorialStep(
            title="You're All Set! 🎉",
            message=(
                "Congratulations! You're ready to start sorting textures!\n\n"
                "Quick Tips:\n"
                "• Press F1 anytime for context-sensitive help\n"
                "• Check the Achievements tab for fun challenges\n"
                "• Use the Image Upscaler to enhance low-res textures\n"
                "• Customize sounds in Settings → Sound\n"
                "• Give AI feedback to improve sorting accuracy\n"
                "• Use the Notepad tab for project notes\n\n"
                "Need help? Click the ❓ button in the menu bar!\n\n"
                "Happy sorting! 🐼"
            ),
            category=TutorialCategory.GETTING_STARTED,
            target_widget=None,
            show_back=True,
            show_skip=False,
            button_text="Finish",
            celebration=True,
            order=999
        )
    )
    
    return all_steps

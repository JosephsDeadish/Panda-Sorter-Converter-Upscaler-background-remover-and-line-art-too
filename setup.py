#!/usr/bin/env python3
"""
Setup script for Game Texture Sorter
Author: Dead On The Inside / JosephsDeadish

This allows installation as a Python package with:
    pip install .
    pip install -e .  # For development (editable mode)
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
README_PATH = Path(__file__).parent / 'README.md'
if README_PATH.exists():
    with open(README_PATH, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = 'Game Texture Sorter - Automatic texture classification and sorting'

# Application metadata
APP_NAME = 'game-texture-sorter'
APP_VERSION = '1.0.0'
APP_AUTHOR = 'Dead On The Inside / JosephsDeadish'
APP_EMAIL = 'josephsdeadish@example.com'  # Update with actual email if available

# Core dependencies (always required)
INSTALL_REQUIRES = [
    # UI Framework - Qt/PyQt6 (REQUIRED - ONLY SUPPORTED UI)
    'PyQt6>=6.6.0',  # Qt6 framework for UI (tabs, buttons, layouts, events)
    'PyOpenGL>=3.1.7',  # OpenGL for 3D rendering (panda, skeletal animations)
    'PyOpenGL-accelerate>=3.1.7',  # Performance optimizations for PyOpenGL
    
    # Image Processing
    'pillow>=10.0.0',  # NOTE: 12.1.1+ recommended for latest security fixes
    'darkdetect>=0.8.0',
    'opencv-python>=4.8.1.78',  # >= 4.8.1.78 for libwebp CVE fix
    'numpy>=1.24.0',
    'scikit-image>=0.21.0',
    
    # Machine Learning
    'scikit-learn>=1.3.0',
    
    # File Operations
    'send2trash>=1.8.2',
    'watchdog>=3.0.0',
    
    # Performance
    'psutil>=5.9.5',
    'tqdm>=4.66.0',
    'xxhash>=3.4.0',
    
    # Archive Support
    'py7zr>=0.20.1',
    'rarfile>=4.0',
    
    # Hotkeys
    'pynput>=1.7.6',
    
    # Utilities
    'colorama>=0.4.6',
    'pyyaml>=6.0',
    'requests>=2.31.0',
    
    # Image Metadata
    'piexif>=1.1.3',
]

# Optional dependencies organized by feature
EXTRAS_REQUIRE = {
    # SVG support (requires system cairo library on Linux)
    'svg': [
        'cairosvg>=2.7.0',
        'cairocffi>=1.6.0',
    ],
    
    # Lightweight AI inference
    'onnx': [
        'onnxruntime>=1.16.0',
    ],
    
    # Advanced deep learning features
    'ml': [
        'torch>=2.6.0',
        'torchvision>=0.21.0',
        'transformers>=4.48.0',  # >= 4.48.0 for security fixes
        'timm>=0.9.0',
        'open-clip-torch>=2.20.0',
        'onnx>=1.14.0',  # ONNX model format - needed for PyTorch model export
        'scipy>=1.10.0',  # Scientific computing (fallback for alpha correction filters)
    ],
    
    # Vector similarity search
    'search': [
        'faiss-cpu>=1.7.4',
        'chromadb>=0.4.0',
        'annoy>=1.17.0',
    ],
    
    # GPU-accelerated search (alternative to faiss-cpu)
    'search-gpu': [
        'faiss-gpu>=1.7.4',
        'chromadb>=0.4.0',
        'annoy>=1.17.0',
    ],
    
    # Image upscaling and super-resolution
    'upscaling': [
        'basicsr>=1.4.2',
        'realesrgan>=0.3.0',
    ],
    
    # AI background removal
    'background-removal': [
        'rembg[cpu]>=2.0.50',
    ],
    
    # OCR support (requires tesseract-ocr system package)
    'ocr': [
        'pytesseract>=0.3.10',
    ],
    
    # Native Rust acceleration (requires Rust toolchain + maturin)
    'native': [
        'maturin>=1.0.0',
    ],
    
    # Build and packaging
    'build': [
        'pyinstaller>=6.0.0',  # >= 6.0.0 for security fixes
    ],
    
    # Development dependencies
    'dev': [
        'pytest>=7.4.0',
        'pytest-cov>=4.1.0',
        'pytest-mock>=3.11.0',
        'flake8>=6.1.0',
        'pylint>=3.0.0',
        'black>=23.7.0',
        'mypy>=1.5.0',
    ],
}

# Convenience groups
EXTRAS_REQUIRE['all'] = list(set(sum([
    deps for key, deps in EXTRAS_REQUIRE.items() 
    if key not in ['search-gpu', 'dev']
], [])))

EXTRAS_REQUIRE['full'] = EXTRAS_REQUIRE['all']  # Alias

setup(
    name=APP_NAME,
    version=APP_VERSION,
    author=APP_AUTHOR,
    author_email=APP_EMAIL,
    description='Professional game texture sorting application with AI classification',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/JosephsDeadish/PS2-texture-sorter',
    project_urls={
        'Bug Reports': 'https://github.com/JosephsDeadish/PS2-texture-sorter/issues',
        'Source': 'https://github.com/JosephsDeadish/PS2-texture-sorter',
        'Documentation': 'https://github.com/JosephsDeadish/PS2-texture-sorter#readme',
    },
    
    # Package configuration
    packages=find_packages(exclude=['tests', 'tests.*', 'examples', 'examples.*']),
    python_requires='>=3.8',
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    
    # Include non-Python files
    include_package_data=True,
    package_data={
        'src': [
            'resources/**/*',
            'resources/icons/*',
            'resources/cursors/*',
            'resources/themes/*',
            'resources/sounds/*',
        ],
    },
    
    # Entry points for command-line scripts
    entry_points={
        'console_scripts': [
            'game-texture-sorter=main:main',
        ],
    },
    
    # Classifiers for PyPI
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Games/Entertainment',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',  # Update if different
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Environment :: X11 Applications',
        'Environment :: Win32 (MS Windows)',
        'Natural Language :: English',
    ],
    
    # Keywords for search
    keywords='texture sorting game-dev ps2 image-processing ai classification',
    
    # Specify platforms
    platforms=['Windows', 'Linux', 'macOS'],
    
    # License
    license='MIT',  # Update if different
    
    # Zip safe
    zip_safe=False,
)

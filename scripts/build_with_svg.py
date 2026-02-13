#!/usr/bin/env python3
"""
Build Wrapper Script for Game Texture Sorter with SVG Support
Author: Dead On The Inside / JosephsDeadish

This script automates building the application with SVG support by:
1. Checking if Cairo DLLs are available
2. Installing cairosvg/cairocffi if not already installed
3. Running PyInstaller with build_spec_with_svg.spec
4. Testing the resulting exe for SVG support
5. Providing clear error messages if build fails
"""

import sys
import subprocess
import os
from pathlib import Path
from typing import Tuple, Optional


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")


def print_status(status: str, message: str):
    """Print a status message with icon."""
    icons = {
        'success': '✓',
        'warning': '⚠',
        'error': '✗',
        'info': 'ℹ',
    }
    icon = icons.get(status, '•')
    print(f"{icon} {message}")


def check_python_version() -> bool:
    """Check if Python version is adequate."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_status('error', f"Python {version.major}.{version.minor} is too old")
        print("  Required: Python 3.8 or later")
        return False
    
    print_status('success', f"Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_cairo_dlls() -> Tuple[bool, Optional[Path]]:
    """
    Check if Cairo DLLs are available in common locations.
    Returns (found, installation_path).
    """
    search_paths = [
        Path(r'C:\Program Files\GTK3-Runtime Win64\bin'),
        Path(r'C:\msys64\mingw64\bin'),
        Path(os.environ.get('CAIRO_DLL_PATH', '')),
        Path.cwd() / 'cairo_dlls',
    ]
    
    for path in search_paths:
        if not path.exists():
            continue
        
        # Check for main Cairo DLL
        if (path / 'libcairo-2.dll').exists():
            return True, path
    
    return False, None


def check_pyinstaller_installed() -> bool:
    """Check if PyInstaller is installed."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', 'pyinstaller'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def install_pyinstaller() -> bool:
    """Install PyInstaller."""
    print_status('info', "Installing PyInstaller...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'pyinstaller'],
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_status('error', f"Failed to install PyInstaller: {e}")
        return False


def check_svg_packages() -> Tuple[bool, bool]:
    """
    Check if cairosvg and cairocffi are installed.
    Returns (cairosvg_installed, cairocffi_installed).
    """
    cairosvg_installed = False
    cairocffi_installed = False
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', 'cairosvg'],
            capture_output=True,
            text=True
        )
        cairosvg_installed = result.returncode == 0
    except Exception:
        pass
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', 'cairocffi'],
            capture_output=True,
            text=True
        )
        cairocffi_installed = result.returncode == 0
    except Exception:
        pass
    
    return cairosvg_installed, cairocffi_installed


def install_svg_packages() -> bool:
    """Install cairosvg and cairocffi packages."""
    print_status('info', "Installing SVG support packages...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'cairosvg', 'cairocffi'],
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_status('error', f"Failed to install SVG packages: {e}")
        return False


def run_pyinstaller() -> bool:
    """Run PyInstaller with build_spec_with_svg.spec."""
    spec_file = Path('build_spec_with_svg.spec')
    
    if not spec_file.exists():
        print_status('error', f"Spec file not found: {spec_file}")
        return False
    
    print_status('info', f"Running PyInstaller with {spec_file}...")
    print("\nThis may take several minutes...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', str(spec_file), '--clean', '--noconfirm'],
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_status('error', f"PyInstaller failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print_status('error', f"Failed to run PyInstaller: {e}")
        return False


def find_built_exe() -> Optional[Path]:
    """Find the built executable."""
    dist_dir = Path('dist')
    
    if not dist_dir.exists():
        return None
    
    # Look for GameTextureSorter.exe
    exe_path = dist_dir / 'GameTextureSorter.exe'
    if exe_path.exists():
        return exe_path
    
    # Look for any .exe file
    exe_files = list(dist_dir.glob('*.exe'))
    if exe_files:
        return exe_files[0]
    
    return None


def verify_exe_svg_support(exe_path: Path) -> bool:
    """
    Attempt to verify SVG support in the built executable.
    This is a basic check - can't fully test without running the exe.
    """
    print_status('info', "Checking if Cairo DLLs are bundled...")
    
    # We can check the EXE file size as a heuristic for whether
    # Cairo DLLs are bundled.
    
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print_status('info', f"EXE size: {size_mb:.1f} MB")
    
    # A rough heuristic: if Cairo DLLs are bundled, the exe should be
    # larger (Cairo DLLs add ~15-20 MB total)
    # Base exe is typically 50-100 MB, with Cairo it should be 65-120 MB
    
    if size_mb > 60:
        print_status('success', "EXE size suggests Cairo DLLs are likely bundled")
        return True
    else:
        print_status('warning', "EXE size is small - Cairo DLLs may not be bundled")
        return False


def print_success_message(exe_path: Path, svg_support: bool):
    """Print success message with next steps."""
    print_header("Build Successful!")
    
    print_status('success', f"Executable created: {exe_path}")
    print_status('success', f"File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
    
    if svg_support:
        print_status('success', "SVG support appears to be included")
    else:
        print_status('warning', "SVG support may be limited")
        print("\nIf SVG files don't work:")
        print("  1. Check that Cairo DLLs are installed on your system")
        print("  2. Run: python scripts/setup_cairo_dlls.py")
        print("  3. Rebuild with this script")
    
    print("\nNext steps:")
    print("  1. Test the executable: ", end="")
    print(f"{exe_path}")
    print("  2. Try loading an SVG file to verify SVG support")
    print("  3. Check console output for 'cairosvg available' message")
    print("  4. If everything works, distribute the EXE to users!")
    
    print("\nFor code signing:")
    print("  See CODE_SIGNING.md for instructions")


def main():
    """Main execution function."""
    print_header("Build Game Texture Sorter with SVG Support")
    
    # Step 1: Check Python version
    print_header("Step 1: Checking Python Version")
    if not check_python_version():
        return 1
    
    # Step 2: Check Cairo DLLs
    print_header("Step 2: Checking Cairo DLLs")
    
    cairo_found, cairo_path = check_cairo_dlls()
    
    if cairo_found:
        print_status('success', f"Cairo DLLs found at: {cairo_path}")
    else:
        print_status('warning', "Cairo DLLs not found in common locations")
        print("\nSVG support will NOT be available unless you:")
        print("  1. Install GTK3 runtime or MSYS2")
        print("  2. Or run: python scripts/setup_cairo_dlls.py")
        print("  3. See docs/SVG_BUILD_GUIDE.md for detailed instructions")
        print("\nContinue anyway? The build will succeed but without SVG support.")
        
        response = input("Continue? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("\nBuild cancelled. Please set up Cairo DLLs first.")
            return 1
    
    # Step 3: Check/Install PyInstaller
    print_header("Step 3: Checking PyInstaller")
    
    if check_pyinstaller_installed():
        print_status('success', "PyInstaller is installed")
    else:
        print_status('warning', "PyInstaller is not installed")
        if not install_pyinstaller():
            return 1
        print_status('success', "PyInstaller installed successfully")
    
    # Step 4: Check/Install SVG packages
    print_header("Step 4: Checking SVG Support Packages")
    
    cairosvg_installed, cairocffi_installed = check_svg_packages()
    
    if cairosvg_installed and cairocffi_installed:
        print_status('success', "cairosvg and cairocffi are installed")
    else:
        if not cairosvg_installed:
            print_status('warning', "cairosvg is not installed")
        if not cairocffi_installed:
            print_status('warning', "cairocffi is not installed")
        
        if not install_svg_packages():
            print_status('warning', "Could not install SVG packages")
            print("SVG support may be limited in the built executable.")
        else:
            print_status('success', "SVG packages installed successfully")
    
    # Step 5: Run PyInstaller
    print_header("Step 5: Building with PyInstaller")
    
    if not run_pyinstaller():
        print_status('error', "Build failed!")
        print("\nTroubleshooting:")
        print("  1. Check the error messages above")
        print("  2. Ensure all dependencies are installed")
        print("  3. Try: pip install -r requirements.txt")
        print("  4. See BUILD.md for more help")
        return 1
    
    # Step 6: Verify output
    print_header("Step 6: Verifying Build Output")
    
    exe_path = find_built_exe()
    
    if not exe_path:
        print_status('error', "Could not find built executable in dist/")
        return 1
    
    svg_support = verify_exe_svg_support(exe_path)
    
    # Success!
    print_success_message(exe_path, svg_support)
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

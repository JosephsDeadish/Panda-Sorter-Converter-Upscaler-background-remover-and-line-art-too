"""
Tests for portable app_data path resolution in config.py.

Verifies that get_app_dir(), get_data_dir(), and get_resource_path()
correctly prefer a local app_data/ folder when present, and fall back
to the home directory and dev-tree resources otherwise.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import get_app_dir, get_data_dir, get_resource_path, _is_frozen

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  ✓ {name}")
        passed += 1
    else:
        print(f"  ✗ {name}: {detail}")
        failed += 1


print("=" * 60)
print("Test: Path resolution helpers")
print("=" * 60)

# --- _is_frozen ---
print("\n-- _is_frozen --")
check("Not frozen in dev mode", not _is_frozen())

# --- get_app_dir ---
print("\n-- get_app_dir --")
app_dir = get_app_dir()
check("Returns a Path", isinstance(app_dir, Path))
check("Directory exists", app_dir.is_dir())
check("Contains src/ (dev mode)", (app_dir / "src").is_dir())

# --- get_data_dir fallback ---
print("\n-- get_data_dir (no app_data/) --")
data_dir = get_data_dir()
check("Returns a Path", isinstance(data_dir, Path))
# In dev mode without app_data/, should fall back to home
check("Falls back to home dir",
      str(data_dir).startswith(str(Path.home())),
      f"got {data_dir}")

# --- get_data_dir with app_data/ present ---
print("\n-- get_data_dir (with app_data/) --")
import src.config as cfg
original = cfg.get_app_dir

tmpdir = tempfile.mkdtemp()
app_data_dir = Path(tmpdir) / "app_data"
app_data_dir.mkdir()
try:
    cfg.get_app_dir = lambda: Path(tmpdir)
    result = cfg.get_data_dir()
    check("Uses local app_data/",
          result == app_data_dir,
          f"expected {app_data_dir}, got {result}")
finally:
    cfg.get_app_dir = original
    shutil.rmtree(tmpdir)

# --- get_resource_path (dev mode) ---
print("\n-- get_resource_path (dev mode) --")
sounds = get_resource_path("sounds")
check("Returns a Path", isinstance(sounds, Path))
check("Resolves to src/resources/sounds",
      "src" in str(sounds) and "resources" in str(sounds) and str(sounds).endswith("sounds"),
      f"got {sounds}")

icons = get_resource_path("icons")
check("Icons resolves correctly",
      str(icons).endswith("icons"),
      f"got {icons}")

# --- get_resource_path with external app_data ---
print("\n-- get_resource_path (with app_data/resources/) --")
tmpdir2 = tempfile.mkdtemp()
ext_sounds = Path(tmpdir2) / "app_data" / "resources" / "sounds"
ext_sounds.mkdir(parents=True)
try:
    cfg.get_app_dir = lambda: Path(tmpdir2)
    result = cfg.get_resource_path("sounds")
    check("Prefers external app_data/resources/sounds",
          result == ext_sounds,
          f"expected {ext_sounds}, got {result}")
finally:
    cfg.get_app_dir = original
    shutil.rmtree(tmpdir2)

# --- Summary ---
print()
print("-" * 60)
total = passed + failed
if failed == 0:
    print(f"✅ All {total} path resolution tests passed!")
else:
    print(f"❌ {failed}/{total} tests failed")
    sys.exit(1)

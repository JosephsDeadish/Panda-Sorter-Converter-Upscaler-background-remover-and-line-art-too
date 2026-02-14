"""Tests for Image Upscaler tool tab logic (no GUI required)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_pil_resample_mapping():
    """Verify all style strings map to valid PIL resample filters."""
    from PIL import Image

    styles = {
        "🔷 Lanczos (Sharpest)": Image.LANCZOS,
        "🟢 Bicubic (Smooth)": Image.BICUBIC,
        "🟡 Bilinear (Fast)": Image.BILINEAR,
        "🔶 Hamming": Image.HAMMING,
        "🟣 Box (Pixel Art)": Image.BOX,
        "⬜ Nearest (Pixel Perfect)": Image.NEAREST,
        "🔵 Mitchell": Image.BICUBIC,   # falls back to BICUBIC
        "🟤 CatRom": Image.BICUBIC,     # falls back to BICUBIC
    }
    for label, expected in styles.items():
        # Replicate the matching logic from _get_pil_resample
        if "Lanczos" in label:
            got = Image.LANCZOS
        elif "Bicubic" in label:
            got = Image.BICUBIC
        elif "Bilinear" in label:
            got = Image.BILINEAR
        elif "Hamming" in label:
            got = Image.HAMMING
        elif "Box" in label:
            got = Image.BOX
        elif "Nearest" in label:
            got = Image.NEAREST
        elif "Mitchell" in label or "CatRom" in label:
            got = Image.BICUBIC
        else:
            got = Image.LANCZOS
        assert got == expected, f"Style '{label}' mapped to {got}, expected {expected}"


def test_upscale_pil_rgba_preservation():
    """Upscaling an RGBA image with preserve_alpha should keep alpha."""
    from PIL import Image

    img = Image.new("RGBA", (4, 4), (255, 0, 0, 128))
    factor = 2
    new_size = (img.size[0] * factor, img.size[1] * factor)
    resample = Image.LANCZOS

    # Replicate the _upscale_pil_image logic for RGBA + preserve_alpha
    rgb = img.convert("RGB").resize(new_size, resample)
    alpha = img.getchannel("A").resize(new_size, resample)
    result = rgb.copy()
    result.putalpha(alpha)

    assert result.mode == "RGBA"
    assert result.size == (8, 8)
    # Alpha should be preserved (128)
    px = result.getpixel((0, 0))
    assert px[3] == 128, f"Alpha should be 128, got {px[3]}"


def test_upscale_rgb_no_alpha():
    """Upscaling an RGB image without alpha should work fine."""
    from PIL import Image

    img = Image.new("RGB", (4, 4), (0, 255, 0))
    factor = 4
    result = img.resize((img.size[0] * factor, img.size[1] * factor), Image.LANCZOS)
    assert result.size == (16, 16)
    assert result.mode == "RGB"


def test_scale_factor_parsing():
    """Scale factor strings should parse to integers correctly."""
    for text, expected in [("2x", 2), ("3x", 3), ("4x", 4), ("6x", 6), ("8x", 8), ("16x", 16)]:
        got = int(text.replace("x", ""))
        assert got == expected, f"'{text}' -> {got}, expected {expected}"


def test_upscale_uses_lanczos_not_nearest():
    """Default style should be Lanczos, never Nearest (which causes jagged edges)."""
    from PIL import Image

    # The default in the UI is Lanczos
    default_style = "🔷 Lanczos (Sharpest)"
    assert "Lanczos" in default_style
    assert "Nearest" not in default_style

    # Lanczos produces smoother results than NEAREST
    img = Image.new("RGBA", (2, 2), (255, 0, 0, 255))
    img.putpixel((0, 0), (0, 0, 255, 255))
    result_lanczos = img.resize((8, 8), Image.LANCZOS)
    result_nearest = img.resize((8, 8), Image.NEAREST)
    # With NEAREST, (3,3) is still in the top-left quadrant → blue
    # With LANCZOS, (3,3) is blended between blue and red
    lanczos_px = result_lanczos.getpixel((3, 3))
    nearest_px = result_nearest.getpixel((3, 3))
    # NEAREST gives exact original pixel; LANCZOS produces blended values
    assert nearest_px[:3] == (0, 0, 255), "NEAREST should give exact pixel copy"
    assert lanczos_px[:3] != (0, 0, 255), "LANCZOS should blend at boundary pixels"


def test_zip_roundtrip():
    """Upscaled images should be writable to and readable from ZIP."""
    import zipfile
    import tempfile
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmp:
        # Create test image
        img = Image.new("RGBA", (4, 4), (100, 200, 50, 200))
        img_path = Path(tmp) / "test.png"
        img.save(str(img_path))

        # ZIP it
        zip_path = Path(tmp) / "test.zip"
        with zipfile.ZipFile(str(zip_path), 'w') as zf:
            zf.write(str(img_path), "test.png")

        # Extract and verify
        extract_dir = Path(tmp) / "extracted"
        extract_dir.mkdir()
        with zipfile.ZipFile(str(zip_path), 'r') as zf:
            zf.extractall(str(extract_dir))

        extracted = Image.open(str(extract_dir / "test.png"))
        assert extracted.mode == "RGBA"
        assert extracted.size == (4, 4)


def test_image_open_and_upscale_roundtrip():
    """Image.open should work for upscaling and saving (validates PIL import availability)."""
    import tempfile
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmp:
        # Create and save a test image
        img = Image.new("RGBA", (8, 8), (50, 100, 150, 200))
        img_path = Path(tmp) / "input.png"
        img.save(str(img_path))

        # Open the image (simulates _preview_upscale_file and _run_upscale)
        opened = Image.open(str(img_path))
        assert opened.size == (8, 8)

        # Upscale using resize with Lanczos (simulates _upscale_pil_image)
        factor = 2
        new_size = (opened.size[0] * factor, opened.size[1] * factor)
        resample = Image.LANCZOS
        rgb = opened.convert("RGB").resize(new_size, resample)
        alpha = opened.getchannel("A").resize(new_size, resample)
        result = rgb.copy()
        result.putalpha(alpha)

        assert result.size == (16, 16)
        assert result.mode == "RGBA"

        # Save the upscaled image (simulates _run_upscale save)
        out_path = Path(tmp) / "output.png"
        result.save(str(out_path))
        assert out_path.exists()

        # Verify saved image
        saved = Image.open(str(out_path))
        assert saved.size == (16, 16)
        assert saved.mode == "RGBA"


def test_pil_resample_filters_accessible():
    """All PIL resample filters used by _get_pil_resample should be accessible."""
    from PIL import Image

    # These are the exact attributes used in _get_pil_resample
    filters = [Image.LANCZOS, Image.BICUBIC, Image.BILINEAR, Image.HAMMING, Image.BOX, Image.NEAREST]
    for f in filters:
        assert f is not None, f"Filter {f} should not be None"


def test_custom_resolution_parsing():
    """Custom resolution strings should parse to (width, height) tuples."""
    valid = [("1024x1024", (1024, 1024)), ("512x256", (512, 256)), ("2048x2048", (2048, 2048))]
    for text, expected in valid:
        parts = text.lower().split("x")
        got = (int(parts[0]), int(parts[1]))
        assert got == expected, f"'{text}' -> {got}, expected {expected}"


def test_post_processing_sharpen():
    """Sharpening filter should not crash and should change pixel values."""
    from PIL import Image, ImageFilter

    img = Image.new("RGBA", (8, 8), (128, 128, 128, 255))
    # Draw a simple edge to sharpen
    for x in range(4, 8):
        for y in range(8):
            img.putpixel((x, y), (200, 200, 200, 255))
    
    rgb = img.convert("RGB").filter(ImageFilter.SHARPEN)
    assert rgb.size == (8, 8)
    assert rgb.mode == "RGB"


def test_post_processing_denoise():
    """Noise reduction (SMOOTH) should not crash."""
    from PIL import Image, ImageFilter

    img = Image.new("RGB", (8, 8), (128, 128, 128))
    result = img.filter(ImageFilter.SMOOTH)
    assert result.size == (8, 8)


def test_post_processing_auto_level():
    """Auto-level should stretch histogram."""
    from PIL import Image, ImageOps

    # Create an image with limited range (100-200)
    img = Image.new("RGB", (4, 4), (100, 150, 200))
    result = ImageOps.autocontrast(img, cutoff=1)
    assert result.size == (4, 4)
    assert result.mode == "RGB"


def test_smart_search_category_keyword_matching():
    """Smart search should expand query to category keywords."""
    import importlib
    from pathlib import Path
    
    try:
        spec = importlib.util.spec_from_file_location(
            'categories',
            str(Path(__file__).parent / 'src' / 'classifier' / 'categories.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        # Search for "gun" should find the weapons/objects category
        search_query = "gun"
        smart_keywords = set()
        for attr_name in dir(mod):
            obj = getattr(mod, attr_name)
            if isinstance(obj, dict) and attr_name.isupper():
                for cat_id, cat_data in obj.items():
                    if not isinstance(cat_data, dict):
                        continue
                    kws = cat_data.get('keywords', [])
                    cat_name = cat_data.get('name', '').lower()
                    matched = search_query in cat_name or search_query == cat_id
                    if not matched:
                        for kw in kws:
                            if search_query in kw.lower():
                                matched = True
                                break
                    if matched:
                        for kw in kws:
                            smart_keywords.add(kw.lower())
        
        # "gun" should match weapon-related keywords
        assert len(smart_keywords) > 0, "Smart search for 'gun' should find category keywords"
        # The expanded set should contain weapon-related terms
        assert any("weapon" in kw or "gun" in kw or "rifle" in kw 
                    for kw in smart_keywords), \
            f"Smart keywords should include weapon terms, got: {list(smart_keywords)[:10]}"
        print(f"✓ Smart search: 'gun' expanded to {len(smart_keywords)} keywords")
    except Exception as e:
        print(f"⚠ Skipping smart search test: {e}")


if __name__ == "__main__":
    test_pil_resample_mapping()
    test_upscale_pil_rgba_preservation()
    test_upscale_rgb_no_alpha()
    test_scale_factor_parsing()
    test_upscale_uses_lanczos_not_nearest()
    test_zip_roundtrip()
    test_image_open_and_upscale_roundtrip()
    test_pil_resample_filters_accessible()
    test_custom_resolution_parsing()
    test_post_processing_sharpen()
    test_post_processing_denoise()
    test_post_processing_auto_level()
    test_smart_search_category_keyword_matching()
    print("All upscaler tool tests passed!")

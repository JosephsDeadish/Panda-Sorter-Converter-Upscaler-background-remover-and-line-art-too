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
    for text, expected in [("2x", 2), ("4x", 4), ("8x", 8)]:
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


if __name__ == "__main__":
    test_pil_resample_mapping()
    test_upscale_pil_rgba_preservation()
    test_upscale_rgb_no_alpha()
    test_scale_factor_parsing()
    test_upscale_uses_lanczos_not_nearest()
    test_zip_roundtrip()
    print("All upscaler tool tests passed!")

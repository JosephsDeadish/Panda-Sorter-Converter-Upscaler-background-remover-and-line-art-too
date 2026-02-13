"""Tests for the native Rust acceleration module and its Python fallbacks."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from src.native_ops import (
    NATIVE_AVAILABLE,
    lanczos_upscale,
    perceptual_hash,
    hamming_distance,
    color_histogram,
    edge_density,
    batch_perceptual_hash,
    batch_color_histogram,
)


def test_native_available():
    """Check whether the Rust extension was loaded (informational)."""
    print(f"  Native Rust module available: {NATIVE_AVAILABLE}")


def test_lanczos_upscale_rgb():
    """Lanczos upscale should double an RGB image correctly."""
    img = np.zeros((4, 4, 3), dtype=np.uint8)
    img[:, :] = [255, 0, 0]  # solid red
    result = lanczos_upscale(img, scale_factor=2)
    assert result.shape == (8, 8, 3), f"Expected (8,8,3), got {result.shape}"
    assert result.dtype == np.uint8


def test_lanczos_upscale_rgba():
    """Lanczos upscale should handle RGBA images."""
    img = np.zeros((4, 4, 4), dtype=np.uint8)
    img[:, :] = [0, 255, 0, 128]
    result = lanczos_upscale(img, scale_factor=2)
    assert result.shape == (8, 8, 4), f"Expected (8,8,4), got {result.shape}"


def test_lanczos_upscale_4x():
    """4x upscale should produce correct dimensions."""
    img = np.full((8, 8, 3), 100, dtype=np.uint8)
    result = lanczos_upscale(img, scale_factor=4)
    assert result.shape == (32, 32, 3)


def test_perceptual_hash_deterministic():
    """Same image should always produce the same hash."""
    img = np.random.RandomState(42).randint(0, 256, (16, 16, 3), dtype=np.uint8)
    h1 = perceptual_hash(img)
    h2 = perceptual_hash(img)
    assert h1 == h2, "Hash should be deterministic"


def test_perceptual_hash_different_images():
    """Very different images should produce different hashes."""
    # Use images with actual contrast variation
    rng = np.random.RandomState(1)
    img_a = rng.randint(0, 128, (16, 16, 3), dtype=np.uint8)
    img_b = rng.randint(128, 256, (16, 16, 3), dtype=np.uint8)
    h_a = perceptual_hash(img_a)
    h_b = perceptual_hash(img_b)
    # They should differ since intensity distributions are very different
    assert h_a != h_b, "Distinct images should hash differently"


def test_perceptual_hash_rgba_stripped():
    """RGBA images should have alpha stripped before hashing."""
    img_rgb = np.full((8, 8, 3), 128, dtype=np.uint8)
    img_rgba = np.full((8, 8, 4), 128, dtype=np.uint8)
    h_rgb = perceptual_hash(img_rgb)
    h_rgba = perceptual_hash(img_rgba)
    assert h_rgb == h_rgba, "RGBA alpha should be stripped to match RGB hash"


def test_hamming_distance_identical():
    """Hamming distance of identical hashes should be 0."""
    assert hamming_distance(0xDEADBEEF, 0xDEADBEEF) == 0


def test_hamming_distance_opposite():
    """Hamming distance of all-zero vs all-one (64-bit) should be 64."""
    assert hamming_distance(0, 0xFFFFFFFFFFFFFFFF) == 64


def test_hamming_distance_single_bit():
    """Flipping one bit should give distance 1."""
    assert hamming_distance(0, 1) == 1


def test_color_histogram_shape():
    """Histogram should have 3*bins entries."""
    img = np.full((4, 4, 3), 128, dtype=np.uint8)
    hist = color_histogram(img, bins=16)
    assert len(hist) == 48, f"Expected 48 bins, got {len(hist)}"


def test_color_histogram_normalized():
    """Each channel of the histogram should sum to ~1."""
    img = np.random.RandomState(7).randint(0, 256, (8, 8, 3), dtype=np.uint8)
    bins = 16
    hist = color_histogram(img, bins=bins)
    for c in range(3):
        channel_sum = sum(hist[c * bins : (c + 1) * bins])
        assert abs(channel_sum - 1.0) < 1e-9, f"Channel {c} sum={channel_sum}"


def test_color_histogram_solid_color():
    """A solid-red image should have all weight in the last red bin."""
    img = np.zeros((4, 4, 3), dtype=np.uint8)
    img[:, :, 0] = 255
    hist = color_histogram(img, bins=16)
    # Red channel: last bin should be 1.0
    assert hist[15] == 1.0, f"Expected red bin=1.0, got {hist[15]}"
    # Green and blue channels: first bin should be 1.0
    assert hist[16] == 1.0, f"Expected green first bin=1.0, got {hist[16]}"
    assert hist[32] == 1.0, f"Expected blue first bin=1.0, got {hist[32]}"


def test_edge_density_range():
    """Edge density should be between 0 and 1."""
    img = np.random.RandomState(99).randint(0, 256, (32, 32, 3), dtype=np.uint8)
    ed = edge_density(img)
    assert 0.0 <= ed <= 1.0, f"Edge density {ed} out of range"


def test_edge_density_flat_image():
    """A solid-color image should have very low edge density."""
    img = np.full((32, 32, 3), 128, dtype=np.uint8)
    ed = edge_density(img)
    assert ed < 0.01, f"Flat image edge density should be ~0, got {ed}"


def test_edge_density_small_image():
    """Images smaller than 3x3 should return 0."""
    img = np.full((2, 2, 3), 128, dtype=np.uint8)
    assert edge_density(img) == 0.0


def test_batch_perceptual_hash():
    """Batch hash should produce same results as individual calls."""
    images = [
        np.full((8, 8, 3), c, dtype=np.uint8)
        for c in [0, 64, 128, 192, 255]
    ]
    batch_hashes = batch_perceptual_hash(images)
    individual_hashes = [perceptual_hash(img) for img in images]
    assert batch_hashes == individual_hashes, "Batch and individual hashes should match"


def test_batch_color_histogram():
    """Batch histogram should produce same results as individual calls."""
    images = [
        np.random.RandomState(i).randint(0, 256, (8, 8, 3), dtype=np.uint8)
        for i in range(3)
    ]
    batch_hists = batch_color_histogram(images, bins=8)
    individual_hists = [color_histogram(img, bins=8) for img in images]
    for bh, ih in zip(batch_hists, individual_hists):
        assert len(bh) == len(ih)
        for a, b in zip(bh, ih):
            assert abs(a - b) < 1e-12


def test_upscaler_lanczos_method():
    """TextureUpscaler should support 'lanczos' method when native is available."""
    from src.preprocessing.upscaler import TextureUpscaler, NATIVE_AVAILABLE as UP_NATIVE

    upscaler = TextureUpscaler()
    img = np.full((8, 8, 3), 100, dtype=np.uint8)
    result = upscaler.upscale(img, scale_factor=2, method='lanczos')
    assert result.shape[0] == 16
    assert result.shape[1] == 16


if __name__ == "__main__":
    test_native_available()
    test_lanczos_upscale_rgb()
    test_lanczos_upscale_rgba()
    test_lanczos_upscale_4x()
    test_perceptual_hash_deterministic()
    test_perceptual_hash_different_images()
    test_perceptual_hash_rgba_stripped()
    test_hamming_distance_identical()
    test_hamming_distance_opposite()
    test_hamming_distance_single_bit()
    test_color_histogram_shape()
    test_color_histogram_normalized()
    test_color_histogram_solid_color()
    test_edge_density_range()
    test_edge_density_flat_image()
    test_edge_density_small_image()
    test_batch_perceptual_hash()
    test_batch_color_histogram()
    test_upscaler_lanczos_method()
    print("All native_ops tests passed!")

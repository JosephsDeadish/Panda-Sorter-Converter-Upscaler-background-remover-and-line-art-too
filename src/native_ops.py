"""
Native Rust Acceleration Wrapper
Provides Python fallbacks when the Rust extension is not available.
Author: Dead On The Inside / JosephsDeadish

The ``texture_ops`` Rust extension (built with PyO3) accelerates:
- Lanczos upscaling (multi-threaded via Rayon)
- Perceptual hashing for duplicate/similarity detection
- Color histogram computation
- Edge density measurement
- Batch parallel processing of multiple images

When the native module is unavailable, the pure-Python fallbacks in this
file are used instead.  They produce identical results but are slower.
"""

import logging
import math
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import the compiled Rust extension
# ---------------------------------------------------------------------------
try:
    import texture_ops as _native

    NATIVE_AVAILABLE = True
    logger.info("Native Rust acceleration module loaded successfully")
except ImportError:
    _native = None
    NATIVE_AVAILABLE = False
    logger.debug("Native Rust acceleration module not available, using Python fallbacks")

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def is_native_available() -> bool:
    """Return *True* if the compiled Rust extension is loaded."""
    return NATIVE_AVAILABLE


# ---------------------------------------------------------------------------
# Upscaling
# ---------------------------------------------------------------------------


def lanczos_upscale(
    image: np.ndarray,
    scale_factor: int = 4,
) -> np.ndarray:
    """Upscale an image using Lanczos-3 interpolation.

    When the Rust extension is available the work is parallelised across CPU
    cores.  Otherwise a pure-Python/NumPy implementation is used.

    Parameters
    ----------
    image : np.ndarray
        Input image with shape ``(H, W, 3)`` or ``(H, W, 4)`` and dtype
        ``uint8``.
    scale_factor : int
        Integer scale factor (e.g. 2, 4, 8).

    Returns
    -------
    np.ndarray
        Upscaled image with shape ``(H*scale, W*scale, C)`` and dtype
        ``uint8``.
    """
    h, w = image.shape[:2]
    channels = image.shape[2] if len(image.shape) == 3 else 1

    if NATIVE_AVAILABLE:
        flat = image.tobytes()
        result_bytes, new_w, new_h = _native.lanczos_upscale(
            flat, w, h, channels, scale_factor
        )
        return np.frombuffer(result_bytes, dtype=np.uint8).reshape(new_h, new_w, channels)

    # Pure-Python fallback using PIL
    from PIL import Image as PILImage

    pil_img = PILImage.fromarray(image)
    new_size = (w * scale_factor, h * scale_factor)
    upscaled = pil_img.resize(new_size, PILImage.LANCZOS)
    return np.array(upscaled)


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------


def perceptual_hash(image: np.ndarray) -> int:
    """Compute a 64-bit perceptual hash of an RGB image.

    Parameters
    ----------
    image : np.ndarray
        RGB image with shape ``(H, W, 3)`` and dtype ``uint8``.

    Returns
    -------
    int
        64-bit perceptual hash.
    """
    if len(image.shape) == 3 and image.shape[2] == 4:
        image = image[:, :, :3]

    h, w = image.shape[:2]

    if NATIVE_AVAILABLE:
        return _native.perceptual_hash(image.tobytes(), w, h)

    # Pure-Python fallback
    from PIL import Image as PILImage

    pil_img = PILImage.fromarray(image).convert("L").resize((8, 8), PILImage.LANCZOS)
    pixels = list(pil_img.getdata())
    mean_val = sum(pixels) / 64.0
    hash_val = 0
    for i, p in enumerate(pixels):
        if p > mean_val:
            hash_val |= 1 << i
    return hash_val


def hamming_distance(hash_a: int, hash_b: int) -> int:
    """Return the Hamming distance between two 64-bit hashes.

    Parameters
    ----------
    hash_a, hash_b : int
        64-bit perceptual hashes.

    Returns
    -------
    int
        Number of differing bits (0–64).
    """
    if NATIVE_AVAILABLE:
        return _native.hamming_distance(hash_a, hash_b)
    return bin(hash_a ^ hash_b).count("1")


def color_histogram(image: np.ndarray, bins: int = 16) -> List[float]:
    """Compute a normalized per-channel color histogram.

    Parameters
    ----------
    image : np.ndarray
        RGB image with shape ``(H, W, 3)`` and dtype ``uint8``.
    bins : int
        Number of bins per channel.

    Returns
    -------
    list[float]
        Flattened histogram of length ``3 * bins``, normalized so that
        each channel sums to 1.
    """
    if len(image.shape) == 3 and image.shape[2] == 4:
        image = image[:, :, :3]

    h, w = image.shape[:2]

    if NATIVE_AVAILABLE:
        return _native.color_histogram(image.tobytes(), w, h, bins)

    # Pure-Python fallback
    total = h * w
    hist = [0.0] * (3 * bins)
    bw = 256.0 / bins
    flat = image.reshape(-1, 3)
    for c in range(3):
        channel = flat[:, c]
        for val in channel:
            b = min(int(val / bw), bins - 1)
            hist[c * bins + b] += 1
    return [v / total for v in hist]


def edge_density(image: np.ndarray) -> float:
    """Compute the edge density of an RGB image using a Sobel operator.

    Parameters
    ----------
    image : np.ndarray
        RGB image with shape ``(H, W, 3)`` and dtype ``uint8``.

    Returns
    -------
    float
        Fraction of pixels classified as edges (0.0–1.0).
    """
    if len(image.shape) == 3 and image.shape[2] == 4:
        image = image[:, :, :3]

    h, w = image.shape[:2]

    if NATIVE_AVAILABLE:
        return _native.edge_density(image.tobytes(), w, h)

    # Pure-Python fallback using OpenCV
    try:
        import cv2

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return float(np.sum(edges > 0)) / edges.size
    except ImportError:
        return 0.0


# ---------------------------------------------------------------------------
# Batch operations
# ---------------------------------------------------------------------------


def batch_perceptual_hash(images: List[np.ndarray]) -> List[int]:
    """Compute perceptual hashes for a list of RGB images in parallel.

    Parameters
    ----------
    images : list[np.ndarray]
        List of RGB images.

    Returns
    -------
    list[int]
        Corresponding 64-bit perceptual hashes.
    """
    if NATIVE_AVAILABLE:
        tuples = []
        for img in images:
            if len(img.shape) == 3 and img.shape[2] == 4:
                img = img[:, :, :3]
            h, w = img.shape[:2]
            tuples.append((img.tobytes(), w, h))
        return _native.batch_perceptual_hash(tuples)

    return [perceptual_hash(img) for img in images]


def batch_color_histogram(
    images: List[np.ndarray], bins: int = 16
) -> List[List[float]]:
    """Compute color histograms for a list of RGB images in parallel.

    Parameters
    ----------
    images : list[np.ndarray]
        List of RGB images.
    bins : int
        Number of bins per channel.

    Returns
    -------
    list[list[float]]
        Corresponding color histograms.
    """
    if NATIVE_AVAILABLE:
        tuples = []
        for img in images:
            if len(img.shape) == 3 and img.shape[2] == 4:
                img = img[:, :, :3]
            h, w = img.shape[:2]
            tuples.append((img.tobytes(), w, h))
        return _native.batch_color_histogram(tuples, bins)

    return [color_histogram(img, bins) for img in images]

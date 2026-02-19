"""
Native Rust Acceleration Wrapper
Provides Python fallbacks when the Rust extension is not available.
Author: Dead On The Inside / JosephsDeadish

The ``texture_ops`` Rust extension (built with PyO3) accelerates:
- Lanczos upscaling (multi-threaded via Rayon)
- Perceptual hashing for duplicate/similarity detection
- Color histogram computation
- Edge density measurement
- Bitmap to SVG vector tracing (via vtracer)
- Batch parallel processing of multiple images

When the native module is unavailable, the pure-Python fallbacks in this
file are used instead.  They produce similar results but are slower.
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


def bitmap_to_svg(
    image: np.ndarray,
    threshold: int = 25,
    mode: str = "color",
) -> Optional[str]:
    """Convert a bitmap image to SVG using vector tracing.

    This function traces the edges in a raster image and converts it to
    scalable vector graphics (SVG). When the Rust extension is available,
    it uses the vtracer library for high-quality tracing. Otherwise, it
    falls back to a pure-Python edge-detection based approach.

    Parameters
    ----------
    image : np.ndarray
        Input image with shape ``(H, W, 3)`` and dtype ``uint8`` (RGB).
    threshold : int, default 25
        Color difference threshold for edge detection (0-255).
        Lower values = more detail. Only used by native implementation.
    mode : str, default "color"
        Tracing mode: "color", "binary", "spline", "polygon", or "none".
        - "color": Full color vectorization
        - "binary": Black and white tracing
        - "spline": Smooth spline curves
        - "polygon": Polygon-based paths
        - "none": No path simplification
        Only used by native implementation.

    Returns
    -------
    Optional[str]
        SVG file content as a string, or None on failure.
    """
    if len(image.shape) == 3 and image.shape[2] == 4:
        image = image[:, :, :3]

    h, w = image.shape[:2]

    if NATIVE_AVAILABLE:
        try:
            return _native.bitmap_to_svg(image.tobytes(), w, h, threshold, mode)
        except Exception as e:
            logger.warning(f"Native bitmap_to_svg failed: {e}, trying fallback")

    # Pure-Python fallback using edge detection
    try:
        import cv2

        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Detect edges
        edges = cv2.Canny(gray, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Build SVG
        svg_parts = [
            f'<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        ]

        # Add background if color mode
        if mode == "color":
            # Sample background color from image center
            bg_color = image[h // 2, w // 2]
            svg_parts.append(
                f'  <rect width="{w}" height="{h}" fill="rgb({bg_color[0]},{bg_color[1]},{bg_color[2]})" />'
            )

        # Add contours as paths
        for contour in contours:
            if len(contour) < 3:
                continue

            # Build path data
            path_data = f"M {contour[0][0][0]} {contour[0][0][1]}"
            for point in contour[1:]:
                path_data += f" L {point[0][0]} {point[0][1]}"
            path_data += " Z"

            # Sample color near contour
            if mode == "color" and len(contour) > 0:
                x, y = contour[0][0]
                x, y = min(x, w - 1), min(y, h - 1)
                color = image[y, x]
                fill = f"rgb({color[0]},{color[1]},{color[2]})"
            else:
                fill = "black"

            svg_parts.append(f'  <path d="{path_data}" fill="{fill}" />')

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)

    except ImportError:
        logger.warning("OpenCV not available for bitmap_to_svg fallback")
        return None
    except Exception as e:
        logger.error(f"Fallback bitmap_to_svg failed: {e}")
        return None


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


def batch_bitmap_to_svg(
    images: List[np.ndarray],
    threshold: int = 25,
    mode: str = "color",
) -> List[Optional[str]]:
    """Convert a batch of bitmap images to SVG in parallel.

    Parameters
    ----------
    images : list[np.ndarray]
        List of RGB images.
    threshold : int, default 25
        Color difference threshold for edge detection (0-255).
    mode : str, default "color"
        Tracing mode: "color", "binary", or "spline".

    Returns
    -------
    list[Optional[str]]
        Corresponding SVG strings, or None for failures.
    """
    if NATIVE_AVAILABLE:
        try:
            tuples = []
            for img in images:
                if len(img.shape) == 3 and img.shape[2] == 4:
                    img = img[:, :, :3]
                h, w = img.shape[:2]
                tuples.append((img.tobytes(), w, h))
            return _native.batch_bitmap_to_svg(tuples, threshold, mode)
        except Exception as e:
            logger.warning(f"Native batch_bitmap_to_svg failed: {e}, using sequential fallback")

    return [bitmap_to_svg(img, threshold, mode) for img in images]

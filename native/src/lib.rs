//! Native Rust acceleration for PS2 texture sorting.
//!
//! Provides high-performance implementations of:
//! - Lanczos image upscaling
//! - Image feature extraction (perceptual hash, color histogram, edge density)
//! - Batch parallel image processing via Rayon
//!
//! Built with PyO3 for seamless Python integration.

use pyo3::prelude::*;
use rayon::prelude::*;

/// Clamp a value to [0, 255] and convert to u8.
#[inline]
fn clamp_u8(v: f64) -> u8 {
    v.round().clamp(0.0, 255.0) as u8
}

/// Lanczos kernel with window size `a`.
#[inline]
fn lanczos_weight(x: f64, a: f64) -> f64 {
    if x.abs() < f64::EPSILON {
        return 1.0;
    }
    if x.abs() >= a {
        return 0.0;
    }
    let pi_x = std::f64::consts::PI * x;
    let pi_x_a = pi_x / a;
    (pi_x.sin() / pi_x) * (pi_x_a.sin() / pi_x_a)
}

// ---------------------------------------------------------------------------
// Upscaling
// ---------------------------------------------------------------------------

/// Upscale a flat RGB/RGBA pixel buffer using Lanczos-3 interpolation.
///
/// Parameters
/// ----------
/// data : bytes
///     Raw pixel data in row-major order (R, G, B[, A] per pixel).
/// width : int
///     Source image width in pixels.
/// height : int
///     Source image height in pixels.
/// channels : int
///     Number of channels (3 for RGB, 4 for RGBA).
/// scale : int
///     Integer scale factor (e.g. 2, 4, 8).
///
/// Returns
/// -------
/// tuple[bytes, int, int]
///     (upscaled_data, new_width, new_height)
#[pyfunction]
fn lanczos_upscale(
    data: &[u8],
    width: usize,
    height: usize,
    channels: usize,
    scale: usize,
) -> PyResult<(Vec<u8>, usize, usize)> {
    if channels != 3 && channels != 4 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "channels must be 3 (RGB) or 4 (RGBA)",
        ));
    }
    let expected_len = width * height * channels;
    if data.len() != expected_len {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "data length {} does not match {}x{}x{}={}",
            data.len(),
            width,
            height,
            channels,
            expected_len,
        )));
    }
    if scale == 0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "scale must be >= 1",
        ));
    }

    let new_w = width * scale;
    let new_h = height * scale;
    let a: f64 = 3.0; // Lanczos-3

    // Two-pass separable filter: horizontal then vertical.

    // --- horizontal pass ---
    let h_buf: Vec<u8> = (0..height)
        .into_par_iter()
        .flat_map_iter(|y| {
            let row_off = y * width * channels;
            (0..new_w).flat_map(move |x| {
                let src_x = (x as f64 + 0.5) / scale as f64 - 0.5;
                let x0 = (src_x.floor() as isize - a as isize + 1).max(0) as usize;
                let x1 = ((src_x.floor() as isize + a as isize) as usize).min(width - 1);
                let mut sums = vec![0.0f64; channels];
                let mut w_sum = 0.0f64;
                for sx in x0..=x1 {
                    let w = lanczos_weight(src_x - sx as f64, a);
                    w_sum += w;
                    let off = row_off + sx * channels;
                    for c in 0..channels {
                        sums[c] += w * data[off + c] as f64;
                    }
                }
                if w_sum.abs() > f64::EPSILON {
                    for s in sums.iter_mut() {
                        *s /= w_sum;
                    }
                }
                sums.into_iter().map(clamp_u8)
            })
        })
        .collect();

    // --- vertical pass ---
    let h_buf_ref = &h_buf;
    let out: Vec<u8> = (0..new_h)
        .into_par_iter()
        .flat_map_iter(|y| {
            let src_y = (y as f64 + 0.5) / scale as f64 - 0.5;
            let y0 = (src_y.floor() as isize - a as isize + 1).max(0) as usize;
            let y1 = ((src_y.floor() as isize + a as isize) as usize).min(height - 1);
            (0..new_w).flat_map(move |x| {
                let mut sums = vec![0.0f64; channels];
                let mut w_sum = 0.0f64;
                for sy in y0..=y1 {
                    let w = lanczos_weight(src_y - sy as f64, a);
                    w_sum += w;
                    let off = (sy * new_w + x) * channels;
                    for c in 0..channels {
                        sums[c] += w * h_buf_ref[off + c] as f64;
                    }
                }
                if w_sum.abs() > f64::EPSILON {
                    for s in sums.iter_mut() {
                        *s /= w_sum;
                    }
                }
                sums.into_iter().map(clamp_u8)
            })
        })
        .collect();

    Ok((out, new_w, new_h))
}

// ---------------------------------------------------------------------------
// Feature extraction helpers
// ---------------------------------------------------------------------------

/// Compute a simple perceptual hash (pHash) of an image.
///
/// The image is down-sampled internally to 8x8 grayscale and the hash is
/// computed from the DCT-like mean comparison, producing a 64-bit integer.
///
/// Parameters
/// ----------
/// data : bytes
///     Raw RGB pixel data (3 bytes per pixel, row-major).
/// width : int
///     Image width.
/// height : int
///     Image height.
///
/// Returns
/// -------
/// int
///     64-bit perceptual hash.
#[pyfunction]
fn perceptual_hash(data: &[u8], width: usize, height: usize) -> PyResult<u64> {
    if data.len() != width * height * 3 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "data length must equal width * height * 3 (RGB)",
        ));
    }
    // Down-sample to 8x8 grayscale using area averaging.
    let mut gray8x8 = [0.0f64; 64];
    let bw = width as f64 / 8.0;
    let bh = height as f64 / 8.0;
    for by in 0..8 {
        for bx in 0..8 {
            let y0 = (by as f64 * bh) as usize;
            let y1 = (((by + 1) as f64 * bh) as usize).min(height);
            let x0 = (bx as f64 * bw) as usize;
            let x1 = (((bx + 1) as f64 * bw) as usize).min(width);
            let mut sum = 0.0f64;
            let mut count = 0u64;
            for y in y0..y1 {
                for x in x0..x1 {
                    let off = (y * width + x) * 3;
                    let r = data[off] as f64;
                    let g = data[off + 1] as f64;
                    let b = data[off + 2] as f64;
                    sum += 0.299 * r + 0.587 * g + 0.114 * b;
                    count += 1;
                }
            }
            gray8x8[by * 8 + bx] = if count > 0 { sum / count as f64 } else { 0.0 };
        }
    }
    // Compute hash: each bit is 1 if pixel > mean.
    let mean: f64 = gray8x8.iter().sum::<f64>() / 64.0;
    let mut hash: u64 = 0;
    for (i, &val) in gray8x8.iter().enumerate() {
        if val > mean {
            hash |= 1u64 << i;
        }
    }
    Ok(hash)
}

/// Compute the Hamming distance between two 64-bit perceptual hashes.
///
/// Parameters
/// ----------
/// hash_a : int
///     First hash.
/// hash_b : int
///     Second hash.
///
/// Returns
/// -------
/// int
///     Number of differing bits (0 = identical, 64 = maximally different).
#[pyfunction]
fn hamming_distance(hash_a: u64, hash_b: u64) -> u32 {
    (hash_a ^ hash_b).count_ones()
}

/// Compute a normalized color histogram for an RGB image.
///
/// Each channel is quantized into `bins` equal-width buckets.
///
/// Parameters
/// ----------
/// data : bytes
///     Raw RGB pixel data.
/// width : int
///     Image width.
/// height : int
///     Image height.
/// bins : int, default 16
///     Number of histogram bins per channel.
///
/// Returns
/// -------
/// list[float]
///     Flattened histogram of length ``3 * bins``, normalized to sum to 1.
#[pyfunction]
#[pyo3(signature = (data, width, height, bins=16))]
fn color_histogram(
    data: &[u8],
    width: usize,
    height: usize,
    bins: usize,
) -> PyResult<Vec<f64>> {
    if data.len() != width * height * 3 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "data length must equal width * height * 3 (RGB)",
        ));
    }
    if bins == 0 || bins > 256 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "bins must be between 1 and 256",
        ));
    }
    let total_pixels = width * height;
    let mut hist = vec![0u64; 3 * bins];
    let bin_width = 256.0 / bins as f64;
    for i in 0..total_pixels {
        let off = i * 3;
        for c in 0..3 {
            let b = (data[off + c] as f64 / bin_width) as usize;
            let b = b.min(bins - 1);
            hist[c * bins + b] += 1;
        }
    }
    let norm = total_pixels as f64;
    let normalized: Vec<f64> = hist.iter().map(|&v| v as f64 / norm).collect();
    Ok(normalized)
}

/// Compute edge density of a grayscale image using a Sobel-like operator.
///
/// Parameters
/// ----------
/// data : bytes
///     Raw RGB pixel data (3 bytes per pixel).
/// width : int
///     Image width.
/// height : int
///     Image height.
///
/// Returns
/// -------
/// float
///     Fraction of pixels considered edges (0.0 to 1.0).
#[pyfunction]
fn edge_density(data: &[u8], width: usize, height: usize) -> PyResult<f64> {
    if data.len() != width * height * 3 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "data length must equal width * height * 3 (RGB)",
        ));
    }
    if width < 3 || height < 3 {
        return Ok(0.0);
    }
    // Convert to grayscale.
    let gray: Vec<f64> = (0..width * height)
        .map(|i| {
            let off = i * 3;
            0.299 * data[off] as f64 + 0.587 * data[off + 1] as f64 + 0.114 * data[off + 2] as f64
        })
        .collect();

    let threshold = 30.0;
    let mut edge_count: u64 = 0;
    let inner_pixels = (height - 2) * (width - 2);
    for y in 1..height - 1 {
        for x in 1..width - 1 {
            let idx = |dy: usize, dx: usize| gray[(y + dy - 1) * width + (x + dx - 1)];
            let gx = -idx(0, 0) + idx(0, 2) - 2.0 * idx(1, 0) + 2.0 * idx(1, 2) - idx(2, 0)
                + idx(2, 2);
            let gy = -idx(0, 0) - 2.0 * idx(0, 1) - idx(0, 2) + idx(2, 0) + 2.0 * idx(2, 1)
                + idx(2, 2);
            let mag = (gx * gx + gy * gy).sqrt();
            if mag > threshold {
                edge_count += 1;
            }
        }
    }
    Ok(edge_count as f64 / inner_pixels as f64)
}

// ---------------------------------------------------------------------------
// Batch parallel operations
// ---------------------------------------------------------------------------

/// Compute perceptual hashes for a batch of RGB images in parallel.
///
/// Parameters
/// ----------
/// images : list[tuple[bytes, int, int]]
///     List of ``(data, width, height)`` tuples (RGB only).
///
/// Returns
/// -------
/// list[int]
///     Corresponding perceptual hashes.
#[pyfunction]
fn batch_perceptual_hash(
    images: Vec<(Vec<u8>, usize, usize)>,
) -> PyResult<Vec<u64>> {
    let results: Vec<Result<u64, PyErr>> = images
        .par_iter()
        .map(|(data, w, h)| perceptual_hash(data.as_slice(), *w, *h))
        .collect();
    results.into_iter().collect()
}

/// Compute color histograms for a batch of RGB images in parallel.
///
/// Parameters
/// ----------
/// images : list[tuple[bytes, int, int]]
///     List of ``(data, width, height)`` tuples (RGB only).
/// bins : int, default 16
///     Number of histogram bins per channel.
///
/// Returns
/// -------
/// list[list[float]]
///     Corresponding color histograms.
#[pyfunction]
#[pyo3(signature = (images, bins=16))]
fn batch_color_histogram(
    images: Vec<(Vec<u8>, usize, usize)>,
    bins: usize,
) -> PyResult<Vec<Vec<f64>>> {
    let results: Vec<Result<Vec<f64>, PyErr>> = images
        .par_iter()
        .map(|(data, w, h)| color_histogram(data.as_slice(), *w, *h, bins))
        .collect();
    results.into_iter().collect()
}

// ---------------------------------------------------------------------------
// Python module
// ---------------------------------------------------------------------------

/// Native Rust acceleration module for PS2 texture processing.
///
/// Provides fast Lanczos upscaling, perceptual hashing, color histograms,
/// edge density computation, and parallel batch operations.
#[pymodule]
fn texture_ops(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Upscaling
    m.add_function(wrap_pyfunction!(lanczos_upscale, m)?)?;

    // Feature extraction
    m.add_function(wrap_pyfunction!(perceptual_hash, m)?)?;
    m.add_function(wrap_pyfunction!(hamming_distance, m)?)?;
    m.add_function(wrap_pyfunction!(color_histogram, m)?)?;
    m.add_function(wrap_pyfunction!(edge_density, m)?)?;

    // Batch operations
    m.add_function(wrap_pyfunction!(batch_perceptual_hash, m)?)?;
    m.add_function(wrap_pyfunction!(batch_color_histogram, m)?)?;

    Ok(())
}

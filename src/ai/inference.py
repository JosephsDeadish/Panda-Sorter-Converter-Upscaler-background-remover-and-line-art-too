"""
ONNX Inference Runtime
======================
This module is the **production inference path** for all batch pipelines,
automation workflows, and the packaged EXE.

Architecture overview
---------------------
                +---------------------+
                |   Main Application  |
                +----------+----------+
                           |
              +------------+------------+
              |                         |
   +----------v----------+   +----------v----------+
   |  inference.py (YOU  |   | training_pytorch.py  |
   |  ARE HERE)          |   | (optional, lazy)     |
   |                     |   |                      |
   |  • ONNX Runtime     |   |  • PyTorch training  |
   |  • CPU-first        |   |  • Experimentation   |
   |  • Batch pipelines  |   |  • Fine-tuning       |
   |  • EXE-safe         |   |  • Power-user only   |
   +---------------------+   +---------------------+

Why ONNX for inference?
-----------------------
- Starts faster: no JIT compilation on cold start
- Lower memory overhead: ideal for old or low-spec hardware
- Easier multi-threading: session is thread-safe
- Predictable performance: no dynamic graph overhead
- EXE-friendly: onnxruntime ships as a compact native DLL
- No training dependencies: torch/transformers are NOT required

Usage
-----
from ai.inference import OnnxInferenceSession, run_batch_inference

# Single model, single image
session = OnnxInferenceSession("path/to/model.onnx")
if session.is_ready():
    result = session.run(preprocessed_image_array)

# Batch pipeline
results = run_batch_inference("model.onnx", image_list, num_threads=4)

Author: Dead On The Inside / JosephsDeadish
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import numpy as np
    _HAS_NUMPY = True
except (ImportError, OSError):  # pragma: no cover
    np = None  # type: ignore[assignment]
    _HAS_NUMPY = False

# onnxruntime is the ONLY required ML dependency for the main app.
# It is intentionally imported at module level (not lazily) because every
# batch pipeline depends on it.  Graceful degradation: if onnxruntime is
# absent the module stays importable – features just report unavailability.
try:
    import onnxruntime as ort  # type: ignore[import-untyped]
    _ORT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    ort = None  # type: ignore[assignment]
    _ORT_AVAILABLE = False
    logger.warning(
        "onnxruntime is not installed – ONNX inference disabled. "
        "Install with: pip install onnxruntime"
    )
except OSError as _ort_os_err:
    # DLL load failure (e.g. "Not enough memory resources" on Windows CI,
    # missing Visual C++ runtime, or incompatible CPU instruction set).
    ort = None  # type: ignore[assignment]
    _ORT_AVAILABLE = False
    logger.warning(
        "onnxruntime failed to load its native DLL – ONNX inference disabled. "
        "Error: %s", _ort_os_err
    )
except Exception as _ort_err:
    # Catch-all for any other initialisation failure (provider init, etc.)
    ort = None  # type: ignore[assignment]
    _ORT_AVAILABLE = False
    logger.warning(
        "onnxruntime raised an unexpected error during import – "
        "ONNX inference disabled. Error: %s", _ort_err
    )


def is_available() -> bool:
    """Return True if onnxruntime is importable and functional."""
    return _ORT_AVAILABLE


class OnnxInferenceSession:
    """
    Thread-safe ONNX Runtime session wrapper.

    This is the recommended inference entry-point for all pipelines.
    Training code lives in ``training_pytorch.py`` and must NOT be called
    from this module.

    Parameters
    ----------
    model_path:
        Path to an ``.onnx`` model file.
    num_threads:
        Number of CPU threads.  Defaults to 4 – a safe value for batch
        work on both high-end and old hardware.
    providers:
        ORT execution providers.  Defaults to CPU-only to keep the EXE
        lean and deterministic.  Pass ``["CUDAExecutionProvider",
        "CPUExecutionProvider"]`` to enable GPU when available.
    """

    def __init__(
        self,
        model_path: Optional[Path | str] = None,
        num_threads: int = 4,
        providers: Optional[List[str]] = None,
    ) -> None:
        self._model_path: Optional[Path] = Path(model_path) if model_path else None
        self._num_threads = num_threads
        self._providers = providers or ["CPUExecutionProvider"]
        self._session: Optional[Any] = None  # ort.InferenceSession
        self._input_name: Optional[str] = None
        self._output_name: Optional[str] = None
        self._lock = threading.Lock()

        if self._model_path and self._model_path.exists():
            self._load(self._model_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_ready(self) -> bool:
        """Return True when the session is loaded and ready for inference."""
        return _ORT_AVAILABLE and self._session is not None

    def load(self, model_path: Path | str) -> bool:
        """Load (or reload) an ONNX model from *model_path*."""
        return self._load(Path(model_path))

    def run(
        self,
        inputs: "np.ndarray",
        input_name: Optional[str] = None,
    ) -> Optional["np.ndarray"]:
        """
        Run inference on a single pre-processed input array.

        Parameters
        ----------
        inputs:
            NumPy array shaped ``(batch, C, H, W)`` or ``(C, H, W)``.
        input_name:
            Override the automatically detected input tensor name.

        Returns
        -------
        np.ndarray or None
            Raw model outputs (logits / probabilities) or None on error.
        """
        if not self.is_ready():
            logger.warning("OnnxInferenceSession.run() called but session is not ready")
            return None
        if not _HAS_NUMPY:
            logger.error("numpy is required for inference")
            return None

        # Ensure batch dimension
        if inputs.ndim == 3:
            inputs = inputs[np.newaxis, ...]

        feed = {input_name or self._input_name: inputs.astype(np.float32)}
        try:
            with self._lock:
                outputs = self._session.run(None, feed)
            return outputs[0] if outputs else None
        except Exception as exc:
            logger.error("ONNX inference error: %s", exc)
            return None

    def get_input_shape(self) -> Optional[Tuple[int, ...]]:
        """Return the expected input shape, or None if session is not loaded."""
        if self._session is None:
            return None
        try:
            return tuple(self._session.get_inputs()[0].shape)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self, model_path: Path) -> bool:
        if not _ORT_AVAILABLE:
            logger.error("onnxruntime is not installed – cannot load ONNX model")
            return False
        if not model_path.exists():
            logger.error("Model file not found: %s", model_path)
            return False

        try:
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = self._num_threads
            opts.inter_op_num_threads = self._num_threads
            opts.log_severity_level = 3  # suppress INFO spam

            with self._lock:
                self._session = ort.InferenceSession(
                    str(model_path),
                    sess_options=opts,
                    providers=self._providers,
                )
                self._input_name = self._session.get_inputs()[0].name
                self._output_name = self._session.get_outputs()[0].name

            logger.info("ONNX model loaded: %s", model_path.name)
            return True
        except Exception as exc:
            logger.error("Failed to load ONNX model '%s': %s", model_path, exc)
            self._session = None
            return False


# ---------------------------------------------------------------------------
# Batch-inference convenience helper
# ---------------------------------------------------------------------------

def run_batch_inference(
    model_path: Path | str,
    images: List["np.ndarray"],
    num_threads: int = 4,
) -> List[Optional["np.ndarray"]]:
    """
    Run inference on a list of pre-processed image arrays.

    This is the recommended entry-point for batch automation pipelines.
    The session is created once and reused for the entire batch, which
    avoids the per-image initialisation overhead.

    Parameters
    ----------
    model_path:
        Path to an ``.onnx`` file.
    images:
        List of NumPy arrays, each shaped ``(C, H, W)`` or
        ``(1, C, H, W)``.
    num_threads:
        Number of CPU threads to allocate to the ORT session.

    Returns
    -------
    list
        One output array per input image (``None`` on individual errors).
    """
    session = OnnxInferenceSession(model_path, num_threads=num_threads)
    if not session.is_ready():
        logger.error(
            "run_batch_inference: session not ready for model '%s'", model_path
        )
        return [None] * len(images)

    results: List[Optional["np.ndarray"]] = []
    for i, img in enumerate(images):
        try:
            results.append(session.run(img))
        except Exception as exc:
            logger.error("Batch inference error on image %d: %s", i, exc)
            results.append(None)

    return results

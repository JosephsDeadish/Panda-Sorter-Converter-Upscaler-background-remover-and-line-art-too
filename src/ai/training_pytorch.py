"""
PyTorch Training Module (Optional)
====================================
This module is the **optional training path**.  It is intentionally
**separated** from the inference runtime (``inference.py``) so that the
main application and its batch pipelines work without PyTorch installed.

Architecture overview
---------------------
+--------------------------------------------------------------+
|                      TRAINING SIDE                           |
|  (heavy, optional, development / power-user only)            |
|                                                              |
|  training_pytorch.py  <---  YOU ARE HERE                    |
|                                                              |
|  Responsibilities:                                           |
|  • Train custom upscalers / segmentation / classifiers       |
|  • Fine-tune existing models on new texture datasets         |
|  • Experimental model architecture search                    |
|  • Export trained weights to ONNX for the inference path     |
|                                                              |
|  When PyTorch is NOT installed:                              |
|  • Module imports cleanly (no ImportError crash)             |
|  • All public functions return None / False / empty results  |
|  • User receives a clear "install extras" message            |
+--------------------------------------------------------------+
                             |
                export_to_onnx()  (bridge)
                             |
+--------------------------------------------------------------+
|                    INFERENCE SIDE                            |
|  (lightweight, always-on, EXE-safe)                          |
|  inference.py  →  OnnxInferenceSession                       |
+--------------------------------------------------------------+

How to enable training features
---------------------------------
Training features require PyTorch.  Install the training extras with:

    pip install torch torchvision

For GPU acceleration (CUDA):

    # Visit https://pytorch.org/get-started/locally/ for platform commands
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

The main app intentionally does NOT list torch in its minimal requirements
(``requirements-minimal.txt``).  Full requirements are in ``requirements.txt``.

Architectural rule
------------------
**Do not** import this module at the top level of any module that is part
of the main runtime path.  Always use a lazy import inside the function /
class method that needs it, e.g.:

    def _get_trainer():
        try:
            from ai.training_pytorch import PyTorchTrainer
            return PyTorchTrainer()
        except Exception:
            return None

Author: Dead On The Inside / JosephsDeadish
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy PyTorch import
# ---------------------------------------------------------------------------
# PyTorch is NOT imported at module level.  Importing it unconditionally
# would:
#   1. Prevent the app from starting when torch is not installed.
#   2. Bloat PyInstaller analysis with thousands of torch sub-modules.
#   3. Mix training-time concerns into the inference runtime path.
#
# Each function/class that needs torch calls _require_torch() which returns
# the torch module or raises a clear RuntimeError.

def _require_torch() -> Any:
    """
    Return the ``torch`` module, or raise RuntimeError with install instructions.

    Raises
    ------
    RuntimeError
        When torch is not installed or fails to import.
    """
    try:
        import torch  # type: ignore[import-untyped]
        return torch
    except (ImportError, Exception) as exc:
        raise RuntimeError(
            "PyTorch is required for training features but is not installed.\n\n"
            "Install with:\n"
            "    pip install torch torchvision\n\n"
            "Or for GPU (CUDA) support, visit:\n"
            "    https://pytorch.org/get-started/locally/\n\n"
            f"Original error: {exc}"
        ) from exc


def is_pytorch_available() -> bool:
    """Return True if PyTorch is importable in the current environment."""
    try:
        import torch  # type: ignore[import-untyped]  # noqa: F401
        return True
    except Exception:
        return False


# Module-level boolean flag for quick availability checks without a function call.
# Use importlib.util.find_spec instead of is_pytorch_available() so that
# importing this module does NOT eagerly load torch at module level.
# (The architecture test verifies that 'import ai' keeps torch out of sys.modules.)
try:
    import importlib.util as _ilu_pt
    PYTORCH_AVAILABLE: bool = _ilu_pt.find_spec('torch') is not None
    del _ilu_pt
except Exception:
    PYTORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Training mode enum
# ---------------------------------------------------------------------------


class TrainingMode(str, Enum):
    """Selects how the ``PyTorchTrainer`` should approach model fitting.

    The value string matches what ``settings_panel_qt.py`` stores in config
    under ``ai.training_mode`` (lower-cased, underscored).
    """
    STANDARD = "standard"               # full training from scratch / warm start
    FINE_TUNE = "fine-tune_existing"    # freeze base layers, train head
    INCREMENTAL = "incremental_(continual)"  # small LR, replay-buffer style
    EXPORT_ONNX = "export_to_onnx"      # no training — just export to ONNX
    EXPORT_PYTORCH = "export_to_pytorch"  # no training — save .pt checkpoint
    CUSTOM_DATASET = "custom_dataset"   # full train with custom data loader


# ---------------------------------------------------------------------------
# ONNX export bridge  (training → inference handoff)
# ---------------------------------------------------------------------------

def export_to_onnx(
    model: Any,
    output_path: Path | str,
    input_shape: tuple = (1, 3, 224, 224),
    input_names: Optional[List[str]] = None,
    output_names: Optional[List[str]] = None,
    dynamic_axes: Optional[Dict[str, Any]] = None,
    opset_version: int = 17,
) -> bool:
    """
    Export a PyTorch model to ONNX format for use by the inference runtime.

    This is the **bridge** between the training side and the inference side.
    After training or fine-tuning, call this function to produce an ``.onnx``
    file that can be loaded by ``ai.inference.OnnxInferenceSession``.

    Parameters
    ----------
    model:
        A ``torch.nn.Module`` in ``eval()`` mode.
    output_path:
        Destination ``.onnx`` file path.
    input_shape:
        Dummy input tensor shape ``(batch, C, H, W)``.
    input_names:
        ONNX tensor input names.  Defaults to ``["input"]``.
    output_names:
        ONNX tensor output names.  Defaults to ``["output"]``.
    dynamic_axes:
        Dynamic axis config for ONNX export (allows variable batch size).
    opset_version:
        ONNX opset version.  17 is broadly supported by onnxruntime ≥ 1.16.

    Returns
    -------
    bool
        True on success, False on failure.
    """
    try:
        torch = _require_torch()
    except RuntimeError as exc:
        logger.error("export_to_onnx: %s", exc)
        return False

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    input_names = input_names or ["input"]
    output_names = output_names or ["output"]
    dynamic_axes = dynamic_axes or {
        "input": {0: "batch"},
        "output": {0: "batch"},
    }

    try:
        dummy = torch.randn(*input_shape)
        model.eval()
        torch.onnx.export(
            model,
            dummy,
            str(output_path),
            input_names=input_names,
            output_names=output_names,
            dynamic_axes=dynamic_axes,
            opset_version=opset_version,
            do_constant_folding=True,
        )
        logger.info("Model exported to ONNX: %s", output_path)
        return True
    except Exception as exc:
        logger.error("ONNX export failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# PyTorchTrainer  –  optional training scaffold
# ---------------------------------------------------------------------------

class PyTorchTrainer:
    """
    Lightweight training scaffold for custom texture classifiers / upscalers.

    This class is intentionally minimal.  It demonstrates the separation
    between training and inference, and provides the ``export_checkpoint``
    helper to hand off a trained model to the ONNX inference path.

    Instantiation fails gracefully when PyTorch is absent – callers should
    check ``is_pytorch_available()`` or wrap in try/except before use.

    Example
    -------
    ::

        from ai.training_pytorch import PyTorchTrainer, is_pytorch_available

        if not is_pytorch_available():
            print("Install torch to enable training features.")
        else:
            trainer = PyTorchTrainer(model, train_loader, val_loader)
            trainer.train(epochs=10)
            trainer.export_checkpoint("my_model.onnx")
    """

    def __init__(
        self,
        model: Any,
        train_loader: Any,
        val_loader: Optional[Any] = None,
        learning_rate: float = 1e-4,
        device: Optional[str] = None,
    ) -> None:
        torch = _require_torch()  # raises if torch absent

        self._device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self._model = model.to(self._device)
        self._train_loader = train_loader
        self._val_loader = val_loader
        self._lr = learning_rate
        self._history: List[Dict[str, float]] = []

        # Default optimizer – callers can replace via .optimizer attribute
        self.optimizer = torch.optim.AdamW(
            self._model.parameters(), lr=learning_rate
        )
        # Default criterion – suitable for classification
        self.criterion = torch.nn.CrossEntropyLoss()

        logger.info(
            "PyTorchTrainer initialized on device=%s lr=%.2e",
            self._device,
            learning_rate,
        )

    # ------------------------------------------------------------------
    # Training loop
    # ------------------------------------------------------------------

    def train(
        self,
        epochs: int = 10,
        progress_callback: Optional[Any] = None,
    ) -> List[Dict[str, float]]:
        """
        Run the training loop.

        Parameters
        ----------
        epochs:
            Number of full passes over ``train_loader``.
        progress_callback:
            Optional callable ``(epoch, total_epochs, metrics_dict)`` called
            after each epoch.  Useful for updating a UI progress bar.

        Returns
        -------
        list of dict
            Training history – one entry per epoch with keys
            ``epoch``, ``train_loss``, ``val_loss`` (if val_loader supplied).
        """
        torch = _require_torch()

        for epoch in range(1, epochs + 1):
            train_loss = self._run_epoch(torch, training=True)
            metrics: Dict[str, float] = {
                "epoch": float(epoch),
                "train_loss": train_loss,
            }

            if self._val_loader is not None:
                val_loss = self._run_epoch(torch, training=False)
                metrics["val_loss"] = val_loss

            self._history.append(metrics)
            logger.info("Epoch %d/%d – %s", epoch, epochs, metrics)

            if progress_callback is not None:
                try:
                    progress_callback(epoch, epochs, metrics)
                except Exception:
                    pass  # Never let UI errors abort training

        return self._history

    def _run_epoch(self, torch: Any, training: bool) -> float:
        loader = self._train_loader if training else self._val_loader
        self._model.train(training)
        total_loss = 0.0
        n_batches = 0

        ctx = torch.enable_grad() if training else torch.no_grad()
        with ctx:
            for inputs, targets in loader:
                inputs = inputs.to(self._device)
                targets = targets.to(self._device)

                if training:
                    self.optimizer.zero_grad()

                outputs = self._model(inputs)
                loss = self.criterion(outputs, targets)

                if training:
                    loss.backward()
                    self.optimizer.step()

                total_loss += loss.item()
                n_batches += 1

        return total_loss / max(n_batches, 1)

    # ------------------------------------------------------------------
    # Checkpoint / export
    # ------------------------------------------------------------------

    def save_checkpoint(self, path: Path | str) -> bool:
        """Save a PyTorch ``.pth`` checkpoint."""
        try:
            torch = _require_torch()
            torch.save(
                {
                    "model_state_dict": self._model.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "history": self._history,
                },
                str(path),
            )
            logger.info("Checkpoint saved: %s", path)
            return True
        except Exception as exc:
            logger.error("Failed to save checkpoint: %s", exc)
            return False

    def export_checkpoint(
        self,
        onnx_path: Path | str,
        input_shape: tuple = (1, 3, 224, 224),
    ) -> bool:
        """
        Export the current model weights to ONNX for the inference runtime.

        This is the recommended hand-off point from training to inference.
        The resulting ``.onnx`` file can be loaded directly by
        ``ai.inference.OnnxInferenceSession``.
        """
        return export_to_onnx(self._model, onnx_path, input_shape=input_shape)

    # ------------------------------------------------------------------
    # Named export methods (convenience aliases for the public API)
    # ------------------------------------------------------------------

    def export_onnx(
        self,
        output_path: 'Path | str | None' = None,
        input_shape: tuple = (1, 3, 224, 224),
    ) -> bool:
        """Export the current model to ONNX format.

        Alias for :meth:`export_checkpoint` with a descriptive name that
        matches the ``TrainingMode.EXPORT_ONNX`` display text.

        Parameters
        ----------
        output_path:
            Destination ``.onnx`` file path.  Defaults to
            ``model_export.onnx`` in the current working directory.
        input_shape:
            ONNX input tensor shape ``(batch, channels, height, width)``.
        """
        dest = Path(output_path or 'model_export.onnx')
        return self.export_checkpoint(dest, input_shape=input_shape)

    def export_pytorch(
        self,
        output_path: 'Path | str | None' = None,
    ) -> bool:
        """Save current model weights as a PyTorch ``.pt`` checkpoint.

        Alias for :meth:`save_checkpoint` with a descriptive name that
        matches the ``TrainingMode.EXPORT_PYTORCH`` display text.

        Parameters
        ----------
        output_path:
            Destination ``.pt`` file path.  Defaults to
            ``model_export.pt`` in the current working directory.
        """
        dest = Path(output_path or 'model_export.pt')
        return self.save_checkpoint(dest)

    # ------------------------------------------------------------------
    # Training mode variants
    # ------------------------------------------------------------------

    def fine_tune(
        self,
        epochs: int = 5,
        unfreeze_layers: int = 2,
        progress_callback: Optional[Any] = None,
    ) -> List[Dict[str, float]]:
        """Fine-tune: freeze all but the last *unfreeze_layers* layers.

        Useful when adapting a pre-trained model to a new texture domain with
        minimal training time and reduced risk of catastrophic forgetting.
        """
        torch = _require_torch()
        params = list(self._model.parameters())
        # Freeze all layers
        for p in params:
            p.requires_grad_(False)
        # Unfreeze the last N layers
        for p in params[-max(unfreeze_layers, 1):]:
            p.requires_grad_(True)
        # Re-create optimizer on unfrozen params only
        self.optimizer = torch.optim.AdamW(
            filter(lambda p: p.requires_grad, self._model.parameters()),
            lr=self._lr * 0.1,  # lower LR for fine-tuning
        )
        result = self.train(epochs=epochs, progress_callback=progress_callback)
        # Unfreeze everything after fine-tuning finishes
        for p in params:
            p.requires_grad_(True)
        return result

    def incremental_train(
        self,
        epochs: int = 2,
        replay_fraction: float = 0.2,
        progress_callback: Optional[Any] = None,
    ) -> List[Dict[str, float]]:
        """Incremental / continual learning with very low learning rate.

        Intended for adding new texture classes without forgetting existing
        ones.  Uses a lower LR and (optionally) a small replay buffer from
        the existing train loader.

        *replay_fraction* is stored for future use when a replay buffer is
        provided by the caller.  Currently functions as a standard train with
        reduced LR.
        """
        original_lr = self._lr
        torch = _require_torch()
        for g in self.optimizer.param_groups:
            g['lr'] = original_lr * 0.01   # very small LR for continual learning
        result = self.train(epochs=epochs, progress_callback=progress_callback)
        for g in self.optimizer.param_groups:
            g['lr'] = original_lr           # restore
        return result

    def run_mode(
        self,
        mode: 'TrainingMode | str',
        epochs: int = 10,
        output_path: Optional['Path | str'] = None,
        progress_callback: Optional[Any] = None,
    ) -> 'List[Dict[str, float]] | bool':
        """Dispatch to the correct training/export variant based on *mode*.

        This is the single entry point called by the AI Settings panel when
        the user presses "Start Training".

        Parameters
        ----------
        mode:
            A ``TrainingMode`` enum value or the raw string stored in config
            under ``ai.training_mode``.
        epochs:
            Number of epochs (ignored for export modes).
        output_path:
            Destination path for ONNX / PyTorch export modes.
        progress_callback:
            Optional ``(epoch, total, metrics)`` callable.

        Returns
        -------
        list of dicts (training history) for train modes,
        bool (success flag) for export modes.
        """
        if isinstance(mode, str):
            try:
                mode = TrainingMode(mode)
            except ValueError:
                # Accept partial / display-text strings from the combo box
                _normalised = mode.lower().replace(' ', '_').replace('-', '_')
                _map = {
                    'standard': TrainingMode.STANDARD,
                    'fine_tune_existing': TrainingMode.FINE_TUNE,
                    'incremental_continual': TrainingMode.INCREMENTAL,
                    'export_to_onnx': TrainingMode.EXPORT_ONNX,
                    'export_to_pytorch': TrainingMode.EXPORT_PYTORCH,
                    'custom_dataset': TrainingMode.CUSTOM_DATASET,
                }
                mode = _map.get(_normalised, TrainingMode.STANDARD)

        if mode == TrainingMode.EXPORT_ONNX:
            dest = Path(output_path or 'model_export.onnx')
            return self.export_checkpoint(dest, input_shape=(1, 3, 224, 224))
        elif mode == TrainingMode.EXPORT_PYTORCH:
            dest = Path(output_path or 'model_export.pt')
            return self.save_checkpoint(dest)
        elif mode == TrainingMode.FINE_TUNE:
            return self.fine_tune(epochs=epochs, progress_callback=progress_callback)
        elif mode == TrainingMode.INCREMENTAL:
            return self.incremental_train(epochs=epochs,
                                          progress_callback=progress_callback)
        else:
            # STANDARD or CUSTOM_DATASET — full train
            return self.train(epochs=epochs, progress_callback=progress_callback)

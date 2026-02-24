"""
Game Texture Sorter - AI Model System
Comprehensive AI-powered texture classification with offline and online support
Author: Dead On The Inside / JosephsDeadish

Architecture
------------
Inference (always-on, EXE-safe):
    ai.inference        – OnnxInferenceSession, run_batch_inference
    ai.offline_model    – OfflineModel (ONNX wrapper)
    ai.online_model     – OnlineModel (optional API)
    ai.model_manager    – ModelManager (orchestration)

Training (optional, requires PyTorch):
    ai.training_pytorch – PyTorchTrainer, export_to_onnx
    ai.training         – TrainingDataStore, IncrementalLearner (SQLite)

Packaging:
    ai.model_exporter   – ModelExporter/Importer (.ps2model format)
"""

from .offline_model import OfflineModel, create_default_model, get_default_model_path
from .online_model import OnlineModel, create_online_model_from_config, RateLimitConfig
from .model_manager import ModelManager
from .training import TrainingDataStore, IncrementalLearner
from .model_exporter import ModelExporter, ModelImporter, ModelPackage, validate_ps2model_file

# Inference runtime (ONNX) – always available, no torch dependency
from .inference import OnnxInferenceSession, run_batch_inference, is_available as onnx_available, ONNX_AVAILABLE

# PyTorch training helpers – optional; callers must check is_pytorch_available()
# before instantiating PyTorchTrainer to avoid ImportError when torch is absent.
# NOTE: PYTORCH_AVAILABLE is derived via importlib.util.find_spec so that
# importing this package does NOT eagerly import torch at module level.
# The training_pytorch module itself is only loaded by callers that explicitly
# instantiate PyTorchTrainer (which will import torch at that point).
try:
    from .training_pytorch import is_pytorch_available, export_to_onnx, PyTorchTrainer, TrainingMode  # type: ignore[assignment]
except (ImportError, OSError, RuntimeError):
    def is_pytorch_available() -> bool:  # type: ignore[misc]
        return False
    def export_to_onnx(*_a, **_kw):  # type: ignore[misc]
        raise RuntimeError("PyTorch not available")
    class PyTorchTrainer:  # type: ignore[no-redef]
        pass
    class TrainingMode:  # type: ignore[no-redef]
        STANDARD = "standard"
        FINE_TUNE = "fine-tune_existing"
        INCREMENTAL = "incremental_(continual)"
        EXPORT_ONNX = "export_to_onnx"
        EXPORT_PYTORCH = "export_to_pytorch"
        CUSTOM_DATASET = "custom_dataset"

try:
    import importlib.util as _ilu
    PYTORCH_AVAILABLE: bool = _ilu.find_spec('torch') is not None
    del _ilu
except Exception:
    PYTORCH_AVAILABLE = False

__all__ = [
    # Offline model
    'OfflineModel',
    'create_default_model',
    'get_default_model_path',
    
    # Online model
    'OnlineModel',
    'create_online_model_from_config',
    'RateLimitConfig',
    
    # Model manager
    'ModelManager',
    
    # Training system (SQLite-backed incremental learning)
    'TrainingDataStore',
    'IncrementalLearner',
    
    # Export/Import
    'ModelExporter',
    'ModelImporter',
    'ModelPackage',
    'validate_ps2model_file',

    # Inference runtime (ONNX)
    'OnnxInferenceSession',
    'run_batch_inference',
    'onnx_available',
    'ONNX_AVAILABLE',

    # PyTorch training (optional)
    'is_pytorch_available',
    'PYTORCH_AVAILABLE',
    'export_to_onnx',
    'PyTorchTrainer',
    'TrainingMode',
]

__version__ = '1.0.0'
__author__ = 'Dead On The Inside / JosephsDeadish'

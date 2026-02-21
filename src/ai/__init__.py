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
from .inference import OnnxInferenceSession, run_batch_inference, is_available as onnx_available

# PyTorch training helpers – optional; callers must check is_pytorch_available()
# before instantiating PyTorchTrainer to avoid ImportError when torch is absent.
from .training_pytorch import (
    is_pytorch_available,
    export_to_onnx,
    PyTorchTrainer,
)

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

    # PyTorch training (optional)
    'is_pytorch_available',
    'export_to_onnx',
    'PyTorchTrainer',
]

__version__ = '1.0.0'
__author__ = 'Dead On The Inside / JosephsDeadish'

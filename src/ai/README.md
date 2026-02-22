# AI Model System - Technical Documentation

**Author:** Dead On The Inside / JosephsDeadish  
**Version:** 1.0.0

## Overview

The Game Texture Sorter AI Model System provides comprehensive texture classification capabilities with both offline and online model support, user feedback learning, and community model sharing.

The system uses a **hybrid PyTorch + ONNX architecture**: inference pipelines and the packaged EXE use ONNX Runtime (lightweight, EXE-safe), while training / experimentation uses PyTorch (optional, not required for normal app operation).

## Architecture

### Hybrid PyTorch + ONNX Design

```
┌─────────────────────────────────────────────┐
│            INFERENCE SIDE                   │
│  (always-on, EXE-safe, no torch required)   │
│                                             │
│  inference.py → OnnxInferenceSession        │
│  offline_model.py → OfflineModel            │
│  • Batch upscaling / classification         │
│  • Automation pipelines                     │
│  • CPU-first, low memory, fast startup      │
│  Install: pip install onnxruntime           │
└─────────────────┬───────────────────────────┘
                  │  export_to_onnx() / .onnx file
┌─────────────────▼───────────────────────────┐
│            TRAINING SIDE                    │
│  (optional — requires PyTorch)              │
│                                             │
│  training_pytorch.py → PyTorchTrainer       │
│  • Custom upscaler / classifier training    │
│  • Fine-tuning segmentation models          │
│  • export_checkpoint() → .onnx handoff      │
│  Install: pip install torch torchvision     │
└─────────────────────────────────────────────┘
```

**Key rule:** Training deps must NOT be required for normal app operation or the EXE build.  
The inference side (`inference.py`) is imported unconditionally; the training side (`training_pytorch.py`) lazy-imports torch only when a training function is actually called.

### Module Reference

#### Inference (always-on)

1. **`inference.py`** — `OnnxInferenceSession`, `run_batch_inference`
   - Primary inference entry-point for all batch pipelines
   - Thread-safe ONNX Runtime session wrapper
   - CPU-first with optional GPU via `providers` argument
   - Gracefully degrades if onnxruntime is absent
   - **No torch dependency**

2. **`offline_model.py`** — `OfflineModel`
   - ONNX Runtime wrapper for texture classification
   - MobileNetV3-like model support
   - Thread-safe operations with automatic image preprocessing

3. **`online_model.py`** — `OnlineModel`
   - Optional OpenAI CLIP API integration
   - Configurable API endpoints, rate limiting, timeout handling
   - Graceful fallback on errors

4. **`model_manager.py`** — `ModelManager`
   - Orchestrates offline and online models
   - Implements fallback logic (online → offline)
   - Blends predictions (confidence-weighted, max, average)
   - Thread-safe model switching

#### Training (optional — requires PyTorch)

5. **`training_pytorch.py`** — `PyTorchTrainer`, `export_to_onnx`
   - Optional PyTorch training scaffold
   - `is_pytorch_available()` — check before instantiating trainer
   - `PyTorchTrainer` — training loop with progress callback support
   - `export_to_onnx()` — bridge: trained model → `.onnx` file
   - `export_checkpoint()` — convenience wrapper on `PyTorchTrainer`
   - Raises `RuntimeError` with install instructions when torch is absent

6. **`training.py`** — `TrainingDataStore`, `IncrementalLearner`
   - SQLite-backed user correction storage (no torch dependency)
   - Incremental learning from user feedback
   - Export/import training history and category statistics

#### Packaging

7. **`model_exporter.py`** — `ModelExporter`, `ModelImporter`
   - Export models as `.ps2model` packages
   - Import community-shared models
   - Model versioning, validation, metadata, and documentation

## Usage Examples

### Batch Inference (ONNX — always-on)

```python
from ai.inference import OnnxInferenceSession, run_batch_inference, is_available
import numpy as np

# Check availability
print("ONNX available:", is_available())

# Single image
session = OnnxInferenceSession("models/classifier.onnx", num_threads=4)
if session.is_ready():
    image = np.random.randn(1, 3, 224, 224).astype(np.float32)
    logits = session.run(image)         # shape: (1, num_classes)

# Batch pipeline
images = [np.random.randn(3, 224, 224).astype(np.float32) for _ in range(100)]
results = run_batch_inference("models/classifier.onnx", images)
```

### Training a Custom Model (PyTorch — optional)

```python
from ai.training_pytorch import is_pytorch_available, PyTorchTrainer

if not is_pytorch_available():
    print("Install PyTorch to enable training: pip install torch torchvision")
else:
    import torch, torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    # Build a simple classifier
    model = nn.Sequential(
        nn.Flatten(),
        nn.Linear(3 * 224 * 224, 256),
        nn.ReLU(),
        nn.Linear(256, 50),    # 50 texture categories
    )

    # Toy dataset
    X = torch.randn(200, 3, 224, 224)
    y = torch.randint(0, 50, (200,))
    loader = DataLoader(TensorDataset(X, y), batch_size=16)

    trainer = PyTorchTrainer(model, loader, learning_rate=1e-3)

    # Optional progress callback for UI integration
    def on_epoch(epoch, total, metrics):
        print(f"  Epoch {epoch}/{total}: loss={metrics['train_loss']:.4f}")

    trainer.train(epochs=5, progress_callback=on_epoch)

    # Export to ONNX for use in inference pipeline
    trainer.export_checkpoint("models/my_classifier.onnx")
    # Now load it back with OnnxInferenceSession for batch processing
```

### Basic Usage (ModelManager)

```python
from ai import ModelManager

# Create manager with default settings
manager = ModelManager.create_default()

# Classify a texture
import numpy as np
from PIL import Image

image = np.array(Image.open("texture.dds"))
predictions = manager.predict(image, top_k=5)

for pred in predictions:
    print(f"{pred['category']}: {pred['confidence']:.2%}")
```

### With Configuration

```python
from ai import ModelManager
from pathlib import Path

config = {
    'offline_enabled': True,
    'offline_model_path': Path("models/my_model.onnx"),
    'online_enabled': True,
    'online': {
        'enabled': True,
        'api_key': 'your-api-key',
        'api_url': 'https://api.openai.com/v1',
        'model': 'clip-vit-base-patch32',
        'timeout': 30,
        'max_requests_per_minute': 60
    },
    'blend_mode': 'confidence_weighted',
    'min_confidence': 0.3
}

manager = ModelManager.create_default(config)
```

### User Feedback Learning

```python
from ai import IncrementalLearner

learner = IncrementalLearner()

# User corrects a prediction
learner.record_correction(
    texture_path="textures/metal_01.dds",
    corrected_category="metal",
    original_predictions=[
        {'category': 'stone', 'confidence': 0.7}
    ]
)

# Apply learned adjustments to future predictions
predictions = manager.predict(image)
adjusted = learner.adjust_predictions(predictions)
```

### Model Export/Import

```python
from ai import ModelExporter, ModelImporter
from pathlib import Path

# Export a model
exporter = ModelExporter()
exporter.export_model(
    model_path=Path("models/my_model.onnx"),
    output_path=Path("exports/my_model.ps2model"),
    name="Custom PS2 Texture Classifier",
    version="1.0.0",
    author="Your Name",
    categories=["metal", "stone", "wood", "fabric"],
    description="Custom trained model for PS2 textures"
)

# Import a model
importer = ModelImporter()
result = importer.import_model(Path("exports/my_model.ps2model"))
if result:
    print(f"Model installed to: {result['install_dir']}")
```

## Offline Model Format

### ONNX Model Requirements

- **Format:** ONNX (Open Neural Network Exchange)
- **Input:** `(batch, channels, height, width)` - typically (1, 3, 224, 224)
- **Output:** `(batch, num_classes)` - logits or probabilities
- **Normalization:** ImageNet mean/std expected
  - Mean: [0.485, 0.456, 0.406]
  - Std: [0.229, 0.224, 0.225]

### Model Metadata

Models should include metadata in ONNX custom_metadata_map:
```json
{
    "categories": ["category1", "category2", ...],
    "version": "1.0.0",
    "description": "Model description"
}
```

### Creating ONNX Models

From PyTorch:
```python
import torch
import torch.onnx

# Load your trained model
model = YourModel()
model.load_state_dict(torch.load("model.pth"))
model.eval()

# Export to ONNX
dummy_input = torch.randn(1, 3, 224, 224)
torch.onnx.export(
    model,
    dummy_input,
    "model.onnx",
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={'input': {0: 'batch'}, 'output': {0: 'batch'}}
)
```

## .ps2model Package Format

### Package Structure

```
my_model.ps2model (ZIP archive)
├── model.onnx          # ONNX model file
├── metadata.json       # Model metadata
├── categories.json     # Category definitions
├── training_data.json  # Optional training data
└── README.md          # Optional documentation
```

### metadata.json Schema

```json
{
    "package_version": "1.0",
    "name": "Model Name",
    "version": "1.0.0",
    "author": "Author Name",
    "description": "Model description",
    "license": "MIT",
    "created": "2024-01-01T00:00:00",
    "format": "onnx",
    "num_categories": 50,
    "tags": ["ps2", "textures", "classification"],
    "model_hash": "sha256_hash",
    "model_size": 12345678,
    "framework": "onnxruntime",
    "compatibility": {
        "min_app_version": "1.0.0",
        "python_version": "3.8+"
    }
}
```

## Online Model Configuration

### OpenAI CLIP Example

```python
config = {
    'enabled': True,
    'api_key': 'sk-...',
    'api_url': 'https://api.openai.com/v1',
    'model': 'clip-vit-base-patch32',
    'timeout': 30,
    'max_requests_per_minute': 60,
    'max_requests_per_hour': 1000
}
```

### Custom API Endpoint

The system supports custom API endpoints. Your API should implement:

**Endpoint:** `POST /classify`

**Request:**
```json
{
    "model": "model_name",
    "image": "data:image/jpeg;base64,...",
    "labels": ["metal", "stone", "wood"],
    "top_k": 5
}
```

**Response:**
```json
{
    "predictions": [
        {"label": "metal", "score": 0.85},
        {"label": "stone", "score": 0.10},
        {"label": "wood", "score": 0.05}
    ]
}
```

## Prediction Blending Modes

### Confidence Weighted (Default)

Weights predictions by each model's total confidence:
```
weight_online = sum(online_confidences) / total_confidence
weight_offline = sum(offline_confidences) / total_confidence
final_confidence = (confidence * weight) averaged across models
```

### Max

Takes maximum confidence for each category:
```
final_confidence[category] = max(online_conf, offline_conf)
```

### Average

Simple average of confidence scores:
```
final_confidence[category] = mean(online_conf, offline_conf)
```

## Training Data Format

### Correction Record

```json
{
    "id": 1,
    "texture_path": "/path/to/texture.dds",
    "texture_hash": "sha256_hash",
    "original_category": "stone",
    "corrected_category": "metal",
    "confidence": 0.7,
    "timestamp": "2024-01-01T00:00:00",
    "image_width": 512,
    "image_height": 512,
    "image_channels": 3,
    "metadata": {"key": "value"}
}
```

## Thread Safety

All components are thread-safe:
- **OfflineModel:** Uses `threading.Lock` for model access
- **OnlineModel:** Uses `threading.Lock` for rate limiting
- **ModelManager:** Uses `threading.RLock` for stats and model switching
- **TrainingDataStore:** Uses `threading.RLock` for database access

## Performance Considerations

### Memory Usage

- **Offline Model:** ~10-50 MB per model (MobileNetV3)
- **Training Database:** ~1 KB per correction record
- **Batch Processing:** Processes images sequentially to control memory

### Inference Speed

- **Offline (CPU):** ~50-200ms per image (depends on model size)
- **Online (API):** ~500-2000ms per image (network dependent)
- **Blending Overhead:** <1ms

### Optimization Tips

1. Use offline models for bulk processing
2. Enable online models only for uncertain predictions
3. Adjust `num_threads` based on CPU cores
4. Cache predictions for frequently seen textures

## Error Handling

All components implement graceful fallback:

1. **Online fails** → Falls back to offline
2. **Offline fails** → Returns empty predictions
3. **No models available** → Falls back to rule-based classification
4. **Import fails** → Preserves existing models

## Logging

All components use Python's `logging` module:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Module-specific loggers
logger = logging.getLogger('ai.model_manager')
logger.setLevel(logging.DEBUG)
```

## Future Enhancements

- [x] Hybrid PyTorch + ONNX architecture
- [x] Batch inference pipeline (`run_batch_inference`)
- [x] PyTorch training scaffold (`PyTorchTrainer`, `export_to_onnx`)
- [x] Training → ONNX bridge (`export_checkpoint`)
- [ ] GPU acceleration (CUDA) in `OnnxInferenceSession` (pass `providers` arg)
- [ ] Model fine-tuning UI (training quest integration)
- [ ] Automatic model updates
- [ ] Community model marketplace
- [ ] Prediction caching system
- [ ] Model performance analytics

## License

MIT License - See LICENSE file for details

## Contributing

For model contributions:
1. Train on diverse PS2 texture dataset
2. Export as `.ps2model` package
3. Document training process in README
4. Test with validation set
5. Submit for review

## Support

For issues or questions:
- Documentation: See main README.md

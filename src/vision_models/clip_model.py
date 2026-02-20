"""
CLIP Model Implementation
Image-text embedding model for texture classification
Author: Dead On The Inside / JosephsDeadish
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False
from pathlib import Path

logger = logging.getLogger(__name__)

# Check for dependencies
try:
    import torch
    import torch.nn.functional as F
    from PIL import Image
    TORCH_AVAILABLE = True
except ImportError as e:
    TORCH_AVAILABLE = False
    logger.warning(f"PyTorch not available: {e}")
    logger.warning("CLIP model will be disabled.")
except OSError as e:
    # Handle DLL initialization errors (e.g., missing CUDA DLLs)
    TORCH_AVAILABLE = False
    logger.warning(f"PyTorch DLL initialization failed: {e}")
    logger.warning("This may occur if CUDA runtime libraries are missing.")
    logger.warning("CLIP model will be disabled. The application will use CPU-only features.")
except Exception as e:
    TORCH_AVAILABLE = False
    logger.warning(f"Unexpected error loading PyTorch: {e}")
    logger.warning("CLIP model will be disabled.")

try:
    from transformers import CLIPProcessor, CLIPModel as HFCLIPModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. CLIP model disabled.")

try:
    import open_clip
    OPEN_CLIP_AVAILABLE = True
except ImportError:
    OPEN_CLIP_AVAILABLE = False
    logger.debug("open_clip not available. Using transformers CLIP.")


class CLIPModel:
    """
    CLIP (Contrastive Language-Image Pre-training) model for texture analysis.
    
    Features:
    - Compare images to text descriptions
    - Compare images to images (similarity)
    - Generate image embeddings
    - Strong performance on stylized and low-res textures
    """
    
    def __init__(
        self,
        model_name: str = 'openai/clip-vit-base-patch32',
        device: Optional[str] = None,
        use_open_clip: bool = False
    ):
        """
        Initialize CLIP model.
        
        Args:
            model_name: HuggingFace model name or open_clip model name
            device: Device to use ('cuda', 'cpu', or None for auto)
            use_open_clip: Use open_clip instead of transformers
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for CLIP model")
        
        self.use_open_clip = use_open_clip and OPEN_CLIP_AVAILABLE
        
        # Determine device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Initializing CLIP model on device: {self.device}")
        
        # Load model
        if self.use_open_clip:
            self._load_open_clip(model_name)
        else:
            self._load_transformers_clip(model_name)
        
        logger.info(f"CLIP model loaded: {model_name}")
    
    def _load_transformers_clip(self, model_name: str):
        """Load CLIP model from transformers."""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers is required for CLIP model")
        
        self.model = HFCLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()
    
    def _load_open_clip(self, model_name: str):
        """Load CLIP model from open_clip."""
        if not OPEN_CLIP_AVAILABLE:
            raise RuntimeError("open_clip is required for open_clip models")
        
        # Parse model name (format: "model_name,pretrained")
        if ',' in model_name:
            model, pretrained = model_name.split(',')
        else:
            model = model_name
            pretrained = 'openai'
        
        self.model, _, self.processor = open_clip.create_model_and_transforms(
            model,
            pretrained=pretrained,
            device=self.device
        )
        self.tokenizer = open_clip.get_tokenizer(model)
        self.model.eval()
    
    def encode_image(
        self,
        image: Union[np.ndarray, Image.Image, Path]
    ) -> np.ndarray:
        """
        Encode image to embedding vector.
        
        Args:
            image: Input image (numpy array, PIL Image, or Path)
            
        Returns:
            Image embedding as numpy array
        """
        # Load image if path
        if isinstance(image, Path):
            image = Image.open(image).convert('RGB')
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        with torch.no_grad():
            if self.use_open_clip:
                image_input = self.processor(image).unsqueeze(0).to(self.device)
                embedding = self.model.encode_image(image_input)
            else:
                inputs = self.processor(images=image, return_tensors="pt").to(self.device)
                embedding = self.model.get_image_features(**inputs)
            
            # Normalize embedding
            embedding = F.normalize(embedding, p=2, dim=-1)
            
            return embedding.cpu().numpy()[0]
    
    def encode_text(
        self,
        text: Union[str, List[str]]
    ) -> np.ndarray:
        """
        Encode text to embedding vector(s).
        
        Args:
            text: Input text or list of texts
            
        Returns:
            Text embedding(s) as numpy array
        """
        if isinstance(text, str):
            text = [text]
        
        with torch.no_grad():
            if self.use_open_clip:
                text_tokens = self.tokenizer(text).to(self.device)
                embedding = self.model.encode_text(text_tokens)
            else:
                inputs = self.processor(text=text, return_tensors="pt", padding=True).to(self.device)
                embedding = self.model.get_text_features(**inputs)
            
            # Normalize embedding
            embedding = F.normalize(embedding, p=2, dim=-1)
            
            return embedding.cpu().numpy()
    
    def compare_image_text(
        self,
        image: Union[np.ndarray, Image.Image, Path],
        texts: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Compare image to multiple text descriptions.
        
        Args:
            image: Input image
            texts: List of text descriptions
            
        Returns:
            List of dictionaries with text and similarity score
        """
        # Encode image
        image_embedding = self.encode_image(image)
        
        # Encode texts
        text_embeddings = self.encode_text(texts)
        
        # Calculate similarities
        similarities = np.dot(text_embeddings, image_embedding)
        
        # Convert to probabilities
        probs = self._softmax(similarities)
        
        # Create results
        results = [
            {
                'text': text,
                'similarity': float(sim),
                'probability': float(prob)
            }
            for text, sim, prob in zip(texts, similarities, probs)
        ]
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results
    
    def compare_images(
        self,
        image1: Union[np.ndarray, Image.Image, Path],
        image2: Union[np.ndarray, Image.Image, Path]
    ) -> float:
        """
        Compare two images for similarity.
        
        Args:
            image1: First image
            image2: Second image
            
        Returns:
            Cosine similarity score (0 to 1)
        """
        # Encode both images
        emb1 = self.encode_image(image1)
        emb2 = self.encode_image(image2)
        
        # Calculate cosine similarity
        similarity = np.dot(emb1, emb2)
        
        return float(similarity)
    
    def classify_texture(
        self,
        image: Union[np.ndarray, Image.Image, Path],
        categories: List[str],
        category_descriptions: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Classify texture into categories using text descriptions.
        
        Args:
            image: Input texture image
            categories: List of category names
            category_descriptions: Optional dict mapping categories to descriptions
            
        Returns:
            List of predictions with category, similarity, and probability
        """
        # Create text prompts
        if category_descriptions:
            texts = [
                category_descriptions.get(cat, f"a {cat} texture")
                for cat in categories
            ]
        else:
            texts = [f"a {cat} texture" for cat in categories]
        
        # Compare image to texts
        results = self.compare_image_text(image, texts)
        
        # Add category names to results
        for result, category in zip(results, categories):
            result['category'] = category
        
        return results
    
    def batch_encode_images(
        self,
        images: List[Union[np.ndarray, Image.Image, Path]],
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Encode multiple images in batches.
        
        Args:
            images: List of images
            batch_size: Batch size for processing
            
        Returns:
            Array of image embeddings (N, embedding_dim)
        """
        embeddings = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            
            # Process batch
            batch_embeddings = [self.encode_image(img) for img in batch]
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)
    
    @staticmethod
    def _softmax(x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        """Apply softmax to convert similarities to probabilities."""
        x = x / temperature
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum()
    
    def fine_tune(
        self,
        images: List[Union[np.ndarray, Image.Image, Path]],
        labels: List[str],
        learning_rate: float = 1e-5,
        epochs: int = 10,
        batch_size: int = 16
    ) -> Dict[str, Any]:
        """
        Fine-tune CLIP model on a custom image–text dataset using
        contrastive loss (symmetric cross-entropy over cosine similarities).

        Args:
            images: List of training images
            labels: List of text labels for images (same length as images)
            learning_rate: Learning rate for AdamW optimizer
            epochs: Number of training epochs
            batch_size: Batch size per step

        Returns:
            Dictionary with training metrics (losses per epoch)

        Raises:
            RuntimeError: If PyTorch is not available
            ValueError:  If *images* and *labels* have mismatched length
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for fine-tuning")
        if len(images) != len(labels):
            raise ValueError(
                f"images ({len(images)}) and labels ({len(labels)}) must have the same length"
            )

        logger.info(
            f"Starting fine-tune: {len(images)} samples, "
            f"lr={learning_rate}, epochs={epochs}, bs={batch_size}"
        )

        # Switch to training mode
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)

        epoch_losses: List[float] = []

        try:
            for epoch in range(epochs):
                running_loss = 0.0
                steps = 0

                # Shuffle indices each epoch
                indices = np.random.permutation(len(images))

                for start in range(0, len(indices), batch_size):
                    batch_idx = indices[start : start + batch_size]

                    # --- Prepare image batch ---
                    pil_images: List[Image.Image] = []
                    for i in batch_idx:
                        img = images[i]
                        if isinstance(img, Path):
                            img = Image.open(img).convert("RGB")
                        elif isinstance(img, np.ndarray):
                            img = Image.fromarray(img)
                        pil_images.append(img)

                    batch_labels = [labels[i] for i in batch_idx]

                    # --- Encode ---
                    if self.use_open_clip:
                        image_input = torch.stack(
                            [self.processor(im) for im in pil_images]
                        ).to(self.device)
                        text_input = self.tokenizer(batch_labels).to(self.device)
                        img_features = self.model.encode_image(image_input)
                        txt_features = self.model.encode_text(text_input)
                    else:
                        inputs = self.processor(
                            text=batch_labels,
                            images=pil_images,
                            return_tensors="pt",
                            padding=True,
                        ).to(self.device)
                        outputs = self.model(**inputs)
                        img_features = outputs.image_embeds
                        txt_features = outputs.text_embeds

                    # Normalise
                    img_features = F.normalize(img_features, p=2, dim=-1)
                    txt_features = F.normalize(txt_features, p=2, dim=-1)

                    # Symmetric contrastive loss
                    logits = img_features @ txt_features.T
                    targets = torch.arange(len(batch_idx), device=self.device)
                    loss_i2t = F.cross_entropy(logits, targets)
                    loss_t2i = F.cross_entropy(logits.T, targets)
                    loss = (loss_i2t + loss_t2i) / 2.0

                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

                    running_loss += loss.item()
                    steps += 1

                avg_loss = running_loss / max(steps, 1)
                epoch_losses.append(avg_loss)
                logger.info(f"Epoch {epoch + 1}/{epochs}  loss={avg_loss:.4f}")

        finally:
            # Always return to eval mode
            self.model.eval()

        logger.info("Fine-tuning complete")
        return {"epoch_losses": epoch_losses}

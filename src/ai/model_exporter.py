"""
Model Export/Import System
Export custom models as .ps2model files and import community models
Author: Dead On The Inside / JosephsDeadish
"""

import json
import logging
import zipfile
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil


logger = logging.getLogger(__name__)


class ModelPackage:
    """
    Container for .ps2model package format.
    
    Package structure:
    - model.onnx: The ONNX model file
    - metadata.json: Model metadata and versioning
    - categories.json: Category definitions
    - training_data.json: Optional training data
    - README.md: Optional documentation
    """
    
    PACKAGE_VERSION = "1.0"
    REQUIRED_FILES = ["model.onnx", "metadata.json", "categories.json"]
    
    def __init__(self):
        """Initialize empty model package."""
        self.model_data: Optional[bytes] = None
        self.metadata: Dict[str, Any] = {}
        self.categories: List[str] = []
        self.training_data: Optional[Dict[str, Any]] = None
        self.readme: Optional[str] = None
        self._validated = False
    
    def validate(self) -> bool:
        """
        Validate package contents.
        
        Returns:
            True if valid, False otherwise
        """
        errors = []
        
        # Check required data
        if not self.model_data:
            errors.append("Missing model.onnx")
        
        if not self.metadata:
            errors.append("Missing metadata.json")
        
        if not self.categories:
            errors.append("Missing categories.json")
        
        # Validate metadata
        required_metadata = ['name', 'version', 'author', 'created', 'format']
        for field in required_metadata:
            if field not in self.metadata:
                errors.append(f"Missing metadata field: {field}")
        
        # Check format
        if self.metadata.get('format') != 'onnx':
            errors.append("Only ONNX format is supported")
        
        # Validate categories
        if not isinstance(self.categories, list):
            errors.append("Categories must be a list")
        
        if len(self.categories) == 0:
            errors.append("Categories list is empty")
        
        if errors:
            for error in errors:
                logger.error(f"Validation error: {error}")
            return False
        
        self._validated = True
        logger.info("Package validation successful")
        return True
    
    def is_validated(self) -> bool:
        """Check if package has been validated."""
        return self._validated


class ModelExporter:
    """
    Export trained models as .ps2model packages.
    
    Handles packaging, metadata, versioning, and validation.
    """
    
    def __init__(self):
        """Initialize model exporter."""
        pass
    
    def export_model(
        self,
        model_path: Path,
        output_path: Path,
        name: str,
        version: str,
        author: str,
        categories: List[str],
        description: Optional[str] = None,
        training_data_path: Optional[Path] = None,
        readme_path: Optional[Path] = None,
        license: str = "MIT",
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Export model as .ps2model package.
        
        Args:
            model_path: Path to ONNX model file
            output_path: Output .ps2model file path
            name: Model name
            version: Model version (e.g., "1.0.0")
            author: Model author
            categories: List of category names
            description: Model description
            training_data_path: Optional training data JSON
            readme_path: Optional README file
            license: License type
            tags: Optional tags for searchability
            
        Returns:
            True if export successful
        """
        try:
            logger.info(f"Exporting model: {name} v{version}")
            
            # Validate inputs
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return False
            
            if not model_path.suffix == ".onnx":
                logger.error("Only ONNX models are supported")
                return False
            
            # Create metadata
            metadata = {
                'package_version': ModelPackage.PACKAGE_VERSION,
                'name': name,
                'version': version,
                'author': author,
                'description': description or f"{name} texture classification model",
                'license': license,
                'created': datetime.now().isoformat(),
                'format': 'onnx',
                'num_categories': len(categories),
                'tags': tags or [],
                'framework': 'onnxruntime',
                'compatibility': {
                    'min_app_version': '1.0.0',
                    'python_version': '3.8+'
                }
            }
            
            # Calculate model hash
            with open(model_path, 'rb') as f:
                model_data = f.read()
                model_hash = hashlib.sha256(model_data).hexdigest()
                metadata['model_hash'] = model_hash
                metadata['model_size'] = len(model_data)
            
            # Create package
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add model
                zf.writestr('model.onnx', model_data)
                logger.debug("Added model.onnx")
                
                # Add metadata
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
                logger.debug("Added metadata.json")
                
                # Add categories
                categories_data = {
                    'categories': categories,
                    'num_categories': len(categories)
                }
                zf.writestr('categories.json', json.dumps(categories_data, indent=2))
                logger.debug("Added categories.json")
                
                # Add optional training data
                if training_data_path and training_data_path.exists():
                    with open(training_data_path, 'r') as f:
                        training_data = f.read()
                    zf.writestr('training_data.json', training_data)
                    logger.debug("Added training_data.json")
                
                # Add optional README
                if readme_path and readme_path.exists():
                    with open(readme_path, 'r') as f:
                        readme = f.read()
                    zf.writestr('README.md', readme)
                    logger.debug("Added README.md")
                else:
                    # Create basic README
                    readme = self._generate_readme(metadata, categories)
                    zf.writestr('README.md', readme)
            
            logger.info(f"Model exported successfully: {output_path}")
            logger.info(f"Package size: {output_path.stat().st_size / 1024:.1f} KB")
            
            return True
        
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            return False
    
    def _generate_readme(self, metadata: Dict[str, Any], categories: List[str]) -> str:
        """Generate basic README content."""
        readme = f"""# {metadata['name']}

**Version:** {metadata['version']}  
**Author:** {metadata['author']}  
**License:** {metadata['license']}  
**Created:** {metadata['created']}

## Description

{metadata['description']}

## Categories

This model classifies textures into {len(categories)} categories:

"""
        # Add category list
        for i, category in enumerate(categories, 1):
            readme += f"{i}. {category}\n"
        
        readme += f"""
## Technical Details

- **Format:** ONNX
- **Framework:** ONNX Runtime
- **Model Size:** {metadata['model_size'] / 1024:.1f} KB
- **Model Hash:** `{metadata['model_hash'][:16]}...`

## Usage

1. Place this .ps2model file in your models directory
2. Restart Game Texture Sorter
3. Select this model in Settings → AI Models

## Compatibility

- Minimum App Version: {metadata['compatibility']['min_app_version']}
- Python Version: {metadata['compatibility']['python_version']}

---

*Exported with Game Texture Sorter Model Exporter*
"""
        return readme


class ModelImporter:
    """
    Import and validate .ps2model packages.
    
    Handles decompression, validation, and installation.
    """
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialize model importer.
        
        Args:
            models_dir: Directory for installed models
        """
        if models_dir is None:
            models_dir = Path.home() / ".ps2_texture_sorter" / "models"
        
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ModelImporter initialized: {models_dir}")
    
    def import_model(
        self,
        package_path: Path,
        validate_only: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Import .ps2model package.
        
        Args:
            package_path: Path to .ps2model file
            validate_only: Only validate, don't install
            
        Returns:
            Metadata dictionary if successful, None otherwise
        """
        try:
            logger.info(f"Importing model from: {package_path}")
            
            # Load package
            package = self._load_package(package_path)
            if not package:
                return None
            
            # Validate package
            if not package.validate():
                logger.error("Package validation failed")
                return None
            
            metadata = package.metadata
            
            # Check compatibility
            if not self._check_compatibility(metadata):
                logger.error("Model not compatible with this version")
                return None
            
            if validate_only:
                logger.info("Validation successful (validate_only mode)")
                return metadata
            
            # Install model
            model_name = metadata['name'].lower().replace(' ', '_')
            model_version = metadata['version']
            install_dir = self.models_dir / f"{model_name}_v{model_version}"
            
            if install_dir.exists():
                logger.warning(f"Model already installed: {install_dir}")
                # Backup old version
                backup_dir = install_dir.with_suffix('.backup')
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                shutil.move(str(install_dir), str(backup_dir))
            
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract model file
            model_path = install_dir / "model.onnx"
            with open(model_path, 'wb') as f:
                f.write(package.model_data)
            
            # Save metadata
            metadata_path = install_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Save categories
            categories_path = install_dir / "categories.json"
            with open(categories_path, 'w') as f:
                json.dump({'categories': package.categories}, f, indent=2)
            
            # Save optional files
            if package.training_data:
                training_path = install_dir / "training_data.json"
                with open(training_path, 'w') as f:
                    json.dump(package.training_data, f, indent=2)
            
            if package.readme:
                readme_path = install_dir / "README.md"
                with open(readme_path, 'w') as f:
                    f.write(package.readme)
            
            logger.info(f"Model installed successfully: {install_dir}")
            
            return {
                'metadata': metadata,
                'model_path': model_path,
                'install_dir': install_dir
            }
        
        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            return None
    
    def _load_package(self, package_path: Path) -> Optional[ModelPackage]:
        """Load and parse .ps2model package."""
        try:
            if not package_path.exists():
                logger.error(f"Package not found: {package_path}")
                return None
            
            if not zipfile.is_zipfile(package_path):
                logger.error("Invalid package format (not a ZIP file)")
                return None
            
            package = ModelPackage()
            
            with zipfile.ZipFile(package_path, 'r') as zf:
                # Check required files
                file_list = zf.namelist()
                missing = [f for f in ModelPackage.REQUIRED_FILES if f not in file_list]
                
                if missing:
                    logger.error(f"Missing required files: {missing}")
                    return None
                
                # Load model
                package.model_data = zf.read('model.onnx')
                
                # Load metadata
                metadata_str = zf.read('metadata.json').decode('utf-8')
                package.metadata = json.loads(metadata_str)
                
                # Load categories
                categories_str = zf.read('categories.json').decode('utf-8')
                categories_data = json.loads(categories_str)
                package.categories = categories_data.get('categories', [])
                
                # Load optional files
                if 'training_data.json' in file_list:
                    training_str = zf.read('training_data.json').decode('utf-8')
                    package.training_data = json.loads(training_str)
                
                if 'README.md' in file_list:
                    package.readme = zf.read('README.md').decode('utf-8')
            
            return package
        
        except Exception as e:
            logger.error(f"Failed to load package: {e}", exc_info=True)
            return None
    
    def _check_compatibility(self, metadata: Dict[str, Any]) -> bool:
        """Check if model is compatible with current version."""
        # Check package version
        package_version = metadata.get('package_version')
        if package_version != ModelPackage.PACKAGE_VERSION:
            logger.warning(f"Package version mismatch: {package_version} vs {ModelPackage.PACKAGE_VERSION}")
            # Allow for now, but could be strict in future
        
        # Check format
        if metadata.get('format') != 'onnx':
            logger.error("Unsupported model format")
            return False
        
        # Check minimum app version
        min_version = metadata.get('compatibility', {}).get('min_app_version')
        if min_version:
            logger.debug(f"Requires app version: {min_version}")
            if not self._version_gte(ModelPackage.PACKAGE_VERSION, min_version):
                logger.error(
                    f"App version {ModelPackage.PACKAGE_VERSION} is below "
                    f"required minimum {min_version}"
                )
                return False
        
        return True
    
    @staticmethod
    def _version_gte(current: str, required: str) -> bool:
        """Return True if *current* >= *required* using simple semver comparison."""
        def _parts(v: str) -> List[int]:
            return [int(x) for x in v.split(".") if x.isdigit()]
        try:
            cur = _parts(current)
            req = _parts(required)
            # Pad to equal length with zeros
            length = max(len(cur), len(req))
            cur.extend([0] * (length - len(cur)))
            req.extend([0] * (length - len(req)))
            return cur >= req
        except (ValueError, AttributeError):
            logger.warning(f"Could not compare versions: {current} vs {required}")
            return True  # Allow on parse failure
    
    def list_installed_models(self) -> List[Dict[str, Any]]:
        """
        List all installed models.
        
        Returns:
            List of model metadata dictionaries
        """
        models = []
        
        try:
            for model_dir in self.models_dir.iterdir():
                if not model_dir.is_dir():
                    continue
                
                metadata_path = model_dir / "metadata.json"
                model_path = model_dir / "model.onnx"
                
                if metadata_path.exists() and model_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    metadata['install_dir'] = str(model_dir)
                    metadata['model_path'] = str(model_path)
                    models.append(metadata)
        
        except Exception as e:
            logger.error(f"Failed to list models: {e}", exc_info=True)
        
        return models
    
    def uninstall_model(self, model_name: str, version: str) -> bool:
        """
        Uninstall a model.
        
        Args:
            model_name: Model name
            version: Model version
            
        Returns:
            True if successful
        """
        try:
            model_name_clean = model_name.lower().replace(' ', '_')
            model_dir = self.models_dir / f"{model_name_clean}_v{version}"
            
            if not model_dir.exists():
                logger.error(f"Model not found: {model_dir}")
                return False
            
            shutil.rmtree(model_dir)
            logger.info(f"Model uninstalled: {model_name} v{version}")
            return True
        
        except Exception as e:
            logger.error(f"Uninstall failed: {e}", exc_info=True)
            return False


def validate_ps2model_file(package_path: Path) -> bool:
    """
    Quick validation of .ps2model file.
    
    Args:
        package_path: Path to package file
        
    Returns:
        True if valid
    """
    importer = ModelImporter()
    result = importer.import_model(package_path, validate_only=True)
    return result is not None

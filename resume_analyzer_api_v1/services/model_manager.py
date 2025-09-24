"""
Model Manager Service for optimizing memory usage in multi-worker environments.

This service implements lazy loading and singleton pattern for SentenceTransformer models
to prevent each Gunicorn worker from loading the model at startup, which causes OOM issues.
"""

import logging
import threading
import os
from typing import Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Singleton model manager that implements lazy loading for SentenceTransformer models.
    
    This prevents each Gunicorn worker from loading the model at startup, instead loading
    it only when first needed. Each worker will still have its own model instance, but
    they won't all load simultaneously at startup.
    """
    
    _instance = None
    _lock = threading.Lock()
    _model = None
    _model_name = "all-MiniLM-L6-v2"
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance
    
    def get_model(self, model_name: Optional[str] = None) -> SentenceTransformer:
        """
        Get the SentenceTransformer model, loading it lazily if not already loaded.

        Args:
            model_name: Optional model name. If None, uses default "all-MiniLM-L6-v2"

        Returns:
            SentenceTransformer: The loaded model instance
        """
        if model_name is None:
            model_name = self._model_name

        # Double-checked locking pattern for thread safety
        if self._model is None:
            with self._lock:
                if self._model is None:
                    logger.info(f"Loading SentenceTransformer model: {model_name}")
                    try:
                        # Configure PyTorch for fork safety on macOS
                        self._configure_pytorch_for_fork_safety()

                        # Load model with explicit device configuration
                        self._model = SentenceTransformer(model_name, device='cpu')
                        logger.info(f"Successfully loaded SentenceTransformer model: {model_name} on CPU")
                    except Exception as e:
                        logger.error(f"Failed to load SentenceTransformer model {model_name}: {e}", exc_info=True)
                        raise

        return self._model

    def _configure_pytorch_for_fork_safety(self):
        """Configure PyTorch settings for fork safety, especially on macOS with MPS."""
        try:
            import torch

            # Force CPU usage to avoid MPS fork issues
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                logger.info("MPS detected, configuring for fork safety")
                # Set environment variables for fork safety
                os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
                os.environ['OMP_NUM_THREADS'] = '1'

                # Force CPU device for fork safety
                torch.set_default_device('cpu')
                logger.info("Configured PyTorch to use CPU for fork safety")

        except ImportError:
            # PyTorch not available, skip configuration
            pass
        except Exception as e:
            logger.warning(f"Could not configure PyTorch for fork safety: {e}")
    
    def is_model_loaded(self) -> bool:
        """Check if the model is already loaded."""
        return self._model is not None
    
    def clear_model(self):
        """Clear the loaded model (useful for testing or memory cleanup)."""
        with self._lock:
            if self._model is not None:
                logger.info("Clearing loaded SentenceTransformer model")
                self._model = None

# Global instance
model_manager = ModelManager()

def get_sentence_transformer_model(model_name: Optional[str] = None) -> SentenceTransformer:
    """
    Convenience function to get the SentenceTransformer model.
    
    Args:
        model_name: Optional model name. If None, uses default "all-MiniLM-L6-v2"
        
    Returns:
        SentenceTransformer: The loaded model instance
    """
    return model_manager.get_model(model_name)

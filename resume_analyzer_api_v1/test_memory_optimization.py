#!/usr/bin/env python3
"""
Test script to verify memory optimization for SentenceTransformer models.

This script tests the lazy loading functionality and measures memory usage.
"""

import os
import sys
import psutil
import time
import logging
from typing import Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.model_manager import ModelManager, get_sentence_transformer_model

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_memory_usage() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def test_lazy_loading():
    """Test that the model is loaded lazily."""
    logger.info("=== Testing Lazy Loading ===")
    
    # Get initial memory usage
    initial_memory = get_memory_usage()
    logger.info(f"Initial memory usage: {initial_memory:.2f} MB")
    
    # Create model manager instance
    model_manager = ModelManager()
    logger.info(f"ModelManager created. Model loaded: {model_manager.is_model_loaded()}")
    
    # Memory should not increase significantly yet
    after_manager_memory = get_memory_usage()
    logger.info(f"Memory after ModelManager creation: {after_manager_memory:.2f} MB")
    
    # Now load the model
    logger.info("Loading model for the first time...")
    start_time = time.time()
    model = model_manager.get_model()
    load_time = time.time() - start_time
    
    # Memory should increase now
    after_model_memory = get_memory_usage()
    model_memory_usage = after_model_memory - initial_memory
    
    logger.info(f"Model loaded in {load_time:.2f} seconds")
    logger.info(f"Memory after model loading: {after_model_memory:.2f} MB")
    logger.info(f"Model memory usage: {model_memory_usage:.2f} MB")
    logger.info(f"Model loaded: {model_manager.is_model_loaded()}")
    
    # Test that subsequent calls don't reload
    logger.info("Getting model again (should not reload)...")
    start_time = time.time()
    model2 = model_manager.get_model()
    second_load_time = time.time() - start_time
    
    final_memory = get_memory_usage()
    logger.info(f"Second model access took {second_load_time:.4f} seconds")
    logger.info(f"Final memory usage: {final_memory:.2f} MB")
    
    # Verify it's the same instance
    assert model is model2, "Model instances should be the same (singleton pattern)"
    logger.info("✅ Singleton pattern working correctly")
    
    # Test convenience function
    model3 = get_sentence_transformer_model()
    assert model is model3, "Convenience function should return same instance"
    logger.info("✅ Convenience function working correctly")
    
    return {
        'initial_memory': initial_memory,
        'model_memory_usage': model_memory_usage,
        'load_time': load_time,
        'second_load_time': second_load_time
    }

def test_model_functionality():
    """Test that the model works correctly."""
    logger.info("=== Testing Model Functionality ===")
    
    model = get_sentence_transformer_model()
    
    # Test encoding
    test_texts = [
        "Python developer with 5 years experience",
        "Machine learning engineer specializing in NLP",
        "Software engineer with expertise in web development"
    ]
    
    logger.info("Testing model encoding...")
    start_time = time.time()
    embeddings = model.encode(test_texts)
    encode_time = time.time() - start_time
    
    logger.info(f"Encoded {len(test_texts)} texts in {encode_time:.4f} seconds")
    logger.info(f"Embedding shape: {embeddings.shape}")
    logger.info(f"Embedding dtype: {embeddings.dtype}")
    
    # Test similarity
    from sentence_transformers import util
    similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1])
    logger.info(f"Similarity between first two texts: {similarity.item():.4f}")
    
    logger.info("✅ Model functionality test passed")

def test_memory_cleanup():
    """Test memory cleanup functionality."""
    logger.info("=== Testing Memory Cleanup ===")
    
    model_manager = ModelManager()
    
    # Load model
    model = model_manager.get_model()
    memory_with_model = get_memory_usage()
    logger.info(f"Memory with model loaded: {memory_with_model:.2f} MB")
    
    # Clear model
    model_manager.clear_model()
    logger.info(f"Model cleared. Model loaded: {model_manager.is_model_loaded()}")
    
    # Force garbage collection
    import gc
    gc.collect()
    
    memory_after_clear = get_memory_usage()
    logger.info(f"Memory after clearing: {memory_after_clear:.2f} MB")
    
    # Note: Memory might not be immediately released due to Python's memory management
    logger.info("✅ Memory cleanup test completed")

def main():
    """Run all tests."""
    logger.info("Starting memory optimization tests...")
    
    try:
        # Test lazy loading
        results = test_lazy_loading()
        
        # Test model functionality
        test_model_functionality()
        
        # Test memory cleanup
        test_memory_cleanup()
        
        # Summary
        logger.info("=== Test Summary ===")
        logger.info(f"Model memory usage: {results['model_memory_usage']:.2f} MB")
        logger.info(f"Initial load time: {results['load_time']:.2f} seconds")
        logger.info(f"Subsequent access time: {results['second_load_time']:.4f} seconds")
        logger.info("✅ All tests passed!")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

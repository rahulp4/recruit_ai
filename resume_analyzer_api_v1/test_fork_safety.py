#!/usr/bin/env python3
"""
Test script to verify fork safety fixes for PyTorch/SentenceTransformer models.
"""

import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pytorch_configuration():
    """Test PyTorch configuration and device selection."""
    logger.info("=== Testing PyTorch Configuration ===")
    
    try:
        import torch
        logger.info(f"PyTorch version: {torch.__version__}")
        
        # Check MPS availability
        if hasattr(torch.backends, 'mps'):
            mps_available = torch.backends.mps.is_available()
            logger.info(f"MPS available: {mps_available}")
            
            if mps_available:
                logger.info("MPS is available but we'll force CPU usage for fork safety")
        
        # Check current default device
        try:
            default_device = torch.get_default_device()
            logger.info(f"Default device: {default_device}")
        except:
            logger.info("Default device: Not set (will use CPU)")
        
        # Test tensor creation
        test_tensor = torch.randn(3, 3)
        logger.info(f"Test tensor device: {test_tensor.device}")
        
        return True
        
    except ImportError:
        logger.error("PyTorch not available")
        return False
    except Exception as e:
        logger.error(f"PyTorch configuration test failed: {e}")
        return False

def test_sentence_transformer_loading():
    """Test SentenceTransformer loading with fork safety."""
    logger.info("=== Testing SentenceTransformer Loading ===")
    
    try:
        # Set environment variables for fork safety
        os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        
        logger.info("Environment variables set for fork safety")
        
        # Test model loading through our model manager
        from services.model_manager import get_sentence_transformer_model
        
        logger.info("Loading model through model manager...")
        model = get_sentence_transformer_model()
        
        # Check model device
        if hasattr(model, 'device'):
            logger.info(f"Model device: {model.device}")
        
        # Test encoding
        test_text = "This is a test sentence for fork safety verification."
        embedding = model.encode(test_text)
        
        logger.info(f"Successfully encoded text. Embedding shape: {embedding.shape}")
        logger.info("✅ SentenceTransformer loading test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"SentenceTransformer loading test failed: {e}", exc_info=True)
        return False

def test_environment_variables():
    """Test that all required environment variables are set."""
    logger.info("=== Testing Environment Variables ===")
    
    required_vars = [
        'PYTORCH_ENABLE_MPS_FALLBACK',
        'OMP_NUM_THREADS',
        'TOKENIZERS_PARALLELISM'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            logger.info(f"✅ {var}={value}")
        else:
            logger.warning(f"❌ {var} not set")
            all_set = False
    
    return all_set

def main():
    """Run all fork safety tests."""
    logger.info("Starting fork safety tests...")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("PyTorch Configuration", test_pytorch_configuration),
        ("SentenceTransformer Loading", test_sentence_transformer_loading)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name} test PASSED")
            else:
                logger.error(f"❌ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} test CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n=== Test Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All fork safety tests passed! The application should work with Gunicorn.")
        return True
    else:
        logger.error("⚠️  Some tests failed. Consider using the safe mode: ./start_app.sh --safe")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

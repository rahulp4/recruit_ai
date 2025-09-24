#!/usr/bin/env python3
"""
Memory comparison script to demonstrate the optimization benefits.

This script simulates the before/after memory usage patterns.
"""

import os
import sys
import time
import logging
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_memory_usage():
    """Get memory usage if psutil is available."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return "N/A (psutil not available)"

def simulate_old_approach():
    """Simulate the old approach where models are loaded at startup."""
    logger.info("=== Simulating OLD approach (eager loading) ===")
    
    initial_memory = get_memory_usage()
    logger.info(f"Initial memory: {initial_memory} MB")
    
    # Simulate loading models at startup (like old app.py)
    logger.info("Loading SentenceTransformer at startup...")
    start_time = time.time()
    
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    load_time = time.time() - start_time
    after_load_memory = get_memory_usage()
    
    logger.info(f"Model loaded in {load_time:.2f} seconds")
    logger.info(f"Memory after loading: {after_load_memory} MB")
    
    if isinstance(initial_memory, (int, float)) and isinstance(after_load_memory, (int, float)):
        model_memory = after_load_memory - initial_memory
        logger.info(f"Model memory usage: {model_memory:.2f} MB")
        return model_memory
    
    return None

def simulate_new_approach():
    """Simulate the new approach with lazy loading."""
    logger.info("=== Simulating NEW approach (lazy loading) ===")
    
    initial_memory = get_memory_usage()
    logger.info(f"Initial memory: {initial_memory} MB")
    
    # Simulate app startup without loading models
    logger.info("App startup (no model loading)...")
    from services.model_manager import ModelManager
    
    model_manager = ModelManager()
    after_startup_memory = get_memory_usage()
    
    logger.info(f"Memory after startup: {after_startup_memory} MB")
    logger.info(f"Model loaded at startup: {model_manager.is_model_loaded()}")
    
    # Simulate first request that needs the model
    logger.info("First request arrives, loading model lazily...")
    start_time = time.time()
    
    model = model_manager.get_model()
    
    load_time = time.time() - start_time
    after_load_memory = get_memory_usage()
    
    logger.info(f"Model loaded in {load_time:.2f} seconds")
    logger.info(f"Memory after lazy loading: {after_load_memory} MB")
    logger.info(f"Model loaded now: {model_manager.is_model_loaded()}")
    
    if isinstance(initial_memory, (int, float)) and isinstance(after_load_memory, (int, float)):
        model_memory = after_load_memory - initial_memory
        logger.info(f"Model memory usage: {model_memory:.2f} MB")
        return model_memory
    
    return None

def simulate_multiple_workers():
    """Simulate memory usage with multiple workers."""
    logger.info("=== Simulating Multiple Workers Impact ===")
    
    # Get single model memory usage
    logger.info("Measuring single model memory usage...")
    from services.model_manager import get_sentence_transformer_model
    
    initial_memory = get_memory_usage()
    model = get_sentence_transformer_model()
    after_memory = get_memory_usage()
    
    if isinstance(initial_memory, (int, float)) and isinstance(after_memory, (int, float)):
        single_model_memory = after_memory - initial_memory
        
        logger.info(f"Single model memory usage: {single_model_memory:.2f} MB")
        
        # Calculate theoretical memory usage for multiple workers
        old_workers = 4
        new_workers = 2
        
        old_total_memory = old_workers * single_model_memory
        new_total_memory = new_workers * single_model_memory
        
        logger.info(f"OLD approach (4 workers, eager loading): {old_total_memory:.2f} MB")
        logger.info(f"NEW approach (2 workers, lazy loading): {new_total_memory:.2f} MB")
        logger.info(f"Memory savings: {old_total_memory - new_total_memory:.2f} MB ({((old_total_memory - new_total_memory) / old_total_memory * 100):.1f}%)")
        
        return {
            'single_model_memory': single_model_memory,
            'old_total_memory': old_total_memory,
            'new_total_memory': new_total_memory,
            'savings_mb': old_total_memory - new_total_memory,
            'savings_percent': (old_total_memory - new_total_memory) / old_total_memory * 100
        }
    
    return None

def main():
    """Run memory comparison."""
    logger.info("Starting memory optimization comparison...")
    
    try:
        # Note: We can't actually simulate the old approach without modifying the code
        # So we'll just demonstrate the new approach and calculate theoretical savings
        
        logger.info("Demonstrating the optimized lazy loading approach...")
        new_memory = simulate_new_approach()
        
        logger.info("\nCalculating theoretical memory savings...")
        savings = simulate_multiple_workers()
        
        if savings:
            logger.info("\n=== OPTIMIZATION SUMMARY ===")
            logger.info(f"Single model memory: {savings['single_model_memory']:.2f} MB")
            logger.info(f"Old approach (4 workers): {savings['old_total_memory']:.2f} MB")
            logger.info(f"New approach (2 workers): {savings['new_total_memory']:.2f} MB")
            logger.info(f"Total memory savings: {savings['savings_mb']:.2f} MB ({savings['savings_percent']:.1f}%)")
            logger.info("\nAdditional benefits:")
            logger.info("- Lazy loading prevents startup OOM issues")
            logger.info("- Worker recycling prevents memory leaks")
            logger.info("- Staggered model loading reduces peak memory usage")
        
        logger.info("\n✅ Memory optimization comparison completed!")
        return True
        
    except Exception as e:
        logger.error(f"Comparison failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

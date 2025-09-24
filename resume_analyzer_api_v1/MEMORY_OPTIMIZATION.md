# Memory Optimization and Fork Safety for SentenceTransformer Models

## Problem
The all-MiniLM-L6-v2 SentenceTransformer model was causing two critical issues:

1. **Memory Issues**: Model loaded in each Gunicorn worker at startup, causing OOM with 4 workers × ~90MB = ~360MB
2. **Fork Safety Issues**: PyTorch MPS backend on macOS crashes when forked (`objc_initializeAfterForkError`)

## Solution Overview
Implemented comprehensive optimization addressing both memory and fork safety:

1. **Lazy Loading**: Models are loaded only when first needed, not at startup
2. **Singleton Pattern**: Each worker has only one model instance
3. **Fork Safety**: Force CPU usage and configure PyTorch for fork safety
4. **Worker Configuration**: Multiple startup options (safe vs optimized)
5. **Environment Variables**: Proper PyTorch/MPS configuration

## Changes Made

### 1. Model Manager Service (`services/model_manager.py`)
- Created `ModelManager` class with singleton pattern
- Implements thread-safe lazy loading
- Provides `get_sentence_transformer_model()` convenience function

### 2. Matching Engine Service (`services/matching_engine_service.py`)
- Modified constructor to accept `Optional[SentenceTransformer]`
- Added `@property model` with lazy loading
- Imports and uses the model manager

### 3. Application Factory (`app.py`)
- Removed eager model loading at startup
- Pass `None` to MatchingEngineService constructor
- Added comments explaining the optimization

### 4. Gunicorn Configuration (`gunicorn_start.sh`)
- Changed from `gevent` to `sync` worker class (fork safety)
- Reduced workers from 4 to 2
- Added `--max-requests 1000` for worker recycling
- Added PyTorch environment variables
- Removed `--preload` to avoid fork issues

### 5. Fork-Safe Configuration (`gunicorn_start_safe.sh`)
- Single worker configuration for maximum stability
- Comprehensive environment variable setup
- Extended timeout for model loading
- Recommended for production on macOS

### 6. Startup Scripts (`start_app.sh`)
- Unified startup with environment configuration
- `./start_app.sh` - optimized mode (2 workers)
- `./start_app.sh --safe` - safe mode (1 worker)

## Memory Usage Before vs After

### Before Optimization:
- **Startup**: 4 workers × ~90MB model = ~360MB just for models
- **Peak**: All models loaded simultaneously during startup
- **Risk**: High probability of OOM on memory-constrained systems

### After Optimization:
- **Startup**: 0MB for models (lazy loading)
- **Runtime**: Models loaded only when matching requests arrive
- **Peak**: 2 workers × ~90MB model = ~180MB maximum
- **Benefit**: 50% reduction in memory usage + staggered loading

## Usage

The optimization is transparent to the application code. The matching engine service will automatically load the model when first accessed:

```python
# This will trigger lazy loading if model not already loaded
match_result = matching_engine_service.perform_match(job_id, profile_id, ...)
```

## Monitoring

To monitor the optimization effectiveness:

1. **Check logs** for lazy loading messages:
   ```
   INFO - Lazy loading SentenceTransformer model for MatchingEngineService
   INFO - Loading SentenceTransformer model: all-MiniLM-L6-v2
   INFO - Successfully loaded SentenceTransformer model: all-MiniLM-L6-v2
   ```

2. **Monitor memory usage** with system tools:
   ```bash
   # Monitor memory usage of gunicorn processes
   ps aux | grep gunicorn
   
   # Monitor system memory
   free -h
   ```

3. **Check worker recycling**:
   ```bash
   # Check gunicorn logs for worker recycling
   tail -f logs/gunicorn_error.log
   ```

## Additional Optimizations

### For Further Memory Reduction:
1. **Single Worker**: Reduce to 1 worker if memory is extremely constrained
2. **Model Quantization**: Use quantized versions of the model
3. **Alternative Models**: Consider smaller models like `all-MiniLM-L12-v2`
4. **External Model Service**: Move model to separate service/container

### For Better Performance:
1. **Model Caching**: Implement disk-based model caching
2. **Batch Processing**: Process multiple requests together
3. **Connection Pooling**: Optimize database connections

## Configuration Options

### Environment Variables:
- `SENTENCE_TRANSFORMER_MODEL`: Override default model name
- `MAX_WORKERS`: Override number of Gunicorn workers

### Gunicorn Options:
- `--max-requests`: Number of requests before worker restart (default: 1000)
- `--max-requests-jitter`: Random jitter for worker restart (default: 100)
- `--workers`: Number of worker processes (default: 2)

## Troubleshooting

### If Fork Safety Issues Persist:
1. **Use safe mode**: `./start_app.sh --safe` (single worker)
2. **Check environment variables**: Ensure PyTorch variables are set
3. **Verify CPU usage**: Model should load on CPU, not MPS
4. **Check logs**: Look for MPS-related error messages

### If Memory Issues Persist:
1. Check if other services are loading models
2. Monitor actual memory usage during peak load
3. Consider reducing to 1 worker
4. Check for memory leaks in application code

### If Performance Degrades:
1. Monitor request latency for first model load
2. Consider pre-warming models with health check endpoint
3. Adjust worker count based on CPU cores and memory

### Common Error Messages:
- `objc_initializeAfterForkError` → Use safe mode or sync workers
- `Worker was sent SIGKILL! Perhaps out of memory?` → Reduce workers or use lazy loading
- `MPS backend not available` → Environment variables working correctly

## Testing

To test the optimization:

1. **Start the application**:
   ```bash
   ./gunicorn_start.sh
   ```

2. **Monitor memory before first request**:
   ```bash
   ps aux | grep gunicorn | awk '{print $6}' | paste -sd+ | bc
   ```

3. **Make a matching request** and monitor memory increase

4. **Verify lazy loading** in logs

## Rollback Plan

If issues occur, rollback by reverting these changes:
1. Restore original `app.py` with eager model loading
2. Restore original `gunicorn_start.sh` with 4 workers
3. Remove `services/model_manager.py`
4. Revert `services/matching_engine_service.py` changes

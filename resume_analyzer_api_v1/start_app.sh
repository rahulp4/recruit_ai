#!/bin/bash

# Comprehensive startup script that handles PyTorch/MPS fork safety issues
# This script sets all necessary environment variables and starts the application

# Set working directory
cd "$(dirname "$0")"

echo "=== Resume Analyzer API Startup ==="
echo "Setting up environment for PyTorch fork safety..."

# PyTorch fork safety environment variables
export PYTORCH_ENABLE_MPS_FALLBACK=1
export OMP_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# Force CPU usage to avoid MPS fork issues
export CUDA_VISIBLE_DEVICES=""

echo "Environment variables set:"
echo "  PYTORCH_ENABLE_MPS_FALLBACK=$PYTORCH_ENABLE_MPS_FALLBACK"
echo "  OMP_NUM_THREADS=$OMP_NUM_THREADS"
echo "  TOKENIZERS_PARALLELISM=$TOKENIZERS_PARALLELISM"

# Check if we should use the safe configuration
if [[ "$1" == "--safe" ]]; then
    echo "Using FORK-SAFE configuration (single worker)..."
    exec ./gunicorn_start_safe.sh
elif [[ "$1" == "--macos" ]]; then
    echo "Using macOS-OPTIMIZED configuration..."
    exec ./gunicorn_start_macos.sh
else
    echo "Using STANDARD configuration (multiple workers)..."
    exec ./gunicorn_start.sh
fi

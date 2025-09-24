#!/bin/bash

# FORK-SAFE Gunicorn startup script for PyTorch/SentenceTransformer models
# This version uses single worker to avoid fork issues with MPS on macOS

# Name of your application directory (where app.py resides)
APP_DIR=/Users/rahulpoddar/my-work/pro_resumev4/talent/resume_analyzer_api_v1 

# Name of your virtual environment directory
VENV_DIR=$APP_DIR/venv

# Gunicorn executable path
GUNICORN=$VENV_DIR/bin/gunicorn

# Flask application entry point: app_module_name:app_instance_name
FLASK_APP_MODULE="wsgi" # Name of the file (wsgi.py)
FLASK_APP_CALLABLE="application" # Name of the Flask app instance in wsgi.py

# FORK-SAFE CONFIGURATION: Use single worker to avoid fork issues
NUM_WORKERS=1
# Port to listen on
PORT=8000

# Log files
LOG_DIR=$APP_DIR/logs
ACCESS_LOG="$LOG_DIR/gunicorn_access.log"
ERROR_LOG="$LOG_DIR/gunicorn_error.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo "Starting FORK-SAFE Gunicorn with $NUM_WORKERS worker on port $PORT..."
echo "This configuration avoids PyTorch MPS fork issues on macOS"
echo "Access logs: $ACCESS_LOG"
echo "Error logs: $ERROR_LOG"

# Set PyTorch environment variables for fork safety
export PYTORCH_ENABLE_MPS_FALLBACK=1
export OMP_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false

exec "$GUNICORN" "${FLASK_APP_MODULE}:${FLASK_APP_CALLABLE}" \
  --bind 0.0.0.0:$PORT \
  --workers "$NUM_WORKERS" \
  --worker-class sync \
  --timeout 300 \
  --max-requests 500 \
  --max-requests-jitter 50 \

  --access-logfile "$ACCESS_LOG" \
  --error-logfile "$ERROR_LOG" \
  --log-level info \
  --capture-output \
  --enable-stdio-inheritance \
  --env FLASK_ENV=production \
  --env PYTORCH_ENABLE_MPS_FALLBACK=1 \
  --env OMP_NUM_THREADS=1 \
  --env TOKENIZERS_PARALLELISM=false \
  --chdir "$APP_DIR"

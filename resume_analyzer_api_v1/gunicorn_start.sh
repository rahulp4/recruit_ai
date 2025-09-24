#!/bin/bash

# Name of your application directory (where app.py resides)
# CRITICAL FIX: Replace with your ACTUAL absolute path
APP_DIR=/Users/rahulpoddar/my-work/pro_resumev4/talent/resume_analyzer_api_v1 

# Name of your virtual environment directory
VENV_DIR=$APP_DIR/venv

# Gunicorn executable path
GUNICORN=$VENV_DIR/bin/gunicorn

# Flask application entry point: app_module_name:app_instance_name
FLASK_APP_MODULE="wsgi" # Name of the file (wsgi.py)
FLASK_APP_CALLABLE="application" # Name of the Flask app instance in wsgi.py

# Number of Gunicorn workers (OPTIMIZED for memory usage with ML models)
# Reduced from 4 to 2 workers to prevent OOM with SentenceTransformer models
# Each worker will lazy-load the model only when needed
NUM_WORKERS=4
# Port to listen on
PORT=8000

# Log files
LOG_DIR=$APP_DIR/logs
ACCESS_LOG="$LOG_DIR/gunicorn_access.log"
ERROR_LOG="$LOG_DIR/gunicorn_error.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR" # Use quotes for paths with spaces or special chars

echo "Starting Gunicorn with $NUM_WORKERS workers on port $PORT..."
echo "Access logs: $ACCESS_LOG"
echo "Error logs: $ERROR_LOG"

exec "$GUNICORN" "${FLASK_APP_MODULE}:${FLASK_APP_CALLABLE}" \
  --bind 0.0.0.0:$PORT \
  --workers "$NUM_WORKERS" \
  --worker-class sync \
  --timeout 120 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  # --access-logfile "$ACCESS_LOG" \
  # --error-logfile "$ERROR_LOG" \
  --log-level info \
  --capture-output \
  --enable-stdio-inheritance \
  --env FLASK_ENV=production \
  --env PYTORCH_ENABLE_MPS_FALLBACK=1 \
  --env OMP_NUM_THREADS=1 \
  --chdir "$APP_DIR"
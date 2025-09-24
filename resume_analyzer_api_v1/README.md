# matchai
MatchAI


# Standard optimized mode (2 workers)
./start_app.sh

# Maximum safety mode (1 worker)  
./start_app.sh --safe

# macOS optimized mode (with /tmp worker directory)
./start_app.sh --macos

# Direct Gunicorn (if preferred)
./gunicorn_start.sh


Mode = development or production
Modify .env for
FLASK_ENV=development
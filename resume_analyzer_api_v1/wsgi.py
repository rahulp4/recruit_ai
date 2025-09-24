# wsgi.py
import os
from app import create_app

# Set the FLASK_ENV environment variable for Gunicorn
# This ensures create_app uses the production config.
#os.environ['FLASK_ENV'] = 'production'

# Call the application factory to create the Flask app instance
application = create_app(os.environ.get('FLASK_ENV', 'production'))

# If you need to run specific setup outside of create_app for WSGI, do it here.
# For example, if you had a separate logging setup for Gunicorn.
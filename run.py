"""
HimClimX Backend API
====================
Main entry point for the Flask application.

Run with:
    flask run
    
Or with gunicorn:
    gunicorn run:app
"""

import os
from app import create_app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )

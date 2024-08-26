"""
This script runs the Flask application.

It imports the Flask app instance and runs it with the specified host and port.
Debug mode is enabled for development purposes.

Usage:
    python run.py
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
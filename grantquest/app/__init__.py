"""
Initialize the Flask application and its components.

Sets up the Flask app, configures it, initializes the Elasticsearch client,
LLM client, and snippet generator. Also handles environment variable loading
and basic error checking for critical configuration items.
"""

import os
import sys
from flask import Flask
from dotenv import load_dotenv
from config import Config
from app.search.search import Search
from app.clients.clients import create_client
from app.snippet_generator.snippet_generator import SnippetGenerator

# Load environment variables
load_dotenv()

def create_app(config_class=Config):
    """
    Create and configure the Flask application.

    Args:
        config_class: The configuration class to use (default: Config)

    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Elasticsearch
    if 'ELASTICSEARCH_URL' not in app.config:
        app.logger.error('ELASTICSEARCH_URL not set in config.py')
        sys.exit(1)

    try:
        search_client = Search(app.config['ELASTICSEARCH_URL'], os.getenv('ELASTICSEARCH_USER'), os.getenv('ELASTICSEARCH_PASSWORD')
        )
    except Exception as e:
        app.logger.error(f'Failed to initialize Elasticsearch client: {e}')
        sys.exit(1)

    # Initialize LLM client
    try:
        llm_client = create_client(app.config['CLIENT_TYPE'], os.getenv('OPENAI_KEY')
        )
    except Exception as e:
        app.logger.error(f'Failed to initialize LLM client: {e}')
        sys.exit(1)

    # Initialize SnippetGenerator
    snippet_generator = SnippetGenerator(llm_client, app.config['MODEL'])

    # Attach clients to app
    app.elasticsearch = search_client
    app.llm_client = llm_client
    app.snippet_generator = snippet_generator
    app.index_name = app.config['INDEX_NAME']

    # Import and register blueprints
    from app import routes
    app.register_blueprint(routes.bp)

    return app
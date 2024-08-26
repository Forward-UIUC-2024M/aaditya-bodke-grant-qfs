# GrantQuest - Semantic search for funding oppurtunities

#### GrantQuest is a semantic search engine developed at Forward Data Lab at UIUC under the guidance of Prof. Kevin Chang. It empowers interested parties to search for relevant funding oppurtunities. Aided by LLM -generated abstractive and query-focused snippets, individual researchers and organisations can quickly sift through the sea of funding oppurtunities to find ones that meet their requirements.

## Getting Started

### Set up conda environment

Refer to the main [README](../README.md) for detailed instructions on setting up the conda environment.

### Environment Variables

Create a `.env` file in the project root directory with the following variables:

```
ELASTICSEARCH_USER=your_elasticsearch_username
ELASTICSEARCH_PASSWORD=your_elasticsearch_password
OPENAI_KEY=your_openai_api_key
```

Alternatively, you can set these as environment variables in your terminal.

Note: If you're using a different LLM client (as defined in `clients/clients.py`), set the appropriate API key variable.

### Configuration

Modify the [config.py](./config.py) file according to your requirements:

```python
ELASTICSEARCH_URL = 'URL of your ElasticSearch cluster'
INDEX_NAME = 'Name of the ElasticSearch index you want to search'
CLIENT_TYPE = 'LLM client from clients.py'
MODEL = 'Name of model used for snippet generation'
```

### Running the Application

To start the Flask application, run:

```
python run.py
```

The application will be available at `http://localhost:5000` by default.


## Modules

- `clients/clients.py`: Defines various LLM clients for snippet generation.
- `search/search.py`: Handles interaction with Elasticsearch for query processing.
- `snippet_generator/snippet_generator.py`: Manages the generation of abstractive and query-focused snippets.
- `routes.py`: Defines the Flask routes for the web application.

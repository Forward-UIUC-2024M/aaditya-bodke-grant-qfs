"""
This module provides a Search class for interacting with Elasticsearch.

The Search class handles connection to Elasticsearch, query construction,
and search operations for different types of searches including semantic,
full-text, and hybrid searches.

Classes:
    Search: Main class for handling Elasticsearch operations.
"""

from typing import Dict, Tuple, Any, List
from elasticsearch import Elasticsearch
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# the id of the inference endpoint created in ElasticSearch, for embeddings 
INFERENCE_ID = os.getenv('INFERENCE_ID', "openai-embeddings-small")

class Search:
    """
    A class for handling Elasticsearch operations including connection,
    query construction, and search execution.

    Attributes:
        es (Elasticsearch): The Elasticsearch client instance.
    """

    def __init__(self, elastic_url: str, elastic_user_name: str, elastic_password: str):
        """
        Initialize the Search class with Elasticsearch connection details.

        Args:
            elastic_url (str): The URL of the Elasticsearch instance.
            elastic_user_name (str): The username for Elasticsearch authentication.
            elastic_password (str): The password for Elasticsearch authentication.

        Raises:
            ConnectionError: If unable to connect to Elasticsearch.
        """
        self.es = Elasticsearch(elastic_url, basic_auth=(elastic_user_name, elastic_password))
        self._check_connection()

    def _check_connection(self):
        """
        Check the connection to Elasticsearch.

        Raises:
            ConnectionError: If unable to connect to Elasticsearch.
        """
        try:
            client_info = self.es.info()
            logger.info('Connected to Elasticsearch!')
            logger.debug(f'Client info: {client_info}')
        except Exception as e:
            logger.error(f'Error connecting to Elasticsearch: {e}')
            raise ConnectionError(f"Failed to connect to Elasticsearch: {e}")

    def get_query_args_semantic(self, query: str, n: int, from_: int, field: str = 'embeddings') -> Dict[str, Any]:
        """
        Construct query arguments for semantic search.

        Args:
            query (str): The search query.
            n (int): The number of results to return.
            from_ (int): The starting point for pagination.
            field (str, optional): The embeddings field to search. Defaults to 'embeddings'.

        Returns:
            Dict[str, Any]: The constructed query arguments.
        """
        return {
            'query': {
                'knn': {
                    "field": field,
                    "num_candidates": 30,
                    "query_vector_builder": {
                        "text_embedding": {
                            "model_id": INFERENCE_ID,
                            "model_text": query,
                        }
                    },
                },
            },
            'size': n,
            'from_': from_,
            '_source_excludes': ['embeddings', 'normalized_embeddings'],
            # remember to exclude embedding fields and any other large fields for efficiency!!
        }
    
    def get_query_args_fulltext(self, query: str, n: int, from_: int) -> Dict[str, Any]:
        """
        Construct query arguments for full-text search.

        Args:
            query (str): The search query.
            n (int): The number of results to return.
            from_ (int): The starting point for pagination.

        Returns:
            Dict[str, Any]: The constructed query arguments.
        """
        return {
            "query": {
                "multi_match": {
                    "query": query,
                    "type": "most_fields",
                    "fields": ["normalized_info", "description", "submission_info", "eligibility"],
                }
            },
            'size': n,
            'from_': from_,
            '_source_excludes': ['embeddings', 'normalized_embeddings'],
            # remember to exclude embedding fields and any other large fields for efficiency!!
        }
    
    def get_query_args_hybrid(self, query: str, n: int, from_: int, field: str = 'embeddings') -> Dict[str, Any]:
        """
        Construct query arguments for hybrid search (combination of semantic and full-text).

        Args:
            query (str): The search query.
            n (int): The number of results to return.
            from_ (int): The starting point for pagination.
            field (str, optional): The embeddings field to use for semantic search. Defaults to 'embeddings'.

        Returns:
            Dict[str, Any]: The constructed query arguments.
        """
        return {
            "query": {
                "multi_match": {
                    "query": query,
                    "type": "most_fields",
                    "fields": ["normalized_info", "description", "submission_info"],
                    "boost": 0.2
                }
            },
            "knn": {
                "field": field,
                "num_candidates": 50,
                "boost": 0.9,
                "query_vector_builder": {
                    "text_embedding": {
                        "model_id": INFERENCE_ID,
                        "model_text": query,
                    }
                },
            },
            'size': n,
            'from_': from_,
            '_source_excludes': ['embeddings', 'normalized_embeddings'],
            # remember to exclude embedding fields and any other large fields for efficiency!!
        }

    def search(self, index_name: str, **query_args: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Execute a search query on the specified Elasticsearch index.

        Args:
            index_name (str): The name of the Elasticsearch index to search.
            **query_args: Arbitrary keyword arguments for the search query.

        Returns:
            Tuple[List[Dict[str, Any]], int]: A tuple containing the list of search hits and the total number of matches.

        Raises:
            ElasticsearchException: If an error occurs during the search operation.
        """
        try:
            res = self.es.search(index=index_name, **query_args)
            hits = res['hits']['hits']
            total = res['hits']['total']['value']
            return hits, total
        except Exception as e:
            logger.error(f'Error executing search: {e}')
            raise

    def retrieve_document(self, index_name: str, id: str) -> Dict[str, Any]:
        """
        Retrieve a specific document from the Elasticsearch index by its ID.

        Args:
            index_name (str): The name of the Elasticsearch index.
            id (str): The ID of the document to retrieve.

        Returns:
            Dict[str, Any]: The retrieved document.

        Raises:
            ElasticsearchException: If an error occurs during the document retrieval.
        """
        try:
            res = self.es.get(index=index_name, id=id, _source_excludes=['embeddings', 'normalized_embeddings'])
            return res
        except Exception as e:
            logger.error(f'Error retrieving document: {e}')
            raise
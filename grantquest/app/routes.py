"""
This module defines the routes for the Flask application.

It includes routes for handling searches and retrieving individual documents.
The module uses the search client, LLM client, and snippet generator initialized in the main application file.

Routes:
    /: Handles both GET and POST requests for the main search functionality.
    /document/<int:id>: Retrieves a specific document by ID.
"""

from flask import Blueprint, render_template, request, current_app, abort, jsonify
from http import HTTPStatus

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
def handle_search():
    """
    Handle the main search functionality.

    On GET: Render the search form.
    On POST: Process the search query and return results.

    Returns:
        str: Rendered HTML template with search results or form.
    """
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        from_ = request.form.get('from_', type=int, default=0)
       
        if not query:
            return render_template('results.html', error="Please enter a search query."), HTTPStatus.BAD_REQUEST
        
        try:
            query_args = current_app.elasticsearch.get_query_args_semantic(
                query, 10, from_, field='normalized_embeddings'
            )
            search_results, total = current_app.elasticsearch.search(current_app.index_name, **query_args)

            results = current_app.snippet_generator.generate_snippets(search_results, query)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return render_template('results.html', results=results, query=query, from_=from_, total=total)
            else:
                return render_template('index.html', results=results, query=query, from_=from_, total=total)
        except Exception as e:
            current_app.logger.error(f"Search error: {str(e)}")
            return render_template('error.html', error="An error occurred during the search. Please try again."), HTTPStatus.INTERNAL_SERVER_ERROR
    
    return render_template('index.html')


@bp.route('/document/<int:id>')
def get_document(id):
    """
    Retrieve and display a specific document.

    Args:
        id (int): The ID of the document to retrieve.

    Returns:
        str: Rendered HTML template with the document details.

    Raises:
        HTTPException: 404 if the document is not found.
    """
    try:
        document = current_app.elasticsearch.retrieve_document(current_app.index_name, str(id))
        if document:
            return render_template('document.html', grant=document['_source'])
        else:
            abort(HTTPStatus.NOT_FOUND)
    except Exception as e:
        current_app.logger.error(f"Error retrieving document {id}: {str(e)}")
        abort(HTTPStatus.INTERNAL_SERVER_ERROR)
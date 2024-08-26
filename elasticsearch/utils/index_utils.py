from elasticsearch import Elasticsearch, exceptions, NotFoundError, helpers
from time import sleep
from typing import Dict, LiteralString, List

def create_index(client: Elasticsearch, index_name: LiteralString, mappings: Dict):
    if client.indices.exists(index=index_name):
            print(f"Index '{index_name}' already exists.")
    else:
        try:
            # Create the index
            client.indices.create(index=index_name, 
                                body={
                                        "settings": {"number_of_shards": 1},
                                        "mappings": mappings 
                                    })

            print(f"Index '{index_name}' created successfully.")
        except exceptions.RequestError as e:
            print(f"Error creating index '{index_name}': {e.info}")
        except Exception as e:
            print(f"Unexpected error: {e}")


def delete_index(client, index_name):
    try:
        resp = client.indices.delete(
            index=index_name,
        )
        print(resp)
    except Exception as e:
            print(f"Unexpected error: {e}")


def construct_indexing_actions(grants_data: Dict, index_name: LiteralString, pipeline_id: LiteralString = None):
    body = []
    for item in grants_data['grants_data']['grant']:
        action = {"_index": index_name, "_id": item['@id']}
        if (pipeline_id):
            action["pipeline"] = pipeline_id
        data = item.copy()
        del data['@id']
        action['_source'] = data
        body.append(action)
    
    return body

def construct_actions_from_ids(grants_data: Dict, ids: List, index_name: LiteralString, pipeline_id: LiteralString = None):
    body = []
    for item in grants_data['grants_data']['grant']:
        if item['@id'] in ids:
            action = {"_index": index_name, "_id": item['@id'], "pipeline": pipeline_id}
            data = item.copy()
            del data['@id']
            action['_source'] = data
            body.append(action)

    return body


def bulk_index_documents(client: Elasticsearch, actions: List[Dict], chunk_size=1000, max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            success, failed = helpers.bulk(client, actions, chunk_size=chunk_size, raise_on_error=False)
            
            # Check for failures
            if failed:
                for doc in failed:
                    print(f"Failed to index document {doc}")
            else:
                print(f"Successfully indexed {success} documents.")
                
            break  # Exit loop if successful
            
        except exceptions.ConnectionTimeout as e:
            print(f"Connection timed out, attempt {attempt + 1} of {max_retries}")
            if attempt < max_retries - 1:
                sleep(retry_delay)
            else:
                print("Max retries reached. Failed to index documents.")
                raise e
        except Exception as e:
            print(f"Error indexing documents: {e}")
            raise e
        

def document_exists(client: Elasticsearch, index_name: LiteralString, doc_id: int):
    try:
        client.get(index=index_name, id=doc_id)
        return True
    except NotFoundError:
        return False


def get_missing_ids(client: Elasticsearch, index_name: LiteralString, ids: List[int]):
    missing_ids = []
    for id in ids:
        if not document_exists(client, index_name, id):
            missing_ids.append(id)
    return missing_ids

def get_failed_embedding_ids(client: Elasticsearch, index_name: LiteralString):
    search_query = {
    "_source": ["error_message"],
    "query": {
        "bool": {
            "must_not": {
                "exists": {
                    "field": "embeddings"
                }}}}
    }

    err = []
    documents = helpers.scan(client, query=search_query, index=index_name)
    for doc in documents:
        # print(doc)
        err.append(doc['_id'])
        # print(doc['_id'])
    
    return err

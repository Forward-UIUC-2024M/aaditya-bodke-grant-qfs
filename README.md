# GrantQuest - Semantic search for funding oppurtunities

#### GrantQuest is a semantic search engine I developed at Forward Data Lab at UIUC under the guidance of Prof. Kevin Chang. It allows interested parties to search for relevant funding oppurtunities. Aided by LLM -generated abstractive and query-focused snippets, individual researchers and organisations can quickly sift through the sea of funding oppurtunities to find ones that meet their requirements.

## Features

- Semantic search capabilities for funding opportunities
- LLM-generated abstractive snippets for quick overview
- Query-focused summaries to assess relevance
- Integration with Elasticsearch for efficient data storage and retrieval
- Flexible LLM client support for snippet generation

## Getting started

### Prerequisites

- Python 3.12
- Conda (for environment management)
- Docker (for running Elasticsearch)
- Access to an LLM API (e.g. OpenAI)

### Set up conda environment

1. #### Create and activate environment
```
conda create -n search_env python=3.12
conda activate search_env
```
2. #### Install dependencies
```
pip install --upgrade pip
pip install -r ./requirements.txt
```

### Get the RankGPT library
Clone the [RankGPT library](https://github.com/sunnweiwei/RankGPT) into grantquest/external if you want to use it for re-ranking

### Set up ElasticSearch
GrantQuest is built on an underlying ElasticSearch index. Elasticsearch is the distributed search and analytics engine at the heart of the Elastic Stack. It is where the indexing, search, and analysis magic happens. Elasticsearch provides near real-time search and analytics for all types of data. Whether you have structured or unstructured text, numerical data, or geospatial data, Elasticsearch can efficiently store and index it in a way that supports fast searches.

You can use [this tutorial](https://www.elastic.co/guide/en/elasticsearch/reference/current/run-elasticsearch-locally.html) to quickly spin up a single-node Elasticsearch cluster in Docker.


### Build search index
For detailed instructions on building the search index, refer to [elasticsearch/README.md](elasticsearch/README.md)

### Run Flask application
To set up and run the Flask application, see [grantquest/README.md](grantquest/README.md)

## Report
See [report.pdf](./report.pdf)

## Demo video

The demo video can be found [here](https://drive.google.com/drive/folders/1pReQ1U_xJsdKp3ptLCzuc2GdU643Tf40?usp=sharing).


## Future Work

- Develop scripts to automatically update index with latest grants. Also, regularly clean out closed grants.
- Collect user actions/preferences to train LTR model.
- Fine-tune LLM for snippet generation.


## Change Log

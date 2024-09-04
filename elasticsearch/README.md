# GrantQuest - Semantic search for funding oppurtunities

#### GrantQuest is a semantic search engine I developed at Forward Data Lab at UIUC under the guidance of Prof. Kevin Chang. It allows interested parties to search for relevant funding oppurtunities. Aided by LLM -generated abstractive and query-focused snippets, individual researchers and organisations can quickly sift through the sea of funding oppurtunities to find ones that meet their requirements.

## Build the search index

#### This directory contains the notebooks required for indexing data using ElasticSearch. You can modify this process to index your own data.

### Data
The data used was scraped from the Internet and included grants till the end of 2023. 

The data is available [here](https://drive.google.com/drive/folders/1pReQ1U_xJsdKp3ptLCzuc2GdU643Tf40?usp=sharing).

[This repository](https://github.com/ericmuckley/foa-finder) contains an automated web scraper for finding funding opportunity announcements from grants.gov. 

Every day, the [grants.gov](grants.gov) database is updated and exported to a zipped XML file which is available for download [here](https://www.grants.gov/xml-extract). 

### Indexing options

#### Full-text

Full-text search is a search technique that looks for matches of a search query within the entire text of a document or a set of documents. It searches for all occurrences of the words or phrases that are specified in the search query, regardless of their location or context within the document.

In full-text search, the text is analyzed to identify the individual words or terms that occur in the document. These words or terms are then indexed, along with their location in the document. When a search query is submitted, the search engine looks up the index to find all the documents that contain the query terms and returns them in order of relevance.

To build an index for full-text search, you can follow [this notebook](./full-text/index.ipynb)

#### Semantic

In full-text search, the emphasis is primarily on keyword matching. It treats each word independently, without considering the relationships between them or the overall context. It retrieves documents or web pages that contain the exact keywords specified in the query. 

On the other hand, semantic search aims to understand the user’s intent behind queries by analyzing its semantics, context, and relationships between words or concepts. This type of search is intended to improve the quality of search results by interpreting natural language more accurately and in context.

A vector search-enabled semantic search produces results by working at both ends of the query pipeline simultaneously: When a query is launched, the search engine transforms the query into embeddings, which are numerical representations of data and related contexts. They are stored in vectors. The kNN algorithm, or k-nearest neighbor algorithm, then matches vectors of existing documents (a semantic search concerns text) to the query vectors. The semantic search then generates results and ranks them based on conceptual relevance.

Elastic search uses approximate kNN to enhance search speed.

To build an index for semantic search, you can follow [this notebook](./semantic/index.ipynb)


#### Semantic with 'normalized documents'

Semantic search is a good method to ensure the search engine takes the context/meaning of the queries into account. 

However the grants are generally long documents, and generating embeddings for long documents has several drawbacks - 
1. Token Limitations:
Token Limit: Most embedding models, like those based on transformers, have a token limit. If a document exceeds this limit, it cannot be embedded in one go, requiring splitting into smaller chunks.
Context Loss: Splitting a document can lead to loss of context, where important relationships between parts of the text are not captured. This can affect the quality of the embedding.
2. Chunking Strategy:
Arbitrary Splits: Naive chunking (e.g., splitting after a certain number of tokens or words) can lead to segments that cut through sentences or paragraphs, resulting in less meaningful embeddings.
Optimal Splitting: Deciding where to split (e.g., after paragraphs, sections, or sentences) to maintain coherence while staying within token limits is challenging and often requires a balance between granularity and context preservation.
3. Combining Embeddings:
Aggregation Methods: After chunking, combining the embeddings of different chunks into a single representation for the whole document can be problematic. Common approaches like averaging may not capture the document's overall meaning accurately.
Loss of Detail: Aggregation might dilute the importance of specific sections, especially if the document contains diverse topics or themes.
4. Increased Computational Costs:
Multiple Embeddings: For long documents, each chunk requires separate embedding, increasing computational costs in terms of both time and resources.
Storage and Retrieval: Storing and retrieving embeddings for large documents can become resource-intensive, especially if embeddings are computed for multiple chunks and stored individually.
5. Contextual Overlap and Redundancy:
Overlapping Chunks: To mitigate context loss, some methods involve creating overlapping chunks. While this can help maintain context, it also leads to redundancy in embedding computation and storage.
Handling Overlap: Determining the appropriate overlap size to balance context preservation and redundancy is non-trivial and varies depending on the document and use case.
6. Loss of Global Structure:
Hierarchical Information: Long documents often have a hierarchical structure (e.g., sections, subsections). Embedding small chunks might ignore this structure, leading to a loss of the document's overall organization and flow in the final embeddings.

To deal with these issues, we developed a document normalization method - 
1. use an LLM to generate detail-rich, structured summaries for all documents.
2. generate embeddings for these normalized documents and add to the index.
3. perform approximate kNN using the 'normalized embeddings'.

We found that the results from these metrics show that the use of normalized document embeddings in Elasticsearch significantly improved retrieval performance, achieving results comparable to the Jina Reranker v2, which is considered a state-of-the-art model.

To build an index for semantic search with normalized documents, you can follow [this notebook](./distill/index.ipynb)

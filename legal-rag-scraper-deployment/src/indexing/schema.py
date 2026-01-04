from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    VectorSearchAlgorithmConfiguration,
)

def create_index_schema(index_name):
    """Create the search index schema for legal documents."""
    
    # Define fields - aligned with instructions/index structure.json
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="chunk_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="parent_id", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="chunk", type=SearchFieldDataType.String),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SimpleField(name="document_type", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="court_name", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="section_title", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="url", type=SearchFieldDataType.String),
        SimpleField(name="document_url", type=SearchFieldDataType.String),
        SimpleField(name="pdf_url", type=SearchFieldDataType.String),
        SimpleField(name="last_updated", type=SearchFieldDataType.String, filterable=True, sortable=True),
        # Vector field for embeddings
        SimpleField(name="chunk_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), 
                   vector_search_dimensions=1536, vector_search_profile_name="embedding_profile"),
    ]
    
    # Define vector search configuration
    vector_search = VectorSearch(
        algorithms=[
            VectorSearchAlgorithmConfiguration(
                name="hnsw-config",
                kind="hnsw",
                hnsw_parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="embedding_profile",
                algorithm_configuration_name="hnsw-config",
            )
        ]
    )
    
    # Create and return index
    return SearchIndex(name=index_name, fields=fields, vector_search=vector_search)

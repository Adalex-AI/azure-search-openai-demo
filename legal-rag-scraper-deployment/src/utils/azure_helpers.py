from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential, AzureCliCredential
import os
import sys
from typing import List, Dict, Any

# Add the parent directory to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.config import Config

def get_azure_credentials():
    """
    Get Azure credentials for authentication.
    
    Returns:
        Azure credential object for authentication with Azure services.
    """
    return Config.get_credentials()

def get_search_client(index_name):
    """
    Get an Azure AI Search client for the specified index.
    
    Args:
        index_name: Name of the search index
        
    Returns:
        SearchClient object connected to the specified index
    """
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential
    
    # Use API key authentication directly for more reliable access
    search_endpoint = Config.AZURE_SEARCH_SERVICE
    
    return SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(Config.AZURE_SEARCH_KEY)
    )

def get_index_client():
    """
    Get an Azure AI Search index client for index management.
    
    Returns:
        SearchIndexClient object for managing search indexes
    """
    from azure.search.documents.indexes import SearchIndexClient
    from azure.core.credentials import AzureKeyCredential
    
    # Use API key authentication directly for more reliable access
    search_endpoint = Config.AZURE_SEARCH_SERVICE
    
    return SearchIndexClient(
        endpoint=search_endpoint,
        credential=AzureKeyCredential(Config.AZURE_SEARCH_KEY),
        api_version="2023-11-01"  # Use a compatible API version
    )

def get_indexer_client():
    """
    Get an Azure AI Search indexer client for indexer management.
    
    Returns:
        SearchIndexerClient object for managing search indexers
    """
    from azure.search.documents.indexes import SearchIndexerClient
    from azure.core.credentials import AzureKeyCredential
    
    # Use API key authentication directly for more reliable access
    search_endpoint = Config.AZURE_SEARCH_SERVICE
    
    return SearchIndexerClient(
        endpoint=search_endpoint,
        credential=AzureKeyCredential(Config.AZURE_SEARCH_KEY),
        api_version="2023-11-01"  # Use a compatible API version
    )

def get_openai_client():
    """
    Get an Azure OpenAI client for API access.
    
    Returns:
        AzureOpenAI client object
    """
    from openai import AzureOpenAI
    
    # Use direct API key authentication since there's an issue with token auth
    return AzureOpenAI(
        api_key=Config.AZURE_OPENAI_KEY,
        api_version="2023-12-01-preview",  # Using a more stable API version
        azure_endpoint=Config.AZURE_OPENAI_ENDPOINT  # Fixed variable name
    )

from azure.search.documents.indexes.models import SearchIndex, SearchField, SearchFieldDataType

def create_search_index(index_name, fields, endpoint):
    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
    
    index = SearchIndex(name=index_name, fields=fields)
    result = index_client.create_or_update_index(index)
    return result

def create_vector_search_index(index_name, fields, endpoint, vector_config=None):
    """
    Create a search index with vector search capabilities.
    
    Args:
        index_name: Name of the search index
        fields: List of search fields
        endpoint: Azure Search endpoint
        vector_config: Optional vector configuration dictionary
        
    Returns:
        Created search index
    """
    from azure.search.documents.indexes.models import (
        SearchIndex, 
        VectorSearch, 
        VectorSearchProfile,
        VectorSearchAlgorithmConfiguration,
        SearchField,
        SearchFieldDataType,
        VectorSearchAlgorithmMetric
    )
    from azure.core.credentials import AzureKeyCredential
    
    # If vector configuration isn't provided, use default settings
    if vector_config is None:
        vector_config = {
            "profile_name": "default-profile",
            "algorithm_name": "default-algorithm",
            "model_name": "text-embedding-ada-002",  # Required model name parameter
            "vector_field_name": "contentVector",
            "dimensions": 1536
        }
    
    # Create a vector search field
    vector_field = SearchField(
        name=vector_config["vector_field_name"],
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        dimensions=vector_config["dimensions"],
        vector_search_profile=vector_config["profile_name"]
    )
    
    # Add vector field to the fields list
    fields_with_vector = list(fields)  # Create a copy
    fields_with_vector.append(vector_field)
    
    # Create algorithm configuration (standard HNSW algorithm configuration)
    algorithm_config = VectorSearchAlgorithmConfiguration(
        name=vector_config["algorithm_name"],
        kind="hnsw",
        hnsw_parameters={
            "m": 4,
            "efConstruction": 400,
            "efSearch": 500,
            "metric": "cosine"
        }
    )
    
    # Create vector search profile
    vector_search_profile = VectorSearchProfile(
        name=vector_config["profile_name"],
        algorithm_configuration_name=vector_config["algorithm_name"]
    )
    
    # Configure vector search
    vector_search = VectorSearch(
        profiles=[vector_search_profile],
        algorithms=[algorithm_config]
    )
    
    # Create the search index with vector search capabilities
    index = SearchIndex(
        name=index_name,
        fields=fields_with_vector,
        vector_search=vector_search
    )
    
    # Create the index client with a compatible API version
    index_client = SearchIndexClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(Config.AZURE_SEARCH_KEY),
        api_version="2023-07-01-Preview"  # Using a preview API version that supports vector search
    )
    
    result = index_client.create_or_update_index(index)
    return result

def get_pdf_fields():
    return [
        SearchField(name="parent_id", type=SearchFieldDataType.String),
        SearchField(name="title", type=SearchFieldDataType.String),
        SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True),
        SearchField(name="chunk", type=SearchFieldDataType.String, sortable=False, filterable=False, facetable=False),
        SearchField(name="court_type", type=SearchFieldDataType.String, filterable=True)
    ]

def get_json_fields():
    return [
        SearchField(name="court_name", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="case_details", type=SearchFieldDataType.String),
        SearchField(name="relevant_court", type=SearchFieldDataType.String, filterable=True)
    ]

def merge_results_with_rrf(keyword_results: List[Dict[str, Any]], 
                           vector_results: List[Dict[str, Any]], 
                           k: float = 60.0) -> List[Dict[str, Any]]:
    """
    Merge results from keyword and vector searches using Reciprocal Rank Fusion.
    
    Args:
        keyword_results: Results from keyword search
        vector_results: Results from vector search
        k: Constant to prevent division by zero and smooth the impact of high rankings
        
    Returns:
        List of merged and re-ranked results
    """
    # Create a dictionary to store combined scores
    combined_scores = {}
    
    # Process keyword results
    for rank, result in enumerate(keyword_results):
        result_id = result.get('id', '')
        if not result_id:
            continue
            
        # RRF formula: 1 / (rank + k)
        score = 1.0 / (rank + k)
        combined_scores[result_id] = {
            'document': result,
            'score': score,
            'keyword_rank': rank
        }
    
    # Process vector results
    for rank, result in enumerate(vector_results):
        result_id = result.get('id', '')
        if not result_id:
            continue
            
        # RRF formula: 1 / (rank + k)
        score = 1.0 / (rank + k)
        
        if result_id in combined_scores:
            # Add scores if document exists in both result sets
            combined_scores[result_id]['score'] += score
            combined_scores[result_id]['vector_rank'] = rank
        else:
            combined_scores[result_id] = {
                'document': result,
                'score': score,
                'vector_rank': rank
            }
    
    # Sort by combined score (descending)
    sorted_results = sorted(
        combined_scores.values(), 
        key=lambda x: x['score'], 
        reverse=True
    )
    
    # Return just the documents
    return [item['document'] for item in sorted_results]

def perform_hybrid_search(search_client, query_text, filter_condition=None, top=10):
    """
    Perform a hybrid search combining keyword and vector search.
    
    Args:
        search_client: Azure Search client
        query_text: Text query to search for
        filter_condition: Optional OData filter string
        top: Number of results to return
        
    Returns:
        Combined search results
    """
    from azure.search.documents.models import VectorizableTextQuery
    
    # Perform keyword search
    keyword_results = list(search_client.search(
        search_text=query_text,
        filter=filter_condition,
        select="id,title,content,document_type,court_name,url,pdf_url",
        top=top
    ))
    
    # Perform vector search - no explicit embeddings generation for simplicity
    # Azure Search will handle text-to-vector conversion with the vectorizer in the index
    vector_query = VectorizableTextQuery(
        text=query_text,
        k_nearest_neighbors=top,
        fields="content_vector"
    )
    
    vector_results = list(search_client.search(
        search_text=None,  # No text search component
        vector_queries=[vector_query],
        filter=filter_condition,
        select="id,title,content,document_type,court_name,url,pdf_url",
        top=top
    ))
    
    # Merge results using RRF
    combined_results = merge_results_with_rrf(keyword_results, vector_results)
    
    return combined_results

def perform_multi_stage_search(search_client, query_text):
    """
    Perform a multi-stage search that first searches civil procedure rules and then court guides if needed.
    
    Args:
        search_client: Azure Search client
        query_text: Text query to search for
        
    Returns:
        Dictionary with search results for rules and guides
    """
    # First search: Civil Procedure Rules and Practice Directions
    rules_results = perform_hybrid_search(
        search_client,
        query_text,
        filter_condition="document_type eq 'civil_rules_and_practice_directions'",
        top=5
    )
    
    # More comprehensive check if query might be about a specific court
    court_terms = [
        "commercial court", "circuit commercial", "chancery", 
        "administrative court", "king's bench", "queen's bench", 
        "technology and construction", "tcc", "business and property"
    ]
    
    court_related = any(court_term in query_text.lower() for court_term in court_terms)
    
    # If no good results from rules or query is court-specific, check court guides
    court_guides_results = []
    if court_related or (rules_results and len(rules_results) < 2):
        # Second search: Court Guides
        court_guides_results = perform_hybrid_search(
            search_client,
            query_text,
            filter_condition="document_type eq 'court_guide'",
            top=5
        )
        
        # If court is specifically mentioned, prioritize court guide results
        if court_related and court_guides_results:
            return {
                "primary_results": court_guides_results,
                "secondary_results": rules_results
            }
    
    return {
        "primary_results": rules_results,
        "secondary_results": court_guides_results
    }

def create_azure_openai_vectorizer(name="text-vector-vectorizer", model_name="text-embedding-ada-002"):
    """
    Create a properly configured VectorSearchVectorizer for Azure OpenAI.
    
    Args:
        name: Name of the vectorizer
        model_name: Name of the embedding model
        
    Returns:
        Configured VectorSearchVectorizer object
    """
    from azure.search.documents.indexes.models import VectorSearchVectorizer
    
    return VectorSearchVectorizer(
        name=name,
        kind="azureOpenAI",
        vectorizer_name="text-embedding-vectorizer",  # Required parameter
        azureOpenAI={
            "resourceUri": Config.AZURE_OPENAI_ENDPOINT,
            "deploymentName": Config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,  # Correct parameter name
            "apiKey": Config.AZURE_OPENAI_KEY,
            "modelName": model_name
        }
    )

# Simplified helper to create a complete vector search configuration
def create_vector_search_config(vector_field_name="text_vector", dimensions=1536):
    """
    Create a complete vector search configuration with proper settings.
    
    Args:
        vector_field_name: Name of the vector field
        dimensions: Dimensions of the vector embeddings
        
    Returns:
        Dictionary containing vector search components
    """
    # Complete vector search configuration using only a dictionary approach
    # This avoids issues with SDK model parameter names
    vector_search = {
        "algorithms": [
            {
                "name": "default-algorithm",
                "kind": "hnsw",
                "hnswParameters": {
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            }
        ],
        "profiles": [
            {
                "name": "default-profile",
                "algorithmConfigurationName": "default-algorithm"
            }
        ]
    }
    
    return {
        "vector_search": vector_search,
        "field_name": vector_field_name,
        "dimensions": dimensions,
        "profile_name": "default-profile"
    }

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from openai import AzureOpenAI

from ..config import get_search_config, get_openai_config

def create_search_service_client():
    """Create an Azure Search service client."""
    config = get_search_config()
    return SearchIndexClient(
        endpoint=config["endpoint"],
        credential=AzureKeyCredential(config["admin_key"])
    )

def create_search_index_client(index_name=None):
    """Create an Azure Search index client."""
    config = get_search_config()
    if index_name is None:
        index_name = config["index_name"]
    
    return SearchClient(
        endpoint=config["endpoint"],
        index_name=index_name,
        credential=AzureKeyCredential(config["admin_key"])
    )

def create_openai_client():
    """Create an Azure OpenAI client."""
    config = get_openai_config()
    return AzureOpenAI(
        azure_endpoint=config["endpoint"],
        api_key=config["api_key"], 
        api_version=config["api_version"]
    )
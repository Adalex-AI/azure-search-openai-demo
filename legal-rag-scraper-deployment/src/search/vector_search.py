from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from ..config import Config
from ..utils.azure_helpers import get_azure_credentials, get_search_client

class VectorSearchClient:
    """Client for performing vector search against Azure Cognitive Search"""
    
    def __init__(self):
        """Initialize the search client with configuration from Config"""
        self.search_endpoint = Config.AZURE_SEARCH_SERVICE
        self.credentials = get_azure_credentials()
        
    def search(self, query, index_name="legal-court-rag-index", filter=None, top=10, use_vector=True):
        """
        Perform a vector search using the Azure OpenAI vectorizer
        
        Args:
            query (str): The search query that will be vectorized
            index_name (str): Name of the index to search
            filter (str): OData filter expression 
            top (int): Number of results to return
            use_vector (bool): Whether to use vector search (falls back to keyword if False)
            
        Returns:
            list: Search results
        """
        # Create a search client for the specified index
        search_client = get_search_client(index_name)
        
        # Build search parameters
        search_params = {
            "select": "chunk_id,chunk,title,parent_id,document_type,court_name,rule_reference,rule_category,pdf_url,overview_url",
            "top": top,
        }
        
        # Add filter if specified
        if filter:
            search_params["filter"] = filter
        
        try:
            if use_vector:
                # Attempt vector search first
                search_params["vector_queries"] = [
                    {
                        "kind": "text",
                        "text": query,
                        "fields": "text_vector",
                        "k": top
                    }
                ]
                # For vector search, use empty string as search text
                results = search_client.search("", **search_params)
            else:
                # Fall back to keyword search
                results = search_client.search(query, **search_params)
                
            # Convert results to list
            return [result for result in results]
                
        except Exception as e:
            print(f"Vector search failed with error: {str(e)}")
            print("Falling back to keyword search...")
            # Remove vector query parameters if they exist
            if "vector_queries" in search_params:
                del search_params["vector_queries"]
            # Use the query as the search text
            try:
                results = search_client.search(query, **search_params)
                return [result for result in results]
            except Exception as fallback_error:
                print(f"Keyword fallback search also failed: {str(fallback_error)}")
                return []
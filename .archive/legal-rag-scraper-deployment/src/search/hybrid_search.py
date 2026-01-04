from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from ..config import Config
from ..utils.azure_helpers import get_azure_credentials, get_search_client, merge_results_with_rrf
from typing import List, Dict, Any, Optional

class HybridSearchClient:
    """Client for performing hybrid search (vector + keyword) against Azure Cognitive Search"""
    
    def __init__(self):
        """Initialize the search client with configuration from Config"""
        self.search_endpoint = Config.AZURE_SEARCH_SERVICE
        self.credentials = get_azure_credentials()
        
        # Set up OpenAI for embeddings
        try:
            from ..utils.azure_helpers import get_openai_client
            self.openai_client = get_openai_client()
            self.embedding_deployment = Config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI client: {str(e)}")
            self.openai_client = None
        
    def _get_search_client(self, index_name):
        """Get a search client for the specified index"""
        return get_search_client(index_name)
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using Azure OpenAI"""
        try:
            if not self.openai_client:
                print("Warning: OpenAI client not initialized. Cannot generate embeddings.")
                return []
                
            if len(text) > 25000:  # Rough approximation to avoid token limits
                text = text[:25000]
                
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return []
    
    def search(self, query, index_name="legal-court-rag-index", filter=None, top=10, 
               semantic_configuration_name=None, vector_fields=None, use_semantic_ranking=True,
               keyword_search=True):
        """
        Perform a hybrid search combining vector and keyword search
        
        Args:
            query (str): The search query
            index_name (str): Name of the index to search
            filter (str): OData filter expression
            top (int): Number of results to return
            semantic_configuration_name (str): Name of the semantic configuration to use for ranking
            vector_fields (list): List of vector fields to include in search
            use_semantic_ranking (bool): Whether to use semantic ranking
            keyword_search (bool): Whether to include keyword search component
            
        Returns:
            list: Search results
        """
        # Create a search client for the specified index
        search_client = self._get_search_client(index_name)
        
        # Build search parameters for keyword search
        keyword_params = {
            "search_text": query,
            "search_fields": ["title", "chunk", "rule_reference", "description"],
            "select": "chunk_id,chunk,title,parent_id,document_type,court_name,rule_reference,rule_category,pdf_url,overview_url",
            "top": top * 2,  # Get more results for better RRF merging
            "scoring_profile": "text_weights_profile"  # Updated to use the new scoring profile
        }
        
        # Add filter if specified
        if filter:
            keyword_params["filter"] = filter
        
        # Add semantic search if requested
        if use_semantic_ranking and semantic_configuration_name:
            keyword_params["query_type"] = "semantic"
            keyword_params["semantic_configuration_name"] = semantic_configuration_name

        # Prepare vector search parameters
        vector_params = keyword_params.copy()
        vector_params["search_text"] = ""  # Empty search text for vector search
        
        # Create vector query if we have embeddings capability
        vector = None
        if vector_fields and self.openai_client:
            vector = self._generate_embedding(query)
            if vector:
                vector_params["vector_queries"] = [
                    {
                        "kind": "text",
                        "text": query,
                        "fields": vector_fields[0] if isinstance(vector_fields, list) else "text_vector",
                        "k": top * 2
                    }
                ]
        
        # Execute searches and merge results
        keyword_results = []
        vector_results = []
        
        # Execute keyword search if requested
        if keyword_search:
            try:
                keyword_results = list(search_client.search(**keyword_params))
                print(f"Keyword search found {len(keyword_results)} results")
            except Exception as e:
                print(f"Keyword search error: {str(e)}")
        
        # Execute vector search if we have vectors and vector search is requested
        if vector and vector_params.get("vector_queries"):
            try:
                vector_results = list(search_client.search(**vector_params))
                print(f"Vector search found {len(vector_results)} results")
            except Exception as e:
                print(f"Vector search error: {str(e)}")
        
        # Merge results using RRF algorithm if we have both types of results
        if keyword_results and vector_results and keyword_search:
            merged_results = merge_results_with_rrf(keyword_results, vector_results)
            print(f"Merged {len(keyword_results)} keyword and {len(vector_results)} vector results into {len(merged_results)} results using RRF")
            return merged_results
        elif keyword_results:
            return keyword_results
        elif vector_results:
            return vector_results
        else:
            return []
        
    def multi_stage_search(self, query: str, index_name: str = "legal-court-rag-index", 
                          top_rules: int = 5, top_guides: int = 5) -> Dict[str, List[Any]]:
        """
        Perform a two-stage search that prioritizes civil procedure rules and practice
        directions before looking at court guides.
        
        Args:
            query (str): The user's query
            index_name (str): The search index name
            top_rules (int): Maximum number of rule results to return
            top_guides (int): Maximum number of court guide results to return
            
        Returns:
            Dict containing results from both stages
        """
        results = {
            "rules": [],
            "court_guides": [],
            "query": query
        }
        
        # First stage: Search civil procedure rules and practice directions
        rule_filter = "document_type eq 'civil_rules' or document_type eq 'practice_direction'"
        rules_results = self.search(
            query=query,
            index_name=index_name,
            filter=rule_filter,
            top=top_rules,
            use_semantic_ranking=True,
            vector_fields=["text_vector"]
        )
        results["rules"] = rules_results
        
        # Determine if we need to look at court guides based on query content
        # Check if the query might be asking about a specific court
        court_keywords = [
            "commercial court", "kings bench", "queen's bench", "high court",
            "chancery", "circuit", "technology and construction", "administrative court",
            "business and property courts", "TCC", "KBD", "admin court"
        ]
        
        need_court_guides = any(keyword.lower() in query.lower() for keyword in court_keywords)
        
        # If we explicitly need court guides or found limited rule results, search guides
        if need_court_guides or len(rules_results) < 2:
            guide_filter = "document_type eq 'court_guide'"
            guide_results = self.search(
                query=query,
                index_name=index_name,
                filter=guide_filter,
                top=top_guides,
                use_semantic_ranking=True,
                vector_fields=["text_vector"]
            )
            results["court_guides"] = guide_results
        
        return results
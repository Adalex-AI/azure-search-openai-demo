import os
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SearchIndex,
    SearchIndexerDataContainer,
    SearchIndexerDataSourceConnection,
    SplitSkill,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    AzureOpenAIEmbeddingSkill,
    EntityRecognitionSkill,
    SearchIndexerIndexProjection,
    SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjectionsParameters,
    IndexProjectionMode,
    SearchIndexerSkillset,
    CognitiveServicesAccountKey,
    SearchIndexer,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch,
    ScoringProfile,
    TagScoringFunction,
    TagScoringParameters,
    ScalarQuantizationCompression,
    ScalarQuantizationParameters
)
from ..config import Config


class IndexingService:
    """Service to handle Azure Search indexing operations"""
    
    def __init__(self):
        self.credentials = Config.get_credentials()
        self.search_endpoint = Config.AZURE_SEARCH_SERVICE
        self.openai_endpoint = Config.AZURE_OPENAI_ACCOUNT
        self.ai_services_key = Config.AZURE_AI_MULTISERVICE_KEY
        self.storage_connection = Config.AZURE_STORAGE_CONNECTION
        
        self.index_client = SearchIndexClient(endpoint=self.search_endpoint, credential=self.credentials)
        self.indexer_client = SearchIndexerClient(endpoint=self.search_endpoint, credential=self.credentials)
    
    def create_basic_index(self, index_name="legal-court-rag-index"):
        """Create a basic search index with vector search capabilities"""
        
        print(f"Creating index: {index_name}")
        
        fields = [
            SearchField(name="parent_id", type=SearchFieldDataType.String),  
            SearchField(name="title", type=SearchFieldDataType.String, searchable=True),
            # Add document_type field to distinguish between CPR JSON and court guides
            SearchField(name="document_type", type=SearchFieldDataType.String, filterable=True, facetable=True),
            # Add court_name field to allow filtering by specific court
            SearchField(name="court_name", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchField(name="locations", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True),
            SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True, analyzer_name="keyword"),  
            SearchField(name="chunk", type=SearchFieldDataType.String, searchable=True),  
            SearchField(name="text_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), 
                       vector_search_dimensions=1024, vector_search_profile_name="myHnswProfile"),
            # Add new court guide metadata fields
            SearchField(name="pdf_url", type=SearchFieldDataType.String),
            SearchField(name="overview_url", type=SearchFieldDataType.String),
            SearchField(name="last_updated", type=SearchFieldDataType.String),
            SearchField(name="description", type=SearchFieldDataType.String, searchable=True)
        ]  
        
        # Configure the vector search  
        vector_search = VectorSearch(  
            algorithms=[  
                HnswAlgorithmConfiguration(name="myHnsw"),
            ],  
            profiles=[  
                VectorSearchProfile(  
                    name="myHnswProfile",  
                    algorithm_configuration_name="myHnsw",  
                    vectorizer_name="myOpenAI",  
                )
            ],  
            vectorizers=[  
                AzureOpenAIVectorizer(  
                    vectorizer_name="myOpenAI",  
                    kind="azureOpenAI",  
                    parameters=AzureOpenAIVectorizerParameters(  
                        resource_url=self.openai_endpoint,  
                        deployment_name="text-embedding-3-large",
                        model_name="text-embedding-3-large"
                    ),
                ),  
            ], 
        )  
        
        # Add semantic configuration with priority on CPR content
        semantic_config = SemanticConfiguration(
            name="legal-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                keywords_fields=[
                    SemanticField(field_name="document_type"), 
                    SemanticField(field_name="court_name"),
                    SemanticField(field_name="locations")
                ],
                content_fields=[
                    SemanticField(field_name="chunk"),
                    SemanticField(field_name="description")  # Add description field to semantic search
                ]
            )
        )
        
        semantic_search = SemanticSearch(configurations=[semantic_config])
        
        # Create the search index
        index = SearchIndex(
            name=index_name, 
            fields=fields, 
            vector_search=vector_search,
            semantic_search=semantic_search
        )  
        result = self.index_client.create_or_update_index(index)  
        print(f"Index '{result.name}' created")
        return result
    
    # Rest of the IndexingService class methods
    def create_optimized_index(self, index_name="legal-court-rag-optimized-index"):
        """Create an optimized search index with vector compression, semantic search, and scoring profiles"""
        
        print(f"Creating optimized index: {index_name}")
        
        fields = [
            SearchField(name="parent_id", type=SearchFieldDataType.String),  
            SearchField(name="title", type=SearchFieldDataType.String),
            SearchField(name="locations", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True),
            SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True, analyzer_name="keyword"),  
            SearchField(name="chunk", type=SearchFieldDataType.String, sortable=False, filterable=False, facetable=False),  
            SearchField(name="text_vector", type="Collection(Edm.Half)", 
                      vector_search_dimensions=1024, vector_search_profile_name="myHnswProfile", stored=False)
        ]  
        
        # Configure the vector search with compression
        vector_search = VectorSearch(  
            algorithms=[  
                HnswAlgorithmConfiguration(name="myHnsw"),
            ],  
            profiles=[  
                VectorSearchProfile(  
                    name="myHnswProfile",  
                    algorithm_configuration_name="myHnsw",
                    compression_name="myScalarQuantization",
                    vectorizer_name="myOpenAI",  
                )
            ],  
            vectorizers=[  
                AzureOpenAIVectorizer(  
                    vectorizer_name="myOpenAI",  
                    kind="azureOpenAI",  
                    parameters=AzureOpenAIVectorizerParameters(  
                        resource_url=self.openai_endpoint,
                        deployment_name="text-embedding-3-large",
                        model_name="text-embedding-3-large"
                    ),
                ),  
            ],
            compressions=[
                ScalarQuantizationCompression(
                    compression_name="myScalarQuantization",
                    rerank_with_original_vectors=True,
                    default_oversampling=10,
                    parameters=ScalarQuantizationParameters(quantized_data_type="int8"),
                )
            ]
        )
        
        # Add semantic configuration
        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                keywords_fields=[SemanticField(field_name="locations")],
                content_fields=[SemanticField(field_name="chunk")]
            )
        )
        
        semantic_search = SemanticSearch(configurations=[semantic_config])
        
        # Add scoring profile
        scoring_profiles = [  
            ScoringProfile(  
                name="my-scoring-profile",
                functions=[
                    TagScoringFunction(  
                        field_name="locations",  
                        boost=5.0,  
                        parameters=TagScoringParameters(  
                            tags_parameter="tags",  
                        ),  
                    ) 
                ]
            )
        ]
        
        # Create the index with all optimizations
        index = SearchIndex(
            name=index_name, 
            fields=fields, 
            vector_search=vector_search, 
            semantic_search=semantic_search, 
            scoring_profiles=scoring_profiles
        )  
        
        result = self.index_client.create_or_update_index(index)  
        print(f"Optimized index '{result.name}' created")
        return result
    
    def create_data_source(self, container_name="legal-court-documents", data_source_name="legal-court-rag-ds"):
        """Create a data source connection to Azure Blob Storage"""
        
        print(f"Creating data source: {data_source_name}")
        
        container = SearchIndexerDataContainer(name=container_name)
        data_source_connection = SearchIndexerDataSourceConnection(
            name=data_source_name,
            type="azureblob",
            connection_string=self.storage_connection,
            container=container
        )
        
        data_source = self.indexer_client.create_or_update_data_source_connection(data_source_connection)
        print(f"Data source '{data_source.name}' created or updated")
        return data_source
    
    def create_skillset(self, skillset_name="legal-court-rag-ss", index_name="legal-court-rag-index"):
        """Create a skillset for document processing"""
        
        print(f"Creating skillset: {skillset_name}")
        
        # Split skill to chunk documents
        split_skill = SplitSkill(  
            description="Split skill to chunk documents",  
            text_split_mode="pages",  
            context="/document",  
            maximum_page_length=2000,  
            page_overlap_length=500,  
            inputs=[  
                InputFieldMappingEntry(name="text", source="/document/content"),  
            ],  
            outputs=[  
                OutputFieldMappingEntry(name="textItems", target_name="pages")  
            ],  
        )  
        
        # Embedding skill
        embedding_skill = AzureOpenAIEmbeddingSkill(  
            description="Skill to generate embeddings via Azure OpenAI",  
            context="/document/pages/*",  
            resource_url=self.openai_endpoint,  
            deployment_name="text-embedding-3-large",  
            model_name="text-embedding-3-large",
            dimensions=1024,
            inputs=[  
                InputFieldMappingEntry(name="text", source="/document/pages/*"),  
            ],  
            outputs=[  
                OutputFieldMappingEntry(name="embedding", target_name="text_vector")  
            ],  
        )
        
        # Entity recognition skill
        entity_skill = EntityRecognitionSkill(
            description="Skill to recognize entities in text",
            context="/document/pages/*",
            categories=["Location"],
            default_language_code="en",
            inputs=[
                InputFieldMappingEntry(name="text", source="/document/pages/*")
            ],
            outputs=[
                OutputFieldMappingEntry(name="locations", target_name="locations")
            ]
        )
        
        # Index projections with document type and court metadata
        index_projections = SearchIndexerIndexProjection(  
            selectors=[  
                SearchIndexerIndexProjectionSelector(  
                    target_index_name=index_name,  
                    parent_key_field_name="parent_id",  
                    source_context="/document/pages/*",  
                    mappings=[  
                        InputFieldMappingEntry(name="chunk", source="/document/pages/*"),  
                        InputFieldMappingEntry(name="text_vector", source="/document/pages/*/text_vector"),
                        InputFieldMappingEntry(name="locations", source="/document/pages/*/locations"),  
                        InputFieldMappingEntry(name="title", source="/document/metadata_storage_name"),
                        # Add document type - default to "cpr_json" for .json files, "court_guide" for PDFs
                        InputFieldMappingEntry(name="document_type", source="/document/metadata_storage_file_extension"), 
                        # Extract court name from file path or metadata when available
                        InputFieldMappingEntry(name="court_name", source="/document/metadata_storage_name"),
                        # Add custom metadata fields if available
                        InputFieldMappingEntry(name="pdf_url", source="/document/pdf_url"),
                        InputFieldMappingEntry(name="overview_url", source="/document/overview_url"),
                        InputFieldMappingEntry(name="last_updated", source="/document/last_updated"),
                        InputFieldMappingEntry(name="description", source="/document/description"),
                    ],  
                ),  
            ],  
            parameters=SearchIndexerIndexProjectionsParameters(  
                projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS  
            ),  
        )
        
        # Cognitive services account for skillset
        cognitive_services_account = CognitiveServicesAccountKey(key=self.ai_services_key)
        
        skills = [split_skill, embedding_skill, entity_skill]
        
        skillset = SearchIndexerSkillset(  
            name=skillset_name,  
            description="Skillset to chunk documents and generating embeddings",  
            skills=skills,  
            index_projection=index_projections,
            cognitive_services_account=cognitive_services_account
        )
        
        result = self.indexer_client.create_or_update_skillset(skillset)  
        print(f"Skillset '{skillset.name}' created")  
        return result
    
    def create_indexer(self, indexer_name="legal-court-rag-idxr", 
                      skillset_name="legal-court-rag-ss", 
                      index_name="legal-court-rag-index",
                      data_source_name="legal-court-rag-ds"):
        """Create and run an indexer"""
        
        print(f"Creating indexer: {indexer_name}")
        
        indexer = SearchIndexer(  
            name=indexer_name,  
            description="Indexer for legal court documents",  
            skillset_name=skillset_name,  
            target_index_name=index_name,  
            data_source_name=data_source_name,
            parameters=None
        )  
        
        result = self.indexer_client.create_or_update_indexer(indexer)  
        print(f"Indexer '{indexer_name}' created and running. This may take some time.")  
        return result
    
    def run_indexer(self, indexer_name="legal-court-rag-idxr"):
        """Run an existing indexer"""
        
        print(f"Running indexer: {indexer_name}")
        self.indexer_client.run_indexer(indexer_name)
        print(f"Indexer '{indexer_name}' started.")
        
    def get_indexer_status(self, indexer_name="legal-court-rag-idxr"):
        """Get the status of an indexer"""
        
        status = self.indexer_client.get_indexer_status(indexer_name)
        print(f"Indexer '{indexer_name}' status: {status.last_result.status if status.last_result else 'Unknown'}")
        return status

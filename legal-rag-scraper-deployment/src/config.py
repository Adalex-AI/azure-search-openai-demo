import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Try to import Azure SDK components, but make them optional
try:
    from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential, AzureCliCredential
    AZURE_SDK_AVAILABLE = True
except ImportError:
    # Azure SDK not available - will use REST API only
    AZURE_SDK_AVAILABLE = False
    DefaultAzureCredential = None
    InteractiveBrowserCredential = None
    AzureCliCredential = None

# Load environment variables from .env file if it exists
load_dotenv()

# Base paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CIVIL_RULES_DIR = os.path.join(DATA_DIR, "civil_rules")
COURT_GUIDES_DIR = os.path.join(DATA_DIR, "court_guides")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed", "Upload")

# Ensure directories exist
for directory in [DATA_DIR, CIVIL_RULES_DIR, COURT_GUIDES_DIR, PROCESSED_DIR]:
    os.makedirs(directory, exist_ok=True)

"""
Configuration settings for the legal-court-rag application.
"""

class Config:
    """Configuration class for storing application settings."""
    
    # Azure Search settings
    AZURE_SEARCH_SERVICE = os.getenv('AZURE_SEARCH_SERVICE', 'https://your-search-service.search.windows.net')
    AZURE_SEARCH_KEY = os.getenv('AZURE_SEARCH_KEY', 'your-admin-key-here')
    AZURE_SEARCH_INDEX = "legal-court-rag"
    
    # Document processing settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 100
    
    # File paths
    DATA_DIR = "data"
    
    # Other settings
    VERBOSE = True

    # Configuration values - preferably set as environment variables
    AZURE_SEARCH_SERVICE = os.environ.get("AZURE_SEARCH_SERVICE", "https://your-search-service.search.windows.net")
    AZURE_SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY", "")  # No default key
    
    # Default to environment variables with no hardcoded fallbacks for sensitive values
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "https://your-openai-service.openai.azure.com/")
    AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY", "")  # No default key
    
    # Azure OpenAI model deployments
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
    AZURE_OPENAI_CHAT_DEPLOYMENT = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-35-turbo")

    # PDF Processing Configuration
    PDF_PROCESSING_CONFIG = {
        # Text chunking settings
        "chunk_size": 1000,  # Maximum characters per chunk
        "chunk_overlap": 100,  # Overlap between consecutive chunks
        
        # OCR settings
        "use_ocr": False,  # Whether to use OCR for scanned documents
        "ocr_language": "eng",  # Language for OCR (if enabled)
        "min_text_length_for_ocr": 50,  # Minimum text length threshold to trigger OCR
        
        # Document processing settings
        "include_page_numbers": True,  # Whether to include page numbers in extracted text
        "extract_court_references": True,  # Whether to extract court references
        
        # Court guide metadata mapping
        "court_guide_metadata_mapping": {
            # Maps field names from court guide to standardized field names for indexing
            "name": "guide_name",
            "last_updated": "guide_last_updated",
            "overview_url": "guide_overview_url",
            "description": "guide_description",
            "pdf_url": "guide_pdf_url"
        },
        
        # Court reference patterns (regular expressions)
        "court_reference_patterns": [
            r'(Commercial Court)',
            r'(Circuit Commercial Court)',
            r'(Chancery Division)',
            r'(Administrative Court)',
            r'(King\'s Bench Division)',
            r'(Queen\'s Bench Division)',
            r'(Technology and Construction Court)',
        ]
    }

    # Ensure embedding dimensions are set for text-embedding-3-large
    EMBEDDING_DIMENSIONS = 3072  # text-embedding-3-large embedding dimensions

    @staticmethod
    def get_credentials():
        """
        Get Azure credentials using the following priority:
        1. DefaultAzureCredential (managed identities, environment, etc.)
        2. AzureCliCredential (if Azure CLI is installed and logged in)
        3. InteractiveBrowserCredential (prompts user to login via browser)
        """
        try:
            # Try DefaultAzureCredential first (checks env vars, managed identity, etc.)
            return DefaultAzureCredential()
        except Exception as e:
            print(f"DefaultAzureCredential failed: {e}")
            
            try:
                # Try using Azure CLI credentials
                return AzureCliCredential()
            except Exception as e:
                print(f"AzureCliCredential failed: {e}")
                
                # Fall back to interactive browser login
                print("Initiating interactive browser login...")
                return InteractiveBrowserCredential()
    
    @staticmethod
    def is_using_key_auth():
        """Check if key-based authentication should be used"""
        return bool(Config.AZURE_SEARCH_KEY) and bool(Config.AZURE_OPENAI_KEY)
    
    @staticmethod
    def login_interactively():
        """Force interactive browser login"""
        print("Launching browser for Azure authentication...")
        return InteractiveBrowserCredential()
    
    @classmethod
    def validate_credentials(cls):
        """Validate that required credentials are available."""
        missing = []
        
        if not cls.AZURE_SEARCH_SERVICE:
            missing.append("AZURE_SEARCH_SERVICE")
            
        if not cls.AZURE_SEARCH_KEY:
            missing.append("AZURE_SEARCH_KEY")
            
        if not cls.AZURE_OPENAI_ENDPOINT:
            missing.append("AZURE_OPENAI_ENDPOINT")
            
        if not cls.AZURE_OPENAI_KEY:
            missing.append("AZURE_OPENAI_KEY")
            
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True

    @staticmethod
    def validate_openai_connection(verbose=False):
        """Validate OpenAI connection and provide troubleshooting guidance."""
        from openai import AzureOpenAI
        import traceback

        if not Config.AZURE_OPENAI_ENDPOINT or not Config.AZURE_OPENAI_KEY:
            print("❌ Missing OpenAI endpoint or API key")
            return False
            
        # Check if endpoint contains placeholder text
        if "your-openai" in Config.AZURE_OPENAI_ENDPOINT or "example" in Config.AZURE_OPENAI_ENDPOINT:
            print("❌ Error: You're using a placeholder OpenAI endpoint URL!")
            print("Please set your actual Azure OpenAI endpoint using:")
            print("1. Environment variable: AZURE_OPENAI_ENDPOINT")
            print("   or")
            print("2. Update src/config.py with your actual endpoint")
            print("\nExample of a valid endpoint: https://my-resource.openai.azure.com/")
            return False

        try:
            # Ensure endpoint has the correct format (ends with /)
            endpoint = Config.AZURE_OPENAI_ENDPOINT
            if not endpoint.endswith('/'):
                endpoint = endpoint + '/'
                
            client = AzureOpenAI(
                api_key=Config.AZURE_OPENAI_KEY,
                api_version="2023-05-15",
                azure_endpoint=endpoint
            )
            
            # Test with a simple embedding request
            response = client.embeddings.create(
                input=["Connection test"],
                model=Config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            
            if verbose:
                print("✅ OpenAI connection verified successfully!")
                
            return True
            
        except Exception as e:
            if verbose:
                print(f"❌ OpenAI connection failed: {str(e)}")
                print("\nFor detailed diagnostics, run: python scripts/diagnose_openai.py")
                
            return False

    @staticmethod
    def is_placeholder_url(url):
        """Check if a URL contains placeholder text."""
        if not url:
            return True
            
        placeholder_terms = [
            'your-', 'example', 'placeholder', 'my-resource', 
            '<replace>', '{your'
        ]
        
        return any(term in url.lower() for term in placeholder_terms)

    @staticmethod
    def validate_search_connection(verbose=False):
        """Validate Azure Search connection and provide troubleshooting guidance."""
        import requests
        
        if not Config.AZURE_SEARCH_SERVICE or not Config.AZURE_SEARCH_KEY:
            if verbose:
                print("❌ Missing Azure Search endpoint or API key")
            return False
        
        # Check if endpoint contains placeholder text
        if Config.is_placeholder_url(Config.AZURE_SEARCH_SERVICE):
            if verbose:
                print("❌ Error: You're using a placeholder Azure Search endpoint URL!")
                print("Please set your actual Azure Search endpoint using:")
                print("1. Environment variable: AZURE_SEARCH_SERVICE")
                print("2. Update src/config.py with your actual endpoint")
                print("\nExample of a valid endpoint: https://your-service-name.search.windows.net")
            return False
        
        # Ensure endpoint has the correct format
        endpoint = Config.AZURE_SEARCH_SERVICE.rstrip('/')
        
        if verbose:
            print(f"Testing connection to: {endpoint}")
        
        # Test the connection
        try:
            headers = {
                "Content-Type": "application/json",
                "api-key": Config.AZURE_SEARCH_KEY
            }
            
            response = requests.get(
                f"{endpoint}/indexes?api-version=2024-07-01",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                if verbose:
                    print("✅ Azure Search connection verified successfully!")
                return True
            else:
                if verbose:
                    print(f"❌ Azure Search connection failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            if verbose:
                print(f"❌ Azure Search connection failed: {str(e)}")
            return False

def get_search_config() -> Dict[str, Any]:
    """Get Azure Search service configuration from environment variables."""
    return {
        "service_name": os.environ.get("AZURE_SEARCH_SERVICE_NAME"),
        "admin_key": os.environ.get("AZURE_SEARCH_ADMIN_KEY"),
        "index_name": os.environ.get("AZURE_SEARCH_INDEX_NAME", "legal-court-index"),
        "endpoint": f"https://{os.environ.get('AZURE_SEARCH_SERVICE_NAME')}.search.windows.net/",
    }

def get_openai_config() -> Dict[str, Any]:
    """Get Azure OpenAI configuration from environment variables."""
    return {
        "endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT"),
        "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
        "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15"),
        "embedding_deployment_name": os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
        "completion_deployment_name": os.environ.get("AZURE_OPENAI_COMPLETION_DEPLOYMENT", "gpt-35-turbo"),
    }

def get_processing_config() -> Dict[str, Any]:
    """Get document processing configuration."""
    return {
        "chunk_size": int(os.environ.get("CHUNK_SIZE", "1000")),
        "chunk_overlap": int(os.environ.get("CHUNK_OVERLAP", "200")),
    }
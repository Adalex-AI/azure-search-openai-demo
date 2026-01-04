#!/usr/bin/env python
"""
Script to create a very basic Azure Search index first,
before attempting vector search capabilities.
"""
import os
import sys
import argparse
import requests
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.config import Config

def create_basic_index(index_name="legal-court-basic-index", recreate=False):
    """
    Create a simple Azure Search index with basic fields and no vector search.
    Uses direct REST API calls for maximum reliability.
    
    Args:
        index_name (str): Name of the index to create
        recreate (bool): If True, delete existing index if it exists
    """
    print(f"Creating basic search index: {index_name}")
    
    # Format the endpoint properly to remove any trailing slashes
    search_endpoint = Config.AZURE_SEARCH_SERVICE.rstrip('/')
    print(f"Using search service endpoint: {search_endpoint}")
    
    # Initialize REST API headers
    headers = {
        "Content-Type": "application/json",
        "api-key": Config.AZURE_SEARCH_KEY
    }
    
    # Test connection and check for existing indexes
    try:
        list_url = f"{search_endpoint}/indexes?api-version=2021-04-30-Preview"
        response = requests.get(list_url, headers=headers)
        
        if response.status_code == 200:
            indexes = response.json().get('value', [])
            print(f"Connection successful! Found {len(indexes)} existing indexes.")
            
            # List the indexes for troubleshooting
            for idx in indexes:
                print(f"  - {idx.get('name')}")
        else:
            print(f"Connection test failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Connection test failed with exception: {str(e)}")
        return None
    
    # Delete existing index if recreate is True
    if recreate:
        try:
            delete_url = f"{search_endpoint}/indexes/{index_name}?api-version=2021-04-30-Preview"
            delete_response = requests.delete(delete_url, headers=headers)
            
            if delete_response.status_code in [200, 204, 404]:
                print(f"Deleted existing index or index did not exist: {index_name}")
            else:
                print(f"Warning: Delete request returned status {delete_response.status_code} - {delete_response.text}")
        except Exception as e:
            print(f"Note when attempting to delete index: {str(e)}")
    
    # Create a very basic index definition - no vector search, just basic fields
    index_definition = {
        "name": index_name,
        "fields": [
            {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
            {"name": "content", "type": "Edm.String", "searchable": True},
            {"name": "title", "type": "Edm.String", "searchable": True},
            {"name": "document_type", "type": "Edm.String", "filterable": True}
        ]
    }
    
    print(f"Creating basic index: {index_name} via REST API...")
    
    # Create the index using direct REST API call
    create_url = f"{search_endpoint}/indexes?api-version=2021-04-30-Preview"
    
    try:
        response = requests.post(
            create_url,
            headers=headers,
            json=index_definition
        )
        
        if response.status_code in [200, 201]:
            print(f"Successfully created basic index: {index_name}")
            print("\nNext steps:")
            print(f"1. Verify this index exists in Azure Portal")
            print(f"2. If successful, try creating the vector-enabled index")
            return response.json()
        else:
            print(f"Error creating basic index: {response.status_code} - {response.text}")
            print("\nTroubleshooting steps:")
            print("1. Check your API key permissions in Azure Portal")
            print("2. Verify network connectivity to Azure Search")
            print("3. Try creating an index through Azure Portal to validate permissions")
            return None
    except Exception as e:
        print(f"Exception during basic index creation: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Create basic Azure Search index as a first step")
    parser.add_argument("--index", default="legal-court-basic-index", help="Name of the index to create")
    parser.add_argument("--recreate", action="store_true", help="Recreate index if it exists")
    
    args = parser.parse_args()
    create_basic_index(args.index, args.recreate)

if __name__ == "__main__":
    main()

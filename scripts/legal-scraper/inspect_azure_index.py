import os
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

import sys

service_endpoint = "https://cpr-rag.search.windows.net"
index_name = "legal-court-rag-index"

search_text = sys.argv[1] if len(sys.argv) > 1 else "Chancery Guide"

credential = DefaultAzureCredential()
client = SearchClient(endpoint=service_endpoint,
                      index_name=index_name,
                      credential=credential)

print(f"Querying index: {index_name}")
try:
    # Search for text
    print(f"Searching for text '{search_text}'")
    results = client.search(search_text=search_text, top=5, select=["id", "sourcefile", "sourcepage"])

    count = 0
    for result in results:
        count += 1
        print(f"ID: {result['id']}")
        print(f"SourceFile: {result['sourcefile']}")
        print(f"SourcePage: {result['sourcepage']}")
        print("-" * 20)
    
    if count == 0:
        print(f"No results found for text '{search_text}'")

except Exception as e:
    print(f"Error: {e}")

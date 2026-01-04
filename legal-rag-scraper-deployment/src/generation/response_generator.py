from azure.search.documents import SearchClient
from azure.search.documents.models import SearchDocument
from typing import List, Dict

class ResponseGenerator:
    def __init__(self, search_client: SearchClient):
        self.search_client = search_client

    def generate_response(self, query: str, court_type: str) -> List[Dict]:
        results = self.search_client.search(query, filter=f"court_type eq '{court_type}'")
        responses = []

        for result in results:
            response = {
                "title": result.get("title"),
                "content": result.get("chunk"),
                "court_type": result.get("court_type"),
                "metadata": result.get("metadata")
            }
            responses.append(response)

        return responses

    def format_response(self, responses: List[Dict]) -> str:
        formatted_responses = []
        for response in responses:
            formatted_responses.append(f"Title: {response['title']}\nContent: {response['content']}\n")
        return "\n".join(formatted_responses)
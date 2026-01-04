from azure.search.documents.indexes.models import SearchIndex
from typing import List, Dict, Any

class Indexer:
    def __init__(self, search_service_client, index_name):
        self.search_service_client = search_service_client
        self.index_name = index_name

    def create_index(self, fields):
        try:
            index = SearchIndex(name=self.index_name, fields=fields)
            result = self.search_service_client.create_or_update_index(index)
            print(f"Index '{result.name}' created.")
            return result
        except Exception as e:
            print(f"Error creating index: {str(e)}")
            raise

    def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Index a list of documents in batches
        
        Args:
            documents: List of document dictionaries to index
        """
        batch = []
        for doc in documents:
            batch.append(doc)
            if len(batch) == 100:  # Azure Search allows a maximum of 100 documents per batch
                try:
                    self.search_service_client.upload_documents(documents=batch)
                    print(f"Indexed batch of {len(batch)} documents")
                except Exception as e:
                    print(f"Error indexing batch: {str(e)}")
                batch = []
        if batch:
            try:
                self.search_service_client.upload_documents(documents=batch)
                print(f"Indexed final batch of {len(batch)} documents")
            except Exception as e:
                print(f"Error indexing final batch: {str(e)}")

    def update_index(self, documents):
        self.index_documents(documents)

    def index_pdf_files(self, pdf_processor):
        pdf_files = pdf_processor.get_pdf_files()
        documents = []
        for pdf_file in pdf_files:
            text = pdf_processor.extract_text(pdf_file)
            metadata = pdf_processor.get_metadata(pdf_file)
            documents.append({
                "title": metadata['title'],
                "content": text,
                "court": metadata['court']
            })
        self.index_documents(documents)

    def index_json_files(self, json_processor):
        """
        Process and index JSON files using the provided processor
        
        Args:
            json_processor: Object with methods to load and process JSON data
        """
        try:
            json_data = json_processor.load_json()
            documents = []
            for item in json_data:
                doc = {
                    "title": item.get('title', ''),
                    "content": item.get('content', ''),
                    "court": item.get('court', 'general'),
                    "document_type": "civil_rules",
                    "chunk_id": item.get('id', f"doc_{len(documents)}"),
                }
                # Add rule-specific fields if available
                if 'rule_reference' in item:
                    doc['rule_reference'] = item['rule_reference']
                if 'rule_category' in item:
                    doc['rule_category'] = item['rule_category']
                
                documents.append(doc)
            
            print(f"Indexing {len(documents)} documents from JSON files")
            self.index_documents(documents)
        except Exception as e:
            print(f"Error in index_json_files: {str(e)}")
            raise
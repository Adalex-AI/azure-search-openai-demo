import asyncio
import os
import logging
from azure.identity.aio import AzureDeveloperCliCredential
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
from load_azd_env import load_azd_env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scripts")

async def add_group_to_all_docs(group_id):
    load_azd_env()
    service_name = os.environ["AZURE_SEARCH_SERVICE"]
    index_name = os.environ["AZURE_SEARCH_INDEX"]
    endpoint = f"https://{service_name}.search.windows.net"
    
    credential = AzureDeveloperCliCredential()
    
    search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
    
    logger.info(f"Adding group {group_id} to all documents in index {index_name}")
    
    async with search_client:
        results = await search_client.search(search_text="*", select=["id", "groups"], top=100000)
        documents_to_merge = []
        async for doc in results:
            groups = doc.get("groups", [])
            if groups is None:
                groups = []
            if group_id not in groups:
                groups.append(group_id)
                documents_to_merge.append({"id": doc["id"], "groups": groups})
        
        if documents_to_merge:
            logger.info(f"Updating {len(documents_to_merge)} documents")
            # Batch updates
            batch_size = 1000
            for i in range(0, len(documents_to_merge), batch_size):
                batch = documents_to_merge[i:i+batch_size]
                await search_client.merge_documents(documents=batch)
                logger.info(f"Merged batch {i//batch_size + 1}")
        else:
            logger.info("No documents needed updating")

if __name__ == "__main__":
    # Civil Procedure Copilot Users Group ID
    GROUP_ID = "36094ff3-5c6d-49ef-b385-fa37118527e3"
    asyncio.run(add_group_to_all_docs(GROUP_ID))

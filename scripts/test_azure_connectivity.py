#!/usr/bin/env python3
"""
Azure Resource Connectivity Test Script
Tests Azure OpenAI and Azure Search endpoints to diagnose backend hang issue.
"""

import os
import sys
import asyncio
from pathlib import Path

# Load environment variables
env_file = Path(__file__).parent.parent / ".azure" / "cpr-rag" / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)
    print(f"✓ Loaded environment from {env_file}\n")
else:
    print(f"✗ Environment file not found: {env_file}")
    sys.exit(1)

# Get Azure configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
AZURE_SEARCH_SERVICE = os.getenv("AZURE_SEARCH_SERVICE")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")

print("=" * 70)
print("AZURE RESOURCE CONNECTIVITY TEST")
print("=" * 70)
print(f"\nConfiguration:")
print(f"  OpenAI Endpoint: {AZURE_OPENAI_ENDPOINT}")
print(f"  ChatGPT Deployment: {AZURE_OPENAI_CHATGPT_DEPLOYMENT}")
print(f"  Search Service: {AZURE_SEARCH_SERVICE}")
print(f"  Search Index: {AZURE_SEARCH_INDEX}")
print(f"  Tenant ID: {AZURE_TENANT_ID}")
print()

async def test_azure_openai():
    """Test Azure OpenAI connectivity and deployment availability"""
    print("-" * 70)
    print("TEST 1: Azure OpenAI Connectivity")
    print("-" * 70)
    
    try:
        from azure.identity.aio import AzureDeveloperCliCredential
        from openai import AsyncAzureOpenAI
        
        print("✓ Imports successful")
        
        # Create credential
        print("→ Creating AzureDeveloperCliCredential...")
        credential = AzureDeveloperCliCredential(tenant_id=AZURE_TENANT_ID)
        print("✓ Credential created")
        
        # Get token
        print("→ Acquiring access token...")
        token = await credential.get_token("https://cognitiveservices.azure.com/.default")
        print(f"✓ Token acquired (expires: {token.expires_on})")
        
        # Create OpenAI client with proper async token provider
        print("→ Creating AsyncAzureOpenAI client...")
        
        async def get_azure_ad_token():
            token = await credential.get_token("https://cognitiveservices.azure.com/.default")
            return token.token
        
        client = AsyncAzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_ad_token_provider=get_azure_ad_token,
            api_version="2024-10-21"
        )
        print("✓ Client created")
        
        # Test simple completion with timeout
        print(f"→ Testing chat completion with deployment: {AZURE_OPENAI_CHATGPT_DEPLOYMENT}")
        print("  (timeout: 30 seconds)")
        
        # GPT-5/reasoning models use max_completion_tokens and don't support temperature=0
        completion_params = {
            "model": AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'test successful' if you can read this."}
            ]
        }
        
        # Configure parameters based on model type
        if "gpt-5" in AZURE_OPENAI_CHATGPT_DEPLOYMENT.lower() or "o1" in AZURE_OPENAI_CHATGPT_DEPLOYMENT.lower():
            print("  (using max_completion_tokens for GPT-5/reasoning model, temperature=1)")
            completion_params["max_completion_tokens"] = 50
            # GPT-5 only supports temperature=1 (default)
        else:
            completion_params["max_tokens"] = 50
            completion_params["temperature"] = 0
        
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(**completion_params),
                timeout=30.0
            )
            
            content = response.choices[0].message.content
            print(f"✓ Response received: {content}")
            print(f"  Model: {response.model}")
            print(f"  Tokens: {response.usage.total_tokens if response.usage else 'N/A'}")
            print("\n✅ AZURE OPENAI TEST PASSED\n")
            return True
            
        except asyncio.TimeoutError:
            print("✗ TIMEOUT: OpenAI API call took longer than 30 seconds")
            print("  Possible causes:")
            print("    - Model deployment offline or provisioning")
            print("    - Network connectivity issues")
            print("    - Rate limiting or quota exhaustion")
            print("\n❌ AZURE OPENAI TEST FAILED (TIMEOUT)\n")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n❌ AZURE OPENAI TEST FAILED\n")
        return False

async def test_azure_search():
    """Test Azure Search connectivity and index availability"""
    print("-" * 70)
    print("TEST 2: Azure Search Connectivity")
    print("-" * 70)
    
    try:
        from azure.identity.aio import AzureDeveloperCliCredential
        from azure.search.documents.aio import SearchClient
        
        print("✓ Imports successful")
        
        # Create credential
        print("→ Creating AzureDeveloperCliCredential...")
        credential = AzureDeveloperCliCredential(tenant_id=AZURE_TENANT_ID)
        print("✓ Credential created")
        
        # Create Search client
        search_endpoint = f"https://{AZURE_SEARCH_SERVICE}.search.windows.net"
        print(f"→ Creating SearchClient for {search_endpoint}...")
        
        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=AZURE_SEARCH_INDEX,
            credential=credential
        )
        print("✓ Client created")
        
        # Test simple search with timeout
        print(f"→ Testing search query on index: {AZURE_SEARCH_INDEX}")
        print("  Query: 'CPR Part 31'")
        print("  (timeout: 30 seconds)")
        
        try:
            results = await asyncio.wait_for(
                search_client.search(
                    search_text="CPR Part 31",
                    top=3,
                    select=["id", "content", "sourcepage"]
                ),
                timeout=30.0
            )
            
            count = 0
            async for doc in results:
                count += 1
                if count <= 3:
                    content_preview = doc.get("content", "")[:100] if doc.get("content") else "N/A"
                    print(f"  Result {count}: {doc.get('id')} - {content_preview}...")
            
            print(f"✓ Search completed: {count} results returned")
            print("\n✅ AZURE SEARCH TEST PASSED\n")
            return True
            
        except asyncio.TimeoutError:
            print("✗ TIMEOUT: Search API call took longer than 30 seconds")
            print("  Possible causes:")
            print("    - Search service overloaded or offline")
            print("    - Index not ready or corrupted")
            print("    - Network connectivity issues")
            print("\n❌ AZURE SEARCH TEST FAILED (TIMEOUT)\n")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n❌ AZURE SEARCH TEST FAILED\n")
        return False

async def test_embedding_generation():
    """Test embedding generation (used in vector search)"""
    print("-" * 70)
    print("TEST 3: Embedding Generation (Vector Search)")
    print("-" * 70)
    
    AZURE_OPENAI_EMB_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT")
    AZURE_OPENAI_EMB_MODEL_NAME = os.getenv("AZURE_OPENAI_EMB_MODEL_NAME", "text-embedding-3-large")
    
    if not AZURE_OPENAI_EMB_DEPLOYMENT:
        print("⚠ SKIPPED: No embedding deployment configured")
        print("  (AZURE_OPENAI_EMB_DEPLOYMENT not set)\n")
        return None
    
    print(f"  Embedding Deployment: {AZURE_OPENAI_EMB_DEPLOYMENT}")
    print(f"  Embedding Model: {AZURE_OPENAI_EMB_MODEL_NAME}")
    
    try:
        from azure.identity.aio import AzureDeveloperCliCredential
        from openai import AsyncAzureOpenAI
        
        credential = AzureDeveloperCliCredential(tenant_id=AZURE_TENANT_ID)
        
        async def get_azure_ad_token():
            token = await credential.get_token("https://cognitiveservices.azure.com/.default")
            return token.token
        
        client = AsyncAzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_ad_token_provider=get_azure_ad_token,
            api_version="2024-10-21"
        )
        
        print("→ Generating embedding for test query...")
        print("  (timeout: 30 seconds)")
        
        try:
            response = await asyncio.wait_for(
                client.embeddings.create(
                    model=AZURE_OPENAI_EMB_DEPLOYMENT,
                    input="test query for embedding"
                ),
                timeout=30.0
            )
            
            embedding = response.data[0].embedding
            print(f"✓ Embedding generated: {len(embedding)} dimensions")
            print(f"  Model: {response.model}")
            print(f"  Sample values: {embedding[:5]}...")
            print("\n✅ EMBEDDING TEST PASSED\n")
            return True
            
        except asyncio.TimeoutError:
            print("✗ TIMEOUT: Embedding API call took longer than 30 seconds")
            print("\n❌ EMBEDDING TEST FAILED (TIMEOUT)\n")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        print("\n❌ EMBEDDING TEST FAILED\n")
        return False

async def main():
    print("\nRunning connectivity tests...\n")
    
    results = {
        "openai": await test_azure_openai(),
        "search": await test_azure_search(),
        "embedding": await test_embedding_generation()
    }
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Azure OpenAI:    {'✅ PASS' if results['openai'] else '❌ FAIL'}")
    print(f"Azure Search:    {'✅ PASS' if results['search'] else '❌ FAIL'}")
    print(f"Embedding:       {'✅ PASS' if results['embedding'] else ('⚠ SKIP' if results['embedding'] is None else '❌ FAIL')}")
    print()
    
    if all(v in [True, None] for v in results.values()):
        print("✅ All tests passed! Azure resources are accessible.")
        print("\nBackend hang is likely caused by:")
        print("  1. Query/prompt complexity causing long processing time")
        print("  2. Large search results overwhelming the response generation")
        print("  3. Backend code logic issue (not Azure connectivity)")
        print("\nNext steps:")
        print("  - Add detailed logging to chatreadretrieveread.py")
        print("  - Test with simpler queries")
        print("  - Check backend logs for internal errors")
    else:
        print("❌ Some tests failed. Fix Azure connectivity issues first.")
        print("\nTroubleshooting:")
        print("  - Check Azure Portal for service health")
        print("  - Verify deployments exist and are online")
        print("  - Check quota and rate limits")
        print("  - Verify network connectivity (VPN, firewall)")
        print("  - Re-authenticate: azd auth login --use-device-code")

if __name__ == "__main__":
    asyncio.run(main())

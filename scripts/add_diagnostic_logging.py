#!/usr/bin/env python3
"""
Backend Diagnostic Logging Patch
Adds detailed logging to chatreadretrieveread.py to identify exact hanging point.
"""

import sys
from pathlib import Path

backend_file = Path(__file__).parent.parent / "app" / "backend" / "approaches" / "chatreadretrieveread.py"

if not backend_file.exists():
    print(f"✗ File not found: {backend_file}")
    sys.exit(1)

print("=" * 70)
print("BACKEND DIAGNOSTIC LOGGING PATCHER")
print("=" * 70)
print(f"\nTarget file: {backend_file}\n")

# Read current content
with open(backend_file, 'r') as f:
    content = f.read()

# Check if already patched
if "DIAGNOSTIC_LOG_START" in content:
    print("⚠ File already patched with diagnostic logging")
    print("\nTo remove patch, run:")
    print("  git checkout app/backend/approaches/chatreadretrieveread.py")
    sys.exit(0)

# Patch 1: Add logging at start of run_until_final_call
patch1_search = """    async def run_until_final_call(
        self,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        auth_claims: dict[str, Any],
        should_stream: bool = False,
    ) -> tuple[ExtraInfo, Union[Awaitable[ChatCompletion], Awaitable[AsyncStream[ChatCompletionChunk]]]]:
        use_agentic_retrieval = True if overrides.get("use_agentic_retrieval") else False
        original_user_query = messages[-1]["content"]"""

patch1_replace = """    async def run_until_final_call(
        self,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        auth_claims: dict[str, Any],
        should_stream: bool = False,
    ) -> tuple[ExtraInfo, Union[Awaitable[ChatCompletion], Awaitable[AsyncStream[ChatCompletionChunk]]]]:
        logging.info("🔍 DIAGNOSTIC_LOG_START: run_until_final_call entered")
        use_agentic_retrieval = True if overrides.get("use_agentic_retrieval") else False
        original_user_query = messages[-1]["content"]
        logging.info(f"🔍 DIAGNOSTIC: use_agentic_retrieval={use_agentic_retrieval}, query='{original_user_query[:100]}...'")"""

# Patch 2: Add logging before retrieval approach
patch2_search = """        if use_agentic_retrieval:
            extra_info = await self.run_agentic_retrieval_approach(messages, overrides, auth_claims)
        else:
            extra_info = await self.run_search_approach(messages, overrides, auth_claims)"""

patch2_replace = """        if use_agentic_retrieval:
            logging.info("🔍 DIAGNOSTIC: Calling run_agentic_retrieval_approach...")
            extra_info = await self.run_agentic_retrieval_approach(messages, overrides, auth_claims)
            logging.info("🔍 DIAGNOSTIC: run_agentic_retrieval_approach completed")
        else:
            logging.info("🔍 DIAGNOSTIC: Calling run_search_approach...")
            extra_info = await self.run_search_approach(messages, overrides, auth_claims)
            logging.info("🔍 DIAGNOSTIC: run_search_approach completed")"""

# Patch 3: Add logging in run_search_approach before OpenAI call
patch3_search = """        # STEP 1: Generate an optimized keyword search query based on the chat history and the last question

        chat_completion = cast(
            ChatCompletion,
            await self.create_chat_completion("""

patch3_replace = """        # STEP 1: Generate an optimized keyword search query based on the chat history and the last question

        logging.info("🔍 DIAGNOSTIC: STEP 1 - Calling OpenAI for query rewrite...")
        chat_completion = cast(
            ChatCompletion,
            await self.create_chat_completion("""

# Patch 4: Add logging after OpenAI query rewrite
patch4_search = """        query_text = self.get_search_query(chat_completion, original_user_query)

        # STEP 2: Retrieve relevant documents from the search index with the GPT optimized query"""

patch4_replace = """        query_text = self.get_search_query(chat_completion, original_user_query)
        logging.info(f"🔍 DIAGNOSTIC: STEP 1 completed - optimized query: '{query_text}'")

        # STEP 2: Retrieve relevant documents from the search index with the GPT optimized query"""

# Patch 5: Add logging before search call
patch5_search = """        # Log the search parameters for debugging (remove court detection logging)
        import logging
        logging.info(f"Searching with query: {query_text}, top: {top}, filter: {search_index_filter}")
        
        results = await self.search("""

patch5_replace = """        # Log the search parameters for debugging (remove court detection logging)
        import logging
        logging.info(f"Searching with query: {query_text}, top: {top}, filter: {search_index_filter}")
        
        logging.info("🔍 DIAGNOSTIC: STEP 2 - Calling Azure Search...")
        results = await self.search("""

# Patch 6: Add logging after search
patch6_search = """        # Log the search results for debugging
        logging.info(f"Search returned {len(results)} results")"""

patch6_replace = """        # Log the search results for debugging
        logging.info("🔍 DIAGNOSTIC: STEP 2 completed")
        logging.info(f"Search returned {len(results)} results")"""

# Patch 7: Add logging before final OpenAI completion
patch7_search = """        # Increase token limit to accommodate full content
        response_token_limit = self.get_response_token_limit(self.chatgpt_model, 8192)  # Increased from 4096
        
        chat_coroutine = cast("""

patch7_replace = """        # Increase token limit to accommodate full content
        response_token_limit = self.get_response_token_limit(self.chatgpt_model, 8192)  # Increased from 4096
        
        logging.info(f"🔍 DIAGNOSTIC: STEP 3 - Creating final chat completion (max_tokens={response_token_limit})...")
        chat_coroutine = cast("""

# Patch 8: Add logging at end of run_until_final_call
patch8_search = """        # Store enhanced citations in extra_info for frontend access"""

patch8_replace = """        logging.info("🔍 DIAGNOSTIC_LOG_END: run_until_final_call returning")
        # Store enhanced citations in extra_info for frontend access"""

# Apply patches
patches = [
    (patch1_search, patch1_replace, "Start of run_until_final_call"),
    (patch2_search, patch2_replace, "Before retrieval approach"),
    (patch3_search, patch3_replace, "Before OpenAI query rewrite"),
    (patch4_search, patch4_replace, "After OpenAI query rewrite"),
    (patch5_search, patch5_replace, "Before Azure Search"),
    (patch6_search, patch6_replace, "After Azure Search"),
    (patch7_search, patch7_replace, "Before final OpenAI completion"),
    (patch8_search, patch8_replace, "End of run_until_final_call")
]

patched_content = content
successful_patches = 0

for i, (search, replace, description) in enumerate(patches, 1):
    if search in patched_content:
        patched_content = patched_content.replace(search, replace, 1)
        print(f"✓ Patch {i}: {description}")
        successful_patches += 1
    else:
        print(f"✗ Patch {i}: {description} (search pattern not found)")

print(f"\n{successful_patches}/{len(patches)} patches applied successfully")

if successful_patches > 0:
    # Write patched content
    with open(backend_file, 'w') as f:
        f.write(patched_content)
    
    print(f"\n✅ Diagnostic logging added to {backend_file}")
    print("\nNext steps:")
    print("  1. Restart backend:")
    print("     kill <backend_pid> && source .azure/cpr-rag/.env && export PATH=\"/usr/local/bin:$PATH\" && ./.venv/bin/python -m quart --app app/backend/main:app run --port 50505 --host localhost --reload &")
    print("  2. Test endpoint:")
    print("     curl -X POST http://localhost:50505/chat -H 'Content-Type: application/json' -d '{\"messages\":[{\"content\":\"What is CPR 31?\",\"role\":\"user\"}],\"context\":{\"overrides\":{}}}'")
    print("  3. Watch logs to see where it hangs:")
    print("     Look for last 🔍 DIAGNOSTIC message before hang")
else:
    print("\n❌ No patches applied. File structure may have changed.")
    print("Manual intervention required.")

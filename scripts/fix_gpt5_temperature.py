#!/usr/bin/env python3
"""
GPT-5 Temperature Fix Script
Fixes backend code to handle GPT-5 models that only support temperature=1.
"""

import sys
from pathlib import Path

backend_file = Path(__file__).parent.parent / "app" / "backend" / "approaches" / "chatreadretrieveread.py"

if not backend_file.exists():
    print(f"✗ File not found: {backend_file}")
    sys.exit(1)

print("=" * 70)
print("GPT-5 TEMPERATURE COMPATIBILITY FIX")
print("=" * 70)
print(f"\nTarget file: {backend_file}\n")
print("Issue: GPT-5-nano only supports temperature=1 (default)")
print("Current code passes temperature=0.0 which causes API errors\n")

# Read current content
with open(backend_file, 'r') as f:
    content = f.read()

# Check if already patched
if "GPT5_TEMPERATURE_FIX_APPLIED" in content:
    print("⚠ File already patched for GPT-5 temperature compatibility")
    print("\nTo remove patch, run:")
    print("  git checkout app/backend/approaches/chatreadretrieveread.py")
    sys.exit(0)

# Fix 1: Modify create_chat_completion to handle temperature for GPT-5
fix1_search = """    def create_chat_completion(
        self,
        chatgpt_deployment: Optional[str],
        chatgpt_model: str,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        response_token_limit: int,
        should_stream: bool = False,
        tools: Optional[list[ChatCompletionToolParam]] = None,
        temperature: Optional[float] = None,
        n: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
    ) -> Union[Awaitable[ChatCompletion], Awaitable[AsyncStream[ChatCompletionChunk]]]:
        if chatgpt_model in self.GPT_REASONING_MODELS:
            params: dict[str, Any] = {
                # Increase max_completion_tokens to handle full content
                "max_completion_tokens": max(response_token_limit, 16384)  # Increased from 8192
            }

            # Adjust parameters for reasoning models
            supported_features = self.GPT_REASONING_MODELS[chatgpt_model]
            if supported_features.streaming and should_stream:
                params["stream"] = True
                params["stream_options"] = {"include_usage": True}
            params["reasoning_effort"] = reasoning_effort or overrides.get("reasoning_effort") or self.reasoning_effort

        else:
            # Include parameters that may not be supported for reasoning models
            params = {
                "max_tokens": max(response_token_limit, 8192),  # Increased from 4096
                "temperature": temperature or overrides.get("temperature", 0.3),
            }
            if should_stream:
                params["stream"] = True
                params["stream_options"] = {"include_usage": True}"""

fix1_replace = """    def create_chat_completion(
        self,
        chatgpt_deployment: Optional[str],
        chatgpt_model: str,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        response_token_limit: int,
        should_stream: bool = False,
        tools: Optional[list[ChatCompletionToolParam]] = None,
        temperature: Optional[float] = None,
        n: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
    ) -> Union[Awaitable[ChatCompletion], Awaitable[AsyncStream[ChatCompletionChunk]]]:
        # GPT5_TEMPERATURE_FIX_APPLIED: GPT-5 models only support temperature=1 (default)
        if chatgpt_model in self.GPT_REASONING_MODELS:
            params: dict[str, Any] = {
                # Increase max_completion_tokens to handle full content
                "max_completion_tokens": max(response_token_limit, 16384)  # Increased from 8192
            }

            # Adjust parameters for reasoning models
            supported_features = self.GPT_REASONING_MODELS[chatgpt_model]
            if supported_features.streaming and should_stream:
                params["stream"] = True
                params["stream_options"] = {"include_usage": True}
            params["reasoning_effort"] = reasoning_effort or overrides.get("reasoning_effort") or self.reasoning_effort
            
            # GPT-5 models only support temperature=1, don't override it
            # Ignore any temperature parameter passed in

        else:
            # Include parameters that may not be supported for reasoning models
            params = {
                "max_tokens": max(response_token_limit, 8192),  # Increased from 4096
                "temperature": temperature or overrides.get("temperature", 0.3),
            }
            if should_stream:
                params["stream"] = True
                params["stream_options"] = {"include_usage": True}"""

# Apply fix
if fix1_search in content:
    content = content.replace(fix1_search, fix1_replace, 1)
    print("✓ Fixed: create_chat_completion now skips temperature for GPT-5 models")
    
    # Write fixed content
    with open(backend_file, 'w') as f:
        f.write(content)
    
    print(f"\n✅ GPT-5 temperature compatibility fix applied to {backend_file}")
    print("\nChanges:")
    print("  - GPT-5 models now use default temperature=1 (API requirement)")
    print("  - temperature parameter ignored for GPT-5/reasoning models")
    print("  - Non-GPT-5 models still respect temperature parameter")
    print("\nNext steps:")
    print("  1. Kill backend process:")
    print("     kill $(lsof -ti:50505)")
    print("  2. Restart backend:")
    print("     source .azure/cpr-rag/.env && export PATH=\"/usr/local/bin:$PATH\" && ./.venv/bin/python -m quart --app app/backend/main:app run --port 50505 --host localhost --reload &")
    print("  3. Test endpoint:")
    print("     curl -X POST http://localhost:50505/chat -H 'Content-Type: application/json' -d '{\"messages\":[{\"content\":\"What is CPR 31?\",\"role\":\"user\"}],\"context\":{\"overrides\":{}}}'")
else:
    print("✗ Fix pattern not found. File structure may have changed.")
    print("Manual fix required:")
    print("  1. Open app/backend/approaches/chatreadretrieveread.py")
    print("  2. Find create_chat_completion method")
    print("  3. In the 'if chatgpt_model in self.GPT_REASONING_MODELS' block:")
    print("     - Remove or comment out temperature parameter")
    print("     - GPT-5 only supports temperature=1 (default)")

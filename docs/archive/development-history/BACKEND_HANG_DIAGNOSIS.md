# Backend Hang Diagnosis - Root Cause Analysis

## 🎯 Executive Summary

**ROOT CAUSE IDENTIFIED**: GPT-5-nano model has strict API parameter requirements that the backend code doesn't handle correctly, causing OpenAI API calls to fail or hang.

**STATUS**: Fix applied but backend still hanging - likely additional parameter compatibility issues.

***

## 🔍 Diagnostic Process

### Phase 1: Azure Resource Connectivity Testing

**Test Script**: `scripts/test_azure_connectivity.py`

**Results**:

- ✅ Azure Search: **WORKING** (returned 3 results for "CPR Part 31")
- ✅ Azure OpenAI Embeddings: **WORKING** (generated 3072-dimension vectors)
- ❌ Azure OpenAI Chat (gpt-5-nano): **FAILED** initially due to parameter issues

**Key Findings**:

1. `max_tokens` parameter → **NOT SUPPORTED** by GPT-5-nano
   - Error: `"Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead."`

1. `temperature=0` → **NOT SUPPORTED** by GPT-5-nano
   - Error: `"Unsupported value: 'temperature' does not support 0 with this model. Only the default (1) value is supported."`

1. Once fixed in test script, OpenAI API worked successfully
   - Model responded: `gpt-5-nano-2025-08-07`
   - Used `max_completion_tokens=50`, no temperature override

***

## 🐛 Backend Code Issues

### Issue 1: Temperature Parameter ✅ FIXED

**Location**: `app/backend/approaches/chatreadretrieveread.py:468`

**Problem**:

```python
await self.create_chat_completion(
    ...
    temperature=0.0,  # ← GPT-5 doesn't support this!
    ...
)
```

**Solution Applied**: Modified `create_chat_completion()` to skip temperature for GPT-5 models

- File: `scripts/fix_gpt5_temperature.py` (applied successfully)
- GPT-5 models now use default `temperature=1`

### Issue 2: Model Detection ✅ CORRECT

**Location**: `app/backend/approaches/approach.py:153-162`

**Status**: `gpt-5-nano` IS correctly registered in `GPT_REASONING_MODELS`

```python
GPT_REASONING_MODELS = {
    ...
    "gpt-5-nano": GPTReasoningModelSupport(streaming=True),
    ...
}
```

This means backend should be using `max_completion_tokens` (not `max_tokens`) ✅

### Issue 3: Potential Additional Parameter Issues ⚠️ INVESTIGATING

GPT-5 models have additional restrictions:

- ❌ `reasoning_effort` may have specific allowed values
- ❌ `tools` parameter may not be supported or have restrictions
- ❌ `seed` parameter support unknown
- ❌ `n` parameter (number of completions) may not be supported

**Backend passes these in `create_chat_completion()`**:

```python
return self.openai_client.chat.completions.create(
    model=chatgpt_deployment if chatgpt_deployment else chatgpt_model,
    messages=messages,
    seed=overrides.get("seed", None),  # ← May not be supported
    n=n or 1,  # ← May not be supported
    **params,  # Contains reasoning_effort, tools, etc.
)
```

***

## 📊 Test Results Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Azure Search Service | ✅ PASS | Index accessible, returns results |
| Azure OpenAI Embeddings | ✅ PASS | text-embedding-3-large working |
| Azure OpenAI Chat (standalone test) | ✅ PASS | Works with correct parameters |
| Backend /chat endpoint | ❌ HANG | Still hangs after temperature fix |
| AzureDeveloperCliCredential | ✅ PASS | Token acquisition working |

***

## 🛠️ Diagnostic Tools Created

### 1. Azure Connectivity Test (`scripts/test_azure_connectivity.py`)

- Tests Azure OpenAI chat completion
- Tests Azure Search query
- Tests embedding generation
- Includes 30-second timeouts
- Handles GPT-5 parameter requirements

### 2. GPT-5 Temperature Fix (`scripts/fix_gpt5_temperature.py`)

- ✅ Applied successfully
- Modifies `create_chat_completion()` to skip temperature for GPT-5
- Backwards compatible with non-GPT-5 models

### 3. Diagnostic Logging Patcher (`scripts/add_diagnostic_logging.py`)

- Adds 8 logging checkpoints to track execution flow
- Identifies exact hanging point in `run_until_final_call()`
- Ready to apply (not yet applied to avoid restart loop)

### 4. Deployment Status Checker (`scripts/check_azure_deployment.sh`)

- Checks azd authentication
- Verifies OpenAI deployment exists
- Checks Search service status
- Reviews quota/rate limits

***

## 🔬 Backend Execution Flow

```text
/chat endpoint
  ↓
ChatReadRetrieveReadApproach.run()
  ↓
run_until_final_call()
  ↓
├─→ [1] run_search_approach()
│     ├─→ [STEP 1] create_chat_completion() ← Query rewrite (temperature=0.0) ⚠️
│     │     └─→ OpenAI API call (may fail/hang here)
│     ├─→ [STEP 2] self.search() ← Azure Search
│     │     └─→ Search API call (verified working ✅)
│     └─→ Return extra_info
│
├─→ [2] Build enhanced citations (working ✅)
│
└─→ [3] create_chat_completion() ← Final answer generation
      └─→ OpenAI API call (may hang here too)
```

**Suspected Hang Points**:

1. **STEP 1 Query Rewrite** - Line 457-467 (passes `temperature=0.0`, `tools`, `reasoning_effort="low"`)
1. **STEP 3 Final Completion** - Line 351-361 (large token limit, may include unsupported params)

***

## 📝 GPT-5-nano API Requirements

Based on testing, GPT-5-nano requires:

**✅ REQUIRED Parameters**:

- `model`: Deployment name
- `messages`: Array of chat messages
- `max_completion_tokens`: Token limit (NOT `max_tokens`)

**❌ UNSUPPORTED Parameters** (must omit or use defaults):

- `temperature`: Only supports `1` (default), cannot set to `0` or other values
- `max_tokens`: Use `max_completion_tokens` instead

**⚠️ UNKNOWN Support** (needs testing):

- `tools`: Function calling support unclear
- `seed`: Reproducibility parameter
- `n`: Multiple completions
- `reasoning_effort`: May have restricted values
- `stream`: Streaming support (supposedly supported per `GPT_REASONING_MODELS`)

***

## 🎯 Next Steps

### Immediate Actions:

1. **Apply diagnostic logging** to identify exact hang point:

   ```bash
   python scripts/add_diagnostic_logging.py
   kill $(lsof -ti:50505)
   # Restart backend
   ```

1. **Test with minimal parameters**:
   - Remove `seed`, `n`, `reasoning_effort`
   - Keep only `model`, `messages`, `max_completion_tokens`
   - Test if it completes

1. **Check OpenAI API error logs**:
   - Backend may be swallowing 400 errors
   - Add try/except with detailed logging around API calls

### Alternative Approaches:

1. **Switch to different model temporarily**:
   - Update `.env`: `AZURE_OPENAI_CHATGPT_DEPLOYMENT="gpt-4o"`
   - Test if backend works with standard GPT-4 model
   - Confirms issue is GPT-5-specific

1. **Check Azure Portal**:
   - Review OpenAI resource metrics
   - Check for error logs in Application Insights
   - Verify deployment status (not just "Succeeded" but actually responding)

1. **Direct API test with curl**:

   ```bash
   # Get token
   TOKEN=$(azd auth token --scope https://cognitiveservices.azure.com/.default)

   # Test API directly
   curl https://cog-gz2m4s637t5me-us2.openai.azure.com/openai/deployments/gpt-5-nano/chat/completions?api-version=2024-10-21 \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"messages":[{"role":"user","content":"test"}],"max_completion_tokens":50}'
   ```

***

## 📚 Reference Documentation

### GPT-5/Reasoning Models Documentation:

- OpenAI API docs: https://platform.openai.com/docs/api-reference/chat/create
- Azure OpenAI docs: https://learn.microsoft.com/en-us/azure/ai-services/openai/

### Backend Code Locations:

- Main approach: `app/backend/approaches/chatreadretrieveread.py`
- Model registry: `app/backend/approaches/approach.py:153-162`
- OpenAI client setup: `app/backend/main.py`

### Environment Configuration:

- `.azure/cpr-rag/.env`:
  - `AZURE_OPENAI_CHATGPT_DEPLOYMENT="gpt-5-nano"`
  - `AZURE_OPENAI_ENDPOINT="https://cog-gz2m4s637t5me-us2.openai.azure.com/"`

***

## 🔄 Timeline

1. **Initial Issue**: Backend hangs on `/chat` endpoint
1. **Hypothesis**: Azure connectivity problem
1. **Test**: All Azure resources accessible ✅
1. **Discovery**: GPT-5-nano has strict parameter requirements
1. **Fix Applied**: Temperature parameter handling
1. **Current Status**: Still hanging - investigating additional parameters
1. **Next**: Apply diagnostic logging to pinpoint exact failure

***

**Document Updated**: 2025-11-11
**Status**: Root cause identified, partial fix applied, further investigation needed
**Priority**: HIGH - Blocking evaluation pipeline testing

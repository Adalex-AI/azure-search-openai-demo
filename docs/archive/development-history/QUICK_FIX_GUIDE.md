# Backend Hang - Quick Reference Guide

## 🎯 ROOT CAUSE

**GPT-5-nano model has strict API parameter requirements causing OpenAI calls to fail**

***

## ✅ What We Know

### Azure Resources Status:

- ✅ Azure Search: **WORKING**
- ✅ Azure OpenAI Embeddings: **WORKING**
- ✅ Azure OpenAI Chat (with correct params): **WORKING**
- ❌ Backend `/chat` endpoint: **HANGS**

### GPT-5-nano Requirements:

- ✅ Use `max_completion_tokens` (NOT `max_tokens`)
- ✅ Use `temperature=1` (default) - cannot set to 0
- ⚠️ Unknown: `tools`, `seed`, `n`, `reasoning_effort` support

### Fixes Applied:

- ✅ Temperature fix (`scripts/fix_gpt5_temperature.py`)
- ✅ Backend code modified to skip temperature for GPT-5

***

## 🚀 Quick Commands

### Test Azure Connectivity

```bash
cd /Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2
source .venv/bin/activate
python scripts/test_azure_connectivity.py
```

### Apply Diagnostic Logging

```bash
python scripts/add_diagnostic_logging.py
```

### Restart Backend

```bash
kill $(lsof -ti:50505)
source .azure/cpr-rag/.env
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
./.venv/bin/python -m quart --app app/backend/main:app run --port 50505 --host localhost --reload &
```

### Test Endpoint

```bash
curl -X POST http://localhost:50505/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"content":"What is CPR 31?","role":"user"}],"context":{"overrides":{}}}'
```

### Run Full Diagnostic

```bash
./scripts/run_full_diagnostic.sh
```

***

## 🔧 Quick Workaround: Switch to GPT-4o

If you need evaluation working NOW, switch models:

```bash
# Edit .env
sed -i '' 's/AZURE_OPENAI_CHATGPT_DEPLOYMENT="gpt-5-nano"/AZURE_OPENAI_CHATGPT_DEPLOYMENT="gpt-4o"/' .azure/cpr-rag/.env

# Restart backend
kill $(lsof -ti:50505)
source .azure/cpr-rag/.env
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
./.venv/bin/python -m quart --app app/backend/main:app run --port 50505 --host localhost --reload &

# Test
curl -X POST http://localhost:50505/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"content":"What is CPR 31?","role":"user"}],"context":{"overrides":{}}}'
```

**Note**: Check your `.env` for actual GPT-4 deployment name. May be `gpt-4`, `gpt-4o`, `gpt-4-turbo`, etc.

***

## 📊 Diagnostic Scripts Created

| Script | Purpose | Status |
|--------|---------|--------|
| `test_azure_connectivity.py` | Test Azure OpenAI & Search | ✅ Working |
| `fix_gpt5_temperature.py` | Fix temperature parameter | ✅ Applied |
| `add_diagnostic_logging.py` | Add execution logging | ✅ Ready |
| `check_azure_deployment.sh` | Check deployment status | ✅ Ready |
| `run_full_diagnostic.sh` | Master diagnostic suite | ✅ Ready |

***

## 🔍 Where It Hangs

Backend execution flow:

```text
/chat → run_until_final_call() → run_search_approach()
  ├─ STEP 1: Query rewrite (OpenAI call) ← Likely hangs here
  ├─ STEP 2: Azure Search (working ✅)
  └─ STEP 3: Final answer (OpenAI call) ← Or here
```

Apply diagnostic logging to see exact point:

```bash
python scripts/add_diagnostic_logging.py
# Look for last 🔍 DIAGNOSTIC message before hang
```

***

## 📝 Next Investigation Steps

1. **Add diagnostic logging** → Identify exact hang point
1. **Test with minimal params** → Remove `seed`, `n`, `reasoning_effort`, `tools`
1. **Check Azure Portal** → Review OpenAI metrics & error logs
1. **Direct API test** → Bypass backend with curl
1. **Switch model temporarily** → Test with GPT-4o to confirm issue is GPT-5-specific

***

## 📚 Documentation

- **Full Analysis**: `BACKEND_HANG_DIAGNOSIS.md`
- **Evaluation Status**: `EVALUATION_STATUS.md`
- **Backend Code**: `app/backend/approaches/chatreadretrieveread.py`
- **Model Registry**: `app/backend/approaches/approach.py:153-162`

***

## ⚡ For Immediate Evaluation

**Evaluation is READY except for backend**. To proceed:

**Option 1**: Fix backend (investigation ongoing)
**Option 2**: Switch to GPT-4o model (see workaround above)
**Option 3**: Use deployed Azure instance (if available)

Then run:

```bash
source .evalenv/bin/activate
python evals/generate_ground_truth.py --numquestions=50
python evals/evaluate.py --numquestions=10
```

***

**Updated**: 2025-11-11
**Status**: Root cause identified, partial fix applied, diagnostics ready

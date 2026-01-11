# GPT-5-nano Issue - Solution: Switch to gpt-4.1-mini

## 🎯 Finding

**The original azure-search-openai-demo repo uses `gpt-4.1-mini` as the recommended chat model**, NOT gpt-5-nano.

From the README:
> "It uses Azure OpenAI Service to access a GPT model (gpt-4.1-mini)"

## 📊 Your Current Setup

You have **TWO** models deployed:

1. ❌ `gpt-5-nano` (main chatgpt deployment) - **INCOMPATIBLE** with backend code
1. ✅ `gpt-4.1-mini` (searchagent deployment) - **COMPATIBLE** and recommended

## 🔧 Quick Fix: Switch to gpt-4.1-mini

### Option 1: Update Environment Variable (Recommended)

```bash
cd /Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2

# Update .env to use gpt-4.1-mini deployment
sed -i '' 's/AZURE_OPENAI_CHATGPT_DEPLOYMENT="gpt-5-nano"/AZURE_OPENAI_CHATGPT_DEPLOYMENT="searchagent"/' .azure/cpr-rag/.env
sed -i '' 's/AZURE_OPENAI_CHATGPT_MODEL="gpt-5-nano"/AZURE_OPENAI_CHATGPT_MODEL="gpt-4.1-mini"/' .azure/cpr-rag/.env

# Restart backend
kill $(lsof -ti:50505) 2>/dev/null
source .azure/cpr-rag/.env
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
./.venv/bin/python -m quart --app app/backend/main:app run --port 50505 --host localhost --reload &

# Test
sleep 5
curl -X POST http://localhost:50505/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"content":"What is CPR 31?","role":"user"}],"context":{"overrides":{}}}'
```

### Option 2: Use azd to Update

```bash
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT "searchagent"
azd env set AZURE_OPENAI_CHATGPT_MODEL "gpt-4.1-mini"
```

## 📋 Why gpt-5-nano Failed

GPT-5 models (including gpt-5-nano) have **different API requirements** than GPT-4:

| Parameter | GPT-4 | GPT-5-nano |
|-----------|-------|------------|
| `max_tokens` | ✅ Supported | ❌ Use `max_completion_tokens` |
| `temperature=0` | ✅ Supported | ❌ Only supports `1` (default) |
| `tools` (function calling) | ✅ Supported | ⚠️ Unknown |
| `seed` | ✅ Supported | ⚠️ Unknown |
| Backend compatibility | ✅ Full | ❌ Requires code changes |

The backend code was written for GPT-4 models and doesn't handle GPT-5's restrictions.

## ✅ Why gpt-4.1-mini Works

- **Fully compatible** with existing backend code
- **Recommended by the original repo**
- **Already deployed** in your environment
- **No code changes needed**
- **Works with evaluation pipeline**

## 🚀 After Switching

Once you switch to gpt-4.1-mini:

1. **Backend should work immediately** ✅
1. **Run evaluation**:

```bash
   source .evalenv/bin/activate
   python evals/generate_ground_truth.py --numquestions=50
   python evals/evaluate.py --numquestions=10
   ```

1. **Review results** in `evals/results/`

## 📝 For Future: Using GPT-5-nano

If you want to use GPT-5-nano in the future, the backend needs these code changes:

1. ✅ **Already applied**: Temperature fix (skip temperature parameter)
1. ⚠️ **Still needed**: Remove/conditionally handle `tools` parameter
1. ⚠️ **Still needed**: Remove/conditionally handle `seed` parameter
1. ⚠️ **Still needed**: Test `reasoning_effort` parameter support
1. ⚠️ **Still needed**: Verify all API calls work with GPT-5 constraints

See `BACKEND_HANG_DIAGNOSIS.md` for complete analysis.

## 🎓 Evaluation Model Recommendation

For **evaluation**, the repo recommends:

- **Model**: `gpt-4o` (not gpt-5)
- **Version**: `2024-08-06`
- **Purpose**: Evaluating groundedness, relevance, etc.

To set up evaluation model:

```bash
azd env set USE_EVAL true
azd env set AZURE_OPENAI_EVAL_DEPLOYMENT_CAPACITY 100
azd provision
```

This will create a separate `gpt-4o` deployment specifically for running evaluations.

***

**Bottom Line**: Switch from `gpt-5-nano` to `gpt-4.1-mini` (searchagent deployment) and everything should work as designed.

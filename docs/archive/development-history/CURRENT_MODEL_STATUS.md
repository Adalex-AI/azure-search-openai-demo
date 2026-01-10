# Current Model Configuration Status

**Date**: 2025-11-17  
**Status**: ✅ READY FOR EVALUATION

***

## Active Configuration

### Chat Model
```
Model: GPT-4.1-mini
Deployment: searchagent
Version: 2025-04-14 (gpt-4.1-mini-2025-04-14)
API Version: 2024-12-01-preview
Status: ✅ Tested and Working
```

### Evaluation Model
```
Model: GPT-4.1-mini  
Deployment: searchagent
Same as chat model (recommended)
```

### Embedding Model
```
Model: text-embedding-3-large
Dimensions: 3072
Status: ✅ Tested and Working
```

***

## Test Results

### Azure Connectivity Test
All services passing:
- ✅ Azure OpenAI (GPT-4.1-mini): Response received
- ✅ Azure Search: 3 results returned for "CPR Part 31"
- ✅ Embeddings: 3072-dimension vectors generated

### Backend Chat Test
```bash
curl -X POST http://localhost:50505/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"content":"What is CPR 31?","role":"user"}],"context":{"overrides":{}}}'
```
**Result**: ✅ Successful response with citations

### Evaluation Environment
```bash
source .evalenv/bin/activate
python -c "import azure.ai.evaluation"
```
**Result**: ✅ Package installed and ready

***

## Why GPT-4.1-mini for Evaluation?

1. **Stable Parameters**: Full support for temperature, max_tokens, etc.
2. **Cost-Effective**: Lower token costs for running evaluations
3. **Proven Reliability**: All evaluation scripts tested and working
4. **Faster Responses**: No reasoning overhead

***

## When to Switch to GPT-5-nano

Consider switching to GPT-5-nano only when:
- You need extended reasoning capabilities
- Complex legal queries require multi-step deduction
- You've read and understood [MODEL_SWITCHING_GUIDE.md](./MODEL_SWITCHING_GUIDE.md)
- You're prepared for potential compatibility issues (see [BACKEND_HANG_DIAGNOSIS.md](./BACKEND_HANG_DIAGNOSIS.md))

**Note**: GPT-5-nano requires special parameter handling:
- Use `max_completion_tokens` instead of `max_tokens`
- Temperature must be `1` (cannot be set to `0`)
- Some parameters (`seed`, `n`, `tools`) may not be fully supported

***

## Running Evaluation Now

The system is ready for evaluation with GPT-4.1-mini:

### 1. Ensure Backend is Running
```bash
# Check backend status
curl -I http://localhost:50505

# If not running, start it:
cd /Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2
./app/start.sh
```

### 2. Generate Ground Truth (if needed)
```bash
source .evalenv/bin/activate
python evals/generate_ground_truth.py --numquestions=50
```

### 3. Run Evaluation
```bash
source .evalenv/bin/activate
python evals/evaluate.py --numquestions=10
```

### 4. View Results
```bash
# Results saved in:
ls -lh evals/results/
```

***

## Quick Health Check Commands

```bash
# Test Azure connectivity
source .venv/bin/activate
python scripts/test_azure_connectivity.py

# Test backend endpoint
curl -X POST http://localhost:50505/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"content":"test","role":"user"}],"context":{"overrides":{}}}'

# Check current model in use
grep "AZURE_OPENAI_CHATGPT_MODEL" .azure/cpr-rag/.env
```

***

## Configuration Files

- **Environment**: `.azure/cpr-rag/.env`
- **Evaluation Config**: `evals/evaluate_config.json`
- **Test Questions**: `evals/practical_test_questions.json`
- **Ground Truth**: `evals/ground_truth.jsonl`

***

## Related Documentation

- [Model Switching Guide](./MODEL_SWITCHING_GUIDE.md) - How to switch to GPT-5-nano
- [Backend Hang Diagnosis](./BACKEND_HANG_DIAGNOSIS.md) - GPT-5-nano compatibility issues
- [Evaluation Status](./EVALUATION_STATUS.md) - Evaluation setup details
- [Upstream Reasoning Docs](./docs/reasoning.md) - Original GPT-5 guidance

***

**Summary**: System is currently configured with GPT-4.1-mini and fully operational. All Azure services tested and responding correctly. Ready to run evaluation.

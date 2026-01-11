# Model Switching Guide

This guide explains how to switch between GPT-4.1-mini (recommended for evaluation) and GPT-5-nano (reasoning model).

## Current Configuration

Your environment is currently configured to use **GPT-4.1-mini** for evaluation purposes.

```bash
# Current settings in .azure/cpr-rag/.env
AZURE_OPENAI_CHATGPT_MODEL="gpt-4.1-mini"
AZURE_OPENAI_CHATGPT_DEPLOYMENT="searchagent"
AZURE_OPENAI_EVAL_MODEL="gpt-4.1-mini"
```

## Why Keep GPT-4.1-mini for Evaluation?

1. **Stability**: GPT-4.1-mini has predictable parameter support (temperature, max_tokens, etc.)
1. **Cost-effective**: Lower token costs for running evaluations
1. **Proven compatibility**: All evaluation scripts and metrics work reliably
1. **Faster responses**: No additional reasoning overhead

## When to Use GPT-5-nano

Use GPT-5-nano when you need:

- Extended reasoning capabilities for complex legal queries
- Deeper analysis of CPR rules and court procedures
- Multi-step logical deduction in responses

## Switching to GPT-5-nano

### Prerequisites

1. Ensure you have a GPT-5-nano deployment in Azure OpenAI
1. Check the [supported regions](https://learn.microsoft.com/azure/ai-services/openai/concepts/models#standard-deployment-model-availability)
1. Review the [GPT-5-nano constraints](#gpt-5-nano-constraints) below

### Steps to Switch

```bash
# Navigate to project directory
cd /Users/HasithB/Downloads/PROJECTS/azure-search-openai-demo-2

# Set GPT-5-nano configuration
azd env set AZURE_OPENAI_CHATGPT_MODEL gpt-5-nano
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT gpt-5-nano
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT_VERSION 2025-08-07
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT_SKU GlobalStandard
azd env set AZURE_OPENAI_API_VERSION 2025-04-01-preview

# Optional: Set reasoning effort (minimal, low, medium, high)
azd env set AZURE_OPENAI_REASONING_EFFORT low

# Deploy changes
azd up
```

### Testing After Switch

```bash
# Activate virtual environment
source .venv/bin/activate

# Test connectivity with new model
python scripts/test_azure_connectivity.py

# Start the application
./app/start.sh

# Test with a simple query
curl -X POST http://localhost:50505/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"content":"What is CPR 31?","role":"user"}],"context":{"overrides":{}}}'
```

## Switching Back to GPT-4.1-mini

```bash
# Set GPT-4.1-mini configuration
azd env set AZURE_OPENAI_CHATGPT_MODEL gpt-4.1-mini
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT searchagent
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT_VERSION 2025-04-14
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT_SKU GlobalStandard
azd env set AZURE_OPENAI_API_VERSION 2024-12-01-preview

# Deploy changes
azd up
```

## GPT-5-nano Constraints

Based on testing and [diagnosis documentation](./BACKEND_HANG_DIAGNOSIS.md), GPT-5-nano has strict API requirements:

### Supported Parameters

- `model`: Deployment name
- `messages`: Array of chat messages
- `max_completion_tokens`: Token limit (use this, NOT `max_tokens`)
- `temperature`: Only supports `1` (default)
- `reasoning_effort`: `minimal`, `low`, `medium`, `high`

### Unsupported/Restricted Parameters

- ❌ `max_tokens`: Use `max_completion_tokens` instead
- ❌ `temperature`: Cannot set to `0` or other values (only `1` is supported)
- ⚠️ `tools`: Function calling support may be limited
- ⚠️ `seed`: Reproducibility parameter support unclear
- ⚠️ `n`: Multiple completions support unclear

### Backend Compatibility

The codebase includes compatibility code for GPT-5 models in:

- `app/backend/approaches/approach.py`: Model registry with `GPT_REASONING_MODELS`
- `app/backend/approaches/chatreadretrieveread.py`: Parameter handling logic

However, some edge cases may still cause issues. Monitor the backend logs carefully when using GPT-5-nano.

## Evaluation Recommendation

**For evaluation runs, stay on GPT-4.1-mini unless:**

1. You specifically want to test GPT-5-nano's reasoning capabilities
1. You have resolved all backend compatibility issues
1. You have budget for higher token costs

To run evaluation with current GPT-4.1-mini setup:

```bash
# Activate evaluation environment
source .evalenv/bin/activate

# Generate ground truth (if needed)
python evals/generate_ground_truth.py --numquestions=50

# Run evaluation
python evals/evaluate.py --numquestions=10
```

## Troubleshooting

### Backend Hangs with GPT-5-nano

If the backend hangs after switching to GPT-5-nano:

1. **Check parameter compatibility**:

```bash
   python scripts/test_azure_connectivity.py
   ```

1. **Apply diagnostic logging**:

```bash
   python scripts/add_diagnostic_logging.py
   ```

1. **Review logs** for parameter errors or timeouts

1. **Temporary workaround**: Switch back to GPT-4.1-mini

### Deployment Verification

Verify your deployment exists in Azure Portal:

1. Navigate to your Azure OpenAI resource
1. Go to "Deployments" section
1. Confirm the deployment name matches your environment variable
1. Check the deployment status is "Succeeded" and quota is available

## References

- [Original Reasoning Docs](./docs/reasoning.md)
- [Backend Hang Diagnosis](./BACKEND_HANG_DIAGNOSIS.md)
- [Quick Fix Guide](./QUICK_FIX_GUIDE.md)
- [Evaluation Status](./EVALUATION_STATUS.md)

***

**Last Updated**: 2025-11-17
**Current Model**: GPT-4.1-mini (recommended for evaluation)

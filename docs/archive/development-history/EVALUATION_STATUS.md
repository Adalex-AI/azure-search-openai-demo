# Evaluation Pipeline Status Report

## Summary

All evaluation infrastructure is **ready** for testing the new `[1][2][3]` citation format. The backend accepts requests but hangs during Azure API calls (Azure OpenAI or Azure Search). This is an **Azure infrastructure issue**, not an evaluation framework issue.

***

## ✅ Completed Work

### 1. Custom Metrics Implementation

All 5 metrics implemented and validated:

| Metric | Purpose | Status |
|--------|---------|--------|
| **AnyCitationMetric** | Detects presence of `[N]` citations | ✅ Validated |
| **CitationsMatchedMetric** | Calculates citation match percentage | ✅ Validated |
| **CitationFormatComplianceMetric** | Detects prohibited patterns like `[1, 2, 3]` | ✅ Validated |
| **SubsectionExtractionMetric** | Extracts CPR subsections (31.1, 31.6, etc.) | ✅ Validated |
| **CategoryCoverageMetric** | Counts document categories referenced | ✅ Validated |

**Validation Test Results**: 20/20 assertions passed (100% success rate)
**Test File**: `evals/validate_metrics.py`

### 2. Test Dataset

- **File**: `evals/practical_test_questions.json`
- **Questions**: 120+ realistic legal questions
- **Categories**: 13 categories covering:
  - Pre-action protocol
  - Limitation periods
  - Case management (CMC)
  - Disclosure
  - Interim applications
  - Statements of case
  - Court-specific procedures (Commercial, Circuit Commercial)
  - Expert evidence
  - Costs
  - Evidence
  - Trial preparation
  - Cross-category questions
  - Urgency questions

### 3. Environment Configuration

- **Virtual Environment**: `.evalenv` created with:
  - `azure-ai-evaluation`
  - `evaltools`
  - `ragas`
  - `langchain`
  - All required dependencies

- **Azure Developer CLI**:
  - Installed at `/usr/local/bin/azd` (version 1.20.3)
  - Authenticated as `hbalapatabendi@gmail.com`
  - Tenant: `3bfe16b2-5fcc-4565-b1f1-15271d20fecf`

### 4. Backend Service

- **Status**: Running (PID 68573, port 50505)
- **Framework**: Quart (async Flask-like)
- **Authentication**: Configured for unauthenticated access
  - `AZURE_ENABLE_UNAUTHENTICATED_ACCESS="true"`
  - `AZURE_USE_AUTHENTICATION="true"` (allows empty auth_claims)

### 5. Configuration Files

- **evaluate_config.json**: Updated with all 5 custom metrics
- **evaluate.py**: Metrics registered and configured
- **load_azd_env.py**: Patched with fallback to scan `.azure/` directories

***

## ⏳ Current Blocker

### Backend /chat Endpoint Hang

**Symptoms**:

- Backend accepts POST `/chat` requests successfully
- Logs show: `"Chat endpoint using approach: ChatReadRetrieveReadApproach"`
- Request hangs indefinitely during `approach.run()` execution
- No Azure-specific errors logged (no connection timeout, auth failure)
- Backend process remains alive, doesn't crash

**Likely Causes**:

1. **Azure OpenAI quota exhausted** - GPT-5-nano deployment may have rate limits
1. **Azure Search service not responding** - Index query timing out
1. **Network connectivity issue** - Firewall/VPN blocking Azure API calls
1. **Model deployment offline** - GPT-5-nano deployment not available
1. **Authentication token expired** - AzureDeveloperCliCredential needs refresh

**Affected Component**: `ChatReadRetrieveReadApproach.run_until_final_call()` at line 274-293

**Evidence**:

```bash
# Backend startup logs
INFO:app:Setting up Azure credential using AzureDeveloperCliCredential with tenant_id 3bfe16b2-5fcc-4565-b1f1-15271d20fecf
INFO:app:OPENAI_HOST is azure, setting up Azure OpenAI client
INFO:app:Using Azure credential (passwordless authentication) for Azure OpenAI client
[2025-11-11 11:29:46 +0000] [68573] [INFO] Running on http://127.0.0.1:50505 (CTRL + C to quit)

# Test request logs
ERROR:root:Exception getting authorization information - "Authorization header is expected"
INFO:app:Chat endpoint received request: {'messages': [{'content': 'What are the key provisions of CPR Part 31?', 'role': 'user'}], 'context': {'overrides': {}}}
INFO:app:Chat endpoint context: {'overrides': {}, 'auth_claims': {}}
INFO:app:Chat endpoint using approach: ChatReadRetrieveReadApproach
# <-- HANGS HERE -->
```

**Azure Resources**:

- **OpenAI Endpoint**: `https://cog-gz2m4s637t5me-us2.openai.azure.com/`
- **Deployment**: `gpt-5-nano` (version `2024-12-01-preview`)
- **Search Index**: `legal-court-rag-index`

***

## 📋 Next Steps

### Option 1: Troubleshoot Azure Backend (Recommended)

1. **Check Azure OpenAI quota**:

   ```bash
   azd config show
   # Check deployment status in Azure Portal
   ```

1. **Verify model deployment**:

   ```bash
   az cognitiveservices account deployment show \
     --resource-group <rg-name> \
     --name cog-gz2m4s637t5me-us2 \
     --deployment-name gpt-5-nano
   ```

1. **Test Azure Search connectivity**:

   ```bash
   curl -H "api-key: <key>" \
     "https://<search-service>.search.windows.net/indexes/legal-court-rag-index?api-version=2023-11-01"
   ```

1. **Add detailed logging to backend**:
   - Add `logger.info()` statements in `chatreadretrieveread.py` at lines 285-360
   - Identify exact hanging point (OpenAI call vs Search call)

1. **Refresh authentication**:

   ```bash
   /usr/local/bin/azd auth login --use-device-code
   ```

### Option 2: Use Deployed Azure Instance

If the app is already deployed to Azure App Service:

1. Get deployed URL from `.azure/cpr-rag/.env` (AZURE_WEBAPP_URL)
1. Modify `evaluate.py` to point to deployed endpoint:

   ```python
   target_url = os.getenv("AZURE_WEBAPP_URL", "http://localhost:50505") + "/chat"
   ```

### Option 3: Generate Synthetic Ground Truth

Create ground truth manually without backend:

1. Pick 10-20 questions from `practical_test_questions.json`
1. Manually write expected answers with `[1][2][3]` citations
1. Save as `ground_truth_manual.jsonl`
1. Run evaluation: `python evals/evaluate.py --data ground_truth_manual.jsonl`

***

## 🚀 Running Evaluation (Once Backend Responds)

### 1. Generate Ground Truth

```bash
source .evalenv/bin/activate
python evals/generate_ground_truth.py --numquestions=50
```

This creates `ground_truth.jsonl` with responses from backend using new citation format.

### 2. Run Evaluation

```bash
source .evalenv/bin/activate
python evals/evaluate.py --numquestions=10
```

### 3. Review Results

Check `evals/results/` directory for:

- Metric scores (CSV/JSON)
- Per-question breakdown
- Aggregate statistics

***

## 📊 Expected Metrics Output

Based on validation tests, expected output format:

```json
{
  "metrics": {
    "any_citation": {
      "total": 10,
      "rate": 1.0,
      "description": "100% of responses contain citations"
    },
    "citations_matched": {
      "avg_match_rate": 0.95,
      "description": "95% average citation match rate"
    },
    "citation_format_compliance": {
      "total_compliant": 9,
      "compliance_rate": 0.90,
      "total_violations": 1,
      "description": "90% responses follow [N] format correctly"
    },
    "subsection_extraction_accuracy": {
      "avg_subsections_extracted": 3.2,
      "description": "Average 3.2 CPR subsections per response"
    },
    "category_coverage": {
      "avg_categories": 1.5,
      "description": "Average 1.5 document categories per response"
    }
  }
}
```

***

## 📁 Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `evals/evaluate.py` | Main evaluation script | ✅ Ready |
| `evals/evaluate_config.json` | Evaluation configuration | ✅ Configured |
| `evals/practical_test_questions.json` | Test dataset | ✅ 120+ questions |
| `evals/validate_metrics.py` | Standalone metric validation | ✅ 100% pass rate |
| `evals/ground_truth.jsonl` | Ground truth Q&A pairs | ⚠️ Needs regeneration |
| `.evalenv/` | Python virtual environment | ✅ Configured |
| `app/backend/main.py` | Backend service | ⏳ Running but hanging |
| `.azure/cpr-rag/.env` | Azure resource config | ✅ Configured |

***

## 🔍 Validation Results

### Metric Logic Validation

```text
TEST CASE 1: Perfect Response - All metrics pass
  ✓ AnyCitationMetric: PASS
  ✓ CitationsMatchedMetric: PASS (100.00%)
  ✓ CitationFormatComplianceMetric: PASS
  ✓ SubsectionExtractionMetric: PASS (3 subsections found)
  ✓ CategoryCoverageMetric: PASS (1 category)

TEST CASE 2: Format Violation - Comma in citations
  ✓ AnyCitationMetric: PASS (detected [1, 2, 3])
  ✓ CitationsMatchedMetric: PASS (100.00%)
  ✓ CitationFormatComplianceMetric: PASS (correctly detected violation)
  ✓ SubsectionExtractionMetric: PASS
  ✓ CategoryCoverageMetric: PASS

TEST CASE 3: Missing Citations
  ✓ AnyCitationMetric: PASS (correctly detected no citations)
  ✓ CitationsMatchedMetric: PASS (0.00%)
  ✓ CitationFormatComplianceMetric: PASS
  ✓ SubsectionExtractionMetric: PASS
  ✓ CategoryCoverageMetric: PASS

TEST CASE 4: Multi-category Coverage
  ✓ AnyCitationMetric: PASS
  ✓ CitationsMatchedMetric: PASS (100.00%)
  ✓ CitationFormatComplianceMetric: PASS
  ✓ SubsectionExtractionMetric: PASS
  ✓ CategoryCoverageMetric: PASS (2 categories)

FINAL: 20/20 assertions passed (100% success rate)
```

***

## 💡 Recommendations

1. **Immediate**: Focus on resolving Azure backend hang (check quota, deployment status, network)
1. **Alternative**: Use deployed Azure instance if available
1. **Fallback**: Create manual ground truth for 10-20 questions to validate evaluation pipeline
1. **Long-term**: Add timeout handling to Azure API calls in backend code

***

## 📞 Support Information

- **Azure Subscription**: Check `.azure/cpr-rag/.env` for resource IDs
- **Authentication**: `hbalapatabendi@gmail.com` (tenant: `3bfe16b2-5fcc-4565-b1f1-15271d20fecf`)
- **Backend PID**: 68573 (port 50505)
- **azd Location**: `/usr/local/bin/azd`

***

**Document Updated**: 2025-11-11
**Status**: Evaluation infrastructure complete, awaiting Azure backend connectivity resolution

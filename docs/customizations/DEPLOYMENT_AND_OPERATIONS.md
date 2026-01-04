# Legal RAG Scraper: Deployment & Operations

**Status**: ✅ **DEPLOYED & OPERATIONAL**

Deployed system for automating the scraping, validation, embedding, and indexing of UK Civil Procedure Rules and Practice Directions using a **GitHub Actions weekly automation workflow**.

## Table of Contents

- [Overview](#overview)
- [What Was Deployed](#what-was-deployed)
- [Local Development](#local-development)
- [Operations & Monitoring](#operations--monitoring)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

---

## Overview

The legal RAG scraper is a **fully automated GitHub Actions workflow** that maintains a current index of UK legal documents (~768 CPR Parts 1-89 and Practice Directions) in Azure Search.

**Pipeline Components:**
1. **Scraping** (`scrape_cpr.py`) - Fetches from justice.gov.uk using Selenium
2. **Validation** (`validation.py`) - Quality and legal terminology checks
3. **Embedding** (`upload_with_embeddings.py`) - Vector generation via Azure OpenAI
4. **Upload** - Batch update to Azure Search index

**Located in:** `scripts/legal-scraper/`

### Data Coverage

- **Civil Procedure Rules**: Parts 1-89 from justice.gov.uk
- **Practice Directions**: 60+ supplementary court guidance documents
- **Index Size**: ~768 documents, 5000+ chunks with 3072-dimension embeddings
- **Update Frequency**: Weekly (Sundays, 00:00 UTC) or manual dispatch

---

## What Was Deployed

### GitHub Actions Workflow (Phase 2)

**Status**: ✅ **DEPLOYED & OPERATIONAL**

The production system uses a **GitHub Actions workflow** for fully automated legal document indexing.

**File**: `.github/workflows/legal-scraper.yml`

**How It Works:**

```
Weekly Schedule (Sundays, 00:00 UTC)
              ↓
    Job 1: Scrape & Validate
    ├── Fetch ~768 CPR documents from justice.gov.uk
    ├── Validate structure, legal terms, UTF-8 encoding
    └── Generate embeddings (2.5-3 hours via Azure OpenAI)
              ↓
    Job 2: Upload to Azure Search
    └── Update cpr-index with validated documents + embeddings
              ↓
    Artifacts retained (7 days):
    ├── Scraped JSON files
    ├── Validation reports
    └── Embedding logs
```

**Key Configuration:**

| Setting | Value |
|---------|-------|
| **Schedule** | Weekly Sunday 00:00 UTC |
| **Manual Trigger** | Yes (with `dry_run` flag) |
| **Auth Method** | Service Principal + OIDC Federated Credentials |
| **Batch Size** | 3 documents (rate limiting) |
| **Batch Delay** | 10 seconds |
| **Retry Strategy** | Exponential backoff (5 attempts, 4-60s waits) |
| **Pipeline Duration** | ~3-4 hours total |

**GitHub Secrets (Production Environment):**
```
AZURE_CLIENT_ID              (Service principal ID)
AZURE_TENANT_ID              (Entra ID tenant)
AZURE_SUBSCRIPTION_ID        (Azure subscription)
AZURE_SEARCH_SERVICE         (Search endpoint URL)
AZURE_SEARCH_INDEX           (cpr-index)
AZURE_OPENAI_SERVICE         (OpenAI endpoint URL)
AZURE_OPENAI_EMB_DEPLOYMENT  (text-embedding-3-large)
```

**Performance Metrics:**

| Phase | Duration | Notes |
|-------|----------|-------|
| Scraping | 2-3 min | Fetches all CPR documents |
| Validation | < 1 min | Quality checks on 768 docs |
| Embedding | 2.5-3 hrs | Rate-limited generation |
| Upload | 30 sec | Only if changes detected |
| **Total** | **~3-4 hours** | Full pipeline (if changes found) |

**Upload Behavior:**
- Only uploads if **changes detected** in scraped content
- Compares new documents against existing index
- Skips upload if documents are unchanged (no redundant operations)
- Dry-run mode always shows what would be uploaded without uploading

---

## Local Development

### Prerequisites

- Python 3.10+
- Chrome/Chromium browser (Selenium WebDriver)
- Azure subscription with:
  - Azure AI Search service
  - Azure OpenAI with `text-embedding-3-large` deployment
  - Credentials configured via `azd`

### Setup & Testing

**1. Install dependencies:**
```bash
cd /path/to/azure-search-openai-demo-2
pip install -r requirements-dev.txt
```

**2. Configure Azure credentials:**
```bash
azd auth login
azd env new dev-env
azd env select dev-env
azd env set AZURE_SEARCH_SERVICE <your-search-service>
azd env set AZURE_SEARCH_INDEX cpr-index
azd env set AZURE_OPENAI_SERVICE <your-openai-service>
azd env set AZURE_OPENAI_EMB_DEPLOYMENT text-embedding-3-large
```

**3. Run pipeline locally:**

```bash
# Full pipeline (scrape → validate → embed → upload)
cd scripts/legal-scraper
./run_pipeline.sh

# Dry-run (no actual upload)
./run_pipeline.sh --dry-run

# Individual steps
python scrape_cpr.py                    # Scrape only
python validation.py --input Upload     # Validate only
python upload_with_embeddings.py        # Upload only
```

**4. Output location:**
```
data/legal-scraper/
├── processed/
│   ├── Upload/           # Scraped JSON documents
│   └── cache/            # Cache and metadata
└── validation-reports/   # Quality check logs
```

### Manual Testing via GitHub Actions

**Dry-run (no upload):**
```bash
gh workflow run legal-scraper.yml \
  --repo adalex-ai/azure-search-openai-demo \
  -f dry_run=true
```

**Production run (with upload):**
```bash
gh workflow run legal-scraper.yml \
  --repo adalex-ai/azure-search-openai-demo
```

**View results:**
```bash
# Monitor workflow
gh run list --workflow legal-scraper.yml --repo adalex-ai/azure-search-openai-demo

# Download artifacts (scraped files + reports)
gh run download <run-id> --name artifacts
```

---

## Operations & Monitoring

### Health Checks

**Check latest workflow run:**
```bash
# View GitHub Actions status
gh run list --workflow legal-scraper.yml \
  --repo adalex-ai/azure-search-openai-demo --limit 5
```

**Check Azure Search index:**
```bash
# Count current documents
curl -X GET "https://<search-service>.search.windows.net/indexes/cpr-index/docs/\$count?api-version=2023-11-01" \
  -H "api-key: <search-key>"

# Verify recent uploads
curl -X POST "https://<search-service>.search.windows.net/indexes/cpr-index/docs/search?api-version=2023-11-01" \
  -H "Content-Type: application/json" \
  -H "api-key: <search-key>" \
  -d '{
    "search": "*",
    "select": "id, sourcepage, updated",
    "orderby": "updated desc",
    "top": 20
  }'
```

---

## Maintenance

### Weekly Tasks

- Monitor GitHub Actions for any failures
- Check Azure OpenAI quota usage (embedding API calls)
- **Note**: If no changes detected, upload phase is skipped (this is normal behavior)
- Verify document count hasn't dropped unexpectedly
- Review workflow logs for any warnings

### Monthly Tasks

- Review validation reports for new content issues (in workflow artifacts)
- Analyze embedding quality on sample user queries
- Check Azure resource costs
- Verify all expected court guides are present in index

### Quarterly Tasks

- Update Selenium selectors if justice.gov.uk layout changes
- Review and update legal terminology validation rules (in `config.py`)
- Archive old workflow artifacts
- Test manual workflow trigger with dry-run flag

### Updating the Pipeline

After modifying scraper scripts:

```bash
# Changes are deployed automatically on next push
git commit -am "Update scraper logic"
git push origin main

# Workflow will use new code on next scheduled run
# Or trigger manually:
gh workflow run legal-scraper.yml --repo adalex-ai/azure-search-openai-demo
```

---

## Troubleshooting

### Common Issues

#### 1. Embedding Dimension Errors

**Error**: `"Embedding has wrong dimensions: 0 vs 3072"`

**Cause**: Documents missing vector embeddings.

**Solution**:
- Check GitHub Actions workflow logs for embedding failures
- Verify Azure OpenAI `text-embedding-3-large` deployment is accessible
- Run validation step separately: `python validation.py --input Upload`
- Check Azure OpenAI API quota hasn't been exceeded

#### 2. Rate Limiting (429 Errors)

**Error**: `"Azure OpenAI 429 Too Many Requests"`

**Status**: ✅ **Already handled** in `upload_with_embeddings.py`:
- Batch size: 3 documents
- Delay: 10 seconds between batches
- Exponential backoff: 4s → 8s → 16s → 32s → 60s (5 attempts)
- Automatic retry with exponential jitter

**If still occurring**: Increase batch delay in `scripts/legal-scraper/upload_with_embeddings.py`:
```python
BATCH_DELAY = 15  # Increase from 10 seconds
```

#### 3. Selenium: ChromeDriver Not Found

**Cause**: Chrome/Chromium not installed on runner.

**Solution** (already handled in GitHub Actions):
- Ubuntu runner includes Chrome pre-installed
- Scraper uses headless mode by default
- For local testing on macOS:
  ```bash
  brew install chromium
  # Or download ChromeDriver manually
  ```

#### 4. Azure Search Index Not Found

**Cause**: Index name mismatch or doesn't exist.

**Solution**:
```bash
# List existing indexes
az search index list --resource-group <rg> --search-service-name <search-service>

# View index details
az search index show --resource-group <rg> --search-service-name <search-service> --name cpr-index
```

#### 5. No Documents Scraped (Zero Results)

**Cause**: Website structure changed or CSS selectors outdated.

**Debugging**:
```bash
# Test locally with debug output
cd scripts/legal-scraper
python scrape_cpr.py --debug

# Check justice.gov.uk is accessible
curl -I https://www.justice.gov.uk/courts/procedure-rules/civil/rules

# Review recent workflow logs
gh run view <run-id> --log
```

#### 6. Validation Failures (Documents Rejected)

**Cause**: Documents don't meet quality standards.

**Check**:
- Legal terminology count (minimum 3 required)
- Content length (minimum 500 characters)
- UTF-8 encoding issues
- Required fields missing (id, content, sourcepage)

**Solution**:
- Review validation report in workflow artifacts
- Adjust thresholds in `scripts/legal-scraper/config.py`
- Check if justice.gov.uk content structure changed

#### 7. Workflow Completes But No Upload

**Scenario**: GitHub Actions finishes scraping and validation, but upload doesn't occur.

**This is normal** - Upload only happens if changes are detected in content compared to existing index.

**What's happening**:
- Scraper fetched documents
- Validation passed
- Comparison found: documents match existing index
- Upload skipped (prevents redundant operations)

**To verify**:
- Check workflow logs for "No changes detected" message
- Ensure dry-run flag is not set to `true`
- Verify justice.gov.uk documents actually changed

**To force upload** (testing only):
- Run with dry-run: `gh workflow run legal-scraper.yml -f dry_run=true`
- Or manually modify documents in Azure Search index before next run

### Workflow Logs

**View GitHub Actions logs:**
```bash
# List recent runs
gh run list --workflow legal-scraper.yml --repo adalex-ai/azure-search-openai-demo

# View specific run details
gh run view <run-id> --log

# Download artifacts (scraped files + reports)
gh run download <run-id> --name artifacts --dir ./debug-data
```

**Artifacts included:**
- `processed/Upload/` - Scraped JSON documents
- `validation-reports/` - Quality check results
- Workflow logs with full pipeline output


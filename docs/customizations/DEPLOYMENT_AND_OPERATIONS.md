# Legal RAG Scraper: Deployment & Operations Guide

Comprehensive guide for deploying, maintaining, and operating the CPR and Practice Direction scraping, embedding, and indexing pipeline.

## Table of Contents

- [Overview](#overview)
- [Local Deployment](#local-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)

---

## Overview

The legal RAG scraper pipeline consists of three core components:

1. **Scraping** (`scrape_cpr.py`) - Fetches Civil Procedure Rules and Practice Directions from justice.gov.uk
2. **Validation** (`validation.py`) - Quality checks on content, legal terminology, and Azure Search comparison
3. **Embedding & Upload** (`upload_with_embeddings.py`) - Generates vector embeddings and indexes documents

**Located in:** `scripts/legal-scraper/`

### Data Sources

- **Civil Procedure Rules (CPR)**: Part 1-89 from justice.gov.uk
- **Practice Directions**: 60+ supplementary legal documents
- **Total Documents**: ~768 indexed documents with 3072-dimension embeddings

---

## Local Deployment

### Prerequisites

- Python 3.10+
- Chrome/Chromium browser (for Selenium scraping)
- Azure credentials (subscription, tenant ID)
- Azure OpenAI service with `text-embedding-3-large` deployment
- Azure AI Search service

### Setup

1. **Install Dependencies:**
   ```bash
   cd /path/to/azure-search-openai-demo-2
   pip install -r requirements-dev.txt
   ```

2. **Configure Azure Credentials:**
   ```bash
   azd auth login
   azd env new my-env
   azd env select my-env
   ```

3. **Set Environment Variables:**
   ```bash
   azd env set AZURE_SEARCH_SERVICE <your-search-service>
   azd env set AZURE_SEARCH_INDEX cpr-index
   azd env set AZURE_OPENAI_SERVICE <your-openai-service>
   azd env set AZURE_OPENAI_EMB_DEPLOYMENT text-embedding-3-large
   ```

### Running the Pipeline

**Full pipeline (scrape → validate → upload):**
```bash
cd scripts/legal-scraper
./run_pipeline.sh
```

**With options:**
```bash
./run_pipeline.sh --dry-run              # Test without uploading
./run_pipeline.sh --staging              # Upload to staging index
./run_pipeline.sh --skip-validation      # Skip validation step
```

**Individual steps:**
```bash
python scrape_cpr.py                    # Scrape only
python validation.py --input Upload     # Validate only
python upload_with_embeddings.py        # Upload only
```

### Output Files

```
data/legal-scraper/
├── processed/
│   ├── Upload/                    # Scraped JSON documents
│   └── cache/                     # Upload cache and metadata
└── validation-reports/            # Validation result logs
```

---

## Cloud Deployment

### Option 1: GitHub Actions (Recommended - Already Implemented)

Phase 2 uses GitHub Actions for fully automated weekly scraping.

**File:** `.github/workflows/legal-scraper.yml`

**Features:**
- Scheduled weekly runs (configurable)
- Manual dispatch with dry-run flag
- Service principal authentication via OIDC
- Automatic rate-limited embedding generation
- Detailed logging and error reporting

**Usage:**
```bash
# Manual trigger (dry-run)
gh workflow run legal-scraper.yml \
  --repo adalex-ai/azure-search-openai-demo \
  -f dry_run=true

# View results
gh run list --workflow legal-scraper.yml --repo adalex-ai/azure-search-openai-demo
```

See [Phase 2 Scraper Automation](./PHASE_2_SCRAPER_AUTOMATION.md) for detailed configuration.

---

### Option 2: Azure Container Apps Job

Deploy as a scheduled Docker container job in Azure.

#### Step 1: Create Dockerfile

```dockerfile
FROM python:3.11-slim

# Install Chrome and dependencies for Selenium
RUN apt-get update && apt-get install -y wget gnupg unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY scripts/legal-scraper/ scripts/legal-scraper/
COPY data/ data/

# Create pipeline script
RUN echo '#!/bin/bash\n\
cd scripts/legal-scraper\n\
python scrape_cpr.py && \n\
python validation.py --input Upload && \n\
python upload_with_embeddings.py' > /app/run_pipeline.sh && \
chmod +x /app/run_pipeline.sh

ENTRYPOINT ["/app/run_pipeline.sh"]
```

#### Step 2: Build and Push Image

```bash
az acr build \
  --registry <your-acr-name> \
  --image legal-rag-scraper:latest \
  --file Dockerfile .

az acr build \
  --registry <your-acr-name> \
  --image legal-rag-scraper:v1.0 \
  --file Dockerfile .
```

#### Step 3: Create Container App Job

```bash
az containerapp job create \
  --name legal-rag-scraper-job \
  --resource-group <your-resource-group> \
  --environment <your-aca-environment> \
  --trigger-type "Schedule" \
  --cron-expression "0 2 * * 0" \
  --image <your-acr-name>.azurecr.io/legal-rag-scraper:latest \
  --registry-server <your-acr-name>.azurecr.io \
  --registry-username <your-username> \
  --registry-password <your-password> \
  --env-vars \
    AZURE_SEARCH_SERVICE=<value> \
    AZURE_SEARCH_KEY=<value> \
    AZURE_OPENAI_ENDPOINT=<value> \
    AZURE_OPENAI_KEY=<value> \
    AZURE_OPENAI_EMB_DEPLOYMENT=text-embedding-3-large
```

**Schedule Format (Cron):**
- `0 2 * * 0` - Every Sunday at 2 AM
- `0 2 * * *` - Every day at 2 AM
- `0 */6 * * *` - Every 6 hours

#### Step 4: Monitor Execution

```bash
# List job executions
az containerapp job execution list \
  --name legal-rag-scraper-job \
  --resource-group <your-resource-group>

# View job logs
az containerapp job execution logs \
  --job legal-rag-scraper-job \
  --execution <execution-id> \
  --resource-group <your-resource-group>

# Manually trigger job
az containerapp job start \
  --name legal-rag-scraper-job \
  --resource-group <your-resource-group>
```

---

### Option 3: Azure Functions (Timer Trigger)

For lightweight scheduling without Docker overhead.

#### Limitations

- **Selenium Challenge**: Azure Functions Consumption Plan has sandbox restrictions. Use Premium Plan or custom container if full browser scraping is required.
- **Timeout**: Default 5-minute timeout (configurable up to 10 minutes). Consider breaking pipeline into separate functions.

#### Setup

1. **Create Function App:**
   ```bash
   az functionapp create \
     --resource-group <your-resource-group> \
     --consumption-plan-location eastus \
     --runtime python \
     --runtime-version 3.11 \
     --functions-version 4 \
     --name <your-function-app>
   ```

2. **Create Timer Trigger Function:**
   ```bash
   func new --name UpdateLegalRAG --template "Timer trigger"
   ```

3. **Implement in `function_app.py`:**
   ```python
   import azure.functions as func
   import subprocess
   
   app = func.FunctionApp()
   
   @app.function_name("UpdateLegalRAG")
   @app.schedule(schedule="0 2 * * *")  # Daily at 2 AM
   def update_legal_rag(myTimer: func.TimerRequest) -> None:
       """Scheduled update of legal RAG index."""
       result = subprocess.run(
           ["python", "-m", "scripts.legal_scraper.run_pipeline"],
           capture_output=True,
           text=True,
           timeout=600  # 10 minutes
       )
       
       if result.returncode != 0:
           raise Exception(f"Pipeline failed: {result.stderr}")
   ```

4. **Deploy:**
   ```bash
   func azure functionapp publish <your-function-app>
   ```

---

## Monitoring & Maintenance

### Health Checks

**Verify Latest Run:**
```bash
# Check GitHub Actions (Phase 2)
gh run list --workflow legal-scraper.yml --repo adalex-ai/azure-search-openai-demo --limit 1

# Or check Container Apps (if using)
az containerapp job execution list --name legal-rag-scraper-job
```

**Check Index Status:**
```bash
# Count documents in Azure Search
curl -X GET "https://<search-service>.search.windows.net/indexes/cpr-index/docs/$count?api-version=2023-11-01" \
  -H "api-key: <search-key>"

# Verify recent embeddings
curl -X POST "https://<search-service>.search.windows.net/indexes/cpr-index/docs/search?api-version=2023-11-01" \
  -H "Content-Type: application/json" \
  -H "api-key: <search-key>" \
  -d '{
    "search": "*",
    "select": "id, title, created_at",
    "orderby": "created_at desc",
    "top": 10
  }'
```

### Maintenance Tasks

#### Weekly

- Monitor GitHub Actions or Container App logs for errors
- Check Azure OpenAI quota usage (track embedding API calls)
- Verify document count hasn't dropped unexpectedly

#### Monthly

- Review validation reports for new content issues
- Check for any CPR website structure changes (Selenium locator failures)
- Analyze embedding quality on sample queries
- Review Azure costs and optimize if needed

#### Quarterly

- Update Selenium selectors if justice.gov.uk changes layout
- Review and update legal terminology validation rules
- Archive old logs and cache files

### Updating the Pipeline

**After modifying scripts:**
```bash
# For GitHub Actions: Just push to main branch
git commit -am "Update scraper logic"
git push origin main

# For Container Apps: Rebuild and redeploy
az acr build --registry <acr> --image legal-rag-scraper:latest --file Dockerfile .
az containerapp job update --name legal-rag-scraper-job --image <new-image>
```

---

## Troubleshooting

### Common Issues

#### 1. **"Embedding has wrong dimensions: 0 vs 3072"**

**Cause:** Documents missing embeddings.

**Solution:**
- Run validation separately: `python validation.py --input Upload`
- Check Azure OpenAI is accessible: `curl https://<openai-service>.openai.azure.com/`
- Verify embedding model deployment: `text-embedding-3-large`

#### 2. **"Azure OpenAI 429 Rate Limit Error"**

**Cause:** Hitting Azure API rate limits.

**Status:** Already handled! `upload_with_embeddings.py` includes:
- Batch processing: 3 documents per batch
- 10-second delay between batches
- Exponential backoff retry (5 attempts, 4-60 second wait)
- Automatic logging of retries

**To optimize:** Reduce batch size or increase delays in `scripts/legal-scraper/upload_with_embeddings.py`:
```python
BATCH_SIZE = 2  # Reduce from 3
BATCH_DELAY = 15  # Increase from 10 seconds
```

#### 3. **"Selenium: ChromeDriver not found"**

**Cause:** Chrome/Chromium not installed.

**Solution:**
```bash
# macOS
brew install chromium

# Linux
apt-get install google-chrome-stable

# Or use headless mode (already implemented in scraper)
```

#### 4. **"Azure Search index not found"**

**Cause:** Index name mismatch or doesn't exist.

**Solution:**
```bash
# List existing indexes
az search index list --resource-group <rg> --search-service-name <search-service>

# Create index if missing
az search index create --resource-group <rg> --search-service-name <search-service> --name cpr-index
```

#### 5. **"No new documents scraped"**

**Cause:** Website structure changed or scraper needs update.

**Debugging:**
```bash
# Test scraper with verbose output
python scrape_cpr.py --debug

# Check if justice.gov.uk is accessible
curl -I https://www.justice.gov.uk/courts/procedure-rules/civil

# Review Selenium logs
python -c "import logging; logging.basicConfig(level=logging.DEBUG); exec(open('scrape_cpr.py').read())"
```

### Log Locations

- **GitHub Actions**: https://github.com/adalex-ai/azure-search-openai-demo/actions
- **Container Apps**: `az containerapp job execution logs --job legal-rag-scraper-job`
- **Azure Functions**: Azure Portal → Function App → Monitor → Logs

---

## Architecture

### Data Flow

```
justice.gov.uk (CPR & Practice Directions)
    ↓
[Selenium Web Scraper]
    ↓
data/legal-scraper/processed/Upload/ (JSON files)
    ↓
[Validation] - Quality checks, legal terminology
    ↓
[Embedding Generation] - Azure OpenAI text-embedding-3-large
    ↓
[Rate-Limited Batching] - 3 docs/batch, 10s delays
    ↓
[Azure Search Upload]
    ↓
Azure AI Search Index (cpr-index)
    ↓
[RAG App Frontend] - User queries return citations
```

### Key Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Documents | ~768 | CPR Parts 1-89 + Practice Directions |
| Embedding Dimension | 3072 | text-embedding-3-large |
| Batch Size | 3 docs | Optimized for rate limiting |
| Batch Delay | 10 seconds | Between batches |
| Pipeline Duration | ~3-4 hours | Full scrape + embed + upload |
| Azure OpenAI Cost | ~$0.02/run | Based on 768 embeddings at $0.02/1M tokens |

### Error Handling

- **Retries**: Automatic exponential backoff (5 attempts)
- **Graceful Degradation**: Skips failed documents, continues pipeline
- **Validation**: Pass-through allows documents to proceed even without embeddings
- **Logging**: All errors logged to validation reports and stdout

---

## Support & References

- **Phase 2 Automation**: [PHASE_2_SCRAPER_AUTOMATION.md](./PHASE_2_SCRAPER_AUTOMATION.md)
- **Legal Evaluation**: [../legal_evaluation.md](../legal_evaluation.md)
- **Scripts**: [../../scripts/legal-scraper/](../../scripts/legal-scraper/)
- **Azure Docs**: [Azure Container Apps Jobs](https://learn.microsoft.com/azure/container-apps/jobs)
- **Azure Functions**: [Timer Trigger Functions](https://learn.microsoft.com/azure/azure-functions/functions-bindings-timer)


# Phase 2: Legal Document Scraper Automation

This document describes the Phase 2 implementation of the Legal RAG system, which automates the scraping, validation, and uploading of Civil Procedure Rules to Azure Search.

## Architecture Overview

Phase 2 consists of a **GitHub Actions workflow** that runs on a schedule (weekly) or on-demand to keep the Azure Search index up-to-date with the latest legal documents.

```text
GitHub Actions Workflow
├── Step 1: Scrape Civil Procedure Rules
│   └── scrape_cpr.py (using Selenium to fetch from justice.gov.uk)
├── Step 2: Validate Documents
│   └── validate_and_review.py (check quality, structure, legal terms)
├── Step 3: Generate Embeddings
│   └── upload_with_embeddings.py (Azure OpenAI text-embedding-3-large)
└── Step 4: Upload to Azure Search
    └── Push validated documents with embeddings to production index
```

## Key Components

### 1. Scraper (`scripts/legal-scraper/scrape_cpr.py`)

- **Purpose**: Fetch Civil Procedure Rules from justice.gov.uk using Selenium WebDriver
- **Language**: Python with Selenium
- **Output**: JSON files saved to `data/legal-scraper/processed/Upload/`
- **Document Format**:

  ```json
  {
    "id": "Insolvency Proceedings_chunk_001",
    "content": "Full document text...",
    "category": "Civil Procedure Rules and Practice Directions",
    "sourcepage": "Insolvency Proceedings",
    "sourcefile": "Insolvency Proceedings",
    "storageUrl": "https://www.justice.gov.uk/...",
    "embedding": [],
    "updated": "2026-01-04T00:00:00Z"
  }
  ```

### 2. Validator (`scripts/legal-scraper/validation.py`, `validate_and_review.py`)

- **Purpose**: Ensure documents meet quality standards before upload
- **Checks**:
  - Required fields present (id, content, category, sourcepage, sourcefile)
  - Minimum content length (500 characters)
  - Legal terminology validation (≥3 legal terms required)
  - Valid UTF-8 encoding
  - No common scraping failures (404 errors, JavaScript required, etc.)
- **Output**: Validation reports saved to `data/legal-scraper/validation-reports/`

### 3. Embedding Generator (`scripts/legal-scraper/upload_with_embeddings.py`)

- **Purpose**: Generate vector embeddings for documents before upload to Azure Search
- **Model**: `text-embedding-3-large` (3072 dimensions)
- **Process**:
  - Batch processing with batch size of 3 documents
  - 10-second delay between batches to respect Azure OpenAI rate limits
  - Automatic retry on 429 (Too Many Requests) errors
  - Handles up to ~768 documents in ~2.5-3 hours
- **Error Handling**: Skips documents that fail embedding generation and logs for review

### 4. GitHub Actions Workflow (`.github/workflows/legal-scraper.yml`)

- **Schedule**: Runs weekly on Sunday at midnight UTC
- **Manual Trigger**: Can be manually triggered via Actions tab with `dry_run` flag
- **Jobs**:
1. **scrape-and-validate**: Scrapes documents and validates them
1. **upload-production**: Uploads validated documents to Azure Search (only if `dry_run=false`)
- **Artifacts**: Uploads scraped data and validation reports for debugging

## Secrets & Configuration

The workflow requires these secrets in the GitHub `Production` environment:

| Secret | Purpose |
|--------|---------|
| `AZURE_CLIENT_ID` | Service principal for GitHub Actions OIDC |
| `AZURE_TENANT_ID` | Azure tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_SEARCH_SERVICE` | Azure Search endpoint URL |
| `AZURE_SEARCH_INDEX` | Target search index name |
| `AZURE_OPENAI_SERVICE` | Azure OpenAI service endpoint |
| `AZURE_OPENAI_EMB_DEPLOYMENT` | Embedding model deployment name |

## Running the Pipeline

### Manual Trigger (Dry-Run)

```bash
gh workflow run legal-scraper.yml --repo adalex-ai/azure-search-openai-demo -f dry_run=true
```

This will:

- Scrape documents
- Validate them
- Generate embeddings
- Show what would be uploaded WITHOUT actually uploading

### Manual Trigger (Production)

```bash
gh workflow run legal-scraper.yml --repo adalex-ai/azure-search-openai-demo
```

This will perform the full pipeline including upload to Azure Search.

### Local Testing

```bash
cd scripts/legal-scraper
./run_pipeline.sh --validate --upload --dry-run --skip-approval
```

Options:

- `--scrape`: Run scraper only
- `--validate`: Run validation only
- `--upload`: Run upload only
- `--dry-run`: Show what would be uploaded without uploading
- `--skip-approval`: Skip approval prompt
- `--input Upload`: Use Upload directory (default)

## Maintenance & Troubleshooting

### Common Issues

#### 1. Rate Limiting (429 Errors)

**Problem**: Azure OpenAI returns "Too Many Requests"

**Solution**:

- The code automatically retries with exponential backoff
- Batch size is reduced to 3 documents
- 10-second delay between batches
- If still failing, increase delay in `upload_with_embeddings.py`:

  ```python
  time.sleep(15)  # Increase from 10
  ```

#### 2. Validation Failures

**Problem**: Documents fail validation

**Check**:

- Ensure documents have legal terminology (check `legal_terms` in `config.py`)
- Verify content length is ≥500 characters
- Check UTF-8 encoding of scraped content

**Solution**:

- Review validation reports in `data/legal-scraper/validation-reports/`
- Adjust `MIN_LEGAL_TERMS` or `MIN_CONTENT_LENGTH` in `config.py`
- Fix scraper if returning malformed documents

#### 3. Scraper Not Finding Documents

**Problem**: Scraper returns 0 documents

**Check**:

- Is justice.gov.uk website structure still the same?
- Are Selenium WebDriver selectors still valid?

**Solution**:

- Run scraper locally to debug
- Update CSS selectors in `scrape_cpr.py` if website changed
- Check browser console for JavaScript errors

### Monitoring

Check workflow status at:

```text
https://github.com/adalex-ai/azure-search-openai-demo/actions
```

Each run produces:

- **Artifacts**: Scraped JSON files and validation reports (retained 7 days)
- **Logs**: Full execution logs visible in Actions UI
- **Status**: Pass/Fail with error messages

### Updating Secrets

To rotate or update secrets:

```bash
gh secret set AZURE_CLIENT_ID --env Production --body "new-value" --repo adalex-ai/azure-search-openai-demo
```

## Performance Notes

- **Scraping**: ~2-3 minutes to fetch all CPR documents
- **Validation**: ~1-2 seconds per document (< 1 minute total)
- **Embedding Generation**: ~2.5-3 hours for 768 documents (~14 seconds per document)
- **Upload**: ~30 seconds for 768 documents

**Total pipeline time**: ~3-4 hours (dominated by embedding generation)

## Future Improvements

- [ ] Incremental updates (only scrape changed documents)
- [ ] Parallel embedding generation (if Azure quota allows)
- [ ] Webhook notifications on completion
- [ ] Automatic rollback if validation fails above threshold
- [ ] Archive old versions of documents with versioning

## Related Documentation

- [Legal Domain Customizations](./README.md) - Overview of all customizations
- [Evaluation Framework](../legal_evaluation.md) - Quality metrics for legal RAG
- [Data Ingestion](../data_ingestion.md) - General document processing pipeline

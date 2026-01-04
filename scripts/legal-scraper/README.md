# Legal Document Scraper for Azure Search

Local scraping and validation pipeline for legal documents (UK Civil Procedure Rules) with Azure AI Search integration.

## Overview

This folder contains Phase 1 of the legal document scraper integration:
- **Scraping**: Selenium-based web scraper for Civil Procedure Rules
- **Validation**: Content quality checks before upload
- **Review**: Interactive approval workflow before pushing to Azure
- **Upload**: Direct integration with Azure AI Search

## Setup

### Prerequisites

- Python 3.10+
- Virtual environment activated
- Azure credentials configured via `azd`

### Installation

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Configure Azure credentials
azd auth login
azd config set defaults.subscription <your-subscription>
azd config set defaults.location <your-region>
```

### Configuration

Configuration is read from `azd` environment variables:
- `AZURE_SEARCH_SERVICE`: Azure Search service endpoint
- `AZURE_SEARCH_KEY`: Azure Search admin key
- `AZURE_OPENAI_SERVICE`: Azure OpenAI service endpoint
- `AZURE_OPENAI_KEY`: Azure OpenAI key
- `AZURE_OPENAI_EMB_DEPLOYMENT`: Embedding model deployment (default: text-embedding-3-large)

View current configuration:

```bash
azd env get-values
```

## Usage

### Full Pipeline

Run the complete scrape → validate → upload workflow:

```bash
# Dry-run (validate without uploading)
./run_pipeline.sh --dry-run

# Upload to staging index for review
./run_pipeline.sh --staging

# Upload to production
./run_pipeline.sh
```

### Individual Steps

#### Step 1: Scrape

```bash
python scrape_cpr.py                 # Scrape all CPR rules
python scrape_cpr.py --test-single   # Test with first rule only
python scrape_cpr.py --test-few 5    # Test with first 5 rules
```

Output: JSON files in `data/legal-scraper/processed/Upload/`

#### Step 2: Validate & Review

```bash
# Validate with approval prompt
python validate_and_review.py --input Upload

# Validate without approval prompt (batch mode)
python validate_and_review.py --input Upload --no-approve

# Upload to staging for manual review in Azure Portal
./run_pipeline.sh --staging --skip-validation
```

The validation script:
- ✅ Checks content quality (length, legal terminology)
- 📊 Detects duplicate content
- 🔍 Compares against current Azure Search index
- ⚠️ Reports new, updated, and unchanged documents
- 📋 Generates validation report JSON

#### Step 3: Upload

```bash
# Dry-run (show what would upload)
python upload_with_embeddings.py --input Upload --dry-run

# Upload to production index
python upload_with_embeddings.py --input Upload

# Upload to staging index
python upload_with_embeddings.py --input Upload --staging

# Upload with custom batch size
python upload_with_embeddings.py --input Upload --batch-size 200
```

## Output Structure

```
data/legal-scraper/
├── processed/
│   ├── Upload/                    # Scraped JSON files
│   │   ├── Part_1.json
│   │   ├── Part_2.json
│   │   └── ...
├── validation-reports/            # Validation results
│   └── validation_report_Upload.json
└── cache/                         # Change tracking
    └── upload_hashes.json
```

## Document Format

Documents are stored in Azure Search OpenAI Demo compatible format:

```json
{
  "id": "Part 1 – Overriding Objective",
  "content": "Full rule content with line breaks and section delimiters (\\n\\n---\\n\\n)",
  "category": "Civil Procedure Rules and Practice Directions",
  "sourcepage": "Overriding Objective",
  "sourcefile": "Part 1",
  "storageUrl": "https://www.justice.gov.uk/courts/procedure-rules/civil/rules/part01",
  "embedding": [],  # Populated by Azure Search during indexing
  "oids": [],
  "groups": [],
  "parent_id": "Part 1 – Overriding Objective"
}
```

## Validation Rules

### Content Quality

- **Minimum length**: 500 characters
- **Legal terminology**: ≥3 terms from (court, rule, procedure, claimant, defendant, etc.)
- **Character encoding**: Valid UTF-8
- **Boilerplate detection**: <10% cookie/navigation text

### Changes Tracking

- Uses SHA-256 hash of document content
- Detects new documents (not in index)
- Identifies modified documents (hash changed)
- Caches hashes in `data/legal-scraper/cache/upload_hashes.json`

## Troubleshooting

### Azure Connection Issues

```bash
# Verify credentials are configured
azd env get-values | grep AZURE

# Re-authenticate if needed
azd auth login

# Check service connectivity
python -c "from config import Config; Config.validate_azure_config()"
```

### Validation Failures

1. Check validation report: `data/legal-scraper/validation-reports/`
2. Review error messages for specific issues
3. Fix content issues (length, terminology) in source
4. Re-run validation

### Upload Issues

- Batch size too large? Try `--batch-size 100`
- Rate limited? Upload automatically adds delays between batches
- Index doesn't exist? Create it first in Azure Portal

## Phase 1 vs Phase 2

### Phase 1 (Current - Local Testing)

- ✅ Local scraping with Selenium
- ✅ Terminal-based approval prompts
- ✅ Dry-run mode for validation
- ✅ Manual pipeline execution
- ✅ Validation reports saved locally

### Phase 2 (With GitHub Enterprise)

- ✅ Scheduled GitHub Actions workflow (`.github/workflows/legal-scraper.yml`)
- ✅ GitHub environment approval gates (See [Setup Guide](../../docs/PHASE_2_SETUP.md))
- 🔲 Slack/Teams notifications (Configurable in workflow)
- 🔲 Automated rollback capability
- ✅ Audit trail of all approvals (Via GitHub Deployments)

See [Phase 2 Setup Guide](../../docs/PHASE_2_SETUP.md) for configuration instructions.

## Performance

- **Scraping**: ~30-60 seconds per rule (depends on content length)
- **Validation**: <5 seconds for 200+ documents
- **Upload**: ~10 seconds per 100 documents

## Notes

- Scraper uses headless Chrome via Selenium
- Documents chunked only if they exceed text-embedding-3-large token limit (7500 tokens)
- Content includes section delimiters (`\n\n---\n\n`) for frontend parsing
- All operations support dry-run mode for safety

## Support

For issues or questions:
1. Check validation reports in `data/legal-scraper/validation-reports/`
2. Review script logs for detailed error messages
3. Run individual steps to isolate issues
4. Use `--help` flag on any script for usage options

## Architecture

```
Legal Document Workflow:
┌─────────────────────────────────────────────┐
│ Scrape CPR Rules from justice.gov.uk        │ (scrape_cpr.py)
└──────────────┬──────────────────────────────┘
               │ JSON files
               ▼
┌─────────────────────────────────────────────┐
│ Validate Content Quality & Azure Index      │ (validate_and_review.py)
│ - Content checks                            │
│ - Azure Search comparison                   │
│ - User approval required                    │
└──────────────┬──────────────────────────────┘
               │ Approved
               ▼
┌─────────────────────────────────────────────┐
│ Upload to Azure Search                      │ (upload_with_embeddings.py)
│ - Staging index (optional)                  │
│ - Production index                          │
└──────────────┬──────────────────────────────┘
               │ Uploaded
               ▼
┌─────────────────────────────────────────────┐
│ Azure AI Search                             │
│ - Embeddings generated                      │
│ - Semantic ranking configured               │
│ - Available for RAG queries                 │
└─────────────────────────────────────────────┘
```

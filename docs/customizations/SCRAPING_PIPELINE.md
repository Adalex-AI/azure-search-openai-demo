# Phase 2: Automated Scraping Pipeline

This document details the automated pipeline used to keep the legal document index (CPR Rules) up to date.

## 🎯 Overview

The legal domain changes frequently. To ensure the RAG system provides accurate answers, we cannot rely on a static dataset. This pipeline:
1.  **Scrapes** the official [justice.gov.uk](https://www.justice.gov.uk) website.
2.  **Validates** the content for quality and legal terminology.
3.  **Embeds** the text using Azure OpenAI.
4.  **Indexes** the data into Azure AI Search.

## 🏗️ Architecture

```text
                    ▲
                    │ (Weekly Trigger or Manual Dispatch)
                    │
┌───────────────────┴──────────────────────────────────────────────────┐
│                 GITHUB ACTIONS WORKFLOW                              │
│             (.github/workflows/legal-scraper.yml)                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐  │
│  │  1. Scraper      │    │  2. Validation   │    │  3. Upload     │  │
│  │  (Selenium)      │───▶│  (Python)        │───▶│  (Azure SDK)   │  │
│  └──────────────────┘    └──────────────────┘    └────────────────┘  │
│           │                       │                       │          │
│           ▼                       ▼                       ▼          │
│      Raw HTML/JSON          Quality Report         Azure AI Search   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## 🔌 Components

The pipeline is implemented in Python matching the main backend environment. The scripts are located in `scripts/legal-scraper/`.

### 1. Scraper (`scrape_cpr.py`)
- **Technology**: Selenium (headless)
- **Target**: Iterates through the CPR "Parts" and "Practice Directions".
- **Output**: Generates JSON files containing the raw text, URL, and title.

### 2. Validation (`validation.py`)
This critical step prevents "garbage in, garbage out". It checks:
- **Legal Terminology**: Ensures common terms (e.g., "claimant", "defendant") appear with expected frequency. Low frequency might indicate a bad scrape.
- **Content Length**: Rejects empty or suspiciously short documents.
- **Structure**: Verifies that required fields (title, content, url) are present.
- **Encoding**: checks for UTF-8 compatibility.

### 3. Embedding & Upload (`upload_with_embeddings.py`)
- **Embeddings**: Uses `text-embedding-3-large` (3072 dimensions) via Azure OpenAI.
- **Updates**: Uses the Azure Search SDK to push updates.
- **Efficiency**: Batches requests and handles rate limiting with exponential backoff.

## 🤖 Automation (GitHub Actions)

The workflow file `.github/workflows/legal-scraper.yml` orchestrates the process.

### Triggers
- **Schedule**: Every Sunday at midnight UTC.
- **Manual**: Can be triggered manually via the "Actions" tab in GitHub.

### Security
The scraper authenticates to Azure using **OpenID Connect (OIDC)** (Federated Credentials). This means:
- No long-lived secrets (like Client Secrets) are stored in GitHub.
- GitHub exchanges a signed token for a short-lived Azure Access Token.

## 🚦 Monitoring

- **Validation Reports**: The validation step outputs a JSON report. If quality drops below a threshold, the pipeline fails *before* touching the production index.
- **GitHub Logs**: Execution logs provide detailed success/failure information for each step.

## 🛠️ Local Development

You can run the pipeline locally for testing or one-off updates.

```bash
cd scripts/legal-scraper

# Dry run (Validate but do not upload)
./run_pipeline.sh --dry-run

# Full execution
./run_pipeline.sh
```

See the [Scraper README](../../scripts/legal-scraper/README.md) for detailed setup instructions.

# Legal RAG System: Architecture & Implementation

This document describes the as-built Legal RAG system architecture, components, and how everything fits together.

## 🎯 System Overview

The Legal RAG system consists of two main phases:

- **Phase 1**: Custom legal domain features integrated into the base RAG application
- **Phase 2**: Automated scraping pipeline for keeping the legal document index current

Together, these create a complete production system for legal document retrieval and analysis.

---

## 📊 End-to-End System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LEGAL RAG APPLICATION                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐         ┌──────────────────┐                    │
│  │  Frontend (React)│         │   Backend (Python)                    │
│  │  TypeScript      │         │   Quart Framework│                    │
│  └────────┬─────────┘         └────────┬─────────┘                    │
│           │                             │                              │
│     ┌─────▼──────────────────────────────▼─────┐                      │
│     │  Chat & Question Interface               │                      │
│     │  - Legal terminology sanitization        │                      │
│     │  - Citation formatting [1][2][3]         │                      │
│     │  - Dynamic source filtering              │                      │
│     └────────────┬────────────────────┬────────┘                      │
│                  │                    │                                │
│     ┌────────────▼─────────────────────▼────────┐                     │
│     │  RAG Retrieval Augmented Generation       │                     │
│     │  - Query processing                       │                     │
│     │  - Hybrid search (keyword + vector)       │                     │
│     │  - Source ranking & citation              │                     │
│     └───────────┬──────────────────────┬────────┘                     │
│                 │                      │                               │
│   ┌─────────────▼─────────┐  ┌─────────▼──────────┐                   │
│   │  Azure AI Search      │  │  Azure OpenAI      │                   │
│   │  Index: cpr-index     │  │  Model: GPT-4      │                   │
│   │  - 768 documents      │  │  Embedding: 3-L    │                   │
│   │  - 3072-D embeddings  │  │  - Response gen    │                   │
│   │  - Hybrid search      │  │  - Embeddings      │                   │
│   └─────────────────────────┘  └────────────────────┘                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

                    ▲
                    │ (Weekly or Manual Trigger)
                    │
┌───────────────────┴──────────────────────────────────────────────────┐
│                 PHASE 2: AUTOMATED SCRAPING PIPELINE                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  GitHub Actions Workflow: `.github/workflows/legal-scraper.yml`       │
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐                         │
│  │  1. Scraper      │    │  2. Validation   │                         │
│  │  ─────────────   │    │  ────────────────│                         │
│  │  scrape_cpr.py   │    │  validation.py   │                         │
│  │  (Selenium)      │    │  - Legal terms   │                         │
│  │                  │    │  - UTF-8 check   │                         │
│  │  Fetches from:   │    │  - Content len   │                         │
│  │  justice.gov.uk  │    │  - Field valid   │                         │
│  │                  │    │                  │                         │
│  │  Outputs:        │    │  Outputs:        │                         │
│  │  - ~768 JSON     │    │  - Validation    │                         │
│  │    documents     │    │    reports       │                         │
│  │  - metadata      │    │  - Quality score │                         │
│  └──────┬───────────┘    └────────┬─────────┘                         │
│         │                         │                                    │
│         └───────────┬─────────────┘                                    │
│                     │                                                  │
│              ┌──────▼──────────┐                                       │
│              │  3. Embedding   │                                       │
│              │  ───────────────│                                       │
│              │  upload_with_   │                                       │
│              │  embeddings.py  │                                       │
│              │                 │                                       │
│              │  - Batch size:3 │                                       │
│              │  - 10s delays   │                                       │
│              │  - Exponential  │                                       │
│              │    backoff      │                                       │
│              │  - Azure OpenAI │                                       │
│              │    3072-D vecs  │                                       │
│              │                 │                                       │
│              │  Duration:      │                                       │
│              │  ~2.5-3 hours   │                                       │
│              └──────┬──────────┘                                       │
│                     │                                                  │
│              ┌──────▼──────────┐                                       │
│              │  4. Upload      │                                       │
│              │  ───────────────│                                       │
│              │  Push to Azure  │                                       │
│              │  Search Index   │                                       │
│              │                 │                                       │
│              │  - Updates cpr- │                                       │
│              │    index        │                                       │
│              │  - Maintains    │                                       │
│              │    embeddings   │                                       │
│              └─────────────────┘                                       │
│                                                                         │
│  Schedule: Weekly (Sundays, midnight UTC) or Manual Dispatch          │
│  Auth: Service Principal with OIDC federated credentials              │
│  Env: Production GitHub environment with 7 secrets                    │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Sequence Diagram

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  Frontend (Chat.tsx / Ask.tsx)      │
│  - Parse query                      │
│  - Apply category filter (optional) │
│  - Apply search depth setting       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  Backend Request Processing                 │
│  - Extract overrides (search depth, etc)    │
│  - Format search query                      │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  Retrieval Strategy Selection               │
│  (RetrieveThenRead or ChatReadRetrieveRead) │
│  - Apply agentic retrieval if enabled       │
│  - Query rewriting for context              │
└────────────┬────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  Azure AI Search - Hybrid Search                │
│  1. Vector Search (embedding similarity)        │
│     - Query embedded via Azure OpenAI           │
│     - Compare to 3072-D doc embeddings          │
│  2. Keyword Search (BM25 ranking)               │
│     - Traditional text matching                 │
│  3. Semantic Ranking (optional)                 │
│     - Rerank top results                        │
│  Result: Top K documents with scores            │
└────────────┬──────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  CUSTOM: Source Processing                      │
│  (customizations/approaches/source_processor.py)│
│  - Extract metadata (title, category, etc)      │
│  - Process subsections                          │
│  - Build enhanced citations                     │
│  Output: Structured sources with metadata       │
└────────────┬──────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  LLM Prompt Construction                        │
│  - System prompt (legal domain specific)        │
│  - Query + sources + conversation history       │
│  - Clear citation format rules                  │
└────────────┬──────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  Azure OpenAI - Response Generation             │
│  Model: GPT-4 (or configured model)             │
│  - Reads sources                                │
│  - Generates answer                             │
│  - Cites relevant sources [1][2][3]            │
│  Output: Answer text with citations             │
└────────────┬──────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  CUSTOM: Citation Sanitization                  │
│  (customizations/citationSanitizer.ts)         │
│  - Fix malformed citations                      │
│  - Ensure [1][2][3] format                      │
│  - Remove extra commas/spaces                   │
│  Output: Clean answer with proper citations     │
└────────────┬──────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│  Frontend Display (Answer.tsx)                  │
│  - Render answer with formatted citations      │
│  - Show source documents                        │
│  - Display metadata (court type, date, etc)    │
│  - Interactive citation clicks                  │
└──────────────────────────────────────────────────┘
```

---

## 📦 Component Architecture

### Frontend Components

```
app/frontend/src/
├── components/
│   ├── Answer/
│   │   └── AnswerParser.tsx
│   │       └── Imports: sanitizeCitations
│   │           (removes malformed citations)
│   │
│   ├── Chat/
│   │   └── QuestionInput.tsx
│   │       ├── CategoryDropdown (custom)
│   │       └── SearchDepthDropdown (custom)
│   │
│   └── Settings.tsx
│       └── UI controls for RAG parameters
│
├── pages/
│   ├── chat/
│   │   └── Chat.tsx
│   │       ├── Imports: useCategories
│   │       └── Search depth controls
│   │
│   └── ask/
│       └── Ask.tsx
│           ├── Imports: useCategories
│           └── Search depth controls
│
└── customizations/
    ├── index.ts (barrel exports)
    ├── config.ts (feature flags)
    ├── citationSanitizer.ts
    │   ├── sanitizeCitations()
    │   ├── fixMalformedCitations()
    │   └── collapseAdjacentCitations()
    ├── useCategories.ts
    │   └── Hook fetching from /api/categories
    ├── CategoryDropdown/
    │   └── Dynamic category selector
    └── SearchBoxWithCategories/
        └── Enhanced search UI
```

### Backend Components

```
app/backend/
├── app.py
│   ├── Imports: categories_bp (blueprint)
│   ├── Registers: /api/categories endpoint
│   └── Returns config with feature flags
│
├── approaches/
│   ├── chatreadretrieveread.py (main chat approach)
│   │   ├── Imports: citation_builder, source_processor
│   │   ├── Delegates citation logic
│   │   └── Delegates source processing
│   │
│   ├── retrievethenread.py (main ask approach)
│   │   ├── Imports: citation_builder, source_processor
│   │   └── Similar delegation pattern
│   │
│   └── prompts/
│       ├── ask_answer_question.prompty (CUSTOM)
│       ├── chat_answer_question.prompty (CUSTOM)
│       ├── chat_query_rewrite.prompty (CUSTOM)
│       └── Explicit legal domain guidance
│
└── customizations/
    ├── __init__.py (exports)
    ├── config.py (feature flags)
    ├── routes/
    │   └── categories.py
    │       └── GET /api/categories endpoint
    │           Queries Azure Search for categories
    │
    └── approaches/
        ├── __init__.py (exports)
        ├── citation_builder.py
        │   ├── build_enhanced_citation()
        │   ├── extract_subsection()
        │   └── Legal citation formatting
        │
        └── source_processor.py
            ├── process_documents()
            ├── extract_multiple_subsections()
            └── Structured source metadata
```

---

## 🚀 Phase 2 Scraping Pipeline Architecture

### Workflow Execution Flow

```
┌──────────────────────────────────────────────────────────┐
│  GitHub Actions Trigger                                  │
│  ├─ Weekly Schedule (Sundays 00:00 UTC)                 │
│  └─ Manual Dispatch (gh workflow run)                   │
└────────────────────┬─────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │ Activate Service      │
         │ Principal via OIDC    │
         │ (federated creds)     │
         └───────────┬───────────┘
                     │
    ┌────────────────▼──────────────────┐
    │  Job 1: Scrape & Validate         │
    ├────────────────────────────────────┤
    │                                    │
    │  Step 1: Setup Python 3.10         │
    │  Step 2: Install dependencies      │
    │  Step 3: Run scraper               │
    │    python scrape_cpr.py            │
    │    └─ Output: ~768 JSON files      │
    │                                    │
    │  Step 4: Validate documents        │
    │    python validation.py            │
    │    ├─ Check legal terms            │
    │    ├─ Verify structure             │
    │    └─ Output: validation report    │
    │                                    │
    │  Step 5: Upload artifacts          │
    │    (scraped files + reports)       │
    │                                    │
    └────────────────┬───────────────────┘
                     │
                     ▼
         ┌──────────────────────┐
         │  Generate Embeddings │
         │  (if not --dry-run)  │
         └──────────────┬───────┘
                        │
    ┌───────────────────▼──────────────────┐
    │  Embedding Generation                │
    ├────────────────────────────────────────┤
    │                                        │
    │  Process: 768 documents                │
    │  ├─ Batch size: 3 documents            │
    │  ├─ Delay: 10 seconds between batches  │
    │  ├─ Retries: Exponential backoff       │
    │  │   (4s → 8s → 16s → 32s → 60s)     │
    │  └─ API: Azure OpenAI text-embedding- │
    │      3-large                          │
    │                                        │
    │  Output: Embedding vectors (3072-D)   │
    │  Duration: ~2.5-3 hours                │
    │                                        │
    └───────────────┬───────────────────────┘
                    │
    ┌───────────────▼───────────────────┐
    │  Job 2: Upload (Conditional)      │
    ├───────────────────────────────────┤
    │                                   │
    │  IF dry_run == "false":           │
    │  ├─ Upload to Azure Search        │
    │  ├─ Index: cpr-index              │
    │  ├─ Batch size: 200 documents     │
    │  └─ Complete with embeddings      │
    │                                   │
    │  ELSE (dry_run == "true"):        │
    │  └─ Show what would be uploaded   │
    │     (no actual changes)           │
    │                                   │
    └───────────────┬───────────────────┘
                    │
    ┌───────────────▼─────────────────┐
    │  Workflow Complete              │
    ├─────────────────────────────────┤
    │  ✅ Success → Index updated     │
    │  ❌ Failure → Check logs         │
    │                                 │
    │  Artifacts retained 7 days      │
    │  (scraped files + reports)      │
    └─────────────────────────────────┘
```

---

## 🔐 Authentication & Security

### GitHub Actions OIDC Flow

```
GitHub Actions
    │
    ├─ Token Request (OIDC)
    │      Subject: repo:adalex-ai/azure-search-openai-demo:...
    │      Audience: api://AzureADTokenExchange
    │      │
    │      ▼
    │   Microsoft Entra ID
    │   (Federated Credentials)
    │      │
    │      ├─ Verify OIDC token
    │      ├─ Map to Service Principal
    │      │  (appId: b23573c4-61fe-4686-a25b-fd2682f128c5)
    │      │
    │      └─ Issue Access Token
    │            │
    │            ▼
    │      Azure SDK
    │      (Automatic credential)
    │            │
    └────────────▼─────────────────┐
                                   │
                ┌──────────────────▼────────────────┐
                │ Authenticate to:                  │
                ├───────────────────────────────────┤
                │ • Azure Search (admin key)        │
                │ • Azure OpenAI (API key)          │
                │ • Subscription management         │
                └───────────────────────────────────┘
```

### Secrets Management

GitHub Production Environment Secrets (7 total):

```
Production Environment
├── AZURE_CLIENT_ID              → Service principal ID
├── AZURE_TENANT_ID              → Entra ID tenant
├── AZURE_SUBSCRIPTION_ID        → Azure subscription
├── AZURE_SEARCH_SERVICE         → Search endpoint URL
├── AZURE_SEARCH_INDEX           → Index name (cpr-index)
├── AZURE_OPENAI_SERVICE         → OpenAI endpoint URL
└── AZURE_OPENAI_EMB_DEPLOYMENT  → Embedding model (text-embedding-3-large)
```

---

## 📊 Key Metrics

### Document Coverage

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Documents** | ~768 | CPR Parts 1-89 + Practice Directions |
| **Embedding Dimension** | 3072 | text-embedding-3-large model |
| **Total Chunks** | 5,000+ | After splitting for search |
| **Index Size** | ~1.2 GB | In Azure Search |

### Performance Characteristics

| Operation | Duration | Notes |
|-----------|----------|-------|
| **Scraping** | 2-3 min | Fetches all documents from justice.gov.uk |
| **Validation** | < 1 min | Quality checks (768 docs) |
| **Embedding Generation** | 2.5-3 hrs | Rate-limited to respect Azure quotas |
| **Upload** | 30 sec | Batch push to Azure Search |
| **Total Pipeline** | ~3-4 hrs | End-to-end weekly run |

### Quality Metrics

| Metric | Score | Notes |
|--------|-------|-------|
| **Precedent Matching** | 95% | Correct source citation (62 test Qs) |
| **Legal Terminology** | 100% | UK legal terms used correctly |
| **Statute Citations** | 60% | CPR Part/Rule numbers cited |
| **Citation Format** | 99% | [1][2][3] format compliance |

### Cost Estimate (Monthly)

| Service | Cost | Notes |
|---------|------|-------|
| **Azure OpenAI (Embeddings)** | ~$0.06 | ~3 runs × 768 docs × $0.02/1M tokens |
| **Azure Search** | ~$50-100 | Basic tier, 1 replica |
| **Compute (GitHub)** | Free | 2000 free minutes/month |
| **Storage (Blob)** | ~$2-3 | Processed documents |
| **Total** | ~$55-110/mo | Fully operational system |

---

## 🔗 Integration Points Summary

### What Was Added to Upstream Code

| File | Change | Type |
|------|--------|------|
| `app.py` | Import + register `categories_bp` | Integration |
| `AnswerParser.tsx` | Import + use `sanitizeCitations` | Integration |
| `Chat.tsx` | Import `useCategories` + dropdown UI | Integration |
| `Ask.tsx` | Import `useCategories` + dropdown UI | Integration |
| `vite.config.ts` | Proxy config for `/api/categories` | Configuration |
| `en/translation.json` | Labels for category filter + search depth | Localization |

### What Was Created in Customizations

| Component | Purpose | Type |
|-----------|---------|------|
| `citation_builder.py` | Enhanced legal citations | Backend Logic |
| `source_processor.py` | Structured source processing | Backend Logic |
| `categories.py` | Dynamic category API endpoint | Backend Route |
| `citationSanitizer.ts` | Fix malformed citations | Frontend Logic |
| `useCategories.ts` | Fetch categories from API | Frontend Hook |
| `CategoryDropdown/` | Category selection UI | Frontend Component |
| `config.py` | Feature flags (backend) | Configuration |
| `config.ts` | Feature flags (frontend) | Configuration |

---

## 🎓 What Was Accomplished

### Phase 1: Legal Domain Customization
✅ **Citation System**
- Enforces [1][2][3] format (not [1,2,3])
- Sanitizes malformed citations automatically
- Legal references properly formatted

✅ **Source Filtering**
- Dynamic categories fetched from Azure Search
- Filter results by document type
- Friendly display names for sources

✅ **Legal Prompts**
- Customized for CPR/court rules
- Explicit citation format guidance
- UK legal terminology emphasis

✅ **Evaluation Framework**
- 41 legal-specific unit tests
- 95% precedent matching accuracy
- 62 ground truth questions
- Legal metrics: statute citations, terminology, formatting

### Phase 2: Automation & Scaling
✅ **GitHub Actions Workflow**
- Weekly automated scraping (configurable schedule)
- Manual dispatch with dry-run option
- Service principal OIDC authentication
- 7 production secrets configured

✅ **Scraping Pipeline**
- ~768 documents fetched weekly
- Selenium-based web scraper
- JSON document output
- Metadata preservation

✅ **Validation System**
- Legal terminology checks
- Content quality validation
- UTF-8 encoding verification
- Duplicate detection

✅ **Embedding Generation**
- On-demand vector generation
- Rate-limited batch processing (3 docs/batch)
- Exponential backoff retry (5 attempts)
- 3072-dimension vectors (text-embedding-3-large)

✅ **Azure Search Integration**
- Automated index updates
- Maintains embeddings
- Hybrid search capability (keyword + vector)
- ~3-4 hour total pipeline

### System Reliability
✅ **Error Handling**
- Graceful degradation (skips failed docs)
- Detailed logging
- Validation reports
- Exponential backoff retries

✅ **Security**
- Federated OIDC credentials (no stored secrets)
- Service principal-based auth
- GitHub Production environment isolation
- Least privilege access

✅ **Documentation**
- Complete architecture diagrams
- Deployment & operations guide
- Phase 2 automation guide
- Troubleshooting reference
- Integration point documentation

---

## 📈 Future Capability

The system is designed to support:

| Capability | Status | Next Steps |
|------------|--------|-----------|
| Incremental updates | Not implemented | Track document versions in index |
| Parallel embedding | Rate limit constrained | Higher Azure quota tier |
| Multi-language | Not implemented | Extend scraper + embedding model |
| Scheduled backups | Not implemented | Archive index snapshots |
| Monitoring dashboards | Not implemented | Application Insights integration |
| Webhook notifications | Not implemented | Teams/Slack integration |

---

## 🏗️ Technology Stack

### Frontend
- **React** 18+ with TypeScript
- **Fluent UI** for components
- **Custom hooks** for API integration
- **Vite** for build tooling

### Backend
- **Python 3.10+** with Quart framework
- **Azure SDK** for service integration
- **Tenacity** for retry logic
- **Selenium** for web scraping

### Cloud Services
- **Azure AI Search** (Hybrid search with semantic ranking)
- **Azure OpenAI** (GPT-4 for generation, text-embedding-3-large for vectors)
- **GitHub Actions** (Workflow orchestration)
- **Azure Key Vault** (Secret management)

### Data Pipeline
- **Batch processing** with rate limiting
- **Error recovery** with exponential backoff
- **Validation** before upload
- **Artifact storage** for debugging

---

## 📚 Related Documentation

- [Customizations Guide](./README.md) - Feature overview
- [Phase 2 Automation](./PHASE_2_SCRAPER_AUTOMATION.md) - Workflow details
- [Deployment & Operations](./DEPLOYMENT_AND_OPERATIONS.md) - Setup and maintenance
- [Legal Evaluation](../legal_evaluation.md) - Quality metrics
- [Main README](../../README.md) - Project overview

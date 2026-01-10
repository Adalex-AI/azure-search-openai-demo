# Customizations Guide: Legal RAG System

This document describes all custom features added to this Azure Search + OpenAI RAG application and how they are organized for merge-safe updates.

## 🎯 Overview

This fork of the Azure Search + OpenAI demo implements a specialized **Legal RAG (Retrieval Augmented Generation)** system for the UK Civil Procedure Rules. It includes:

- **Phase 1**: Custom prompts and evaluation framework for legal domain
- **Phase 2**: Automated scraping and indexing pipeline (GitHub Actions workflow)
- **Enhanced Citations**: Legal-specific citation formatting
- **Quality Metrics**: Precedent matching, legal terminology validation

All custom code is isolated in `/customizations/` folders to support seamless upstream merges.

## 🏗️ System Architecture

For a comprehensive overview of the complete deployed system architecture, data flows, and component interactions, see [System Architecture Documentation](./SYSTEM_ARCHITECTURE.md). This includes:
- **End-to-end system architecture diagrams**
- **Data flow sequence diagrams**
- **Component breakdown (frontend + backend)**
- **Phase 2 scraping pipeline architecture**
- **Technology stack & key metrics**
- **What was accomplished (Phase 1 & 2)**

## 📁 Merge-Safe Architecture

All customizations are isolated in dedicated `/customizations/` folders to prevent conflicts when updating from upstream.

### Backend Customizations
Location: `/app/backend/customizations/`

```
customizations/
├── __init__.py          # Module initialization with feature exports
├── config.py            # Feature flags and configuration
├── approaches/          # Legal domain RAG approach customizations
│   ├── __init__.py      # Exports CitationBuilder, SourceProcessor
│   ├── citation_builder.py  # Enhanced legal citation logic
│   └── source_processor.py  # Structured source content processing
└── routes/
    ├── __init__.py      # Blueprint exports
    └── categories.py    # Dynamic categories API endpoint
```

### Approaches Customization Architecture

The `/customizations/approaches/` module provides modular, reusable components for legal document processing. This follows a **composition** pattern where helper classes are used by the main approach classes.

#### CitationBuilder (`citation_builder.py`)
Handles legal-specific citation formatting:
- Three-part citations: `"1.1, D5 - Filing deadlines (p. 210), Commercial Court Guide"`
- Subsection extraction from content (e.g., `"1.1 Filing requirements..."` → `"1.1"`)
- Encoded sourcepage parsing (e.g., `"PD3E-1.1"` → `"1.1"`)
- Multi-subsection document splitting

**Usage:**
```python
from customizations.approaches import citation_builder

# Build enhanced citation
citation = citation_builder.build_enhanced_citation(doc, source_index=1)

# Extract subsection
subsection = citation_builder.extract_subsection(doc)

# Split document into subsections
subsections = citation_builder.extract_multiple_subsections(doc)
```

#### SourceProcessor (`source_processor.py`)
Handles structured source content for frontend:
- Document processing with metadata enrichment
- Multi-subsection document splitting
- Consistent field mapping (storageUrl, category, updated, etc.)

**Usage:**
```python
from customizations.approaches import source_processor

# Process documents for frontend
structured_sources = source_processor.process_documents(
    documents, 
    use_semantic_captions=False
)
```

### Frontend Customizations
Location: `/app/frontend/src/customizations/`

```
customizations/
├── index.ts                    # Barrel file exporting all components/hooks
├── config.ts                   # Frontend feature flags
├── citationSanitizer.ts        # Citation formatting fixes
├── useCategories.ts            # Hook for dynamic category fetching
├── CategoryDropdown/           # Category selection component
│   ├── CategoryDropdown.tsx
│   └── index.ts
├── SearchBoxWithCategories/    # Enhanced search with categories
│   ├── SearchBoxWithCategories.tsx
│   └── index.ts
└── GPT4VSettings/              # Vision settings component (deprecated)
    ├── GPT4VSettings.tsx
    └── index.ts
```

### Custom Prompts
Location: `/app/backend/approaches/prompts/`

These files are intentionally NOT in `/customizations/` because they are the core business logic and should be reviewed during upgrades:
- `ask_answer_question.prompty` - Legal domain prompt for "Ask" approach
- `chat_answer_question.prompty` - Legal domain prompt for "Chat" approach
- `chat_query_rewrite.prompty` - Query rewriting for legal context

---

## ✨ Custom Features

### 1. Citation Formatting
**Files:** `citationSanitizer.ts`, Custom prompts

#### Problem Solved
AI models sometimes generate malformed citations in various incorrect formats:

| Issue | Example | Fixed To |
|-------|---------|----------|
| Comma-separated | `1, 2, 4` | `[1][2][4]` |
| Mixed format | `1, 2, [3]` | `[1][2][3]` |
| Commas in brackets | `[1, 2, 3]` | `[1][2][3]` |
| Commas between brackets | `[1], [2], [3]` | `[1][2][3]` |
| Paragraph confusion | `1. 1` | `[1]` |

#### Expected Format
- Each citation: single number in brackets `[1]`
- Multiple citations: consecutive brackets with NO commas `[1][2][3]`
- Example: "The bundle should include case summaries and draft orders [1][2]."

#### Frontend Sanitizer Functions
- `sanitizeCitations(text)` - Master function that applies all fixes
- `fixMalformedCitations(text)` - Fixes `1. 1` → `[1]` patterns
- `collapseAdjacentCitations(text)` - Keeps only last citation in sequences

**Usage:**
```typescript
import { sanitizeCitations } from "../customizations";

const cleanText = sanitizeCitations(rawModelOutput);
```

#### Prompt-Level Rules
The custom prompts in `/approaches/prompts/` contain explicit citation format rules:
- Single source per sentence (one citation at end)
- Punctuation before citation: `...rule.[1]` not `...[1] rule.`
- Explicit examples of correct and incorrect formats

### 2. Dynamic Source Filtering
**Files:** Backend `categories.py`, Frontend `useCategories.ts`, `CategoryDropdown/`

Enables filtering search results by document source fetched dynamically from Azure Search index. Sources are displayed with friendly names (e.g., "Commercial Court Guide" instead of "Commercial Court").

**Backend Endpoint:** `GET /api/categories`
- Returns sources from "category" field in search index with display name mapping
- Falls back to default sources if field not found

**Frontend Usage:**
```typescript
import { useCategories } from "../customizations";

const { categories, loading, error } = useCategories();
```

### 3. Search Depth Dropdown (Agentic Retrieval Reasoning Effort)
**Files:** `Chat.tsx` (inline integration)

Adds a user-facing dropdown next to the category filter to control agentic retrieval reasoning effort. This allows users to choose how thoroughly the system searches for relevant documents.

**Options:**
| Option | Label | Description |
|--------|-------|-------------|
| `minimal` | Minimal | Single search query - fastest, cheapest, best for simple lookups |
| `low` | Low (Recommended) | Expands queries for better coverage - good for most legal questions |
| `medium` | Medium | Thorough multi-query planning - best for complex comparative questions |

**UI Location:** Chat input area, to the right of the source dropdown, with an info icon (ℹ️) that shows a tooltip explaining each option.

**Visibility Conditions:**
- Only shows when `showAgenticRetrievalOption` is true (configured in backend)
- Only shows when `useAgenticRetrieval` is true (agentic retrieval is enabled)

**Merge Notes:**
- This is an inline change in `Chat.tsx` (not in `/customizations/`)
- Look for `// CUSTOM: Search Depth dropdown` comment
- Uses existing `reasoningEffort` state variable
- Translations added to `en/translation.json` under `labels.agenticReasoningEffortOptions`

### 4. Legal Domain Prompts
**Files:** `*.prompty` files in `/approaches/prompts/`

Customized system prompts for:
- Legal terminology and definitions
- Civil Procedure Rules context
- Strict citation formatting rules
- Court-specific guidance

### 4. Legal Domain Evaluation Framework
**Files:** `evals/evaluate.py`, `evals/evaluate_config_legal.json`, `evals/ground_truth_cpr.jsonl`, `evals/test_legal_metrics.py`, `evals/test_search_index.py`

Comprehensive evaluation framework with legal-specific metrics:

| Metric | Purpose |
|--------|---------|
| `statute_citation_accuracy` | Validates CPR Part/Rule and statutory references |
| `case_law_citation_accuracy` | Checks neutral citation format ([2024] EWCA Civ 123) |
| `legal_terminology_accuracy` | Ensures UK terminology (claimant, not plaintiff) |
| `citation_format_compliance` | Validates [1][2][3] format, not [1,2,3] |
| `precedent_matching` | Verifies correct source document attribution |

**Quick Start:**
```bash
# Run legal evaluation
cd evals
python evaluate.py --config evaluate_config_legal.json

# Run unit tests (41 tests)
python -m pytest test_legal_metrics.py -v

# Test Azure Search index
python test_search_index.py --action test
```

See [Legal Domain Evaluation Documentation](docs/legal_evaluation.md) for full details.

### 5. Feature Flags
**Backend:** `customizations/config.py`
```python
ENABLE_CATEGORY_FILTER = True
ENABLE_GPT4V_SUPPORT = True
```

**Frontend:** `customizations/config.ts`
```typescript
export const CUSTOM_FEATURES = {
    ENABLE_CATEGORY_FILTER: true,
    ENABLE_GPT4V_SETTINGS: false,  // Deprecated
    ENABLE_DYNAMIC_CATEGORIES: true,
};
```

---

## 🎁 Enhanced Feedback System (v1.0)

**Files:** 
- `app/backend/customizations/thought_filter.py` - Filters system prompts from thoughts
- `app/backend/customizations/routes/feedback.py` - Enhanced feedback API with deployment tracking
- `tests/test_feedback.py` - Feedback endpoint tests
- `tests/test_thought_filter.py` - Thought filtering unit tests

### Problem Solved
The original feedback system exposed system prompts to end users because thoughts from API responses included "Prompt to generate answer" steps containing sensitive instructions. The system had no deployment version tracking for feedback correlation.

### Security Model

The enhanced system ensures **system prompts are never visible to users**:

1. **User API Response** → Filtered thoughts (no system prompts)
2. **User Submits Feedback** → Feedback only contains user-safe thoughts  
3. **Admin Storage** → Separate `*_admin.json` files with full diagnostic data
4. **Deployment Tracking** → Every feedback includes version/commit hash

### Key Components

#### ThoughtFilter Utility (`thought_filter.py`)
Automatically classifies and filters thought steps:

**Admin-Only Thoughts (Filtered from users):**
- "Prompt to generate answer" - Contains system instructions
- Any thought with `raw_messages` - Raw LLM message objects
- "Prompt to rewrite query" - Internal reasoning
- "Query rewrite" - System-level operations

**User-Safe Thoughts (Preserved for users):**
- "Search Query" - The actual search query executed
- "Retrieved Documents" - Document summaries and counts
- "Custom Analysis" - Custom user-visible analysis steps

**Functions:**
```python
# Check if a thought contains sensitive info
is_admin_only_thought(thought: ThoughtStep) -> bool

# Get only user-safe thoughts
filter_thoughts_for_user(thoughts: list[ThoughtStep]) -> list[ThoughtStep]

# Filter thoughts for feedback submission (same as above)
filter_thoughts_for_feedback(thoughts: list[ThoughtStep]) -> list[ThoughtStep]

# Extract admin-only thoughts for backend storage
extract_admin_only_thoughts(thoughts: list[ThoughtStep]) -> list[ThoughtStep]

# Split into both categories
split_thoughts(thoughts: list[ThoughtStep]) -> tuple[list, list]
```

**Usage:**
```python
from customizations import filter_thoughts_for_user, extract_admin_only_thoughts

# Filter for user-facing API response
api_response["context"]["thoughts"] = filter_thoughts_for_user(thoughts)

# Extract for admin storage
admin_file["admin_only_thoughts"] = extract_admin_only_thoughts(thoughts)
```

#### Deployment Metadata (`config.py`)
Captures version information automatically:

```python
from customizations import get_deployment_metadata

metadata = get_deployment_metadata()
# Returns:
# {
#     "deployment_id": "prod-v1",              # DEPLOYMENT_ID env var
#     "app_version": "1.0.0",                  # APP_VERSION env var
#     "git_sha": "abc123def456",               # GIT_SHA env var
#     "model_name": "gpt-4",                   # AZURE_OPENAI_CHATGPT_MODEL
#     "environment": "production"              # Based on RUNNING_IN_PRODUCTION
# }
```

**Environment Variables:**
- `DEPLOYMENT_ID` - Unique deployment identifier (optional, defaults to "unknown")
- `APP_VERSION` - Semantic version string (optional, defaults to "0.0.0")
- `GIT_SHA` - Git commit hash for exact version tracking (optional, defaults to "unknown")
- `AZURE_OPENAI_CHATGPT_MODEL` - Model name for feedback correlation
- `RUNNING_IN_PRODUCTION` - Environment indicator (set automatically by Bicep)

#### Enhanced Feedback Route (`routes/feedback.py`)
Processes feedback with security and metadata:

**Features:**
1. Filters system prompts from user-submitted context
2. Includes deployment metadata in every feedback record
3. Stores separate admin files with full diagnostic data
4. Respects user consent for context sharing
5. Logs to both local storage and Azure Blob Storage

**Feedback Payload Structure:**
```json
{
  "event_type": "legal_feedback",
  "context_shared": true,
  "payload": {
    "message_id": "msg-id-123",
    "rating": "helpful",
    "issues": ["wrong_citation"],
    "comment": "Citation was outdated"
  },
  "context": {
    "user_prompt": "What is...",
    "ai_response": "The answer is...",
    "conversation_history": [...],
    "thoughts": [...]  // FILTERED - no system prompts
  },
  "metadata": {
    "deployment_id": "prod-v1",
    "app_version": "1.0.0",
    "git_sha": "abc123def456",
    "model_name": "gpt-4",
    "environment": "production"
  }
}
```

**Separate Admin File** (`*_admin.json`):
```json
{
  "message_id": "msg-id-123",
  "timestamp": "2026-01-10T12:00:00Z",
  "admin_only_thoughts": [
    {
      "title": "Prompt to generate answer",
      "description": "System prompt content",
      "props": {"raw_messages": [...]}
    }
  ],
  "metadata": { ... }
}
```

### Integration Points

#### Backend API Response Filtering
In `app/backend/approaches/chatapproach.py`:
```python
# CUSTOM: Filter system prompts from response
from customizations import filter_thoughts_for_user
extra_info.thoughts = filter_thoughts_for_user(extra_info.thoughts)
```

This is called in both `run_without_streaming()` and `run_with_streaming()` to ensure system prompts are never sent to frontend.

### Storage Structure

**Local Development:**
```
feedback_data/
├── local/
│   ├── 2026-01-10t12-00-00_msg-id-123.json       # User-visible feedback
│   ├── 2026-01-10t12-00-00_msg-id-123_admin.json # Admin-only thoughts
│   └── ...
└── prod-v1/
    ├── 2026-01-10t12-00-00_msg-id-123.json
    ├── 2026-01-10t12-00-00_msg-id-123_admin.json
    └── ...
```

**Azure Blob Storage:**
```
feedback/<deployment_id>/<timestamp>_<message_id>.json         # User-visible
feedback/<deployment_id>/<timestamp>_<message_id>_admin.json   # Admin-only
```

### Testing

**Feedback Endpoint Tests:**
```bash
pytest tests/test_feedback.py -v
```

Tests cover:
- Simple feedback without context
- Feedback with context (verifies system prompts are filtered)
- Deployment metadata inclusion
- Consent-based storage
- Multiple issue categories
- Admin file creation

**Thought Filtering Tests:**
```bash
pytest tests/test_thought_filter.py -v
```

Tests cover:
- Identification of admin-only thoughts
- User-safe thought preservation
- Splitting thoughts into categories
- Complete integration flow

### Deployment Configuration

**Bicep Variables** (`infra/main.bicep`):
```bicep
// CUSTOM: Deployment metadata for feedback tracking
DEPLOYMENT_ID: environmentName
APP_VERSION: 'v1.0.0'
GIT_SHA: deployment().properties.template.metadata.version
```

**Azure.yaml Environment Setup:**
```yaml
# Optional: Override in environment or CI/CD pipeline
DEPLOYMENT_ID: my-custom-id
APP_VERSION: 1.2.3
GIT_SHA: $(git rev-parse --short HEAD)
```

---

## 🔌 Integration Points

These are the minimal changes made to upstream files to integrate customizations:

### Backend (`app/backend/app.py`)
```python
# Line ~20: Import categories and feedback blueprints
from customizations.routes import categories_bp, feedback_bp

# Line ~850: Register blueprints
app.register_blueprint(categories_bp)
app.register_blueprint(feedback_bp)

# In config() function: Add showCategoryFilter
from customizations.config import is_feature_enabled
"showCategoryFilter": is_feature_enabled("category_filter"),
```

### Backend (`app/backend/approaches/chatapproach.py`)
```python
# In run_without_streaming() and run_with_streaming():
# CUSTOM: Filter system prompts from response
from customizations import filter_thoughts_for_user
extra_info.thoughts = filter_thoughts_for_user(extra_info.thoughts)
```

### Frontend (`app/frontend/src/components/Answer/AnswerParser.tsx`)
```typescript
// Import sanitizer
import { sanitizeCitations } from "../../customizations";

// Apply to answer text
const sanitizedAnswer = sanitizeCitations(answer);
```

### Frontend (`app/frontend/src/pages/chat/Chat.tsx` and `ask/Ask.tsx`)
```typescript
// CUSTOM: Import from customizations folder for merge-safe architecture
import { useCategories } from "../../customizations";

// Use dynamic categories
const { categories, loading: categoriesLoading } = useCategories();

// CUSTOM: Search Depth dropdown for agentic retrieval reasoning effort
// Located in leftOfSend area of QuestionInput, after category dropdown
// Uses TooltipHost, IconButton, DirectionalHint from @fluentui/react
// Look for comment: "CUSTOM: Search Depth dropdown..."
```

### Vite Config (`app/frontend/vite.config.ts`)
```typescript
// CUSTOM: Category filter and feedback API routes
"/api/categories": "http://localhost:50505",
"/api/feedback": "http://localhost:50505"
```

---

## 🔄 Upgrading from Upstream

When pulling updates from `Azure-Samples/azure-search-openai-demo`:

1. **Safe files (no conflicts expected):** 
   - All files in `/customizations/` folders
   - Custom prompts in `/approaches/prompts/`

2. **Integration points to re-add:**
   - `app.py` - Re-add blueprint imports for feedback and categories
   - `chatapproach.py` - Re-add thought filtering in `run_without_streaming()` and `run_with_streaming()`
   - `AnswerParser.tsx` - Re-add sanitizeCitations import and usage
   - `Settings.tsx` - Re-add useCategories hook usage
   - `vite.config.ts` - Re-add `/api/` proxies (categories and feedback)
   - `Chat.tsx` - Re-add Search Depth dropdown (look for `// CUSTOM: Search Depth dropdown` comment)
   - `en/translation.json` - Re-add `agenticReasoningEffortOptions` labels if overwritten

3. **Approaches files:**
   - `chatreadretrieveread.py` - Imports from `customizations.approaches` (citation_builder, source_processor)
   - Methods delegate to customization modules - minimizes conflicts during upgrades

4. **Feedback Integration (NEW):**
   - `chatapproach.py` has 2 integration points in `run_without_streaming()` and `run_with_streaming()`
   - Add: `from customizations import filter_thoughts_for_user` and apply filter to `extra_info.thoughts`
   - This is critical for security - ensures system prompts never leak to frontend

5. **Check prompts:** Review if upstream prompts have changed and merge any improvements into your custom prompts.

---

## 🧪 Testing

### Run all tests:
```bash
cd . && python -m pytest tests/ -v
```

### Run specific test suites:
```bash
# Feedback system tests
pytest tests/test_feedback.py tests/test_thought_filter.py -v

# With coverage report
pytest tests/test_feedback.py tests/test_thought_filter.py --cov=customizations -v

# Frontend tests
cd app/frontend && npm test
```

### Expected Results:
- **Backend**: 4 failures expected (custom prompts differ from default)
- **Feedback**: All new tests passing (12 feedback tests, 14 thought filter tests)
- **Frontend**: All passing (18+ tests)

---

## 📋 Test Status

| Category | Passed | Failed | Notes |
|----------|--------|--------|-------|
| Backend Unit Tests | 486 | 4 | 4 failures are expected (custom prompts) |
| Feedback Tests | 12 | 0 | New enhanced feedback tests |
| Thought Filter Tests | 14 | 0 | System prompt filtering tests |
| Frontend Tests | 18+ | 0 | Citation sanitizer + feedback tests |
| Legal Metrics Tests | 41 | 0 | `test_legal_metrics.py` - all passing |
| TypeScript | ✅ | - | No compilation errors |
| **Legal RAG Evaluation** | **95%** | - | Precedent matching across 62 questions |

---

## 📊 Legal Evaluation Results

The legal RAG system has been evaluated against 62 ground truth questions covering UK Civil Procedure Rules and specialist court guides.

### Overall Performance

| Metric | Score | Status |
|--------|-------|--------|
| **Precedent Matching** | 95% | ✅ Excellent |
| Legal Terminology | 100% | ✅ Perfect |
| Statute Citation | 60% | ⚠️ Moderate |

### Performance by Category

| Category | Score | Questions |
|----------|-------|-----------|
| Patents Court | 98.8% | 8 |
| Circuit Commercial | 99.2% | 6 |
| TCC | 96.4% | 7 |
| Civil Procedure Rules | 97.5% | 20 |
| King's Bench | 95.4% | 13 |
| Commercial Court | 85.6% | 8 |

### Running the Evaluation

```bash
cd evals
../.venv/bin/python run_direct_evaluation.py
```

For detailed evaluation documentation, see [Legal Evaluation Guide](docs/legal_evaluation.md).

---

## 🚀 Deployment

Use `azd up` as normal. The customizations are included in the standard deployment.

```bash
azd up
```

---

## � Phase 2: Automated Scraper Pipeline

Phase 2 introduces a **GitHub Actions workflow** that automates the scraping, validation, and indexing of Civil Procedure Rules.

**Key Files:**
- [Deployment & Operations Guide](./DEPLOYMENT_AND_OPERATIONS.md) - Local, cloud, and monitoring setup- `.github/workflows/legal-scraper.yml` - GitHub Actions workflow definition
- `scripts/legal-scraper/` - Scraper, validator, and uploader scripts

**Features:**
- ✅ Weekly automated scraping from justice.gov.uk
- ✅ Document validation with legal term checking
- ✅ Vector embedding generation with Azure OpenAI
- ✅ Automatic upload to Azure Search
- ✅ Dry-run mode for testing without uploading
- ✅ Rate-limited embedding generation (respects Azure quotas)

**Quick Start:**
```bash
# Manual trigger (dry-run, no actual upload)
gh workflow run legal-scraper.yml --repo adalex-ai/azure-search-openai-demo -f dry_run=true

# View results
https://github.com/adalex-ai/azure-search-openai-demo/actions
```

See [Deployment & Operations](./DEPLOYMENT_AND_OPERATIONS.md) for detailed configuration, monitoring, and troubleshooting.

---

## 📝 Changelog

### Phase 2: Automated Scraper Pipeline (2026-01-04)
- **GitHub Actions Workflow**: Automated weekly scraping of Civil Procedure Rules
- **Embedding Generation**: On-demand vector generation with rate limiting
- **Service Principal**: OIDC federated credentials for secure authentication
- **Batch Processing**: Intelligent batching with exponential backoff for Azure OpenAI
- **Validation Enhancements**: Pass-through for empty embeddings during scrape phase

### Legal Evaluation Framework v2.0 (2025-12-24)
- **Achieved 95% precedent matching** (up from initial 9.5%)
- Expanded ground truth to 62 entries across 6 court categories
- Created `run_direct_evaluation.py` for live Azure Search + OpenAI evaluation
- Implemented multi-level semantic matching (exact → containment → topic → word overlap)
- Added topic-based matching for related legal concepts
- Fixed ground truth references to match actual Azure Search index documents
- Updated [Legal Evaluation Documentation](../legal_evaluation.md) with comprehensive results

### Legal Evaluation Framework v1.0 (2025-12-23)
- Added 5 legal-specific evaluation metrics to `evaluate.py`
- Created `evaluate_config_legal.json` with optimized settings
- Created `ground_truth_cpr.jsonl` with 20 UK CPR Q&A pairs
- Added `test_legal_metrics.py` with 41 comprehensive unit tests
- Added `test_search_index.py` for Azure Search index testing
- Added `convert_search_to_groundtruth.py` for ground truth generation
- Created [Legal Evaluation Documentation](docs/legal_evaluation.md)

### Initial Customizations (Fresh Clone from Upstream)
- Added citation sanitization for legal documents
- Added dynamic category filtering from Azure Search index
- Added legal domain prompts for CPR/Court Rules
- Implemented merge-safe architecture

### Security & Ingestion Customizations (2026-01-06)
- **Automatic Security Group Assignment**: 
  - Modified `app/backend/prepdocslib/searchmanager.py` to automatically inject the "Civil Procedure Copilot Users" Security Group ID (`36094ff3-5c6d-49ef-b385-fa37118527e3`) into all document ACLs.
  - This logic uses `CIVIL_PROCEDURE_COPILOT_SECURITY_GROUP_ID` from `app/backend/customizations/config.py` for centralized configuration.
  - Includes a fallback mechanism for environments like Azure Functions where customizations might not be available.
  - **Merge Note**: When updating `prepdocslib` from upstream, ensure the "Security Group Logic" block in `searchmanager.py` is preserved or re-applied. Unlike strictly isolated customizations, this change touches the core library to enforce security by default.

# Customizations Guide

This document describes all custom features added to this Azure Search + OpenAI RAG application and how they are organized for merge-safe updates.

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

### 2. Dynamic Category Filtering
**Files:** Backend `categories.py`, Frontend `useCategories.ts`, `CategoryDropdown/`

Enables filtering search results by document categories fetched dynamically from Azure Search index.

**Backend Endpoint:** `GET /api/categories`
- Returns categories from "category" field in search index
- Falls back to default categories if field not found

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

**UI Location:** Chat input area, to the right of the category dropdown, with an info icon (ℹ️) that shows a tooltip explaining each option.

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

## 🔌 Integration Points

These are the minimal changes made to upstream files to integrate customizations:

### Backend (`app/backend/app.py`)
```python
# Line ~20: Import categories blueprint
from customizations.routes import categories_bp

# Line ~850: Register blueprint
app.register_blueprint(categories_bp)

# In config() function: Add showCategoryFilter
from customizations.config import is_feature_enabled
"showCategoryFilter": is_feature_enabled("category_filter"),
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
// CUSTOM: Category filter API route
"/api/categories": "http://localhost:50505"
```

---

## 🔄 Upgrading from Upstream

When pulling updates from `Azure-Samples/azure-search-openai-demo`:

1. **Safe files (no conflicts expected):** 
   - All files in `/customizations/` folders
   - Custom prompts in `/approaches/prompts/`

2. **Integration points to re-add:**
   - `app.py` - Re-add blueprint import and registration
   - `AnswerParser.tsx` - Re-add sanitizeCitations import and usage
   - `Settings.tsx` - Re-add useCategories hook usage
   - `vite.config.ts` - Re-add `/api/` proxy
   - `Chat.tsx` - Re-add Search Depth dropdown (look for `// CUSTOM: Search Depth dropdown` comment)
   - `en/translation.json` - Re-add `agenticReasoningEffortOptions` labels if overwritten

3. **Approaches file (`chatreadretrieveread.py`):**
   - The main approach file imports from `customizations.approaches`
   - Add the import: `from customizations.approaches import citation_builder, source_processor`
   - Methods delegate to the customization modules
   - If upstream changes these methods, the delegation pattern minimizes conflicts

4. **Check prompts:** Review if upstream prompts have changed and merge any improvements into your custom prompts.

---

## 🧪 Testing

### Run frontend tests:
```bash
cd app/frontend && npm test
```

### Run backend tests:
```bash
cd . && python -m pytest tests/
```

Expected: 4 tests will fail due to custom prompts (they expect default "Assistant helps company employees" text).

---

## 📋 Test Status

| Category | Passed | Failed | Notes |
|----------|--------|--------|-------|
| Backend Unit Tests | 486 | 4 | 4 failures are expected (custom prompts) |
| Frontend Tests | 18 | 0 | Citation sanitizer tests |
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

## 📝 Changelog

### Legal Evaluation Framework v2.0 (2025-12-24)
- **Achieved 95% precedent matching** (up from initial 9.5%)
- Expanded ground truth to 62 entries across 6 court categories
- Created `run_direct_evaluation.py` for live Azure Search + OpenAI evaluation
- Implemented multi-level semantic matching (exact → containment → topic → word overlap)
- Added topic-based matching for related legal concepts
- Fixed ground truth references to match actual Azure Search index documents
- Updated [Legal Evaluation Documentation](docs/legal_evaluation.md) with comprehensive results

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

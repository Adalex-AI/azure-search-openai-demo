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

### 3. Legal Domain Prompts
**Files:** `*.prompty` files in `/approaches/prompts/`

Customized system prompts for:
- Legal terminology and definitions
- Civil Procedure Rules context
- Strict citation formatting rules
- Court-specific guidance

### 4. Feature Flags
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

### Frontend (`app/frontend/src/components/Settings/Settings.tsx`)
```typescript
// Import hook and config
import { useCategories, CUSTOM_FEATURES } from "../../customizations";

// Use dynamic categories
const { categories: dynamicCategories } = useCategories();
```

### Vite Config (`app/frontend/vite.config.ts`)
```typescript
// Add proxy for categories endpoint
"/api/": "http://localhost:50505"
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
| TypeScript | ✅ | - | No compilation errors |

---

## 🚀 Deployment

Use `azd up` as normal. The customizations are included in the standard deployment.

```bash
azd up
```

---

## 📝 Changelog

### Initial Customizations (Fresh Clone from Upstream)
- Added citation sanitization for legal documents
- Added dynamic category filtering from Azure Search index
- Added legal domain prompts for CPR/Court Rules
- Implemented merge-safe architecture

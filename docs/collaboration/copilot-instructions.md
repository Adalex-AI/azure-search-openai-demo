# GitHub Copilot Instructions for Azure Search OpenAI Demo (Legal RAG)

This repository is a customized fork of [Azure-Samples/azure-search-openai-demo](https://github.com/Azure-Samples/azure-search-openai-demo) with legal domain-specific features.

## 🏗️ Architecture Overview

This codebase follows a **merge-safe architecture** where all custom features are isolated in dedicated `/customizations/` folders to prevent conflicts when updating from upstream.

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `app/backend/customizations/` | Backend feature flags, routes, and approach helpers |
| `app/frontend/src/customizations/` | Frontend utilities, hooks, and config |
| `app/backend/approaches/prompts/` | Legal domain prompts (reviewed during upgrades) |

## 📁 Custom Code Locations

### Backend Customizations (`app/backend/customizations/`)

```text
customizations/
├── __init__.py              # Module initialization
├── config.py                # Feature flags (is_feature_enabled)
├── prompt_extensions.py     # Prompt enhancement utilities
├── approaches/              # Legal RAG helpers
│   ├── citation_builder.py  # Enhanced legal citations
│   └── source_processor.py  # Structured source processing
└── routes/
    └── categories.py        # Dynamic /api/categories endpoint
```

### Frontend Customizations (`app/frontend/src/customizations/`)

```text
customizations/
├── index.ts                 # Barrel exports
├── config.ts                # Frontend feature flags
├── citationSanitizer.ts     # Fix malformed citations
├── useCategories.ts         # Dynamic category hook
└── __tests__/               # Unit tests
```

## 🔌 Integration Points

When modifying upstream files, these are the **minimal integration points** that connect customizations:

### Backend (`app/backend/app.py`)

```python
# Import categories blueprint
from customizations.routes import categories_bp

# Register blueprint in create_app()
app.register_blueprint(categories_bp)
```

### Frontend Pages (`app/frontend/src/pages/chat/Chat.tsx`, `ask/Ask.tsx`)

```typescript
// CUSTOM: Import from customizations folder for merge-safe architecture
import { useCategories } from "../../customizations";

// CUSTOM: Search Depth dropdown for agentic retrieval reasoning effort
// Located in leftOfSend area of QuestionInput, after category dropdown
// Uses TooltipHost, IconButton, DirectionalHint from @fluentui/react
```

### Answer Parser (`app/frontend/src/components/Answer/AnswerParser.tsx`)

```typescript
// CUSTOM: Import citation sanitization from isolated customizations folder
import { sanitizeCitations } from "../../customizations/citationSanitizer";
```

### Vite Config (`app/frontend/vite.config.ts`)

```typescript
// CUSTOM: Category filter API route
"/api/categories": "http://localhost:50505"
```

### Approach Files (`app/backend/approaches/*.py`)

```python
# Import legal domain customizations
from customizations.approaches import citation_builder, source_processor
```

## 📝 Coding Guidelines

### When Adding New Features

1. **Always add custom code to `/customizations/` folders**
1. **Use feature flags** in `config.py` (backend) or `config.ts` (frontend)
1. **Minimize changes to upstream files** - only add imports and function calls
1. **Add clear `# CUSTOM:` comments** to mark integration points
1. **Write tests** in `customizations/__tests__/`

### When Modifying Prompts

The prompts in `/approaches/prompts/` are **intentionally NOT in `/customizations/`** because they are core business logic. When upstream updates prompts:

- Review changes manually
- Merge improvements while preserving legal domain customizations
- Keep citation format rules intact

### Feature Flag Pattern

**Backend:**

```python
from customizations.config import is_feature_enabled

if is_feature_enabled("category_filter"):
    # Custom feature code
```

**Frontend:**

```typescript
import { isFeatureEnabled } from "../../customizations";

if (isFeatureEnabled("categoryFilter")) {
    // Custom feature code
}
```

## 🔄 Upgrading from Upstream

When pulling updates from `Azure-Samples/azure-search-openai-demo`:

1. **Safe files (no conflicts expected):**
   - All files in `/customizations/` folders

1. **Integration points to re-add:**
   - `app.py` - Re-add blueprint import and registration
   - `Chat.tsx` & `Ask.tsx` - Re-add useCategories import
   - `AnswerParser.tsx` - Re-add sanitizeCitations import
   - `vite.config.ts` - Re-add `/api/categories` proxy
   - `chatreadretrieveread.py` - Re-add customizations import

1. **Prompts to merge carefully:**
   - Review upstream prompt changes
   - Preserve legal domain terminology and citation rules

## 🧪 Testing

### Run All Tests

```bash
# Frontend tests
cd app/frontend && npm test

# Backend tests  
cd . && python -m pytest tests/

# Integration check
./test_integration.sh
```

### Expected Test Results

- Frontend: All tests should pass
- Backend: 4 failures expected (custom prompts differ from default)

## 📚 Documentation

- `CUSTOMIZATIONS_README.md` - Detailed customization guide
- `AGENTS.md` - Coding agent instructions
- `docs/M365_AGENT_IMPLEMENTATION.md` - M365 integration guide

## ⚠️ Important Notes

1. **Never modify files in `/customizations/` during upstream merges** - these are safe
1. **Keep citation format rules** - legal documents require `[1][2][3]` format
1. **Test after merges** - run `./test_integration.sh` to verify integrations
1. **Commit separately** - keep customization changes separate from upstream updates

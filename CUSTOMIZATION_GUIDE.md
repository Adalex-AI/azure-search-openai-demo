# Customization Guide for Legal Document RAG

This document explains how to maintain your customizations when merging updates from the upstream `azure-search-openai-demo` repository.

## Architecture Overview

Your customizations are isolated in dedicated folders that won't be touched by upstream merges:

```
app/
├── backend/
│   └── customizations/           # ← YOUR BACKEND CUSTOMIZATIONS
│       ├── __init__.py
│       └── prompt_extensions.py  # Citation rules, legal context
│
├── frontend/
│   └── src/
│       └── customizations/       # ← YOUR FRONTEND CUSTOMIZATIONS
│           ├── citationSanitizer.ts
│           └── __tests__/
│               └── citationSanitizer.test.ts
```

## After Merging Upstream Updates

### Step 1: Verify Your Custom Folders Still Exist

```bash
ls app/backend/customizations/
ls app/frontend/src/customizations/
```

### Step 2: Re-integrate Frontend Citation Sanitizer

If `AnswerParser.tsx` was overwritten, add this import at the top:

```typescript
import { sanitizeCitations } from "../../customizations/citationSanitizer";
```

Then find where `answerText` is first used and wrap it:

```typescript
// Before
let parsedAnswer = answerText;

// After  
let parsedAnswer = sanitizeCitations(answerText);
```

### Step 3: Run Tests to Verify

```bash
cd app/frontend
npm test -- --run citationSanitizer
```

### Step 4: Backend Prompt Extensions (Optional)

If you need to enhance prompts programmatically instead of editing prompty files:

```python
from customizations.prompt_extensions import get_legal_enhanced_prompt

# In your approach file
enhanced_prompt = get_legal_enhanced_prompt(base_system_prompt)
```

## What Each Customization Does

### Citation Sanitizer (`citationSanitizer.ts`)

Fixes common LLM citation mistakes:

| Pattern | Problem | Fix |
|---------|---------|-----|
| `1. 1` | Model confuses paragraph numbers with citations | → `[1]` |
| `[1][2][3]` | Multiple adjacent citations | → `[3]` (keeps last) |
| `[1-5]` | Range citations | → `[1]` (first only) |
| `text 1.` | Unbracketed citation at end | → `text.[1]` |

### Prompt Extensions (`prompt_extensions.py`)

Adds rules to system prompts:
- Single source per sentence
- Punctuation before citation
- Prohibited patterns list
- Legal document context

## Updating Prompty Files After Merge

If the `.prompty` files are overwritten, add these rules to the end of the system section:

```
CUSTOM CITATION FORMAT REQUIREMENTS:
- End every sentence with exactly one citation [1], never [1][2]
- Place citations after punctuation: "...rule.[1]" not "...[1] rule."
- Never use ranges like [1-5] or duplicates like "1. 1"
```

## Testing Your Customizations

```bash
# Frontend tests
cd app/frontend
npm test

# Backend tests  
cd ../..
python -m pytest tests/test_chatapproach.py -v
```

## Conflict Resolution Priority

When resolving merge conflicts, prioritize:

1. **Keep upstream infrastructure** (Bicep, CI/CD, dependencies)
2. **Keep your prompty customizations** (citation rules)
3. **Keep your sanitizer imports** in AnswerParser.tsx
4. **Accept upstream UI changes** unless they break citations

## Version Tracking

| Date | Upstream Commit | Notes |
|------|-----------------|-------|
| 2025-12-14 | (initial) | Created isolation architecture |

Update this table after each upstream merge.

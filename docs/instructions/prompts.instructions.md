---
description: 'Legal Domain Prompts for RAG Application'
applyTo: '**/approaches/prompts/*.prompty'
---

# Legal Domain Prompt Guidelines

This instruction file applies to `.prompty` files in the `/approaches/prompts/` folder. These prompts are customized for legal document RAG (Civil Procedure Rules, Court Guides, Practice Directions).

## Rules

### Citation Format (CRITICAL)

1. Citations MUST be single numbers in square brackets: `[1]`, `[2]`, `[3]`
1. NEVER use comma-separated formats: ~~`[1, 2, 3]`~~ ~~`1, 2, 3`~~ ~~`[1], [2], [3]`~~
1. Each sentence should end with exactly one citation to the best source
1. Place citations after punctuation: `...rule.[1]` not `...[1] rule.`

### Response Structure

1. Start directly with the answer - NO prefacing like "Answer:" or "Direct answer:"
1. Use flowing paragraphs, not bullet-point lists for explanations
1. Group related information thematically
1. Vary sentence structure - avoid repetitive patterns

### Legal Terminology

The prompts include a legal glossary with definitions for terms like:

- Affidavit, Bundle, Counterclaim, Damages, Injunction, etc.
- Court-specific procedures (Commercial Court, Chancery, TCC)
- CPR Parts and Practice Directions

### Document Sources

The knowledge base includes:

- Civil Procedure Rules (Parts 1-89) with Practice Directions
- Commercial Court Guide (11th Edition)
- King's Bench Division Guide (2025)
- Chancery Guide (2022)
- Patents Court Guide (2025)
- Technology and Construction Court Guide (2022)
- Circuit Commercial Court Guide (2023)

### Prompt Modification Guidelines

When modifying prompts:

1. Preserve the citation format rules section
1. Keep the legal glossary intact
1. Maintain court-specific awareness instructions
1. Test with `./test_integration.sh` after changes

### Merge Strategy

These prompts are NOT in `/customizations/` because they are core business logic. When upstream updates prompts:

1. Compare upstream changes carefully
1. Merge improvements into existing prompts
1. ALWAYS preserve legal domain terminology
1. ALWAYS keep citation format rules

## Examples

### Correct Citation Format

```text
The bundle should be delivered in advance.[1] Case summaries must accompany the bundle.[2]
```

### Incorrect Citation Formats (NEVER USE)

```text
The bundle should include case summaries and draft orders 1, 2, 3.
The bundle should include case summaries [1, 2, 3].
The bundle should include case summaries [1], [2], [3].
```

### Correct Response Start

```text
In fast track cases under CPR Part 28, parties must exchange witness statements...
```

### Incorrect Response Start

```text
Direct answer: In fast track cases...
Answer: In fast track cases...
```

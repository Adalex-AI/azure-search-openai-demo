---
description: 'Customizations for Legal RAG Application'
applyTo: '**/customizations/**'
---

# Customizations Best Practices

This instruction file applies to all files in `/customizations/` folders. These folders contain merge-safe custom features that should not conflict with upstream updates.

## Rules

### General

1. All custom features MUST be placed in `/customizations/` folders
1. Use feature flags from `config.py` (backend) or `config.ts` (frontend)
1. Export all public APIs through `__init__.py` (backend) or `index.ts` (frontend)
1. Add `# CUSTOM:` comments when integrating into upstream files

### Backend Customizations

1. Place new routes in `customizations/routes/` as Flask Blueprints
1. Place approach helpers in `customizations/approaches/`
1. Use `is_feature_enabled("feature_name")` for conditional features
1. Follow existing patterns in `citation_builder.py` and `source_processor.py`

### Frontend Customizations

1. Export all utilities through `customizations/index.ts`
1. Use `isFeatureEnabled("featureName")` for conditional features
1. Place tests in `customizations/__tests__/`
1. Use TypeScript strict typing

### Citation Format Rules (Legal Domain)

1. Citations MUST use format `[1][2][3]` - single number in brackets
1. Never use comma-separated citations like `[1, 2, 3]` or `1, 2, 3`
1. Each sentence should end with exactly one citation
1. The `sanitizeCitations()` function fixes malformed citations

### Integration Points

When connecting customizations to upstream files:

```python
# Backend: app.py
from customizations.routes import categories_bp
app.register_blueprint(categories_bp)
```

```typescript
// Frontend: Use barrel import
import { useCategories, sanitizeCitations } from "../../customizations";
```

## Glossary

- **Merge-safe**: Code that won't conflict when updating from upstream
- **Feature flag**: Boolean configuration to enable/disable features
- **Barrel export**: Re-exporting modules through index.ts/index.py
- **Integration point**: Minimal code added to upstream files to connect customizations

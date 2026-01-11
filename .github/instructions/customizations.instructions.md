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
from customizations.routes import categories_bp, feedback_bp
app.register_blueprint(categories_bp)
app.register_blueprint(feedback_bp)
```

```typescript
// Frontend: Use barrel import
import { useCategories, sanitizeCitations } from "../../customizations";
```

## Enhanced Feedback System (v1.0)

The enhanced feedback system captures comprehensive deployment metadata and protects system prompts from end users.

### Feedback Features

- **Deployment Tracking**: Captures deployment ID, app version, Git commit hash
- **Thought Filtering**: Automatically filters system prompts from API responses
- **Separate Admin Storage**: Admin-only thoughts stored separately for debugging
- **Consent-Based Context**: Only stores full context when users explicitly consent

### Deployment Metadata

The system automatically tracks:

```python
{
    "deployment_id": "prod-v1",          # From environment or DEPLOYMENT_ID env var
    "app_version": "1.0.0",              # From APP_VERSION env var
    "git_sha": "abc123def456",           # From GIT_SHA env var
    "model_name": "gpt-4",               # From AZURE_OPENAI_CHATGPT_MODEL
    "environment": "production"          # Based on RUNNING_IN_PRODUCTION flag
}
```

### Thought Filtering

The `thought_filter.py` utility automatically:

1. **Removes admin-only thoughts** from API responses sent to users:
   - "Prompt to generate answer" (contains system instructions)
   - Any thought with `raw_messages` (contains system prompts)
1. **Preserves user-safe thoughts**:
   - "Search Query"
   - "Retrieved Documents"
   - Custom analysis steps without system prompts
1. **Maintains admin copies** in separate backend storage for debugging

### Security Model

- **User API Response**: Filtered thoughts, no system prompts
- **Feedback Storage**: User-visible feedback has filtered thoughts, user cannot see system prompts
- **Admin Storage**: Separate `*_admin.json` files contain full thoughts for backend analysis
- **Never Exposed**: System prompts are never sent to users, even via consent flow

## Glossary

- **Merge-safe**: Code that won't conflict when updating from upstream
- **Feature flag**: Boolean configuration to enable/disable features
- **Barrel export**: Re-exporting modules through index.ts/index.py
- **Integration point**: Minimal code added to upstream files to connect customizations
- **Admin-only thought**: Thought step containing sensitive system prompts or LLM internals
- **User-safe thought**: Thought step that is appropriate to display to end users

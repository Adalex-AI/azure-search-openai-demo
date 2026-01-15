# Feedback System Architecture

This document details the optional feedback mechanism integrated into the Legal RAG application. It allows users to rate answers, provide comments, and (optionally) share their conversation context for debugging.

## 🎯 Overview

The feedback system is designed with three core principles:
1.  **Privacy First**: No conversational data is captured unless the user explicitly consents.
2.  **Infrastructure Agnostic**: Data persists to whatever storage is available (Local, Standard Blob, or Data Lake).
3.  **Deploy Traceability**: Every piece of feedback is tagged with the exact deployment ID and commit hash.

## 🏗️ Architecture

```text
┌───────────────────────────┐
│     Frontend UI           │
│  (LegalFeedback.tsx)      │
└────────────┬──────────────┘
             │ 1. User rates "Helpful"/"Unhelpful"
             │ 2. Enters comment & tags issues
             │ 3. User opts-in to Share Context?
             ▼
┌───────────────────────────┐
│   Feedback API POST       │
│     /api/feedback         │
└────────────┬──────────────┘
             │
             ▼
┌──────────────────────────────────────────────┐
│  Backend Processing (routes/feedback.py)     │
│  1. Extract payload                          │
│  2. Filter Sensitive Data                    │
│     - Only include prompt/response if consented |
│  3. Attach Deployment Metadata               │
│     - Deployment ID, Git Commit, Env         │
└────────────┬─────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐      ┌──────────────────────────┐
│  Storage Strategy Selection             │      │  Telemetry (App Insights)│
│  (Dual-Path Persistence)                │◄─────┤  - Truncated events      │
└────────┬──────────────────────┬─────────┘      │  - Usage metrics         │
         │                      │                └──────────────────────────┘
         │ (Strategy A)         │ (Strategy B)
         ▼                      ▼
┌──────────────────┐    ┌─────────────────────┐
│  Azure Blob      │    │  Local Disk         │
│  Storage         │    │  (Dev/Fallback)     │
│                  │    │  /feedback_data/    │
└──────────────────┘    └─────────────────────┘
```

## 🔌 Components

### Frontend (`LegalFeedback.tsx`)
Located in `app/frontend/src/customizations/`.
- **State Management**: Handles the UI flow from thumb-rating to the detail dialog.
- **Privacy Toggle**: Forces the user to make an explicit choice about sharing context.
- **Context Collection**: If consented, bundles:
    - `userPrompt`: The specific question asked.
    - `aiResponse`: The text generated.
    - `thoughts`: The retrieval steps (search queries, citation logic).
    - `conversationHistory`: Previous turns.

### Backend (`routes/feedback.py`)
Located in `app/backend/customizations/routes/`.
- **Deployment Metadata**: Automatically detects if running in Azure Container Apps (`AZURE_ENV_NAME`) or locally, and attaches this to the record.
- **Storage Logic**:
    - **Priority 1 (Enterprise)**: If `USE_USER_UPLOAD` is true, uses the `AZURE_USERSTORAGE_ACCOUNT` (Data Lake Gen2).
    - **Priority 2 (Standard)**: If no user storage, falls back to the main `AZURE_STORAGE_ACCOUNT` (creating a `feedback` container if needed).
    - **Priority 3 (Local)**: If configured for local dev, writes JSON files to `./feedback_data/`.

## 💾 Data Schema

Feedback is stored as JSON files with the following structure:

```json
{
  "event_type": "legal_feedback",
  "context_shared": true,
  "payload": {
    "message_id": "uuid-1234",
    "rating": "unhelpful",
    "issues": ["citation_missing", "incomplete"],
    "comment": "The citation for Part 36 seems wrong."
  },
  "context": {
    "user_prompt": "What is Part 36?",
    "ai_response": "Part 36 deals with...",
    "thoughts": [...]
  },
  "metadata": {
    "deployment_id": "azd-deploy-123",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## 🔧 Configuration

Feature flags in `config.py`:
- `USE_USER_UPLOAD`: Enables using the high-performance Data Lake account for feedback.
- `AZURE_STORAGE_ACCOUNT`: Used as fallback if the specialized user storage is missing.

## 📊 Analytics
Truncated events are sent to **Application Insights** via OpenTelemetry. This allows for creating dashboards that show:
- Happiness Trend (Ratio of Helpful vs Unhelpful)
- Top Issues (e.g., "slow_response" vs "citation_error")
- Volume by Deployment (Did the new release improve feedback?)

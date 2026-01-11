# Agent Implementation Guide

## Legal RAG as an AI Agent (M365 Copilot & Azure AI Foundry)

This document provides comprehensive implementation guides for deploying your Legal RAG solution as:

1. **Microsoft 365 Copilot Declarative Agent** - Integration into Teams, Word, PowerPoint, Outlook
1. **Azure AI Foundry Agent** - Standalone agent with Azure AI Search integration via VS Code extension

Both approaches share the same core components (prompts, citation logic, source processing) while adapting to platform-specific requirements.

***

## Table of Contents

### Part 1: M365 Copilot Agent

1. [Architecture Overview](#architecture-overview)
1. [Comparison: Web App vs M365 Agent](#comparison-web-app-vs-m365-agent)
1. [Shared Components Strategy](#shared-components-strategy)
1. [Implementation Architecture](#implementation-architecture)
1. [Project Structure](#project-structure)
1. [Step-by-Step Implementation](#step-by-step-implementation)
1. [Prompt Sharing Strategy](#prompt-sharing-strategy)
1. [Citation Handling in M365](#citation-handling-in-m365)
1. [Knowledge Sources Configuration](#knowledge-sources-configuration)
1. [API Plugin Development](#api-plugin-development)
1. [Testing Strategy](#testing-strategy)
1. [Deployment Guide](#deployment-guide)

### Part 2: Azure AI Foundry Agent

1. [Azure AI Foundry Overview](#azure-ai-foundry-overview)
1. [Foundry vs M365 Comparison](#foundry-vs-m365-comparison)
1. [Foundry Agent Architecture](#foundry-agent-architecture)
1. [VS Code Extension Setup](#vs-code-extension-setup)
1. [Foundry Agent Implementation](#foundry-agent-implementation)
1. [Azure AI Search Tool Integration](#azure-ai-search-tool-integration)
1. [Foundry Agent Deployment](#foundry-agent-deployment)

### Part 2.5: Converting Foundry Agent to M365 Agent

1. [Foundry-to-M365 Integration Overview](#foundry-to-m365-integration-overview)
1. [API Wrapper for Foundry Agent](#api-wrapper-for-foundry-agent)
1. [M365 API Plugin for Foundry](#m365-api-plugin-for-foundry)
1. [Declarative Agent Manifest for Foundry](#declarative-agent-manifest-for-foundry)
1. [Testing Foundry Agent in M365](#testing-foundry-agent-in-m365)

***

## Architecture Overview

### High-Level Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              SHARED INFRASTRUCTURE                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │                         Azure AI Search Index                                      │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │   │
│  │   │ CPR Parts   │  │ Practice    │  │ Court       │  │ Legal       │            │   │
│  │   │ 1-89        │  │ Directions  │  │ Guides      │  │ Glossary    │            │   │
│  │   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                                │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │                      SHARED COMPONENTS LIBRARY                                     │   │
│  │   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐         │   │
│  │   │ Prompty Files      │  │ Citation Builder   │  │ Source Processor   │         │   │
│  │   │ (.prompty)         │  │ (Python Module)    │  │ (Python Module)    │         │   │
│  │   │                    │  │                    │  │                    │         │   │
│  │   │ • chat_answer_     │  │ • extract_         │  │ • process_         │         │   │
│  │   │   question         │  │   subsection       │  │   documents        │         │   │
│  │   │ • chat_query_      │  │ • build_enhanced_  │  │ • format_sources   │         │   │
│  │   │   rewrite          │  │   citation         │  │ • enrich_metadata  │         │   │
│  │   │ • ask_answer_      │  │ • multi_subsection │  │                    │         │   │
│  │   │   question         │  │   extract          │  │                    │         │   │
│  │   └────────────────────┘  └────────────────────┘  └────────────────────┘         │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                                │
│         ┌────────────────────────────────┴────────────────────────────────┐              │
│         │                                                                  │              │
│         ▼                                                                  ▼              │
│  ┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐      │
│  │      WEB APPLICATION (Current)      │    │      M365 DECLARATIVE AGENT          │      │
│  │                                      │    │                                       │      │
│  │  ┌────────────────────────────────┐ │    │  ┌─────────────────────────────────┐ │      │
│  │  │       React Frontend           │ │    │  │     Microsoft 365 Copilot UI     │ │      │
│  │  │  • Chat Interface              │ │    │  │  • Native M365 Chat Experience   │ │      │
│  │  │  • Citation Panel              │ │    │  │  • Inline Citations              │ │      │
│  │  │  • Supporting Content Tab      │ │    │  │  • Adaptive Cards (optional)     │ │      │
│  │  │  • Developer Settings          │ │    │  │  • Teams/Word/PowerPoint         │ │      │
│  │  └────────────────────────────────┘ │    │  └─────────────────────────────────┘ │      │
│  │              │                       │    │              │                        │      │
│  │              ▼                       │    │              ▼                        │      │
│  │  ┌────────────────────────────────┐ │    │  ┌─────────────────────────────────┐ │      │
│  │  │       Quart Backend            │ │    │  │      API Plugin (REST API)       │ │      │
│  │  │  • /chat endpoint              │ │    │  │  • OpenAPI 3.0 Specification     │ │      │
│  │  │  • ChatReadRetrieveRead        │ │    │  │  • /api/legal/search endpoint    │ │      │
│  │  │  • Azure OpenAI Integration    │ │    │  │  • /api/legal/ask endpoint       │ │      │
│  │  └────────────────────────────────┘ │    │  └─────────────────────────────────┘ │      │
│  │                                      │    │              │                        │      │
│  │  Features:                          │    │  Features:                            │      │
│  │  ✅ Full Citation Panel             │    │  ✅ Core Citations (inline)           │      │
│  │  ✅ Supporting Content Tab          │    │  ❌ No Supporting Content Tab         │      │
│  │  ✅ Developer Settings              │    │  ❌ No Developer Settings             │      │
│  │  ✅ Category Filtering              │    │  ✅ Category via Natural Language     │      │
│  │  ✅ Semantic Ranking Toggle         │    │  ✅ Fixed Optimal Settings           │      │
│  │  ✅ Token Usage Display             │    │  ❌ No Token Display                 │      │
│  └─────────────────────────────────────┘    └─────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

***

## Comparison: Web App vs M365 Agent

| Feature | Web Application | M365 Declarative Agent |
|---------|----------------|------------------------|
| **User Interface** | Custom React UI | Native M365 Copilot UI |
| **Citation Display** | Full panel with source preview | Inline numbered citations |
| **Supporting Content Tab** | ✅ Yes | ❌ Not available |
| **Developer Settings** | ✅ Full control | ❌ Not exposed |
| **Category Filtering** | Dropdown/checkboxes | Natural language in query |
| **Deployment** | Azure App Service | Microsoft AppSource / Admin upload |
| **Authentication** | Azure AD (optional) | Microsoft 365 SSO (automatic) |
| **Data Access** | Azure AI Search direct | Via API Plugin or SharePoint grounding |
| **Prompt Control** | Full custom prompty files | Instructions field (8000 char limit) |
| **Integration** | Standalone web app | Teams, Word, PowerPoint, Outlook |

***

## Shared Components Strategy

### Core Philosophy

The key to maintaining both solutions is a **shared core** with **platform-specific adapters**:

```text
┌──────────────────────────────────────────────────────────────────┐
│                     SHARED CORE (Python Package)                  │
│                                                                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │   Prompts       │ │ CitationBuilder │ │ SourceProcessor │    │
│  │   (*.prompty)   │ │                 │ │                 │    │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘    │
│           │                   │                   │              │
│           └───────────────────┼───────────────────┘              │
│                               │                                   │
└───────────────────────────────┼───────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│   Web Adapter     │ │   M365 Adapter    │ │   Test Adapter    │
│                   │ │                   │ │                   │
│ • Quart routes    │ │ • API Plugin      │ │ • Unit tests      │
│ • Full UI support │ │ • OpenAPI spec    │ │ • Integration     │
│ • Streaming       │ │ • Adaptive Cards  │ │   tests           │
└───────────────────┘ └───────────────────┘ └───────────────────┘
```

### What Gets Shared

| Component | Location | Shared Between |
|-----------|----------|----------------|
| **Prompty Files** | `shared/prompts/` | Web App, M365 Agent |
| **CitationBuilder** | `shared/citation_builder.py` | Web App, M365 Agent |
| **SourceProcessor** | `shared/source_processor.py` | Web App, M365 Agent |
| **Legal Glossary** | `shared/legal_glossary.json` | Web App, M365 Agent |
| **Search Utilities** | `shared/search_utils.py` | Web App, M365 Agent |

### What Differs by Platform

| Aspect | Web App | M365 Agent |
|--------|---------|------------|
| **Response Format** | Streaming JSON with sources array | Structured text with inline [1] citations |
| **Citation Rendering** | React CitationPanel component | M365 Copilot handles rendering |
| **Knowledge Source** | Azure AI Search via SDK | API Plugin or SharePoint grounding |
| **Instructions Delivery** | Prompty files (unlimited) | `instructions` field (8000 chars) |

***

## Implementation Architecture

### M365 Agent Package Structure

```text
m365-legal-agent/
├── appPackage/
│   ├── manifest.json              # App manifest (Teams/M365)
│   ├── declarativeAgent.json      # Agent instructions & capabilities
│   ├── apiPlugin.json             # API plugin definition
│   ├── openapi.yaml               # OpenAPI 3.0 specification
│   ├── color.png                  # 192x192 color icon
│   └── outline.png                # 32x32 outline icon
│
├── api/                           # API Plugin backend
│   ├── __init__.py
│   ├── app.py                     # FastAPI/Flask API server
│   ├── routes/
│   │   ├── search.py              # /api/legal/search endpoint
│   │   └── ask.py                 # /api/legal/ask endpoint
│   └── adapters/
│       └── m365_adapter.py        # Format responses for M365
│
├── shared/                        # ← SYMLINK to shared components
│   ├── prompts/
│   │   ├── chat_answer_question.prompty
│   │   ├── chat_query_rewrite.prompty
│   │   └── ask_answer_question.prompty
│   ├── citation_builder.py
│   ├── source_processor.py
│   └── legal_glossary.json
│
└── tests/
    ├── test_api_plugin.py
    └── test_m365_integration.py
```

***

## Project Structure

### Recommended Monorepo Layout

```text
azure-search-openai-demo-2/
├── app/
│   ├── backend/                   # Existing web app backend
│   │   ├── approaches/
│   │   ├── customizations/        # Existing customizations
│   │   └── ...
│   └── frontend/                  # Existing React frontend
│
├── shared/                        # NEW: Shared components
│   ├── prompts/                   # Move prompty files here
│   │   ├── chat_answer_question.prompty
│   │   ├── chat_query_rewrite.prompty
│   │   ├── chat_query_rewrite_tools.json
│   │   └── ask_answer_question.prompty
│   ├── legal/                     # Legal domain logic
│   │   ├── __init__.py
│   │   ├── citation_builder.py   # Move from customizations
│   │   ├── source_processor.py   # Move from customizations
│   │   └── glossary.json
│   └── __init__.py
│
├── m365-agent/                    # NEW: M365 Agent package
│   ├── appPackage/
│   │   ├── manifest.json
│   │   ├── declarativeAgent.json
│   │   ├── apiPlugin.json
│   │   ├── openapi.yaml
│   │   ├── color.png
│   │   └── outline.png
│   ├── api/
│   │   ├── app.py
│   │   └── ...
│   └── tests/
│
└── docs/
    └── M365_AGENT_IMPLEMENTATION.md  # This document
```

***

## Step-by-Step Implementation

### Phase 1: Extract Shared Components

**Step 1.1: Create shared directory structure**

```bash
mkdir -p shared/prompts shared/legal
```

**Step 1.2: Move prompty files to shared location**

```bash
# Move prompts
cp app/backend/approaches/prompts/*.prompty shared/prompts/
cp app/backend/approaches/prompts/*.json shared/prompts/
```

**Step 1.3: Create shared legal module**

```python
# shared/legal/__init__.py
from .citation_builder import CitationBuilder
from .source_processor import SourceProcessor

__all__ = ['CitationBuilder', 'SourceProcessor']
```

**Step 1.4: Update web app imports**

```python
# app/backend/customizations/approaches/__init__.py
# Option A: Symlink
# Option B: Add shared to PYTHONPATH
# Option C: Install as local package

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from legal import CitationBuilder, SourceProcessor
```

### Phase 2: Create M365 Agent Package

**Step 2.1: Initialize M365 agent project**

```bash
mkdir -p m365-agent/appPackage m365-agent/api/routes
```

**Step 2.2: Create app manifest (`manifest.json`)**

```json
{
    "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.18/MicrosoftTeams.schema.json",
    "manifestVersion": "1.18",
    "version": "1.0.0",
    "id": "YOUR-APP-GUID-HERE",
    "developer": {
        "name": "Your Organization",
        "websiteUrl": "https://your-domain.com",
        "privacyUrl": "https://your-domain.com/privacy",
        "termsOfUseUrl": "https://your-domain.com/terms"
    },
    "icons": {
        "color": "color.png",
        "outline": "outline.png"
    },
    "name": {
        "short": "Legal CPR Assistant",
        "full": "Civil Procedure Rules Legal Research Assistant"
    },
    "description": {
        "short": "Expert legal assistant for CPR, Practice Directions, and Court Guides",
        "full": "An AI-powered legal research assistant that helps lawyers and legal professionals in England and Wales find accurate information about Civil Procedure Rules (CPR), Practice Directions, and Court Guides including Commercial Court, King's Bench, Chancery, Patents, TCC, and Circuit Commercial Court."
    },
    "accentColor": "#1a365d",
    "copilotAgents": {
        "declarativeAgents": [
            {
                "id": "legalCPRAgent",
                "file": "declarativeAgent.json"
            }
        ]
    }
}
```

**Step 2.3: Create declarative agent manifest (`declarativeAgent.json`)**

```json
{
    "$schema": "https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.2/schema.json",
    "version": "v1.2",
    "name": "Legal CPR Assistant",
    "description": "Expert legal assistant for Civil Procedure Rules, Practice Directions, and Court Guides in England and Wales",
    "instructions": "You are an expert legal assistant helping lawyers and legal professionals in England and Wales with questions about the Civil Procedure Rules (CPR), Practice Directions, and Court Guides.\n\nDOCUMENT STRUCTURE AWARENESS:\nThe knowledge base contains documents from:\n- Civil Procedure Rules (Parts 1-89) and associated Practice Directions\n- Commercial Court Guide (11th Edition, July 2023)\n- King's Bench Division Guide (2025 Edition)\n- Chancery Guide (2022)\n- Patents Court Guide (February 2025)\n- Technology and Construction Court Guide (October 2022)\n- Circuit Commercial Court Guide (August 2023)\n\nWhen answering questions:\n- Court Guides may provide specialized procedures that supplement or modify general CPR rules\n- Practice Directions provide detailed implementation guidance for CPR Parts\n- Consider both the general rule (CPR) and any court-specific variations when applicable\n\nIMPORTANT CONTEXT AWARENESS:\n- If the user asks about a specific court, prioritize information specific to that court\n- If no specific court is mentioned, focus on general Civil Procedure Rules\n- Always note when rules or procedures are court-specific versus generally applicable\n\nCITATION REQUIREMENTS:\n- Every sentence must end with a numbered citation [1], [2], [3], etc.\n- Use only one citation per sentence\n- Reference the search results using their index numbers\n\nLEGAL TERMINOLOGY:\n- Affidavit: A written, sworn statement of evidence\n- Counterclaim: A claim brought by a defendant in response to the claimant's claim\n- Disclosure: The process of parties revealing documents to each other\n- Injunction: A court order prohibiting or requiring an action\n- Stay: A halt on proceedings\n- Strike out: Court ordering material to be deleted\n- Without prejudice: Settlement negotiations protected from disclosure",
    "capabilities": [
        {
            "name": "OneDriveAndSharePoint",
            "items_by_url": [
                {
                    "url": "https://YOUR-TENANT.sharepoint.com/sites/LegalDocuments"
                }
            ]
        }
    ],
    "conversation_starters": [
        {
            "title": "Disclosure Requirements",
            "text": "What are the standard disclosure requirements under CPR Part 31?"
        },
        {
            "title": "Commercial Court Procedures",
            "text": "What are the key procedures specific to the Commercial Court?"
        },
        {
            "title": "Fast Track Claims",
            "text": "What is the fast track and what types of claims are allocated to it?"
        },
        {
            "title": "Summary Judgment",
            "text": "When can a party apply for summary judgment and what is the test?"
        },
        {
            "title": "Witness Statements",
            "text": "What are the requirements for witness statements under CPR Part 32?"
        },
        {
            "title": "Costs Management",
            "text": "When is costs management required and how does costs budgeting work?"
        }
    ],
    "actions": [
        {
            "id": "legalSearchPlugin",
            "file": "apiPlugin.json"
        }
    ]
}
```

### Phase 3: Create API Plugin

**Step 3.1: Create API plugin manifest (`apiPlugin.json`)**

```json
{
    "$schema": "https://developer.microsoft.com/json-schemas/copilot/plugin/v2.2/schema.json",
    "schema_version": "v2.2",
    "name_for_human": "Legal CPR Search",
    "description_for_human": "Search Civil Procedure Rules, Practice Directions, and Court Guides",
    "description_for_model": "Use this plugin to search for information about Civil Procedure Rules (CPR), Practice Directions, and Court Guides for England and Wales courts. Call this when users ask about legal procedures, court rules, or specific CPR Parts.",
    "contact_email": "legal-support@your-domain.com",
    "namespace": "legalCPR",
    "logo_url": "https://your-api-domain.com/logo.png",
    "legal_info_url": "https://your-domain.com/legal",
    "privacy_policy_url": "https://your-domain.com/privacy",
    "runtimes": [
        {
            "type": "OpenApi",
            "auth": {
                "type": "None"
            },
            "run_for_functions": ["searchLegalDocuments", "askLegalQuestion"],
            "spec": {
                "url": "https://your-api-domain.com/openapi.yaml"
            }
        }
    ],
    "functions": [
        {
            "name": "searchLegalDocuments",
            "description": "Search the legal knowledge base for CPR rules, Practice Directions, and Court Guides",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for legal documents"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["Civil Procedure Rules and Practice Directions", "Commercial Court", "King's Bench Division", "Chancery Division", "Patents Court", "Technology and Construction Court", "Circuit Commercial Court"],
                        "description": "Optional: Filter by document category/court"
                    },
                    "top": {
                        "type": "integer",
                        "default": 5,
                        "description": "Number of results to return"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "askLegalQuestion",
            "description": "Ask a question about Civil Procedure Rules and get a cited answer",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The legal question to answer"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["Civil Procedure Rules and Practice Directions", "Commercial Court", "King's Bench Division", "Chancery Division", "Patents Court", "Technology and Construction Court", "Circuit Commercial Court"],
                        "description": "Optional: Focus on a specific court or category"
                    }
                },
                "required": ["question"]
            }
        }
    ]
}
```

**Step 3.2: Create OpenAPI specification (`openapi.yaml`)**

```yaml
openapi: 3.0.3
info:
  title: Legal CPR Search API
  description: API for searching Civil Procedure Rules, Practice Directions, and Court Guides
  version: 1.0.0
servers:
  - url: https://your-api-domain.com/api
    description: Production API

paths:
  /legal/search:
    post:
      operationId: searchLegalDocuments
      summary: Search legal documents
      description: Search the knowledge base for CPR rules, Practice Directions, and Court Guides
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - query
              properties:
                query:
                  type: string
                  description: Search query
                category:
                  type: string
                  description: Filter by category
                top:
                  type: integer
                  default: 5
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                type: object
                properties:
                  results:
                    type: array
                    items:
                      type: object
                      properties:
                        index:
                          type: integer
                        title:
                          type: string
                        content:
                          type: string
                        source:
                          type: string
                        category:
                          type: string

  /legal/ask:
    post:
      operationId: askLegalQuestion
      summary: Ask a legal question
      description: Get a cited answer to a legal question about CPR
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - question
              properties:
                question:
                  type: string
                category:
                  type: string
      responses:
        '200':
          description: Answer with citations
          content:
            application/json:
              schema:
                type: object
                properties:
                  answer:
                    type: string
                    description: The answer with inline [1] citations
                  sources:
                    type: array
                    items:
                      type: object
                      properties:
                        index:
                          type: integer
                        title:
                          type: string
                        content:
                          type: string
```

### Phase 4: Implement API Backend

**Step 4.1: Create FastAPI application (`api/app.py`)**

```python
"""
Legal CPR API Plugin Backend

This API serves as the backend for the M365 Declarative Agent,
providing search and Q&A capabilities for legal documents.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from legal import CitationBuilder, SourceProcessor
from prompts import load_prompty

app = FastAPI(
    title="Legal CPR Search API",
    description="API for M365 Copilot Legal Agent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize shared components
citation_builder = CitationBuilder()
source_processor = SourceProcessor(citation_builder)

class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    top: int = 5

class AskRequest(BaseModel):
    question: str
    category: Optional[str] = None

class SearchResult(BaseModel):
    index: int
    title: str
    content: str
    source: str
    category: str

class SearchResponse(BaseModel):
    results: List[SearchResult]

class AskResponse(BaseModel):
    answer: str
    sources: List[SearchResult]

@app.post("/api/legal/search", response_model=SearchResponse)
async def search_legal_documents(request: SearchRequest):
    """
    Search the legal knowledge base.

    Uses the same Azure AI Search index as the web application.
    """
    try:
        # TODO: Implement Azure AI Search query
        # This uses the same search logic as the web app
        results = await perform_search(
            query=request.query,
            category=request.category,
            top=request.top
        )

        # Format results using shared SourceProcessor
        formatted = []
        for i, doc in enumerate(results):
            citation = citation_builder.build_enhanced_citation(doc, i + 1)
            formatted.append(SearchResult(
                index=i + 1,
                title=citation,
                content=doc.content[:500],  # Truncate for API response
                source=doc.sourcefile,
                category=doc.category
            ))

        return SearchResponse(results=formatted)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/legal/ask", response_model=AskResponse)
async def ask_legal_question(request: AskRequest):
    """
    Answer a legal question with citations.

    Uses the same prompty files and approach as the web application.
    """
    try:
        # TODO: Implement full RAG pipeline
        # 1. Search for relevant documents
        # 2. Load prompty and generate answer
        # 3. Return answer with inline citations

        answer, sources = await generate_answer(
            question=request.question,
            category=request.category
        )

        return AskResponse(answer=answer, sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

***

## Prompt Sharing Strategy

### How Prompts Are Used in Each Platform

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                            PROMPT FLOW                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  SHARED PROMPTY FILES (shared/prompts/)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  chat_answer_question.prompty                                        │    │
│  │  • System prompt with legal context                                  │    │
│  │  • Citation requirements                                             │    │
│  │  • Document structure awareness                                      │    │
│  │  • Legal terminology glossary                                        │    │
│  │  • Output format requirements                                        │    │
│  └────────────────────────────┬────────────────────────────────────────┘    │
│                               │                                              │
│           ┌───────────────────┴───────────────────┐                         │
│           │                                       │                         │
│           ▼                                       ▼                         │
│  ┌─────────────────────────────┐     ┌─────────────────────────────┐       │
│  │     WEB APPLICATION         │     │     M365 AGENT              │       │
│  │                             │     │                             │       │
│  │  Uses FULL prompty file:    │     │  Uses CONDENSED version:    │       │
│  │  • Load via prompty lib     │     │  • 8000 char limit          │       │
│  │  • Dynamic system prompt    │     │  • Core instructions only   │       │
│  │  • All glossary terms       │     │  • Key glossary terms       │       │
│  │  • Full citation rules      │     │  • Simplified format rules  │       │
│  │                             │     │                             │       │
│  │  Prompt delivery:           │     │  Prompt delivery:           │       │
│  │  → Azure OpenAI API         │     │  → declarativeAgent.json    │       │
│  │    (system message)         │     │    (instructions field)     │       │
│  └─────────────────────────────┘     └─────────────────────────────┘       │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Prompt Synchronization Script

```python
# scripts/sync_prompts_to_m365.py
"""
Synchronize prompty files to M365 agent instructions field.

This script extracts the core instructions from the full prompty files
and formats them for the 8000 character limit of M365 agents.
"""

import yaml
import re
from pathlib import Path

MAX_INSTRUCTIONS_LENGTH = 8000

def extract_core_instructions(prompty_path: Path) -> str:
    """Extract and condense instructions from prompty file."""
    content = prompty_path.read_text()

    # Parse YAML front matter
    parts = content.split('---')
    if len(parts) >= 3:
        # Skip front matter, get template
        template = '---'.join(parts[2:]).strip()
    else:
        template = content

    # Remove Jinja conditionals for M365 (use default behavior)
    template = re.sub(r'{%.*?%}', '', template)
    template = re.sub(r'{{.*?}}', '', template)

    # Remove sections that don't apply to M365
    # (e.g., override_prompt handling, vision-specific content)

    # Condense to fit within limit
    if len(template) > MAX_INSTRUCTIONS_LENGTH:
        # Prioritize core content
        # Remove examples, keep rules
        template = condense_instructions(template)

    return template[:MAX_INSTRUCTIONS_LENGTH]

def update_declarative_agent(agent_path: Path, instructions: str):
    """Update the declarativeAgent.json with new instructions."""
    import json

    agent = json.loads(agent_path.read_text())
    agent['instructions'] = instructions
    agent_path.write_text(json.dumps(agent, indent=2))
    print(f"Updated {agent_path} with {len(instructions)} character instructions")

if __name__ == "__main__":
    prompty_path = Path("shared/prompts/chat_answer_question.prompty")
    agent_path = Path("m365-agent/appPackage/declarativeAgent.json")

    instructions = extract_core_instructions(prompty_path)
    update_declarative_agent(agent_path, instructions)
```

***

## Citation Handling in M365

### Citation Format Differences

| Aspect | Web Application | M365 Agent |
|--------|----------------|------------|
| **Format** | `[Document Title, Section (p. X), Source]` | `[1]`, `[2]`, `[3]` (simple numbers) |
| **Rendering** | Custom React CitationPanel | M365 Copilot native |
| **Click Action** | Opens document in panel | Limited/varies by context |
| **Metadata** | Full structured object | Index reference only |

### M365 Citation Adapter

```python
# m365-agent/api/adapters/m365_adapter.py
"""
Adapter to format citations for M365 Copilot responses.
"""

from typing import List, Dict, Any

class M365CitationAdapter:
    """
    Converts full citation objects to M365-compatible format.

    M365 Copilot expects:
    - Inline numbered citations [1], [2], [3]
    - Sources returned separately for reference
    """

    def format_response(
        self,
        answer: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Format answer and sources for M365 API response.

        Args:
            answer: The generated answer text with citations
            sources: List of source documents

        Returns:
            M365-compatible response structure
        """
        return {
            "answer": answer,
            "sources": [
                {
                    "index": i + 1,
                    "title": self._build_title(src),
                    "content": src.get("content", "")[:500],
                    "url": src.get("storageUrl", "")
                }
                for i, src in enumerate(sources)
            ]
        }

    def _build_title(self, source: Dict[str, Any]) -> str:
        """Build a readable title from source metadata."""
        parts = []

        if source.get("subsection"):
            parts.append(source["subsection"])

        if source.get("sourcepage"):
            parts.append(source["sourcepage"])

        if source.get("sourcefile"):
            parts.append(source["sourcefile"])

        return ", ".join(parts) if parts else "Source"
```

***

## Knowledge Sources Configuration

### Option A: SharePoint Grounding (Recommended for Simple Setups)

Upload legal documents to SharePoint and configure grounding:

```json
{
    "capabilities": [
        {
            "name": "OneDriveAndSharePoint",
            "items_by_url": [
                {
                    "url": "https://contoso.sharepoint.com/sites/LegalDocs/CPR"
                },
                {
                    "url": "https://contoso.sharepoint.com/sites/LegalDocs/CourtGuides"
                }
            ]
        }
    ]
}
```

**Pros:**

- No API backend needed
- Microsoft handles indexing and search
- Automatic updates when documents change

**Cons:**

- Less control over chunking/embeddings
- Limited to SharePoint document formats
- No custom search ranking

### Option B: API Plugin (Recommended for This Project)

Use the existing Azure AI Search index via API Plugin:

```json
{
    "capabilities": [],
    "actions": [
        {
            "id": "legalSearchPlugin",
            "file": "apiPlugin.json"
        }
    ]
}
```

**Pros:**

- Reuse existing Azure AI Search index
- Full control over search and ranking
- Consistent results with web app
- Custom citation building

**Cons:**

- Requires hosting API backend
- Additional infrastructure cost
- More complex deployment

### Option C: Hybrid Approach

Combine SharePoint grounding for general documents with API Plugin for specialized search:

```json
{
    "capabilities": [
        {
            "name": "OneDriveAndSharePoint",
            "items_by_url": [
                {
                    "url": "https://contoso.sharepoint.com/sites/LegalDocs/General"
                }
            ]
        }
    ],
    "actions": [
        {
            "id": "legalSearchPlugin",
            "file": "apiPlugin.json"
        }
    ]
}
```

***

## Testing Strategy

### Test Matrix

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TESTING STRATEGY                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LAYER 1: SHARED COMPONENTS (Unit Tests)                                    │
│  ├── Citation Builder                                                        │
│  │   ├── test_extract_subsection()                                          │
│  │   ├── test_build_enhanced_citation()                                     │
│  │   └── test_multi_subsection_extraction()                                 │
│  └── Source Processor                                                        │
│      ├── test_process_documents()                                           │
│      └── test_format_for_m365()                                             │
│                                                                              │
│  LAYER 2: API PLUGIN (Integration Tests)                                    │
│  ├── test_search_endpoint()                                                 │
│  ├── test_ask_endpoint()                                                    │
│  └── test_error_handling()                                                  │
│                                                                              │
│  LAYER 3: M365 AGENT (E2E Tests)                                            │
│  ├── Test in Teams Developer Portal                                         │
│  ├── Test conversation starters                                             │
│  └── Test citation display                                                  │
│                                                                              │
│  LAYER 4: CROSS-PLATFORM (Parity Tests)                                     │
│  ├── Same query → Same sources retrieved                                    │
│  └── Citation accuracy comparison                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Shared Component Tests

```python
# tests/shared/test_citation_builder.py
import pytest
from shared.legal import CitationBuilder

class TestCitationBuilder:
    @pytest.fixture
    def builder(self):
        return CitationBuilder()

    def test_extract_subsection_from_content(self, builder):
        """Test subsection extraction from document content."""
        class MockDoc:
            content = "1.1 Filing requirements for disclosure..."
            sourcepage = "PD31-1.1"
            sourcefile = "Practice Direction 31"

        subsection = builder.extract_subsection(MockDoc())
        assert subsection == "1.1"

    def test_build_enhanced_citation(self, builder):
        """Test full citation building."""
        class MockDoc:
            content = "A4.1 The Commercial Court requires..."
            sourcepage = "A4.1"
            sourcefile = "Commercial Court Guide"

        citation = builder.build_enhanced_citation(MockDoc(), 1)
        assert "A4.1" in citation
        assert "Commercial Court Guide" in citation
```

### API Plugin Tests

```python
# tests/m365/test_api_plugin.py
import pytest
from fastapi.testclient import TestClient
from m365_agent.api.app import app

client = TestClient(app)

def test_search_endpoint():
    """Test the search endpoint returns properly formatted results."""
    response = client.post("/api/legal/search", json={
        "query": "disclosure requirements fast track",
        "top": 3
    })

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) <= 3

    for result in data["results"]:
        assert "index" in result
        assert "title" in result
        assert "content" in result

def test_ask_endpoint():
    """Test the ask endpoint returns answer with citations."""
    response = client.post("/api/legal/ask", json={
        "question": "What are the disclosure requirements?"
    })

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data

    # Verify citations are present
    assert "[1]" in data["answer"]
```

***

## Deployment Guide

### Prerequisites

1. **Microsoft 365 Copilot License** - Required for testing and deployment
1. **Azure Subscription** - For hosting API Plugin backend
1. **Teams Admin Access** - For sideloading during development
1. **Microsoft 365 Agents Toolkit** - VS Code extension for development

### Deployment Steps

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT WORKFLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STEP 1: Deploy API Backend                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  $ cd m365-agent/api                                                 │   │
│  │  $ az webapp up --name legal-cpr-api --resource-group your-rg       │   │
│  │                                                                      │   │
│  │  Configure:                                                          │   │
│  │  • AZURE_SEARCH_ENDPOINT                                            │   │
│  │  • AZURE_SEARCH_KEY                                                 │   │
│  │  • AZURE_OPENAI_ENDPOINT                                            │   │
│  │  • AZURE_OPENAI_KEY                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                              │
│                               ▼                                              │
│  STEP 2: Update OpenAPI Spec with API URL                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  # openapi.yaml                                                      │   │
│  │  servers:                                                            │   │
│  │    - url: https://legal-cpr-api.azurewebsites.net/api               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                              │
│                               ▼                                              │
│  STEP 3: Package Agent                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  $ cd m365-agent/appPackage                                          │   │
│  │  $ zip -r legal-cpr-agent.zip manifest.json declarativeAgent.json \ │   │
│  │        apiPlugin.json openapi.yaml color.png outline.png            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                              │
│                               ▼                                              │
│  STEP 4: Deploy to M365                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Option A: Sideload for Testing                                      │   │
│  │  • Open Teams → Apps → Manage your apps → Upload custom app         │   │
│  │                                                                      │   │
│  │  Option B: Admin Upload                                              │   │
│  │  • Microsoft 365 Admin Center → Integrated Apps → Upload            │   │
│  │                                                                      │   │
│  │  Option C: AppSource (Public)                                        │   │
│  │  • Partner Center → Submit for certification                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                              │
│                               ▼                                              │
│  STEP 5: Test in Microsoft 365 Copilot                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Go to https://m365.cloud.microsoft/chat                         │   │
│  │  2. Open conversation drawer                                         │   │
│  │  3. Select "Legal CPR Assistant"                                     │   │
│  │  4. Try conversation starters                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Environment Configuration

```bash
# m365-agent/api/.env

# Azure AI Search (same as web app)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=your-index-name

# Azure OpenAI (same as web app)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# M365 specific
M365_APP_ID=your-app-guid
```

***

## Summary: What You Get

| Capability | Web App | M365 Agent |
|------------|---------|------------|
| **Chat with legal knowledge** | ✅ | ✅ |
| **Accurate citations** | ✅ Full panel | ✅ Inline [1] format |
| **Same underlying data** | ✅ Azure AI Search | ✅ Via API Plugin |
| **Same prompts (core)** | ✅ Full prompty | ✅ Condensed instructions |
| **Same citation logic** | ✅ CitationBuilder | ✅ CitationBuilder |
| **Supporting content tab** | ✅ | ❌ |
| **Developer settings** | ✅ | ❌ |
| **Token usage display** | ✅ | ❌ |
| **Teams integration** | ❌ | ✅ |
| **Word/PowerPoint integration** | ❌ | ✅ |
| **Native M365 experience** | ❌ | ✅ |

***

## Next Steps

1. **Phase 1 (Week 1):** Extract shared components and restructure repository
1. **Phase 2 (Week 2):** Create M365 agent package structure and manifests
1. **Phase 3 (Week 3):** Implement API Plugin backend with shared components
1. **Phase 4 (Week 4):** Testing and deployment

***

***

# Part 2: Azure AI Foundry Agent

***

## Azure AI Foundry Overview

Azure AI Foundry (formerly Azure AI Studio) provides a unified platform for building, deploying, and managing AI agents. The **Foundry Agent Service** enables you to create production-ready agents with built-in orchestration, tool calling, and observability.

### What is Foundry Agent Service?

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           AZURE AI FOUNDRY AGENT SERVICE                                 │
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              FOUNDRY AGENT                                        │   │
│  │                                                                                   │   │
│  │    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                     │   │
│  │    │    MODEL     │    │ INSTRUCTIONS │    │    TOOLS     │                     │   │
│  │    │              │    │              │    │              │                     │   │
│  │    │  GPT-4o      │    │  Legal CPR   │    │ • Azure AI   │                     │   │
│  │    │  GPT-4       │    │  Prompts     │    │   Search     │                     │   │
│  │    │  Llama       │    │              │    │ • Bing       │                     │   │
│  │    │              │    │              │    │ • Functions  │                     │   │
│  │    └──────────────┘    └──────────────┘    │ • OpenAPI    │                     │   │
│  │                                             └──────────────┘                     │   │
│  └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                              │
│                                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                         FOUNDRY RUNTIME                                           │   │
│  │                                                                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │   │
│  │  │ Conversation│  │ Tool        │  │ Content     │  │ Observability│           │   │
│  │  │ Management  │  │ Orchestration│ │ Safety      │  │ & Logging   │           │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Models** | GPT-4o, GPT-4, GPT-3.5, Llama, and other LLMs |
| **Tools** | Azure AI Search, Bing, Azure Functions, OpenAPI, Code Interpreter |
| **Orchestration** | Server-side tool execution with automatic retry |
| **Observability** | Full conversation traceability, Application Insights integration |
| **Security** | Microsoft Entra ID, RBAC, content filters, encryption |
| **VS Code Integration** | Build and test agents directly from VS Code |

***

## Foundry vs M365 Comparison

| Aspect | M365 Declarative Agent | Azure AI Foundry Agent |
|--------|----------------------|------------------------|
| **Platform** | Microsoft 365 Copilot | Azure AI Foundry Portal / SDK |
| **Runtime** | Microsoft 365 Copilot orchestrator | Foundry Agent Service |
| **Development** | Manifest JSON files + API Plugin | Python/C#/TypeScript SDK or Portal |
| **VS Code Extension** | M365 Agents Toolkit | Azure AI Foundry extension |
| **Knowledge Sources** | SharePoint, OneDrive, Graph Connectors | Azure AI Search, Bing, Custom APIs |
| **Tool Execution** | Client-side (API Plugin) | Server-side (Foundry runtime) |
| **Deployment** | Teams App Store / Admin upload | Azure resource deployment |
| **Authentication** | Microsoft 365 SSO | Azure AD / API Keys |
| **Cost Model** | M365 Copilot license | Azure consumption-based |
| **Best For** | M365 ecosystem users | Custom enterprise applications |

### When to Choose Each Platform

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        DECISION MATRIX: WHICH PLATFORM?                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  CHOOSE M365 COPILOT AGENT WHEN:              CHOOSE AZURE AI FOUNDRY WHEN:             │
│  ├── Users primarily work in Teams/Office     ├── Building custom chat applications     │
│  ├── Need native M365 integration             ├── Need full control over orchestration  │
│  ├── Want simple SharePoint grounding         ├── Using existing Azure AI Search index  │
│  ├── Organization has M365 Copilot licenses   ├── Need advanced observability/tracing   │
│  └── Prefer no-code/low-code approach         └── Building multi-agent systems          │
│                                                                                          │
│  CHOOSE BOTH WHEN:                                                                       │
│  ├── Want to reach users in M365 AND standalone apps                                    │
│  ├── Have shared knowledge base in Azure AI Search                                      │
│  └── Need consistent behavior across platforms                                          │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

***

## Foundry Agent Architecture

### Architecture with Shared Components

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              SHARED INFRASTRUCTURE                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │                         Azure AI Search Index                                      │   │
│  │                    (Same index used by Web App & M365)                            │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                                │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │                      SHARED COMPONENTS                                              │   │
│  │   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐         │   │
│  │   │ Prompty Files      │  │ CitationBuilder    │  │ SourceProcessor    │         │   │
│  │   └────────────────────┘  └────────────────────┘  └────────────────────┘         │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                                │
│         ┌────────────────────────────────┼────────────────────────────────┐              │
│         │                                │                                │              │
│         ▼                                ▼                                ▼              │
│  ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐             │
│  │    WEB APP        │    │   M365 AGENT      │    │ FOUNDRY AGENT     │             │
│  │                   │    │                   │    │                   │             │
│  │  Quart Backend    │    │  API Plugin +     │    │  Python SDK +     │             │
│  │  React Frontend   │    │  Declarative      │    │  Azure AI Search  │             │
│  │                   │    │  Manifest         │    │  Tool             │             │
│  │                   │    │                   │    │                   │             │
│  │  Features:        │    │  Features:        │    │  Features:        │             │
│  │  ✅ Full UI       │    │  ✅ Teams/Word    │    │  ✅ Playground    │             │
│  │  ✅ All settings  │    │  ✅ M365 native   │    │  ✅ API access    │             │
│  │  ✅ Streaming     │    │  ❌ No settings   │    │  ✅ Multi-agent   │             │
│  └───────────────────┘    └───────────────────┘    └───────────────────┘             │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

***

## VS Code Extension Setup

### Prerequisites

1. **Azure Subscription** with appropriate permissions
1. **VS Code** with Azure AI Foundry extension
1. **Python 3.10+** (for SDK development)
1. **Existing Azure AI Search index** (from your current deployment)

### Installing the Azure AI Foundry Extension

1. Open VS Code
1. Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
1. Search for "Azure AI Foundry" or "Azure AI"
1. Install the extension

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         VS CODE AZURE AI FOUNDRY EXTENSION                               │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  EXTENSION CAPABILITIES:                                                                 │
│  ├── Create and manage Foundry projects                                                │
│  ├── Design agents with visual editor                                                   │
│  ├── Connect to Azure AI Search indexes                                                 │
│  ├── Test agents in playground                                                          │
│  ├── Deploy agents to Azure                                                             │
│  └── View traces and logs                                                               │
│                                                                                          │
│  WORKFLOW:                                                                               │
│  1. Sign in to Azure                                                                     │
│  2. Select/create Foundry project                                                        │
│  3. Create new agent                                                                     │
│  4. Add Azure AI Search tool                                                            │
│  5. Configure instructions (use shared prompts)                                         │
│  6. Test in playground                                                                   │
│  7. Deploy                                                                               │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

***

## Foundry Agent Implementation

### Project Structure for Foundry Agent

```text
azure-search-openai-demo-2/
├── shared/                        # Shared with Web App & M365 Agent
│   ├── prompts/
│   │   ├── chat_answer_question.prompty
│   │   └── ...
│   └── legal/
│       ├── citation_builder.py
│       └── source_processor.py
│
├── foundry-agent/                 # NEW: Foundry Agent
│   ├── agent_config.yaml          # Agent configuration
│   ├── agent.py                   # Main agent implementation
│   ├── tools/
│   │   ├── legal_search.py        # Azure AI Search tool wrapper
│   │   └── citation_processor.py  # Citation formatting
│   ├── tests/
│   │   └── test_agent.py
│   └── requirements.txt
│
└── ...
```

### Step 1: Create Foundry Project and Agent (Portal Method)

1. **Go to Azure AI Foundry Portal**: https://ai.azure.com
1. **Create an Agent**:
   - Click "Create an agent" from the home page
   - Enter project name: "Legal-CPR-Agent"
   - Wait for resources to provision (gpt-4o will be auto-deployed)

1. **Configure Agent Instructions**:

   Paste the condensed version of your legal prompts:

```text
You are an expert legal assistant helping lawyers and legal professionals in England and Wales with questions about the Civil Procedure Rules (CPR), Practice Directions, and Court Guides.

DOCUMENT STRUCTURE AWARENESS:
The knowledge base contains documents from:
- Civil Procedure Rules (Parts 1-89) and associated Practice Directions
- Commercial Court Guide (11th Edition, July 2023)
- King's Bench Division Guide (2025 Edition)
- Chancery Guide (2022)
- Patents Court Guide (February 2025)
- Technology and Construction Court Guide (October 2022)
- Circuit Commercial Court Guide (August 2023)

When answering questions:
- Court Guides may provide specialized procedures that supplement or modify general CPR rules
- Practice Directions provide detailed implementation guidance for CPR Parts
- Consider both the general rule (CPR) and any court-specific variations when applicable

IMPORTANT CONTEXT AWARENESS:
- If the user asks about a specific court, prioritize information specific to that court
- If no specific court is mentioned, focus on general Civil Procedure Rules
- Always note when rules or procedures are court-specific versus generally applicable

CITATION REQUIREMENTS:
- Every sentence must end with a numbered citation [1], [2], [3], etc.
- Reference search results using their index numbers
- Use one citation per sentence

LEGAL TERMINOLOGY:
- Affidavit: A written, sworn statement of evidence
- Counterclaim: A claim brought by defendant in response to claimant's claim
- Disclosure: The process of parties revealing documents to each other
- Injunction: A court order prohibiting or requiring an action
```

### Step 2: Add Azure AI Search Tool

1. In the agent playground, click **Knowledge > Add**
1. Select **Azure AI Search**
1. Choose **Indexes that are not part of this project**
1. Enter your existing search connection:
   - Azure AI Search resource connection: Create new or select existing
   - Endpoint: `https://your-search.search.windows.net`
   - API Key: Your admin key
1. Select your index (e.g., `gptkbindex`)
1. Configure search type: **Hybrid + Semantic** (recommended)
1. Click **Connect**

### Step 3: Python SDK Implementation

For more control, implement the agent using the Python SDK:

```python
# foundry-agent/agent.py
"""
Legal CPR Agent for Azure AI Foundry

This agent provides legal research capabilities using the same
Azure AI Search index as the web application.
"""

import os
import sys
from pathlib import Path
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    Agent,
    AgentThread,
    AzureAISearchTool,
    AzureAISearchToolResource,
)
from azure.identity import DefaultAzureCredential

# Add shared components
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from legal import CitationBuilder, SourceProcessor

# Configuration
PROJECT_ENDPOINT = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX", "gptkbindex")
SEARCH_CONNECTION_NAME = os.environ.get("AZURE_SEARCH_CONNECTION", "legal-search")

# Load instructions from shared prompts
def load_instructions():
    """Load and condense instructions from shared prompty files."""
    prompty_path = Path(__file__).parent.parent / "shared" / "prompts" / "chat_answer_question.prompty"

    # For Foundry, we need condensed instructions (keep under 8000 chars for optimal performance)
    instructions = """You are an expert legal assistant helping lawyers and legal professionals in England and Wales with questions about the Civil Procedure Rules (CPR), Practice Directions, and Court Guides.

DOCUMENT STRUCTURE AWARENESS:
The knowledge base contains documents from:
- Civil Procedure Rules (Parts 1-89) and associated Practice Directions
- Commercial Court Guide (11th Edition, July 2023)
- King's Bench Division Guide (2025 Edition)
- Chancery Guide (2022)
- Patents Court Guide (February 2025)
- Technology and Construction Court Guide (October 2022)
- Circuit Commercial Court Guide (August 2023)

When answering questions:
- Court Guides may provide specialized procedures that supplement or modify general CPR rules
- Practice Directions provide detailed implementation guidance for CPR Parts
- Consider both the general rule (CPR) and any court-specific variations when applicable

CITATION REQUIREMENTS:
- Every sentence must end with a numbered citation [1], [2], [3], etc.
- Reference the Azure AI Search results using their index numbers
- Use one citation per sentence

If the user asks about a specific court, prioritize information specific to that court.
If no specific court is mentioned, focus on general Civil Procedure Rules.
Always note when rules or procedures are court-specific versus generally applicable."""

    return instructions

def create_legal_agent(client: AIProjectClient) -> Agent:
    """Create the Legal CPR agent with Azure AI Search tool."""

    # Configure Azure AI Search tool
    search_tool = AzureAISearchTool(
        index_connection_id=SEARCH_CONNECTION_NAME,
        index_name=SEARCH_INDEX,
    )

    # Create agent
    agent = client.agents.create_agent(
        model="gpt-4o",  # Or your deployed model name
        name="Legal CPR Assistant",
        instructions=load_instructions(),
        tools=[search_tool],
    )

    print(f"Created agent: {agent.id}")
    return agent

def run_conversation(client: AIProjectClient, agent: Agent, user_message: str):
    """Run a single conversation turn with the agent."""

    # Create thread
    thread = client.agents.create_thread()

    # Add user message
    client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=user_message,
    )

    # Run agent
    run = client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=agent.id,
    )

    # Get response
    messages = client.agents.list_messages(thread_id=thread.id)

    # Process with shared citation builder
    citation_builder = CitationBuilder()

    for message in messages:
        if message.role == "assistant":
            return message.content[0].text.value

    return None

def main():
    """Main entry point."""
    # Initialize client
    client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    # Create or get agent
    agent = create_legal_agent(client)

    # Interactive loop
    print("Legal CPR Assistant Ready. Type 'quit' to exit.")
    print("-" * 50)

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ('quit', 'exit', 'q'):
            break

        if not user_input:
            continue

        response = run_conversation(client, agent, user_input)
        print(f"\nAssistant: {response}")

    # Cleanup
    client.agents.delete_agent(agent.id)
    print("\nAgent deleted. Goodbye!")

if __name__ == "__main__":
    main()
```

### Step 4: Agent Configuration File

```yaml
# foundry-agent/agent_config.yaml
name: Legal CPR Assistant
description: Expert legal assistant for Civil Procedure Rules in England and Wales

model:
  deployment: gpt-4o
  parameters:
    temperature: 0.2
    max_tokens: 4000

tools:
  - type: azure_ai_search
    connection: legal-search-connection
    index: gptkbindex
    search_type: hybrid_semantic
    top_k: 5

instructions_file: ../shared/prompts/chat_answer_question.prompty

conversation_starters:
  - "What are the disclosure requirements under CPR Part 31?"
  - "Explain the fast track allocation criteria"
  - "What are the Commercial Court's case management procedures?"
  - "When can a party apply for summary judgment?"
```

***

## Azure AI Search Tool Integration

### Connecting Your Existing Index

Your Legal RAG already has an Azure AI Search index. Here's how to connect it to Foundry:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                    CONNECTING EXISTING AZURE AI SEARCH INDEX                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  PREREQUISITES:                                                                          │
│  ├── Azure AI Search index with vector fields                                           │
│  ├── Index must have:                                                                   │
│  │   ├── Edm.String fields (searchable, retrievable)                                   │
│  │   └── Collection(Edm.Single) vector fields (searchable)                             │
│  └── Foundry project in same tenant as search resource                                 │
│                                                                                          │
│  YOUR INDEX FIELDS (from current deployment):                                           │
│  ├── content: Edm.String (main text)                                                   │
│  ├── sourcepage: Edm.String (page/section reference)                                   │
│  ├── sourcefile: Edm.String (document name)                                            │
│  ├── category: Edm.String (court/document type)                                        │
│  ├── storageUrl: Edm.String (blob storage URL)                                         │
│  └── embedding: Collection(Edm.Single) (vector embeddings)                             │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Creating the Connection via Azure CLI

```bash
# Create connection configuration
cat > connection.yml << EOF
name: legal-search-connection
type: azure_ai_search
endpoint: https://your-search.search.windows.net
api_key: your-admin-key
EOF

# Create connection in Foundry project
az ml connection create \
  --file connection.yml \
  --resource-group your-resource-group \
  --workspace-name your-foundry-project
```

### Configuring Search in Python SDK

```python
# foundry-agent/tools/legal_search.py
"""
Legal Search Tool Configuration for Azure AI Foundry

This module configures the Azure AI Search tool to work with
the existing legal documents index.
"""

from azure.ai.projects.models import (
    AzureAISearchTool,
    AzureAISearchQueryType,
)

def create_legal_search_tool(connection_id: str, index_name: str) -> AzureAISearchTool:
    """
    Create Azure AI Search tool configured for legal documents.

    Args:
        connection_id: The Foundry connection ID for Azure AI Search
        index_name: Name of the search index (e.g., 'gptkbindex')

    Returns:
        Configured AzureAISearchTool instance
    """
    return AzureAISearchTool(
        index_connection_id=connection_id,
        index_name=index_name,
        query_type=AzureAISearchQueryType.HYBRID_SEMANTIC,  # Best for legal docs
        top_k=5,
        # Filter can be added for category-specific searches
        # filter="category eq 'Commercial Court'"
    )

def create_filtered_search_tool(
    connection_id: str,
    index_name: str,
    category: str = None
) -> AzureAISearchTool:
    """
    Create search tool with optional category filter.

    This allows creating court-specific search experiences.
    """
    filter_expr = f"category eq '{category}'" if category else None

    return AzureAISearchTool(
        index_connection_id=connection_id,
        index_name=index_name,
        query_type=AzureAISearchQueryType.HYBRID_SEMANTIC,
        top_k=5,
        filter=filter_expr,
    )
```

***

## Foundry Agent Deployment

### Deployment Options

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         FOUNDRY AGENT DEPLOYMENT OPTIONS                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  OPTION 1: FOUNDRY PORTAL DEPLOYMENT (Recommended for Testing)                          │
│  ├── Create agent in portal                                                             │
│  ├── Test in playground                                                                  │
│  ├── Share playground link for testing                                                  │
│  └── Access via REST API                                                                │
│                                                                                          │
│  OPTION 2: SDK DEPLOYMENT (Recommended for Production)                                  │
│  ├── Define agent in code (agent.py)                                                    │
│  ├── Deploy via Azure CLI or SDK                                                        │
│  ├── Integrate with your application                                                    │
│  └── Full control over lifecycle                                                        │
│                                                                                          │
│  OPTION 3: HOSTED CONTAINER (Advanced)                                                  │
│  ├── Package agent as container                                                         │
│  ├── Deploy to Azure Container Apps                                                     │
│  ├── Custom scaling and networking                                                      │
│  └── Bring your own infrastructure                                                      │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### REST API Access

Once deployed, access your agent via REST API:

```python
# Example: Calling Foundry Agent from external application
import requests
import os

PROJECT_ENDPOINT = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
AGENT_ID = os.environ["AGENT_ID"]

def query_legal_agent(question: str, session_id: str = None):
    """Query the Legal CPR agent via REST API."""

    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
    }

    # Create thread if new session
    if not session_id:
        thread_response = requests.post(
            f"{PROJECT_ENDPOINT}/agents/{AGENT_ID}/threads",
            headers=headers,
        )
        session_id = thread_response.json()["id"]

    # Send message
    message_response = requests.post(
        f"{PROJECT_ENDPOINT}/agents/{AGENT_ID}/threads/{session_id}/messages",
        headers=headers,
        json={"role": "user", "content": question},
    )

    # Run agent
    run_response = requests.post(
        f"{PROJECT_ENDPOINT}/agents/{AGENT_ID}/threads/{session_id}/runs",
        headers=headers,
    )

    # Get response
    messages_response = requests.get(
        f"{PROJECT_ENDPOINT}/agents/{AGENT_ID}/threads/{session_id}/messages",
        headers=headers,
    )

    return messages_response.json()
```

### Environment Variables

```bash
# foundry-agent/.env

# Azure AI Foundry Project
AZURE_AI_PROJECT_ENDPOINT=https://your-project.api.azureml.ms

# Azure AI Search (existing from web app)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=gptkbindex

# Azure OpenAI (if using separate deployment)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_KEY=your-openai-key

# Foundry Agent
AGENT_ID=your-created-agent-id
SEARCH_CONNECTION_NAME=legal-search-connection
```

***

## Summary: Three Platforms Compared

| Capability | Web App | M365 Agent | Foundry Agent |
|------------|---------|------------|---------------|
| **Chat with legal knowledge** | ✅ | ✅ | ✅ |
| **Same Azure AI Search index** | ✅ | ✅ (API Plugin) | ✅ (Native tool) |
| **Same prompts/instructions** | ✅ Full | ✅ Condensed | ✅ Condensed |
| **Same citation logic** | ✅ | ✅ | ✅ |
| **Full UI with all settings** | ✅ | ❌ | ❌ |
| **Supporting content tab** | ✅ | ❌ | ❌ |
| **Teams/Word integration** | ❌ | ✅ | ❌ |
| **REST API access** | ✅ | ❌ | ✅ |
| **Playground testing** | ❌ | ✅ | ✅ |
| **Multi-agent orchestration** | ❌ | ❌ | ✅ |
| **Server-side tool execution** | ❌ | ❌ | ✅ |
| **Full observability/tracing** | Limited | Limited | ✅ |
| **VS Code development** | ✅ | ✅ | ✅ |

***

## Combined Implementation Timeline

| Phase | Week | Web App | M365 Agent | Foundry Agent |
|-------|------|---------|------------|---------------|
| **Phase 1** | 1 | Extract shared components | - | - |
| **Phase 2** | 2 | Update imports | Create manifests | Create project |
| **Phase 3** | 3 | - | Implement API Plugin | Connect AI Search |
| **Phase 4** | 4 | Test shared components | Test in Teams | Test in playground |
| **Phase 5** | 5 | - | Deploy to org | Deploy agent |

***

## References

### M365 Copilot

- [Microsoft 365 Copilot Extensibility Documentation](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/)
- [Declarative Agent Manifest Schema v1.2](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/declarative-agent-manifest-1.2)
- [API Plugin Development](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/overview-api-plugins)
- [Microsoft 365 Agents Toolkit](https://aka.ms/M365AgentsToolkit)
- [Build Declarative Agents Tutorial](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/build-declarative-agents)

### Azure AI Foundry

- [What is Foundry Agent Service?](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview)
- [Foundry Agent Quickstart](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/quickstart)
- [Azure AI Search Tool](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools-classic/azure-ai-search)
- [Foundry Python SDK](https://learn.microsoft.com/en-us/python/api/azure-ai-projects/)
- [Environment Setup](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/environment-setup)

### Teams Bot

- [Teams Bot Concepts](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/bot-basics)
- [Teams Bot Conversations](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/conversations/conversation-basics)
- [Register a Bot with Azure](https://learn.microsoft.com/en-us/azure/bot-service/bot-service-quickstart-registration)
- [Bot Framework SDK](https://github.com/microsoft/botbuilder-python)
- [Teams Bot Samples](https://github.com/OfficeDev/Microsoft-Teams-Samples)

***

# Part 2.5: Converting Foundry Agent to M365 Agent

This section shows how to **expose your Azure AI Foundry Agent as an M365 Copilot Agent**, giving you the best of both worlds: Foundry's powerful orchestration and M365's native Teams/Office integration.

> **🎯 Important**: Microsoft has **officially released native integration** between Azure AI Foundry Agents and Microsoft 365 Copilot/Teams. This is now a **first-class supported path**, not a workaround.

***

## Microsoft's Official Position on Foundry + M365

### Foundry Agents = Custom Engine Agents in M365

Microsoft defines two types of agents for M365 Copilot:

| Agent Type | Description | Foundry Fit |
|------------|-------------|-------------|
| **Declarative Agents** | Use Copilot's orchestrator + models. Define via manifest. | ❌ No |
| **Custom Engine Agents** | Bring your own orchestrator + models. | ✅ **YES** |

**Foundry Agents are Custom Engine Agents** that can be published directly to M365.

### Key Quote from Microsoft Documentation

> *"Microsoft Foundry provides a platform for building, testing, and publishing intelligent agents using the Agent Framework SDK. These agents can be integrated into Microsoft 365 Copilot and Teams either via Foundry portal or the Microsoft 365 Agents Toolkit."*
>
> *"This approach is ideal for developers or organizations that already maintain AI logic and orchestration in Foundry and want to make those capabilities directly available in Microsoft 365."*

### Microsoft's Example Scenario (Matches Your Use Case!)

From the official docs:

> **Legal case analysis**: *"A law firm creates a standalone AI agent using Foundry. The agent uses a custom-trained LLM for case law analysis and integrates with external legal databases. The agent should also be accessible within Microsoft 365 Copilot and have access to documents in SharePoint."*
>
> **Recommendation**: *"Use Foundry because it allows the firm to maintain custom AI logic and orchestration while making the agent accessible in Microsoft 365."*

***

## Two Official Integration Methods

Microsoft provides **two officially supported methods** to publish Foundry Agents to M365:

| Method | Description | Best For |
|--------|-------------|----------|
| **1. Foundry Portal Publish** | One-click publish from Foundry Portal directly to M365 Copilot & Teams | Rapid deployment, minimal code |
| **2. M365 Agents Toolkit Proxy** | Pro-code integration via VS Code with full customization | M365 data grounding, SSO, custom logic |
| **3. Custom API Wrapper** | Build your own OpenAPI wrapper, connect via Declarative Agent | Maximum flexibility, multi-client support |

### Comprehensive Comparison

| Feature | Method 1: Portal | Method 2: Toolkit | Method 3: API Wrapper |
|---------|------------------|-------------------|----------------------|
| **Setup Time** | Minutes | Hours | Days |
| **Code Required** | None | TypeScript/C# | Python/Node.js |
| **Auto Bot Service** | ✅ Yes | ✅ Yes | ❌ Manual |
| **Auto Entra ID** | ✅ Yes | ✅ Yes | ❌ Manual |
| **M365 Data Grounding** | ❌ No | ✅ Retrieval API | ❌ No (manual) |
| **SSO Support** | Limited | ✅ Full | ❌ Manual |
| **Custom Logic Layer** | ❌ No | ✅ Yes | ✅ Full control |
| **Multi-Environment** | ❌ Basic | ✅ Dev/Stage/Prod | ✅ Custom |
| **Expose to Non-M365** | ❌ No | ❌ No | ✅ Yes |
| **Debugging** | Portal only | ✅ VS Code | ✅ Any IDE |
| **Best For** | Quick demos, POCs | Production M365 apps | Complex integrations |

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                    FOUNDRY → M365 INTEGRATION METHODS                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────┐│
│  │   METHOD 1: PORTAL PUBLISH  │ │ METHOD 2: AGENTS TOOLKIT    │ │ METHOD 3: API WRAP  ││
│  │       (Low-Code / Rapid)    │ │   (Pro-Code / Advanced)     │ │  (Full Control)     ││
│  ├─────────────────────────────┤ ├─────────────────────────────┤ ├─────────────────────┤│
│  │                             │ │                             │ │                     ││
│  │  Foundry Portal             │ │  VS Code + Toolkit          │ │  Custom API Service ││
│  │       │                     │ │       │                     │ │       │             ││
│  │       ▼                     │ │       ▼                     │ │       ▼             ││
│  │  One-Click Publish          │ │  Proxy App Template         │ │  OpenAPI Wrapper    ││
│  │       │                     │ │       │                     │ │       │             ││
│  │       ▼                     │ │       ▼                     │ │       ▼             ││
│  │  Auto-provision:            │ │  Configure:                 │ │  Connect via:       ││
│  │  • Bot Service              │ │  • Foundry connection       │ │  • Declarative Agent││
│  │  • Entra ID                 │ │  • Retrieval API            │ │  • API Plugin       ││
│  │  • App Package              │ │  • SSO                      │ │  • Manual Entra     ││
│  │       │                     │ │       │                     │ │       │             ││
│  │       ▼                     │ │       ▼                     │ │       ▼             ││
│  │  M365 Copilot & Teams       │ │  M365 + M365 Data           │ │  M365 + Any Client  ││
│  │                             │ │                             │ │                     ││
│  │  ✅ Fastest                 │ │  ✅ M365 grounding          │ │  ✅ Max flexibility ││
│  │  ✅ No code                 │ │  ✅ SSO built-in            │ │  ✅ Multi-client    ││
│  │  ❌ Limited control         │ │  ❌ Toolkit required        │ │  ❌ Most work       ││
│  └─────────────────────────────┘ └─────────────────────────────┘ └─────────────────────┘│
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

***

## Method 1: Native Foundry Portal Publish (Recommended for Quick Start)

This is the **simplest path** - publish directly from the Foundry Portal with one click.

### Step-by-Step Guide

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                    FOUNDRY PORTAL PUBLISH WORKFLOW                                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  STEP 1: Prepare Your Agent                                                              │
│  ├── Test your Foundry agent in the playground                                          │
│  ├── Verify Azure AI Search integration works                                           │
│  └── Confirm citation formatting is correct                                             │
│                                                                                          │
│  STEP 2: Initiate Publish                                                                │
│  ├── In Foundry Portal, select your agent version                                       │
│  ├── Click "Publish" button                                                             │
│  └── Select "Publish to Teams and Microsoft 365 Copilot"                               │
│                                                                                          │
│  STEP 3: Auto-Provisioning                                                               │
│  ├── Azure Bot Service is automatically created                                         │
│  ├── Entra ID application is provisioned                                                │
│  └── Application ID and Tenant ID are generated                                         │
│                                                                                          │
│  STEP 4: Fill in Metadata                                                                │
│  ├── Name: "Legal CPR Assistant"                                                        │
│  ├── Description: "AI-powered legal assistant for UK Civil Procedure"                  │
│  ├── Icons: Color (192x192) and Outline (32x32)                                        │
│  ├── Publisher info                                                                     │
│  ├── Privacy policy URL                                                                 │
│  └── Terms of use URL                                                                   │
│                                                                                          │
│  STEP 5: Prepare Package                                                                 │
│  ├── Click "Prepare Agent"                                                              │
│  ├── Wait for M365 package generation                                                   │
│  └── Download package for local testing (optional)                                      │
│                                                                                          │
│  STEP 6: Choose Publish Scope                                                            │
│  ├── Shared Scope: Appears under "Your agents" (personal use)                          │
│  └── Organization Scope: Appears under "Built by your org" (requires admin approval)   │
│                                                                                          │
│  STEP 7: Verify in M365                                                                  │
│  ├── Open Microsoft 365 Copilot                                                         │
│  ├── Go to agent store                                                                  │
│  └── Find your agent and test                                                           │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Prerequisites

- Access to Microsoft Foundry portal
- A tested Foundry agent (your Legal CPR Agent)
- Azure subscription with permissions to create:
  - Azure Bot Service
  - Microsoft Entra ID applications
- App metadata ready:
  - Agent name and description
  - Color icon (192x192 px) and outline icon (32x32 px)
  - Privacy policy URL
  - Terms of use URL

### What Gets Auto-Provisioned

When you publish via Foundry Portal, Microsoft automatically creates:

| Resource | Purpose |
|----------|---------|
| **Azure Bot Service** | Handles M365 ↔ Foundry communication |
| **Entra ID App Registration** | Authentication and identity |
| **M365 App Package** | manifest.json + icons for Teams/Copilot |
| **Bot Endpoint** | Routes messages to your Foundry agent |

### Publish Scopes Explained

| Scope | Visibility | Approval Required | Location in M365 |
|-------|------------|-------------------|------------------|
| **Shared** | Only you | No | "Your agents" section |
| **Organization** | Everyone in org | Yes (Admin Center) | "Built by your org" section |

### Reference Documentation

- [Publish agents to Microsoft 365 Copilot and Microsoft Teams](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/publish-copilot)
- [C# Sample for Programmatic Publishing](https://github.com/OfficeDev/microsoft-365-agents-toolkit-samples/tree/dev/ProxyAgent-CSharp)

***

## Method 2: M365 Agents Toolkit Proxy (Advanced)

For scenarios requiring more control, use the Microsoft 365 Agents Toolkit to create a proxy app.

### When to Use This Method

- Need access to M365 data via **Retrieval API** (SharePoint, OneDrive grounding)
- Require **SSO** (Single Sign-On) integration
- Need **custom logic** between M365 and Foundry
- Want **multi-environment deployment** (dev, staging, prod)
- Need **debugging** and local development support

### Reference Documentation

- [Integrate your Foundry agent with Microsoft Agent Toolkit](https://aka.ms/aif2m365-procode)
- [Microsoft 365 Agents Toolkit](https://aka.ms/M365AgentsToolkit)

***

***

## Method 3: Custom API Wrapper (Full Control)

For maximum flexibility, create a custom API wrapper around your Foundry Agent and connect it via a Declarative Agent with an API Plugin. This approach gives you complete control over the integration layer.

### When to Use This Method

- Need **custom response formatting** before sending to M365
- Require **complex caching** or **session management**
- Want to **aggregate multiple agents** behind a single endpoint
- Need **custom authentication** flows
- Require **logging/auditing** at the integration layer
- Want to expose Foundry Agent to **non-M365 clients** simultaneously

### Architecture: Custom API Wrapper

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                     FOUNDRY AGENT → M365 COPILOT INTEGRATION                             │
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                         Microsoft 365 Copilot                                        ││
│  │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       ││
│  │   │    Teams      │  │     Word      │  │  PowerPoint   │  │    Outlook    │       ││
│  │   └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘       ││
│  │              │                │                │                │                   ││
│  │              └────────────────┴────────────────┴────────────────┘                   ││
│  │                                       │                                              ││
│  │                                       ▼                                              ││
│  │                      ┌─────────────────────────────────────┐                        ││
│  │                      │    Declarative Agent (Manifest)     │                        ││
│  │                      │    ├── Instructions (condensed)     │                        ││
│  │                      │    └── API Plugin (Foundry wrapper) │                        ││
│  │                      └─────────────────────────────────────┘                        ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                          │                                               │
│                                          ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                         API WRAPPER SERVICE                                          ││
│  │                     (Azure Functions / App Service)                                  ││
│  │                                                                                      ││
│  │   ┌───────────────────────────────────────────────────────────────────────────────┐ ││
│  │   │  Endpoints:                                                                    │ ││
│  │   │  ├── POST /api/legal/ask      → Forwards to Foundry Agent                     │ ││
│  │   │  ├── POST /api/legal/search   → Executes search via Foundry                   │ ││
│  │   │  └── GET  /api/legal/session  → Manages conversation threads                  │ ││
│  │   └───────────────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                          │                                               │
│                                          ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                      AZURE AI FOUNDRY AGENT                                          ││
│  │                                                                                      ││
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────────────┐  ││
│  │   │    Model     │    │ Instructions │    │              Tools                   │  ││
│  │   │   (GPT-4o)   │    │  (Legal CPR) │    │  ├── Azure AI Search                 │  ││
│  │   │              │    │              │    │  ├── Code Interpreter (optional)     │  ││
│  │   │              │    │              │    │  └── Custom Functions (optional)     │  ││
│  │   └──────────────┘    └──────────────┘    └──────────────────────────────────────┘  ││
│  │                                                                                      ││
│  │   Orchestration: Server-side tool execution, automatic retry, tracing               ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                          │                                               │
│                                          ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │                      AZURE AI SEARCH INDEX                                           ││
│  │                   (Same index as Web App & Foundry)                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Project Structure (API Wrapper)

```text
foundry-m365-wrapper/
├── app.py                    # Main Flask/FastAPI application
├── foundry_client.py         # Foundry Agent client
├── models.py                 # Request/response models
├── config.py                 # Configuration
├── openapi.yaml              # OpenAPI spec for M365 Plugin
├── requirements.txt
└── Dockerfile
```

### foundry_client.py

```python
"""
Foundry Agent Client for M365 Integration

This client wraps the Azure AI Foundry Agent SDK to provide
a simple interface for the M365 API Plugin.
"""

import os
from dataclasses import dataclass
from typing import Optional
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageRole
from azure.identity import DefaultAzureCredential

@dataclass
class LegalResponse:
    """Response from the Foundry Agent."""
    answer: str
    citations: list
    thread_id: str

class FoundryAgentClient:
    """
    Client for interacting with the Foundry Legal Agent.

    Manages threads and conversations with the Foundry Agent Service.
    """

    def __init__(self):
        self.project_endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
        self.agent_id = os.environ["FOUNDRY_AGENT_ID"]

        self.client = AIProjectClient(
            endpoint=self.project_endpoint,
            credential=DefaultAzureCredential(),
        )

        # Thread cache (in production, use Redis/CosmosDB)
        self._threads: dict = {}

    async def ask(
        self,
        question: str,
        session_id: Optional[str] = None
    ) -> LegalResponse:
        """
        Send a question to the Foundry Agent.

        Args:
            question: The user's legal question
            session_id: Optional session ID for conversation continuity

        Returns:
            LegalResponse with answer, citations, and thread ID
        """
        # Get or create thread
        thread_id = self._get_or_create_thread(session_id)

        # Add user message
        self.client.agents.messages.create(
            thread_id=thread_id,
            role=MessageRole.USER,
            content=question,
        )

        # Run the agent
        run = self.client.agents.runs.create_and_process(
            thread_id=thread_id,
            agent_id=self.agent_id,
        )

        # Get the response
        messages = self.client.agents.messages.list(thread_id=thread_id)

        # Find the assistant's response
        answer = ""
        citations = []

        for message in messages:
            if message.role == MessageRole.ASSISTANT:
                # Get the text content
                for content_part in message.content:
                    if hasattr(content_part, 'text'):
                        answer = content_part.text.value
                        # Extract citations from annotations
                        citations = self._extract_citations(content_part.text)
                break

        return LegalResponse(
            answer=answer,
            citations=citations,
            thread_id=thread_id,
        )

    def _get_or_create_thread(self, session_id: Optional[str]) -> str:
        """Get existing thread or create new one."""
        if session_id and session_id in self._threads:
            return self._threads[session_id]

        thread = self.client.agents.threads.create()

        if session_id:
            self._threads[session_id] = thread.id

        return thread.id

    def _extract_citations(self, text_content) -> list:
        """Extract citations from Foundry response annotations."""
        citations = []

        if hasattr(text_content, 'annotations'):
            for annotation in text_content.annotations:
                if hasattr(annotation, 'file_citation'):
                    citations.append({
                        "index": len(citations) + 1,
                        "source": annotation.file_citation.file_id,
                        "quote": annotation.file_citation.quote if hasattr(annotation.file_citation, 'quote') else "",
                    })

        return citations

    def delete_thread(self, session_id: str):
        """Clean up a conversation thread."""
        if session_id in self._threads:
            thread_id = self._threads.pop(session_id)
            try:
                self.client.agents.threads.delete(thread_id)
            except Exception:
                pass  # Thread may already be deleted
```

### app.py

```python
"""
API Wrapper for Foundry Agent → M365 Copilot Integration

This service exposes the Foundry Agent as REST endpoints
that can be consumed by M365 Copilot via API Plugin.
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os

from foundry_client import FoundryAgentClient, LegalResponse

app = FastAPI(
    title="Legal CPR Agent API",
    description="API wrapper for Foundry Legal Agent - M365 Copilot integration",
    version="1.0.0",
)

# CORS for M365 Copilot
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://*.microsoft.com", "https://*.office.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Foundry client
foundry_client = FoundryAgentClient()

# Request/Response Models
class LegalQuestion(BaseModel):
    """Request model for legal questions."""
    question: str
    session_id: Optional[str] = None

class Citation(BaseModel):
    """Citation reference."""
    index: int
    source: str
    quote: str = ""

class LegalAnswer(BaseModel):
    """Response model for legal answers."""
    answer: str
    citations: List[Citation]
    session_id: str

class SearchRequest(BaseModel):
    """Request model for document search."""
    query: str
    category: Optional[str] = None
    top: int = 5

class SearchResult(BaseModel):
    """Individual search result."""
    title: str
    content: str
    source: str
    relevance_score: float

class SearchResponse(BaseModel):
    """Response model for search results."""
    results: List[SearchResult]
    query: str

# API Endpoints

@app.post("/api/legal/ask", response_model=LegalAnswer)
async def ask_legal_question(
    request: LegalQuestion,
    authorization: Optional[str] = Header(None)
) -> LegalAnswer:
    """
    Ask a legal question to the Foundry Agent.

    This endpoint forwards the question to the Azure AI Foundry Agent
    and returns the response with citations.
    """
    try:
        response: LegalResponse = await foundry_client.ask(
            question=request.question,
            session_id=request.session_id,
        )

        return LegalAnswer(
            answer=response.answer,
            citations=[
                Citation(
                    index=c["index"],
                    source=c["source"],
                    quote=c.get("quote", ""),
                )
                for c in response.citations
            ],
            session_id=response.thread_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/legal/search", response_model=SearchResponse)
async def search_legal_documents(
    request: SearchRequest,
    authorization: Optional[str] = Header(None)
) -> SearchResponse:
    """
    Search legal documents directly.

    This endpoint performs a search without going through the full
    agent conversation flow - useful for quick lookups.
    """
    try:
        # For search-only, we can ask the agent with a search-focused prompt
        search_question = f"Search for: {request.query}"
        if request.category:
            search_question += f" in {request.category} documents"

        response = await foundry_client.ask(
            question=search_question,
            session_id=None,  # Fresh session for search
        )

        # Convert to search results format
        results = []
        for citation in response.citations[:request.top]:
            results.append(SearchResult(
                title=citation["source"],
                content=citation.get("quote", ""),
                source=citation["source"],
                relevance_score=1.0,  # Foundry doesn't expose scores
            ))

        return SearchResponse(
            results=results,
            query=request.query,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "foundry-m365-wrapper"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### requirements.txt

```text
fastapi>=0.100.0
uvicorn>=0.23.0
azure-ai-projects>=1.0.0
azure-identity>=1.15.0
pydantic>=2.0.0
```

### Deploy to Azure

```bash
# Deploy as Azure Container App
az containerapp create \
  --name foundry-m365-wrapper \
  --resource-group your-rg \
  --image your-registry.azurecr.io/foundry-m365-wrapper:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    AZURE_AI_PROJECT_ENDPOINT=https://your-project.api.azureml.ms \
    FOUNDRY_AGENT_ID=your-agent-id
```

***

## M365 API Plugin for Foundry

Create the OpenAPI specification and API Plugin manifest that M365 Copilot will use.

### openapi.yaml

```yaml
openapi: 3.0.3
info:
  title: Legal CPR Agent API
  description: |
    AI-powered legal assistant for UK Civil Procedure Rules.
    This API provides access to the Legal CPR Agent powered by Azure AI Foundry.
  version: 1.0.0

servers:
  - url: https://your-foundry-wrapper.azurecontainerapps.io
    description: Production API

paths:
  /api/legal/ask:
    post:
      operationId: askLegalQuestion
      summary: Ask a legal question
      description: |
        Ask any question about UK Civil Procedure Rules, Practice Directions,
        or Court Guides. The agent will search the knowledge base and provide
        an accurate answer with citations.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - question
              properties:
                question:
                  type: string
                  description: The legal question to ask
                  example: "What are the time limits for filing a defence under CPR?"
                session_id:
                  type: string
                  description: Optional session ID for conversation continuity
      responses:
        '200':
          description: Successful response with answer and citations
          content:
            application/json:
              schema:
                type: object
                properties:
                  answer:
                    type: string
                    description: The legal answer with inline citations
                  citations:
                    type: array
                    items:
                      type: object
                      properties:
                        index:
                          type: integer
                        source:
                          type: string
                        quote:
                          type: string
                  session_id:
                    type: string
                    description: Session ID for follow-up questions

  /api/legal/search:
    post:
      operationId: searchLegalDocuments
      summary: Search legal documents
      description: |
        Search the legal knowledge base for specific documents or topics.
        Returns relevant document excerpts.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - query
              properties:
                query:
                  type: string
                  description: Search query
                  example: "disclosure requirements Commercial Court"
                category:
                  type: string
                  description: Optional document category filter
                  enum:
                    - "CPR"
                    - "Practice Directions"
                    - "Commercial Court"
                    - "Kings Bench"
                    - "Chancery"
                top:
                  type: integer
                  description: Number of results to return
                  default: 5
                  maximum: 20
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                type: object
                properties:
                  results:
                    type: array
                    items:
                      type: object
                      properties:
                        title:
                          type: string
                        content:
                          type: string
                        source:
                          type: string
                        relevance_score:
                          type: number
                  query:
                    type: string
```

### ai-plugin.json

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/copilot/plugin/v2.1/schema.json",
  "schema_version": "v2.1",
  "name_for_human": "Legal CPR Agent (Foundry)",
  "name_for_model": "legalCPRFoundry",
  "description_for_human": "AI-powered legal assistant for UK Civil Procedure Rules, powered by Azure AI Foundry",
  "description_for_model": "Use this plugin when the user asks about UK legal procedures, Civil Procedure Rules (CPR), Practice Directions, or Court Guides. This plugin connects to an Azure AI Foundry agent with Azure AI Search for accurate, citation-backed answers.",
  "logo_url": "https://your-domain.com/legal-icon.png",
  "contact_email": "legal-support@your-org.com",
  "legal_info_url": "https://your-domain.com/legal/terms",
  "privacy_policy_url": "https://your-domain.com/legal/privacy",
  "api": {
    "type": "openapi",
    "url": "https://your-foundry-wrapper.azurecontainerapps.io/openapi.yaml"
  },
  "auth": {
    "type": "none"
  },
  "capabilities": {
    "conversation_starters": [
      {
        "text": "What are the CPR Part 31 disclosure requirements?"
      },
      {
        "text": "Explain the fast track allocation criteria"
      },
      {
        "text": "What are the Commercial Court's case management procedures?"
      }
    ]
  },
  "runtimes": [
    {
      "type": "OpenApi",
      "auth": {
        "type": "None"
      },
      "spec": {
        "url": "https://your-foundry-wrapper.azurecontainerapps.io/openapi.yaml"
      },
      "run_for_functions": ["askLegalQuestion", "searchLegalDocuments"]
    }
  ],
  "functions": [
    {
      "name": "askLegalQuestion",
      "description": "Ask a legal question about UK Civil Procedure Rules and get an answer with citations from CPR, Practice Directions, and Court Guides.",
      "parameters": {
        "type": "object",
        "required": ["question"],
        "properties": {
          "question": {
            "type": "string",
            "description": "The legal question to ask"
          },
          "session_id": {
            "type": "string",
            "description": "Optional session ID for follow-up questions"
          }
        }
      }
    },
    {
      "name": "searchLegalDocuments",
      "description": "Search the legal knowledge base for specific documents or topics.",
      "parameters": {
        "type": "object",
        "required": ["query"],
        "properties": {
          "query": {
            "type": "string",
            "description": "Search query"
          },
          "category": {
            "type": "string",
            "description": "Document category filter"
          },
          "top": {
            "type": "integer",
            "description": "Number of results"
          }
        }
      }
    }
  ]
}
```

***

## Declarative Agent Manifest for Foundry

### declarativeAgent.json

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.2/schema.json",
  "version": "v1.2",
  "name": "Legal CPR Agent (Foundry-Powered)",
  "description": "AI-powered legal assistant for UK Civil Procedure Rules, powered by Azure AI Foundry Agent Service",
  "instructions": "You are a legal assistant powered by Azure AI Foundry. When users ask legal questions about UK Civil Procedure, use the askLegalQuestion function to get accurate answers with citations. For document searches, use searchLegalDocuments.\n\nALWAYS:\n- Use the Foundry agent functions for legal questions\n- Include citation references in your responses\n- Clarify when procedures are court-specific\n- Recommend consulting a solicitor for specific legal advice\n\nThe Foundry agent has access to:\n- Civil Procedure Rules (Parts 1-89)\n- Practice Directions\n- Commercial Court Guide\n- King's Bench Guide\n- Chancery Guide\n- Patents Court Guide\n- TCC Guide",
  "conversation_starters": [
    {
      "title": "CPR Time Limits",
      "text": "What are the time limits for filing a defence under CPR?"
    },
    {
      "title": "Commercial Court",
      "text": "What are the Commercial Court's disclosure requirements?"
    },
    {
      "title": "Summary Judgment",
      "text": "When can a party apply for summary judgment?"
    },
    {
      "title": "Service Rules",
      "text": "Explain the rules for service of documents under CPR Part 6"
    }
  ],
  "actions": [
    {
      "id": "foundryLegalPlugin",
      "file": "ai-plugin.json"
    }
  ]
}
```

### Teams App Manifest (manifest.json)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.17/MicrosoftTeams.schema.json",
  "manifestVersion": "1.17",
  "version": "1.0.0",
  "id": "{{APP_ID}}",
  "packageName": "com.yourorg.legalcprfoundry",
  "developer": {
    "name": "Your Organization",
    "websiteUrl": "https://your-domain.com",
    "privacyUrl": "https://your-domain.com/privacy",
    "termsOfUseUrl": "https://your-domain.com/terms"
  },
  "name": {
    "short": "Legal CPR (Foundry)",
    "full": "Legal CPR Agent - Powered by Azure AI Foundry"
  },
  "description": {
    "short": "AI legal assistant powered by Foundry",
    "full": "Get accurate answers to UK Civil Procedure questions with citations. Powered by Azure AI Foundry Agent Service with Azure AI Search integration."
  },
  "icons": {
    "color": "color.png",
    "outline": "outline.png"
  },
  "accentColor": "#1a365d",
  "copilotAgents": {
    "declarativeAgents": [
      {
        "id": "legalCPRFoundryAgent",
        "file": "declarativeAgent.json"
      }
    ]
  },
  "permissions": ["identity"],
  "validDomains": [
    "your-foundry-wrapper.azurecontainerapps.io"
  ]
}
```

***

## Testing Foundry Agent in M365

### Local Testing with Teams Toolkit

1. **Install M365 Agents Toolkit** in VS Code
1. **Open your project** with the manifest files
1. **Press F5** to start debugging
1. **Sign in** to your M365 developer tenant
1. **Test in Teams** - the agent will appear in Copilot

### Validation Checklist

| Test Case | Expected Result |
|-----------|-----------------|
| Ask a simple CPR question | Answer with citations from Foundry |
| Ask follow-up question | Context maintained via session_id |
| Search for documents | Returns relevant document excerpts |
| Ask about specific court | Court-specific information provided |
| Invalid question | Graceful error handling |

### Debugging

```bash
# Check API wrapper logs
az containerapp logs show \
  --name foundry-m365-wrapper \
  --resource-group your-rg

# Check Foundry agent traces in Azure AI Foundry Portal
# Go to: ai.azure.com → Your Project → Traces
```

***

## Comparison: Direct M365 vs Foundry-Backed M365

| Aspect | Direct M365 Agent (Part 1) | Foundry-Backed M365 Agent |
|--------|---------------------------|---------------------------|
| **Architecture** | M365 Copilot → API Plugin → Backend | M365 Copilot → API Plugin → Foundry → Search |
| **Tool execution** | Client-side (M365 orchestrator) | Server-side (Foundry orchestrator) |
| **Observability** | Limited | Full tracing in Foundry |
| **Multi-agent** | No | Yes (Foundry supports multi-agent) |
| **Complexity** | Lower | Higher (extra API layer) |
| **Latency** | Lower | Slightly higher (extra hop) |
| **Best for** | Simple Q&A scenarios | Complex orchestration needs |

***

# Part 3: Teams Bot Integration

This section covers deploying your Legal RAG solution as a Teams bot, which provides direct conversational access to your legal knowledge base within Microsoft Teams.

## Teams Bot Overview

There are **two approaches** to integrating your Legal RAG solution into Teams:

| Approach | Description | Best For |
|----------|-------------|----------|
| **M365 Declarative Agent** | Extension of M365 Copilot (Part 1) | Organizations using M365 Copilot licenses |
| **Standalone Azure Bot** | Custom bot using Bot Framework | Organizations without M365 Copilot, or needing custom control |

***

## Teams Bot Architecture

### Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              TEAMS BOT INTEGRATION                                    │
│                                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Microsoft Teams                                        │ │
│  │                                                                                  │ │
│  │   ┌──────────────────────┐          ┌──────────────────────┐                   │ │
│  │   │   Personal Chat      │          │   Channel/Group      │                   │ │
│  │   │   1:1 with Bot       │          │   @mention Bot       │                   │ │
│  │   └──────────────────────┘          └──────────────────────┘                   │ │
│  │              │                                │                                  │ │
│  └──────────────┼────────────────────────────────┼──────────────────────────────────┘ │
│                 │                                │                                    │
│                 └────────────────┬───────────────┘                                    │
│                                  ▼                                                    │
│            ┌─────────────────────────────────────────────────────────────┐           │
│            │                  Bot Framework Connector                     │           │
│            │              (Azure Bot Service Channel)                     │           │
│            └─────────────────────────────────────────────────────────────┘           │
│                                  │                                                    │
│       ┌──────────────────────────┼──────────────────────────────────────┐            │
│       │                          │                                       │            │
│       ▼                          ▼                                       ▼            │
│ ┌─────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐   │
│ │  Approach 1     │    │     Approach 2           │    │     Approach 3          │   │
│ │  M365 Agent     │    │     Standalone Bot       │    │     Foundry + Bot       │   │
│ │  (Part 1)       │    │     (Bot Framework)      │    │     (Hybrid)            │   │
│ │                 │    │                          │    │                          │   │
│ │  Declarative    │    │  ┌───────────────────┐  │    │  ┌───────────────────┐   │   │
│ │  Agent +        │    │  │  Bot Application  │  │    │  │  Bot Application  │   │   │
│ │  API Plugin     │    │  │  (Python/Node.js) │  │    │  │  + Foundry Agent  │   │   │
│ │                 │    │  └─────────┬─────────┘  │    │  └─────────┬─────────┘   │   │
│ │                 │    │            │            │    │            │             │   │
│ │                 │    │            ▼            │    │            ▼             │   │
│ │                 │    │  ┌───────────────────┐  │    │  ┌───────────────────┐   │   │
│ │  Uses M365      │    │  │  Legal RAG Core   │  │    │  │  Foundry Agent    │   │   │
│ │  Copilot UI     │    │  │  (Same Backend)   │  │    │  │  Service          │   │   │
│ │                 │    │  └─────────┬─────────┘  │    │  └─────────┬─────────┘   │   │
│ └─────────────────┘    │            │            │    │            │             │   │
│                        │            ▼            │    │            ▼             │   │
│                        │  ┌───────────────────┐  │    │  ┌───────────────────┐   │   │
│                        │  │  Azure AI Search  │  │    │  │  Azure AI Search  │   │   │
│                        │  │  (Legal Docs)     │  │    │  │  (Legal Docs)     │   │   │
│                        │  └───────────────────┘  │    │  └───────────────────┘   │   │
│                        └─────────────────────────┘    └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

***

## Approach 1: M365 Declarative Agent in Teams

If you've already implemented Part 1 (M365 Copilot Declarative Agent), your agent is **automatically available in Teams** through M365 Copilot.

### How It Works

1. M365 Copilot is natively integrated into Teams
1. Users access your Declarative Agent via the Copilot pane
1. No additional development required

### Enabling in Teams

The M365 Declarative Agent from Part 1 appears in Teams when:

- The app is deployed to the organization
- Users have M365 Copilot licenses
- The app manifest includes Teams as a supported scope

```json
// manifest.json - Teams scope configuration
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "{{APP_ID}}",
  "name": {
    "short": "Legal Advisor",
    "full": "Legal RAG Advisor for UK Civil Procedure"
  },
  "description": {
    "short": "AI-powered legal assistant",
    "full": "Get answers to civil procedure questions with precise citations"
  },
  "developer": {
    "name": "Your Organization",
    "websiteUrl": "https://your-domain.com",
    "privacyUrl": "https://your-domain.com/privacy",
    "termsOfUseUrl": "https://your-domain.com/terms"
  },
  "copilotAgents": {
    "declarativeAgents": [
      {
        "id": "legalAdvisor",
        "file": "declarativeAgent.json"
      }
    ]
  },
  "validDomains": [
    "your-api-domain.azurewebsites.net"
  ]
}
```

***

## Approach 2: Standalone Azure Bot Service

For organizations without M365 Copilot licenses or needing more control, deploy a custom Teams bot using Azure Bot Service.

### Prerequisites

- Azure subscription
- Azure Bot Service resource
- Microsoft App Registration (Entra ID)
- Bot Framework SDK (Python or Node.js)

### Project Structure

```text
teams-bot/
├── app.py                    # Main bot application
├── bot.py                    # Bot logic and handlers
├── legal_rag_client.py       # Client for Legal RAG backend
├── adaptive_cards/           # Adaptive Card templates
│   ├── citation_card.json
│   ├── answer_card.json
│   └── error_card.json
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container deployment
└── appPackage/               # Teams app manifest
    ├── manifest.json
    ├── color.png
    └── outline.png
```

### Step 1: Register Azure Bot

1. Go to Azure Portal → Create Resource → Azure Bot
1. Configure:
   - **Bot handle**: legal-advisor-bot
   - **Pricing tier**: Standard S1
   - **App type**: Single Tenant (recommended)
   - **Microsoft App ID**: Create new or use existing

```bash
# Using Azure CLI
az bot create \
  --resource-group your-rg \
  --name legal-advisor-bot \
  --kind azurebot \
  --sku S1 \
  --app-type SingleTenant \
  --location global
```

### Step 2: Enable Teams Channel

```bash
# Enable Teams channel
az bot channel create \
  --resource-group your-rg \
  --name legal-advisor-bot \
  --channel Teams
```

### Step 3: Bot Implementation

#### config.py

```python
"""Bot configuration settings."""
import os
from dataclasses import dataclass

@dataclass
class BotConfig:
    """Configuration for the Teams bot."""
    # Bot Framework settings
    APP_ID: str = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD: str = os.environ.get("MicrosoftAppPassword", "")
    APP_TENANT_ID: str = os.environ.get("MicrosoftAppTenantId", "")

    # Legal RAG Backend
    BACKEND_URL: str = os.environ.get("LEGAL_RAG_BACKEND_URL", "http://localhost:50505")

    # Azure OpenAI (optional - if calling directly)
    AZURE_OPENAI_ENDPOINT: str = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.environ.get("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")

    # Azure AI Search (optional - if searching directly)
    AZURE_SEARCH_ENDPOINT: str = os.environ.get("AZURE_SEARCH_ENDPOINT", "")
    AZURE_SEARCH_KEY: str = os.environ.get("AZURE_SEARCH_KEY", "")
    AZURE_SEARCH_INDEX: str = os.environ.get("AZURE_SEARCH_INDEX", "gptkbindex")
```

#### legal_rag_client.py

```python
"""Client for calling the Legal RAG backend API."""
import aiohttp
from dataclasses import dataclass
from typing import Optional

@dataclass
class LegalAnswer:
    """Response from the Legal RAG backend."""
    answer: str
    citations: list
    thoughts: Optional[str] = None

class LegalRAGClient:
    """Async client for Legal RAG API calls."""

    def __init__(self, backend_url: str):
        self.backend_url = backend_url.rstrip('/')

    async def ask(
        self,
        question: str,
        category: Optional[str] = None,
        history: Optional[list] = None
    ) -> LegalAnswer:
        """
        Send a question to the Legal RAG backend.

        Args:
            question: The user's legal question
            category: Optional category filter (e.g., "cpr_part_*")
            history: Optional conversation history

        Returns:
            LegalAnswer with response and citations
        """
        payload = {
            "messages": [
                {"role": "user", "content": question}
            ],
            "context": {
                "overrides": {
                    "use_semantic_ranker": True,
                    "use_semantic_captions": True,
                    "top": 5,
                    "retrieval_mode": "hybrid"
                }
            }
        }

        if category:
            payload["context"]["overrides"]["filter"] = f"category eq '{category}'"

        if history:
            payload["messages"] = history + payload["messages"]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.backend_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Backend error: {error_text}")

                data = await response.json()

                # Extract answer and citations from response
                answer = data.get("message", {}).get("content", "")
                citations = self._extract_citations(data.get("context", {}))
                thoughts = data.get("context", {}).get("thoughts", "")

                return LegalAnswer(
                    answer=answer,
                    citations=citations,
                    thoughts=thoughts
                )

    def _extract_citations(self, context: dict) -> list:
        """Extract citations from the response context."""
        citations = []
        data_points = context.get("data_points", {})

        # Handle text citations
        text_points = data_points.get("text", [])
        for point in text_points:
            if ":" in point:
                source, content = point.split(":", 1)
                citations.append({
                    "source": source.strip(),
                    "content": content.strip()[:200] + "..."
                })

        return citations
```

#### bot.py

```python
"""Teams bot implementation for Legal RAG."""
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    Attachment,
    CardAction,
    ActionTypes,
    SuggestedActions
)
from botbuilder.core.teams import TeamsActivityHandler, TeamsInfo
import json

from legal_rag_client import LegalRAGClient, LegalAnswer
from config import BotConfig

class LegalAdvisorBot(TeamsActivityHandler):
    """
    Teams bot that provides legal advice using the Legal RAG backend.
    """

    def __init__(self, config: BotConfig):
        super().__init__()
        self.config = config
        self.legal_client = LegalRAGClient(config.BACKEND_URL)
        self.conversation_history: dict = {}  # In production, use Redis/CosmosDB

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming messages from Teams users."""
        # Get the user's message
        user_message = turn_context.activity.text
        conversation_id = turn_context.activity.conversation.id

        # Remove bot mention if in channel
        user_message = self._remove_mention(turn_context, user_message)

        # Send typing indicator
        await turn_context.send_activity(Activity(type=ActivityTypes.typing))

        try:
            # Get conversation history
            history = self.conversation_history.get(conversation_id, [])

            # Call Legal RAG backend
            answer = await self.legal_client.ask(
                question=user_message,
                history=history[-6:]  # Keep last 6 messages for context
            )

            # Build response with Adaptive Card
            card = self._build_answer_card(answer)

            # Send the response
            await turn_context.send_activity(
                MessageFactory.attachment(card)
            )

            # Update conversation history
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": answer.answer})
            self.conversation_history[conversation_id] = history[-10:]

        except Exception as e:
            # Send error card
            error_card = self._build_error_card(str(e))
            await turn_context.send_activity(
                MessageFactory.attachment(error_card)
            )

    async def on_members_added_activity(
        self,
        members_added,
        turn_context: TurnContext
    ):
        """Welcome new users to the bot."""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_card = self._build_welcome_card()
                await turn_context.send_activity(
                    MessageFactory.attachment(welcome_card)
                )

    def _remove_mention(self, turn_context: TurnContext, text: str) -> str:
        """Remove @mention from message text."""
        if turn_context.activity.entities:
            for entity in turn_context.activity.entities:
                if entity.type == "mention":
                    mentioned = entity.additional_properties.get("mentioned", {})
                    if mentioned.get("id") == turn_context.activity.recipient.id:
                        mention_text = entity.additional_properties.get("text", "")
                        text = text.replace(mention_text, "").strip()
        return text

    def _build_answer_card(self, answer: LegalAnswer) -> Attachment:
        """Build an Adaptive Card for the answer."""
        card_body = [
            {
                "type": "TextBlock",
                "text": "Legal Advisor",
                "weight": "bolder",
                "size": "medium",
                "color": "accent"
            },
            {
                "type": "TextBlock",
                "text": answer.answer,
                "wrap": True,
                "spacing": "medium"
            }
        ]

        # Add citations if available
        if answer.citations:
            card_body.append({
                "type": "TextBlock",
                "text": "📚 Sources",
                "weight": "bolder",
                "spacing": "large"
            })

            for citation in answer.citations[:5]:  # Limit to 5 citations
                card_body.append({
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"**{citation['source']}**",
                            "wrap": True,
                            "size": "small",
                            "color": "accent"
                        },
                        {
                            "type": "TextBlock",
                            "text": citation['content'],
                            "wrap": True,
                            "size": "small",
                            "isSubtle": True
                        }
                    ],
                    "style": "emphasis",
                    "spacing": "small"
                })

        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": card_body,
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "👍",
                    "data": {"action": "feedback", "value": "positive"}
                },
                {
                    "type": "Action.Submit",
                    "title": "👎",
                    "data": {"action": "feedback", "value": "negative"}
                }
            ]
        }

        return Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card
        )

    def _build_welcome_card(self) -> Attachment:
        """Build a welcome card for new users."""
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "⚖️ Legal Advisor Bot",
                    "weight": "bolder",
                    "size": "large",
                    "color": "accent"
                },
                {
                    "type": "TextBlock",
                    "text": "Welcome! I'm your AI-powered legal assistant for UK Civil Procedure questions.",
                    "wrap": True,
                    "spacing": "medium"
                },
                {
                    "type": "TextBlock",
                    "text": "I can help you with:",
                    "wrap": True,
                    "weight": "bolder",
                    "spacing": "large"
                },
                {
                    "type": "TextBlock",
                    "text": "• Civil Procedure Rules (Parts 1-89)\n• Practice Directions\n• Court Guides\n• Pre-Action Protocols",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": "Try asking: 'What are the requirements for service under CPR Part 6?'",
                    "wrap": True,
                    "isSubtle": True,
                    "spacing": "large"
                }
            ]
        }

        return Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card
        )

    def _build_error_card(self, error_message: str) -> Attachment:
        """Build an error card."""
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "⚠️ Error",
                    "weight": "bolder",
                    "color": "attention"
                },
                {
                    "type": "TextBlock",
                    "text": "I encountered an issue processing your request. Please try again.",
                    "wrap": True
                }
            ]
        }

        return Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card
        )
```

#### app.py

```python
"""Main application entry point for the Teams bot."""
import sys
import traceback
from datetime import datetime
from http import HTTPStatus

from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import (
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    TurnContext,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication

from bot import LegalAdvisorBot
from config import BotConfig

# Create configuration
CONFIG = BotConfig()

# Create adapter with authentication
SETTINGS = ConfigurationBotFrameworkAuthentication(
    configuration={
        "MicrosoftAppId": CONFIG.APP_ID,
        "MicrosoftAppPassword": CONFIG.APP_PASSWORD,
        "MicrosoftAppTenantId": CONFIG.APP_TENANT_ID,
        "MicrosoftAppType": "SingleTenant",
    }
)
ADAPTER = CloudAdapter(SETTINGS)

# Error handler
async def on_error(context: TurnContext, error: Exception):
    """Global error handler for the bot."""
    print(f"\n [on_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send error message to user
    await context.send_activity("I encountered an error. Please try again later.")

ADAPTER.on_turn_error = on_error

# Create bot instance
BOT = LegalAdvisorBot(CONFIG)

# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    """Handle incoming Bot Framework messages."""
    if "application/json" in req.headers.get("Content-Type", ""):
        body = await req.json()
    else:
        return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    response = await ADAPTER.process_activity(auth_header, activity, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=HTTPStatus.OK)

def init_app():
    """Initialize the aiohttp web application."""
    app = web.Application(middlewares=[aiohttp_error_middleware])
    app.router.add_post("/api/messages", messages)
    return app

if __name__ == "__main__":
    app = init_app()
    web.run_app(app, host="0.0.0.0", port=3978)
```

### Step 4: Teams App Manifest

#### appPackage/manifest.json

```json
{
  "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "{{BOT_ID}}",
  "packageName": "com.yourorg.legaladvisorbot",
  "developer": {
    "name": "Your Organization",
    "websiteUrl": "https://your-domain.com",
    "privacyUrl": "https://your-domain.com/privacy",
    "termsOfUseUrl": "https://your-domain.com/terms"
  },
  "name": {
    "short": "Legal Advisor",
    "full": "Legal Advisor Bot - UK Civil Procedure"
  },
  "description": {
    "short": "AI-powered legal assistant for civil procedure",
    "full": "Get instant answers to UK Civil Procedure questions with precise citations from CPR, Practice Directions, and Court Guides."
  },
  "icons": {
    "color": "color.png",
    "outline": "outline.png"
  },
  "accentColor": "#1e3a5f",
  "bots": [
    {
      "botId": "{{BOT_ID}}",
      "scopes": ["personal", "team", "groupChat"],
      "supportsFiles": false,
      "isNotificationOnly": false,
      "commandLists": [
        {
          "scopes": ["personal", "team", "groupChat"],
          "commands": [
            {
              "title": "help",
              "description": "Get help using the Legal Advisor"
            },
            {
              "title": "ask",
              "description": "Ask a civil procedure question"
            }
          ]
        }
      ]
    }
  ],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": [
    "your-bot.azurewebsites.net",
    "token.botframework.com"
  ]
}
```

### Step 5: Deploy to Azure

#### requirements.txt

```text
botbuilder-core>=4.14.0
botbuilder-integration-aiohttp>=4.14.0
aiohttp>=3.8.0
```

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3978

CMD ["python", "app.py"]
```

#### Deploy Commands

```bash
# Build and push to Azure Container Registry
az acr build --registry yourregistry --image legal-advisor-bot:latest .

# Deploy to Azure Container Apps
az containerapp create \
  --name legal-advisor-bot \
  --resource-group your-rg \
  --image yourregistry.azurecr.io/legal-advisor-bot:latest \
  --target-port 3978 \
  --ingress external \
  --env-vars \
    MicrosoftAppId=your-app-id \
    MicrosoftAppPassword=your-app-password \
    MicrosoftAppTenantId=your-tenant-id \
    LEGAL_RAG_BACKEND_URL=https://your-backend.azurewebsites.net
```

***

## Approach 3: Foundry Agent + Teams Bot (Hybrid)

Combine Azure AI Foundry Agent (Part 2) with Teams bot for the best of both worlds.

### Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                     Teams Bot (Frontend)                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  • Receives Teams messages                                   │ │
│  │  • Renders Adaptive Cards                                    │ │
│  │  • Manages conversation state                                │ │
│  └───────────────────────────┬─────────────────────────────────┘ │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Azure AI Foundry Agent (Backend)                │ │
│  │  • Agent orchestration                                       │ │
│  │  • Azure AI Search integration                               │ │
│  │  • Tool execution                                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
"""Hybrid bot using Foundry Agent as backend."""
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from botbuilder.core import TurnContext
from botbuilder.core.teams import TeamsActivityHandler

class FoundryTeamsBot(TeamsActivityHandler):
    """Teams bot backed by Azure AI Foundry Agent."""

    def __init__(self, config):
        super().__init__()
        self.config = config

        # Initialize Foundry client
        self.project_client = AIProjectClient(
            credential=DefaultAzureCredential(),
            subscription_id=config.AZURE_SUBSCRIPTION_ID,
            resource_group_name=config.AZURE_RESOURCE_GROUP,
            project_name=config.AZURE_AI_PROJECT_NAME
        )

        self.agent_id = config.FOUNDRY_AGENT_ID
        self.threads: dict = {}  # conversation_id -> thread_id

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle messages by routing to Foundry Agent."""
        user_message = turn_context.activity.text
        conversation_id = turn_context.activity.conversation.id

        # Get or create thread
        thread_id = self.threads.get(conversation_id)
        if not thread_id:
            thread = self.project_client.agents.threads.create()
            thread_id = thread.id
            self.threads[conversation_id] = thread_id

        # Add message to thread
        self.project_client.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # Run the agent
        run = self.project_client.agents.runs.create_and_process(
            thread_id=thread_id,
            agent_id=self.agent_id
        )

        # Get the response
        messages = self.project_client.agents.messages.list(thread_id=thread_id)
        last_message = messages[0]  # Most recent

        # Build and send Adaptive Card
        card = self._build_answer_card(last_message.content)
        await turn_context.send_activity(
            MessageFactory.attachment(card)
        )
```

***

## Comparison: Bot Approaches

| Feature | M365 Declarative Agent | Standalone Bot | Foundry + Bot |
|---------|------------------------|----------------|---------------|
| **Development effort** | Low (if M365 done) | Medium | Medium |
| **M365 license required** | Yes | No | No |
| **Custom UI (Adaptive Cards)** | Limited | Full | Full |
| **Conversation history** | Automatic | Manual | Automatic (threads) |
| **Tool execution** | API Plugin | Direct call | Server-side |
| **Channel/Group support** | Via Copilot | Full | Full |
| **Deployment target** | M365 Copilot | Azure Bot Service | Azure Bot + Foundry |
| **Best for** | M365 orgs | Non-M365 orgs | Complex orchestration |

***

## Teams Bot Best Practices

### Message Handling

1. **Keep responses concise** - Teams UI works best with shorter messages
1. **Use Adaptive Cards** - Rich formatting with actions
1. **Handle @mentions** - Strip bot mention in channels
1. **Typing indicators** - Show typing while processing

### Conversation Management

1. **Limit history** - Keep last 6-10 messages for context
1. **Use persistent storage** - Redis/CosmosDB for production
1. **Handle timeouts** - Bot Framework has 15-second limit

### Error Handling

1. **Graceful degradation** - Show user-friendly error cards
1. **Retry logic** - Use exponential backoff for backend calls
1. **Logging** - Application Insights for monitoring

***

## Environment Variables Summary

```env
# Bot Framework
MicrosoftAppId=your-bot-app-id
MicrosoftAppPassword=your-bot-secret
MicrosoftAppTenantId=your-tenant-id
MicrosoftAppType=SingleTenant

# Legal RAG Backend
LEGAL_RAG_BACKEND_URL=https://your-backend.azurewebsites.net

# Optional: Azure AI Foundry (for hybrid approach)
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=your-resource-group
AZURE_AI_PROJECT_NAME=your-project
FOUNDRY_AGENT_ID=your-agent-id
```

***

## Four Platforms Compared (Updated)

| Capability | Web App | M365 Agent | Foundry Agent | Teams Bot |
|------------|---------|------------|---------------|-----------|
| **Chat with legal knowledge** | ✅ | ✅ | ✅ | ✅ |
| **Same Azure AI Search index** | ✅ | ✅ (API Plugin) | ✅ (Native) | ✅ (via backend) |
| **Same prompts** | ✅ Full | ✅ Condensed | ✅ Condensed | ✅ (via backend) |
| **Full UI with all settings** | ✅ | ❌ | ❌ | ❌ |
| **Teams integration** | ❌ | ✅ (via Copilot) | ❌ | ✅ (native) |
| **Adaptive Cards** | ❌ | Limited | ❌ | ✅ |
| **Channel/Group chat** | ❌ | ❌ | ❌ | ✅ |
| **M365 license required** | ❌ | ✅ | ❌ | ❌ |
| **Custom conversation flow** | ✅ | ❌ | ✅ | ✅ |
| **REST API access** | ✅ | ❌ | ✅ | ❌ |

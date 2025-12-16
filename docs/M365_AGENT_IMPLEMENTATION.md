# Agent Implementation Guide

## Legal RAG as an AI Agent (M365 Copilot & Azure AI Foundry)

This document provides comprehensive implementation guides for deploying your Legal RAG solution as:

1. **Microsoft 365 Copilot Declarative Agent** - Integration into Teams, Word, PowerPoint, Outlook
2. **Azure AI Foundry Agent** - Standalone agent with Azure AI Search integration via VS Code extension

Both approaches share the same core components (prompts, citation logic, source processing) while adapting to platform-specific requirements.

---

## Table of Contents

### Part 1: M365 Copilot Agent
1. [Architecture Overview](#architecture-overview)
2. [Comparison: Web App vs M365 Agent](#comparison-web-app-vs-m365-agent)
3. [Shared Components Strategy](#shared-components-strategy)
4. [Implementation Architecture](#implementation-architecture)
5. [Project Structure](#project-structure)
6. [Step-by-Step Implementation](#step-by-step-implementation)
7. [Prompt Sharing Strategy](#prompt-sharing-strategy)
8. [Citation Handling in M365](#citation-handling-in-m365)
9. [Knowledge Sources Configuration](#knowledge-sources-configuration)
10. [API Plugin Development](#api-plugin-development)
11. [Testing Strategy](#testing-strategy)
12. [Deployment Guide](#deployment-guide)

### Part 2: Azure AI Foundry Agent
13. [Azure AI Foundry Overview](#azure-ai-foundry-overview)
14. [Foundry vs M365 Comparison](#foundry-vs-m365-comparison)
15. [Foundry Agent Architecture](#foundry-agent-architecture)
16. [VS Code Extension Setup](#vs-code-extension-setup)
17. [Foundry Agent Implementation](#foundry-agent-implementation)
18. [Azure AI Search Tool Integration](#azure-ai-search-tool-integration)
19. [Foundry Agent Deployment](#foundry-agent-deployment)

---

## Architecture Overview

### High-Level Architecture Diagram

```
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

---

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

---

## Shared Components Strategy

### Core Philosophy

The key to maintaining both solutions is a **shared core** with **platform-specific adapters**:

```
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

---

## Implementation Architecture

### M365 Agent Package Structure

```
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

---

## Project Structure

### Recommended Monorepo Layout

```
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

---

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

---

## Prompt Sharing Strategy

### How Prompts Are Used in Each Platform

```
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

---

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

---

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

---

## Testing Strategy

### Test Matrix

```
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

---

## Deployment Guide

### Prerequisites

1. **Microsoft 365 Copilot License** - Required for testing and deployment
2. **Azure Subscription** - For hosting API Plugin backend
3. **Teams Admin Access** - For sideloading during development
4. **Microsoft 365 Agents Toolkit** - VS Code extension for development

### Deployment Steps

```
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

---

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

---

## Next Steps

1. **Phase 1 (Week 1):** Extract shared components and restructure repository
2. **Phase 2 (Week 2):** Create M365 agent package structure and manifests
3. **Phase 3 (Week 3):** Implement API Plugin backend with shared components
4. **Phase 4 (Week 4):** Testing and deployment

---

---

# Part 2: Azure AI Foundry Agent

---

## Azure AI Foundry Overview

Azure AI Foundry (formerly Azure AI Studio) provides a unified platform for building, deploying, and managing AI agents. The **Foundry Agent Service** enables you to create production-ready agents with built-in orchestration, tool calling, and observability.

### What is Foundry Agent Service?

```
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

---

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

```
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

---

## Foundry Agent Architecture

### Architecture with Shared Components

```
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

---

## VS Code Extension Setup

### Prerequisites

1. **Azure Subscription** with appropriate permissions
2. **VS Code** with Azure AI Foundry extension
3. **Python 3.10+** (for SDK development)
4. **Existing Azure AI Search index** (from your current deployment)

### Installing the Azure AI Foundry Extension

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
3. Search for "Azure AI Foundry" or "Azure AI"
4. Install the extension

```
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

---

## Foundry Agent Implementation

### Project Structure for Foundry Agent

```
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
2. **Create an Agent**:
   - Click "Create an agent" from the home page
   - Enter project name: "Legal-CPR-Agent"
   - Wait for resources to provision (gpt-4o will be auto-deployed)

3. **Configure Agent Instructions**:
   Paste the condensed version of your legal prompts:

```
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
2. Select **Azure AI Search**
3. Choose **Indexes that are not part of this project**
4. Enter your existing search connection:
   - Azure AI Search resource connection: Create new or select existing
   - Endpoint: `https://your-search.search.windows.net`
   - API Key: Your admin key
5. Select your index (e.g., `gptkbindex`)
6. Configure search type: **Hybrid + Semantic** (recommended)
7. Click **Connect**

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

---

## Azure AI Search Tool Integration

### Connecting Your Existing Index

Your Legal RAG already has an Azure AI Search index. Here's how to connect it to Foundry:

```
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

---

## Foundry Agent Deployment

### Deployment Options

```
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

---

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

---

## Combined Implementation Timeline

| Phase | Week | Web App | M365 Agent | Foundry Agent |
|-------|------|---------|------------|---------------|
| **Phase 1** | 1 | Extract shared components | - | - |
| **Phase 2** | 2 | Update imports | Create manifests | Create project |
| **Phase 3** | 3 | - | Implement API Plugin | Connect AI Search |
| **Phase 4** | 4 | Test shared components | Test in Teams | Test in playground |
| **Phase 5** | 5 | - | Deploy to org | Deploy agent |

---

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

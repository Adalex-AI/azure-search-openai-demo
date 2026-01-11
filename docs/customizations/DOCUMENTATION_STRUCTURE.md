# Documentation Structure: Legal RAG System

This document describes the current documentation organization and what each file covers.

## 📋 Active Documentation

### 1. **README.md** - Customizations Overview

**Purpose**: Main entry point for understanding all custom features

**Contents**:

- What was built (Phase 1 & 2)
- System architecture overview link
- Merge-safe architecture explanation
- Custom features (citations, filtering, evaluation)
- Integration points (minimal changes to upstream)
- Upgrading from upstream guidelines
- Test status and evaluation results

**When to Use**: Starting point for new developers, understanding feature scope

***

### 2. **SYSTEM_ARCHITECTURE.md** - As-Built Architecture & Design

**Purpose**: Comprehensive system design documentation with diagrams

**Contents**:

- End-to-end system architecture diagram
- Data flow sequence diagram (user query → answer)
- Component breakdown (frontend + backend)
- Phase 2 scraping pipeline architecture
- Authentication & security model (OIDC flow)
- Technology stack
- Key metrics & performance
- Future capabilities

**When to Use**: Understanding overall system design, integration points, data flow

***

### 3. **DEPLOYMENT_AND_OPERATIONS.md** - What Was Deployed & How to Operate

**Status**: ✅ **DEPLOYED & OPERATIONAL**

**Purpose**: Production deployment setup, monitoring, maintenance, and troubleshooting

**Contents**:

- **What Was Deployed**: GitHub Actions workflow (the ONLY deployment option used)
  - Weekly automation schedule (Sundays 00:00 UTC)
  - Configuration details (batch size, delays, retries)
  - GitHub secrets and authentication
  - Performance metrics & pipeline duration

- **Local Development**:
  - Setup and prerequisites
  - Testing the pipeline locally
  - Manual GitHub Actions workflow triggers

- **Operations & Monitoring**:
  - Health checks (workflow status, index verification)
  - Weekly/monthly/quarterly maintenance tasks
  - Pipeline updates and deployment

- **Troubleshooting**:
  - 6 common issues with solutions
  - Log locations and artifact access

**When to Use**: Setting up production, monitoring, maintenance, troubleshooting issues

***

## 🏛️ Archived Documentation

### **PHASE_2_SCRAPER_AUTOMATION.md** (Archived)

**Location**: `.archive/PHASE_2_SCRAPER_AUTOMATION.md`

**Reason Archived**: Content consolidated into [DEPLOYMENT_AND_OPERATIONS.md](./DEPLOYMENT_AND_OPERATIONS.md)

**Original Purpose**: Detailed Phase 2 GitHub Actions workflow documentation

**What Happened**:

- All workflow configuration merged into DEPLOYMENT_AND_OPERATIONS.md
- Phase 2 is no longer presented as an option - it's the deployed system
- Single source of truth approach: operations doc now covers deployed solution

**To Access**: If historical reference needed: `docs/customizations/.archive/PHASE_2_SCRAPER_AUTOMATION.md`

***

## 📚 Related Documentation

These documents are in other locations but referenced by customizations docs:

| Document | Location | Purpose |
|----------|----------|---------|
| System Evaluation | `docs/legal_evaluation.md` | Legal RAG quality metrics (95% precedent matching) |
| Data Ingestion | `docs/data_ingestion.md` | General document processing pipeline |
| Architectural Details | `docs/architecture.md` | Overall application architecture |
| Legal Customizations | `docs/customizations/README.md` | This folder - all custom features |

***

## 🎯 Documentation Philosophy

The documentation is organized around **what was actually deployed**:

### ✅ What We Document

1. **Deployed Systems**: GitHub Actions weekly automation
1. **How to Operate**: Setup, monitoring, troubleshooting
1. **How to Develop**: Local testing, modifying scripts
1. **What Was Built**: Architecture and components

### ❌ What We Don't Document

Alternative deployment options that weren't implemented:

- Azure Container Apps (removed - not deployed)
- Azure Functions (removed - not deployed)
- Multiple deployment paths (removed - clarity matters)

**Rationale**: Single source of truth. When you read the docs, you see what's actually running in production, not theoretical options.

***

## 🔍 Finding Information

**If you want to...**

| Goal | Read | Section |
|------|------|---------|
| Understand the system | README.md + SYSTEM_ARCHITECTURE.md | All |
| Set up production | DEPLOYMENT_AND_OPERATIONS.md | "What Was Deployed" + "Local Development" |
| Monitor/maintain | DEPLOYMENT_AND_OPERATIONS.md | "Operations & Monitoring" + "Maintenance" |
| Fix a problem | DEPLOYMENT_AND_OPERATIONS.md | "Troubleshooting" |
| See data flow | SYSTEM_ARCHITECTURE.md | "Data Flow Sequence Diagram" |
| Understand components | SYSTEM_ARCHITECTURE.md | "Component Architecture" |
| Check evaluation metrics | README.md | "📊 Legal Evaluation Results" |
| Learn about features | README.md | "✨ Custom Features" |

***

## 📊 Documentation Statistics

| Metric | Value |
|--------|-------|
| **Active MD Files** | 3 |
| **Archived MD Files** | 1 |
| **Total Content** | ~4,000 lines |
| **Diagrams** | 5+ ASCII architecture diagrams |
| **Code Examples** | 40+ command snippets |
| **Troubleshooting Issues** | 6 with solutions |
| **Deployment Status** | ✅ Fully Deployed |

***

## 🔄 When to Update Documentation

**Update README.md when**:

- New custom features added
- Integration points change
- Feature flags modified
- Evaluation metrics improve

**Update SYSTEM_ARCHITECTURE.md when**:

- Component structure changes
- Technology stack changes
- Data flow changes

**Update DEPLOYMENT_AND_OPERATIONS.md when**:

- Deployment process changes
- Monitoring procedures change
- New troubleshooting issues discovered
- Configuration parameters change
- Maintenance schedules change

**Archive a doc when**:

- Approach deprecated or replaced
- Feature no longer in use
- Documented only as historical reference

***

## 📝 Version History

| Date | Change | Commit |
|------|--------|--------|
| 2026-01-04 | Consolidated Phase 2 docs, focused on GitHub Actions deployment | 1a5f1fb |
| 2026-01-04 | Added as-built system architecture documentation | 3cc6702 |
| 2025-12-24 | Initial Legal Evaluation Framework v2.0 | Earlier |

***

## 💡 Key Takeaways

1. **Single Source of Truth**: DEPLOYMENT_AND_OPERATIONS.md describes the deployed system (GitHub Actions)
1. **No Alternatives**: Removed Container Apps and Functions options - reduces confusion
1. **Archived, Not Deleted**: Historical docs preserved in `.archive/` for reference
1. **Comprehensive Architecture**: SYSTEM_ARCHITECTURE.md provides design overview
1. **Easy Navigation**: README.md serves as entry point to all customizations

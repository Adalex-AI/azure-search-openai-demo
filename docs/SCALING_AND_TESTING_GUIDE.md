# Scaling & Testing Guide for Civil Procedure Copilot

This guide covers how to scale up your Legal RAG solution in Azure and test it with multiple users before going to production.

## 📋 Table of Contents

- [Current Configuration Summary](#current-configuration-summary)
- [Pre-Testing Checklist](#pre-testing-checklist)
- [Azure Resource Scaling](#azure-resource-scaling)
- [Load Testing with Locust](#load-testing-with-locust)
- [Monitoring During Tests](#monitoring-during-tests)
- [Scaling Recommendations by User Count](#scaling-recommendations-by-user-count)
- [Cost Management](#cost-management)
- [Common Bottlenecks & Solutions](#common-bottlenecks--solutions)

***

## Current Configuration Summary

Your Civil Procedure Copilot is currently deployed with:

| Resource | Current Config | Details |
|----------|---------------|---------|
| **Application URL** | [capps-backend-ot6tupm5qi5wy](https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io) | Container Apps (eastus2) |
| **OpenAI Model** | gpt-5-nano | 1.5M TPM capacity, GlobalStandard |
| **Search Agent Model** | gpt-4.1-mini (searchagent) | 150k TPM capacity |
| **Embedding Model** | text-embedding-3-large | 200K TPM, 3072 dimensions |
| **AI Search** | Basic SKU | 1 replica, 1 partition |
| **Semantic Ranker** | Standard | Unlimited queries (paid tier) |
| **Container Apps** | Consumption | 1 CPU, 2GB RAM |
| **Authentication** | Enabled | Microsoft Entra ID |

### OpenAI Deployments Available

| Deployment | Model | Capacity (TPM) | Use Case |
|------------|-------|----------------|----------|
| `gpt-5-nano` | gpt-5-nano | 1.5M | Primary chat (scaled) |
| `gpt-5-mini` | gpt-5-mini | 1.5M | Higher quality alternative |
| `searchagent` | gpt-4.1-mini | 150k | Agentic retrieval & Evaluations |
| `text-embedding-3-large` | text-embedding-3-large | 200K | Vector search |

> **Capacity Assessment**: With **1.5M TPM** on gpt-5-nano, you can support **~1,500 concurrent conversations** (assuming 1K tokens per exchange). Your model deployment is ready for enterprise-scale testing.

***

## Pre-Testing Checklist

Before inviting testers, ensure:

- [x] **Authentication configured** - Microsoft Entra ID enabled
- [x] **Semantic ranker upgraded** - Standard tier (unlimited queries)
- [ ] **Document access granted** - Users/groups have ACL permissions
- [ ] **Application URL shared** - Send to testers with login instructions
- [ ] **Monitoring verified** - Application Insights is tracking requests

### Check Current Configuration

```bash
# View current Azure environment settings
azd env get-values

# Your current key settings:
# AZURE_OPENAI_CHATGPT_DEPLOYMENT=gpt-5-nano (250K TPM)
# AZURE_SEARCH_SEMANTIC_RANKER=standard (unlimited)
# AZURE_SEARCH_SERVICE=cpr-rag (Basic SKU)
# DEPLOYMENT_TARGET=containerapps
```

***

## Azure Resource Scaling

### 1. Azure OpenAI Capacity

Your current setup uses **gpt-5-nano with 1.5M TPM** - sufficient for enterprise-scale testing (~1,500 concurrent users).

#### Current Deployments (Already Provisioned)

| Model | Capacity | When to Use |
|-------|----------|-------------|
| gpt-5-nano (1.5M) | Primary | High-scale production use |
| gpt-5-mini (1.5M) | Alternative | Better reasoning quality |
| searchagent (150k) | Agentic | Complex multi-step queries & Eval |

#### Deployment Update (Completed)

You have successfully upgraded capacity:

*   **Deployment**: `gpt-5-nano`
*   **SKU**: GlobalStandard (Scaled)
*   **Rate Limit**: 1,500,000 TPM

No further model switching is required for throughput, though `gpt-5-mini` may still optionally be used if answer quality needs improvement.

#### Increase Capacity (If Needed)

```bash
# Check current quota in Azure OpenAI Studio
# https://oai.azure.com/ → Quotas tab

# If you need more TPM, increase via Azure CLI:
az cognitiveservices account deployment update \
  --name cog-gz2m4s637t5me-us2 \
  --resource-group rg-cpr-rag \
  --deployment-name gpt-5-nano \
  --sku-capacity 500  # Increase from 250K to 500K TPM
```

#### Check Regional Quotas

Different Azure regions have different quotas. If you're hitting limits:

1. Go to [Azure OpenAI Studio](https://oai.azure.com/) → **Quotas**
1. Check available TPM for your model in eastus2
1. Your GlobalStandard SKU has regional flexibility

#### Multi-Region Load Balancing (For High Traffic)

If you need more than your region's maximum TPM:

```bash
# Option 1: Azure API Management load balancer
# See: https://learn.microsoft.com/azure/developer/python/get-started-app-chat-scaling-with-azure-api-management

# Option 2: Container-based load balancing
# See: https://learn.microsoft.com/azure/developer/python/get-started-app-chat-scaling-with-azure-container-apps
```

### 2. Azure AI Search

Your current setup: **Basic SKU** with 1 replica, **Standard semantic ranker** (unlimited queries).

✅ **Semantic Ranker**: Already upgraded to Standard - no query limits!

#### Scale Search Service (Only If Needed)

```bash
# Your current config is sufficient for most testing scenarios
# Basic SKU: 2GB storage, 3 indexes, good for ~1M small documents

# Upgrade SKU only if you need:
# - More storage (Standard = 25GB per partition)
# - Higher query throughput
# - More replicas for availability

# WARNING: Cannot change SKU of existing service - requires new service + re-indexing
azd env set AZURE_SEARCH_SERVICE_SKU standard
azd provision
```

#### Add Search Replicas (For High Query Volume)

If you see search throttling during testing, add replicas:

```bash
# Add replica via Azure CLI (no reindexing needed)
az search service update \
  --name cpr-rag \
  --resource-group rg-cpr-rag \
  --replica-count 2
```

| Replicas | Effect | Cost Impact |
|----------|--------|-------------|
| 1 (current) | Baseline | ~$2.50/day |
| 2 | 2x query throughput | ~$5/day |
| 3 | 3x throughput + 99.9% SLA | ~$7.50/day |

### 3. Container Apps / App Service

Your current setup: **Consumption plan** with 1 CPU, 2GB RAM (scales to zero when idle).

#### Container Apps Scaling Options

```bash
# Current: Consumption plan (scales 0-10 replicas automatically)
# Cost: Pay only for active usage

# Upgrade to Dedicated workload for consistent performance (no cold starts)
azd env set AZURE_CONTAINER_APPS_WORKLOAD_PROFILE D4
azd provision

# Available profiles: D4, D8, D16, D32, E4, E8, E16, E32
# See: https://learn.microsoft.com/azure/container-apps/workload-profiles-overview
```

#### Increase CPU/Memory (Edit Bicep)

If containers are running out of memory, edit `infra/main.bicep` line ~626:

```bicep
// Find acaBackend module and update:
containerCpuCoreCount: '2.0'  // Increase from 1.0
containerMemory: '4Gi'        // Increase from 2Gi
```

Then redeploy: `azd provision`

***

## Load Testing with Locust

Before inviting real users, run load tests to identify bottlenecks.

### Setup

```bash
# Install locust
source .venv/bin/activate
pip install locust
```

### Update Load Test Questions (Legal Domain)

Edit `locustfile.py` to use legal questions:

```python
import random
import time

from locust import HttpUser, between, task

class LegalChatUser(HttpUser):
    wait_time = between(5, 20)

    @task
    def ask_legal_question(self):
        self.client.get("/", name="home")
        time.sleep(self.wait_time())

        # Legal domain questions for Civil Procedure Copilot
        first_question = random.choice([
            "What are the time limits for filing a defence under CPR Part 15?",
            "How do I apply for summary judgment under CPR Part 24?",
            "What documents must be disclosed in standard disclosure?",
            "What are the grounds for setting aside a default judgment?",
            "How do I make a Part 36 offer?",
            "What is the procedure for witness statements under CPR Part 32?",
            "When can costs be awarded on an indemnity basis?",
            "What are the requirements for a claim form under Part 7?",
        ])

        response = self.client.post(
            "/chat",
            name="legal question",
            json={
                "messages": [{"content": first_question, "role": "user"}],
                "context": {
                    "overrides": {
                        "retrieval_mode": "hybrid",
                        "semantic_ranker": True,
                        "top": 5,
                        "suggest_followup_questions": True,
                    },
                },
            },
        )

        if response.status_code == 200:
            time.sleep(self.wait_time())
            # Follow up question
            follow_up = random.choice(response.json().get("context", {}).get("followup_questions", ["Tell me more"]))
            result_message = response.json().get("message", {}).get("content", "")

            self.client.post(
                "/chat",
                name="follow up",
                json={
                    "messages": [
                        {"content": first_question, "role": "user"},
                        {"content": result_message, "role": "assistant"},
                        {"content": follow_up, "role": "user"},
                    ],
                    "context": {
                        "overrides": {
                            "retrieval_mode": "hybrid",
                            "semantic_ranker": True,
                            "top": 5,
                        },
                    },
                },
            )
```

### Run Load Test

```bash
# Start locust
locust -f locustfile.py LegalChatUser

# Open browser to http://localhost:8089
```

#### Locust Settings by Test Phase

| Phase | Users | Spawn Rate | Duration | Target |
|-------|-------|------------|----------|--------|
| **Smoke Test** | 5 | 1/sec | 5 min | Verify basic functionality |
| **Small Team** | 20 | 2/sec | 15 min | Small law firm scenario |
| **Department** | 50 | 5/sec | 30 min | Legal department scenario |
| **Enterprise** | 100+ | 10/sec | 1 hour | Large firm scenario |

#### Test Against Your Deployment

```bash
# Test against your Azure deployment
# Enter your Container Apps URL (without trailing slash):
# https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io

# For local testing first:
# ./app/start.sh
# Then use http://localhost:50505
```

***

## Monitoring During Tests

### Real-Time Monitoring Dashboard

```bash
# Open Application Insights dashboard
azd monitor
```

### Key Metrics to Watch

| Metric | Location | Warning Threshold |
|--------|----------|-------------------|
| **Response Time** | App Insights → Performance | >10 seconds |
| **Error Rate** | App Insights → Failures | >5% |
| **OpenAI Rate Limits** | Azure OpenAI → Metrics | 429 errors |
| **Search Latency** | AI Search → Metrics | >500ms |
| **CPU Usage** | Container Apps → Metrics | >80% |
| **Memory Usage** | Container Apps → Metrics | >80% |

### Check for Rate Limiting

```bash
# Look for 429 errors in logs
az containerapp logs show \
  --name capps-backend-ot6tupm5qi5wy \
  --resource-group rg-hbalapatabendi-3200 \
  --follow | grep -i "429\|rate\|throttl"
```

### Application Insights Queries

In Azure Portal → Application Insights → Logs:

```kusto
// Request latency distribution
requests
| where timestamp > ago(1h)
| summarize percentiles(duration, 50, 90, 95, 99) by bin(timestamp, 5m)
| render timechart

// Error rate over time
requests
| where timestamp > ago(1h)
| summarize total=count(), failed=countif(success == false) by bin(timestamp, 5m)
| extend errorRate = failed * 100.0 / total
| project timestamp, errorRate
| render timechart

// OpenAI dependency calls
dependencies
| where timestamp > ago(1h)
| where name contains "openai"
| summarize avg(duration), count() by bin(timestamp, 5m), resultCode
| render timechart
```

***

## Scaling Recommendations by User Count

Use the following table to plan your infrastructure based on the number of **concurrent users** (users actively asking questions at the same moment).

### Summary Table: User Count vs. Infrastructure

| Concurrent Users | OpenAI TPM (Tokens/Min) | AI Search Replicas | App Service Plan |
| :--- | :--- | :--- | :--- |
| **< 30** (Pilot/Dev) | **30k** (Default/Basic) | **1** (Basic SKU) | **B1 / Consumption** |
| **50 - 100** (SMB) | **100k - 150k** | **2** (Standard SKU) | **P1v3 / D4** (Min 2 instances) |
| **100 - 500** (Enterprise) | **500k+** | **3+** | **P2v3 / D8** (Auto-scale enabled) |
| **1,500+** (Large Scale) | **1.5M+** or PTU | **5+** | **P3v3** (Multiple regions) |

### Steps to Scale

#### 1. Calculate Your Load (TPM)

*   **Formula**: `Users * (Tokens per Query) = Required TPM`.
*   *Example*: 100 users * 1,000 tokens/query = **100k TPM** required.
*   *Action*: Increase `chatGptDeploymentCapacity` in parameters.

#### 2. Scale Azure AI Search (QPS)

*   **Rule**: 1 Standard Replica handles ~10-15 Queries Per Second (QPS) with Semantic Ranker enabled.
*   *Action*: For >50 concurrent users, run:

    ```bash
    az search service update --replica-count 2 --resource-group rg-cpr-rag --name cpr-rag
    ```

#### 3. Scale App Hosting (Concurrency)

*   **Rule**: A single Python container (Uvicorn) handles ~4-10 concurrent requests efficiently.
*   *Action*: Set `Minimum Instances` to `Users / 10`.

    ```bash
    # Switch to Dedicated Profile D4 for stable performance
    azd env set AZURE_CONTAINER_APPS_WORKLOAD_PROFILE D4
    azd provision
    ```

***

## Cost Management

### Estimated Monthly Cost Breakdown (East US)

These estimates capture the difference between a low-cost testing environment and a high-performance production setup.

#### 1. Azure AI Search (Primary Cost Driver)

| Feature | Current (Basic) | Recommended (Standard) | Difference |
| :--- | :--- | :--- | :--- |
| **Base Service** | ~$75 / month | ~$250 / month | +$175 |
| **Replicas** | 1 unit included | +$250 per addl. replica | +$250 per unit |
| **Semantic Ranker** | Free (max 1k queries/mo) | ~$500 / month (up to 250k) | +$500 |
| **Total Search Cost** | **~$75 / mo** | **~$750 - $1,000 / mo** | **~$675+** |

#### 2. App Service / Container Apps

| Plan | Current (B1 / Consumption) | Recommended (P1v3 / Dedicated) | Difference |
| :--- | :--- | :--- | :--- |
| **Compute** | ~$13 / month | ~$85 / month | +$72 |
| **Capabilities** | Shared cores, scales to zero | Dedicated cores, auto-scale | |

#### 3. Total Estimated Monthly Bill

| Tier | Services Included | Est. Cost |
| :--- | :--- | :--- |
| **Dev / Pilot** | Basic Search, Consumption Apps, Pay-as-you-go OpenAI | **~$100 - $150 / mo** |
| **Production** | Standard Search (3 replicas), Semantic Ranker, Premium Apps | **~$900 - $1,200 / mo** |

### Monitor Costs

```bash
# Check Azure costs for your resource groups
az consumption usage list --start-date 2026-01-01 --end-date 2026-01-31 \
  --query "[?contains(instanceName, 'cpr-rag') || contains(instanceName, 'gz2m4s637t5me')]" \
  --output table
```

### Set Budget Alerts

1. Go to Azure Portal → **Cost Management + Billing**
1. Click **Budgets** → **Add**
1. Set daily/weekly budget based on testing phase
1. Configure alert emails at 50%, 80%, 100% thresholds

### Cost-Saving Tips During Testing

1. **Scale down after hours**: Reduce capacity when not actively testing
1. **Use Consumption plan**: Scale to zero when idle
1. **Test locally first**: Use `./start.sh` for initial testing
1. **Batch your tests**: Run all load tests in dedicated windows

```bash
# Scale down after testing (evening)
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT gpt-5-nano  # Use smaller model
azd env set AZURE_CONTAINER_APPS_WORKLOAD_PROFILE ""    # Back to consumption
azd provision

# Scale up for testing (morning) 
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT gpt-5-mini  # Better quality
azd provision
```

***

## Common Bottlenecks & Solutions

### 1. OpenAI Rate Limiting (429 Errors)

**Symptoms**: Slow responses, 429 errors, "Rate limit exceeded" messages

**Your situation**: With 30K TPM on gpt-5-nano, you may hit limits with 10+ concurrent users.

**Solutions**:

```bash
# Switch to gpt-5-mini which has 1.5M TPM (50x more capacity!)
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT gpt-5-mini
azd env set AZURE_OPENAI_CHATGPT_MODEL gpt-5-mini
azd deploy

# Or increase gpt-5-nano capacity (if you want to stay on nano)
az cognitiveservices account deployment update \
  --name cog-gz2m4s637t5me-us2 \
  --resource-group rg-cpr-rag \
  --deployment-name gpt-5-nano \
  --sku-capacity 100  # Increase from 30K to 100K TPM
```

### 2. Search Throttling

**Symptoms**: Slow search results, timeouts on complex queries

**Solutions**:

```bash
# Add replicas for query throughput (no reindexing needed!)
az search service update --name cpr-rag --resource-group rg-cpr-rag --replica-count 2

# Check current replicas
az search service show --name cpr-rag --resource-group rg-cpr-rag \
  --query "{sku:sku.name, replicas:replicaCount}"
```

### 3. Container App Cold Starts

**Symptoms**: First request after idle takes 10+ seconds

**Solutions**:

```bash
# Use dedicated workload profile (no cold starts)
azd env set AZURE_CONTAINER_APPS_WORKLOAD_PROFILE D4
azd provision

# Or configure minimum replicas in Bicep
# Edit infra/main.bicep, acaBackend module:
# minReplicas: 1  // Keep 1 replica always running
```

### 4. Memory Pressure

**Symptoms**: OOM errors, slow responses, container restarts

**Solutions**:

```bash
# Increase memory
# Edit infra/main.bicep:
containerMemory: '4Gi'  # Increase from 2Gi
containerCpuCoreCount: '2.0'  # Increase from 1.0
```

### 5. Authentication Failures

**Symptoms**: Users can't log in, consent errors

**Solutions**:

- Grant admin consent for the application (see [SHARING_WITH_USERS.md](SHARING_WITH_USERS.md))
- Check user is invited to the tenant
- Verify API permissions are configured

***

## Testing Workflow Checklist

### Week Before Testing

- [ ] Notify testers with application URL and login instructions
- [ ] Run smoke test with 5 users
- [ ] Verify Application Insights is collecting data
- [ ] Document baseline metrics

### Day Before Testing

- [ ] Scale up resources to expected capacity
- [ ] Run load test matching expected user count
- [ ] Clear any cached errors
- [ ] Send reminder to testers

### During Testing

- [ ] Monitor Application Insights dashboard
- [ ] Watch for 429 errors
- [ ] Track response times
- [ ] Collect user feedback

### After Testing

- [ ] Export metrics and logs
- [ ] Document any issues encountered
- [ ] Scale down resources to save costs
- [ ] Plan improvements for next phase

***

## Quick Reference Commands

```bash
# Check current environment
azd env get-values

# Check OpenAI deployments and capacity
az cognitiveservices account deployment list \
  --name cog-gz2m4s637t5me-us2 \
  --resource-group rg-cpr-rag \
  --query "[].{name:name, model:properties.model.name, capacity:sku.capacity}" -o table

# Check Search service
az search service show --name cpr-rag --resource-group rg-cpr-rag \
  --query "{sku:sku.name, replicas:replicaCount, partitions:partitionCount}"

# Switch to better model (already deployed!)
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT gpt-5-mini
azd env set AZURE_OPENAI_CHATGPT_MODEL gpt-5-mini
azd deploy

# Add search replicas
az search service update --name cpr-rag --resource-group rg-cpr-rag --replica-count 2

# Monitor deployment
azd monitor

# View live container logs
az containerapp logs show \
  --name capps-backend-ot6tupm5qi5wy \
  --resource-group rg-hbalapatabendi-3200 \
  --follow

# Run load test
source .venv/bin/activate
pip install locust
locust -f locustfile.py LegalChatUser
# Open http://localhost:8089
# Enter: https://capps-backend-ot6tupm5qi5wy.delightfulground-1a2f1220.eastus2.azurecontainerapps.io
```

***

## Related Documentation

- [SHARING_WITH_USERS.md](SHARING_WITH_USERS.md) - How to invite testers
- [EMAIL_TEMPLATES_FOR_USERS.md](EMAIL_TEMPLATES_FOR_USERS.md) - Communication templates
- [productionizing.md](productionizing.md) - Full production readiness guide
- [monitoring.md](monitoring.md) - Application Insights setup
- [azure_container_apps.md](azure_container_apps.md) - Container Apps configuration

# Phase 2: GitHub Enterprise Automation Setup

This guide details how to configure the GitHub Enterprise automation for the Legal Document Scraper.

## 1. GitHub Environment Setup

To enable approval gates, you must configure a GitHub Environment.

1.  Go to your repository on GitHub (`https://github.com/adalex-ai/azure-search-openai-demo-2`).
2.  Navigate to **Settings** > **Environments**.
3.  Click **New environment**.
4.  Name it `production`.
5.  Click **Configure environment**.
6.  Under **Deployment protection rules**, check **Required reviewers**.
7.  Search for and select the users or teams who must approve updates to the Azure Search index.
8.  Click **Save protection rules**.

## 2. Azure OIDC Configuration

The workflow uses Azure OIDC (OpenID Connect) for passwordless authentication. You need to create a Federated Credential in Azure.

1.  Go to the Azure Portal and find your User Assigned Managed Identity or App Registration used for deployment.
2.  Navigate to **Federated credentials**.
3.  Click **Add credential**.
4.  Select **GitHub Actions deploying Azure resources**.
5.  Fill in the details:
    *   **Organization**: `adalex-ai`
    *   **Repository**: `azure-search-openai-demo-2`
    *   **Entity type**: `Environment`
    *   **Environment name**: `production`
6.  Click **Add**.

## 3. Repository Secrets

Add the following secrets to your repository (**Settings** > **Secrets and variables** > **Actions**):

| Secret Name | Description |
|-------------|-------------|
| `AZURE_CLIENT_ID` | Client ID of the Managed Identity/App Registration |
| `AZURE_TENANT_ID` | Your Azure Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Your Azure Subscription ID |
| `AZURE_SEARCH_SERVICE` | Name of your Azure AI Search service |
| `AZURE_SEARCH_INDEX` | Name of the index (e.g., `legal-court-rag`) |
| `AZURE_OPENAI_SERVICE` | Name of your Azure OpenAI service |
| `AZURE_OPENAI_EMB_DEPLOYMENT` | Deployment name for embeddings (e.g., `text-embedding-3-large`) |

## 4. Workflow Usage

The workflow is scheduled to run weekly on Sundays. You can also trigger it manually:

1.  Go to the **Actions** tab.
2.  Select **Legal Document Scraper Pipeline**.
3.  Click **Run workflow**.
4.  (Optional) Check **Run in dry-run mode** to test without uploading.

### Approval Process

When the workflow runs:
1.  The `scrape-and-validate` job will execute.
2.  If successful, the `upload-production` job will trigger but wait.
3.  Reviewers will receive a notification to approve the deployment.
4.  Reviewers should check the **Artifacts** (Validation Reports) attached to the workflow run before approving.
5.  Once approved, the upload proceeds.

## 5. Slack/Teams Notifications (Optional)

To add notifications:
1.  Create a Webhook URL in Slack/Teams.
2.  Add it as a secret (e.g., `SLACK_WEBHOOK_URL`).
3.  Update `.github/workflows/legal-scraper.yml` to use a notification action (e.g., `slackapi/slack-github-action`).

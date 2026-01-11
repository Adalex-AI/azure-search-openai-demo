# Legal Court RAG Scraper & Indexer Deployment

This folder contains the necessary scripts and source code to scrape Civil Procedure Rules (CPR), generate embeddings, and update an Azure AI Search index.

## Prerequisites

- Python 3.8+
- Chrome browser (for Selenium scraping)
- Azure AI Search service
- Azure OpenAI service (for embeddings)

## Setup

1.  **Install Dependencies:**

```bash
    pip install -r requirements.txt
    ```

1.  **Environment Configuration:**

    Copy `.env.example` to `.env` and fill in your Azure credentials.

```bash
    cp .env.example .env
    ```

    Edit `.env` with your specific values:

    - `AZURE_SEARCH_SERVICE`: Your Azure Search service URL.
    - `AZURE_SEARCH_KEY`: Your Azure Search admin key.
    - `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint.
    - `AZURE_OPENAI_KEY`: Your Azure OpenAI key.
    - `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`: Deployment name for your embedding model (e.g., `text-embedding-3-large`).

## Usage

The update process consists of three steps: Scraping, Embedding Generation, and Indexing.

### 1. Scrape Data

Run the scraper to fetch the latest Civil Procedure Rules.

```bash
python scripts/scrape/scrape_cpr.py
```

This will download content to `data/civil_rules` and process it into `data/processed`.

### 2. Generate Embeddings

Generate vector embeddings for the processed documents.

```bash
python scripts/indexing/generate_embeddings.py
```

This script reads from `data/processed`, generates embeddings using Azure OpenAI, and saves the results (often updating the JSON files or creating a new consolidated file).

### 3. Upload to Azure Search

Upload the documents and their embeddings to your Azure Search index.

```bash
python scripts/indexing/upload_with_embeddings.py
```

This script checks for changes and uploads new or modified documents to the configured Azure Search index.

## Automation

To automatically check and update the solution, you can schedule these scripts to run sequentially using a cron job or a task scheduler.

**Example Shell Script (`update_search.sh`):**

```bash
#!/bin/bash
cd /path/to/this/folder
source venv/bin/activate  # If using a virtual environment

echo "Starting update process..."

# 1. Scrape
python scripts/scrape/scrape_cpr.py
if [ $? -ne 0 ]; then
    echo "Scraping failed."
    exit 1
fi

# 2. Generate Embeddings
python scripts/indexing/generate_embeddings.py
if [ $? -ne 0 ]; then
    echo "Embedding generation failed."
    exit 1
fi

# 3. Upload
python scripts/indexing/upload_with_embeddings.py
if [ $? -ne 0 ]; then
    echo "Upload failed."
    exit 1
fi

echo "Update completed successfully."
```

## Deploying to Azure

To run this solution in the cloud instead of locally, **Azure Container Apps (Jobs)** is the recommended approach. This allows you to package the scraper and indexer as a Docker container and schedule it to run automatically (e.g., daily or weekly).

### Option 1: Azure Container Apps Job (Recommended)

1.  **Containerize the Application**

    Create a `Dockerfile` in the root of this folder:

```dockerfile
    FROM python:3.11-slim

    # Install Chrome and dependencies for Selenium
    RUN apt-get update && apt-get install -y wget gnupg unzip \
        && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
        && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
        && apt-get update \
        && apt-get install -y google-chrome-stable \
        && rm -rf /var/lib/apt/lists/*

    WORKDIR /app
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    # Create a script to run the full pipeline
    RUN echo '#!/bin/bash\npython scripts/scrape/scrape_cpr.py && python scripts/indexing/generate_embeddings.py && python scripts/indexing/upload_with_embeddings.py' > run_pipeline.sh
    RUN chmod +x run_pipeline.sh

    CMD ["./run_pipeline.sh"]
    ```

1.  **Build and Push Image**

    Build the Docker image and push it to an Azure Container Registry (ACR).

```bash
    az acr build --registry <your-acr-name> --image legal-rag-scraper:v1 .
    ```

1.  **Create the Container App Job**

    Create a scheduled job in Azure Container Apps.

```bash
    az containerapp job create \
      --name legal-rag-scraper-job \
      --resource-group <your-resource-group> \
      --environment <your-aca-environment> \
      --image <your-acr-name>.azurecr.io/legal-rag-scraper:v1 \
      --cron-expression "0 2 * * *" \
      --registry-server <your-acr-name>.azurecr.io \
      --env-vars "AZURE_SEARCH_SERVICE=..." "AZURE_SEARCH_KEY=..." "AZURE_OPENAI_ENDPOINT=..." "AZURE_OPENAI_KEY=..."
    ```

    *Note: Replace the environment variables with your actual secrets or use Key Vault references.*

### Option 2: Azure Functions (Timer Trigger)

Alternatively, you can deploy this as an Azure Function with a Timer Trigger.

1.  Create a new Azure Function App (Python).
1.  Move the logic from `scripts/` into a Timer Trigger function.
1.  **Note:** Selenium in Azure Functions (Consumption Plan) can be challenging due to sandbox limitations. You may need to use the **Premium Plan** or a custom Docker container (similar to Option 1) if you require a full browser instance for scraping.


#!/usr/bin/env python3
"""
Generate Diverse Ground Truth Script
====================================
Generates ground truth Q&A pairs from Azure Search index, ensuring diversity
across different legal sources (CPR, PDs, Court Guides).

Usage:
    python generate_diverse_ground_truth.py --output evals/ground_truth_diverse.jsonl
"""

import asyncio
import json
import os
import random
import argparse
from typing import List, Dict

from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents.aio import SearchClient
from openai import AsyncAzureOpenAI
from rich.console import Console
from rich.progress import Progress

console = Console()

# Target categories/sources to ensure diversity
TARGET_SOURCES = [
    {"name": "CPR", "filter": "category eq 'Civil Procedure Rules and Practice Directions' and search.ismatch('Part', 'sourcepage')"},
    {"name": "Practice Directions", "filter": "category eq 'Civil Procedure Rules and Practice Directions' and search.ismatch('Practice Direction', 'sourcepage')"},
    {"name": "Commercial Court Guide", "filter": "category eq 'Commercial Court'"},
    {"name": "Circuit Commercial Court Guide", "filter": "category eq 'Circuit Commercial Court'"},
    {"name": "TCC Guide", "filter": "category eq 'Technology and Construction Court'"},
    {"name": "Patents Court Guide", "filter": "category eq 'Patents Court'"},
    {"name": "King's Bench Guide", "filter": "category eq 'King''s Bench Division'"}, # Escape single quote
]

async def get_clients():
    """Initialize Azure clients."""
    # Load env vars (simplified, assumes .env or environment is set)
    # In a real run, you might need to load from .env file or azd
    service_name = os.environ.get("AZURE_SEARCH_SERVICE")
    index_name = os.environ.get("AZURE_SEARCH_INDEX")
    openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    openai_deployment = os.environ.get("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "gpt-4o")
    
    if not all([service_name, index_name, openai_endpoint]):
        console.print("[red]Missing environment variables. Please run 'source .venv/bin/activate' and ensure variables are set.[/red]")
        # Try loading from azd as fallback (like in run_direct_evaluation.py)
        import subprocess
        try:
            result = subprocess.run(["azd", "env", "get-values"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v.strip('"')
            
            service_name = os.environ.get("AZURE_SEARCH_SERVICE")
            index_name = os.environ.get("AZURE_SEARCH_INDEX")
            openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            openai_deployment = os.environ.get("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "gpt-4o")
        except Exception:
            pass

    credential = DefaultAzureCredential()
    
    search_client = SearchClient(
        endpoint=f"https://{service_name}.search.windows.net",
        index_name=index_name,
        credential=credential
    )
    
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    openai_client = AsyncAzureOpenAI(
        azure_endpoint=openai_endpoint,
        api_version="2024-12-01-preview",
        azure_ad_token_provider=token_provider
    )
    
    return search_client, openai_client, openai_deployment

async def fetch_documents_for_source(search_client, source_config: Dict, count: int = 5) -> List[Dict]:
    """Fetch random documents for a specific source category."""
    results = []
    try:
        # We use a random skip to get diverse documents if index is large
        # For now, just get top 50 and pick random
        search_results = await search_client.search(
            search_text="*",
            filter=source_config["filter"],
            select=["sourcepage", "content", "category"],
            top=50
        )
        
        docs = []
        async for result in search_results:
            docs.append(result)
            
        if docs:
            # Pick random 'count' documents
            selected = random.sample(docs, min(len(docs), count))
            results.extend(selected)
            
    except Exception as e:
        console.print(f"[yellow]Error fetching for {source_config['name']}: {e}[/yellow]")
        
    return results

async def generate_qa_pair(openai_client, deployment, doc: Dict) -> Dict:
    """Generate a Q&A pair from a document using GPT."""
    
    content = doc.get("content", "")[:2000] # Limit content length
    source = doc.get("sourcepage", "")
    category = doc.get("category", "")
    
    prompt = f"""You are a legal expert creating a test dataset for a RAG system.
    
Based on the following legal text from "{source}" ({category}), generate a specific, difficult question and a comprehensive answer.

TEXT:
{content}

REQUIREMENTS:
1. Question: Should be specific to the rules or guidance in the text.
2. Answer: Must be accurate, use UK legal terminology, and cite the source document.
3. Citations: The answer MUST end with the citation in format: [{source}]
4. Format: Return ONLY a JSON object with "question" and "truth" fields.

Example JSON:
{{
  "question": "What is the time limit for serving a claim form?",
  "truth": "The claim form must be served within 4 months of issue. [{source}]"
}}
"""

    try:
        response = await openai_client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result["source_type"] = category
        result["category"] = category
        return result
    except Exception as e:
        console.print(f"[red]Error generating Q&A: {e}[/red]")
        return None

async def main():
    parser = argparse.ArgumentParser(description="Generate diverse ground truth")
    parser.add_argument("--output", default="evals/ground_truth_diverse.jsonl", help="Output file path")
    parser.add_argument("--count", type=int, default=3, help="Number of questions per source type")
    args = parser.parse_args()
    
    console.print("[bold green]Starting Ground Truth Generation...[/bold green]")
    
    search_client, openai_client, deployment = await get_clients()
    
    all_qa_pairs = []
    
    async with search_client:
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing sources...", total=len(TARGET_SOURCES))
            
            for source in TARGET_SOURCES:
                progress.console.print(f"Fetching documents for: [bold]{source['name']}[/bold]")
                
                docs = await fetch_documents_for_source(search_client, source, count=args.count)
                progress.console.print(f"  Found {len(docs)} documents. Generating Q&A...")
                
                for doc in docs:
                    qa = await generate_qa_pair(openai_client, deployment, doc)
                    if qa:
                        all_qa_pairs.append(qa)
                
                progress.advance(task)
    
    # Save to file
    with open(args.output, "w") as f:
        for qa in all_qa_pairs:
            f.write(json.dumps(qa) + "\n")
            
    console.print(f"[bold green]Successfully generated {len(all_qa_pairs)} Q&A pairs in {args.output}[/bold green]")
    await openai_client.close()

if __name__ == "__main__":
    asyncio.run(main())

# AI Engineering & Python Theory Guide

This guide covers the key AI engineering concepts and Python theory required to understand, manage, and maintain this Legal RAG (Retrieval-Augmented Generation) codebase.

***

## Table of Contents

1. [RAG Architecture Overview](#rag-architecture-overview)
2. [Core AI/ML Concepts](#core-aiml-concepts)
3. [Python Theory & Patterns](#python-theory--patterns)
4. [Azure AI Services Integration](#azure-ai-services-integration)
5. [Prompt Engineering](#prompt-engineering)
6. [Evaluation & Metrics](#evaluation--metrics)
7. [Production Best Practices](#production-best-practices)

***

## RAG Architecture Overview

### What is RAG?

**Retrieval-Augmented Generation (RAG)** is an AI architecture that enhances Large Language Models (LLMs) by providing them with relevant external knowledge at query time, rather than relying solely on their training data.

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG Pipeline                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Query ──► Query Processing ──► Vector Search ──► LLM      │
│       │              │                    │              │       │
│       │         (Rewriting)          (Retrieval)    (Generation) │
│       │              │                    │              │       │
│       └──────────────┴────────────────────┴──────────────┘       │
│                              │                                   │
│                        Response + Citations                      │
└─────────────────────────────────────────────────────────────────┘
```

### This Codebase's RAG Pattern

This application implements a **Chat-Read-Retrieve-Read** pattern:

1. **Query Rewriting**: Transform conversational queries into effective search queries
2. **Retrieval**: Search Azure AI Search index for relevant document chunks
3. **Answer Generation**: Generate response using retrieved context + conversation history

**Key files:**
- [approaches/chatreadretrieveread.py](../app/backend/approaches/chatreadretrieveread.py) - Main chat approach
- [approaches/retrievethenread.py](../app/backend/approaches/retrievethenread.py) - Single-turn ask approach

***

## Core AI/ML Concepts

### 1. Embeddings

**Embeddings** are dense vector representations of text that capture semantic meaning. Similar texts have vectors that are close together in high-dimensional space.

```python
# From prepdocslib/embeddings.py
class OpenAIEmbeddings(ABC):
    """
    Converts text to vector embeddings using OpenAI models.
    
    Supported models:
    - text-embedding-ada-002: 1536 dimensions
    - text-embedding-3-small: 512-1536 dimensions  
    - text-embedding-3-large: 256-3072 dimensions
    """
    
    SUPPORTED_BATCH_AOAI_MODEL = {
        "text-embedding-ada-002": {"token_limit": 8100, "max_batch_size": 16},
        "text-embedding-3-small": {"token_limit": 8100, "max_batch_size": 16},
        "text-embedding-3-large": {"token_limit": 8100, "max_batch_size": 16},
    }
```

**Key concepts:**
- **Dimensionality**: Higher dimensions can capture more nuance but require more storage
- **Cosine similarity**: Measures similarity between vectors (0 = orthogonal, 1 = identical)
- **Token limits**: Models have maximum input sizes measured in tokens

### 2. Vector Search

**Vector search** finds documents based on semantic similarity rather than keyword matching.

```python
# Vector query construction
VectorizedQuery(
    vector=query_embedding,          # The query as a vector
    k_nearest_neighbors=top,         # Number of results  
    fields=embedding_field,          # Field containing document embeddings
    exhaustive=use_semantic_ranker,  # Whether to search all vectors
)
```

**Hybrid Search** combines:
- **Lexical search**: Traditional keyword matching (BM25)
- **Vector search**: Semantic similarity matching
- **Semantic reranking**: Re-scores results using a cross-encoder model

### 3. Tokenization

**Tokenization** splits text into subword units that models can process. This codebase uses `tiktoken`:

```python
import tiktoken

# Get encoding for embedding model
bpe = tiktoken.encoding_for_model("text-embedding-ada-002")

def calculate_token_length(text: str) -> int:
    """Count tokens in text."""
    return len(bpe.encode(text))
```

**Why tokens matter:**
- Models have context window limits (e.g., 128K tokens for GPT-4o)
- Costs are calculated per token
- Chunking strategies must respect token limits

### 4. Chunking / Text Splitting

Large documents must be split into smaller chunks for effective retrieval:

```python
# From prepdocslib/textsplitter.py
class SentenceTextSplitter(TextSplitter):
    """
    Splits text into chunks that:
    - Respect sentence boundaries
    - Stay within token limits
    - Include overlap for context continuity
    """
    
    def __init__(
        self,
        max_tokens_per_section: int = 1000,   # Max tokens per chunk
        sentence_search_limit: int = 100,      # Characters to search for sentence end
        section_overlap: int = 100,            # Overlap between chunks
    ):
```

**Chunking strategies:**
| Strategy | Use Case |
|----------|----------|
| Fixed-size | Simple, predictable chunk sizes |
| Sentence-based | Preserves semantic boundaries |
| Recursive | Tries multiple separators hierarchically |
| Document structure | Uses headings, paragraphs as natural boundaries |

***

## Python Theory & Patterns

### 1. Async/Await (Asynchronous Programming)

This codebase is heavily asynchronous for scalable I/O operations:

```python
from collections.abc import AsyncGenerator

async def run_without_streaming(
    self,
    messages: list[ChatCompletionMessageParam],
    overrides: dict[str, Any],
) -> dict[str, Any]:
    """Non-streaming chat completion."""
    
    # Await async OpenAI call
    response = await self.openai_client.chat.completions.create(
        model=self.chatgpt_deployment,
        messages=messages,
        temperature=0.3,
    )
    return {"answer": response.choices[0].message.content}


async def run_with_streaming(
    self,
    messages: list[ChatCompletionMessageParam],
) -> AsyncGenerator[dict[str, Any], None]:
    """Streaming chat completion using async generators."""
    
    async for chunk in await self.openai_client.chat.completions.create(
        model=self.chatgpt_deployment,
        messages=messages,
        stream=True,
    ):
        yield {"delta": chunk.choices[0].delta.content}
```

**Key async patterns used:**
- `async def` / `await`: For async functions
- `AsyncGenerator`: For streaming responses
- `async with`: For async context managers
- `asyncio.gather()`: For parallel execution

### 2. Abstract Base Classes (ABC)

Abstract classes define interfaces that concrete implementations must follow:

```python
from abc import ABC, abstractmethod

class TextSplitter(ABC):
    """Abstract base class for text splitters."""
    
    @abstractmethod
    def split_pages(self, pages: list[Page]) -> Generator[SplitPage, None, None]:
        """All splitters must implement this method."""
        pass


class SentenceTextSplitter(TextSplitter):
    """Concrete implementation."""
    
    def split_pages(self, pages: list[Page]) -> Generator[SplitPage, None, None]:
        # Actual implementation
        for page in pages:
            yield from self._split_page(page)
```

### 3. Dataclasses

Dataclasses reduce boilerplate for data containers:

```python
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Document:
    """Represents a retrieved document chunk."""
    id: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    sourcepage: Optional[str] = None
    sourcefile: Optional[str] = None
    score: Optional[float] = None
    reranker_score: Optional[float] = None
    
    def serialize_for_results(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id or "",
            "content": self.content or "",
            "score": float(self.score or 0.0),
        }
```

### 4. Type Hints

Modern Python typing for better code quality:

```python
from typing import Any, Optional, Union, TypedDict
from collections.abc import Awaitable, AsyncGenerator

# Type aliases
ChatMessages = list[dict[str, str]]

# TypedDict for structured dictionaries
class ExtraArgs(TypedDict, total=False):
    dimensions: int
    temperature: float

# Union types for multiple possibilities  
def process(data: Union[str, bytes]) -> Optional[dict[str, Any]]:
    ...

# Generic async callables
ComputeEmbedding = Callable[[str], Awaitable[list[float]]]
```

### 5. Context Managers

Resource management with `with` statements:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_search_client():
    """Async context manager for search client."""
    client = SearchClient(endpoint, index_name, credential)
    try:
        yield client
    finally:
        await client.close()

# Usage
async with get_search_client() as client:
    results = await client.search(query)
```

### 6. Generators

Memory-efficient iteration for large datasets:

```python
from collections.abc import Generator

def split_text(text: str, chunk_size: int) -> Generator[str, None, None]:
    """Yield chunks without loading all into memory."""
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]

# Process chunks lazily
for chunk in split_text(large_document, 1000):
    process_chunk(chunk)
```

### 7. Decorators

Function modification patterns used in the codebase:

```python
from functools import wraps
from quart import request

def authenticated(func):
    """Decorator to require authentication."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        auth_helper = current_app.config.get("auth_helper")
        if auth_helper and not await auth_helper.check_auth(request):
            return error_response(401, "Unauthorized")
        return await func(*args, **kwargs)
    return wrapper

# Usage
@bp.route("/chat", methods=["POST"])
@authenticated
async def chat():
    ...
```

### 8. Retry Logic with Tenacity

Handling transient failures:

```python
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from openai import RateLimitError

async def create_embedding_with_retry(self, text: str) -> list[float]:
    """Create embedding with exponential backoff on rate limits."""
    
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_random_exponential(min=15, max=60),
        stop=stop_after_attempt(15),
        before_sleep=self.before_retry_sleep,
    ):
        with attempt:
            return await self._create_embedding(text)
```

***

## Azure AI Services Integration

### Azure OpenAI

```python
from openai import AsyncAzureOpenAI
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider

# Create client with Entra ID authentication
credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)

openai_client = AsyncAzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version="2024-12-01-preview",
    azure_ad_token_provider=token_provider,
)

# Chat completion
response = await openai_client.chat.completions.create(
    model="gpt-4o",  # deployment name
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
    temperature=0.3,
)
```

### Azure AI Search

```python
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery

search_client = SearchClient(
    endpoint="https://your-search.search.windows.net",
    index_name="your-index",
    credential=credential,
)

# Hybrid search with vector and keyword
results = await search_client.search(
    search_text=query_text,           # Keyword search
    vector_queries=[
        VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=50,
            fields="embedding",
        )
    ],
    query_type="semantic",            # Enable semantic ranking
    semantic_configuration_name="default",
    top=10,
)
```

### Azure Document Intelligence

For document parsing during ingestion:

```python
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient

doc_client = DocumentIntelligenceClient(
    endpoint=os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"],
    credential=credential,
)

# Analyze PDF document
poller = await doc_client.begin_analyze_document(
    model_id="prebuilt-layout",
    document=pdf_bytes,
)
result = await poller.result()

# Extract text with layout information
for page in result.pages:
    for line in page.lines:
        print(line.content)
```

***

## Prompt Engineering

### Prompty Format

This codebase uses the `.prompty` format for prompt management:

```yaml
---
name: Chat
description: Answer questions using text sources.
model:
    api: chat
    parameters:
        temperature: 0.2
sample:
    user_query: What are disclosure obligations?
---
system:
You are an expert legal assistant...

{% if sources %}
Sources:
{% for source in sources %}
{{ source }}
{% endfor %}
{% endif %}

user:
{{ user_query }}
```

**Key features:**
- YAML frontmatter for configuration
- Jinja2 templating for dynamic content
- Sample data for testing
- Separation of system/user/assistant roles

### Prompt Loading

```python
import prompty
from pathlib import Path

class PromptyManager:
    PROMPTS_DIRECTORY = Path(__file__).parent / "prompts"
    
    def load_prompt(self, path: str):
        """Load prompty file."""
        return prompty.load(self.PROMPTS_DIRECTORY / path)
    
    def render_prompt(self, prompt, data) -> list[dict]:
        """Render prompt with data."""
        return prompty.prepare(prompt, data)
```

### Prompt Best Practices for Legal RAG

1. **Grounding instructions**: Require citations, discourage hallucination
2. **Domain terminology**: Include glossary of legal terms
3. **Context awareness**: Handle court-specific vs. general rules
4. **Citation format**: Enforce consistent citation style `[1][2][3]`

***

## Evaluation & Metrics

### Legal RAG Metrics

This codebase includes specialized evaluation metrics:

```python
# From evals/test_legal_metrics.py

def evaluate_precedent_matching(response: str, expected_sources: list[str]) -> float:
    """Check if correct source documents are cited."""
    citations = extract_citations(response)
    matched = sum(1 for src in expected_sources if src in citations)
    return matched / len(expected_sources) if expected_sources else 0.0

def evaluate_legal_terminology(response: str) -> float:
    """Verify proper use of UK legal terminology."""
    terms = ["claimant", "defendant", "disclosure", "CPR", "Part"]
    found = sum(1 for term in terms if term.lower() in response.lower())
    return found / len(terms)

def evaluate_statute_citation(response: str) -> float:
    """Check for proper CPR Part/Rule citations."""
    pattern = r"CPR\s+(Part\s+)?\d+(\.\d+)?|Rule\s+\d+\.\d+"
    matches = re.findall(pattern, response)
    return 1.0 if matches else 0.0
```

### Ground Truth Format

```jsonl
{"question": "What is standard disclosure?", 
 "answer": "Standard disclosure requires...", 
 "sources": ["CPR_Part_31.pdf"]}
```

### Running Evaluations

```bash
cd evals
python run_direct_evaluation.py
```

***

## Production Best Practices

### 1. Error Handling

```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
async def robust_search(query: str) -> list[Document]:
    try:
        results = await search_client.search(query)
        return [Document(**r) for r in results]
    except ResourceNotFoundError:
        logging.error("Search index not found")
        return []
    except Exception as e:
        logging.exception(f"Search failed: {e}")
        raise
```

### 2. Observability

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor

# Enable Azure Monitor telemetry
configure_azure_monitor()

# Auto-instrument OpenAI calls
OpenAIInstrumentor().instrument()
```

### 3. Cost Management

```python
# Track token usage
@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    @property
    def estimated_cost(self) -> float:
        """Estimate cost in USD."""
        # GPT-4o pricing (as of 2024)
        prompt_cost = self.prompt_tokens * 0.005 / 1000
        completion_cost = self.completion_tokens * 0.015 / 1000
        return prompt_cost + completion_cost
```

### 4. Rate Limiting

```python
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.tokens = requests_per_minute
        self.last_update = datetime.now()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        async with self.lock:
            now = datetime.now()
            elapsed = (now - self.last_update).total_seconds()
            self.tokens = min(self.rpm, self.tokens + elapsed * self.rpm / 60)
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) * 60 / self.rpm
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1
```

### 5. Security

```python
# Always use managed identity in production
from azure.identity.aio import ManagedIdentityCredential

credential = ManagedIdentityCredential()

# Validate and sanitize user input
def sanitize_query(query: str) -> str:
    # Remove potential injection patterns
    query = query.strip()[:1000]  # Limit length
    query = re.sub(r'[<>{}]', '', query)  # Remove suspicious chars
    return query
```

***

## Key Files Reference

| File | Purpose |
|------|---------|
| `app/backend/app.py` | Main Quart application entry point |
| `app/backend/approaches/*.py` | RAG approach implementations |
| `app/backend/approaches/prompts/*.prompty` | Prompt templates |
| `app/backend/prepdocslib/*.py` | Document ingestion library |
| `app/backend/customizations/` | Custom legal domain extensions |
| `evals/*.py` | Evaluation scripts and metrics |
| `infra/*.bicep` | Azure infrastructure as code |

***

## Learning Resources

### AI/ML Fundamentals
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
- [RAG Pattern Overview](https://learn.microsoft.com/azure/search/retrieval-augmented-generation-overview)

### Python
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [Quart Documentation](https://quart.palletsprojects.com/)

### Azure
- [Azure OpenAI Service](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure AI Search](https://learn.microsoft.com/azure/search/)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/)

***

## Quick Command Reference

```bash
# Activate virtual environment
source .venv/bin/activate

# Run backend locally
cd app/backend && quart run -p 50505

# Run frontend
cd app/frontend && npm run dev

# Run tests
pytest tests/ -v

# Run evaluations
cd evals && python run_direct_evaluation.py

# Type checking
cd app/backend && mypy . --config-file=../../pyproject.toml

# Deploy to Azure
azd up
```

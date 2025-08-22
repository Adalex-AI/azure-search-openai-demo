# Data Flow Diagrams - Complete System Analysis

## 1. User Question Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant CourtDetect as Court Detection
    participant Search as Azure Search
    participant DocProc as Document Processor
    participant OpenAI
    participant CitationMap as Citation Mapper

    User->>Frontend: Types question
    Note over User,Frontend: "What are disclosure rules in Circuit Commercial Court?"
    
    Frontend->>Backend: POST /chat
    Note over Backend: Extract query
    
    Backend->>CourtDetect: Detect court in query
    CourtDetect-->>Backend: "Circuit Commercial Court"
    
    Backend->>Search: Search with court filter
    Note over Search: Filter: category eq 'Circuit Commercial Court'<br/>OR 'Civil Procedure Rules'
    
    Search-->>Backend: Return documents (10 results)
    
    Backend->>DocProc: Process each document
    
    loop For each document
        DocProc->>DocProc: Extract subsections
        DocProc->>DocProc: Split if multiple found
    end
    
    DocProc-->>Backend: 15 sources (from 10 docs)
    
    Backend->>CitationMap: Create citation mappings
    Note over CitationMap: [1] = "31.1, CPR Part 31, Disclosure"<br/>[2] = "31.2, CPR Part 31, Disclosure"
    
    Backend->>OpenAI: Send question + sources
    Note over OpenAI: Uses [1], [2], [3] format
    
    OpenAI-->>Backend: Response with citations
    Note over OpenAI: "Disclosure requires... [1]"
    
    Backend->>Backend: Map [1] to full citations
    Backend-->>Frontend: Response + structured sources
    Frontend-->>User: Display answer with clickable citations
```

## 2. Document Indexing Pipeline

```mermaid
graph TD
    subgraph "Document Ingestion"
        Upload[Document Upload] --> Storage[Azure Blob Storage]
        Storage --> DocIntel[Document Intelligence]
        DocIntel --> Extract[Text Extraction]
    end
    
    subgraph "Processing"
        Extract --> Split[Split into Chunks]
        Split --> Detect[Detect Subsections]
        Detect --> Decision{Multiple Subsections?}
        Decision -->|Yes| MultiSplit[Split into Multiple]
        Decision -->|No| Single[Keep as Single]
        MultiSplit --> Enhance[Enhance Metadata]
        Single --> Enhance
    end
    
    subgraph "Indexing"
        Enhance --> Embed[Generate Embeddings]
        Embed --> Fields[Add Fields]
        Fields --> |"id, content, sourcepage,<br/>sourcefile, category,<br/>storageUrl, updated"| Index[Azure Search Index]
    end
    
    subgraph "Your Additions"
        style YourAdd fill:#ffeb3b
        YourAdd[Enhanced Fields]
        YourAdd --> |"subsection_id<br/>is_subsection<br/>original_doc_id"| Index
    end
```

## 3. Citation Creation Flow

```mermaid
flowchart LR
    subgraph "Input Document"
        Doc[Document with Content]
    end
    
    subgraph "Subsection Detection"
        Doc --> Scan[Scan for Patterns]
        Scan --> P1["Pattern: 31.1"]
        Scan --> P2["Pattern: Rule 1.1"]
        Scan --> P3["Pattern: A4.1"]
        Scan --> P4["Pattern: Para 5.2"]
    end
    
    subgraph "Citation Building"
        P1 --> Build1["31.1, CPR Part 31, Rules"]
        P2 --> Build2["Rule 1.1, CPR Part 1, Rules"]
        P3 --> Build3["A4.1, Court Guide, Procedures"]
        P4 --> Build4["Para 5.2, PD 5, Directions"]
    end
    
    subgraph "Storage"
        Build1 --> Map["Citation Map<br/>[1] → 31.1, CPR Part 31, Rules"]
        Build2 --> Map
        Build3 --> Map
        Build4 --> Map
    end
```

## 4. Search and Filter Logic

```mermaid
flowchart TD
    Query[User Query] --> Detect{Court Mentioned?}
    
    Detect -->|Yes| CheckCourt[Check if Court is Category]
    Detect -->|No| DefaultFilter[Use Default Filter]
    
    CheckCourt --> Exists{Category Exists?}
    
    Exists -->|Yes| CourtFilter["Filter:<br/>category = 'Court Name'<br/>OR 'CPR'"]
    Exists -->|No| DefaultFilter
    
    DefaultFilter --> CPRFilter["Filter:<br/>category = 'CPR'<br/>OR null"]
    
    CourtFilter --> Search[Execute Search]
    CPRFilter --> Search
    
    Search --> Results[Search Results]
    
    Results --> Process[Process Each Result]
    Process --> Extract[Extract Subsections]
    Extract --> Final[Final Source List]
```

## 5. Storage URL Redirection Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Search as Azure Search
    participant Storage as Azure Storage

    User->>Frontend: Click citation link
    Note over User,Frontend: Clicks "[31.1, CPR Part 31, Rules]"
    
    Frontend->>Backend: GET /content/31.1
    Note over Backend: Extract path: "31.1"
    
    Backend->>Search: Search for document
    Note over Search: Filter: sourcepage eq '31.1'
    
    Search-->>Backend: Document with storageUrl
    Note over Backend: storageUrl: "https://storage.azure.com/doc123"
    
    Backend->>Backend: Add highlight params
    Note over Backend: URL + "?search=disclosure"
    
    Backend-->>Frontend: HTTP 302 Redirect
    Frontend-->>Storage: Direct request
    Storage-->>User: Document with highlighting
```

## 6. Enhanced Token Processing

```mermaid
graph LR
    subgraph "Original Token Limits"
        O1[Question: 512 tokens]
        O2[Context: 3584 tokens]
        O3[Response: 1024 tokens]
        O4[Total: 4096 tokens]
    end
    
    subgraph "Your Enhanced Limits"
        style YourLimits fill:#4caf50
        N1[Question: 1024 tokens]
        N2[Context: 7168 tokens]
        N3[Response: 8192 tokens]
        N4[Total: 16384 tokens]
    end
    
    O1 --> N1
    O2 --> N2
    O3 --> N3
    O4 --> N4
    
    N4 --> Benefits[Benefits]
    Benefits --> B1[Longer Documents]
    Benefits --> B2[More Sources]
    Benefits --> B3[Detailed Answers]
```

## 7. Error Handling Flow

```mermaid
flowchart TD
    Start[Request Received] --> Try[Try Processing]
    
    Try --> E1{Storage URL Error?}
    E1 -->|Yes| Fallback1[Use Blob Download]
    E1 -->|No| E2{Citation Error?}
    
    E2 -->|Yes| Fallback2[Use Simple Citation]
    E2 -->|No| E3{Search Error?}
    
    E3 -->|Yes| Fallback3[Return Limited Results]
    E3 -->|No| Success[Process Normally]
    
    Fallback1 --> Log1[Log: Storage URL Failed]
    Fallback2 --> Log2[Log: Citation Extract Failed]
    Fallback3 --> Log3[Log: Search Failed]
    
    Log1 --> Continue[Continue Processing]
    Log2 --> Continue
    Log3 --> Continue
    
    Success --> Response[Send Response]
    Continue --> Response
```

## 8. Logging and Debugging Flow

```mermaid
graph TD
    subgraph "Entry Points"
        Chat[/chat endpoint]
        Ask[/ask endpoint]
        Content[/content endpoint]
    end
    
    subgraph "Processing Stages"
        Chat --> L1["🔍 Request received"]
        Ask --> L1
        Content --> L1
        
        L1 --> L2["🎯 Court detected"]
        L2 --> L3["🔍 Search executed"]
        L3 --> L4["📄 Documents found"]
        L4 --> L5["✂️ Subsections extracted"]
        L5 --> L6["🏷️ Citations created"]
        L6 --> L7["🤖 AI processing"]
        L7 --> L8["✅ Response sent"]
    end
    
    subgraph "Debug Output"
        L1 --> D1[Request details]
        L2 --> D2[Court: 'Circuit Commercial']
        L3 --> D3[Filter: category eq '...']
        L4 --> D4[Found: 10 documents]
        L5 --> D5[Split into: 15 sources]
        L6 --> D6[Mapping: [1] = '31.1...']
        L7 --> D7[Tokens used: 4521]
        L8 --> D8[Response time: 2.3s]
    end
```

## Key Data Structures

### Document Object (Enhanced)
```python
{
    "id": "doc_123",
    "content": "31.1 Standard disclosure requires...",
    "sourcepage": "CPR Part 31",
    "sourcefile": "Civil Procedure Rules",
    "category": "Circuit Commercial Court",
    "storageUrl": "https://storage.azure.com/...",
    "updated": "2024-01-15",
    # Your additions:
    "subsection_id": "31.1",
    "is_subsection": True,
    "original_doc_id": "doc_100",
    "citation": "31.1, CPR Part 31, Civil Procedure Rules"
}
```

### Citation Map Structure
```python
{
    "1": "31.1, CPR Part 31, Civil Procedure Rules",
    "2": "31.2, CPR Part 31, Civil Procedure Rules",
    "3": "A4.1, Circuit Commercial Court Guide, Procedures"
}
```

### Response Structure
```python
{
    "answer": "Disclosure in fast track cases...",
    "context": {
        "data_points": {
            "text": [/* structured documents */]
        },
        "thoughts": [/* processing steps */],
        "enhanced_citations": [/* your addition */],
        "citation_map": {/* your addition */}
    }
}
```

These diagrams show how your modifications enhance the data flow at every stage, from initial query to final response!

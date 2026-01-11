# Data Flow Diagrams - Complete System Analysis

## 1. User Question Processing Flow (Enhanced)

```mermaid
sequenceDiagram
    participant User
    participant CategoryUI as Category Dropdown
    participant Frontend
    participant Backend
    participant CourtDetect as Court Detection
    participant Search as Azure Search
    participant DocProc as Document Processor
    participant OpenAI
    participant CitationMap as Citation Mapper

    User->>CategoryUI: Selects "Circuit Commercial Court"
    CategoryUI->>Frontend: Update category filter

    User->>Frontend: Types question
    Note over User,Frontend: "What are disclosure rules in fast track?"

    Frontend->>Backend: POST /chat with category selection
    Note over Backend: category: "Circuit Commercial Court"<br/>query: "disclosure rules fast track"

    Backend->>CourtDetect: Check for court mentions in query
    CourtDetect-->>Backend: No additional court detected

    Backend->>Search: Search with combined filters
    Note over Search: Filter: category eq 'Circuit Commercial Court'<br/>OR 'Civil Procedure Rules'

    Search-->>Backend: Return documents (10 results)

    Backend->>DocProc: Process each document

    loop For each document
        DocProc->>DocProc: Extract subsections
        DocProc->>DocProc: Split if multiple found
        DocProc->>DocProc: Build enhanced citations
    end

    DocProc-->>Backend: 15 sources (from 10 docs)

    Backend->>CitationMap: Create citation mappings + preview content
    Note over CitationMap: [1] = "31.1, CPR Part 31, Disclosure"<br/>preview: "Standard disclosure requires..."

    Backend->>OpenAI: Send question + sources
    Note over OpenAI: Uses [1], [2], [3] format

    OpenAI-->>Backend: Response with citations
    Note over OpenAI: "Disclosure requires... [1]"

    Backend->>Backend: Enhance citations with preview content
    Backend-->>Frontend: Response + structured sources + previews
    Frontend-->>User: Display answer with hoverable citations
```

## 2. Hover Citation Preview Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant CitationSup as Citation Element
    participant Preview as Preview System
    participant SupportingContent as Supporting Content Panel

    User->>CitationSup: Hovers over [1]
    CitationSup->>Frontend: Trigger hover event

    Frontend->>Preview: Extract preview content
    Note over Preview: data-citation-content="Standard disclosure requires..."

    Preview->>Frontend: Display tooltip/preview
    Frontend-->>User: Show quick preview

    Note over User,Frontend: User can read preview without clicking

    alt User wants more details
        User->>CitationSup: Clicks [1]
        CitationSup->>Frontend: Trigger click event
        Frontend->>SupportingContent: Open full citation details
        SupportingContent-->>User: Show complete source information
    end
```

## 3. Category Selection Flow

```mermaid
flowchart TD
    UserInput[User Starts Session] --> CategorySelect{Select Category?}

    CategorySelect -->|Yes| Dropdown[Choose from Dropdown]
    CategorySelect -->|No| AutoDetect[Auto-detect from Query]

    Dropdown --> SpecificCourt[Specific Court Selected]
    Dropdown --> AllCategories[All Categories Selected]

    SpecificCourt --> SetFilter1["Filter: category = 'Selected Court'<br/>OR 'CPR'"]
    AllCategories --> SetFilter2["Filter: No category restriction"]

    AutoDetect --> ParseQuery[Parse Query for Court Names]
    ParseQuery --> CourtFound{Court Detected?}

    CourtFound -->|Yes| ValidateCourt[Validate Court as Category]
    CourtFound -->|No| DefaultFilter[Use Default CPR Filter]

    ValidateCourt --> CourtExists{Category Exists?}
    CourtExists -->|Yes| SetFilter3["Filter: category = 'Detected Court'<br/>OR 'CPR'"]
    CourtExists -->|No| DefaultFilter

    DefaultFilter --> SetFilter4["Filter: category = 'CPR'<br/>OR null"]

    SetFilter1 --> ExecuteSearch[Execute Search]
    SetFilter2 --> ExecuteSearch
    SetFilter3 --> ExecuteSearch
    SetFilter4 --> ExecuteSearch

    ExecuteSearch --> ReturnResults[Return Filtered Results]
```

## 4. Enhanced Citation Creation with Preview Content

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
    end

    subgraph "Citation Building"
        P1 --> Build1["31.1, CPR Part 31, Rules"]
        P2 --> Build2["Rule 1.1, CPR Part 1, Rules"]
        P3 --> Build3["A4.1, Court Guide, Procedures"]
    end

    subgraph "Preview Content Extraction"
        Build1 --> Extract1["Preview: 'Standard disclosure requires...'"]
        Build2 --> Extract2["Preview: 'The overriding objective...'"]
        Build3 --> Extract3["Preview: 'Commercial Court procedures...'"]
    end

    subgraph "Storage with Preview"
        Extract1 --> Map["Citation Map + Previews<br/>[1] → Citation + Preview Text"]
        Extract2 --> Map
        Extract3 --> Map
    end
```

## 5. User Interface Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant CategoryDropdown
    participant QueryInput
    participant AnswerDisplay
    participant CitationHover
    participant DocumentViewer

    User->>CategoryDropdown: Select "High Court"
    CategoryDropdown->>QueryInput: Update context

    User->>QueryInput: Type "What are case management powers?"
    QueryInput->>AnswerDisplay: Submit with category context

    AnswerDisplay->>User: Show answer with citations [1] [2] [3]

    User->>CitationHover: Hover over [1]
    CitationHover->>User: Show preview: "Case management powers include..."

    alt User wants full details
        User->>CitationHover: Click [1]
        CitationHover->>DocumentViewer: Open source document
        DocumentViewer->>User: Show full document with highlighting
    end

    alt User tries different category
        User->>CategoryDropdown: Change to "Commercial Court"
        CategoryDropdown->>QueryInput: Update context
        User->>QueryInput: Ask same question
        QueryInput->>AnswerDisplay: Show different, court-specific results
    end
```

## 6. Storage URL with Category Context

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Search as Azure Search
    participant Storage as Azure Storage

    User->>Frontend: Click citation from "Commercial Court" results
    Note over User,Frontend: Citation: "[A4.1, Commercial Court Guide, Procedures]"

    Frontend->>Backend: GET /content/A4.1
    Note over Backend: Extract path: "A4.1"<br/>Context: Commercial Court

    Backend->>Search: Search with court context
    Note over Search: Filter: sourcepage eq 'A4.1'<br/>AND category eq 'Commercial Court'

    Search-->>Backend: Document with storageUrl
    Note over Backend: storageUrl: "https://storage.azure.com/commercial-court-guide"

    Backend->>Backend: Add highlighting for court-specific terms
    Note over Backend: URL + "?search=case+management+powers"

    Backend-->>Frontend: HTTP 302 Redirect with context
    Frontend-->>Storage: Direct request with highlighting
    Storage-->>User: Commercial Court document with specific highlighting
```

## 7. Category Priority Resolution

```mermaid
flowchart TD
    Start[User Request] --> CheckUI{UI Category Selected?}

    CheckUI -->|Yes, Specific Court| UseSelected[Use Selected Category]
    CheckUI -->|Yes, All Categories| NoFilter[No Category Filter]
    CheckUI -->|No Selection| AutoDetect[Auto-detect from Query]

    UseSelected --> Priority1["Priority 1: Selected Category<br/>+ CPR fallback"]
    NoFilter --> Priority2["Priority 2: No restrictions<br/>Show all categories"]

    AutoDetect --> ParseQuery[Parse Query for Courts]
    ParseQuery --> Found{Court Found?}

    Found -->|Yes| Validate[Validate as Category]
    Found -->|No| Default[Use CPR Default]

    Validate --> Exists{Category Exists?}
    Exists -->|Yes| Priority3["Priority 3: Detected Court<br/>+ CPR fallback"]
    Exists -->|No| Default

    Default --> Priority4["Priority 4: CPR only<br/>Default fallback"]

    Priority1 --> Filter1["category eq 'Selected' OR 'CPR'"]
    Priority2 --> Filter2["No category filter"]
    Priority3 --> Filter3["category eq 'Detected' OR 'CPR'"]
    Priority4 --> Filter4["category eq 'CPR' OR null"]

    Filter1 --> Execute[Execute Search]
    Filter2 --> Execute
    Filter3 --> Execute
    Filter4 --> Execute
```

## 8. Enhanced Logging with User Interactions

```mermaid
graph TD
    subgraph "User Actions"
        CategorySelect[Category Selection] --> L1["🎯 Category: Commercial Court"]
        HoverCitation[Hover Citation] --> L2["👁️ Hover: [1] preview shown"]
        ClickCitation[Click Citation] --> L3["🔗 Click: [1] full details"]
    end

    subgraph "System Processing"
        L1 --> L4["🔍 Filter: category eq 'Commercial Court'"]
        L2 --> L5["📖 Preview: 'Case management powers...'"]
        L3 --> L6["📄 Full content loaded"]
    end

    subgraph "Search Operations"
        L4 --> L7["🔍 Search: 15 results found"]
        L7 --> L8["🎯 Subsections: 23 sources created"]
        L8 --> L9["🏷️ Citations: Enhanced format applied"]
    end

    subgraph "User Experience"
        L5 --> UX1[Quick Preview Available]
        L6 --> UX2[Direct Document Access]
        L9 --> UX3[Professional Citations]
    end
```

## Key Data Structures (Enhanced)

### Document Object with Preview Support

```python
{
    "id": "doc_123",
    "content": "31.1 Standard disclosure requires...",
    "sourcepage": "CPR Part 31", 
    "sourcefile": "Civil Procedure Rules",
    "category": "Circuit Commercial Court",
    "storageUrl": "https://storage.azure.com/...",
    "updated": "2024-01-15",
    # Enhanced fields:
    "subsection_id": "31.1",
    "is_subsection": True,
    "citation": "31.1, CPR Part 31, Civil Procedure Rules",
    "preview_content": "Standard disclosure requires a party to disclose documents...",
    "selected_category": "Circuit Commercial Court"  # User selection context
}
```

### Citation Map with Preview Content

```python
{
    "1": {
        "citation": "31.1, CPR Part 31, Civil Procedure Rules",
        "preview": "Standard disclosure requires a party to disclose documents on which they rely...",
        "category_context": "Circuit Commercial Court"
    },
    "2": {
        "citation": "A4.1, Commercial Court Guide, Case Management",
        "preview": "Case management powers include the power to extend time limits...",
        "category_context": "Commercial Court"
    }
}
```

### Frontend State Management

```typescript
interface AppState {
    selectedCategory: string;           // User dropdown selection
    detectedCourt: string | null;      // Auto-detected from query
    hoverCitationId: string | null;    // Currently hovered citation
    previewContent: string | null;     // Preview text being shown
    activeCitation: string | null;     // Full citation details
}
```

## Benefits of Enhanced Features

### Hover Citations

- **Speed**: Instant preview without navigation
- **Context**: Quick verification of source relevance
- **Efficiency**: Reduced clicks for information gathering

### Category Selection

- **Control**: User can focus on specific court rules
- **Intelligence**: System auto-detects courts from queries
- **Flexibility**: Easy switching between court contexts
- **Accuracy**: Results targeted to relevant jurisdiction

### Combined Impact

- **Professional Workflow**: Matches legal research patterns
- **Reduced Cognitive Load**: Less navigation, more information
- **Improved Accuracy**: Context-aware results
- **Enhanced User Experience**: Intuitive, responsive interface

These enhanced diagrams show how your modifications create a sophisticated legal research platform that understands user intent, provides intelligent assistance, and delivers professional-grade citation management!

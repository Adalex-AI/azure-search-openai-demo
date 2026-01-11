# Citation System - Complete Flow Diagram

## How Citations Work in Your Enhanced System

This document explains the complete journey of how citations are created, processed, displayed, and interacted with through hover previews and category selection.

## Enhanced Citation Creation Flow

```mermaid
graph TD
    Start[User Selects Category & Asks Question] --> CategoryFilter[Apply Category Filter]
    CategoryFilter --> Search[Search Documents]
    Search --> Results[Get Search Results]

    Results --> Loop{For Each Document}

    Loop --> Extract[Extract Subsection Info]
    Extract --> Check{Multiple Subsections?}

    Check -->|Yes| Split[Split Document]
    Split --> Multi[Create Multiple Citations with Previews]
    Multi --> Format1[Format: 'subsection, page, file' + preview content]

    Check -->|No| Single[Keep as Single Source]
    Single --> Format2[Format: 'page, file' or 'subsection, page, file' + preview]

    Format1 --> Store[Store in Citation Map with Preview]
    Format2 --> Store

    Store --> AI[Send to OpenAI with [1], [2], [3] refs]
    AI --> Response[AI Response with [1], [2], [3]]

    Response --> Enhance[Enhance with Hover Data]
    Enhance --> Display[Display with Interactive Citations]
```

## Detailed Step-by-Step Process

### Step 1: Category Selection & Court Detection

Users can select categories or the system auto-detects courts:

```python
# User selects "Commercial Court" from dropdown
# OR system detects "Commercial Court" in query

def build_filter(self, overrides: dict[str, Any], auth_claims: dict[str, Any]):
    include_category = overrides.get("include_category", None)

    if include_category and include_category != "All":
        # User explicitly selected a category
        filters.append(f"category eq '{include_category}'")
    else:
        # Auto-detect court from query
        detected_court = self.detect_court_in_query(original_user_query)
        if detected_court:
            normalized_court = self.normalize_court_to_category(detected_court)
            filters.append(f"(category eq '{normalized_court}' or category eq 'Civil Procedure Rules')")
```

### Step 2: Enhanced Document Search

Search respects category selection:

```python
# User asks: "What are case management powers in Commercial Court?"
# With category: "Commercial Court" selected

results = await search_client.search(
    search_text="case management powers",
    filter="category eq 'Commercial Court' or category eq 'Civil Procedure Rules'",
    top=10
)
```

### Step 3: Subsection Detection with Preview Creation

For each document, extract subsections AND create preview content:

```python
def _extract_multiple_subsections_from_document(self, doc):
    # Example input document:
    # "A4.1 Case Management Powers
    #  The court has power to extend time limits and make case management directions...
    #
    #  A4.2 Pre-Trial Review
    #  The court will conduct a pre-trial review in appropriate cases..."

    subsections = [
        {
            "subsection": "A4.1",
            "content": "The court has power to extend time limits...",
            "preview": "The court has power to extend time limits and make case management directions..."[:100]
        },
        {
            "subsection": "A4.2",
            "content": "The court will conduct a pre-trial review...",
            "preview": "The court will conduct a pre-trial review in appropriate cases..."[:100]
        }
    ]
```

### Step 4: Enhanced Citation Building with Category Context

Create citations that include category information:

```python
def build_enhanced_citation_from_document(self, doc, source_index):
    subsection = "A4.1"
    sourcepage = "Commercial Court Guide"
    sourcefile = "Case Management Procedures"
    category = doc.category  # "Commercial Court"

    # Three-part format with category context
    citation = f"{subsection}, {sourcepage}, {sourcefile}"
    preview = doc.content[:200] + "..." if len(doc.content) > 200 else doc.content

    return {
        "citation": citation,
        "preview": preview,
        "category": category
    }
```

### Step 5: Citation Mapping with Hover Support

Store mapping with preview content for hover functionality:

```python
self.citation_map = {
    "1": {
        "citation": "A4.1, Commercial Court Guide, Case Management Procedures",
        "preview": "The court has power to extend time limits and make case management directions...",
        "category": "Commercial Court",
        "full_content": "A4.1 Case Management Powers\nThe court has power to extend..."
    },
    "2": {
        "citation": "31.1, CPR Part 31, Disclosure Rules",
        "preview": "Standard disclosure requires a party to disclose documents...",
        "category": "Civil Procedure Rules",
        "full_content": "31.1 Standard disclosure\nStandard disclosure requires..."
    }
}
```

### Step 6: AI Processing with Enhanced Context

Send sources to OpenAI with category-aware context:

```text
Sources sent to AI (Commercial Court context):
[1]: The court has power to extend time limits and make case management directions...
[2]: Standard disclosure requires a party to disclose documents on which they rely...

AI Response:
"In Commercial Court proceedings, case management powers include the ability to extend time limits [1].
Standard disclosure obligations still apply [2]."
```

### Step 7: Frontend Display with Interactive Citations

The frontend receives structured data with hover support:

```json
{
  "answer": "In Commercial Court proceedings, case management powers include...",
  "context": {
    "data_points": {
      "text": [
        {
          "id": "doc_1",
          "content": "A4.1 Case Management Powers\nThe court has power to extend...",
          "citation": "A4.1, Commercial Court Guide, Case Management Procedures",
          "preview": "The court has power to extend time limits...",
          "category": "Commercial Court",
          "storageUrl": "https://storage.azure.com/commercial-court-guide",
          "subsection_id": "A4.1"
        }
      ]
    }
  }
}
```

## Interactive Citation Features

### Hover Preview Implementation

```typescript
// Answer.tsx - Enhanced citation rendering
const renderCitationWithPreview = (citationData) => {
    return (
        <sup
            className="citation-sup"
            data-citation-text={citationData.citation}
            data-citation-content={citationData.preview}
            data-category={citationData.category}
            onMouseEnter={showPreview}
            onMouseLeave={hidePreview}
            onClick={showFullDetails}
        >
            {citationNumber}
        </sup>
    );
};
```

### Category-Aware Citation Display

```typescript
// Supporting Content displays category context
const formatCitationWithCategory = (citation, category) => {
    return (
        <div className="citation-item">
            <div className="citation-text">{citation}</div>
            <div className="citation-category">Source: {category}</div>
            <div className="citation-preview">{preview}</div>
        </div>
    );
};
```

## Special Cases with Category Context

### Case 1: Category Override

```python
# User selects "High Court" but query mentions "Commercial Court"
# User selection takes priority
selected_category = "High Court"
detected_court = "Commercial Court"
# Result: Search High Court documents + CPR fallback
```

### Case 2: Multi-Court Query

```python
# Query: "How do Commercial Court and High Court handle disclosure?"
# System detects multiple courts
detected_courts = ["Commercial Court", "High Court"]
# Uses selected category if available, or defaults to CPR
```

### Case 3: No Category Context

```python
# User selects "All Categories"
# Shows all available sources regardless of court
filter = None  # No category restriction
```

## Citation Display Examples with Hover

### Hover Preview

```text
User hovers over: [1]
Shows tooltip: "The court has power to extend time limits and make case management directions in accordance with the overriding objective..."
Category tag: "Commercial Court"
```

### Click for Full Details

```text
User clicks: [1]
Opens panel with:
- Full citation: "A4.1, Commercial Court Guide, Case Management Procedures"
- Complete content: Full text of A4.1
- Category: "Commercial Court"
- Direct link: Click to open source document
```

### Category-Specific Results

```text
User selected "Circuit Commercial Court":
[A4.1, Circuit Commercial Court Guide, Case Management] - Circuit-specific procedures
[31.1, CPR Part 31, Disclosure Rules] - General CPR rule that applies
```

## Benefits of Enhanced Citation System

### User Experience Benefits

1. **Quick Preview**: Hover to see content without clicking
1. **Category Control**: Select specific court for focused results
1. **Smart Detection**: System understands court mentions in queries
1. **Professional Format**: Three-part legal citation standard
1. **Direct Access**: Click to open source with highlighting

### Technical Benefits

1. **Performance**: Preview content cached, no additional requests
1. **Context Awareness**: Category information preserved throughout
1. **Intelligent Filtering**: Combines user selection with auto-detection
1. **Scalable**: Supports adding new courts and categories
1. **Maintainable**: Clear separation of concerns

## Debugging Enhanced Citations

Your logging helps track the enhanced citation process:

```python
logging.info(f"🎯 Category selected: {include_category}")
logging.info(f"🔍 Court detected in query: {detected_court}")
logging.info(f"📊 Filter applied: {search_filter}")
logging.info(f"🏷️ Citation with preview created: {citation}")
logging.info(f"👁️ Preview content: {preview[:50]}...")
```

Look for these enhanced log patterns:

- "🎯 Category": User selection tracking
- "🔍 Court detected": Auto-detection results
- "📊 Filter": Final search filter applied
- "🏷️ Citation": Enhanced citation format
- "👁️ Preview": Hover content preparation

## Citation Interaction Workflows

### Workflow 1: Expert User

1. Selects "Commercial Court" from category dropdown
1. Asks specific question about case management
1. Gets targeted Commercial Court results + CPR fallback
1. Hovers over citations for quick verification
1. Clicks relevant citations for detailed review

### Workflow 2: General Query

1. Leaves category as "All Categories"
1. Asks question mentioning specific court
1. System auto-detects court and filters accordingly
1. Reviews results from detected court + general rules
1. Uses hover preview to quickly assess relevance

### Workflow 3: Research Comparison

1. Asks question with "All Categories" selected
1. Reviews citations from multiple courts
1. Uses category tags to identify jurisdiction differences
1. Compares approaches across different courts

This enhanced citation system provides professional-grade legal research capabilities with intuitive user interactions!

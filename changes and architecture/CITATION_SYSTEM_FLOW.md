# Citation System - Complete Flow Diagram

## How Citations Work in Your Modified System

This document explains the complete journey of how a citation is created, processed, and displayed to the user.

## Citation Creation Flow

```mermaid
graph TD
    Start[User Asks Question] --> Search[Search Documents]
    Search --> Results[Get Search Results]
    
    Results --> Loop{For Each Document}
    
    Loop --> Extract[Extract Subsection Info]
    Extract --> Check{Multiple Subsections?}
    
    Check -->|Yes| Split[Split Document]
    Split --> Multi[Create Multiple Citations]
    Multi --> Format1[Format: 'subsection, page, file']
    
    Check -->|No| Single[Keep as Single Source]
    Single --> Format2[Format: 'page, file' or 'subsection, page, file']
    
    Format1 --> Store[Store in Citation Map]
    Format2 --> Store
    
    Store --> AI[Send to OpenAI with [1], [2], [3] refs]
    AI --> Response[AI Response with [1], [2], [3]]
    
    Response --> Map[Map Numbers to Full Citations]
    Map --> Display[Display to User]
```

## Detailed Step-by-Step Process

### Step 1: Document Search
When a user asks a question, the system searches for relevant documents.

```python
# User asks: "What are disclosure rules in fast track?"
results = await search_client.search(
    search_text="disclosure fast track",
    filter="category eq 'Civil Procedure Rules'",
    top=10
)
```

### Step 2: Subsection Detection
For each document found, the system looks for subsection markers.

```python
def _extract_subsection_from_document(self, doc):
    # Looks for patterns in content:
    # - "1.1 Disclosure obligations"
    # - "Rule 31.1"
    # - "Para 5.2"
    # Returns the subsection identifier
```

### Step 3: Document Splitting (Your Innovation)
If multiple subsections exist, split the document:

```python
def _extract_multiple_subsections_from_document(self, doc):
    # Input: One document with multiple rules
    # Output: List of subsection chunks
    
    # Example:
    # Document contains:
    #   "31.1 Standard disclosure..."
    #   "31.2 Specific disclosure..."
    #   "31.3 Disclosure statements..."
    
    # Becomes three separate sources:
    subsections = [
        {"subsection": "31.1", "content": "Standard disclosure..."},
        {"subsection": "31.2", "content": "Specific disclosure..."},
        {"subsection": "31.3", "content": "Disclosure statements..."}
    ]
```

### Step 4: Citation Building
Create the three-part citation format:

```python
def build_enhanced_citation_from_document(self, doc, source_index):
    subsection = "31.1"
    sourcepage = "CPR Part 31"
    sourcefile = "Civil Procedure Rules"
    
    # Three-part format
    citation = f"{subsection}, {sourcepage}, {sourcefile}"
    # Result: "31.1, CPR Part 31, Civil Procedure Rules"
```

### Step 5: Citation Mapping
Store the mapping between simple numbers and full citations:

```python
self.citation_map = {
    "1": "31.1, CPR Part 31, Civil Procedure Rules",
    "2": "31.2, CPR Part 31, Civil Procedure Rules",
    "3": "31.3, CPR Part 31, Civil Procedure Rules"
}
```

### Step 6: AI Processing
Send sources to OpenAI with simple numbering:

```
Sources sent to AI:
[1]: Standard disclosure requires parties to disclose...
[2]: Specific disclosure may be ordered by the court...
[3]: Disclosure statements must be signed...

AI Response:
"Standard disclosure is required in fast track cases [1]. 
The court may order specific disclosure if needed [2]."
```

### Step 7: Frontend Display
The frontend receives structured data:

```json
{
  "answer": "Standard disclosure is required...",
  "context": {
    "data_points": {
      "text": [
        {
          "id": "doc_1",
          "content": "Standard disclosure requires...",
          "citation": "31.1, CPR Part 31, Civil Procedure Rules",
          "storageUrl": "https://storage.azure.com/...",
          "subsection_id": "31.1",
          "is_subsection": true
        }
      ]
    }
  }
}
```

## Special Cases Handled

### Case 1: No Subsection Found
```python
# Document has no clear subsection markers
# Falls back to two-part citation:
citation = "CPR Part 31, Civil Procedure Rules"
```

### Case 2: Duplicate Detection
```python
# Avoids repeating subsection in citation
if sourcepage == subsection:
    # Don't duplicate: "31.1, 31.1, Rules"
    # Instead: "31.1, Civil Procedure Rules"
```

### Case 3: Encoded Formats
```python
# Handles encoded page names like "PD3E-1.1"
# Extracts just "1.1" for the subsection
```

## Citation Display Examples

### Simple Citation
```
User sees: [31.1, CPR Part 31, Civil Procedure Rules]
Clicking opens: Direct link to document with section 31.1 highlighted
```

### Multiple Subsections from Same Document
```
User sees:
[31.1, CPR Part 31, Civil Procedure Rules] - About standard disclosure
[31.2, CPR Part 31, Civil Procedure Rules] - About specific disclosure
[31.3, CPR Part 31, Civil Procedure Rules] - About disclosure statements
```

### Court-Specific Citation
```
User sees: [A4.1, Circuit Commercial Court Guide, Court Procedures]
This is specific to Circuit Commercial Court
```

## Benefits of Your Citation System

1. **Precision**: Exact subsection references
2. **Clarity**: Three-part format is unambiguous
3. **Efficiency**: Direct storage URL access
4. **Intelligence**: Automatic subsection detection
5. **Flexibility**: Handles various document formats

## Debugging Citations

Your logging helps track citation creation:

```python
logging.info(f"🔍 DEBUG: Processing document {doc.id}")
logging.info(f"🎯 DEBUG: Document split into {len(subsections)} sources")
logging.info(f"Citation mapping [1] = '31.1, CPR Part 31, Civil Procedure Rules'")
```

Look for these log patterns to debug:
- "🔍 DEBUG": Document processing
- "🎯 DEBUG": Subsection splitting
- "Citation mapping": Final citation format

## Citation Storage URL Integration

When a user clicks a citation:

```python
# Original: Download file through app
# Your version: Redirect to storage URL

async def assets(path):
    # Find document by citation
    filter_query = f"sourcepage eq '{path}'"
    results = await search_client.search(filter=filter_query)
    
    # Get storage URL
    storage_url = document.get("storageUrl")
    
    # Add highlighting if needed
    if highlight_terms:
        url = f"{storage_url}?search={highlight_terms}"
    
    return redirect(url)
```

This makes citation links fast and supports search highlighting!

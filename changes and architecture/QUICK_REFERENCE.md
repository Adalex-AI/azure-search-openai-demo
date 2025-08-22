# Quick Reference Guide for Developers

## Essential Concepts to Understand

### 1. RAG (Retrieval-Augmented Generation)
- **What it is**: AI that searches documents before answering
- **Why it matters**: Provides accurate, sourced answers
- **Your enhancement**: Made it legal-document aware

### 2. Document Processing Pipeline
```
PDF → Text Extraction → Chunking → Embedding → Indexing → Searchable
```

### 3. Key Python Files and Their Roles

| File | Purpose | Your Changes |
|------|---------|--------------|
| `app.py` | Main server, handles HTTP requests | Added storage URL redirection, enhanced logging |
| `approach.py` | Base class for AI strategies | Added Document fields, subsection extraction |
| `chatreadretrieveread.py` | Chat with memory | Implemented 3-part citations, court detection |
| `retrievethenread.py` | Simple Q&A | Added court-aware filtering |

### 4. Important Functions You Modified

#### Citation Building
```python
build_enhanced_citation_from_document(doc, index)
# Creates: "31.1, CPR Part 31, Civil Procedure Rules"
```

#### Subsection Extraction
```python
_extract_subsection_from_document(doc)
# Finds: "31.1", "Rule 1.1", "A4.1", etc.
```

#### Multiple Subsection Splitting
```python
_extract_multiple_subsections_from_document(doc)
# Splits one doc into multiple citation sources
```

#### Court Detection
```python
detect_court_in_query(query)
# Finds: "Circuit Commercial Court", "High Court", etc.
```

## Common Tasks and How to Do Them

### Adding a New Court Category
```python
# In normalize_court_to_category() function:
court_category_map = {
    'your new court': 'Your New Court',  # Add here
    # ... existing courts
}
```

### Adjusting Token Limits
```python
# In chatreadretrieveread.py:
response_token_limit = self.get_response_token_limit(
    self.chatgpt_model, 
    8192  # Change this number
)
```

### Adding New Subsection Patterns
```python
# In _extract_subsection_from_document():
subsection_patterns = [
    r'^(\d+\.\d+)',          # Existing: 1.1
    r'^(YourPattern\d+)',    # Add your pattern
]
```

### Changing Search Result Count
```python
# In run() method:
top = overrides.get("top", 3)  # Change default from 3
```

## Debugging Tips

### 1. Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Check Citation Mapping
Look for logs with:
```
"Citation mapping [1] = '...'"
```

### 3. Monitor Document Splitting
Look for logs with:
```
"🎯 DEBUG: Document split into X sources"
```

### 4. Trace Search Filters
Look for:
```
"Searching with filter: category eq '...'"
```

## Environment Variables

### Key Settings
```bash
# AI Model Settings
AZURE_OPENAI_EMB_MODEL_NAME=text-embedding-3-large  # Your change
AZURE_OPENAI_EMB_DIMENSIONS=3072                    # Your change

# Search Settings
AZURE_SEARCH_INDEX_NAME=your-index-name
AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG=default

# Enable Features
AZURE_USE_AUTHENTICATION=false
AZURE_ENFORCE_ACCESS_CONTROL=false
```

## Testing Your Changes

### 1. Test Citation Extraction
```python
# Create test document
doc = Document(
    content="31.1 This is a test rule",
    sourcepage="CPR Part 31",
    sourcefile="Rules.pdf"
)

# Test extraction
subsection = self._extract_subsection_from_document(doc)
assert subsection == "31.1"
```

### 2. Test Court Detection
```python
query = "What are the rules for Circuit Commercial Court?"
court = detect_court_in_query(query)
assert court == "circuit commercial court"
```

### 3. Test Document Splitting
```python
doc = Document(content="""
31.1 First rule
31.2 Second rule
31.3 Third rule
""")

subsections = _extract_multiple_subsections_from_document(doc)
assert len(subsections) == 3
```

## Common Errors and Solutions

### Error: "No storageUrl found"
**Solution**: Ensure documents in index have storageUrl field populated

### Error: "Citation not mapping correctly"
**Solution**: Check citation_map in logs, verify subsection extraction patterns

### Error: "Court filter not working"
**Solution**: Verify court name in normalize_court_to_category()

### Error: "Token limit exceeded"
**Solution**: Increase limits in get_response_token_limit()

## Frontend Integration Points

### Getting Citation Data
```javascript
// Citations come in context.data_points.text
const citations = response.context.data_points.text;

// Each citation has:
citation.citation     // "31.1, CPR Part 31, Rules"
citation.storageUrl   // Direct link to document
citation.content      // Full text content
```

### Displaying Citations
```javascript
// Show three-part citation
<span>{citation.citation}</span>

// Link to document
<a href={citation.storageUrl}>View Source</a>
```

## Performance Optimization Tips

1. **Reduce Search Results**: Lower `top` parameter if too many results
2. **Use Semantic Captions**: Enable for faster processing
3. **Enable Caching**: Use Redis for frequently accessed documents
4. **Optimize Embeddings**: Use smaller dimension models if needed

## Deployment Checklist

- [ ] Test all citation formats
- [ ] Verify court detection works
- [ ] Check storage URL access
- [ ] Confirm token limits adequate
- [ ] Test with real legal documents
- [ ] Verify logging is working
- [ ] Check error handling

## Need Help?

1. Check logs first (look for "DEBUG" entries)
2. Verify your changes in my_changes.diff
3. Test with simple queries before complex ones
4. Use the Python debugger for step-by-step execution

## Key GitHub Copilot Prompts

When working with this codebase, use these prompts:

```
"Add logging to track citation creation in this function"
"Create a test for subsection extraction with legal documents"
"Optimize this search query for legal terminology"
"Add error handling for missing storage URLs"
"Implement caching for frequently accessed documents"
```

Remember: Your changes make this a specialized legal tool. Always test with real legal document formats!

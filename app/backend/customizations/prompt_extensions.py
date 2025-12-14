"""
CUSTOM PROMPT EXTENSIONS
========================
This module contains custom prompt additions for legal document citation formatting.
These extensions are designed to be appended to the base prompts without modifying them.

To use after upstream merge:
1. Import these constants
2. Append to the base prompt template before sending to the LLM

Author: Your Name
Created: 2025-12-14
"""

# Additional citation formatting rules to append to any answer prompt
CITATION_FORMAT_RULES = """
CUSTOM CITATION FORMAT REQUIREMENTS:
- **SINGLE SOURCE PER SENTENCE**: End every sentence with exactly one citation to the single best supporting source (e.g., [1]); never include multiple citations such as [1][2].
- **PUNCTUATION THEN CITATION**: Finish each sentence with its natural punctuation (usually a period) and immediately append the citation without adding a space, e.g., "... complies with CPR 3.9.[1]"
- **NO REPEATED CITATIONS**: Do not cite the same source twice for the same sentence (e.g., use [1] instead of [1][1]).
- **SIMPLE BRACKET FORMAT**: Use only [1], [2], [3] etc. Never use ranges like [1-5], duplicates like "1. 1", or unbracketed numbers.

PROHIBITED CITATION PATTERNS:
- Using range citations like "[1-5]" or "[1–5]" - cite one source per sentence, not ranges
- Ending a sentence with an unbracketed number followed by a period (e.g., "...proceedings 1.") - always use brackets: "...proceedings.[1]"
- Using citation formats like "1.", "1. 1", "1 1", "(1)" - ONLY use "[1]"
- Chaining citations like [1][2][3] - pick the single best source
"""

# Legal document specific context additions
LEGAL_DOCUMENT_CONTEXT = """
LEGAL DOCUMENT CONTEXT:
- When citing legal sources, always use the simple numbered format [1], [2] etc.
- Legal documents often have internal section numbers (like "1.1", "2.3") - do NOT confuse these with citation indices
- Practice Directions, CPR rules, and court guides should each be cited as separate sources
- Preserve the hierarchical structure of legal requirements when summarizing
"""

def get_enhanced_system_prompt(base_prompt: str) -> str:
    """
    Append custom citation rules to any base system prompt.
    
    Usage after upstream merge:
        from customizations.prompt_extensions import get_enhanced_system_prompt
        
        enhanced_prompt = get_enhanced_system_prompt(original_prompt)
    """
    return f"{base_prompt}\n\n{CITATION_FORMAT_RULES}"


def get_legal_enhanced_prompt(base_prompt: str) -> str:
    """
    Append both citation rules and legal document context.
    Use this for legal document RAG applications.
    """
    return f"{base_prompt}\n\n{CITATION_FORMAT_RULES}\n\n{LEGAL_DOCUMENT_CONTEXT}"

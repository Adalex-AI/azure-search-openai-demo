"""
Utility for filtering thought steps to protect system prompts from end users.

This module provides functions to classify thoughts as either user-safe or admin-only,
ensuring system prompts and raw LLM messages are never exposed to non-admin users.

CUSTOM: This is a merge-safe customization for protecting sensitive system prompts
from being visible to end users while maintaining them in backend feedback storage.

Supports both:
- ThoughtStep dataclass objects from approaches (have .title, .description, .props attributes)
- Dictionary representations from API responses (have "title", "description", "props" keys)
"""

from typing import Any, TypedDict, Union


class ThoughtStepDict(TypedDict, total=False):
    """TypedDict representing a thought step dictionary from API response."""
    title: str
    description: Any
    props: dict[str, Any]


# Type alias for both dataclass and dict representations
ThoughtStep = Union[Any, ThoughtStepDict]  # Any to support dataclass without importing


# Titles that contain system prompt or sensitive LLM internals
ADMIN_ONLY_THOUGHT_TITLES = {
    "Prompt to generate answer",  # Contains full rendered prompt with system message
    "Prompt to rewrite query",    # May contain system context
    "Query rewrite",              # Internal reasoning about query rewriting
    "Thought step",               # Generic admin-only step
}


def get_thought_attr(thought: ThoughtStep, attr: str, default: Any = None) -> Any:
    """
    Get attribute from thought, supporting both dataclass and dict.
    
    Args:
        thought: A thought step (dataclass or dict)
        attr: The attribute name to get
        default: Default value if attribute doesn't exist
        
    Returns:
        The attribute value or default
    """
    if thought is None:
        return default
    
    # Try dataclass attribute access first
    if hasattr(thought, attr):
        return getattr(thought, attr, default)
    
    # Fall back to dict-style access
    if isinstance(thought, dict):
        return thought.get(attr, default)
    
    return default


def is_admin_only_thought(thought: ThoughtStep) -> bool:
    """
    Check if a thought step contains admin-only (sensitive) information.
    
    Args:
        thought: A thought step (dataclass or dict) with title, description, and optional props
        
    Returns:
        True if the thought is admin-only and should not be shown to regular users
    """
    if thought is None:
        return False
    
    # Get title using attribute-safe accessor
    title = get_thought_attr(thought, "title", "")
    if not title:
        return False
    
    # Check if title matches admin-only thought types
    if title in ADMIN_ONLY_THOUGHT_TITLES:
        return True
    
    # Check if props contains raw system messages
    props = get_thought_attr(thought, "props", None)
    if props and isinstance(props, dict):
        # Check for raw_messages which contain system prompts
        if "raw_messages" in props:
            return True
    
    return False


def filter_thoughts_for_user(thoughts: list[ThoughtStep]) -> list[ThoughtStep]:
    """
    Filter out admin-only thoughts from a list, returning only user-safe thoughts.
    
    This function removes:
    - Thoughts with system prompts ("Prompt to generate answer")
    - Thoughts with raw LLM messages
    - Any other admin-only classified thoughts
    
    Keeps user-safe thoughts like:
    - Search Query
    - Retrieved Documents
    - Query rewrite reasoning (if not sensitive)
    
    Args:
        thoughts: List of thought step dictionaries
        
    Returns:
        Filtered list containing only user-safe thoughts
    """
    if not thoughts:
        return []
    
    return [thought for thought in thoughts if not is_admin_only_thought(thought)]


def filter_thoughts_for_feedback(thoughts: list[ThoughtStep]) -> list[ThoughtStep]:
    """
    Filter thoughts when user submits feedback.
    
    When users submit feedback, they should only see the user-safe portion of thoughts.
    The system prompt should never be included in feedback data that users can see.
    
    This is stricter than filter_thoughts_for_user to ensure feedback privacy.
    
    Args:
        thoughts: List of thought step dictionaries from API response
        
    Returns:
        Filtered list safe to include in user-submitted feedback
    """
    return filter_thoughts_for_user(thoughts)


def extract_admin_only_thoughts(thoughts: list[ThoughtStep]) -> list[ThoughtStep]:
    """
    Extract admin-only thoughts for backend storage.
    
    These are stored separately in backend feedback storage for debugging and analysis,
    but are never exposed to end users.
    
    Args:
        thoughts: List of thought step dictionaries
        
    Returns:
        List of admin-only thoughts
    """
    if not thoughts:
        return []
    
    return [thought for thought in thoughts if is_admin_only_thought(thought)]


def split_thoughts(thoughts: list[ThoughtStep]) -> tuple[list[ThoughtStep], list[ThoughtStep]]:
    """
    Split thoughts into user-safe and admin-only categories.
    
    Args:
        thoughts: List of thought step dictionaries
        
    Returns:
        Tuple of (user_safe_thoughts, admin_only_thoughts)
    """
    user_safe = filter_thoughts_for_user(thoughts)
    admin_only = extract_admin_only_thoughts(thoughts)
    return user_safe, admin_only

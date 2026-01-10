"""
Unit tests for the thought_filter utility.

CUSTOM: Tests for filtering system prompts from thought steps to protect
sensitive information from end users.
"""

import pytest
from customizations.thought_filter import (
    is_admin_only_thought,
    filter_thoughts_for_user,
    filter_thoughts_for_feedback,
    extract_admin_only_thoughts,
    split_thoughts,
)


class TestIsAdminOnlyThought:
    """Tests for is_admin_only_thought function."""
    
    def test_admin_only_prompt_to_generate_answer(self):
        """Test that 'Prompt to generate answer' is marked as admin-only."""
        thought = {
            "title": "Prompt to generate answer",
            "description": "Some prompt content",
            "props": {}
        }
        assert is_admin_only_thought(thought) is True
    
    def test_admin_only_with_raw_messages(self):
        """Test that thoughts with raw_messages are marked as admin-only."""
        thought = {
            "title": "Some thought",
            "description": "Description",
            "props": {
                "raw_messages": [
                    {"role": "system", "content": "You are a legal AI..."}
                ]
            }
        }
        assert is_admin_only_thought(thought) is True
    
    def test_user_safe_search_query(self):
        """Test that 'Search Query' is user-safe."""
        thought = {
            "title": "Search Query",
            "description": "Searching for appeal procedures",
            "props": {}
        }
        assert is_admin_only_thought(thought) is False
    
    def test_user_safe_retrieved_documents(self):
        """Test that 'Retrieved Documents' is user-safe."""
        thought = {
            "title": "Retrieved Documents",
            "description": "Found 5 relevant documents",
            "props": {}
        }
        assert is_admin_only_thought(thought) is False
    
    def test_custom_user_safe_title(self):
        """Test that custom titles without admin markers are user-safe."""
        thought = {
            "title": "Custom Analysis",
            "description": "Some analysis",
            "props": {}
        }
        assert is_admin_only_thought(thought) is False
    
    def test_empty_thought(self):
        """Test handling of empty/None thought."""
        assert is_admin_only_thought(None) is False
        assert is_admin_only_thought({}) is False
    
    def test_thought_without_title(self):
        """Test thought without title field."""
        thought = {"description": "No title"}
        assert is_admin_only_thought(thought) is False


class TestFilterThoughtsForUser:
    """Tests for filter_thoughts_for_user function."""
    
    def test_filter_removes_admin_only_thoughts(self):
        """Test that admin-only thoughts are removed."""
        thoughts = [
            {
                "title": "Search Query",
                "description": "Query text",
                "props": {}
            },
            {
                "title": "Prompt to generate answer",
                "description": "Admin content",
                "props": {}
            },
            {
                "title": "Retrieved Documents",
                "description": "Documents",
                "props": {}
            }
        ]
        
        filtered = filter_thoughts_for_user(thoughts)
        
        assert len(filtered) == 2
        assert filtered[0]["title"] == "Search Query"
        assert filtered[1]["title"] == "Retrieved Documents"
    
    def test_filter_preserves_all_user_safe_thoughts(self):
        """Test that all user-safe thoughts are preserved."""
        thoughts = [
            {"title": "Search Query", "description": "q", "props": {}},
            {"title": "Retrieved Documents", "description": "d", "props": {}},
            {"title": "Custom Step", "description": "c", "props": {}}
        ]
        
        filtered = filter_thoughts_for_user(thoughts)
        
        assert len(filtered) == 3
    
    def test_filter_empty_thoughts(self):
        """Test filtering empty thoughts list."""
        assert filter_thoughts_for_user([]) == []
        assert filter_thoughts_for_user(None) == []
    
    def test_filter_all_admin_only_thoughts(self):
        """Test filtering when all thoughts are admin-only."""
        thoughts = [
            {
                "title": "Prompt to generate answer",
                "description": "Admin",
                "props": {"raw_messages": []}
            }
        ]
        
        filtered = filter_thoughts_for_user(thoughts)
        
        assert len(filtered) == 0


class TestFilterThoughtsForFeedback:
    """Tests for filter_thoughts_for_feedback function."""
    
    def test_feedback_filter_is_stricter(self):
        """Test that feedback filter removes same thoughts as user filter."""
        thoughts = [
            {"title": "Search Query", "description": "q", "props": {}},
            {"title": "Prompt to generate answer", "description": "a", "props": {}}
        ]
        
        feedback_filtered = filter_thoughts_for_feedback(thoughts)
        
        assert len(feedback_filtered) == 1
        assert feedback_filtered[0]["title"] == "Search Query"
    
    def test_feedback_filter_with_raw_messages(self):
        """Test that feedback filter removes thoughts with raw_messages."""
        thoughts = [
            {
                "title": "Custom Analysis",
                "description": "Analysis",
                "props": {
                    "raw_messages": [{"role": "system", "content": "secret"}]
                }
            }
        ]
        
        filtered = filter_thoughts_for_feedback(thoughts)
        
        assert len(filtered) == 0


class TestExtractAdminOnlyThoughts:
    """Tests for extract_admin_only_thoughts function."""
    
    def test_extract_admin_only_thoughts(self):
        """Test extraction of admin-only thoughts."""
        thoughts = [
            {"title": "Search Query", "description": "q", "props": {}},
            {"title": "Prompt to generate answer", "description": "a", "props": {}},
            {"title": "Retrieved Documents", "description": "d", "props": {}}
        ]
        
        admin_thoughts = extract_admin_only_thoughts(thoughts)
        
        assert len(admin_thoughts) == 1
        assert admin_thoughts[0]["title"] == "Prompt to generate answer"
    
    def test_extract_empty_list(self):
        """Test extraction from empty list."""
        assert extract_admin_only_thoughts([]) == []
        assert extract_admin_only_thoughts(None) == []
    
    def test_extract_with_raw_messages(self):
        """Test extraction of thoughts with raw_messages."""
        thoughts = [
            {
                "title": "Query Analysis",
                "description": "Analysis",
                "props": {
                    "raw_messages": [{"role": "system", "content": "prompt"}]
                }
            }
        ]
        
        admin_thoughts = extract_admin_only_thoughts(thoughts)
        
        assert len(admin_thoughts) == 1


class TestSplitThoughts:
    """Tests for split_thoughts function."""
    
    def test_split_thoughts(self):
        """Test splitting thoughts into user-safe and admin-only."""
        thoughts = [
            {"title": "Search Query", "description": "q", "props": {}},
            {"title": "Prompt to generate answer", "description": "a", "props": {}},
            {"title": "Retrieved Documents", "description": "d", "props": {}}
        ]
        
        user_safe, admin_only = split_thoughts(thoughts)
        
        assert len(user_safe) == 2
        assert len(admin_only) == 1
        assert user_safe[0]["title"] == "Search Query"
        assert user_safe[1]["title"] == "Retrieved Documents"
        assert admin_only[0]["title"] == "Prompt to generate answer"
    
    def test_split_empty_thoughts(self):
        """Test splitting empty thoughts."""
        user_safe, admin_only = split_thoughts([])
        
        assert user_safe == []
        assert admin_only == []
    
    def test_split_all_user_safe(self):
        """Test splitting when all thoughts are user-safe."""
        thoughts = [
            {"title": "Search Query", "description": "q", "props": {}},
            {"title": "Retrieved Documents", "description": "d", "props": {}}
        ]
        
        user_safe, admin_only = split_thoughts(thoughts)
        
        assert len(user_safe) == 2
        assert len(admin_only) == 0
    
    def test_split_all_admin_only(self):
        """Test splitting when all thoughts are admin-only."""
        thoughts = [
            {"title": "Prompt to generate answer", "description": "a", "props": {}}
        ]
        
        user_safe, admin_only = split_thoughts(thoughts)
        
        assert len(user_safe) == 0
        assert len(admin_only) == 1


class TestIntegration:
    """Integration tests for thought filtering."""
    
    def test_complete_feedback_flow(self):
        """Test complete flow of processing thoughts for feedback."""
        # Simulate thoughts from API response
        api_thoughts = [
            {
                "title": "Search Query",
                "description": "Searching for precedent",
                "props": {}
            },
            {
                "title": "Retrieved Documents",
                "description": "Found 3 documents",
                "props": {}
            },
            {
                "title": "Prompt to generate answer",
                "description": "Complex prompt with system instructions",
                "props": {
                    "raw_messages": [
                        {"role": "system", "content": "You are a legal AI..."},
                        {"role": "user", "content": "Question?"}
                    ]
                }
            }
        ]
        
        # User receives filtered version
        user_thoughts = filter_thoughts_for_user(api_thoughts)
        assert len(user_thoughts) == 2
        for thought in user_thoughts:
            assert not thought["title"].startswith("Prompt to")
        
        # Feedback includes filtered thoughts
        feedback_thoughts = filter_thoughts_for_feedback(user_thoughts)
        assert len(feedback_thoughts) == 2
        
        # Admin storage includes all thoughts
        all_admin_thoughts = extract_admin_only_thoughts(api_thoughts)
        assert len(all_admin_thoughts) == 1
        assert all_admin_thoughts[0]["title"] == "Prompt to generate answer"
    
    def test_thought_with_multiple_admin_markers(self):
        """Test thought that has multiple admin markers."""
        thought = {
            "title": "Prompt to generate answer",
            "description": "Admin content",
            "props": {
                "raw_messages": [{"role": "system", "content": "secret"}]
            }
        }
        
        # Should be filtered due to title alone
        assert is_admin_only_thought(thought) is True
        
        # Should be removed by filter
        filtered = filter_thoughts_for_user([thought])
        assert len(filtered) == 0

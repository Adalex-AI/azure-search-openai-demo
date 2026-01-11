"""
Unit tests for customization prompt extensions.

Tests prompt enhancement functions for legal citations and formatting.
"""

import pytest


class TestCitationFormatRules:
    """Tests for citation format rules constant."""

    def test_citation_format_rules_is_string(self):
        """Test that CITATION_FORMAT_RULES is a non-empty string."""
        from customizations.prompt_extensions import CITATION_FORMAT_RULES

        assert isinstance(CITATION_FORMAT_RULES, str)
        assert len(CITATION_FORMAT_RULES) > 0

    def test_citation_format_rules_contains_key_prohibitions(self):
        """Test that format rules cover key citation prohibitions."""
        from customizations.prompt_extensions import CITATION_FORMAT_RULES

        required_content = [
            "SINGLE SOURCE PER SENTENCE",
            "PUNCTUATION THEN CITATION",
            "NO REPEATED CITATIONS",
            "SIMPLE BRACKET FORMAT",
            "PROHIBITED CITATION PATTERNS",
        ]

        for content in required_content:
            assert content in CITATION_FORMAT_RULES


class TestLegalDocumentContext:
    """Tests for legal document context constant."""

    def test_legal_document_context_is_string(self):
        """Test that LEGAL_DOCUMENT_CONTEXT is a non-empty string."""
        from customizations.prompt_extensions import LEGAL_DOCUMENT_CONTEXT

        assert isinstance(LEGAL_DOCUMENT_CONTEXT, str)
        assert len(LEGAL_DOCUMENT_CONTEXT) > 0

    def test_legal_document_context_covers_key_aspects(self):
        """Test that context covers important legal document aspects."""
        from customizations.prompt_extensions import LEGAL_DOCUMENT_CONTEXT

        required_content = [
            "LEGAL DOCUMENT CONTEXT",
            "numbered format",
            "section numbers",
            "Practice Directions",
            "CPR rules",
        ]

        for content in required_content:
            assert content in LEGAL_DOCUMENT_CONTEXT


class TestGetEnhancedSystemPrompt:
    """Tests for get_enhanced_system_prompt function."""

    def test_get_enhanced_system_prompt_appends_to_base_prompt(self):
        """Test that function appends citation rules to base prompt."""
        from customizations.prompt_extensions import (
            get_enhanced_system_prompt,
            CITATION_FORMAT_RULES,
        )

        base_prompt = "You are a helpful assistant."
        enhanced = get_enhanced_system_prompt(base_prompt)

        assert base_prompt in enhanced
        assert CITATION_FORMAT_RULES in enhanced

    def test_get_enhanced_system_prompt_preserves_base_prompt_intact(self):
        """Test that base prompt is not modified, only extended."""
        from customizations.prompt_extensions import get_enhanced_system_prompt

        base_prompt = "You are a helpful assistant.\nAnswer questions accurately."
        enhanced = get_enhanced_system_prompt(base_prompt)

        assert enhanced.startswith(base_prompt)

    def test_get_enhanced_system_prompt_adds_separator(self):
        """Test that a separator is added between base and custom content."""
        from customizations.prompt_extensions import get_enhanced_system_prompt

        base_prompt = "Base prompt."
        enhanced = get_enhanced_system_prompt(base_prompt)

        # Should have newlines separating content
        assert "\n\n" in enhanced

    def test_get_enhanced_system_prompt_with_empty_base_prompt(self):
        """Test that function handles empty base prompt."""
        from customizations.prompt_extensions import (
            get_enhanced_system_prompt,
            CITATION_FORMAT_RULES,
        )

        enhanced = get_enhanced_system_prompt("")

        assert CITATION_FORMAT_RULES in enhanced

    def test_get_enhanced_system_prompt_with_long_base_prompt(self):
        """Test that function handles long base prompts."""
        from customizations.prompt_extensions import (
            get_enhanced_system_prompt,
            CITATION_FORMAT_RULES,
        )

        base_prompt = "Base content.\n" * 100  # Long prompt
        enhanced = get_enhanced_system_prompt(base_prompt)

        assert base_prompt in enhanced
        assert CITATION_FORMAT_RULES in enhanced


class TestGetLegalEnhancedPrompt:
    """Tests for get_legal_enhanced_prompt function."""

    def test_get_legal_enhanced_prompt_includes_both_extensions(self):
        """Test that legal enhanced prompt includes both citation rules and context."""
        from customizations.prompt_extensions import (
            get_legal_enhanced_prompt,
            CITATION_FORMAT_RULES,
            LEGAL_DOCUMENT_CONTEXT,
        )

        base_prompt = "You are a legal assistant."
        enhanced = get_legal_enhanced_prompt(base_prompt)

        assert base_prompt in enhanced
        assert CITATION_FORMAT_RULES in enhanced
        assert LEGAL_DOCUMENT_CONTEXT in enhanced

    def test_get_legal_enhanced_prompt_has_proper_structure(self):
        """Test that legal enhanced prompt has proper structure with separators."""
        from customizations.prompt_extensions import get_legal_enhanced_prompt

        base_prompt = "Base prompt."
        enhanced = get_legal_enhanced_prompt(base_prompt)

        # Should have multiple separators
        separator_count = enhanced.count("\n\n")
        assert separator_count >= 2

    def test_get_legal_enhanced_prompt_longer_than_simple_enhanced(self):
        """Test that legal enhanced prompt is longer than simple enhanced version."""
        from customizations.prompt_extensions import (
            get_enhanced_system_prompt,
            get_legal_enhanced_prompt,
        )

        base_prompt = "Base prompt."
        simple = get_enhanced_system_prompt(base_prompt)
        legal = get_legal_enhanced_prompt(base_prompt)

        assert len(legal) > len(simple)

    def test_get_legal_enhanced_prompt_preserves_order(self):
        """Test that legal enhanced prompt maintains proper order of content."""
        from customizations.prompt_extensions import get_legal_enhanced_prompt

        base_prompt = "Base prompt."
        enhanced = get_legal_enhanced_prompt(base_prompt)

        # Base should come first
        base_pos = enhanced.find(base_prompt)
        citation_pos = enhanced.find("CUSTOM CITATION FORMAT REQUIREMENTS")
        legal_pos = enhanced.find("LEGAL DOCUMENT CONTEXT")

        assert base_pos < citation_pos < legal_pos


class TestPromptEnhancementIntegration:
    """Integration tests for prompt enhancement functions."""

    def test_enhanced_prompts_are_valid_strings(self):
        """Test that enhanced prompts are valid strings without encoding issues."""
        from customizations.prompt_extensions import (
            get_enhanced_system_prompt,
            get_legal_enhanced_prompt,
        )

        base_prompt = "Test prompt"

        simple = get_enhanced_system_prompt(base_prompt)
        legal = get_legal_enhanced_prompt(base_prompt)

        # Should be valid strings
        assert isinstance(simple, str)
        assert isinstance(legal, str)

        # Should be encodable to UTF-8
        assert simple.encode("utf-8")
        assert legal.encode("utf-8")

    def test_enhanced_prompts_dont_contain_html_or_markdown_artifacts(self):
        """Test that enhanced prompts don't have encoding artifacts."""
        from customizations.prompt_extensions import get_legal_enhanced_prompt

        base_prompt = "Test prompt"
        enhanced = get_legal_enhanced_prompt(base_prompt)

        # Should not have HTML entities or escaped quotes
        assert "&quot;" not in enhanced
        assert "&#" not in enhanced
        assert "\\n" not in enhanced  # Should have actual newlines, not escaped

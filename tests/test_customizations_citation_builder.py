"""
Unit tests for Citation Builder module.

Tests for legal citation extraction and formatting functionality.
"""

import pytest
from unittest.mock import Mock


class TestCitationBuilderInit:
    """Tests for CitationBuilder initialization."""

    def test_citation_builder_initialization(self):
        """Test that CitationBuilder initializes with empty citation map."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        assert hasattr(builder, "citation_map")
        assert isinstance(builder.citation_map, dict)
        assert len(builder.citation_map) == 0


class TestExtractSubsection:
    """Tests for subsection extraction from documents."""

    def test_extract_subsection_from_content_simple_numbered(self):
        """Test extracting simple numbered subsection like 1.1 from content."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "1.1 Filing Requirements\nThis section describes..."
        doc.sourcepage = ""

        subsection = builder.extract_subsection(doc)
        assert subsection == "1.1"

    def test_extract_subsection_from_content_alpha_numeric(self):
        """Test extracting alpha-numeric subsection like A4.1 from content."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "A4.1 Court Procedure\nDetails here..."
        doc.sourcepage = ""

        subsection = builder.extract_subsection(doc)
        assert subsection == "A4.1"

    def test_extract_subsection_from_markdown_heading(self):
        """Test extracting subsection from markdown heading."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "# 1.1 Filing Requirements\nContent..."
        doc.sourcepage = ""

        subsection = builder.extract_subsection(doc)
        assert subsection == "1.1"

    def test_extract_subsection_from_bold_markdown(self):
        """Test extracting subsection from bold markdown."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "**2.3** Procedural Rules\nMore content..."
        doc.sourcepage = ""

        subsection = builder.extract_subsection(doc)
        assert subsection == "2.3"

    def test_extract_subsection_from_encoded_sourcepage(self):
        """Test extracting subsection from encoded sourcepage format."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = ""
        doc.sourcepage = "PD3E-1.1"

        subsection = builder.extract_subsection(doc)
        assert subsection == "1.1"

    def test_extract_subsection_content_takes_priority_over_sourcepage(self):
        """Test that content subsection takes priority over sourcepage."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "2.5 Important Section\nContent..."
        doc.sourcepage = "PD3E-1.1"

        subsection = builder.extract_subsection(doc)
        assert subsection == "2.5"

    def test_extract_subsection_rule_format(self):
        """Test extracting Rule format subsection."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "Rule 31.1 Discovery\nContent..."
        doc.sourcepage = ""

        subsection = builder.extract_subsection(doc)
        assert subsection == "Rule 31.1"

    def test_extract_subsection_para_format(self):
        """Test extracting Paragraph format subsection."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "Para 5.2 Court Orders\nContent..."
        doc.sourcepage = ""

        subsection = builder.extract_subsection(doc)
        assert subsection == "Para 5.2"

    def test_extract_subsection_returns_empty_string_when_not_found(self):
        """Test that empty string is returned when no subsection found."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "Some random content without subsection markers"
        doc.sourcepage = ""

        subsection = builder.extract_subsection(doc)
        assert subsection == ""

    def test_extract_subsection_handles_multiple_lines(self):
        """Test that function checks first 20 lines only."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "\n" * 25 + "3.7 Late Content\nFound after many lines..."
        doc.sourcepage = ""

        subsection = builder.extract_subsection(doc)
        # Should not find subsection on line 26+
        assert subsection == ""

    def test_extract_subsection_with_none_content(self):
        """Test handling when content is None."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = None
        doc.sourcepage = ""

        subsection = builder.extract_subsection(doc)
        assert subsection == ""

    def test_extract_subsection_with_empty_content_falls_back_to_sourcepage(self):
        """Test fallback to sourcepage when content is empty."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = ""
        doc.sourcepage = "PD2A-2.3"

        subsection = builder.extract_subsection(doc)
        assert subsection == "2.3"


class TestBuildEnhancedCitation:
    """Tests for building enhanced citations."""

    def test_build_enhanced_citation_three_part_format(self):
        """Test building three-part citation with subsection, sourcepage, and sourcefile."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "1.1 Filing Requirements\nContent..."
        doc.sourcepage = "p. 10"
        doc.sourcefile = "CPR Part 1"

        citation = builder.build_enhanced_citation(doc, source_index=1)
        assert "1.1" in citation
        assert "p. 10" in citation
        assert "CPR Part 1" in citation

    def test_build_enhanced_citation_two_part_format(self):
        """Test building two-part citation without sourcepage."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "2.3 Procedure\nContent..."
        doc.sourcepage = ""
        doc.sourcefile = "Commercial Court Guide"

        citation = builder.build_enhanced_citation(doc, source_index=2)
        assert "2.3" in citation
        assert "Commercial Court Guide" in citation

    def test_build_enhanced_citation_sourcefile_only(self):
        """Test building citation with only sourcefile."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = ""
        doc.sourcepage = ""
        doc.sourcefile = "Practice Direction 3E"

        citation = builder.build_enhanced_citation(doc, source_index=3)
        assert citation == "Practice Direction 3E"

    def test_build_enhanced_citation_fallback_to_source_index(self):
        """Test fallback to generic source label when document is empty."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = ""
        doc.sourcepage = ""
        doc.sourcefile = ""

        citation = builder.build_enhanced_citation(doc, source_index=5)
        assert citation == "Source 5"

    def test_build_enhanced_citation_deduplicates_subsection_and_sourcepage(self):
        """Test that duplicate subsection/sourcepage are not repeated."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "1.1 Filing\nContent..."
        doc.sourcepage = "1.1"  # Same as subsection
        doc.sourcefile = "CPR"

        citation = builder.build_enhanced_citation(doc, source_index=1)
        # Should not have "1.1" repeated
        assert citation.count("1.1") == 1

    def test_build_enhanced_citation_with_none_attributes(self):
        """Test handling of None attributes."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = None
        doc.sourcepage = None
        doc.sourcefile = "Guide"

        citation = builder.build_enhanced_citation(doc, source_index=1)
        assert "Guide" in citation


class TestCitationBuilderPatterns:
    """Tests for citation pattern matching."""

    def test_content_subsection_patterns_defined(self):
        """Test that content subsection patterns are defined."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        assert len(builder.CONTENT_SUBSECTION_PATTERNS) > 0

    def test_encoded_subsection_patterns_defined(self):
        """Test that encoded subsection patterns are defined."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        assert len(builder.ENCODED_SUBSECTION_PATTERNS) > 0

    def test_direct_subsection_patterns_defined(self):
        """Test that direct subsection patterns are defined."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        assert len(builder.DIRECT_SUBSECTION_PATTERNS) > 0

    def test_multi_subsection_pattern_exists(self):
        """Test that multi-subsection pattern is compiled."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        assert hasattr(builder, "MULTI_SUBSECTION_PATTERN")
        assert builder.MULTI_SUBSECTION_PATTERN is not None


class TestExtractMultipleSubsections:
    """Tests for extracting multiple subsections from document content."""

    def test_extract_multiple_subsections_method_exists(self):
        """Test that extract_multiple_subsections method exists."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        assert hasattr(builder, "extract_multiple_subsections")
        assert callable(builder.extract_multiple_subsections)


class TestCitationBuilderEdgeCases:
    """Tests for edge cases in citation building."""

    def test_extract_subsection_with_extra_whitespace(self):
        """Test handling of extra whitespace around subsection."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "   1.1   Filing Requirements\n"
        doc.sourcepage = ""

        subsection = builder.extract_subsection(doc)
        assert subsection == "1.1"

    def test_extract_subsection_with_special_characters(self):
        """Test handling of content with special characters."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = "1.1 - Filing Requirements & Procedures\nContent..."
        doc.sourcepage = ""

        subsection = builder.extract_subsection(doc)
        assert subsection == "1.1"

    def test_build_citation_with_special_characters_in_sourcefile(self):
        """Test building citation with special characters in sourcefile."""
        from customizations.approaches.citation_builder import CitationBuilder

        builder = CitationBuilder()
        doc = Mock()
        doc.content = ""
        doc.sourcepage = ""
        doc.sourcefile = "CPR Part 1 (as amended 2024)"

        citation = builder.build_enhanced_citation(doc, source_index=1)
        assert "CPR Part 1 (as amended 2024)" in citation

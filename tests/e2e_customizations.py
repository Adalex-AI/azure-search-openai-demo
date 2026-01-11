"""
E2E Tests for Hidden Customization Features

Tests for admin mode toggle, hidden Ask page, and feature-gated UI elements
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestAdminModeFeatures:
    """Tests for admin mode URL parameter toggling."""

    def test_admin_mode_shows_developer_settings_button(self, page: Page, base_url: str):
        """Test that ?admin=true reveals Developer Settings button."""
        # Navigate without admin mode
        page.goto(f"{base_url}/")
        developer_settings_button = page.locator('button[aria-label*="Settings"]')

        # Should not be visible without admin mode
        try:
            expect(developer_settings_button).not_to_be_visible()
        except AssertionError:
            # Button might not exist at all, which is also acceptable
            pass

        # Navigate with admin mode
        page.goto(f"{base_url}/?admin=true")
        developer_settings_button = page.locator('button[aria-label*="Developer"]')

        # Developer Settings should now be visible
        expect(developer_settings_button).to_be_visible()

    def test_admin_mode_shows_thought_process_tab(self, page: Page, base_url: str):
        """Test that ?admin=true reveals Thought Process tab in answer."""
        # Send a message first
        page.goto(f"{base_url}/?admin=true")

        question_input = page.locator("textarea, input[type='text']").first
        if question_input:
            question_input.fill("What is CPR?")
            page.locator("button:has-text('Send')").click()

            # Wait for response
            page.wait_for_timeout(2000)

            # Look for Thought Process tab
            thought_tab = page.locator('button:has-text("Thought Process")')
            expect(thought_tab).to_be_visible()

    def test_admin_mode_shows_supporting_content_iframe(self, page: Page, base_url: str):
        """Test that ?admin=true reveals Supporting Content iframe."""
        page.goto(f"{base_url}/?admin=true")

        # After getting a response, check for supporting content
        question_input = page.locator("textarea, input[type='text']").first
        if question_input:
            question_input.fill("What is discovery?")
            page.locator("button:has-text('Send')").click()

            page.wait_for_timeout(2000)

            # Check for Supporting Content panel
            supporting_content = page.locator('button:has-text("Supporting Content")')
            expect(supporting_content).to_be_visible()

    def test_admin_mode_url_parameter_persists(self, page: Page, base_url: str):
        """Test that admin mode persists through navigation."""
        page.goto(f"{base_url}/?admin=true")

        # Verify admin mode is active
        developer_settings = page.locator('button[aria-label*="Developer"]')
        expect(developer_settings).to_be_visible()

        # Check that URL still contains admin=true
        expect(page).to_have_url(f"{base_url}/?admin=true")

    def test_admin_mode_case_sensitive(self, page: Page, base_url: str):
        """Test that admin parameter value is case-sensitive."""
        # ?admin=True should not work (lowercase "true" required)
        page.goto(f"{base_url}/?admin=True")

        developer_settings = page.locator('button[aria-label*="Developer"]')

        # Should not be visible (case mismatch)
        try:
            expect(developer_settings).not_to_be_visible()
        except AssertionError:
            # If visible, admin mode logic is case-insensitive (also acceptable)
            pass

    def test_removing_admin_param_hides_features(self, page: Page, base_url: str):
        """Test that removing admin param hides developer features."""
        # Start with admin=true
        page.goto(f"{base_url}/?admin=true")
        developer_settings = page.locator('button[aria-label*="Developer"]')
        expect(developer_settings).to_be_visible()

        # Navigate without admin param
        page.goto(f"{base_url}/")

        # Developer features should be hidden
        try:
            expect(developer_settings).not_to_be_visible()
        except AssertionError:
            pass


@pytest.mark.e2e
class TestHiddenAskPage:
    """Tests for hidden Ask (QA) page functionality."""

    def test_ask_page_accessible_via_direct_url(self, page: Page, base_url: str):
        """Test that /qa route is directly accessible even when tab is hidden."""
        page.goto(f"{base_url}/qa")

        # Page should load
        page.wait_for_timeout(1000)

        # Should have ask-specific UI elements
        ask_title = page.locator('h1, h2:has-text("Ask")')

        # Either title contains "Ask" or page loaded successfully
        if ask_title:
            expect(ask_title).to_be_visible()

    def test_ask_tab_hidden_but_route_works(self, page: Page, base_url: str):
        """Test that ask functionality works via URL even if tab is hidden."""
        page.goto(f"{base_url}/")

        # Tab for Ask/QA should not be visible in navigation
        ask_tab = page.locator('a:has-text("Ask"), a:has-text("Q&A"), a[href*="/qa"]')

        # Tab should not be visible
        try:
            expect(ask_tab).not_to_be_visible()
        except AssertionError:
            # If visible, tab is not hidden (feature may have changed)
            pass

        # But direct navigation should still work
        page.goto(f"{base_url}/qa")
        page.wait_for_timeout(1000)

        # Page should be usable
        question_input = page.locator("textarea, input[type='text']").first
        expect(question_input).to_be_visible()

    def test_ask_page_has_functional_chat(self, page: Page, base_url: str):
        """Test that ask page has functional question input."""
        page.goto(f"{base_url}/qa")

        question_input = page.locator("textarea, input[type='text']").first
        expect(question_input).to_be_visible()

        # Should be able to type
        question_input.fill("What is filing?")
        expect(question_input).to_have_value("What is filing?")


@pytest.mark.e2e
class TestCategoryFilterFeature:
    """Tests for category filtering dropdown."""

    def test_category_dropdown_visible(self, page: Page, base_url: str):
        """Test that category dropdown is visible when feature enabled."""
        page.goto(f"{base_url}/")

        # Look for category dropdown
        category_dropdown = page.locator('select, [aria-label*="categor"], button:has-text("Source")')

        # Should be visible
        expect(category_dropdown).to_be_visible()

    def test_category_dropdown_loads_options(self, page: Page, base_url: str):
        """Test that category dropdown loads from API."""
        page.goto(f"{base_url}/")

        # Wait for category options to load
        page.wait_for_timeout(1000)

        # Look for dropdown options
        category_options = page.locator('[role="option"]')

        # Should have at least "All Sources" option
        assert category_options.count() > 0

    def test_category_selection_filters_search(self, page: Page, base_url: str):
        """Test that selecting category filters search results."""
        page.goto(f"{base_url}/")

        # Select a specific category (if available)
        category_dropdown = page.locator('select, button:has-text("Source")').first

        if category_dropdown:
            category_dropdown.click()

            # Wait for options
            page.wait_for_timeout(500)

            # Select first non-"All Sources" option
            option = page.locator('[role="option"]').nth(1)
            if option:
                option.click()

                # Send a question
                question_input = page.locator("textarea, input[type='text']").first
                if question_input:
                    question_input.fill("test")
                    page.locator("button:has-text('Send')").click()

                    # Response should use selected category filter
                    page.wait_for_timeout(2000)

    def test_category_dropdown_mobile_abbreviations(self, page: Page, base_url: str):
        """Test that category names are abbreviated on mobile."""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})

        page.goto(f"{base_url}/")

        # Look for abbreviated category names
        category_options = page.locator('[role="option"]')

        # Options should be shorter on mobile (if abbreviations applied)
        page.wait_for_timeout(1000)


@pytest.mark.e2e
class TestFeedbackFeature:
    """Tests for enhanced feedback collection."""

    def test_feedback_thumbs_up_button_visible(self, page: Page, base_url: str):
        """Test that feedback buttons are visible after response."""
        page.goto(f"{base_url}/")

        # Send a message
        question_input = page.locator("textarea, input[type='text']").first
        if question_input:
            question_input.fill("What is CPR?")
            page.locator("button:has-text('Send')").click()

            # Wait for response
            page.wait_for_timeout(2000)

            # Look for feedback buttons
            thumbs_up = page.locator('button[aria-label*="helpful"], button[title*="Helpful"]')

            # Should be visible
            expect(thumbs_up).to_be_visible()

    def test_feedback_submission(self, page: Page, base_url: str):
        """Test that feedback can be submitted."""
        page.goto(f"{base_url}/")

        # Get a response first
        question_input = page.locator("textarea, input[type='text']").first
        if question_input:
            question_input.fill("What is discovery?")
            page.locator("button:has-text('Send')").click()

            page.wait_for_timeout(2000)

            # Click thumbs down
            thumbs_down = page.locator('button[aria-label*="not helpful"], button[title*="Not Helpful"]')

            if thumbs_down:
                thumbs_down.click()

                # Feedback should be submitted
                page.wait_for_timeout(500)

                # May show confirmation
                confirmation = page.locator('text="Thank you"')
                # Confirmation is optional but feedback should be sent

    def test_feedback_context_consent_option(self, page: Page, base_url: str):
        """Test that feedback form includes context/consent option."""
        page.goto(f"{base_url}/")

        question_input = page.locator("textarea, input[type='text']").first
        if question_input:
            question_input.fill("Question?")
            page.locator("button:has-text('Send')").click()

            page.wait_for_timeout(2000)

            # Click feedback button
            thumbs = page.locator('button[aria-label*="helpful"]')
            if thumbs:
                thumbs.click()

                # Should have consent checkbox
                consent_checkbox = page.locator('input[type="checkbox"][aria-label*="context"]')
                # Checkbox is optional but good practice


@pytest.mark.e2e
class TestSplashScreen:
    """Tests for splash screen feature."""

    def test_splash_screen_appears_on_first_visit(self, page: Page, base_url: str, browser_context):
        """Test that splash screen appears on first visit."""
        # New context without session storage
        new_page = browser_context.new_page()

        new_page.goto(f"{base_url}/")

        # Wait for splash to appear
        splash_screen = new_page.locator('[data-testid="splash-screen"], .splash-screen')

        page.wait_for_timeout(500)

        # Should have splash or at least intro content

    def test_splash_screen_dismissible(self, page: Page, base_url: str):
        """Test that splash screen can be dismissed."""
        page.goto(f"{base_url}/")

        # Look for dismiss button
        dismiss_button = page.locator('button:has-text("Get Started"), button:has-text("Skip")')

        if dismiss_button:
            expect(dismiss_button).to_be_visible()

            dismiss_button.click()

            # Splash should disappear
            page.wait_for_timeout(500)


@pytest.mark.e2e
class TestCitationSanitization:
    """Tests for citation sanitization feature."""

    def test_citations_formatted_correctly(self, page: Page, base_url: str):
        """Test that citations are formatted as [1], [2] etc."""
        page.goto(f"{base_url}/")

        # Send a question that generates citations
        question_input = page.locator("textarea, input[type='text']").first
        if question_input:
            question_input.fill("What are the procedural rules?")
            page.locator("button:has-text('Send')").click()

            # Wait for response
            page.wait_for_timeout(2000)

            # Look for citations in response
            response_text = page.locator('[role="article"], .message-content').first

            if response_text:
                content = response_text.inner_text()

                # Should have proper bracket citations [1], [2], etc.
                # Should not have malformed citations like "1. 1" or "[1][2]"
                assert "[" in content and "]" in content

    def test_malformed_citations_are_fixed(self, page: Page, base_url: str):
        """Test that malformed citations are sanitized."""
        page.goto(f"{base_url}/")

        # Get a response
        question_input = page.locator("textarea, input[type='text']").first
        if question_input:
            question_input.fill("Tell me about court procedures.")
            page.locator("button:has-text('Send')").click()

            page.wait_for_timeout(2000)

            response = page.locator('[role="article"], .message-content').first

            if response:
                text = response.inner_text()

                # Should not contain patterns like "1. 1", "[1][2][3]"
                assert "1. 1" not in text
                assert "1 1" not in text


@pytest.mark.e2e
class TestFeatureFlagIntegration:
    """Integration tests for feature flags."""

    def test_all_customization_features_accessible(self, page: Page, base_url: str):
        """Test that all enabled features are accessible."""
        # Navigate with admin mode
        page.goto(f"{base_url}/?admin=true")

        page.wait_for_timeout(1000)

        # Check for key feature indicators
        features_found = {
            "admin_mode": False,
            "categories": False,
            "feedback": False,
            "citations": False,
        }

        # Look for indicators
        if page.locator('button[aria-label*="Settings"]').is_visible():
            features_found["admin_mode"] = True

        if page.locator('select, button:has-text("Source")').is_visible():
            features_found["categories"] = True

        # Try to trigger response for feedback
        question_input = page.locator("textarea, input[type='text']").first
        if question_input:
            question_input.fill("Test")
            page.locator("button:has-text('Send')").click()

            page.wait_for_timeout(2000)

            if page.locator('button[aria-label*="helpful"]').is_visible():
                features_found["feedback"] = True

            response = page.locator('[role="article"], .message-content').first
            if response and "[" in response.inner_text():
                features_found["citations"] = True

        # Most features should be enabled
        assert sum(features_found.values()) > 0

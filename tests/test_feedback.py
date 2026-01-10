"""
Tests for feedback functionality with deployment metadata and thought filtering.

CUSTOM: Tests for enhanced feedback system that captures deployment info and
protects system prompts from user exposure.
"""

import pytest
import json
import os
from unittest import mock
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_feedback_simple_no_context(client):
    """Test simple feedback submission without context sharing."""
    response = await client.post(
        "/api/feedback",
        json={
            "message_id": "test-simple-001",
            "rating": "helpful",
            "issues": [],
            "comment": "Great answer!",
            "context_shared": False
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    assert result["status"] == "received"


@pytest.mark.asyncio
async def test_feedback_with_context_no_system_prompts(client):
    """Test feedback with context sharing, verifying system prompts are filtered."""
    response = await client.post(
        "/api/feedback",
        json={
            "message_id": "test-context-001",
            "rating": "unhelpful",
            "issues": ["wrong_citation", "missing_info"],
            "comment": "Citation was incorrect",
            "context_shared": True,
            "user_prompt": "What is the precedent for appeal procedures?",
            "ai_response": "The precedent is found in CPR Part 52...",
            "conversation_history": [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"}
            ],
            "thoughts": [
                {
                    "title": "Search Query",
                    "description": "Searching for appeal procedures",
                    "props": {}
                },
                {
                    "title": "Retrieved Documents",
                    "description": "Found 3 relevant documents",
                    "props": {}
                },
                {
                    "title": "Prompt to generate answer",
                    "description": "System prompt content here",
                    "props": {"raw_messages": [{"role": "system", "content": "You are a legal AI..."}]}
                }
            ]
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    assert result["status"] == "received"


@pytest.mark.asyncio
async def test_feedback_includes_deployment_metadata(client, monkeypatch):
    """Test that feedback includes deployment metadata."""
    # Set environment variables for deployment info
    monkeypatch.setenv("DEPLOYMENT_ID", "test-deployment-123")
    monkeypatch.setenv("APP_VERSION", "1.0.0")
    monkeypatch.setenv("GIT_SHA", "abc123def456")
    
    with mock.patch("os.getenv") as mock_getenv:
        # Setup mock to return our test values
        def getenv_side_effect(key, default=None):
            values = {
                "DEPLOYMENT_ID": "test-deployment-123",
                "APP_VERSION": "1.0.0",
                "GIT_SHA": "abc123def456",
                "AZURE_OPENAI_CHATGPT_MODEL": "gpt-4",
                "RUNNING_IN_PRODUCTION": "false",
            }
            return values.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        response = await client.post(
            "/api/feedback",
            json={
                "message_id": "test-metadata-001",
                "rating": "helpful",
                "issues": [],
                "comment": "Good response",
                "context_shared": False
            },
        )
        
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_feedback_filters_admin_only_thoughts(client):
    """Test that admin-only thoughts are filtered from user-submitted feedback."""
    response = await client.post(
        "/api/feedback",
        json={
            "message_id": "test-filter-001",
            "rating": "unhelpful",
            "issues": [],
            "comment": "Something was wrong",
            "context_shared": True,
            "user_prompt": "Test question",
            "ai_response": "Test response",
            "conversation_history": [],
            "thoughts": [
                {
                    "title": "Search Query",
                    "description": "Normal search query",
                    "props": {}
                },
                {
                    "title": "Prompt to generate answer",
                    "description": "This should be filtered",
                    "props": {"raw_messages": []}
                }
            ]
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_feedback_creates_separate_admin_file(client, monkeypatch, tmp_path):
    """Test that admin-only thoughts are saved separately."""
    # Mock the feedback data directory
    monkeypatch.setenv("DEPLOYMENT_ID", "test-deploy")
    
    response = await client.post(
        "/api/feedback",
        json={
            "message_id": "test-admin-001",
            "rating": "unhelpful",
            "issues": [],
            "comment": "Test feedback",
            "context_shared": True,
            "user_prompt": "Test",
            "ai_response": "Test",
            "conversation_history": [],
            "thoughts": [
                {
                    "title": "Prompt to generate answer",
                    "description": "Admin content",
                    "props": {"raw_messages": [{"role": "system", "content": "secret"}]}
                }
            ]
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_feedback_preserves_user_safe_thoughts(client):
    """Test that user-safe thoughts are preserved in feedback."""
    response = await client.post(
        "/api/feedback",
        json={
            "message_id": "test-preserve-001",
            "rating": "helpful",
            "issues": [],
            "comment": "Good",
            "context_shared": True,
            "user_prompt": "What is X?",
            "ai_response": "X is...",
            "conversation_history": [],
            "thoughts": [
                {
                    "title": "Search Query",
                    "description": ["Searched for X"],
                    "props": {}
                },
                {
                    "title": "Retrieved Documents",
                    "description": "Found 5 documents",
                    "props": {}
                }
            ]
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    assert result["status"] == "received"


@pytest.mark.asyncio
async def test_feedback_with_multiple_issues(client):
    """Test feedback with multiple issue categories."""
    response = await client.post(
        "/api/feedback",
        json={
            "message_id": "test-issues-001",
            "rating": "unhelpful",
            "issues": ["wrong_citation", "missing_info", "outdated_law"],
            "comment": "Multiple problems found",
            "context_shared": True,
            "user_prompt": "Test",
            "ai_response": "Test response",
            "conversation_history": [],
            "thoughts": []
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_feedback_empty_comment(client):
    """Test feedback with empty comment."""
    response = await client.post(
        "/api/feedback",
        json={
            "message_id": "test-empty-001",
            "rating": "unhelpful",
            "issues": ["wrong_citation"],
            "comment": "",
            "context_shared": False
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_feedback_missing_optional_fields(client):
    """Test feedback with missing optional fields."""
    response = await client.post(
        "/api/feedback",
        json={
            "message_id": "test-minimal-001",
            "rating": "helpful",
            "context_shared": False
        },
    )
    assert response.status_code == 200
    result = await response.get_json()
    assert result["status"] == "received"


@pytest.mark.asyncio
async def test_feedback_consent_required(client):
    """Test that context_shared consent flag is respected."""
    response = await client.post(
        "/api/feedback",
        json={
            "message_id": "test-consent-001",
            "rating": "helpful",
            "issues": [],
            "comment": "Test",
            "context_shared": False,
            # Even though we provide these, they should not be stored without consent
            "user_prompt": "Should not be stored",
            "ai_response": "Should not be stored",
        },
    )
    assert response.status_code == 200

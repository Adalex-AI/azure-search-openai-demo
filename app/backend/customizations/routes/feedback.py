from quart import Blueprint, request, jsonify
from opentelemetry import trace
import logging
import json

feedback_bp = Blueprint("feedback", __name__)
tracer = trace.get_tracer(__name__)
logger = logging.getLogger("azure")

@feedback_bp.post("/api/feedback")
async def submit_feedback():
    data = await request.get_json()

    # Check if user consented to share context
    context_shared = data.get("context_shared", False)

    # Log to Application Insights via OpenTelemetry
    with tracer.start_as_current_span("legal_feedback") as span:
        span.set_attribute("feedback.rating", data.get("rating"))
        span.set_attribute("feedback.issues", ",".join(data.get("issues", [])))
        span.set_attribute("feedback.has_comment", bool(data.get("comment")))
        span.set_attribute("feedback.message_id", data.get("message_id"))
        span.set_attribute("feedback.context_shared", context_shared)

        # Add detailed event
        event_data = {
            "rating": data.get("rating"),
            "comment": data.get("comment", "")[:100]  # Truncate for trace
        }
        
        # Include context data if user consented
        if context_shared:
            span.set_attribute("feedback.user_prompt", data.get("user_prompt", "")[:500])
            span.set_attribute("feedback.has_conversation_history", bool(data.get("conversation_history")))
            span.set_attribute("feedback.has_thoughts", bool(data.get("thoughts")))
            event_data["user_prompt"] = data.get("user_prompt", "")[:200]

        span.add_event("feedback_submitted", event_data)

    # Log full JSON for Blob Storage/Log Analytics ingestion
    # This log contains all the data including full context if shared
    log_payload = {
        "event_type": "legal_feedback",
        "context_shared": context_shared,
        "payload": {
            "message_id": data.get("message_id"),
            "rating": data.get("rating"),
            "issues": data.get("issues", []),
            "comment": data.get("comment", "")
        }
    }

    # Only include context data if user explicitly consented
    if context_shared:
        log_payload["context"] = {
            "user_prompt": data.get("user_prompt", ""),
            "ai_response": data.get("ai_response", ""),
            "conversation_history": data.get("conversation_history", []),
            "thoughts": data.get("thoughts", [])
        }

    logger.info(json.dumps(log_payload))

    return jsonify({"status": "received"})

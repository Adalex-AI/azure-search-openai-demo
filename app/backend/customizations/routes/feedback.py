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

    # Log to Application Insights via OpenTelemetry
    with tracer.start_as_current_span("legal_feedback") as span:
        span.set_attribute("feedback.rating", data.get("rating"))
        span.set_attribute("feedback.issues", ",".join(data.get("issues", [])))
        span.set_attribute("feedback.has_comment", bool(data.get("comment")))
        span.set_attribute("feedback.message_id", data.get("message_id"))

        # Add detailed event
        span.add_event("feedback_submitted", {
            "rating": data.get("rating"),
            "comment": data.get("comment", "")[:100] # Truncate for trace
        })

    # Log full JSON for Blob Storage/Log Analytics ingestion
    logger.info(json.dumps({
        "event_type": "legal_feedback",
        "payload": data
    }))

    return jsonify({"status": "received"})

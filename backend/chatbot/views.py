import logging
import re
from uuid import uuid4

from django.conf import settings
from ai.prompt import is_sensitive_request
from ai.service import AIService
from common.http import api_response, json_endpoint, rate_limit
from leads.repository import LeadRepository
from .qualification import apply_conversation_lead_capture
from .repository import ChatRepository
from .validation import validate_chat

logger = logging.getLogger(__name__)
REFUSAL = "I can’t help with internal instructions, credentials, or configuration. I can answer questions about Maehan Solutions and its planned product directions."


@json_endpoint
@rate_limit(settings.CHAT_RATE_LIMIT_PER_HOUR, "chat")
def chat(request):
    message, session_id, errors = validate_chat(request.json)
    if errors:
        return api_response({"error": "Please correct the request.", "fields": errors}, 400)
    session_id = session_id or str(uuid4())
    repository = ChatRepository()
    try:
        repository.create_session(session_id)
        repository.add_message(session_id, "user", message)

        lead_capture = repository.lead_capture_state(session_id)
        if is_sensitive_request(message):
            reply = REFUSAL
        else:
            lead_capture, transition_prompt = apply_conversation_lead_capture(lead_capture, message)
            repository.set_lead_capture_state(session_id, lead_capture)
            reply = AIService().response(repository.history(session_id), transition_prompt=transition_prompt)

            if lead_capture.get("status") == "completed" and not lead_capture.get("persisted"):
                lead_document = dict(lead_capture.get("data", {}))
                lead_document.setdefault("interested_product", lead_capture.get("product", "general"))
                lead_document.setdefault("message", "Lead captured through website chatbot conversation.")
                LeadRepository().create(lead_document, source="chatbot", chatbot_generated=True)
                lead_capture["persisted"] = True
                repository.set_lead_capture_state(session_id, lead_capture)
        repository.add_message(session_id, "assistant", reply)
    except Exception:
        logger.exception("Chat request failed")
        return api_response({"error": "We are having trouble processing your message. Please try again shortly."}, 503)
    return api_response({"session_id": session_id, "message": reply})


@json_endpoint
@rate_limit(settings.CHAT_RATE_LIMIT_PER_HOUR, "chat-session")
def create_session(request):
    session_id = str(uuid4())
    try:
        ChatRepository().create_session(session_id)
    except Exception:
        logger.exception("Chat session creation failed")
        return api_response({"error": "Our servers are down! Please try again after some time."}, 503)
    return api_response({"session_id": session_id}, 201)

import re

SESSION_ID_PATTERN = re.compile(r"^[a-f0-9-]{36}$")


def validate_chat(payload):
    message = payload.get("message")
    session_id = payload.get("session_id")
    errors = {}
    if not isinstance(message, str) or not 1 <= len(message.strip()) <= 2000:
        errors["message"] = "Message must be between 1 and 2,000 characters."
    if session_id is not None and (not isinstance(session_id, str) or not SESSION_ID_PATTERN.fullmatch(session_id)):
        errors["session_id"] = "Session identifier is invalid."
    return message.strip() if isinstance(message, str) else "", session_id, errors

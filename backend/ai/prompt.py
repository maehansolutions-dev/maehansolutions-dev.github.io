from pathlib import Path


PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "system.md"


def load_system_prompt():
    """Load the editable prompt file once when the Django process starts."""
    return PROMPT_FILE.read_text(encoding="utf-8").strip()


SYSTEM_PROMPT = load_system_prompt()

INJECTION_MARKERS = ("system prompt", "hidden instruction", "ignore your instructions", "api key", "environment variable", "internal configuration", "reveal your prompt")


def is_sensitive_request(message):
    return any(marker in message.lower() for marker in INJECTION_MARKERS)

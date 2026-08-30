import os
import urllib.request
import urllib.parse
import json
import re
import socket
import subprocess
import logging
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

logger = logging.getLogger(__name__)

INTEREST_TERMS = ("demo", "contact", "connect", "interested", "evaluate", "proposal", "pilot", "consult", "discuss", "learn more", "help us", "hello", "hi", "hey", "good morning", "good afternoon", "welcome")
PRODUCT_TERMS = {"document_intelligence": ("document", "handwriting", "legacy record", "digitiz"), "engineering_drawing_intelligence": ("drawing", "markup", "annotation", "engineering")}
POSITIVE_SENTIMENT_TERMS = ("happy", "excited", "interested", "good", "love", "great", "helpful")
NEGATIVE_SENTIMENT_TERMS = ("not interested", "frustrated", "disappointed", "complaint", "not a fit", "dont want", "don't want", "no thanks", "no thank you")
PHONE_PATTERN = re.compile(r"^[0-9+().\-\s]{7,30}$")

_EMAIL_CACHE = {}

def validate_email_abstract(email_address):
    if email_address in _EMAIL_CACHE:
        return _EMAIL_CACHE[email_address]

    api_key = os.getenv("ABSTRACT_EMAIL_VALIDATION_API_KEY")
    if not api_key:
        return _fallback_email_validation(email_address)

    url = f"https://emailvalidation.abstractapi.com/v1/?api_key={api_key}&email={urllib.parse.quote(email_address)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if data.get("is_disposable_email", {}).get("value"):
            result = "disposable"
        elif data.get("deliverability") == "UNDELIVERABLE":
            result = "undeliverable"
        elif data.get("is_valid_format", {}).get("value") == False:
            result = "invalid_format"
        else:
            result = "verified"
            
        _EMAIL_CACHE[email_address] = result
        return result
    except Exception as e:
        logger.warning(f"Abstract API email validation failed: {e}")
        return _fallback_email_validation(email_address)

def _fallback_email_validation(email_address):
    domain = email_address.split('@')[-1] if '@' in email_address else ""
    if not domain:
        return "unknown"
    try:
        result = subprocess.run(["nslookup", "-q=mx", domain], capture_output=True, text=True, timeout=2)
        if "mail exchanger" in result.stdout.lower() or "mx" in result.stdout.lower():
            return "unknown"
    except Exception:
        pass
    return "unknown"

def analyze_message(message):
    text = (message or "").lower()
    product = next((name for name, terms in PRODUCT_TERMS.items() if any(term in text for term in terms)), "general")
    intent = sum(term in text for term in INTEREST_TERMS)
    if any(term in text for term in NEGATIVE_SENTIMENT_TERMS):
        sentiment = "negative"
    elif intent or any(term in text for term in POSITIVE_SENTIMENT_TERMS):
        sentiment = "positive"
    else:
        sentiment = "neutral"
    return product, intent, sentiment

def _extract_value(value, markers):
    if not isinstance(value, str):
        return ""
    text = value.strip()
    lowered = text.lower()
    for marker in markers:
        marker_index = lowered.find(marker)
        if marker_index != -1:
            text = text[marker_index + len(marker):].strip()
            break
    text = re.sub(r"^(?:name|email|phone)\s*(?:is|:)?\s*", "", text, flags=re.IGNORECASE)
    return text.strip(" .,")

def name(value):
    parsed = _extract_value(value, ("my name is", "i am", "i'm ", "this is", "call me"))
    if not (2 <= len(parsed) <= 120 and "@" not in parsed):
        return None
    return re.sub(r"\s+", " ", parsed)

def email(value):
    parsed = _extract_value(value, ("my email is", "email is", "email:", "work email is", "my work email is"))
    if not parsed:
        parsed = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", value or "")
        parsed = parsed.group(0) if parsed else ""
    value = parsed.strip().lower()
    try:
        validate_email(value)
        return value
    except ValidationError:
        return None

def phone(value):
    parsed = _extract_value(value, ("my phone number is", "phone number is", "phone is", "my number is", "number is", "call me at"))
    if not parsed:
        parsed = re.search(r"(?:\+?\d[\d().\-\s]{6,}\d)", value or "")
        parsed = parsed.group(0) if parsed else ""
    value = parsed.strip()
    if not PHONE_PATTERN.fullmatch(value):
        return None
    digits = re.sub(r'\D', '', value)
    if not digits or len(digits) < 7 or len(digits) > 15:
        return None
    if len(set(digits)) <= 2 and len(digits) >= 8:
        return None
    if "12345678" in digits or "98765432" in digits:
        return None
    return value

def _parse_name_and_company(text):
    sentence = text.strip()
    if not sentence:
        return None, None
    # Special case: Just "I'm from X"
    match = re.match(r"(?:i['’]m|i am)\s+from\s+(.+)", sentence, flags=re.IGNORECASE)
    if match:
        return None, match.group(1).strip()
    
    match = re.match(r"(?:i['’]m|i am|my name is|this is)\s+(.+?)(?:\s+from\s+(.+)|$)", sentence, flags=re.IGNORECASE)
    if match:
        n = match.group(1).strip()
        c = match.group(2).strip() if match.group(2) else None
        return re.sub(r"\s+", " ", n), c
    if re.search(r"\bfrom\b", sentence, flags=re.IGNORECASE):
        match = re.match(r"(.+?)\s+from\s+(.+)", sentence, flags=re.IGNORECASE)
        if match:
            return re.sub(r"\s+", " ", match.group(1).strip()), match.group(2).strip()
    return None, None

def _looks_like_name_reply(text):
    lowered = (text or "").strip().lower()
    if not lowered:
        return False
    if re.match(r"(?:i['’]m|i am|my name is|this is)\s+.+", lowered):
        return True
    return bool(re.search(r"\b(?:mr|ms|mrs|dr)\b\s+[a-z]", lowered))

def is_ambiguous(text):
    if not text: return False
    if re.search(r'[^a-zA-Z0-9\s.\-&,]', text): return True
    lower = text.lower()
    if 'slutions' in lower or 'solutons' in lower or 'tecnolog' in lower or 'maehan' in lower:
        return True
    return False

def apply_conversation_lead_capture(state, message):
    state = state or {}
    state.setdefault("data", {})
    state.setdefault("active", False)
    state.setdefault("status", "new")
    
    text = (message or "").strip()
    if not text:
        return state, "Ask the user to share a little more so you can help them better."

    product, intent, sentiment = analyze_message(text)
    if sentiment == "negative":
        state["active"] = False
        state["status"] = "declined"
        state["current_field"] = None
        return state, "Thank the user for their feedback and politely end the conversation."

    if not state["active"]:
        if intent <= 0 and not (text.lower() in {"hi", "hello", "hey", "good morning", "good afternoon", "welcome"}):
            return state, None
        state["active"] = True
        state["status"] = "in_progress"
        state["product"] = product
        return state, "Ask the user about the problem they are trying to solve today, mentioning that we help teams reduce manual work in document-heavy operations and AI-powered workflows."

    # Active flow - attempt to parse fields from text
    parsed_email = email(text)
    if parsed_email:
        validation_result = validate_email_abstract(parsed_email)
        if validation_result == "disposable":
            return state, "Politely inform the user that disposable email addresses are not accepted and ask for their real work email address."
        elif validation_result == "undeliverable":
            return state, "Politely ask the user to double check their email address, as it seems to be undeliverable."
        elif validation_result == "invalid_format":
            return state, "Ask the user to provide a validly formatted email address."
        else:
            state["data"]["email"] = parsed_email
            state["data"]["email_verification_status"] = validation_result

    parsed_phone = phone(text)
    if parsed_phone:
        state["data"]["phone"] = parsed_phone

    parsed_name, parsed_company = _parse_name_and_company(text)
    if not parsed_name and _looks_like_name_reply(text):
        parsed_name = name(text)
        
    if parsed_name and not state["data"].get("name"):
        state["data"]["name"] = parsed_name
        
    if parsed_company and not state["data"].get("company"):
        if is_ambiguous(parsed_company):
            state["unconfirmed_company"] = parsed_company
        else:
            state["data"]["company"] = parsed_company

    if not state["data"].get("requirement") and not parsed_name and not parsed_email and not parsed_phone:
        if not state.get("context_asked"):
            state["context_asked"] = True
        else:
            state["data"]["requirement"] = text

    if state.get("unconfirmed_company"):
        lower_text = text.lower()
        if lower_text in {"yes", "yep", "correct", "that's right", "yeah", "yes it is"}:
            state["data"]["company"] = state["unconfirmed_company"]
            del state["unconfirmed_company"]
        elif lower_text in {"no", "nope", "incorrect"}:
            del state["unconfirmed_company"]
            return state, "Ask the user to clarify their correct company name."
        elif not parsed_company and not parsed_name and not parsed_email and not parsed_phone:
            return state, f"Confirm with the user if their company name is '{state['unconfirmed_company']}'."

    # Check what is still missing
    if not state["data"].get("name"):
        return state, "Ask the user for their full name."
    
    if not state["data"].get("company") and not state.get("unconfirmed_company"):
        return state, "Ask the user for their company name."
        
    if state.get("unconfirmed_company"):
        return state, f"Confirm with the user if their company name is '{state['unconfirmed_company']}'."
        
    if not state["data"].get("email"):
        return state, "Ask the user for their work email address."
        
    if not state["data"].get("phone"):
        return state, "Ask the user for the best phone number to reach them on."

    # All details collected
    state["data"]["interested_product"] = state.get("product", "general")
    state["status"] = "completed"
    state["active"] = False
    state["current_field"] = None
    first_name = state["data"].get("name", "").split(" ")[0] if state["data"].get("name") else ""
    return state, f"Thank the user '{first_name}' and let them know the Maehan Solutions team will follow up next."

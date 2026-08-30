import re

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

EMAIL_MAX_LENGTH = 254
PHONE_PATTERN = re.compile(r"^[0-9+().\-\s]{7,30}$")
TEXT_LIMITS = {"name": 120, "company": 160, "job_title": 120, "industry": 100, "country": 100, "interested_product": 100, "message": 2000}
ALLOWED_PRODUCTS = {"document_intelligence", "engineering_drawing_intelligence", "general"}


def clean_text(value, maximum):
    return value.strip() if isinstance(value, str) and len(value.strip()) <= maximum else None


def validate_lead(payload):
    errors, cleaned = {}, {}
    for field, maximum in TEXT_LIMITS.items():
        value = payload.get(field, "")
        if value:
            cleaned[field] = clean_text(value, maximum)
            if cleaned[field] is None:
                errors[field] = f"Must be a text value of {maximum} characters or fewer."
    name = cleaned.get("name")
    if not name:
        errors["name"] = "Name is required."
    email = payload.get("email", "")
    if not isinstance(email, str) or len(email.strip()) > EMAIL_MAX_LENGTH:
        errors["email"] = "Enter a valid email address."
    else:
        try:
            validate_email(email.strip())
            cleaned["email"] = email.strip().lower()
        except ValidationError:
            errors["email"] = "Enter a valid email address."
    phone = payload.get("phone", "")
    if phone:
        if not isinstance(phone, str) or not PHONE_PATTERN.fullmatch(phone.strip()):
            errors["phone"] = "Enter a valid international phone number."
        else:
            cleaned["phone"] = phone.strip()
    if payload.get("interested_product", "general") not in ALLOWED_PRODUCTS:
        errors["interested_product"] = "Select a valid product interest."
    else:
        cleaned["interested_product"] = payload.get("interested_product", "general")
    if payload.get("consent") is not True:
        errors["consent"] = "Consent is required to submit your details."
    if not cleaned.get("message"):
        errors["message"] = "Please provide a short requirement or message."
    return cleaned, errors

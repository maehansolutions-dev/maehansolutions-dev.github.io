import logging

from django.conf import settings
from django.http import JsonResponse
from common.http import api_response, json_endpoint, rate_limit
from database.mongo import database_is_available
from .repository import LeadRepository
from .validation import validate_lead

logger = logging.getLogger(__name__)


@json_endpoint
@rate_limit(settings.LEAD_RATE_LIMIT_PER_HOUR, "lead")
def create_lead(request):
    if request.json.get("website"):
        return api_response({"success": True, "message": "Thanks for your interest."}, 201)
    lead, errors = validate_lead(request.json)
    if errors:
        return api_response({"error": "Please correct the highlighted fields.", "fields": errors}, 400)
    try:
        lead_id, score, quality = LeadRepository().create(lead)
    except Exception:
        logger.exception("Lead persistence failed")
        return api_response({"error": "We are having trouble processing your request. Please try again shortly."}, 503)
    return api_response({"success": True, "lead_id": lead_id, "lead_score": score, "lead_quality": quality, "message": "Thanks — the Maehan Solutions team will be in touch."}, 201)


def health(request):
    if request.method != "GET":
        return api_response({"error": "Method not allowed."}, 405)
    available = database_is_available()
    return JsonResponse({"status": "ok" if available else "degraded", "database": "available" if available else "unavailable"}, status=200 if available else 503)

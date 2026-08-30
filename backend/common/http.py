import json
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def api_response(payload, status=200):
    return JsonResponse(payload, status=status)


def json_endpoint(view):
    @csrf_exempt
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.method != "POST":
            return api_response({"error": "Method not allowed."}, 405)
        if request.content_type.split(";")[0] != "application/json":
            return api_response({"error": "Content-Type must be application/json."}, 415)
        if len(request.body) > settings.MAX_REQUEST_BODY_BYTES:
            return api_response({"error": "Request is too large."}, 413)
        try:
            request.json = json.loads(request.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return api_response({"error": "Request body must contain valid JSON."}, 400)
        if not isinstance(request.json, dict):
            return api_response({"error": "JSON body must be an object."}, 400)
        return view(request, *args, **kwargs)
    return wrapped


def rate_limit(limit, namespace):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            ip = request.META.get("REMOTE_ADDR", "unknown")
            key = f"rate:{namespace}:{ip}"
            count = cache.get(key, 0)
            if count >= limit:
                return api_response({"error": "Too many requests. Please try again later."}, 429)
            cache.set(key, count + 1, timeout=3600)
            return view(request, *args, **kwargs)
        return wrapped
    return decorator

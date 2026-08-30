from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404


def homepage(request):
    """Serve the existing static site without moving or rebuilding it."""
    if request.method != "GET":
        raise Http404
    index_file = Path(settings.BASE_DIR).parent / "index.html"
    if not index_file.is_file():
        raise Http404
    return FileResponse(index_file.open("rb"), content_type="text/html; charset=utf-8")

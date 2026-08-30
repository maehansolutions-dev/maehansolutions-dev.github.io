from django.urls import include, path
from .views import homepage

urlpatterns = [
    path("", homepage, name="homepage"),
    path("api/", include("leads.urls")),
    path("api/", include("chatbot.urls")),
]

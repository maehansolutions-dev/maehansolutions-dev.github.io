from django.urls import path
from .views import create_lead, health

urlpatterns = [path("leads/", create_lead), path("health/", health)]

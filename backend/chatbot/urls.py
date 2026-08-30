from django.urls import path
from .views import chat, create_session

urlpatterns = [path("chat/", chat), path("chat/session/", create_session)]

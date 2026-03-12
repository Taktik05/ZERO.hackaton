"""Маршруты служебного приложения core."""
from django.urls import path

from core.views import HomeRedirectView

app_name = "core"

urlpatterns = [
    path("", HomeRedirectView.as_view(), name="home"),
]

"""URL-маршруты проекта Zero."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("", include("antifraud.urls")),
    path("api/v1/", include("antifraud.api.urls")),
]

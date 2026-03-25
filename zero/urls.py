"""URL-маршруты проекта Zero."""
from django.contrib import admin
from django.urls import include, path

from antifraud.api.views import TransactionViewSet

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("", include("antifraud.urls")),
    path("api/v1/", include("antifraud.api.urls")),
    path("api/ingest/", TransactionViewSet.as_view({"post": "create"}), name="api-ingest"),
    path(
        "api/confirm/<int:pk>/",
        TransactionViewSet.as_view({"post": "confirm"}),
        name="api-confirm",
    ),
]

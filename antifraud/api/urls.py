"""URL-маршруты API anti-fraud приложения."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from antifraud.api.views import TransactionViewSet

app_name = "antifraud-api"

router = DefaultRouter()
router.register("transactions", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("", include(router.urls)),
]

"""URL-маршруты веб-интерфейса antifraud."""
from django.urls import path

from antifraud.views import (
    TransactionCreateView,
    TransactionDetailView,
    TransactionListView,
    confirm_transaction_view,
)

app_name = "antifraud"

urlpatterns = [
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("transactions/new/", TransactionCreateView.as_view(), name="transaction-create"),
    path("transactions/<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path(
        "transactions/<int:pk>/confirm/",
        confirm_transaction_view,
        name="transaction-confirm",
    ),
]

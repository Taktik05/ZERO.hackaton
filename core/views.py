"""Представления служебного приложения core."""
from django.urls import reverse_lazy
from django.views.generic import RedirectView


class HomeRedirectView(RedirectView):
    """Перенаправляет на основной список транзакций anti-fraud модуля."""

    pattern_name = "antifraud:transaction-list"
    permanent = False
    query_string = True
    url = reverse_lazy("antifraud:transaction-list")

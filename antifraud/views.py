"""Представления веб-интерфейса anti-fraud модуля."""
from __future__ import annotations

import random
from decimal import Decimal

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from antifraud.forms import TransactionCreateForm
from antifraud.models import Transaction, TransactionStatus
from antifraud.services import RuleEngine

HOME_COUNTRY = "RU"
FOREIGN_COUNTRIES = ("NG", "KZ", "UA", "US")


class TransactionListView(ListView):
    """Отображает список последних транзакций с решениями антифрода."""

    model = Transaction
    template_name = "antifraud/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 20


class TransactionCreateView(CreateView):
    """Создаёт транзакцию и запускает anti-fraud RuleEngine."""

    model = Transaction
    form_class = TransactionCreateForm
    template_name = "antifraud/transaction_form.html"

    def form_valid(self, form: TransactionCreateForm) -> HttpResponse:
        response = super().form_valid(form)
        RuleEngine().evaluate(self.object)
        messages.success(self.request, "Транзакция создана и проверена антифрод-движком.")
        return response

    def get_success_url(self) -> str:
        return reverse("antifraud:transaction-detail", kwargs={"pk": self.object.pk})


class TransactionDetailView(DetailView):
    """Отображает карточку транзакции и результаты проверки правил."""

    model = Transaction
    template_name = "antifraud/transaction_detail.html"
    context_object_name = "transaction"


class AntifraudDemoView(TemplateView):
    """Отображает интерактивную демо-страницу генерации транзакций."""

    template_name = "antifraud/demo.html"


@require_POST
def create_random_transaction_view(request: HttpRequest) -> HttpResponse:
    """Создаёт случайную демо-транзакцию по нажатию кнопки и выполняет её проверку."""

    random_payload = _build_random_transaction_payload()
    transaction = Transaction.objects.create(**random_payload)
    RuleEngine().evaluate(transaction)

    messages.success(request, "Случайная транзакция автоматически создана и проверена.")
    return redirect("antifraud:transaction-detail", pk=transaction.pk)


@require_POST
def confirm_transaction_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Подтверждает транзакцию клиентом и запускает повторную оценку риска."""

    tx = get_object_or_404(Transaction, pk=pk)
    if tx.status == TransactionStatus.DECLINED:
        messages.error(request, "Отклонённую транзакцию нельзя подтвердить.")
        return redirect("antifraud:transaction-detail", pk=tx.pk)

    tx.is_client_confirmed = True
    tx.confirmed_at = timezone.now()
    tx.save(update_fields=["is_client_confirmed", "confirmed_at", "updated_at"])

    RuleEngine().evaluate(tx)
    messages.success(request, "Транзакция подтверждена клиентом и переоценена.")
    return redirect("antifraud:transaction-detail", pk=tx.pk)


def _build_random_transaction_payload() -> dict[str, str | Decimal]:
    """Формирует данные для безопасного автосоздания демо-транзакции."""

    is_home_country = random.random() < 0.7
    country = HOME_COUNTRY if is_home_country else random.choice(FOREIGN_COUNTRIES)

    is_low_amount = random.random() < 0.7
    amount = Decimal(random.randint(10, 900) if is_low_amount else random.randint(1000, 10000))

    use_main_email = random.random() < 0.85
    email = "user@example.com"
    if not use_main_email:
        email = f"demo{random.randint(10000, 99999)}@temp-mail.org"

    ip_address = "5.45.207.10"
    if country != HOME_COUNTRY:
        first_octet = random.randint(1, 223)
        second_octet = random.randint(0, 255)
        third_octet = random.randint(0, 255)
        fourth_octet = random.randint(1, 254)
        ip_address = f"{first_octet}.{second_octet}.{third_octet}.{fourth_octet}"

    return {
        "amount": amount,
        "currency": "RUB",
        "card_number": "4111111111111111",
        "card_holder": "Demo User",
        "email": email,
        "ip_address": ip_address,
        "country": country,
        "device_id": "demo_device",
        "merchant_id": "demo_merchant",
    }

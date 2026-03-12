"""Представления веб-интерфейса anti-fraud модуля."""
from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView

from antifraud.forms import TransactionCreateForm
from antifraud.models import Transaction, TransactionStatus
from antifraud.services import RuleEngine


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

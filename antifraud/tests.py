"""Тесты anti-fraud веб-интерфейса."""
from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from antifraud.models import Transaction, TransactionStatus


class TransactionAutoCreateViewTests(TestCase):
    """Проверяет автосоздание транзакции через кнопку на странице списка."""

    def test_transaction_list_contains_auto_create_form(self) -> None:
        """Страница списка содержит форму с кнопкой автосоздания транзакции."""

        response = self.client.get(reverse("antifraud:transaction-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("antifraud:transaction-create-random"))
        self.assertContains(response, "Создать транзакцию автоматически")

    def test_post_to_create_random_endpoint_creates_transaction(self) -> None:
        """POST-запрос на endpoint автосоздания создаёт транзакцию и делает редирект в карточку."""

        url = reverse("antifraud:transaction-create-random")

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 1)

        transaction = Transaction.objects.get()
        self.assertEqual(
            response.url,
            reverse("antifraud:transaction-detail", kwargs={"pk": transaction.pk}),
        )
        self.assertNotEqual(transaction.status, TransactionStatus.PENDING)
        self.assertGreaterEqual(transaction.risk_score, 0)

    def test_get_to_create_random_endpoint_is_not_allowed(self) -> None:
        """GET-запрос запрещён, так как endpoint предназначен только для POST."""

        response = self.client.get(reverse("antifraud:transaction-create-random"))

        self.assertEqual(response.status_code, 405)

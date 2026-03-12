"""Модели антифрод-домена."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TransactionStatus(models.TextChoices):
    """Статусы обработки транзакции."""

    PENDING = "PENDING", "Ожидает проверки"
    APPROVED = "APPROVED", "Одобрена"
    MANUAL_REVIEW = "MANUAL_REVIEW", "Ручная проверка"
    DECLINED = "DECLINED", "Отклонена"


class Transaction(models.Model):
    """Платежная транзакция, поступающая на антифрод-проверку."""

    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    card_number = models.CharField(max_length=19)
    card_holder = models.CharField(max_length=120)
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    country = models.CharField(max_length=2, default="US")
    device_id = models.CharField(max_length=128)
    merchant_id = models.CharField(max_length=64)

    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
    )
    risk_score = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    decision_reason = models.CharField(max_length=255, blank=True)
    is_client_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("status", "created_at"), name="tx_status_created_idx"),
            models.Index(fields=("merchant_id", "created_at"), name="tx_merchant_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.external_id} ({self.amount} {self.currency})"

    @property
    def masked_card(self) -> str:
        """Возвращает маску номера карты для безопасного отображения."""

        normalized = self.card_number.replace(" ", "")
        if len(normalized) < 10:
            return "****"
        return f"{normalized[:6]}******{normalized[-4:]}"


class FraudRule(models.Model):
    """Настраиваемое антифрод-правило."""

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    score = models.PositiveSmallIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    threshold_decimal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code}: {self.name}"


class RuleCheckResult(models.Model):
    """Результат выполнения конкретного правила для транзакции."""

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="rule_results",
    )
    rule = models.ForeignKey(
        FraudRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="check_results",
    )
    rule_code = models.CharField(max_length=64)
    is_triggered = models.BooleanField(default=False)
    score_delta = models.PositiveSmallIntegerField(default=0)
    message = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=("transaction", "rule_code"), name="rule_result_tx_code_idx")]

    def __str__(self) -> str:
        state = "TRIGGERED" if self.is_triggered else "PASSED"
        return f"{self.rule_code} for {self.transaction_id}: {state}"

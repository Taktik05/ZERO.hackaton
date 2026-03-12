"""Административная панель для anti-fraud сущностей."""
from django.contrib import admin

from antifraud.models import FraudRule, RuleCheckResult, Transaction


@admin.register(FraudRule)
class FraudRuleAdmin(admin.ModelAdmin):
    """Администрирование правил антифрода."""

    list_display = ("code", "name", "score", "threshold_decimal", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "description")
    ordering = ("code",)


class RuleCheckResultInline(admin.TabularInline):
    """Результаты проверок в карточке транзакции."""

    model = RuleCheckResult
    extra = 0
    can_delete = False
    fields = ("rule_code", "is_triggered", "score_delta", "message", "created_at")
    readonly_fields = fields


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Администрирование транзакций."""

    list_display = (
        "external_id",
        "masked_card",
        "amount",
        "currency",
        "country",
        "status",
        "risk_score",
        "created_at",
    )
    list_filter = ("status", "currency", "country")
    search_fields = ("external_id", "email", "merchant_id", "device_id")
    readonly_fields = ("external_id", "risk_score", "decision_reason", "created_at", "updated_at")
    inlines = (RuleCheckResultInline,)


@admin.register(RuleCheckResult)
class RuleCheckResultAdmin(admin.ModelAdmin):
    """Администрирование результатов проверок правил."""

    list_display = ("transaction", "rule_code", "is_triggered", "score_delta", "created_at")
    list_filter = ("is_triggered", "rule_code")
    search_fields = ("transaction__external_id", "rule_code", "message")
    readonly_fields = ("transaction", "rule", "rule_code", "is_triggered", "score_delta", "message", "details", "created_at")

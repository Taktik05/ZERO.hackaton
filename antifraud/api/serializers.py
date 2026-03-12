"""DRF serializers for anti-fraud API endpoints."""
from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from antifraud.models import RuleCheckResult, Transaction, TransactionStatus
from antifraud.services import RuleEngine


class RuleCheckResultSerializer(serializers.ModelSerializer):
    """Serialized representation of a single rule evaluation result."""

    class Meta:
        model = RuleCheckResult
        fields = (
            "id",
            "rule_code",
            "is_triggered",
            "score_delta",
            "message",
            "details",
            "created_at",
        )
        read_only_fields = fields


class TransactionSerializer(serializers.ModelSerializer):
    """Read serializer with nested rule evaluation results."""

    rule_results = RuleCheckResultSerializer(many=True, read_only=True)
    masked_card = serializers.CharField(read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id",
            "external_id",
            "amount",
            "currency",
            "card_holder",
            "masked_card",
            "email",
            "ip_address",
            "country",
            "device_id",
            "merchant_id",
            "status",
            "risk_score",
            "decision_reason",
            "is_client_confirmed",
            "confirmed_at",
            "created_at",
            "updated_at",
            "rule_results",
        )
        read_only_fields = (
            "id",
            "external_id",
            "masked_card",
            "status",
            "risk_score",
            "decision_reason",
            "is_client_confirmed",
            "confirmed_at",
            "created_at",
            "updated_at",
            "rule_results",
        )


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Create serializer that runs the anti-fraud rule engine."""

    class Meta:
        model = Transaction
        fields = (
            "amount",
            "currency",
            "card_number",
            "card_holder",
            "email",
            "ip_address",
            "country",
            "device_id",
            "merchant_id",
        )

    def create(self, validated_data: dict) -> Transaction:
        transaction = Transaction.objects.create(**validated_data)
        RuleEngine().evaluate(transaction)
        transaction.refresh_from_db()
        return transaction


class TransactionConfirmSerializer(serializers.Serializer):
    """Serializer used to confirm transaction by customer action."""

    confirmation = serializers.BooleanField(default=True)

    def validate_confirmation(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("Confirmation must be true.")
        return value

    def save(self, **kwargs) -> Transaction:
        transaction: Transaction = self.context["transaction"]
        if transaction.status == TransactionStatus.DECLINED:
            raise serializers.ValidationError("Declined transaction cannot be confirmed.")

        transaction.is_client_confirmed = True
        transaction.confirmed_at = timezone.now()
        transaction.save(update_fields=["is_client_confirmed", "confirmed_at", "updated_at"])
        RuleEngine().evaluate(transaction)
        transaction.refresh_from_db()
        return transaction

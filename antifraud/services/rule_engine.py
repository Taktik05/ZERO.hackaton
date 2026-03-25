"""RuleEngine для вычисления антифрод-рисков и решения по транзакциям."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db import transaction as db_transaction
from django.db.models import Count
from django.utils import timezone

from antifraud.models import FraudRule, RuleCheckResult, Transaction, TransactionStatus


@dataclass(frozen=True)
class RuleEvaluation:
    """Результат вычисления одного правила."""

    rule_code: str
    is_triggered: bool
    score_delta: int
    message: str
    details: dict[str, object]
    rule: FraudRule | None = None


class RuleEngine:
    """Применяет набор бизнес-правил к транзакции и выставляет итоговый статус."""

    DEFAULT_MANUAL_REVIEW_THRESHOLD = 40
    DEFAULT_DECLINE_THRESHOLD = 70

    def evaluate(self, transaction: Transaction) -> Transaction:
        """Выполняет проверку транзакции, сохраняет результаты и финальное решение."""

        active_rules = {
            rule.code: rule
            for rule in FraudRule.objects.filter(is_active=True).order_by("code")
        }

        evaluations = [
            self._check_high_amount(transaction, active_rules.get("HIGH_AMOUNT")),
            self._check_foreign_country(transaction, active_rules.get("FOREIGN_COUNTRY")),
            self._check_velocity(transaction, active_rules.get("VELOCITY")),
            self._check_disposable_email(transaction, active_rules.get("DISPOSABLE_EMAIL")),
        ]

        total_risk = sum(max(item.score_delta, 0) for item in evaluations)

        with db_transaction.atomic():
            RuleCheckResult.objects.filter(transaction=transaction).delete()

            for item in evaluations:
                RuleCheckResult.objects.create(
                    transaction=transaction,
                    rule=item.rule,
                    rule_code=item.rule_code,
                    is_triggered=item.is_triggered,
                    score_delta=item.score_delta,
                    message=item.message,
                    details=item.details,
                )

            decision_status, reason = self._get_decision(transaction, total_risk)

            transaction.risk_score = min(total_risk, 100)
            transaction.status = decision_status
            transaction.decision_reason = reason
            transaction.save(update_fields=["risk_score", "status", "decision_reason", "updated_at"])

        return transaction

    def _check_high_amount(self, transaction: Transaction, rule: FraudRule | None) -> RuleEvaluation:
        threshold = rule.threshold_decimal if rule else Decimal("1000.00")
        score = int(rule.score if rule else 30)
        triggered = transaction.amount >= threshold
        return RuleEvaluation(
            rule_code="HIGH_AMOUNT",
            is_triggered=triggered,
            score_delta=score if triggered else 0,
            message=(
                f"Сумма {transaction.amount} превышает порог {threshold}."
                if triggered
                else f"Сумма ниже порога {threshold}."
            ),
            details={"threshold": str(threshold), "amount": str(transaction.amount)},
            rule=rule,
        )

    def _check_foreign_country(self, transaction: Transaction, rule: FraudRule | None) -> RuleEvaluation:
        allowed_country = "RU"
        score = int(rule.score if rule else 15)
        triggered = transaction.country.upper() != allowed_country
        return RuleEvaluation(
            rule_code="FOREIGN_COUNTRY",
            is_triggered=triggered,
            score_delta=score if triggered else 0,
            message=(
                f"Транзакция из страны {transaction.country}."
                if triggered
                else "Транзакция из домашней страны."
            ),
            details={"country": transaction.country, "home_country": allowed_country},
            rule=rule,
        )

    def _check_velocity(self, transaction: Transaction, rule: FraudRule | None) -> RuleEvaluation:
        score = int(rule.score if rule else 25)
        lookback_minutes = int(rule.threshold_decimal) if rule and rule.threshold_decimal > 0 else 10
        start_time = timezone.now() - timedelta(minutes=lookback_minutes)

        recent_count = (
            Transaction.objects.filter(
                card_number=transaction.card_number,
                created_at__gte=start_time,
            )
            .exclude(pk=transaction.pk)
            .aggregate(total=Count("id"))["total"]
            or 0
        )
        triggered = recent_count >= 3

        return RuleEvaluation(
            rule_code="VELOCITY",
            is_triggered=triggered,
            score_delta=score if triggered else 0,
            message=(
                f"Обнаружено {recent_count} недавних операций по карте."
                if triggered
                else "Подозрительной частоты операций не обнаружено."
            ),
            details={"recent_transactions": recent_count, "window_minutes": lookback_minutes},
            rule=rule,
        )

    def _check_disposable_email(self, transaction: Transaction, rule: FraudRule | None) -> RuleEvaluation:
        score = int(rule.score if rule else 20)
        blocked_domains = {
            "mailinator.com",
            "tempmail.com",
            "10minutemail.com",
            "guerrillamail.com",
        }
        domain = transaction.email.split("@")[-1].lower()
        triggered = domain in blocked_domains

        return RuleEvaluation(
            rule_code="DISPOSABLE_EMAIL",
            is_triggered=triggered,
            score_delta=score if triggered else 0,
            message=(
                f"Обнаружен временный email-домен {domain}."
                if triggered
                else "Email-домен не входит в список временных."
            ),
            details={"domain": domain},
            rule=rule,
        )

    def _get_decision(self, transaction: Transaction, total_risk: int) -> tuple[str, str]:
        """Возвращает итоговое решение по суммарному риску."""

        if total_risk >= self.DEFAULT_DECLINE_THRESHOLD:
            return TransactionStatus.DECLINED, "Высокий риск — операция отклонена"

        if total_risk >= self.DEFAULT_MANUAL_REVIEW_THRESHOLD:
            if transaction.status == TransactionStatus.APPROVED:
                return TransactionStatus.APPROVED, "Подтверждено клиентом"
            return TransactionStatus.MANUAL_REVIEW, "Требуется подтверждение клиента"

        return TransactionStatus.APPROVED, "Риск в допустимых пределах"

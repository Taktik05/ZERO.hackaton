"""DRF-представления для anti-fraud API."""
from __future__ import annotations

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from antifraud.api.serializers import (
    TransactionConfirmSerializer,
    TransactionCreateSerializer,
    TransactionSerializer,
)
from antifraud.models import Transaction


class TransactionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD-операции для транзакций и endpoint подтверждения."""

    queryset = Transaction.objects.prefetch_related("rule_results").order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return TransactionCreateSerializer
        if self.action == "confirm":
            return TransactionConfirmSerializer
        return TransactionSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Создаёт транзакцию, запускает RuleEngine и возвращает результат оценки."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()
        response_serializer = TransactionSerializer(transaction, context={"request": request})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request: Request, pk: int | None = None) -> Response:
        """Подтверждает транзакцию клиентом и возвращает обновлённые данные."""

        transaction = self.get_object()
        serializer = self.get_serializer(
            data=request.data or {"confirmation": True},
            context={"transaction": transaction},
        )
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()
        response_serializer = TransactionSerializer(transaction, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

"""Формы anti-fraud приложения."""
from __future__ import annotations

import re

from django import forms

from antifraud.models import Transaction


class TransactionCreateForm(forms.ModelForm):
    """Форма создания транзакции для проверки антифрод-правилами."""

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
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "currency": forms.TextInput(attrs={"maxlength": 3}),
            "country": forms.TextInput(attrs={"maxlength": 2}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css_classes} form-control".strip()

    def clean_card_number(self) -> str:
        """Нормализует и проверяет номер карты."""

        card_number = re.sub(r"\s+", "", self.cleaned_data["card_number"])
        if not card_number.isdigit() or len(card_number) < 13 or len(card_number) > 19:
            raise forms.ValidationError("Введите корректный номер банковской карты.")
        return card_number

    def clean_currency(self) -> str:
        """Приводит код валюты к ISO-формату."""

        return self.cleaned_data["currency"].upper()

    def clean_country(self) -> str:
        """Приводит код страны к ISO-формату."""

        return self.cleaned_data["country"].upper()

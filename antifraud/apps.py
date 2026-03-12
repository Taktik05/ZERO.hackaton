"""Конфигурация приложения antifraud."""
from django.apps import AppConfig


class AntifraudConfig(AppConfig):
    """Конфигурация anti-fraud приложения."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "antifraud"
    verbose_name = "AntiFraud"

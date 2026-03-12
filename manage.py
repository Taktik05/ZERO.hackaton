#!/usr/bin/env python
"""Командная утилита Django."""
import os
import sys


def main() -> None:
    """Запуск административных команд Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zero.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не удалось импортировать Django. Убедитесь, что зависимости установлены."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

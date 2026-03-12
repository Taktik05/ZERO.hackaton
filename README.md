Zero – Антифрод система на правилах
Продукт для хакатона CodeGryphon. Zero анализирует транзакции по поведенческим правилам и уведомляет пользователя о подозрительных операциях.

🚀 Быстрый старт
1. Клонировать репозиторий
git clone https://github.com/Taktik05/ZERO.hackaton.git
cd ZERO.hackaton
3. Создать и активировать виртуальное окружение
python -m venv venv
venv\Scripts\activate
4. Установить зависимости
pip install -r requirements.txt
5. Создать миграции
python manage.py makemigrations antifraud
6. Применить миграции
python manage.py migrate
7. Загрузить тестовые данные
python manage.py loaddata antifraud/fixtures/initial_data.json
8. Создать суперпользователя (для админки)
python manage.py createsuperuser
9. Запустить сервер
python manage.py runserver
10. Открыть в браузере
- Вход: http://127.0.0.1:8000/
- Админка: http://127.0.0.1:8000/admin/

📡 API endpoints
- `POST /api/ingest/` – принять транзакцию от банка
- `GET /api/alerts/?user_id=1` – получить уведомления пользователя
- `POST /api/alerts/<id>/confirm/` – подтвердить личность

🧠 Правила антифрода
Реализовано 8 эвристических правил (см. `*services/rule_engine.py`):
- Ночные траты
- Телепортация (невозможное перемещение)
- Необычная география
- Скачок суммы
- Необычная категория
- Шквал транзакций
- Новое устройство
- Кофейный лимит

🛠 Технологии
- Django + DRF
- Bootstrap 5
- SQLite (для разработки)

#!/bin/bash
# Скрипт первоначальной настройки бэкенда
# Запускать из папки /backend

set -e
echo "=== Авто-помощник: настройка бэкенда ==="

# 1. Виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 2. Зависимости
pip install -r requirements.txt

# 3. .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✅ Создан .env — заполните его перед запуском!"
fi

# 4. Миграции
python manage.py makemigrations
python manage.py migrate

# 5. Суперпользователь
echo "Создать суперпользователя для Django Admin? (y/n)"
read -r answer
if [ "$answer" = "y" ]; then
  python manage.py createsuperuser
fi

# 6. Статика
python manage.py collectstatic --noinput

echo ""
echo "=== Готово! ==="
echo "Запуск для разработки:  python manage.py runserver"
echo "Запуск для продакшна:   gunicorn config.wsgi:application --bind 0.0.0.0:8000"
echo "Django Admin:           http://localhost:8000/admin/"
echo ""
echo "Эндпоинты API:"
echo "  POST /api/auth/register/"
echo "  POST /api/auth/login/"
echo "  GET  /api/services/"
echo "  GET  /api/organizations/"

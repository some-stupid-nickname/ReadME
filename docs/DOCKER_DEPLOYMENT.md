# Docker Setup для RAG-системы рекомендации книг

Этот каталог содержит Docker-конфигурацию для запуска всей системы в контейнерах.

## Структура

```
docker/
├── Dockerfile.backend          # FastAPI backend
├── Dockerfile.telegram-bot      # Telegram bot
├── Dockerfile.frontend          # (Опционально) Web frontend
├── docker-compose.yml          # Основная конфигурация
├── .env.example                # Пример переменных окружения
└── scripts/                    # Скрипты управления
    ├── build.sh
    ├── start.sh
    ├── stop.sh
    ├── logs.sh
    └── clean.sh
```

## Быстрый старт

### 1. Подготовка

```bash
# В корне проекта
cp env.example .env
# Отредактируйте .env: укажите MISTRAL_API_KEY, TELEGRAM_BOT_TOKEN и настройки PostgreSQL
```

### 2. Запуск

```bash
# Сборка и запуск (из корня проекта)
docker-compose up -d --build
```

### 3. Проверка

- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Web Frontend: http://localhost:80 (или порт из `FRONTEND_PORT`)
- Telegram Bot: начните диалог с ботом в Telegram

**Запущенные сервисы:**
- PostgreSQL (порт 5432) — база данных пользователей
- FastAPI Backend (порт 8000) — API сервер
- React Frontend (порт 80) — веб-интерфейс
- Telegram Bot — Telegram бот

## Особенности текущей конфигурации

1.  **Frontend**: React веб-интерфейс (`frontend-web/`) включен в `docker-compose.yml` и доступен на порту 80 (или значении `FRONTEND_PORT`). Также доступны Telegram бот и CLI консоль (`frontend/console_interface.py`).
2.  **База данных книг**: Файл `data/storage.sqlite` пробрасывается в контейнер backend как read-only volume для векторного поиска.
3.  **PostgreSQL**: Используется для хранения пользовательских данных, аутентификации, библиотек пользователей, отзывов и рейтингов, а также для персонализации поиска.

## Переменные окружения (.env)

- `MISTRAL_API_KEY` - **Обязательно**.
- `TELEGRAM_BOT_TOKEN` - Токен вашего бота.
- `BOOKS_DB_PATH` - Путь внутри контейнера (по умолчанию `/app/data/storage.sqlite`).
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` - Настройки для PostgreSQL.

## Troubleshooting

Если backend не видит базу книг:
1. Проверьте, что в корне проекта есть `data/storage.sqlite`.
2. Проверьте логи: `docker-compose logs backend`.
3. Убедитесь, что путь в `docker-compose.yml` в секции `volumes` для backend соответствует реальности.

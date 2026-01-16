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
cd docker
cp .env.example .env
# Отредактируйте .env: укажите MISTRAL_API_KEY и TELEGRAM_BOT_TOKEN
```

### 2. Запуск

```bash
# Сборка и запуск
docker-compose up -d --build
```

### 3. Проверка

- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Telegram Bot: начните диалог с ботом в Telegram

## Особенности текущей конфигурации

1.  **Frontend**: В репозитории есть `Dockerfile.frontend`, однако в `docker-compose.yml` сервис frontend отсутствует. В данный момент основным интерфейсом являются Telegram бот и CLI консоль (`frontend/console_interface.py`).
2.  **База данных книг**: Файл `data/storage.sqlite` пробрасывается в контейнер backend как read-only volume.
3.  **История (PostgreSQL)**: Контейнер PostgreSQL запускается для будущего использования (история чатов), но в текущей реализации backend (версия 1.0.0) история в БД не сохраняется.

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

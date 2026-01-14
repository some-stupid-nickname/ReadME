# Docker Setup для RAG-системы рекомендации книг

Этот каталог содержит Docker-конфигурацию для запуска всей системы в контейнерах.

## Структура

```
docker/
├── Dockerfile.backend          # FastAPI backend
├── Dockerfile.telegram-bot      # Telegram bot
├── docker-compose.yml          # Production конфигурация
├── docker-compose.dev.yml      # Development конфигурация
├── .env.example                # Пример переменных окружения
├── .dockerignore               # Исключения для сборки
└── scripts/                    # Скрипты управления
    ├── build.sh                # Сборка образов
    ├── start.sh                # Запуск контейнеров
    ├── stop.sh                 # Остановка контейнеров
    ├── logs.sh                 # Просмотр логов
    └── clean.sh                # Очистка ресурсов
```

## Быстрый старт

### 1. Подготовка

```bash
# Перейти в директорию docker
cd docker

# Создать .env файл из примера
cp .env.example .env

# Отредактировать .env и указать свои значения
# Особенно важно: MISTRAL_API_KEY
```

### 2. Сборка образов

```bash
# Собрать все Docker образы
./scripts/build.sh

# Или вручную через docker-compose
docker-compose build
```

### 3. Запуск

```bash
# Запустить все контейнеры
./scripts/start.sh

# Или вручную
docker-compose up -d
```

### 4. Проверка

- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Telegram Bot: начните диалог с ботом в Telegram

## Скрипты управления

### build.sh - Сборка образов

Собирает все Docker образы для проекта.

```bash
./scripts/build.sh
```

### start.sh - Запуск контейнеров

Запускает все контейнеры в фоновом режиме.

```bash
./scripts/start.sh
```

### stop.sh - Остановка контейнеров

Останавливает контейнеры.

```bash
# Остановить без удаления
./scripts/stop.sh

# Остановить и удалить контейнеры
./scripts/stop.sh --remove
```

### logs.sh - Просмотр логов

Просмотр логов контейнеров.

```bash
# Логи всех сервисов
./scripts/logs.sh

# Логи конкретного сервиса
./scripts/logs.sh backend
./scripts/logs.sh -s backend

# Следить за логами (follow)
./scripts/logs.sh -f
./scripts/logs.sh backend -f

# Последние N строк
./scripts/logs.sh --tail 50
```

### clean.sh - Очистка

Очистка контейнеров, образов и volumes.

```bash
# Базовая очистка (контейнеры)
./scripts/clean.sh

# С удалением volumes
./scripts/clean.sh --volumes

# С удалением образов
./scripts/clean.sh --images

# Полная очистка
./scripts/clean.sh --all
```

## Development режим

Для разработки с hot-reload используйте:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Это обеспечит:
- Автоматическую перезагрузку backend при изменении кода
- Монтирование исходного кода в контейнеры
- Дополнительные порты для отладки

**Примечание:** Frontend сервис удалён из конфигурации, так как используется только CLI интерфейс и Telegram бот.

## Переменные окружения

Основные переменные в `.env`:

- `MISTRAL_API_KEY` - **Обязательно** - ключ API Mistral
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` - настройки PostgreSQL
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота (если используется)
- `BOOKS_DB_PATH` - путь к storage.sqlite в контейнере (по умолчанию: `/app/data/storage.sqlite`)

Полный список см. в `.env.example`.

## Volumes

Система использует следующие volumes:

- `postgres_data` - данные PostgreSQL (персистентные)
- `books_data` - данные для storage.sqlite

**Важно:** Убедитесь, что файл `storage.sqlite` существует в `data/` директории или укажите правильный путь в `BOOKS_DB_PATH`.

## Сети

Все сервисы находятся в одной сети `rag-network` и могут обращаться друг к другу по именам сервисов:

- `backend` - FastAPI приложение
- `postgres` - PostgreSQL база данных
- `telegram-bot` - Telegram бот

## Healthchecks

Все сервисы имеют healthchecks:

- **Backend**: `GET /api/health`
- **PostgreSQL**: `pg_isready`
- **Telegram Bot**: проверка процесса

## Troubleshooting

### Проблемы с запуском

1. Проверьте, что Docker и Docker Compose установлены:
   ```bash
   docker --version
   docker-compose --version
   ```

2. Проверьте `.env` файл:
   ```bash
   cat .env
   ```

3. Просмотрите логи:
   ```bash
   ./scripts/logs.sh
   ```

### Проблемы с базой данных

Если PostgreSQL не запускается:

1. Проверьте логи:
   ```bash
   ./scripts/logs.sh postgres
   ```

2. Убедитесь, что порт 5432 свободен:
   ```bash
   netstat -an | grep 5432
   ```

3. Измените порт в `.env`:
   ```
   POSTGRES_PORT=5433
   ```

### Проблемы с storage.sqlite

Если backend не может найти storage.sqlite:

1. Убедитесь, что файл существует в `data/storage.sqlite`
2. Или укажите полный путь в `BOOKS_DB_PATH` в `.env`
3. Проверьте volume mount в `docker-compose.yml`
4. Проверьте качество данных: `python tests/check_book_data_quality.py --db-path data/storage.sqlite`

## Production deployment

Для production:

1. Используйте `docker-compose.yml` (без dev override)
2. Настройте reverse proxy (nginx/traefik) для frontend и backend
3. Используйте секреты для sensitive данных (не храните в .env)
4. Настройте мониторинг и логирование
5. Используйте managed PostgreSQL вместо контейнера (для production)

## Дополнительная информация

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Backend API Documentation](API_SPECS.md)

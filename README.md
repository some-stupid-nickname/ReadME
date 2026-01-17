# RAG-система для рекомендации книг

Система на базе Retrieval-Augmented Generation для поиска и рекомендации книг с кратким обзором сюжета.

## Структура проекта

```
backend/          # FastAPI + LangChain RAG pipeline
frontend/         # CLI консольный интерфейс
frontend-web/     # React + TypeScript веб-интерфейс
telegram-bot/     # Telegram бот
data/
  ├── raw/        # Исходные датасеты
  ├── processed/  # Очищенные данные
  └── storage.sqlite  # SQLite база данных с векторами книг
tests/            # Валидационный датасет и тесты
docs/             # Документация
docker/           # Docker конфигурация для контейнеризации
docker-compose.yml # Docker Compose для запуска всех сервисов
```

## Технологический стек

**Backend:**
- FastAPI с использованием фреймворка LangChain для построения RAG-пайплайна
- PostgreSQL для хранения пользовательских данных, библиотек, отзывов и персонализации
- SQLite с встроенным векторным поиском для хранения эмбеддингов книг
- Mistral API для генерации ответов
- sentence-transformers (модель all-MiniLM-L6-v2) для генерации эмбеддингов

**Frontend:**
- React 18 + TypeScript + Vite для веб-интерфейса
- TailwindCSS для стилизации
- CLI консольный интерфейс (Python)

**Интеграции:**
- Telegram-бот (python-telegram-bot)

## Данные

В основе системы лежит датасет из **174,467 книг**, собранный из четырех источников на Kaggle: Google Books Dataset, Books Dataset, GoodReads 100k books и CMU Books Summary Dataset. Все данные были объединены, очищены и приведены к единой структуре. Для каждой книги хранится название, автор, дата публикации, описание и количество страниц (где доступно).

Пропущенные значения были восстановлены с помощью Google Books API. Итоговый датасет сохранен в файле `data/processed/book_data_prepared.xlsx`.
На основе этих данных построена векторная база SQLite (`data/storage.sqlite`), содержащая эмбеддинги книг для быстрого семантического поиска.

**Ссылки на данные:**
- [Итоговый датасет и сырые данные](https://drive.google.com/drive/folders/17La2w8ZsIB5Vu0nA3CGZgYhP7fqEM1hH) (Google Drive)
- Подробности о структуре данных: `docs/Отчет_Чекпоинт 1.md`
- Скрипт обработки: `data/scripts/data_preparation.ipynb`
- Скрипт создания БД: `data/scripts/build_sqlite_db.py`

## Документация

Полная техническая документация доступна в папке `docs/`:
- [API Reference](docs/API_SPECS.md) — спецификация всех эндпоинтов backend API
- [Настройка Backend](docs/BACKEND_SETUP.md) — инструкции по настройке и запуску backend
- [Docker Deployment](docs/DOCKER_DEPLOYMENT.md) — инструкции по запуску через Docker
- [LLM Query Enrichment](docs/LLM_ENRICHMENT_FEATURE.md) — фича: уточняющие вопросы для неточных запросов
- [Отчет по данным](docs/Отчет_Чекпоинт 1.md) — детали процесса сбора и подготовки датасета
- [Настройка векторной БД](docs/VECTOR_DB_SETUP.md) — детали реализации SQLite Vector Search

**Дополнительно:**
- [Frontend Web README](frontend-web/README.md) — документация по веб-интерфейсу


## Быстрый старт

### Вариант 1: Запуск через Docker (рекомендуется)

```bash
# 1. Клонируйте репозиторий
git clone <url>
cd ReadME

# 2. Настройте переменные окружения
cd docker
cp .env.example .env
# Отредактируйте .env и укажите:
# - MISTRAL_API_KEY (обязательно)
# - TELEGRAM_BOT_TOKEN (если используете бота)
# - POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB (для PostgreSQL)

# 3. Запустите все сервисы
docker-compose up -d

# 4. Проверьте работу
# Backend API: http://localhost:8000/docs
# Web Frontend: http://localhost:80 (или порт из FRONTEND_PORT)
# Telegram бот: начните диалог с ботом в Telegram
```

**Запущенные сервисы:**
- PostgreSQL (порт 5432) — база данных пользователей
- FastAPI Backend (порт 8000) — API сервер
- React Frontend (порт 80) — веб-интерфейс
- Telegram Bot — Telegram бот

Подробнее: [Docker Deployment](docs/DOCKER_DEPLOYMENT.md)

### Вариант 2: Локальный запуск

```bash
# 1. Установите зависимости
pip install -r requirements.txt
pip install -r backend/requirements.txt

# 2. Настройте PostgreSQL
# Убедитесь, что PostgreSQL запущен и создана база данных
# Или используйте Docker только для PostgreSQL:
# docker-compose up -d postgres

# 3. Настройте переменные окружения
# Создайте .env в корне проекта:
# MISTRAL_API_KEY=your_key_here
# BOOKS_DB_PATH=data/storage.sqlite
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_USER=rag_user
# POSTGRES_PASSWORD=rag_password
# POSTGRES_DB=rag_db

# 4. Запустите backend
cd backend
python -m api.main

# 5. В другом терминале запустите веб-интерфейс (опционально)
cd frontend-web
npm install
npm run dev
# Доступен на http://localhost:5173

# 6. Или запустите Telegram бот (опционально)
cd telegram-bot
python bot.py

# 7. Или используйте CLI интерфейс
cd frontend
python console_interface.py
```

### Проверка базы данных

Перед запуском убедитесь, что база данных существует:

```bash
# Проверка качества данных
python tests/check_book_data_quality.py --db-path data/storage.sqlite
```

## Разработка

Проект использует Git Flow с feature-ветками для отдельных задач:

```bash
git checkout -b feature/название-задачи
# ... работаете над задачей ...
git add .
git commit -m "Описание изменений"
git push origin feature/название-задачи
```

**Kanban-доска проекта:** https://ru.yougile.com/board/fuzv88umzyoe

## Архитектура системы

### Схема взаимодействия модулей

```
┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐
│  Web Frontend   │  │ CLI Interface│  │  Telegram Bot    │
│  (React + TS)   │  │  (Console)   │  │   (python-tg)    │
└────────┬────────┘  └──────┬───────┘  └────────┬─────────┘
         │                   │                   │
         └───────────┬───────┴───────────────────┘
                     │ HTTP/REST
              ┌──────▼──────────────────────┐
              │      FastAPI Backend        │
              │                             │
              │  ┌───────────────────────┐  │
              │  │   LangChain Pipeline  │  │
              │  │                       │  │
              │  │ • Query Enrichment    │  │
              │  │ • Embedder            │  │
              │  │ • Retriever           │  │
              │  │ • Response Generator  │  │
              │  │ • Personalization     │  │
              │  └───────────────────────┘  │
              └──────┬──────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼────┐ ┌───▼────┐ ┌───▼─────┐
    │  LLM    │ │Postgres│ │ SQLite  │
    │ Mistral │ │   DB   │ │ Vector  │
    │   API   │ │(Users, │ │   DB    │
    │         │ │Library)│ │(Books)  │
    └─────────┘ └────────┘ └─────────┘
```

### LangChain Pipeline (внутри Backend)

```
User Query → FastAPI Endpoint
                ↓
     ┌──────────────────────┐
     │   LangChain Chain    │
     │                      │
     │  1. Query Enrichment │ → LLM Mistral (Optional)
     │     ↓                │
     │  2. Embedder         │ → sentence-transformers
     │     ↓                │
     │  3. Retriever        │ → SQLite vector search
     │     ↓                │
     │  4. Response Gen     │ → LLM Mistral
     │     ↓                │
     └──────────────────────┘
                ↓
         Return Response
```

### Поток обработки запроса
```
1. Пользователь вводит запрос (через Web/CLI/Bot)
   ↓
2. Клиент → Backend API (POST /api/search или /api/search/personalized)
   ↓
3. (Optional) Аутентификация (для персонализированного поиска)
   ↓
4. (Optional) Query Enrichment (API анализирует запрос)
   "хочу про космос" → Clarification Questions
   ↓
5. Генерация эмбеддинга запроса
   ↓
6. Векторный поиск в SQLite (top_k книг)
   ↓
7. (Optional) Персонализация результатов на основе:
   - Предпочтений пользователя из PostgreSQL
   - Истории поиска
   - Библиотеки пользователя
   ↓
8. LLM генерирует финальный ответ с обзорами книг
   ↓
9. Возврат ответа клиенту
```

**Особенности:**
- Для анонимных пользователей доступен базовый поиск
- Для авторизованных пользователей доступен персонализированный поиск на основе их предпочтений
- Найденные книги передаются в LLM вместе с исходным запросом пользователя, и модель генерирует финальный ответ с обзорами и рекомендациями

## Команда

- Дима: Frontend + Telegram Bot + Tech Lead
- Катя: Backend + RAG
- Ксюша, Никита: Data + RAG

## Требования к коду

- Стандарт: PEP8 (Python)
- Тестирование: обязательно для RAG pipeline
- Метрики: relevance, precision@k на валидационной выборке

## Тестирование и оценка качества

### Векторная база данных
- **103,063 книги** загружены в SQLite
- Модель эмбеддингов: `all-MiniLM-L6-v2` (384 измерения)
- Хранилище: `data/storage.sqlite`
- Метрика поиска: косинусное сходство
- Формат: SQLite с сериализованными векторами через pickle

### База данных пользователей
- PostgreSQL для хранения:
  - Пользователей и аутентификации
  - Библиотек пользователей
  - Отзывов и рейтингов
  - Предпочтений для персонализации
  - Онбординга (выбранные книги при регистрации)

### RAG Evaluation (LLM-as-Judge)
Для автоматической оценки качества рекомендаций используем подход LLM-as-Judge:

**Методология:**
- 20 тестовых запросов по разным жанрам
- Топ-5 рекомендаций на запрос (100 оценок всего)
- Оценка релевантности по шкале 0-5
- Поддержка двух провайдеров: Mistral (бесплатный) и OpenAI (платный)
- Метрики: средняя релевантность, топ-1 качество, успешность API-вызовов

**Запуск тестов:**
```bash
cd tests
# Mistral (с защитой от rate limits)
python evaluate_rag.py --queries-file test_queries.json --provider mistral --top-k 5 --output results.json

# OpenAI (быстрее, платный)
python evaluate_rag.py --queries-file test_queries.json --provider openai --top-k 5 --output results.json

# RAGAS метрики (требует дополнительных зависимостей)
pip install -r requirements_ragas.txt
python evaluate_rag_ragas.py --queries-file test_queries.json --top-k 5
```

### Основные API эндпоинты

**Поиск:**
- `POST /api/search` — базовый поиск (анонимный)
- `POST /api/search/personalized` — персонализированный поиск (требует аутентификации)
- `POST /api/search/clarify` — анализ запроса и уточняющие вопросы
- `POST /api/search/enriched` — поиск с обогащенным контекстом

**Аутентификация:**
- `POST /api/auth/register` — регистрация пользователя
- `POST /api/auth/login` — вход в систему

**Библиотека:**
- `GET /api/library` — получить библиотеку пользователя
- `POST /api/library` — добавить книгу в библиотеку
- `DELETE /api/library/{book_id}` — удалить книгу из библиотеки

**Отзывы:**
- `POST /api/reviews` — создать/обновить отзыв
- `GET /api/reviews/{book_id}` — получить отзыв пользователя на книгу

**Онбординг:**
- `GET /api/onboarding/books` — получить список книг для онбординга
- `POST /api/onboarding/complete` — завершить онбординг

**Книги:**
- `GET /api/books/{book_id}` — получить информацию о книге

**Администрирование:**
- `GET /api/admin/metrics` — метрики системы (требует API ключ)

Полная документация: [API Reference](docs/API_SPECS.md)

## Контакты

По всем вопросам: https://t.me/dimitriymir

# RAG-система для рекомендации книг

Система на базе Retrieval-Augmented Generation для поиска и рекомендации книг с кратким обзором сюжета.

## Структура проекта

```
backend/          # FastAPI + LangChain RAG pipeline (см. backend/README.md)
frontend/         # CLI консольный интерфейс
telegram-bot/     # Telegram бот
data/
  ├── raw/        # Исходные датасеты
  ├── processed/  # Очищенные данные
  └── storage.sqlite  # SQLite база данных с векторами книг
tests/            # Валидационный датасет и тесты
docs/             # Документация
docker/           # Docker конфигурация для контейнеризации
```

## Технологический стек

Наш проект построен на современном стеке технологий для работы с большими языковыми моделями и векторным поиском.
Backend реализован на FastAPI с использованием фреймворка LangChain для построения RAG-пайплайна.
В качестве векторной базы данных используется SQLite с встроенным векторным поиском, который хранит эмбеддинги всех книг из датасета.
Для генерации ответов задействован Mistral API.

Эмбеддинги текстов генерируются через библиотеку sentence-transformers (модель all-MiniLM-L6-v2).
Система предоставляет два интерфейса: CLI консольный интерфейс и Telegram-бот (python-telegram-bot).

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
- [Примеры использования Telegram бота](docs/TELEGRAM_BOT_EXAMPLES.md) — примеры команд и запросов
- [Docker Deployment](docs/DOCKER_DEPLOYMENT.md) — инструкции по запуску через Docker
- [LLM Query Enrichment](docs/LLM_ENRICHMENT_FEATURE.md) — фича: уточняющие вопросы для неточных запросов
- [Отчет по данным](docs/Отчет_Чекпоинт 1.md) — детали процесса сбора и подготовки датасета
- [Настройка векторной БД](docs/VECTOR_DB_SETUP.md) — детали реализации SQLite Vector Search


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
# - BOOKS_DB_PATH (путь к data/storage.sqlite)

# 3. Запустите все сервисы
docker-compose up -d

# 4. Проверьте работу
# Backend API: http://localhost:8000/docs
# Telegram бот: начните диалог с ботом в Telegram
```

Подробнее: [Docker Setup](docker/README.md)

### Вариант 2: Локальный запуск

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Настройте переменные окружения
# Создайте .env в корне проекта:
# MISTRAL_API_KEY=your_key_here
# BOOKS_DB_PATH=data/storage.sqlite

# 3. Запустите backend
cd backend
python -m api.main

# 4. В другом терминале запустите Telegram бот (опционально)
cd telegram-bot
python bot.py

# 5. Или используйте CLI интерфейс
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
┌─────────────────┐         ┌──────────────────┐
│   CLI Interface │         │  Telegram Bot    │
│   (Console)     │         │   (python-tg)    │
└────────┬────────┘         └────────┬─────────┘
         │                           │
         └───────────┬───────────────┘
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
              │  └───────────────────────┘  │
              └──────┬──────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼────┐ ┌───▼────┐ ┌───▼─────┐
    │  LLM    │ │Postgres│ │ SQLite  │
    │ Mistral │ │ SQL    │ │ Vector  │
    │   API   │ │        │ │   DB    │
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
1. Пользователь вводит запрос
   ↓
2. CLI/Bot → Backend API (POST /api/search)
   ↓
3. (Optional) Query Enrichment (API анализирует запрос)
   "хочу про космос" → Clarification Questions
   ↓
4. Генерация эмбеддинга запроса
   ↓
5. Векторный поиск в SQLite (top_k книг)
   ↓
6. LLM генерирует финальный ответ с обзорами книг
   ↓
7. Возврат ответа пользователю
```

Найденные книги передаются в LLM вместе с исходным запросом пользователя, и модель генерирует финальный ответ с обзорами и рекомендациями. Ответ возвращается клиенту (CLI или Telegram боту).

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
```

## Контакты

По всем вопросам: https://t.me/dimitriymir

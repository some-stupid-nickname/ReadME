# Backend - RAG System Setup

This directory contains the backend components for the RAG-based book recommendation system.

## Database Setup

### Prerequisites

1. Python 3.10+
2. Virtual environment
3. SQLite database file: `data/storage.sqlite`

### Installation

Install required packages:

```bash
# Из корня проекта
pip install -r requirements.txt
```

### Database Structure

Система использует SQLite базу данных с векторным поиском:

- **Файл:** `data/storage.sqlite`
- **Количество книг:** 103,063
- **Размерность векторов:** 384 (модель all-MiniLM-L6-v2)

### Проверка базы данных

Перед запуском проверьте качество данных:

```bash
# Из корня проекта
python tests/check_book_data_quality.py --db-path data/storage.sqlite
```

### Configuration

Создайте файл `.env` в корне проекта или в папке `backend/`:

```env
# Обязательно
MISTRAL_API_KEY=your_mistral_api_key_here

# Опционально (пути по умолчанию)
BOOKS_DB_PATH=data/storage.sqlite
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=rag_password
POSTGRES_DB=rag_db
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### RAG System Evaluation

Скрипты оценки находятся в папке `tests/`:

```bash
# Оценка качества (LLM-as-Judge)
cd tests
python evaluate_rag.py --queries-file test_queries.json --provider mistral

# Оценка с RAGAS
python evaluate_rag_ragas.py \
  --queries-file test_queries_small.json \
  --db-path ../data/storage.sqlite \
  --top-k 5 \
  --output evaluation_results.json
```

**Метрики:**
- **Relevance** (evaluate_rag.py) - оценка релевантности через LLM.
- **Faithfulness** (RAGAS) - верность ответа контексту.
- **Answer Relevancy** (RAGAS) - релевантность ответа запросу.

### Запуск Backend API

```bash
# Из директории backend
python -m api.main

# Или через uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API будет доступен по адресу: http://localhost:8000
Документация Swagger: http://localhost:8000/docs

### Troubleshooting

**Проблемы с базой данных:**
- Убедитесь, что файл `data/storage.sqlite` существует.
- Если вы запускаете из `backend/`, проверьте что `BOOKS_DB_PATH` в `.env` указывает правильный относительный путь (например, `../data/storage.sqlite`).
- Запустите проверку: `python tests/check_book_data_quality.py --db-path data/storage.sqlite`.

**Mistral rate limits:**
- На бесплатном тарифе Mistral есть лимиты (около 1 запроса в секунду).
- Скрипты оценки в `tests/` имеют встроенные задержки (`time.sleep`).

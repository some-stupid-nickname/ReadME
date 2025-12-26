# Backend - RAG System Setup

This directory contains the backend components for the RAG-based book recommendation system.

## Database Setup

### Prerequisites

1. Python 3.10+
2. Virtual environment (already configured in project root)
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
- **Структура:** Таблица `points` с сериализованными векторами через pickle
- **Количество книг:** 103,063
- **Размерность векторов:** 384 (модель all-MiniLM-L6-v2)

### Проверка базы данных

Перед запуском проверьте качество данных:

```bash
# Из корня проекта
python tests/check_book_data_quality.py --db-path data/storage.sqlite
```

Это покажет:
- Количество книг с описаниями
- Статистику по категориям
- Примеры книг без описаний

### Configuration

Создайте файл `.env` в корне проекта:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
BOOKS_DB_PATH=data/storage.sqlite
```

### Embedding Model

Система использует `all-MiniLM-L6-v2`:
- Быстрая и эффективная
- 384-мерные эмбеддинги
- Хороший баланс между скоростью и качеством

### RAG System Evaluation

Система использует RAGAS для оценки качества рекомендаций:

```bash
# Оценка с Mistral
cd backend
python evaluate_rag_ragas.py \
  --queries-file ../tests/test_queries_small.json \
  --db-path ../data/storage.sqlite \
  --top-k 5 \
  --output evaluation_results.json \
  --context-lang ru
```

**Метрики RAGAS:**
- **Faithfulness** - верность ответа контексту (0-1)
- **Answer Relevancy** - релевантность ответа запросу (0-1)

**Тестовые запросы:**
- `tests/test_queries.json` - 20 разнообразных запросов
- `tests/test_queries_small.json` - 5 запросов для быстрого тестирования

**Параметры:**
- `--context-lang` - язык контекста (`ru` или `en`)
- `--use-description-only` - использовать только описания (старое поведение)
- `--db-path` - путь к SQLite базе данных

### Запуск Backend API

```bash
# Из директории backend
python -m api.main

# Или через uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API будет доступен по адресу: http://localhost:8000
Документация: http://localhost:8000/docs

### Troubleshooting

**Проблемы с базой данных:**
- Убедитесь, что файл `data/storage.sqlite` существует
- Проверьте путь в `BOOKS_DB_PATH` в `.env`
- Запустите проверку качества данных: `python tests/check_book_data_quality.py`

**Проблемы с памятью:**
- SQLite загружает все векторы в память при старте
- Для больших баз данных рассмотрите использование Qdrant или другой векторной БД

**Mistral rate limits:**
- Free tier: ~30 запросов перед лимитом
- Скрипты автоматически добавляют задержки
- Неудачные запросы исключаются из метрик

**Ошибки импорта:**
- Убедитесь, что установлены все зависимости: `pip install -r requirements.txt`
- Проверьте, что вы находитесь в правильной директории

# FastAPI Backend - Инструкция по запуску

## Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

## Настройка переменных окружения

Создайте файл `.env` в директории `backend/` или в корне проекта:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
BOOKS_DB_PATH=../frontend/books.sqlite  # опционально, будет найден автоматически
```

## Запуск сервера

### Вариант 1: Через Python модуль (из корня проекта)

```bash
# Из корня проекта
cd backend
python -m api.main
```

### Вариант 2: Через uvicorn напрямую

```bash
# Из корня проекта
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Вариант 3: Из корня проекта с PYTHONPATH

```bash
# Из корня проекта
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
cd backend
python api/main.py
```

## Проверка работы

После запуска сервера:

1. Откройте документацию API: http://localhost:8000/docs
2. Проверьте health endpoint: http://localhost:8000/api/health
3. Протестируйте поиск: POST http://localhost:8000/api/search

## Структура API

- `POST /api/search` - Анонимный поиск книг
- `GET /api/health` - Проверка работоспособности
- `GET /docs` - Интерактивная документация (Swagger UI)
- `GET /redoc` - Альтернативная документация (ReDoc)

## Примечания

- База данных `books.sqlite` автоматически ищется в следующих местах:
  1. Путь из переменной окружения `BOOKS_DB_PATH`
  2. `frontend/books.sqlite`
  3. `backend/books.sqlite`
  4. Корень проекта `books.sqlite`

- RAG компоненты инициализируются один раз при первом запросе (singleton pattern)


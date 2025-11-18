# RAG-система для рекомендации книг

Система на базе Retrieval-Augmented Generation для поиска и рекомендации книг с кратким обзором сюжета.

## Структура проекта
```
backend/          # FastAPI + LangChain RAG pipeline
frontend/         # React веб-интерфейс
telegram-bot/     # Telegram бот
data/            
  ├── raw/        # Исходные датасеты
  ├── processed/  # Очищенные данные
  └── scripts/    # ETL скрипты для обработки данных
tests/            # Валидационный датасет и тесты
docs/             # Документация
```

## Технологический стек

- **Backend:** FastAPI, LangChain, Qdrant
- **LLM:** Mistral API, HuggingFace Inference
- **Frontend:** React
- **Bot:** python-telegram-bot
- **Embeddings:** sentence-transformers

## Документация
- [API Reference](docs/API_SPECS.md)
- [Развертывание](docs/DEPLOYMENT.md) (TODO)

## Как начать работу

### 1. Клонировать репозиторий
```bash
git clone <url>
cd llm-course-project
```

### 2. Создать feature-ветку для своей задачи
```bash
git checkout develop
git pull
git checkout -b feature/название-задачи
```

### 3. Работать в своей ветке
```bash
# Делаете задачу...
git add .
git commit -m "Описание изменений"
git push origin feature/название-задачи
```

### 4. Создать Pull Request
- GitHub → Pull Request
- `feature/название-задачи` → `develop`
- Дождаться review → Merge

### 5. Взять следующую задачу
```bash
git checkout develop
git pull
git checkout -b feature/следующая-задача
```

## Workflow

- `main` - production-ready код (не трогаем до финала)
- `develop` - рабочая ветка (сюда мерджим всё)
- `feature/*` - для каждой задачи с Kanban

## Kanban задачи

См. https://ru.yougile.com/board/fuzv88umzyoe

## Архитектура системы

### Схема взаимодействия модулей

## Архитектура системы

### Схема взаимодействия модулей
```
┌─────────────────┐         ┌──────────────────┐
│   React Web     │         │  Telegram Bot    │
│   (Frontend)    │         │   (python-tg)    │
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
              │  │ • Query Rewriter      │  │
              │  │ • Embedder            │  │
              │  │ • Retriever           │  │
              │  │ • Response Generator  │  │
              │  └───────────────────────┘  │
              └──────┬──────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼────┐ ┌───▼────┐ ┌───▼─────┐
    │  LLM    │ │Postgres│ │ Qdrant  │
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
     │  1. Query Rewriter   │ → LLM Mistral
     │     ↓                │
     │  2. Embedder         │ → sentence-transformers
     │     ↓                │
     │  3. Retriever        │ → Qdrant search
     │     ↓                │
     │  4. Response Gen     │ → LLM Mistral
     └──────────────────────┘
                ↓
         Save to PostgreSQL
                ↓
         Return Response
```

### Поток обработки запроса
```
1. Пользователь вводит запрос
   ↓
2. Frontend/Bot → Backend API (POST /api/search)
   ↓
3. Query Transformation (LLM улучшает запрос)
   "хочу про космос" → "научная фантастика космические путешествия"
   ↓
4. Генерация эмбеддинга улучшенного запроса
   ↓
5. Векторный поиск в Qdrant (top_k книг)
   ↓
6. LLM генерирует финальный ответ с обзорами книг
   ↓
7. Сохранение в PostgreSQL (история чата)
   ↓
8. Возврат ответа пользователю
```


## Команда

- Разработчик 1: Frontend + Tech Lead
- Разработчик 2: Backend + RAG
- Разработчик 3: Data + Telegram Bot

## Требования к коду

- Стандарт: PEP8 (Python)
- Тестирование: обязательно для RAG pipeline
- Метрики: relevance, precision@k на валидационной выборке

## Контакты

https://t.me/dimitriymir

# API Reference

## Base URL
```
Development: http://localhost:8000
```

## Аутентификация

API использует JWT (JSON Web Tokens) для аутентификации. Большинство эндпоинтов доступны анонимно, но для персонализированного поиска и работы с библиотекой требуется аутентификация.

**Формат заголовка:**
```
Authorization: Bearer <token>
```

**Получение токена:**
- `POST /api/auth/register` — регистрация нового пользователя
- `POST /api/auth/login` — вход существующего пользователя

Оба эндпоинта возвращают JWT токен в формате:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": 123
}
```

---

# Endpoints

## 1. Поиск книг

### POST /api/search
Базовый поиск книг (анонимный)

**Auth:** ❌ Не требуется

**Request:**
```json
{
  "query": "хочу что-то про космос"
}
```

**Response:** `200 OK`
```json
{
  "response": "Вот несколько отличных книг про космос:\n\n📚 **\"Автостопом по галактике\"** - Дуглас Адамс\nЮмористическая космическая одиссея...\n\n📚 **\"Марсианин\"** - Энди Вейр\nРеалистичная история выживания астронавта на Марсе...",
  "books": [
    {
      "id": "book_123",
      "title": "Автостопом по галактике",
      "author": "Дуглас Адамс",
      "genres": ["фантастика"],
      "description": "История обычного человека, который отправляется в невероятное путешествие по галактике...",
      "source_link": null
    }
  ],
  "message_id": null
}
```

---

### POST /api/search/clarify
Анализ запроса на полноту и генерация уточняющих вопросов

**Auth:** ❌ Не требуется

**Request:**
```json
{
  "query": "хочу книгу"
}
```

**Response:** `200 OK`
```json
{
  "is_vague": true,
  "clarifying_questions": [
    "Какой жанр вы предпочитаете?",
    "О чем должна быть книга?"
  ],
  "original_query": "хочу книгу"
}
```

---

### POST /api/search/enriched
Поиск с использованием уточненного контекста

**Auth:** ❌ Не требуется

**Request:**
```json
{
  "original_query": "хочу книгу",
  "user_context": "фантастика про путешествия во времени"
}
```

**Response:** `200 OK`
(Формат совпадает с `/api/search`)

---

### POST /api/search/personalized
Персонализированный поиск книг на основе предпочтений пользователя

**Auth:** ✅ Требуется (Authorization: Bearer <token>)

**Request:**
```json
{
  "query": "хочу что-то про космос"
}
```

**Response:** `200 OK`
```json
{
  "response": "Вот несколько отличных книг про космос...",
  "books": [...],
  "personalization_metadata": {
    "query_enhanced": true,
    "preference_match_score": 0.85,
    "library_books_filtered": 2
  }
}
```

**Особенности:**
- Использует предпочтения пользователя из библиотеки и отзывов
- Фильтрует книги, уже находящиеся в библиотеке пользователя
- Улучшает запрос на основе истории чтения

---

## 2. Аутентификация

### POST /api/auth/register
Регистрация нового пользователя

**Auth:** ❌ Не требуется

**Request:**
```json
{
  "username": "user123",
  "password": "password123"
}
```

**Требования:**
- Username: 3-50 символов, только буквы, цифры и подчеркивание
- Password: минимум 6 символов

**Response:** `201 Created`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": 123
}
```

---

### POST /api/auth/login
Вход в систему

**Auth:** ❌ Не требуется

**Request:**
```json
{
  "username": "user123",
  "password": "password123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": 123
}
```

---

### GET /api/auth/me
Получить профиль текущего пользователя

**Auth:** ✅ Требуется

**Response:** `200 OK`
```json
{
  "user_id": 123,
  "username": "user123",
  "onboarding_completed": true,
  "library_count": 15
}
```

---

## 3. Библиотека пользователя

### GET /api/library
Получить все книги из библиотеки пользователя

**Auth:** ✅ Требуется

**Query параметры:**
- `sort` (optional): `recent`, `rating`, `alphabetical` (default: `recent`)
- `rated_only` (optional): `true`/`false` (default: `false`)

**Response:** `200 OK`
```json
[
  {
    "book_id": "book_123",
    "title": "Название книги",
    "author": "Автор",
    "category": "Жанр",
    "cover_url": "https://...",
    "rating": 8,
    "review": "Мой отзыв...",
    "added_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### POST /api/library
Добавить книгу в библиотеку

**Auth:** ✅ Требуется

**Request:**
```json
{
  "book_id": "book_123"
}
```

**Response:** `200 OK`
```json
{
  "message": "Book added to library",
  "book_id": "book_123"
}
```

---

### DELETE /api/library/{book_id}
Удалить книгу из библиотеки

**Auth:** ✅ Требуется

**Response:** `200 OK`
```json
{
  "message": "Book removed from library",
  "book_id": "book_123"
}
```

---

## 4. Отзывы и рейтинги

### POST /api/reviews
Создать или обновить отзыв на книгу

**Auth:** ✅ Требуется

**Request:**
```json
{
  "book_id": "book_123",
  "rating": 8,
  "review": "Отличная книга! Очень понравилось..."
}
```

**Требования:**
- Rating: 1-10 (целое число)
- Review: опционально, текст отзыва

**Response:** `200 OK`
```json
{
  "message": "Review saved",
  "book_id": "book_123",
  "rating": 8
}
```

---

### GET /api/reviews/{book_id}
Получить отзыв пользователя на книгу

**Auth:** ✅ Требуется

**Response:** `200 OK`
```json
{
  "book_id": "book_123",
  "rating": 8,
  "review": "Отличная книга!",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Если отзыва нет:** `404 Not Found`

---

## 5. Онбординг

### GET /api/onboarding/books
Получить список книг для онбординга

**Auth:** ❌ Не требуется (публичный эндпоинт)

**Response:** `200 OK`
```json
[
  {
    "book_id": "book_123",
    "title": "Название",
    "author": "Автор",
    "category": "Classic",
    "cover_url": "https://..."
  }
]
```

Возвращает 16 книг: по 4 в каждой категории (Classic, Fantasy, Thriller, Modern).

---

### POST /api/onboarding/complete
Завершить онбординг (выбрать 3-10 любимых книг)

**Auth:** ✅ Требуется

**Request:**
```json
{
  "selected_book_ids": ["book_1", "book_2", "book_3"]
}
```

**Требования:**
- Минимум 3 книги, максимум 10

**Response:** `200 OK`
```json
{
  "message": "Onboarding completed",
  "selected_count": 3
}
```

---

## 6. Информация о книгах

### GET /api/books/{book_id}
Получить детальную информацию о книге

**Auth:** ⚠️ Опционально (если авторизован, показывает отзыв пользователя)

**Response:** `200 OK`
```json
{
  "book_id": "book_123",
  "title": "Название",
  "author": "Автор",
  "category": "Жанр",
  "description": "Описание книги...",
  "cover_url": "https://...",
  "user_review": {
    "rating": 8,
    "review": "Мой отзыв"
  },
  "in_library": true
}
```

---

## 7. Администрирование

### GET /api/admin/metrics
Получить метрики системы

**Auth:** ✅ Требуется API ключ (X-API-Key header)

**Response:** `200 OK`
```json
{
  "total_users": 150,
  "total_library_books": 1250,
  "total_reviews": 890,
  "average_rating": 7.5,
  "onboarding_completion_rate": 0.85,
  "search_queries_count": 5432
}
```

---

## 8. Служебные endpoints

### GET /api/health
Проверка работоспособности API

**Auth:** ❌ Не требуется

**Response:** `200 OK`
```json
{
  "status": "ok",
  "services": {
    "database": "ok",
    "llm": "ok",
    "qdrant": "ok"
  },
  "version": "2.0.0"
}
```
*Примечание: `qdrant: ok` является плейсхолдером, так как система использует SQLite.*

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | OK - успешный запрос |
| 201 | Created - ресурс создан |
| 400 | Bad Request - невалидные данные |
| 401 | Unauthorized - требуется аутентификация |
| 404 | Not Found - ресурс не найден |
| 500 | Internal Server Error - ошибка сервера |

## Формат ошибок
```json
{
  "detail": "Описание ошибки"
}
```

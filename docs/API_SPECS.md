# API Reference

## Base URL
```
Development: http://localhost:8000
```

## Аутентификация

Защищенные endpoints требуют JWT token в header:
```
Authorization: Bearer <token>
```

---

# Endpoints

## 1. Аутентификация

### POST /api/auth/register
Регистрация нового пользователя

**Auth:** ❌ Не требуется

**Request:**
```json
{
  "username": "ivan_reader",
  "password": "securepass123"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "ivan_reader",
  "created_at": "2024-11-17T10:00:00Z"
}
```

**Errors:**
- `400 Bad Request` - Username уже занят
- `422 Unprocessable Entity` - Невалидный формат (пароль < 8 символов, username < 3 символов)

---

### POST /api/auth/login
Вход в систему

**Auth:** ❌ Не требуется

**Request:**
```json
{
  "username": "ivan_reader",
  "password": "securepass123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "ivan_reader"
  }
}
```

**Errors:**
- `401 Unauthorized` - Неверные credentials

---

### POST /api/auth/logout
Выход из системы (опционально, для фронтенда - удаление token на клиенте)

**Auth:** ✅ Требуется

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

---

### GET /api/auth/me
Получить данные текущего пользователя

**Auth:** ✅ Требуется

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "ivan_reader",
  "created_at": "2024-11-17T10:00:00Z"
}
```

**Errors:**
- `401 Unauthorized` - Невалидный/истекший token

---

## 2. Поиск книг

### POST /api/search
Анонимный поиск книг (БЕЗ сохранения в историю)

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
      "genres": ["фантастика", "юмор"],
      "description": "История обычного человека, который отправляется в невероятное путешествие по галактике...",
      "source_link": "https://example.com/hitchhikers-guide"
    },
    {
      "id": "book_456",
      "title": "Марсианин",
      "author": "Энди Вейр",
      "genres": ["фантастика", "выживание"],
      "description": "Астронавт остается один на Марсе и должен выжить...",
      "source_link": "https://example.com/martian"
    }
  ],
  "message_id": null
}
```

**Errors:**
- `400 Bad Request` - Пустой запрос
- `500 Internal Server Error` - Ошибка LLM/Qdrant

**Примечание:** Анонимные запросы не сохраняются, `message_id` = `null`, нельзя поставить лайк/дизлайк

---

## 3. Чаты (история)

### GET /api/chats
Список всех чатов пользователя

**Auth:** ✅ Требуется

**Query Parameters:**
- `limit` (optional, default=20) - количество чатов
- `offset` (optional, default=0) - смещение для пагинации

**Response:** `200 OK`
```json
{
  "chats": [
    {
      "id": 123,
      "title": "Книги про космос",
      "created_at": "2024-11-17T10:00:00Z",
      "updated_at": "2024-11-17T10:15:00Z",
      "messages_count": 4
    },
    {
      "id": 124,
      "title": "Фэнтези для подростков",
      "created_at": "2024-11-17T11:00:00Z",
      "updated_at": "2024-11-17T11:05:00Z",
      "messages_count": 2
    }
  ],
  "total": 2
}
```

---

### POST /api/chats
Создать новый чат

**Auth:** ✅ Требуется

**Request:**
```json
{
  "title": "Новый чат"  // опционально, автогенерируется из первого сообщения
}
```

**Response:** `201 Created`
```json
{
  "id": 125,
  "title": "Новый чат",
  "created_at": "2024-11-17T12:00:00Z",
  "updated_at": "2024-11-17T12:00:00Z"
}
```

---

### GET /api/chats/{chat_id}
Получить сообщения конкретного чата

**Auth:** ✅ Требуется

**Response:** `200 OK`
```json
{
  "id": 123,
  "title": "Книги про космос",
  "created_at": "2024-11-17T10:00:00Z",
  "updated_at": "2024-11-17T10:15:00Z",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "хочу что-то про космос",
      "created_at": "2024-11-17T10:00:00Z",
      "feedback": null
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Вот несколько отличных книг про космос:\n\n📚 **\"Автостопом по галактике\"**...",
      "books": [
        {
          "id": "book_123",
          "title": "Автостопом по галактике",
          "author": "Дуглас Адамс",
          "genres": ["фантастика", "юмор"],
          "source_link": "https://example.com/hitchhikers-guide"
        }
      ],
      "created_at": "2024-11-17T10:00:05Z",
      "feedback": "like"
    },
    {
      "id": 3,
      "role": "user",
      "content": "а что-то похожее но серьезнее?",
      "created_at": "2024-11-17T10:10:00Z",
      "feedback": null
    },
    {
      "id": 4,
      "role": "assistant",
      "content": "📚 **\"Дюна\"** - Фрэнк Герберт\nЭпическая научная фантастика...",
      "books": [...],
      "created_at": "2024-11-17T10:10:05Z",
      "feedback": null
    }
  ]
}
```

**Errors:**
- `404 Not Found` - Чат не найден или не принадлежит пользователю

---

### DELETE /api/chats/{chat_id}
Удалить чат

**Auth:** ✅ Требуется

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Чат не найден или не принадлежит пользователю

---

### PATCH /api/chats/{chat_id}
Изменить название чата

**Auth:** ✅ Требуется

**Request:**
```json
{
  "title": "Космическая фантастика"
}
```

**Response:** `200 OK`
```json
{
  "id": 123,
  "title": "Космическая фантастика",
  "updated_at": "2024-11-17T12:30:00Z"
}
```

---

## 4. Сообщения в чате

### POST /api/chats/{chat_id}/messages
Отправить сообщение в чат (поиск книг с сохранением в историю)

**Auth:** ✅ Требуется

**Request:**
```json
{
  "query": "хочу что-то про космос"
}
```

**Response:** `201 Created`
```json
{
  "user_message": {
    "id": 5,
    "role": "user",
    "content": "хочу что-то про космос",
    "created_at": "2024-11-17T13:00:00Z"
  },
  "assistant_message": {
    "id": 6,
    "role": "assistant",
    "content": "Вот несколько отличных книг про космос:\n\n📚 **\"Автостопом по галактике\"**...",
    "books": [
      {
        "id": "book_123",
        "title": "Автостопом по галактике",
        "author": "Дуглас Адамс",
        "genres": ["фантастика", "юмор"],
        "description": "...",
        "source_link": "https://example.com/hitchhikers-guide"
      }
    ],
    "created_at": "2024-11-17T13:00:05Z",
    "feedback": null
  }
}
```

**Errors:**
- `404 Not Found` - Чат не найден или не принадлежит пользователю
- `400 Bad Request` - Пустой запрос

**Примечание:** 
- Автоматически обновляет `title` чата, если это первое сообщение
- Сообщения сохраняются в БД

---

## 5. Обратная связь (лайки/дизлайки)

### POST /api/messages/{message_id}/feedback
Поставить лайк или дизлайк ответу ассистента

**Auth:** ✅ Требуется

**Request:**
```json
{
  "feedback": "like"  // или "dislike"
}
```

**Response:** `200 OK`
```json
{
  "message_id": 6,
  "feedback": "like",
  "updated_at": "2024-11-17T13:05:00Z"
}
```

**Errors:**
- `404 Not Found` - Сообщение не найдено или не принадлежит чату пользователя
- `400 Bad Request` - Невалидное значение feedback (не "like" или "dislike")
- `403 Forbidden` - Нельзя оценить сообщение пользователя (только assistant messages)

---

### DELETE /api/messages/{message_id}/feedback
Убрать лайк/дизлайк

**Auth:** ✅ Требуется

**Response:** `200 OK`
```json
{
  "message_id": 6,
  "feedback": null,
  "updated_at": "2024-11-17T13:10:00Z"
}
```

---

## 6. Служебные endpoints

### GET /api/health
Проверка работоспособности API

**Auth:** ❌ Не требуется

**Response:** `200 OK`
```json
{
  "status": "ok",
  "services": {
    "database": "ok",
    "qdrant": "ok",
    "llm": "ok"
  },
  "version": "1.0.0"
}
```

---

### GET /api/stats
Статистика использования (опционально, для аналитики)

**Auth:** ✅ Требуется

**Response:** `200 OK`
```json
{
  "total_chats": 5,
  "total_messages": 24,
  "liked_messages": 8,
  "disliked_messages": 2,
  "most_searched_genres": ["фантастика", "детектив", "классика"]
}
```

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | OK - успешный запрос |
| 201 | Created - ресурс создан |
| 204 | No Content - успешно удалено |
| 400 | Bad Request - невалидные данные |
| 401 | Unauthorized - требуется аутентификация |
| 403 | Forbidden - нет доступа к ресурсу |
| 404 | Not Found - ресурс не найден |
| 422 | Unprocessable Entity - ошибка валидации |
| 500 | Internal Server Error - ошибка сервера |

## Формат ошибок
```json
{
  "detail": "Описание ошибки"
}
```

## Rate Limiting (опционально)

- Анонимные запросы: 10 запросов/минуту
- Авторизованные: 60 запросов/минуту

## CORS

Разрешенные origins:
- Development: `http://localhost:3000`, `http://localhost:5173`

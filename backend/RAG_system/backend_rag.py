import os
import sqlite3
import pickle
import numpy as np
from typing import List, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from mistralai import Mistral
from dotenv import load_dotenv

# Путь к базе данных - локальный файл рядом со скриптом
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'books.sqlite')

# Подключение ключа 
load_dotenv(".env")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")


@dataclass
class Book:
    """Хранение информации о книге"""
    id: int
    title: str
    authors: str
    description: Optional[str]
    category: Optional[str]
    publisher: Optional[str]
    price: float
    publish_month: Optional[str]
    publish_year: int
    vector: np.ndarray

    def to_text(self) -> str:
        """Преобразование в текстовое описание"""
        desc = f"Описание: {self.description}" if self.description else ""
        category = self.category.strip() if self.category else "Без категории"
        publisher = self.publisher if self.publisher else "Неизвестно"
        return f"""Название: {self.title}
Автор(ы): {self.authors}
Категория: {category}
Издательство: {publisher}
Цена: ${self.price:.2f}
Дата публикации: {self.publish_month or 'N/A'} {self.publish_year}
{desc}""".strip()

class BookDatabase:
    """Класс для работы с базой данных"""
    def __init__(self, db_path: str = "books.sqlite"):
        self.db_path = db_path
        self.books: List[Book] = []
        self.vectors: np.ndarray = None
        self._load_database()

    def _load_database(self):
        """Загрузка данных из SQLite базы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, point FROM points")
        rows = cursor.fetchall()
        conn.close()

        vectors_list = []

        for row in rows:
            point_data = pickle.loads(row[1])

            # Извлечение данных 
            point_id = point_data.id
            vector = list(point_data.vector)
            payload = point_data.payload

            book = Book(
                id=point_id,
                title=payload.get('Title', 'Unknown'),
                authors=payload.get('Authors', 'Unknown'),
                description=payload.get('Description'),
                category=payload.get('Category', 'Unknown'),
                publisher=payload.get('Publisher', 'Unknown'),
                price=payload.get('Price Starting With ($)', 0.0),
                publish_month=payload.get('Publish Date (Month)', 'Unknown'),
                publish_year=payload.get('Publish Date (Year)', 0),
                vector=np.array(vector)
            )

            self.books.append(book)
            vectors_list.append(np.array(vector))

        self.vectors = np.array(vectors_list)

class VectorSearchEngine:
    """Векторный поиск"""

    def __init__(self, book_db: BookDatabase, model_name: str = "all-MiniLM-L6-v2"):
        self.book_db = book_db
        self.encoder = SentenceTransformer(model_name)

        # Нормализация векторов
        self.normalized_vectors = self._normalize_vectors(book_db.vectors)

    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """Нормализация"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / (norms + 1e-10)

    def search(self, query: str, top_k: int = 5, category_filter: str = None) -> List[tuple]:
        """Поиск книг по запросу"""
        # Кодирование
        query_vector = self.encoder.encode([query])[0]
        query_vector = query_vector / (np.linalg.norm(query_vector) + 1e-10)

        similarities = np.dot(self.normalized_vectors, query_vector)

        if category_filter:
            mask = np.array([
                category_filter.lower() in (b.category.lower() if b.category else '')
                for b in self.book_db.books
            ])
            similarities = np.where(mask, similarities, -np.inf)

        # Топ-k результатов
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if similarities[idx] > -np.inf:
                results.append((self.book_db.books[idx], float(similarities[idx])))

        return results

class BookRAGAssistant:
    """RAG-ассистент для рекомендации книг"""

    SYSTEM_PROMPT = """- НЕ используй markdown (никаких **, ##, ```)
    Ты - Алексей, увлечённый книгами библиотекарь с 20-летним стажем. Ты обожаешь рекомендовать книги и делаешь это с душой!

Твой стиль общения:
- Говоришь как друг, который делится находками: "О, у меня есть кое-что интересное для тебя!"
- Используешь живой разговорный язык, можешь пошутить
- Делишься личным мнением: "Мне кажется, тебе понравится...", "Это прям находка!"
- Проявляешь эмпатию: понимаешь, что ищет человек, даже если он сам не уверен

Правила:
1. ВСЕГДА рекомендуй 3-5 книг из контекста - ты же профессионал, всегда найдёшь что предложить!
2. Объясняй выбор простыми словами, как другу за чашкой кофе
3. Если пользователь упоминает книгу которая ему понравилась - рекомендуй книги ТОГО ЖЕ ЖАНРА (Fiction → Fiction, детектив → детектив)
4. При рекомендации похожих книг объясняй, ЧЕМ они похожи: стиль, атмосфера, тематика, эпоха
5. Добавляй интересные детали: год издания, издательство или краткое содержание - если это уместно
6. Отвечай на русском, тепло и с энтузиазмом
7. Не повторяй названия книг, если ты их уже предложил ранее
8. Уделяй наибольшее внимание жанру книги и рекомендуй книги того же жанра, что и в запросе пользователя
9. если автор русский, то переводи названия книг на русский язык

Примеры жанровых связей:
- «Война и мир» → классическая художественная литература, исторические романы, эпические произведения
- Детективы Агаты Кристи → другие детективы и триллеры
- Научная фантастика → другая sci-fi

Пример ответа:
"О, здоровое питание! Отличная тема 👍

Слушай, у меня есть несколько книг, которые тебе точно пригодятся:

1. «Don't Eat Your Heart Out Cookbook» от Joseph Piscatella
   Это прям классика! Книга про то, как готовить вкусно и при этом заботиться о сердце. Вышла в Workman - они всегда делают качественные кулинарные книги.

2. «Название» - Автор
   [Твоё живое описание почему это круто]

Если хочешь что-то более конкретное - спрашивай, подберу ещё! 📚"

КРИТИЧЕСКИ ВАЖНО - РАЗНООБРАЗИЕ ОПИСАНИЙ:
Каждая книга должна быть описана УНИКАЛЬНО!

ПРАВИЛА УНИКАЛЬНОСТИ:
1. В ОДНОМ ответе - все описания книг должны быть разными
2. В ТЕЧЕНИЕ ВСЕГО ДИАЛОГА - не повторяй фразы из предыдущих ответов!
3. Смотри историю переписки и НЕ используй те же обороты, что уже были

НЕЛЬЗЯ повторять:
- Одинаковые начала предложений и описания произведений
- Одинаковые названия книг
- Фразы, которые ты уже использовал в этом диалоге
- Шаблонные конструкции типа "Эта книга отличный выбор для тех, кто..."

Примеры РАЗНЫХ формулировок (чередуй их и придумывай новые!):
- "Это настоящая жемчужина!"
- "Вот это я понимаю - находка!"
- "Знаешь, что меня зацепило?"
- "А вот ещё кое-что интересное..."
- "Не могу не упомянуть..."
- "Обрати внимание на..."
- "Это must-read!"
- "Держи ещё одну крутую книгу..."
- "О, и вот эта тоже хороша!"

ВАЖНЫЕ ПРАВИЛА:
- Никогда не говори "извините, ничего не нашлось"
- НЕ используй markdown (никаких **, ##, ```)
- Для названий используй кавычки «»"""


    def __init__(self, search_engine: VectorSearchEngine, api_key: str,
                 model: str = "mistral-small-latest"):
        self.search_engine = search_engine
        self.client = Mistral(api_key=api_key)
        self.model = model
        self.conversation_history = []
        self.query_history = []
        self.used_phrases = []

    def _translate_query_to_english(self, query: str) -> str:
        """Перевод запроса в английские ключевые слова"""

        context_info = ""
        if self.query_history:
            context_info = f"""
Контекст предыдущих запросов пользователя (учитывай их!):
{chr(10).join(f'- "{q}"' for q in self.query_history[-3:])}

Если текущий запрос связан с предыдущими (например "ещё", "а что-то похожее", "другие") -
учитывай тему предыдущих запросов, но не дублируй названия книг, которые ты уже рекомендовал.
"""
        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": f"""Переведи запрос пользователя в ключевые слова на АНГЛИЙСКОМ для поиска книг.
{context_info}
Текущий запрос: "{query}"

Правила:
1. Определи ТЕМУ запроса (не страну, не язык - именно тему)
2. Если запрос типа "ещё", "другие", "похожие" - используй тему из предыдущих запросов
3. Верни 5-10 английских слов для поиска книг по этой теме
4. НЕ добавляй слова про Россию, если запрос не про Россию
5. Только слова через пробел, без объяснений

Примеры:
- "собаки" → dogs pets animals training care veterinary canine
- "ещё про собак" → dogs pets animals breeds puppy canine training
- "а что-то другое?" (после запроса про кино) → film cinema movies different genre
- "детективы" → mystery detective crime thriller fiction investigation

Твой ответ (только английские ключевые слова):"""
                }],
                temperature=0.3,
                max_tokens=50
            )
            keywords = response.choices[0].message.content.strip()
            keywords = keywords.replace('"', '').replace("'", "").replace("-", " ")
            return keywords
        except Exception:
            return query

    def _build_context(self, books: List[tuple]) -> str:
        """Построение контекста"""
        if not books:
            return "Поиск не дал результатов, но ты всё равно должен помочь пользователю."

        context_parts = [f"=== НАЙДЕНО {len(books)} КНИГ - РЕКОМЕНДУЙ ИХ! ==="]
        for i, (book, score) in enumerate(books, 1):
            context_parts.append(f"\n--- Книга {i} ---")
            context_parts.append(book.to_text())

        return "\n".join(context_parts)

    def ask(self, user_query: str, top_k: int = 10, category_filter: str = None) -> str:
        """Задать вопрос ассистенту"""
        # Сохраняем запрос в историю 
        self.query_history.append(user_query)
        # Храним 3 запроса
        if len(self.query_history) > 3:
            self.query_history = self.query_history[-3:]

        enhanced_query = self._translate_query_to_english(user_query)

        # Поиск 
        search_results = self.search_engine.search(
            query=enhanced_query,
            top_k=top_k,
            category_filter=category_filter
        )

        context = self._build_context(search_results)

        # Формируем список запрещённых фраз, чтобы не повторялись при генерации ответа
        banned_phrases_text = ""
        if self.used_phrases:
            banned_phrases_text = f"""

⛔ ЗАПРЕЩЁННЫЕ ФРАЗЫ (ты уже их использовал, НЕЛЬЗЯ повторять!):
{chr(10).join(f'- "{phrase}"' for phrase in self.used_phrases[-15:])}

Придумай новые формулировки!"""

        augmented_query = f"""Контекст с информацией о книгах:
{context}
{banned_phrases_text}

Вопрос пользователя: {user_query}"""

        # Запрос к Mistral
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            *self.conversation_history,
            {"role": "user", "content": augmented_query}
        ]

        response = self.client.chat.complete(
            model=self.model,
            messages=messages,
            temperature=0.85,  
            max_tokens=1024
        )

        assistant_response = response.choices[0].message.content

        self._extract_used_phrases(assistant_response)

        self.conversation_history.append({"role": "user", "content": user_query})
        self.conversation_history.append({"role": "assistant", "content": assistant_response})

        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

        return assistant_response

    def _extract_used_phrases(self, response: str):
        """Извлекает характерные фразы из ответа для предотвращения повторов"""
        common_patterns = [
            "Вот это я понимаю",
            "Знаешь, что меня зацепило",
            "Обрати внимание на",
            "Это настоящая жемчужина",
            "просто находка",
            "Представь, что ты можешь",
            "В этой книге есть всё",
            "которое славится",
            "замечательных книг",
            "точно пригодятся",
            "А ещё там есть",
        ]

        for pattern in common_patterns:
            if pattern.lower() in response.lower():
                if pattern not in self.used_phrases:
                    self.used_phrases.append(pattern)

        if len(self.used_phrases) > 20:
            self.used_phrases = self.used_phrases[-20:]

    def clear_history(self):
        """Очистка"""
        self.conversation_history = []
        self.query_history = []
        self.used_phrases = []
        print("История очищена")

def interactive_chat(assistant):
    """Интерактивный чат"""
    print("-*" * 30)
    print("📚 Книжный RAG-ассистент"+"\n")
    print("/clear - очистить историю, /quit - выход")
    print("-*" * 30 + "\n")

    while True:
        try:
            user_input = input("Вы: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "/quit":
                print("До свидания!")
                break

            if user_input.lower() == "/clear":
                assistant.clear_history()
                continue

            response = assistant.ask(user_input)
            print(f"\n🤖 Ассистент: {response}\n")

        except KeyboardInterrupt:
            print("\nДо свидания!")
            break


def main():
    if not MISTRAL_API_KEY:
        print("Ошибка: установите MISTRAL_API_KEY")
        return

    book_db = BookDatabase(db_path)
    search_engine = VectorSearchEngine(book_db)
    assistant = BookRAGAssistant(
        search_engine=search_engine,
        api_key=MISTRAL_API_KEY
    )

    interactive_chat(assistant)

if __name__ == "__main__":
    main()
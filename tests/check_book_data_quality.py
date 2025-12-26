#!/usr/bin/env python3
"""
Скрипт для проверки качества данных книг в SQLite базе данных

Проверяет наличие/отсутствие данных в полях книг и выводит статистику.
Полезен для диагностики проблем с низкими метриками RAGAS.
"""

import sqlite3
import pickle
import sys
import os
from typing import Dict, List, Any
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict, Counter

# Добавляем путь к backend для импорта
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from models.book import Book


@dataclass
class DataQualityStats:
    """Статистика качества данных"""
    total_books: int = 0
    books_with_description: int = 0
    books_with_empty_description: int = 0
    books_with_null_description: int = 0
    books_without_title: int = 0
    books_without_authors: int = 0
    books_without_category: int = 0
    books_without_publisher: int = 0

    # Детальная статистика по категориям
    category_stats: Dict[str, int] = None
    publisher_stats: Dict[str, int] = None
    author_patterns: Dict[str, int] = None

    def __post_init__(self):
        if self.category_stats is None:
            self.category_stats = defaultdict(int)
        if self.publisher_stats is None:
            self.publisher_stats = defaultdict(int)
        if self.author_patterns is None:
            self.author_patterns = defaultdict(int)


def load_books_from_db(db_path: str) -> List[Book]:
    """Загрузка книг из SQLite базы данных"""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    books = []

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, point FROM points")
        rows = cursor.fetchall()

        for row in rows:
            point_data = pickle.loads(row[1])

            # Извлечение данных
            point_id = point_data.id
            vector = list(point_data.vector)
            payload = point_data.payload

            book = Book(
                id=point_id,
                title=payload.get('Title', ''),
                authors=payload.get('Authors', ''),
                description=payload.get('Description'),
                category=payload.get('Category'),
                publisher=payload.get('Publisher'),
                price=payload.get('Price Starting With ($)', 0.0),
                publish_month=payload.get('Publish Date (Month)'),
                publish_year=payload.get('Publish Date (Year)', 0),
                vector=vector
            )

            books.append(book)

    except Exception as e:
        print(f"Error loading database: {e}")
        return []
    finally:
        conn.close()

    return books


def analyze_data_quality(books: List[Book]) -> DataQualityStats:
    """Анализ качества данных книг"""
    stats = DataQualityStats()

    for book in books:
        stats.total_books += 1

        # Проверка описания
        if book.description is None:
            stats.books_with_null_description += 1
        elif not book.description.strip():
            stats.books_with_empty_description += 1
        else:
            stats.books_with_description += 1

        # Проверка других полей
        if not book.title or book.title.strip() == '':
            stats.books_without_title += 1

        if not book.authors or book.authors.strip() == '':
            stats.books_without_authors += 1

        if not book.category or book.category.strip() in ('', 'Unknown'):
            stats.books_without_category += 1
        else:
            stats.category_stats[book.category.strip()] += 1

        if not book.publisher or book.publisher.strip() in ('', 'Unknown'):
            stats.books_without_publisher += 1
        else:
            stats.publisher_stats[book.publisher.strip()] += 1

        # Анализ паттернов авторов
        if book.authors and book.authors.strip():
            # Упрощенный анализ (можно расширить)
            if ',' in book.authors:
                stats.author_patterns['multiple_authors'] += 1
            else:
                stats.author_patterns['single_author'] += 1
        else:
            stats.author_patterns['no_authors'] += 1

    return stats


def print_quality_report(stats: DataQualityStats, db_path: str):
    """Вывод отчета о качестве данных"""
    print("=" * 60)
    print("ОТЧЕТ О КАЧЕСТВЕ ДАННЫХ КНИГ")
    print("=" * 60)
    print(f"База данных: {db_path}")
    print(f"Всего книг: {stats.total_books:,}")
    print()

    # Основная статистика по описаниям
    print("[STATS] СТАТИСТИКА ПО ОПИСАНИЯМ:")
    print("-" * 40)

    desc_percent = (stats.books_with_description / stats.total_books * 100) if stats.total_books > 0 else 0
    empty_percent = (stats.books_with_empty_description / stats.total_books * 100) if stats.total_books > 0 else 0
    null_percent = (stats.books_with_null_description / stats.total_books * 100) if stats.total_books > 0 else 0

    print(f"[OK] С описанием:     {stats.books_with_description:>6,} ({desc_percent:>5.1f}%)")
    print(f"[EMPTY] Пустые описания: {stats.books_with_empty_description:>6,} ({empty_percent:>5.1f}%)")
    print(f"[NULL] NULL описания:   {stats.books_with_null_description:>6,} ({null_percent:>5.1f}%)")
    print()

    # Статистика по другим полям
    print("[STATS] СТАТИСТИКА ПО ДРУГИМ ПОЛЯМ:")
    print("-" * 40)

    title_missing = stats.books_without_title
    authors_missing = stats.books_without_authors
    category_missing = stats.books_without_category
    publisher_missing = stats.books_without_publisher

    print(f"Без названия:       {title_missing:>6,}")
    print(f"Без авторов:        {authors_missing:>6,}")
    print(f"Без категории:      {category_missing:>6,}")
    print(f"Без издательства:   {publisher_missing:>6,}")
    print()

    # Топ категорий
    if stats.category_stats:
        print("[TOP] ТОП-10 КАТЕГОРИЙ:")
        print("-" * 40)
        sorted_categories = sorted(stats.category_stats.items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories[:10]:
            percent = (count / stats.total_books * 100)
            print(f"{category:<30} {count:>6,} ({percent:>5.1f}%)")
        print()

    # Топ издательств
    if stats.publisher_stats:
        print("[TOP] ТОП-10 ИЗДАТЕЛЬСТВ:")
        print("-" * 40)
        sorted_publishers = sorted(stats.publisher_stats.items(), key=lambda x: x[1], reverse=True)
        for publisher, count in sorted_publishers[:10]:
            percent = (count / stats.total_books * 100)
            print(f"{publisher:<30} {count:>6,} ({percent:>5.1f}%)")
        print()

    # Проблемные книги
    if desc_percent < 50:
        print("[WARNING] ВНИМАНИЕ: МЕНЬШЕ 50% КНИГ ИМЕЮТ ОПИСАНИЯ!")
        print("          Это может вызвать проблемы с метриками RAGAS")
        print()

    print("=" * 60)


def find_books_without_description(books: List[Book], limit: int = 10) -> List[Book]:
    """Найти книги без описания для примера"""
    books_without_desc = []

    for book in books:
        if not book.description or not book.description.strip():
            books_without_desc.append(book)
            if len(books_without_desc) >= limit:
                break

    return books_without_desc


def main():
    """Основная функция"""
    import argparse

    parser = argparse.ArgumentParser(description="Проверка качества данных книг в SQLite БД")
    parser.add_argument("--db-path", default="data/storage.sqlite",
                       help="Путь к файлу базы данных SQLite")
    parser.add_argument("--show-examples", action="store_true",
                       help="Показать примеры книг без описания")

    args = parser.parse_args()

    # Преобразование пути относительно скрипта
    if not os.path.isabs(args.db_path):
        script_dir = Path(__file__).parent
        db_path = script_dir.parent / args.db_path
    else:
        db_path = Path(args.db_path)

    db_path = db_path.resolve()

    print(f"Загрузка базы данных: {db_path}")

    try:
        # Загрузка книг
        books = load_books_from_db(str(db_path))

        if not books:
            print("[ERROR] Ошибка: Не удалось загрузить книги из базы данных")
            return 1

        # Анализ качества данных
        stats = analyze_data_quality(books)

        # Вывод отчета
        print_quality_report(stats, str(db_path))

        # Показать примеры книг без описания
        if args.show_examples:
            print("[EXAMPLES] ПРИМЕРЫ КНИГ БЕЗ ОПИСАНИЯ:")
            print("-" * 40)
            books_without_desc = find_books_without_description(books, 5)

            for i, book in enumerate(books_without_desc, 1):
                print(f"{i}. ID: {book.id}")
                print(f"   Название: {book.title}")
                print(f"   Авторы: {book.authors}")
                print(f"   Категория: {book.category or 'N/A'}")
                print(f"   Описание: {repr(book.description)}")
                print()

        return 0

    except Exception as e:
        print(f"[ERROR] Ошибка выполнения: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

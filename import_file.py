"""CLI скрипт для імпорту відгуків з CSV файлу, що знаходиться на диску.

Використання:
    python import_file.py --file reviews.csv --column text
    python import_file.py --file amazon_export.csv --column review_body

Скрипт виводить результат аналізу кожного відгуку в консоль
та підсумкову статистику в кінці.
"""

import argparse
import sys


def parse_args() -> argparse.Namespace:
    """Парсить аргументи командного рядка.

    Returns:
        Namespace з полями:
            - file (str): шлях до CSV файлу
            - column (str): назва колонки з текстом відгуку
    """
    parser = argparse.ArgumentParser(
        description="Імпорт та аналіз відгуків з CSV файлу.",
        # Приклад використання у довідці
        epilog="Приклад: python import_file.py --file data.csv --column text",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Шлях до CSV файлу з відгуками.",
    )
    parser.add_argument(
        "--column",
        required=True,
        help="Назва колонки, що містить текст відгуку.",
    )
    return parser.parse_args()


def main() -> None:
    """Головна функція: завантажує відгуки, аналізує та виводить результат."""
    args = parse_args()

    # Підтримуємо два варіанти запуску:
    # 1. З кореня проекту через pip install -e . (звичайний імпорт)
    # 2. Напряму через python import_file.py (з префіксом src.)
    try:
        from feedback_analyzer.analyzer import analyze
        from feedback_analyzer.importer import load_texts
    except ImportError:
        from src.feedback_analyzer.analyzer import analyze
        from src.feedback_analyzer.importer import load_texts

    # Завантажуємо та очищаємо тексти з вказаної колонки
    try:
        texts = load_texts(args.file, args.column)
    except (ValueError, FileNotFoundError) as e:
        # Виводимо зрозуміле повідомлення про помилку і виходимо
        print(f"Помилка: {e}")
        sys.exit(1)

    if not texts:
        print("Не знайдено жодного валідного відгуку. Перевірте файл та назву колонки.")
        sys.exit(1)

    # Лічильники для підсумкової статистики
    results = {"positive": 0, "negative": 0, "neutral": 0}

    # Аналізуємо кожен відгук та виводимо результат у форматованому вигляді
    for text in texts:
        result = analyze(text)
        sentiment = result["sentiment"]
        score = result["score"]

        results[sentiment] += 1

        # Обрізаємо текст до 60 символів для зручного відображення в консолі
        short_text = text[:60] + "..." if len(text) > 60 else text
        print(f"[{sentiment:8}] {score:+.4f}  {short_text}")

    # Виводимо підсумкову статистику
    total = len(texts)
    print(f"\n{'─' * 40}")
    print(f"Всього відгуків: {total}")
    print(f"  позитивних : {results['positive']}  ({results['positive']/total*100:.1f}%)")
    print(f"  негативних : {results['negative']}  ({results['negative']/total*100:.1f}%)")
    print(f"  нейтральних: {results['neutral']}  ({results['neutral']/total*100:.1f}%)")


if __name__ == "__main__":
    main()
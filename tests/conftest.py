"""Спільні фікстури для всіх тестів проекту.

Фікстури автоматично підхоплюються pytest з цього файлу
без необхідності явного імпорту в тестових модулях.
"""

import pytest


@pytest.fixture
def sample_texts() -> dict:
    """Повертає набір текстів з відомою тональністю для тестування analyze().

    Тексти підібрані так, щоб VADER однозначно їх класифікував —
    без граничних випадків, де compound близький до порогів ±0.05.

    Returns:
        Словник з ключами 'positive', 'negative', 'neutral',
        кожен містить список рядків відповідної тональності.
    """
    return {
        "positive": [
            "I absolutely love this product, it is amazing!",
            "Great quality, fast delivery, very happy with my purchase.",
            "Excellent service, highly recommend to everyone!",
        ],
        "negative": [
            "Terrible experience, total waste of money.",
            "Worst product I have ever bought in my life.",
            "Very disappointed, do not buy this, complete garbage.",
        ],
        "neutral": [
            # Нейтральні тексти — факти без емоційного забарвлення
            "It arrived on time.",
            "The package was delivered yesterday.",
            "Item received as described.",
        ],
    }


@pytest.fixture
def sample_csv(tmp_path) -> str:
    """Створює тимчасовий CSV файл зі стандартною структурою для тестів.

    Файл містить:
        - 3 валідні відгуки різної тональності
        - 1 порожній рядок (має бути пропущений)
        - 1 рядок занадто короткий — "Ok" (2 символи, має бути пропущений)

    Args:
        tmp_path: Вбудована фікстура pytest — тимчасова директорія,
                  яка автоматично видаляється після тесту.

    Returns:
        Шлях до створеного CSV файлу у вигляді рядка.
    """
    csv_file = tmp_path / "reviews.csv"
    csv_file.write_text(
        "text,source\n"
        "\"Great product, I love it!\",test\n"   # позитивний — валідний
        "\"Terrible service, very bad.\",test\n"  # негативний — валідний
        "\"It arrived on time.\",test\n"           # нейтральний — валідний
        "\"\",test\n"                              # порожній — має бути пропущений
        "\"Ok\",test\n",                           # 2 символи — має бути пропущений
        encoding="utf-8",
    )
    return str(csv_file)


@pytest.fixture
def multiformat_csv(tmp_path) -> str:
    """Створює тимчасовий CSV з нестандартною назвою колонки (Amazon-подібний формат).

    Використовується для перевірки що importer коректно працює
    з різними форматами експорту (Trustpilot, Amazon тощо).

    Args:
        tmp_path: Вбудована фікстура pytest — тимчасова директорія.

    Returns:
        Шлях до створеного CSV файлу у вигляді рядка.
    """
    csv_file = tmp_path / "amazon_reviews.csv"
    csv_file.write_text(
        "review_body,rating,date\n"
        "\"Fast delivery and great quality!\",5,2026-01-15\n"
        "\"Broken on arrival, very disappointed.\",1,2026-01-16\n",
        encoding="utf-8",
    )
    return str(csv_file)
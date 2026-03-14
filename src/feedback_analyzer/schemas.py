"""Pydantic схеми для валідації даних на вході та виході API."""

from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    """Схема для створення нового відгуку.

    Використовується при отриманні даних від користувача —
    через форму або JSON тіло запиту.
    """

    # Текст відгуку — мінімум 3 символи, максимум 5000
    text: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Текст відгуку англійською мовою.",
    )

    # Джерело відгуку — за замовчуванням 'form'
    source: str = Field(
        default="form",
        description="Джерело відгуку: form, csv або script.",
    )


class FeedbackOut(BaseModel):
    """Схема для відповіді API — відгук з результатом аналізу.

    Використовується при поверненні даних клієнту.
    """

    id: int
    text: str
    source: str
    sentiment: str
    score: float
    created_at: datetime

    # Дозволяємо читати дані з SQLAlchemy об'єктів (ORM mode)
    model_config = {"from_attributes": True}


class ImportColumn(BaseModel):
    """Схема для підтвердження імпорту CSV — вибір колонки."""

    # Назва колонки яку обрав користувач
    column: str = Field(
        ...,
        description="Назва колонки що містить текст відгуку.",
    )


class StatsOut(BaseModel):
    """Схема статистики тональності відгуків."""

    total: int
    positive: int
    negative: int
    neutral: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
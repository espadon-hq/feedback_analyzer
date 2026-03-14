"""Роутер для отримання статистики тональності відгуків."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from feedback_analyzer.database import get_db
from feedback_analyzer.models import Feedback
from feedback_analyzer.schemas import StatsOut

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "/",
    response_model=StatsOut,
    summary="Статистика тональності відгуків",
)
def get_stats(db: Session = Depends(get_db)) -> StatsOut:
    """Повертає загальну статистику тональності всіх відгуків.

    Args:
        db: Сесія БД, інжектується через Depends.

    Returns:
        StatsOut з кількістю та відсотками по кожній тональності.
    """
    # Отримуємо загальну кількість відгуків
    total = db.query(Feedback).count()

    # Якщо відгуків немає — повертаємо нулі
    if total == 0:
        return StatsOut(
            total=0,
            positive=0,
            negative=0,
            neutral=0,
            positive_pct=0.0,
            negative_pct=0.0,
            neutral_pct=0.0,
        )

    # Рахуємо кількість по кожній тональності окремими запитами
    positive = (
        db.query(Feedback)
        .filter(Feedback.sentiment == "positive")
        .count()
    )
    negative = (
        db.query(Feedback)
        .filter(Feedback.sentiment == "negative")
        .count()
    )
    neutral = (
        db.query(Feedback)
        .filter(Feedback.sentiment == "neutral")
        .count()
    )

    # Рахуємо відсотки, округлюємо до 1 знака після коми
    return StatsOut(
        total=total,
        positive=positive,
        negative=negative,
        neutral=neutral,
        positive_pct=round(positive / total * 100, 1),
        negative_pct=round(negative / total * 100, 1),
        neutral_pct=round(neutral / total * 100, 1),
    )
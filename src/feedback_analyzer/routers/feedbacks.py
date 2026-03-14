"""Роутер для операцій з відгуками — створення, перегляд, видалення."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from feedback_analyzer.analyzer import analyze
from feedback_analyzer.database import get_db
from feedback_analyzer.models import Feedback
from feedback_analyzer.schemas import FeedbackCreate, FeedbackOut

# Створюємо роутер з префіксом — всі ендпоінти починатимуться з /feedbacks
router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])


@router.post(
    "/",
    response_model=FeedbackOut,
    status_code=status.HTTP_201_CREATED,
    summary="Додати новий відгук",
)
def create_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
) -> Feedback:
    """Приймає текст відгуку, аналізує тональність та зберігає в БД.

    Args:
        data: Валідовані дані від користувача (текст + джерело).
        db: Сесія БД, інжектується через Depends.

    Returns:
        Збережений відгук з результатом аналізу.
    """
    # Аналізуємо тональність тексту через VADER
    result = analyze(data.text)

    # Створюємо об'єкт моделі з даними відгуку та результатом аналізу
    feedback = Feedback(
        text=data.text,
        source=data.source,
        sentiment=result["sentiment"],
        score=result["score"],
    )

    # Зберігаємо в БД
    db.add(feedback)
    db.commit()

    # Оновлюємо об'єкт з БД щоб отримати id та created_at
    db.refresh(feedback)

    return feedback


@router.get(
    "/",
    response_model=list[FeedbackOut],
    summary="Отримати список відгуків",
)
def get_feedbacks(
    skip: int = 0,
    limit: int = 50,
    sentiment: str | None = None,
    db: Session = Depends(get_db),
) -> list[Feedback]:
    """Повертає список відгуків з пагінацією та фільтрацією.

    Args:
        skip: Кількість записів для пропуску (для пагінації).
        limit: Максимальна кількість записів у відповіді.
        sentiment: Фільтр за тональністю — 'positive', 'negative', 'neutral'.
        db: Сесія БД, інжектується через Depends.

    Returns:
        Список відгуків відсортованих від найновіших до найстаріших.
    """
    # Базовий запит — всі відгуки
    query = db.query(Feedback)

    # Якщо переданий фільтр — додаємо умову WHERE
    if sentiment:
        # Перевіряємо що передане значення допустиме
        allowed = {"positive", "negative", "neutral"}
        if sentiment not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустиме значення sentiment. Допустимі: {allowed}",
            )
        query = query.filter(Feedback.sentiment == sentiment)

    # Сортуємо від найновіших, застосовуємо пагінацію
    return (
        query
        .order_by(Feedback.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/{feedback_id}",
    response_model=FeedbackOut,
    summary="Отримати один відгук за id",
)
def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
) -> Feedback:
    """Повертає один відгук за його id.

    Args:
        feedback_id: Унікальний ідентифікатор відгуку.
        db: Сесія БД, інжектується через Depends.

    Returns:
        Відгук з вказаним id.

    Raises:
        HTTPException 404: Якщо відгук з таким id не знайдено.
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Відгук з id={feedback_id} не знайдено.",
        )

    return feedback


@router.delete(
    "/{feedback_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити відгук за id",
)
def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Видаляє відгук з БД за його id.

    Args:
        feedback_id: Унікальний ідентифікатор відгуку.
        db: Сесія БД, інжектується через Depends.

    Raises:
        HTTPException 404: Якщо відгук з таким id не знайдено.
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()

    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Відгук з id={feedback_id} не знайдено.",
        )

    db.delete(feedback)
    db.commit()
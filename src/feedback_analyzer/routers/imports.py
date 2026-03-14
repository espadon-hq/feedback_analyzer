"""Роутер для імпорту відгуків з CSV файлу."""

import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from feedback_analyzer.analyzer import analyze
from feedback_analyzer.database import get_db
from feedback_analyzer.importer import get_columns, load_texts
from feedback_analyzer.models import Feedback
from feedback_analyzer.schemas import FeedbackOut

router = APIRouter(prefix="/feedbacks", tags=["imports"])

# Максимальний розмір CSV файлу — 5 MB
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post(
    "/import/columns",
    summary="Завантажити CSV та отримати список колонок",
)
async def upload_csv_get_columns(
    file: UploadFile = File(...),
) -> dict:
    """Приймає CSV файл та повертає список його колонок.

    Перший крок двоетапного імпорту — користувач дізнається
    які колонки є у файлі перед підтвердженням імпорту.

    Args:
        file: CSV файл завантажений через форму.

    Returns:
        Словник з ключем 'columns' — список назв колонок.

    Raises:
        HTTPException 400: Якщо файл не є CSV або перевищує ліміт розміру.
    """
    # Перевіряємо що завантажено саме CSV файл
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дозволені лише файли формату CSV.",
        )

    # Читаємо вміст файлу та перевіряємо розмір
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл перевищує максимальний розмір 5 MB.",
        )

    # Зберігаємо у тимчасовий файл щоб pandas міг його прочитати
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".csv", mode="wb"
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        columns = get_columns(tmp_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Помилка читання файлу: {e}",
        )
    finally:
        # Видаляємо тимчасовий файл у будь-якому випадку
        os.unlink(tmp_path)

    return {"columns": columns}


@router.post(
    "/import",
    response_model=list[FeedbackOut],
    status_code=status.HTTP_201_CREATED,
    summary="Імпортувати відгуки з CSV файлу",
)
async def import_csv(
    file: UploadFile = File(...),
    column: str = Form(...),
    db: Session = Depends(get_db),
) -> list[Feedback]:
    """Імпортує відгуки з CSV файлу та аналізує їх тональність.

    Другий крок двоетапного імпорту — користувач передає файл
    та вказує яка колонка містить текст відгуку.

    Args:
        file: CSV файл завантажений через форму.
        column: Назва колонки що містить текст відгуку.
        db: Сесія БД, інжектується через Depends.

    Returns:
        Список створених відгуків з результатами аналізу.

    Raises:
        HTTPException 400: Якщо файл некоректний або колонка не знайдена.
    """
    # Перевіряємо формат файлу
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дозволені лише файли формату CSV.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл перевищує максимальний розмір 5 MB.",
        )

    # Зберігаємо у тимчасовий файл
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".csv", mode="wb"
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        texts = load_texts(tmp_path, column)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    finally:
        os.unlink(tmp_path)

    if not texts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не знайдено жодного валідного відгуку у вказаній колонці.",
        )

    # Аналізуємо кожен текст та зберігаємо в БД
    saved = []
    for text in texts:
        result = analyze(text)
        feedback = Feedback(
            text=text,
            source="csv",
            sentiment=result["sentiment"],
            score=result["score"],
        )
        db.add(feedback)
        saved.append(feedback)

    # Зберігаємо всі відгуки одним commit — ефективніше ніж по одному
    db.commit()

    # Оновлюємо всі об'єкти щоб отримати id та created_at з БД
    for feedback in saved:
        db.refresh(feedback)

    return saved
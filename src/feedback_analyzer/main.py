"""Головний модуль FastAPI застосунку.

Точка входу — тут створюється app, підключаються роутери,
ініціалізується база даних та реєструються HTML ендпоінти
для веб-інтерфейсу.
"""

import os
import tempfile

from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from feedback_analyzer.analyzer import analyze
from feedback_analyzer.database import get_db, init_db
from feedback_analyzer.importer import get_columns, load_texts
from feedback_analyzer.models import Feedback
from feedback_analyzer.routers import feedbacks, imports, stats

# Створюємо екземпляр FastAPI застосунку
app = FastAPI(
    title="Система аналізу відгуків",
    description="REST API для збору та аналізу тональності відгуків.",
    version="0.1.0",
)

# Визначаємо шлях до папки з Jinja2 шаблонами відносно цього файлу
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


@app.on_event("startup")
def startup() -> None:
    """Виконується один раз при старті застосунку.

    Створює таблиці в БД якщо вони ще не існують.
    """
    init_db()


# ── REST API роутери ──────────────────────────────────────────────────────────

app.include_router(feedbacks.router)
app.include_router(imports.router)
app.include_router(stats.router)


@app.get("/api", tags=["root"])
def api_root() -> dict:
    """Кореневий ендпоінт API — перевірка що застосунок працює."""
    return {"message": "Система аналізу відгуків працює!"}


# ── HTML сторінки (веб-інтерфейс) ────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse, tags=["web"])
def index(
    request: Request,
    sentiment: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Головна сторінка — список відгуків з формою додавання.

    Args:
        request: Об'єкт запиту FastAPI (потрібен для Jinja2).
        sentiment: Необов'язковий фільтр тональності з query параметра.
        db: Сесія БД, інжектується через Depends.

    Returns:
        HTML сторінка зі списком відгуків.
    """
    # Базовий запит — всі відгуки
    query = db.query(Feedback)

    # Застосовуємо фільтр якщо переданий query параметр ?sentiment=...
    if sentiment in ("positive", "negative", "neutral"):
        query = query.filter(Feedback.sentiment == sentiment)

    # Сортуємо від найновіших до найстаріших
    feedbacks_list = query.order_by(Feedback.created_at.desc()).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "feedbacks": feedbacks_list,
        # Передаємо поточний фільтр щоб шаблон міг виділити активний пункт
        "sentiment": sentiment,
    })


@app.post("/feedbacks/form", tags=["web"])
def create_feedback_form(
    text: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Приймає відгук з HTML форми, аналізує тональність та зберігає в БД.

    Після збереження перенаправляє на головну сторінку (PRG патерн —
    Post/Redirect/Get запобігає повторному відправленню форми при F5).

    Args:
        text: Текст відгуку з поля форми.
        db: Сесія БД, інжектується через Depends.

    Returns:
        Перенаправлення на головну сторінку зі статусом 303.
    """
    # Аналізуємо тональність тексту через VADER
    result = analyze(text)

    # Створюємо та зберігаємо відгук в БД
    feedback = Feedback(
        text=text,
        source="form",
        sentiment=result["sentiment"],
        score=result["score"],
    )
    db.add(feedback)
    db.commit()

    # 303 See Other — стандартний статус для PRG патерну
    return RedirectResponse(url="/", status_code=303)


@app.post("/feedbacks/{feedback_id}/delete", tags=["web"])
def delete_feedback_form(
    feedback_id: int,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Видаляє відгук за id та повертає на головну сторінку.

    HTML форми не підтримують метод DELETE тому використовуємо POST
    з URL що містить /delete.

    Args:
        feedback_id: Ідентифікатор відгуку з URL.
        db: Сесія БД, інжектується через Depends.

    Returns:
        Перенаправлення на головну сторінку зі статусом 303.
    """
    # Шукаємо відгук — якщо не знайдено просто ігноруємо
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if feedback:
        db.delete(feedback)
        db.commit()

    return RedirectResponse(url="/", status_code=303)


@app.get("/import", response_class=HTMLResponse, tags=["web"])
def import_page(request: Request) -> HTMLResponse:
    """Сторінка імпорту CSV — крок 1 (порожня форма завантаження).

    Args:
        request: Об'єкт запиту FastAPI.

    Returns:
        HTML сторінка з формою завантаження файлу.
    """
    return templates.TemplateResponse("import.html", {
        "request": request,
    })


@app.post("/import", response_class=HTMLResponse, tags=["web"])
async def import_upload(
    request: Request,
    file: UploadFile = File(...),
) -> HTMLResponse:
    """Приймає CSV файл, зберігає тимчасово та повертає список колонок.

    Файл зберігається у тимчасовий файл на диску і НЕ видаляється одразу —
    його шлях передається в шаблон як приховане поле форми.
    Це дозволяє уникнути повторного завантаження файлу на кроці 2.

    Args:
        request: Об'єкт запиту FastAPI.
        file: Завантажений CSV файл.

    Returns:
        HTML сторінка зі списком колонок файлу.
    """
    # Перевіряємо формат файлу
    if not file.filename.endswith(".csv"):
        return templates.TemplateResponse("import.html", {
            "request": request,
            "error": "Дозволені лише файли формату CSV.",
        })

    content = await file.read()

    # Перевіряємо розмір файлу — максимум 5 MB
    if len(content) > 5 * 1024 * 1024:
        return templates.TemplateResponse("import.html", {
            "request": request,
            "error": "Файл перевищує максимальний розмір 5 MB.",
        })

    # Зберігаємо файл тимчасово на диску.
    # delete=False — файл НЕ видаляється автоматично,
    # бо він потрібен на наступному кроці підтвердження
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".csv", mode="wb"
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        columns = get_columns(tmp_path)
    except Exception as e:
        # Якщо файл некоректний — видаляємо і показуємо помилку
        os.unlink(tmp_path)
        return templates.TemplateResponse("import.html", {
            "request": request,
            "error": f"Помилка читання файлу: {e}",
        })

    # Передаємо шлях до тимчасового файлу через приховане поле форми
    return templates.TemplateResponse("import.html", {
        "request": request,
        "columns": columns,
        "tmp_path": tmp_path,
    })


@app.post("/import/confirm", response_class=HTMLResponse, tags=["web"])
async def import_confirm(
    request: Request,
    tmp_path: str = Form(...),
    column: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Імпортує відгуки з раніше збереженого тимчасового файлу.

    Отримує шлях до файлу збереженого на кроці 1 —
    файл завантажувати повторно не потрібно.
    Після імпорту тимчасовий файл обов'язково видаляється.

    Args:
        request: Об'єкт запиту FastAPI.
        tmp_path: Шлях до тимчасового CSV файлу збереженого на кроці 1.
        column: Назва колонки з текстом відгуку.
        db: Сесія БД, інжектується через Depends.

    Returns:
        HTML сторінка з повідомленням про результат імпорту.
    """
    # Перевіряємо що файл існує та має правильне розширення —
    # захист від підробки шляху через форму
    if not os.path.exists(tmp_path) or not tmp_path.endswith(".csv"):
        return templates.TemplateResponse("import.html", {
            "request": request,
            "error": "Тимчасовий файл не знайдено. Завантажте файл знову.",
        })

    try:
        texts = load_texts(tmp_path, column)
    except ValueError as e:
        return templates.TemplateResponse("import.html", {
            "request": request,
            "error": str(e),
        })
    finally:
        # Видаляємо тимчасовий файл у будь-якому випадку — успіх або помилка
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if not texts:
        return templates.TemplateResponse("import.html", {
            "request": request,
            "error": "Не знайдено жодного валідного відгуку у вказаній колонці.",
        })

    # Аналізуємо кожен текст та зберігаємо в БД
    for text in texts:
        result = analyze(text)
        db.add(Feedback(
            text=text,
            source="csv",
            sentiment=result["sentiment"],
            score=result["score"],
        ))

    # Зберігаємо всі відгуки одним commit — ефективніше ніж по одному
    db.commit()

    return templates.TemplateResponse("import.html", {
        "request": request,
        "imported_count": len(texts),
    })


@app.get("/stats", response_class=HTMLResponse, tags=["web"])
def stats_page(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Сторінка статистики тональності відгуків.

    Args:
        request: Об'єкт запиту FastAPI.
        db: Сесія БД, інжектується через Depends.

    Returns:
        HTML сторінка зі статистикою та прогрес-барами.
    """
    total = db.query(Feedback).count()

    if total == 0:
        # Якщо відгуків немає — передаємо нулі в шаблон
        stats_data = {
            "total": 0,
            "positive": 0, "negative": 0, "neutral": 0,
            "positive_pct": 0.0, "negative_pct": 0.0, "neutral_pct": 0.0,
        }
    else:
        # Рахуємо кількість по кожній тональності окремими запитами
        pos = db.query(Feedback).filter(Feedback.sentiment == "positive").count()
        neg = db.query(Feedback).filter(Feedback.sentiment == "negative").count()
        neu = db.query(Feedback).filter(Feedback.sentiment == "neutral").count()

        stats_data = {
            "total": total,
            "positive": pos,
            "negative": neg,
            "neutral": neu,
            "positive_pct": round(pos / total * 100, 1),
            "negative_pct": round(neg / total * 100, 1),
            "neutral_pct": round(neu / total * 100, 1),
        }

    return templates.TemplateResponse("stats.html", {
        "request": request,
        # Передаємо як об'єкт для зручного звернення stats.total в шаблоні
        "stats": type("Stats", (), stats_data)(),
    })
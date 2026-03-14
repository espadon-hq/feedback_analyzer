"""Головний модуль FastAPI застосунку.

Точка входу — тут створюється app, підключаються роутери
та ініціалізується база даних при старті.
"""

from fastapi import FastAPI

from feedback_analyzer.database import init_db
from feedback_analyzer.routers import feedbacks, imports, stats

# Створюємо екземпляр FastAPI застосунку
app = FastAPI(
    title="Система аналізу відгуків",
    description="REST API для збору та аналізу тональності відгуків користувачів.",
    version="0.1.0",
)


@app.on_event("startup")
def startup() -> None:
    """Виконується один раз при старті застосунку.

    Створює таблиці в БД якщо вони ще не існують.
    """
    init_db()


# Підключаємо роутери — кожен відповідає за свою групу ендпоінтів
app.include_router(feedbacks.router)
app.include_router(imports.router)
app.include_router(stats.router)


@app.get("/", tags=["root"])
def root() -> dict:
    """Кореневий ендпоінт — перевірка що застосунок працює."""
    return {"message": "Система аналізу відгуків працює!"}
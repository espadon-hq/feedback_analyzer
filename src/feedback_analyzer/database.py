"""Модуль підключення до бази даних SQLite через SQLAlchemy.

Тут створюється єдине підключення до БД, яке використовується
всіма іншими модулями застосунку через залежність get_db().
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Шлях до файлу SQLite — буде створений автоматично при першому запуску.
# Файл з'явиться в корені проекту як feedback.db
DATABASE_URL = "sqlite:///./feedback.db"

# Створюємо рушій підключення до БД.
# connect_args={"check_same_thread": False} потрібен лише для SQLite —
# дозволяє використовувати одне підключення з різних потоків FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# SessionLocal — фабрика сесій для роботи з БД.
# autocommit=False — зміни треба підтверджувати явно через session.commit()
# autoflush=False — не відправляти зміни в БД до явного flush або commit
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Базовий клас для всіх SQLAlchemy моделей проекту.

    Всі моделі успадковуються від цього класу —
    це дозволяє створити таблиці одним викликом Base.metadata.create_all().
    """
    pass


def init_db() -> None:
    """Створює всі таблиці в БД якщо вони ще не існують.

    Викликається один раз при старті застосунку в main.py.
    Якщо таблиці вже існують — нічого не робить (безпечно повторювати).
    """
    # Імпортуємо models щоб SQLAlchemy знав про всі моделі
    # перед викликом create_all()
    from feedback_analyzer import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """Генератор сесії БД для використання як залежність у FastAPI.

    Використовується через Depends(get_db) в роутерах.
    Гарантує що сесія завжди закривається після запиту —
    навіть якщо під час обробки виникла помилка.

    Yields:
        Session: активна сесія SQLAlchemy для поточного запиту.
    """
    db = SessionLocal()
    try:
        # Передаємо сесію в роутер
        yield db
    finally:
        # Закриваємо сесію в будь-якому випадку — успіх або помилка
        db.close()
"""Моделі бази даних — SQLAlchemy таблиці проекту."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from feedback_analyzer.database import Base


class Feedback(Base):
    """Модель таблиці відгуків у базі даних.

    Кожен рядок таблиці — один відгук з результатом аналізу тональності.

    Атрибути таблиці:
        id: Унікальний ідентифікатор, первинний ключ, автоінкремент.
        text: Текст відгуку англійською мовою.
        source: Звідки надійшов відгук — 'form', 'csv' або 'script'.
        sentiment: Результат аналізу — 'positive', 'negative', 'neutral'.
        score: Числова оцінка VADER compound від -1.0 до +1.0.
        created_at: Дата і час додавання відгуку в систему (UTC).
    """

    # Назва таблиці в БД
    __tablename__ = "feedbacks"

    # Первинний ключ — автоматично збільшується при кожному новому записі
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Текст відгуку — обов'язкове поле
    text: Mapped[str] = mapped_column(String, nullable=False)

    # Джерело відгуку — звідки він надійшов
    # Можливі значення: 'form', 'csv', 'script'
    source: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="form",
    )

    # Тональність — результат аналізу VADER
    # Можливі значення: 'positive', 'negative', 'neutral'
    sentiment: Mapped[str] = mapped_column(String, nullable=False)

    # Числова оцінка VADER compound від -1.0 до +1.0
    score: Mapped[float] = mapped_column(Float, nullable=False)

    # Час створення запису — встановлюється автоматично при збереженні
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        # default= викликається Python-стороною при створенні об'єкта
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        """Рядкове представлення об'єкта для зручного дебагу."""
        return (
            f"<Feedback id={self.id} "
            f"sentiment={self.sentiment!r} "
            f"score={self.score} "
            f"source={self.source!r}>"
        )
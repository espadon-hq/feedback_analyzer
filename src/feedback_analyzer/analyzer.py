"""Модуль аналізу тональності тексту за допомогою бібліотеки VADER."""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Створюємо єдиний екземпляр аналізатора для всього застосунку.
# Ініціалізація відбувається один раз при імпорті модуля —
# це уникає зайвих витрат пам'яті при кожному виклику analyze().
_analyzer = SentimentIntensityAnalyzer()

# Порогові значення compound score для визначення тональності.
# Значення взяті з офіційної документації VADER:
# >= 0.05  — позитивна
# <= -0.05 — негативна
# між ними — нейтральна
_POSITIVE_THRESHOLD = 0.05
_NEGATIVE_THRESHOLD = -0.05


def analyze(text: str) -> dict:
    """Аналізує тональність англійського тексту.

    Використовує VADER (Valence Aware Dictionary and sEntiment Reasoner) —
    бібліотеку, оптимізовану для коротких текстів, відгуків та соціальних мереж.

    Args:
        text: Вхідний текст для аналізу (англійська мова).

    Returns:
        Словник з двома ключами:
            - sentiment (str): 'positive', 'negative' або 'neutral'
            - score (float): числова оцінка від -1.0 до +1.0,
              округлена до 4 знаків після коми
    """
    # polarity_scores повертає словник з чотирма ключами:
    # 'pos', 'neg', 'neu' — частки відповідної тональності (сума = 1.0)
    # 'compound' — загальна нормалізована оцінка від -1.0 до +1.0
    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]

    # Визначаємо мітку тональності на основі порогових значень
    if compound >= _POSITIVE_THRESHOLD:
        sentiment = "positive"
    elif compound <= _NEGATIVE_THRESHOLD:
        sentiment = "negative"
    else:
        # Compound між -0.05 і +0.05 — текст не має чіткої тональності
        sentiment = "neutral"

    return {
        "sentiment": sentiment,
        # Округлюємо до 4 знаків для зручності відображення
        "score": round(compound, 4),
    }
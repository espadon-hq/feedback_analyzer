"""Тести для модуля analyzer.py — функція analyze()."""

from feedback_analyzer.analyzer import analyze


class TestAnalyzeReturnStructure:
    """Перевіряє структуру та типи значень, що повертає analyze()."""

    def test_returns_dict(self):
        """analyze() повинна повертати словник."""
        result = analyze("Great product!")
        assert isinstance(result, dict)

    def test_has_sentiment_key(self):
        """Результат повинен містити ключ 'sentiment'."""
        result = analyze("Great product!")
        assert "sentiment" in result

    def test_has_score_key(self):
        """Результат повинен містити ключ 'score'."""
        result = analyze("Great product!")
        assert "score" in result

    def test_score_is_float(self):
        """Значення 'score' повинно бути типу float."""
        result = analyze("Great product!")
        assert isinstance(result["score"], float)

    def test_score_in_valid_range(self):
        """Значення 'score' повинно знаходитись у діапазоні від -1.0 до +1.0."""
        result = analyze("Great product!")
        assert -1.0 <= result["score"] <= 1.0

    def test_sentiment_is_valid_label(self):
        """Значення 'sentiment' повинно бути одним з трьох допустимих."""
        result = analyze("Great product!")
        assert result["sentiment"] in ("positive", "negative", "neutral")


class TestAnalyzeSentimentLabels:
    """Перевіряє правильність визначення тональності для різних типів тексту."""

    def test_positive_texts(self, sample_texts):
        """Позитивні тексти повинні отримати мітку 'positive'."""
        for text in sample_texts["positive"]:
            result = analyze(text)
            assert result["sentiment"] == "positive", (
                f"Очікувалось 'positive', отримано '{result['sentiment']}' для: {text}"
            )

    def test_negative_texts(self, sample_texts):
        """Негативні тексти повинні отримати мітку 'negative'."""
        for text in sample_texts["negative"]:
            result = analyze(text)
            assert result["sentiment"] == "negative", (
                f"Очікувалось 'negative', отримано '{result['sentiment']}' для: {text}"
            )

    def test_neutral_texts(self, sample_texts):
        """Нейтральні тексти повинні отримати мітку 'neutral'."""
        for text in sample_texts["neutral"]:
            result = analyze(text)
            assert result["sentiment"] == "neutral", (
                f"Очікувалось 'neutral', отримано '{result['sentiment']}' для: {text}"
            )

    def test_positive_score_is_positive(self, sample_texts):
        """Позитивний текст повинен мати score >= 0.05."""
        for text in sample_texts["positive"]:
            assert analyze(text)["score"] >= 0.05

    def test_negative_score_is_negative(self, sample_texts):
        """Негативний текст повинен мати score <= -0.05."""
        for text in sample_texts["negative"]:
            assert analyze(text)["score"] <= -0.05


class TestAnalyzeEdgeCases:
    """Перевіряє граничні та нестандартні випадки вхідних даних."""

    def test_empty_string(self):
        """Порожній рядок повинен повертати 'neutral' зі score 0.0."""
        result = analyze("")
        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.0

    def test_single_positive_word(self):
        """Одне позитивне слово повинно визначатись як 'positive'."""
        assert analyze("excellent")["sentiment"] == "positive"

    def test_single_negative_word(self):
        """Одне негативне слово повинно визначатись як 'negative'."""
        assert analyze("terrible")["sentiment"] == "negative"

    def test_score_rounded_to_4_decimals(self):
        """Score повинен бути округлений до 4 знаків після коми."""
        result = analyze("This is a good product.")
        # Перевіряємо що кількість знаків після коми не перевищує 4
        decimal_part = str(result["score"]).split(".")[-1]
        assert len(decimal_part) <= 4

    def test_text_with_numbers(self):
        """Текст що містить числа повинен оброблятись без помилок."""
        result = analyze("Rated 5 out of 5, absolutely perfect!")
        assert result["sentiment"] in ("positive", "negative", "neutral")

    def test_long_text(self):
        """Довгий текст повинен оброблятись без помилок."""
        long_text = "Great product! " * 100
        result = analyze(long_text)
        assert result["sentiment"] == "positive"
"""Тести для модуля importer.py — функції get_columns() та load_texts()."""

import pytest

from feedback_analyzer.importer import get_columns, load_texts


class TestGetColumns:
    """Перевіряє функцію get_columns() — отримання назв колонок з CSV."""

    def test_returns_list(self, sample_csv):
        """get_columns() повинна повертати список."""
        result = get_columns(sample_csv)
        assert isinstance(result, list)

    def test_returns_correct_columns(self, sample_csv):
        """Повинна повертати правильні назви колонок зі стандартного CSV."""
        columns = get_columns(sample_csv)
        assert columns == ["text", "source"]

    def test_multiformat_contains_review_body(self, multiformat_csv):
        """Повинна знаходити колонку 'review_body' в Amazon-подібному форматі."""
        columns = get_columns(multiformat_csv)
        assert "review_body" in columns

    def test_multiformat_contains_rating(self, multiformat_csv):
        """Повинна знаходити колонку 'rating' в Amazon-подібному форматі."""
        columns = get_columns(multiformat_csv)
        assert "rating" in columns

    def test_returns_all_columns(self, multiformat_csv):
        """Повинна повертати всі колонки файлу."""
        # Amazon CSV має 3 колонки: review_body, rating, date
        columns = get_columns(multiformat_csv)
        assert len(columns) == 3


class TestLoadTexts:
    """Перевіряє функцію load_texts() — завантаження та очищення текстів."""

    def test_returns_list(self, sample_csv):
        """load_texts() повинна повертати список."""
        result = load_texts(sample_csv, "text")
        assert isinstance(result, list)

    def test_all_items_are_strings(self, sample_csv):
        """Всі елементи результату повинні бути рядками."""
        texts = load_texts(sample_csv, "text")
        assert all(isinstance(t, str) for t in texts)

    def test_skips_empty_rows(self, sample_csv):
        """Порожні рядки повинні бути виключені з результату."""
        texts = load_texts(sample_csv, "text")
        assert "" not in texts

    def test_skips_short_rows(self, sample_csv):
        """Рядки коротші за 3 символи повинні бути виключені."""
        texts = load_texts(sample_csv, "text")
        assert all(len(t) >= 3 for t in texts)

    def test_correct_valid_count(self, sample_csv):
        """З sample_csv повинно завантажитись рівно 3 валідні відгуки."""
        # sample_csv містить 5 рядків: 3 валідні, 1 порожній, 1 занадто короткий
        texts = load_texts(sample_csv, "text")
        assert len(texts) == 3

    def test_multiformat_correct_count(self, multiformat_csv):
        """З multiformat_csv повинно завантажитись рівно 2 відгуки."""
        texts = load_texts(multiformat_csv, "review_body")
        assert len(texts) == 2

    def test_invalid_column_raises_value_error(self, sample_csv):
        """Неіснуюча колонка повинна викликати ValueError."""
        with pytest.raises(ValueError):
            load_texts(sample_csv, "nonexistent_column")

    def test_error_message_contains_column_name(self, sample_csv):
        """Повідомлення помилки повинно містити назву неіснуючої колонки."""
        with pytest.raises(ValueError, match="nonexistent_column"):
            load_texts(sample_csv, "nonexistent_column")
"""
Тесты для билдеров клавиатур.

Проверяем, что кнопки имеют правильные тексты и callback_data.
"""

import pytest
from aiogram.types import InlineKeyboardMarkup

from src.bot.keyboards import get_main_menu, get_templates_menu, get_back_button
from src.bot.services import prompt_builder


# ---------------------------------------------------------------------------
# Главное меню
# ---------------------------------------------------------------------------

class TestMainMenu:
    """Проверка главного меню."""

    def test_returns_inline_keyboard(self):
        """Функция возвращает InlineKeyboardMarkup."""
        kb = get_main_menu()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_all_category_buttons(self):
        """В меню есть кнопки всех 4 категорий + кнопка улучшения."""
        kb = get_main_menu()
        texts = [btn.text for row in kb.inline_keyboard for btn in row]

        assert "📝 Текст" in texts
        assert "🎨 Изображение" in texts
        assert "💻 Код" in texts
        assert "🎭 Роль" in texts
        assert "✨ Улучшить мой промпт" in texts

    def test_category_callback_data(self):
        """Callback_data у категорий начинаются с 'category:'."""
        kb = get_main_menu()
        for row in kb.inline_keyboard:
            for btn in row:
                if btn.text in ("📝 Текст", "🎨 Изображение", "💻 Код", "🎭 Роль"):
                    assert btn.callback_data.startswith("category:")

    def test_improve_callback_data(self):
        """Кнопка улучшения имеет callback_data action:improve."""
        kb = get_main_menu()
        for row in kb.inline_keyboard:
            for btn in row:
                if "Улучшить" in btn.text:
                    assert btn.callback_data == "action:improve"


# ---------------------------------------------------------------------------
# Меню шаблонов
# ---------------------------------------------------------------------------

class TestTemplatesMenu:
    """Проверка меню выбора шаблона."""

    def test_returns_inline_keyboard(self):
        """Функция возвращает InlineKeyboardMarkup."""
        templates = prompt_builder.get_templates("text")
        kb = get_templates_menu("text", templates)
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_template_buttons(self):
        """В меню есть кнопки для каждого шаблона категории."""
        templates = prompt_builder.get_templates("text")
        kb = get_templates_menu("text", templates)
        texts = [btn.text for row in kb.inline_keyboard for btn in row]

        for tmpl in templates.values():
            assert tmpl["label"] in texts

    def test_template_callback_format(self):
        """Callback_data шаблона имеет формат template:category:key."""
        templates = prompt_builder.get_templates("text")
        kb = get_templates_menu("text", templates)
        for row in kb.inline_keyboard:
            for btn in row:
                if btn.callback_data.startswith("template:"):
                    parts = btn.callback_data.split(":")
                    assert len(parts) >= 3
                    assert parts[1] == "text"

    def test_has_back_button(self):
        """В меню есть кнопка 'Назад'."""
        templates = prompt_builder.get_templates("text")
        kb = get_templates_menu("text", templates)
        texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert "◀️ Назад" in texts

    def test_back_button_callback(self):
        """Кнопка 'Назад' имеет callback_data action:back."""
        templates = prompt_builder.get_templates("text")
        kb = get_templates_menu("text", templates)
        for row in kb.inline_keyboard:
            for btn in row:
                if "Назад" in btn.text:
                    assert btn.callback_data == "action:back"


# ---------------------------------------------------------------------------
# Кнопка назад (в главное меню)
# ---------------------------------------------------------------------------

class TestBackButton:
    """Проверка кнопки возврата в главное меню."""

    def test_returns_inline_keyboard(self):
        """Функция возвращает InlineKeyboardMarkup."""
        kb = get_back_button()
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_has_one_button(self):
        """Ровно одна кнопка."""
        kb = get_back_button()
        total_buttons = sum(len(row) for row in kb.inline_keyboard)
        assert total_buttons == 1

    def test_button_text(self):
        """Текст кнопки — '◀️ В главное меню'."""
        kb = get_back_button()
        btn = kb.inline_keyboard[0][0]
        assert btn.text == "◀️ В главное меню"

    def test_callback_data(self):
        """callback_data — action:main_menu."""
        kb = get_back_button()
        btn = kb.inline_keyboard[0][0]
        assert btn.callback_data == "action:main_menu"

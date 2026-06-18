"""
Тесты для PromptBuilder — загрузка шаблонов и сборка промптов.

PromptBuilder — изолированный сервис без зависимостей от aiogram,
поэтому все тесты синхронные и не требуют фикстур.
"""

import json
from pathlib import Path

import pytest

from src.bot.services.prompt_builder import PromptBuilder, prompt_builder

# Используем тот же путь, что и в продакшене
TEMPLATES_PATH = Path("src/bot/data/templates.json")


# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------

@pytest.fixture
def builder():
    """Свежий экземпляр PromptBuilder для каждого теста."""
    return PromptBuilder()


# ---------------------------------------------------------------------------
# Загрузка шаблонов
# ---------------------------------------------------------------------------

class TestLoadTemplates:
    """Проверяем, что JSON-файл читается и парсится корректно."""

    def test_templates_file_exists(self):
        """Файл шаблонов должен быть на месте (иначе тесты не имеют смысла)."""
        assert TEMPLATES_PATH.exists(), (
            f"Файл {TEMPLATES_PATH} не найден"
        )

    def test_templates_file_is_valid_json(self):
        """Файл должен быть валидным JSON."""
        with open(TEMPLATES_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert "categories" in data

    def test_categories_loaded(self, builder):
        """После инициализации должны быть загружены все категории."""
        categories = builder.get_categories()
        assert "text" in categories
        assert "image" in categories
        assert "code" in categories
        assert "role" in categories

    def test_category_has_required_fields(self, builder):
        """У каждой категории должны быть label, description и templates."""
        for cat_key, cat_value in builder.get_categories().items():
            assert "label" in cat_value, f"Категория {cat_key} без label"
            assert "description" in cat_value, (
                f"Категория {cat_key} без description"
            )
            assert "templates" in cat_value, (
                f"Категория {cat_key} без templates"
            )


# ---------------------------------------------------------------------------
# get_category / get_templates
# ---------------------------------------------------------------------------

class TestGetCategory:
    """Проверка методов доступа к категориям."""

    def test_get_existing_category(self, builder):
        """Существующая категория возвращается."""
        cat = builder.get_category("text")
        assert cat is not None
        assert cat["label"] == "📝 Текст"

    def test_get_missing_category(self, builder):
        """Несуществующая категория — None."""
        assert builder.get_category("nonexistent") is None


class TestGetTemplates:
    """Проверка получения шаблонов внутри категории."""

    def test_get_existing_templates(self, builder):
        """В категории 'text' есть минимум 3 шаблона."""
        templates = builder.get_templates("text")
        assert len(templates) >= 3

    def test_get_templates_missing_category(self, builder):
        """Для несуществующей категории — пустой словарь."""
        assert builder.get_templates("void") == {}

    def test_each_template_has_label_and_template(self, builder):
        """У каждого шаблона есть поля label и template."""
        for cat_key in builder.get_categories():
            templates = builder.get_templates(cat_key)
            for tmpl_key, tmpl_value in templates.items():
                assert "label" in tmpl_value, (
                    f"Шаблон {cat_key}/{tmpl_key} без label"
                )
                assert "template" in tmpl_value, (
                    f"Шаблон {cat_key}/{tmpl_key} без template"
                )


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------

class TestBuildPrompt:
    """Проверка сборки готового промпта из шаблона и параметров."""

    def test_build_article_prompt(self, builder):
        """Сборка промпта 'Статья' со всеми параметрами."""
        result = builder.build_prompt("text", "article", {
            "tone": "нейтральный",
            "topic": "ИИ",
            "length": "1000",
            "audience": "специалисты",
            "sections": "5",
        })
        assert result is not None
        assert "ИИ" in result
        assert "нейтральный" in result
        assert "1000" in result
        assert "специалисты" in result

    def test_build_email_prompt(self, builder):
        """Сборка промпта 'Письмо'."""
        result = builder.build_prompt("text", "email", {
            "tone": "официальный",
            "sender": "Иван",
            "recipient": "Петр",
            "topic": "встреча",
            "goal": "назначить дату",
        })
        assert result is not None
        assert "официальный" in result
        assert "Иван" in result
        assert "Петр" in result

    def test_build_image_prompt(self, builder):
        """Сборка промпта для изображения."""
        result = builder.build_prompt("image", "portrait", {
            "subject": "a cat",
            "style": "watercolor",
            "lighting": "soft",
            "camera": "close-up",
        })
        assert result is not None
        assert "a cat" in result
        assert "watercolor" in result
        assert "8k resolution" in result

    def test_build_code_prompt(self, builder):
        """Сборка промпта для кода."""
        result = builder.build_prompt("code", "function", {
            "language": "Python",
            "task": "parse a CSV file",
            "requirements": "use pandas",
        })
        assert result is not None
        assert "Python" in result
        assert "parse a CSV file" in result
        assert "pandas" in result

    def test_build_role_prompt(self, builder):
        """Сборка промпта с ролью."""
        result = builder.build_prompt("role", "expert", {
            "profession": "data scientist",
            "years": "10",
        })
        assert result is not None
        assert "data scientist" in result
        assert "10" in result

    def test_missing_required_param(self, builder):
        """Если не хватает обязательного параметра — None."""
        result = builder.build_prompt("text", "article", {
            "tone": "нейтральный",
            # Нет 'topic', 'length', 'audience', 'sections' — шаблон упадёт
        })
        assert result is None

    def test_nonexistent_template(self, builder):
        """Несуществующий шаблон — None."""
        result = builder.build_prompt("text", "nonexistent", {"tone": "x"})
        assert result is None

    def test_nonexistent_category(self, builder):
        """Несуществующая категория — None."""
        result = builder.build_prompt("void", "article", {"tone": "x"})
        assert result is None


# ---------------------------------------------------------------------------
# improve_prompt
# ---------------------------------------------------------------------------

class TestImprovePrompt:
    """Проверка функции улучшения промпта."""

    def test_improve_short_prompt(self, builder):
        """Улучшение короткого промпта — добавляются требования."""
        result = builder.improve_prompt("Напиши стих")
        assert result is not None
        assert "Напиши стих" in result
        assert "Дополнительные требования" in result
        assert "структурированно" in result

    def test_improve_strips_whitespace(self, builder):
        """Пробелы по краям удаляются, текст не дублируется."""
        result = builder.improve_prompt("  Привет  ")
        assert result.startswith("Привет")
        assert "  Привет  " not in result

    def test_improve_does_not_mutate_singleton(self, builder):
        """Проверка, что improve_prompt не меняет глобальный singleton."""
        # Берём текст из singleton
        original_improve = prompt_builder.improve_prompt("Тест")
        assert "Тест" in original_improve
        # И из свежего экземпляра — результат идентичен
        fresh = PromptBuilder()
        assert fresh.improve_prompt("Тест") == original_improve

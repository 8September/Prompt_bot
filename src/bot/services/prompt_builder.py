import json
from pathlib import Path

from src.bot.logger import logger


class PromptBuilder:
    """
    Загружает шаблоны из JSON и собирает готовые промпты.
    Один экземпляр на весь проект — шаблоны читаются один раз.
    """

    TEMPLATES_PATH = Path("src/bot/data/templates.json")

    def __init__(self) -> None:
        self._templates: dict = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Читает шаблоны из JSON файла при инициализации."""
        try:
            with open(self.TEMPLATES_PATH, encoding="utf-8") as f:
                data = json.load(f)
                self._templates = data.get("categories", {})
                logger.info(f"Шаблоны загружены: {list(self._templates.keys())}")
        except FileNotFoundError:
            logger.error(f"Файл шаблонов не найден: {self.TEMPLATES_PATH}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON шаблонов: {e}")

    def get_categories(self) -> dict:
        """Возвращает все категории."""
        return self._templates

    def get_category(self, category: str) -> dict | None:
        """Возвращает одну категорию по ключу."""
        return self._templates.get(category)

    def get_templates(self, category: str) -> dict:
        """Возвращает шаблоны внутри категории."""
        cat = self.get_category(category)
        if not cat:
            return {}
        return cat.get("templates", {})

    def build_prompt(
        self, category: str, template_key: str, params: dict
    ) -> str | None:
        """
        Собирает готовый промпт из шаблона и параметров пользователя.

        Args:
            category: ключ категории (text, image, code, role)
            template_key: ключ шаблона (article, portrait, ...)
            params: словарь значений для подстановки в шаблон

        Returns:
            Готовый промпт или None если шаблон не найден.
        """
        templates = self.get_templates(category)
        template = templates.get(template_key)

        if not template:
            logger.warning(f"Шаблон не найден: category={category}, key={template_key}")
            return None

        try:
            result = template["template"].format(**params)
            logger.info(f"Промпт собран: category={category}, template={template_key}")
            return result
        except KeyError as e:
            logger.error(f"Не хватает параметра для шаблона: {e}")
            return None

    def improve_prompt(self, original: str) -> str:
        """
        Улучшает промпт пользователя — добавляет структуру и детали.
        """
        improved = (
            f"{original.strip()}\n\n"
            "Дополнительные требования:\n"
            "- Отвечай структурированно, используй заголовки\n"
            "- Приводи конкретные примеры\n"
            "- Избегай общих фраз, будь точен\n"
            "- Если чего-то не знаешь — честно скажи об этом"
        )
        logger.info("Промпт улучшен пользователем")
        return improved

prompt_builder = PromptBuilder()

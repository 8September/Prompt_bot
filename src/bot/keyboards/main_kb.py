from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню — выбор категории промпта."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Текст", callback_data="category:text"),
        InlineKeyboardButton(text="🎨 Изображение", callback_data="category:image"),
    )
    builder.row(
        InlineKeyboardButton(text="💻 Код", callback_data="category:code"),
        InlineKeyboardButton(text="🎭 Роль", callback_data="category:role"),
    )
    builder.row(
        InlineKeyboardButton(
            text="✨ Улучшить мой промпт", callback_data="action:improve"
        ),
    )
    return builder.as_markup()


def get_templates_menu(category: str, templates: dict) -> InlineKeyboardMarkup:
    """Меню шаблонов внутри категории."""
    builder = InlineKeyboardBuilder()
    for key, value in templates.items():
        builder.row(
            InlineKeyboardButton(
                text=value["label"],
                callback_data=f"template:{category}:{key}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="action:back"),
    )
    return builder.as_markup()


def get_back_button() -> InlineKeyboardMarkup:
    """Кнопка назад — возврат в главное меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="◀️ В главное меню", callback_data="action:main_menu"
        ),
    )
    return builder.as_markup()


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Основная reply-клавиатура — быстрый доступ без ввода команд."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Текст"),
                KeyboardButton(text="🎨 Изображение"),
            ],
            [
                KeyboardButton(text="💻 Код"),
                KeyboardButton(text="🎭 Роль"),
            ],
            [
                KeyboardButton(text="✨ Улучшить"),
                KeyboardButton(text="❓ Помощь"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие…",
    )

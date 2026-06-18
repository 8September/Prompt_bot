from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message

from src.bot.keyboards import get_main_menu, get_templates_menu, get_main_reply_keyboard
from src.bot.logger import logger
from src.bot.services import prompt_builder

from src.bot.handlers.prompts import PromptStates
from src.bot.handlers.improve import ImproveStates

router = Router(name="start")

# Список текстов reply-кнопок — используется в фильтре хендлера
REPLY_BUTTONS = {
    "📝 Текст",
    "🎨 Изображение",
    "💻 Код",
    "🎭 Роль",
    "✨ Улучшить",
    "❓ Помощь",
}


class StartHandler:
    """Обработчик команд /start и /help."""

    @staticmethod
    @router.message(Command("start"))
    async def handle_start(message: Message) -> None:
        try:
            await message.answer(
                text=(
                    "👋 Привет! Я помогу тебе составить промпт для нейросети.\n\n"
                    "Выбери категорию:"
                ),
                reply_markup=get_main_menu(),
            )
            # Отправляем reply-клавиатуру для быстрого доступа без команд
            await message.answer(
                text="👇 Используй кнопки ниже для быстрого выбора:",
                reply_markup=get_main_reply_keyboard(),
            )
            logger.info(f"Отправлено главное меню | user_id={message.from_user.id}")
        except Exception as e:
            logger.error(f"Ошибка /start | user_id={message.from_user.id} | {e}")

    @staticmethod
    @router.message(Command("help"))
    async def handle_help(message: Message) -> None:
        try:
            await message.answer(
                text=(
                    "ℹ️ Как пользоваться ботом:\n\n"
                    "1️⃣ Выбери категорию промпта\n"
                    "2️⃣ Выбери шаблон\n"
                    "3️⃣ Ответь на вопросы бота\n"
                    "4️⃣ Получи готовый промпт\n\n"
                    "✨ Или выбери «Улучшить мой промпт» и отправь свой вариант."
                ),
            )
            logger.info(f"Отправлена помощь | user_id={message.from_user.id}")
        except Exception as e:
            logger.error(f"Ошибка /help | user_id={message.from_user.id} | {e}")

    # ------------------------------------------------------------------
    # Reply-клавиатура — быстрые кнопки без набора команд
    # ------------------------------------------------------------------

    @staticmethod
    @router.message(F.text.in_(REPLY_BUTTONS), default_state)
    async def handle_reply_button(message: Message, state: FSMContext) -> None:
        """
        Обрабатывает нажатия reply-кнопок (только когда нет активного FSM-состояния).

        Категории → показываем inline-меню шаблонов.
        ✨ Улучшить → запускаем improve-flow.
        ❓ Помощь → показываем справку.
        """
        text = message.text.strip()
        try:
            # ------ Категории ------
            if text in ("📝 Текст", "🎨 Изображение", "💻 Код", "🎭 Роль"):
                CATEGORY_MAP = {
                    "📝 Текст": "text",
                    "🎨 Изображение": "image",
                    "💻 Код": "code",
                    "🎭 Роль": "role",
                }
                category = CATEGORY_MAP[text]
                templates = prompt_builder.get_templates(category)

                if not templates:
                    await message.answer("❌ Шаблоны не найдены")
                    return

                cat_info = prompt_builder.get_category(category)
                await state.update_data(category=category)
                await state.set_state(PromptStates.choosing_template)

                await message.answer(
                    text=f"{cat_info['label']}\n{cat_info['description']}\n\nВыбери шаблон:",
                    reply_markup=get_templates_menu(category, templates),
                )
                logger.info(
                    f"Reply-кнопка: категория={category} | user_id={message.from_user.id}"
                )

            # ------ Улучшить промпт ------
            elif text == "✨ Улучшить":
                await state.set_state(ImproveStates.waiting_for_prompt)
                await message.answer(
                    text=(
                        "✏️ Отправь мне свой промпт — я его улучшу.\n\n"
                        "Например:\n"
                        "<i>напиши статью про искусственный интеллект</i>"
                    ),
                    parse_mode="HTML",
                    reply_markup=get_main_menu(),
                )
                logger.info(
                    f"Reply-кнопка: улучшение | user_id={message.from_user.id}"
                )

            # ------ Помощь ------
            elif text == "❓ Помощь":
                await message.answer(
                    text=(
                        "ℹ️ Как пользоваться ботом:\n\n"
                        "1️⃣ Выбери категорию промпта\n"
                        "2️⃣ Выбери шаблон\n"
                        "3️⃣ Ответь на вопросы бота\n"
                        "4️⃣ Получи готовый промпт\n\n"
                        "✨ Или выбери «Улучшить мой промпт» и отправь свой вариант."
                    ),
                )

        except Exception as e:
            logger.error(f"Ошибка reply-кнопки | text={text} | {e}")
            await message.answer("❌ Произошла ошибка. Попробуй снова.")

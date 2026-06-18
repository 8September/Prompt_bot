from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.keyboards import get_main_menu
from src.bot.logger import logger

router = Router(name="start")


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

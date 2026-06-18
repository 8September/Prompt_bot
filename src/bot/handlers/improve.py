from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import get_main_menu
from src.bot.logger import logger
from src.bot.services import prompt_builder

router = Router(name="improve")


class ImproveStates(StatesGroup):
    """Состояния диалога улучшения промпта."""

    waiting_for_prompt = State()  # ждём промпт от пользователя


class ImproveHandler:
    """Обработчик улучшения пользовательского промпта."""

    @staticmethod
    @router.callback_query(F.data == "action:improve")
    async def handle_improve_start(callback: CallbackQuery, state: FSMContext) -> None:
        """Пользователь нажал 'Улучшить промпт' — просим прислать текст."""
        try:
            await state.set_state(ImproveStates.waiting_for_prompt)
            await callback.message.edit_text(
                text=(
                    "✏️ Отправь мне свой промпт — я его улучшу.\n\n"
                    "Например:\n"
                    "<i>напиши статью про искусственный интеллект</i>"
                ),
                parse_mode="HTML",
                reply_markup=get_main_menu(),
            )
            logger.info(f"Запрос улучшения промпта | user_id={callback.from_user.id}")
            await callback.answer()
        except Exception as e:
            logger.error(f"Ошибка запуска улучшения | {e}")
            await callback.answer("Произошла ошибка", show_alert=True)

    @staticmethod
    @router.message(ImproveStates.waiting_for_prompt)
    async def handle_improve_input(message: Message, state: FSMContext) -> None:
        """Пользователь прислал промпт — улучшаем и отправляем."""
        try:
            original = message.text.strip()

            if len(original) < 5:
                await message.answer("❌ Промпт слишком короткий. Напиши подробнее.")
                return

            improved = prompt_builder.improve_prompt(original)
            await state.clear()

            await message.answer(
                text=(f"✅ Улучшенный промпт:\n\n" f"<code>{improved}</code>"),
                parse_mode="HTML",
                reply_markup=get_main_menu(),
            )
            logger.info(f"Промпт улучшен и отправлен | user_id={message.from_user.id}")
        except Exception as e:
            logger.error(f"Ошибка улучшения промпта | {e}")
            await message.answer(
                "❌ Произошла ошибка. Попробуй снова.",
                reply_markup=get_main_menu(),
            )

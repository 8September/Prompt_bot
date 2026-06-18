from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import get_main_menu, get_templates_menu, get_back_button
from src.bot.logger import logger
from src.bot.services import prompt_builder

router = Router(name="prompts")


class PromptStates(StatesGroup):
    """Состояния диалога построения промпта."""

    choosing_template = State()  # пользователь выбирает шаблон
    filling_params = State()  # пользователь отвечает на вопросы
    done = State()  # промпт готов


class PromptsHandler:
    """Обработчик выбора категорий, шаблонов и сборки промпта."""

    @staticmethod
    @router.callback_query(F.data.startswith("category:"))
    async def handle_category(callback: CallbackQuery, state: FSMContext) -> None:
        """Пользователь выбрал категорию — показываем шаблоны."""
        try:
            category = callback.data.split(":")[1]
            templates = prompt_builder.get_templates(category)

            if not templates:
                await callback.answer("Шаблоны не найдены", show_alert=True)
                return

            cat_info = prompt_builder.get_category(category)
            await state.update_data(category=category)
            await state.set_state(PromptStates.choosing_template)

            await callback.message.edit_text(
                text=f"{cat_info['label']}\n{cat_info['description']}\n\nВыбери шаблон:",
                reply_markup=get_templates_menu(category, templates),
            )
            logger.info(
                f"Выбрана категория={category} | user_id={callback.from_user.id}"
            )
            await callback.answer()
        except Exception as e:
            logger.error(f"Ошибка выбора категории | {e}")
            await callback.answer("Произошла ошибка", show_alert=True)

    @staticmethod
    @router.callback_query(F.data.startswith("template:"))
    async def handle_template(callback: CallbackQuery, state: FSMContext) -> None:
        """Пользователь выбрал шаблон — просим ввести тему."""
        try:
            _, category, template_key = callback.data.split(":")
            await state.update_data(
                category=category,
                template_key=template_key,
                params={},
            )
            await state.set_state(PromptStates.filling_params)

            await callback.message.edit_text(
                text="✏️ Введи тему или главный предмет промпта:",
                reply_markup=get_back_button(),
            )
            logger.info(
                f"Выбран шаблон={template_key} | user_id={callback.from_user.id}"
            )
            await callback.answer()
        except Exception as e:
            logger.error(f"Ошибка выбора шаблона | {e}")
            await callback.answer("Произошла ошибка", show_alert=True)

    @staticmethod
    @router.message(PromptStates.filling_params)
    async def handle_param_input(message: Message, state: FSMContext) -> None:
        """Пользователь ввёл параметр — собираем промпт."""
        try:
            data = await state.get_data()
            params = data.get("params", {})

            # Подставляем введённый текст как основной параметр
            params["topic"] = message.text
            params.setdefault("tone", "профессиональный")
            params.setdefault("length", "500")
            params.setdefault("audience", "широкая аудитория")
            params.setdefault("sections", "3")
            params.setdefault("subject", message.text)
            params.setdefault("style", "realistic")
            params.setdefault("lighting", "natural")
            params.setdefault("camera", "medium")
            params.setdefault("scene", message.text)
            params.setdefault("time_of_day", "golden hour")
            params.setdefault("weather", "clear")
            params.setdefault("art_style", "photorealistic")
            params.setdefault("language", "Python")
            params.setdefault("task", message.text)
            params.setdefault("requirements", "чистый читаемый код")
            params.setdefault("code", message.text)
            params.setdefault("profession", message.text)
            params.setdefault("years", "10")
            params.setdefault("sender", "отправитель")
            params.setdefault("recipient", "получатель")
            params.setdefault("goal", message.text)
            params.setdefault("text", message.text)
            params.setdefault("level", "начинающий")

            result = prompt_builder.build_prompt(
                category=data["category"],
                template_key=data["template_key"],
                params=params,
            )

            if not result:
                await message.answer(
                    "❌ Не удалось собрать промпт. Попробуй снова.",
                    reply_markup=get_main_menu(),
                )
                return

            await state.set_state(PromptStates.done)
            await message.answer(
                text=f"✅ Готовый промпт:\n\n<code>{result}</code>",
                parse_mode="HTML",
                reply_markup=get_main_menu(),
            )
            logger.info(f"Промпт отправлен | user_id={message.from_user.id}")
        except Exception as e:
            logger.error(f"Ошибка сборки промпта | {e}")
            await message.answer("Произошла ошибка. Попробуй снова.")

    @staticmethod
    @router.callback_query(F.data == "action:back")
    async def handle_back(callback: CallbackQuery, state: FSMContext) -> None:
        """Кнопка Назад — возврат к выбору шаблонов."""
        try:
            data = await state.get_data()
            category = data.get("category")

            if category:
                templates = prompt_builder.get_templates(category)
                cat_info = prompt_builder.get_category(category)
                await state.set_state(PromptStates.choosing_template)
                await callback.message.edit_text(
                    text=f"{cat_info['label']}\nВыбери шаблон:",
                    reply_markup=get_templates_menu(category, templates),
                )
            else:
                await state.clear()
                await callback.message.edit_text(
                    text="Выбери категорию:",
                    reply_markup=get_main_menu(),
                )
            await callback.answer()
        except Exception as e:
            logger.error(f"Ошибка кнопки назад | {e}")
            await callback.answer("Произошла ошибка", show_alert=True)

    @staticmethod
    @router.callback_query(F.data == "action:main_menu")
    async def handle_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
        """Возврат в главное меню."""
        try:
            await state.clear()
            await callback.message.edit_text(
                text="Выбери категорию:",
                reply_markup=get_main_menu(),
            )
            await callback.answer()
        except Exception as e:
            logger.error(f"Ошибка возврата в меню | {e}")
            await callback.answer("Произошла ошибка", show_alert=True)

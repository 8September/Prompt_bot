"""
Тесты для хендлеров aiogram.

Используем реальный Dispatcher с MemoryStorage и делаем update-ы
через dp.feed_update(). Telegram API не вызывается — у Bot замокана сессия.

Как работают вызовы в aiogram 3.x:
  handler вызывает await message.answer(text=..., reply_markup=...)
  → создаётся SendMessage(...).as_(bot)
  → await вызывает Bot.__call__(send_msg)
  → Bot.__call__ вызывает await session(bot, method, timeout=None)

Поэтому все проверки смотрят на mock_bot.session.call_args,
а не на mock_bot.send_message / edit_message_text / answer_callback_query.
"""

from aiogram.methods import (
    AnswerCallbackQuery,
    EditMessageText,
    SendMessage,
)

from tests.conftest import feed, make_update_callback, make_update_message


# ---------------------------------------------------------------------------
# Утилита — извлекаем Telegram-метод из последнего вызова сессии
# ---------------------------------------------------------------------------

def _last_method(mock_bot):
    """Вернуть Telegram-метод из последнего вызова bot.session()."""
    return mock_bot.session.call_args[0][1]


def _method_of_type(mock_bot, method_type):
    """
    Найти первый вызов session() с методом указанного типа.

    Нужно, потому что ``callback.answer()`` вызывается
    **после** ``callback.message.edit_text()``, а нас интересует
    результат ``edit_text``, а не последний вызов сессии.
    """
    for call_args in mock_bot.session.call_args_list:
        method = call_args[0][1]
        if isinstance(method, method_type):
            return method
    return None


def _last_text(mock_bot) -> str:
    """Вернуть text из последнего вызова bot.session()."""
    return _last_method(mock_bot).text


# ===================================================================
# /start и /help
# ===================================================================

class TestStartHandler:
    """Команды /start и /help."""

    async def test_start_returns_main_menu(self, dp, mock_bot):
        """После /start бот отвечает с главным меню и reply-клавиатурой."""
        await feed(dp, mock_bot,
            make_update_message(text="/start"),
        )

        assert mock_bot.session.called
        # Первый SendMessage — приветствие с inline-клавиатурой
        method = _method_of_type(mock_bot, SendMessage)
        assert method is not None
        assert "Привет" in method.text
        assert method.reply_markup is not None
        # Второй вызов — reply-клавиатура (отдельное сообщение)
        assert mock_bot.session.call_count >= 2

    async def test_help_returns_info(self, dp, mock_bot):
        """После /help бот отправляет справку."""
        await feed(dp, mock_bot,
            make_update_message(text="/help"),
        )

        assert mock_bot.session.called
        method = _last_method(mock_bot)
        assert isinstance(method, SendMessage)
        assert "Как пользоваться" in method.text

    async def test_unknown_command(self, dp, mock_bot):
        """Неизвестная команда не вызывает ни один хендлер (session не вызван)."""
        await feed(dp, mock_bot,
            make_update_message(text="/unknown"),
        )

        assert not mock_bot.session.called


# ===================================================================
# Категории и шаблоны
# ===================================================================

class TestCategorySelection:
    """Выбор категории из главного меню."""

    async def test_select_text_category(self, dp, mock_bot):
        """При выборе категории 'text' показываются шаблоны."""
        await feed(dp, mock_bot,
            make_update_callback(data="category:text"),
        )

        assert mock_bot.session.called
        method = _method_of_type(mock_bot, EditMessageText)
        assert method is not None
        assert "Текст" in method.text
        assert "Выбери шаблон" in method.text

    async def test_select_image_category(self, dp, mock_bot):
        """При выборе категории 'image'."""
        await feed(dp, mock_bot,
            make_update_callback(data="category:image"),
        )

        method = _method_of_type(mock_bot, EditMessageText)
        assert method is not None
        assert "Изображение" in method.text

    async def test_select_code_category(self, dp, mock_bot):
        """При выборе категории 'code'."""
        await feed(dp, mock_bot,
            make_update_callback(data="category:code"),
        )

        method = _method_of_type(mock_bot, EditMessageText)
        assert method is not None
        assert "Код" in method.text

    async def test_select_role_category(self, dp, mock_bot):
        """При выборе категории 'role'."""
        await feed(dp, mock_bot,
            make_update_callback(data="category:role"),
        )

        method = _method_of_type(mock_bot, EditMessageText)
        assert method is not None
        assert "Роль" in method.text

    async def test_select_nonexistent_category(self, dp, mock_bot):
        """Несуществующая категория — алерт об ошибке."""
        await feed(dp, mock_bot,
            make_update_callback(data="category:void"),
        )

        assert mock_bot.session.called
        method = _last_method(mock_bot)
        assert isinstance(method, AnswerCallbackQuery)
        assert "Шаблоны не найдены" in method.text
        assert method.show_alert is True


class TestTemplateSelection:
    """Выбор шаблона внутри категории."""

    async def test_select_template_starts_input(self, dp, mock_bot):
        """После выбора шаблона бот просит ввести тему."""
        # Сначала выбираем категорию
        await feed(dp, mock_bot,
            make_update_callback(data="category:text"),
        )
        mock_bot.session.reset_mock()

        # Потом шаблон
        await feed(dp, mock_bot,
            make_update_callback(data="template:text:article"),
        )

        assert mock_bot.session.called
        method = _method_of_type(mock_bot, EditMessageText)
        assert method is not None
        assert "Введи тему" in method.text


# ===================================================================
# Полный цикл генерации промпта
# ===================================================================

class TestFullPromptFlow:
    """От выбора категории до готового промпта."""

    async def test_build_article_prompt(self, dp, mock_bot):
        """Полный цикл: текст → статья → ввод темы → промпт."""
        # Шаг 1: категория text
        await feed(dp, mock_bot,
            make_update_callback(data="category:text"),
        )
        mock_bot.session.reset_mock()

        # Шаг 2: шаблон article
        await feed(dp, mock_bot,
            make_update_callback(data="template:text:article"),
        )
        mock_bot.session.reset_mock()

        # Шаг 3: вводим тему
        await feed(dp, mock_bot,
            make_update_message(text="Искусственный интеллект"),
        )

        # Проверяем итоговый промпт
        assert mock_bot.session.called
        method = _last_method(mock_bot)
        assert isinstance(method, SendMessage)
        assert "Готовый промпт" in method.text
        assert "Искусственный интеллект" in method.text
        assert "профессиональный" in method.text  # тон по умолчанию
        assert method.parse_mode == "HTML"

    async def test_build_image_prompt(self, dp, mock_bot):
        """Полный цикл для изображения."""
        await feed(dp, mock_bot,
            make_update_callback(data="category:image"),
        )
        mock_bot.session.reset_mock()
        await feed(dp, mock_bot,
            make_update_callback(data="template:image:portrait"),
        )
        mock_bot.session.reset_mock()
        await feed(dp, mock_bot,
            make_update_message(text="a beautiful landscape"),
        )

        assert mock_bot.session.called
        method = _last_method(mock_bot)
        assert isinstance(method, SendMessage)
        assert "Готовый промпт" in method.text
        assert "a beautiful landscape" in method.text


# ===================================================================
# Кнопки навигации
# ===================================================================

class TestNavigation:
    """Кнопки Назад и В главное меню."""

    async def test_back_from_template_to_category(self, dp, mock_bot):
        """'Назад' в меню шаблонов возвращает к категории."""
        # Заходим в категорию
        await feed(dp, mock_bot,
            make_update_callback(data="category:text"),
        )
        mock_bot.session.reset_mock()

        # Нажимаем "Назад"
        await feed(dp, mock_bot,
            make_update_callback(data="action:back"),
        )

        assert mock_bot.session.called
        method = _method_of_type(mock_bot, EditMessageText)
        assert method is not None
        assert "Текст" in method.text
        assert "Выбери шаблон" in method.text

    async def test_main_menu_clears_state(self, dp, mock_bot):
        """'В главное меню' очищает состояние FSM."""
        # Сначала заходим в категорию
        await feed(dp, mock_bot,
            make_update_callback(data="category:text"),
        )
        mock_bot.session.reset_mock()

        # Нажимаем "В главное меню"
        await feed(dp, mock_bot,
            make_update_callback(data="action:main_menu"),
        )

        assert mock_bot.session.called
        method = _method_of_type(mock_bot, EditMessageText)
        assert method is not None
        assert "Выбери категорию" in method.text


# ===================================================================
# Улучшение промпта
# ===================================================================

class TestImproveFlow:
    """Функция улучшения промпта."""

    async def test_improve_start(self, dp, mock_bot):
        """Нажатие 'Улучшить промпт' переключает в режим ожидания текста."""
        await feed(dp, mock_bot,
            make_update_callback(data="action:improve"),
        )

        assert mock_bot.session.called
        method = _method_of_type(mock_bot, EditMessageText)
        assert method is not None
        assert "Отправь мне свой промпт" in method.text

    async def test_improve_input(self, dp, mock_bot):
        """Отправка промпта → улучшенная версия."""
        # Начинаем улучшение
        await feed(dp, mock_bot,
            make_update_callback(data="action:improve"),
        )
        mock_bot.session.reset_mock()

        # Отправляем промпт
        await feed(dp, mock_bot,
            make_update_message(text="Напиши статью про Python"),
        )

        assert mock_bot.session.called
        method = _last_method(mock_bot)
        assert isinstance(method, SendMessage)
        assert "Улучшенный промпт" in method.text
        assert "Напиши статью про Python" in method.text
        assert "Дополнительные требования" in method.text
        assert "структурированно" in method.text
        assert method.parse_mode == "HTML"

    async def test_improve_short_prompt(self, dp, mock_bot):
        """Очень короткий промпт (<5 символов) отклоняется."""
        # Начинаем улучшение
        await feed(dp, mock_bot,
            make_update_callback(data="action:improve"),
        )
        mock_bot.session.reset_mock()

        # Отправляем короткий промпт
        await feed(dp, mock_bot,
            make_update_message(text="При"),
        )

        assert mock_bot.session.called
        method = _last_method(mock_bot)
        assert isinstance(method, SendMessage)
        assert "слишком короткий" in method.text


# ===================================================================
# Edge cases
# ===================================================================

class TestEdgeCases:
    """Граничные случаи."""

    async def test_prompt_after_improve_differs_from_original(self, dp, mock_bot):
        """Улучшенный промпт длиннее исходного."""
        await feed(dp, mock_bot,
            make_update_callback(data="action:improve"),
        )
        mock_bot.session.reset_mock()

        original = "Напиши стихотворение"
        await feed(dp, mock_bot,
            make_update_message(text=original),
        )

        text = _last_text(mock_bot)
        assert len(text) > len(original)

    async def test_callback_without_state_handles_gracefully(self, dp, mock_bot):
        """callback без состояния не падает."""
        await feed(dp, mock_bot,
            make_update_callback(data="action:main_menu"),
        )

        assert mock_bot.session.called
        method = _method_of_type(mock_bot, EditMessageText)
        assert method is not None
        assert "Выбери категорию" in method.text

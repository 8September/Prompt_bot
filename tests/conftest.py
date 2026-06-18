"""
Общие фикстуры для всех тестов.

Перед запуском тестов гарантирует, что BOT_TOKEN установлен,
чтобы src.bot.config не упал при импорте.
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    Chat,
    Message,
    Update,
    User,
)

# Гарантируем наличие BOT_TOKEN в окружении до импорта src.bot.config
# Токен должен проходить aiogram.utils.token.validate_token: ^\d+:[a-zA-Z0-9_-]{35,}$
os.environ.setdefault("BOT_TOKEN", "1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
os.environ.setdefault("LOG_LEVEL", "CRITICAL")
os.environ.setdefault("LOG_FILE", "logs/test_bot.log")


@pytest.fixture(autouse=True)
def _mock_logger(monkeypatch):
    """Заглушка для логгера — не пишем в файлы и консоль во время тестов."""
    import logging
    import sys

    import src.bot.services  # noqa: F401 — гарантируем загрузку пакета

    fake = logging.getLogger("test")
    fake.addHandler(logging.NullHandler())
    monkeypatch.setattr("src.bot.logger.logger", fake)
    monkeypatch.setattr("src.bot.middlewares.logging_middleware.logger", fake)
    monkeypatch.setattr("src.bot.handlers.start.logger", fake)
    monkeypatch.setattr("src.bot.handlers.prompts.logger", fake)
    monkeypatch.setattr("src.bot.handlers.improve.logger", fake)

    # Обращение через sys.modules, чтобы обойти shadowing
    # из-за from … import prompt_builder в __init__.py
    _prompt_builder_mod = sys.modules.get("src.bot.services.prompt_builder")
    if _prompt_builder_mod is not None:
        monkeypatch.setattr(_prompt_builder_mod, "logger", fake)


@pytest.fixture
def mock_bot():
    """
    Бот с замоканной сессией — не ходит в Telegram API.

    Используем реальный ``aiogram.Bot`` с валидным (но фейковым) токеном,
    а его ``.session`` подменяем на AsyncMock.
    В aiogram 3.x ``message.answer()`` внутри вызывает
    ``Bot.__call__(SendMessage(...))`` → ``session(bot, method)``.
    """
    bot = Bot(token="1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    bot.session = AsyncMock()
    bot.session.close = AsyncMock()
    return bot


@pytest.fixture
def dp():
    """Диспетчер со всеми роутерами — как в продакшене.

    Роутеры — синглтоны, поэтому перед каждым тестом сбрасываем им
    родительскую связь через приватный ``_parent_router``.
    """
    from src.bot.handlers import improve_router, prompts_router, start_router

    for r in (start_router, prompts_router, improve_router):
        r._parent_router = None

    _dp = Dispatcher(storage=MemoryStorage())
    _dp.include_router(start_router)
    _dp.include_router(prompts_router)
    _dp.include_router(improve_router)
    return _dp


# ---------------------------------------------------------------------------
# Helpers для создания объектов Telegram
# ---------------------------------------------------------------------------

def _user(user_id: int = 123, username: str = "testuser") -> User:
    return User(id=user_id, is_bot=False, first_name="Test", username=username)


def _chat(chat_id: int = 456) -> Chat:
    return Chat(id=chat_id, type="private")


def make_message(
    text: str | None = None,
    user_id: int = 123,
    chat_id: int = 456,
    message_id: int = 1,
) -> Message:
    """Создаёт Message с минимальным набором полей."""
    return Message(
        message_id=message_id,
        date=datetime.now(),
        text=text,
        from_user=_user(user_id=user_id),
        chat=_chat(chat_id=chat_id),
        sender_chat=None,
        is_topic_message=False,
    )


def make_callback(
    data: str,
    message_text: str | None = "some text",
    user_id: int = 123,
    chat_id: int = 456,
) -> CallbackQuery:
    """Создаёт CallbackQuery с минимальным набором полей."""
    msg = make_message(text=message_text, user_id=user_id, chat_id=chat_id)
    return CallbackQuery(
        id="cb1",
        from_user=_user(user_id=user_id),
        chat_instance="instance1",
        data=data,
        message=msg,
    )


def make_update_message(
    text: str | None = None,
    user_id: int = 123,
    chat_id: int = 456,
) -> Update:
    """Создаёт Update, содержащий входящее сообщение."""
    return Update(
        update_id=1,
        message=make_message(text=text, user_id=user_id, chat_id=chat_id),
    )


def make_update_callback(
    data: str,
    message_text: str | None = "some text",
    user_id: int = 123,
    chat_id: int = 456,
) -> Update:
    """Создаёт Update, содержащий callback query."""
    cb = make_callback(
        data=data, message_text=message_text, user_id=user_id, chat_id=chat_id
    )
    return Update(update_id=2, callback_query=cb)


def feed(dp, mock_bot, update):
    """
    feed_update + автоматическая установка ``_bot`` на Message.

    aiogram 3.x не выставляет ``_bot`` на объектах Message/CallbackQuery
    при вызове feed_update, поэтому делаем это вручную.
    """
    if update.message is not None:
        update.message._bot = mock_bot
    if update.callback_query is not None:
        update.callback_query.message._bot = mock_bot
    return dp.feed_update(bot=mock_bot, update=update)


# ---------------------------------------------------------------------------
# Сброс роутеров-синглтонов
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_routers():
    """
    Сбрасываем ``_parent_router`` у синглтонов-роутеров после каждого теста.

    Без этого тесты, создающие Dispatcher с ``include_router()``,
    упадут с RuntimeError: Router is already attached.
    """
    from src.bot.handlers import improve_router, prompts_router, start_router

    for r in (start_router, prompts_router, improve_router):
        r._parent_router = None

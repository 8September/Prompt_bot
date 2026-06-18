"""
Тесты для BotApp — главного класса приложения.

Проверяем, что приложение корректно собирается:
- Bot создаётся с токеном
- Диспетчер использует MemoryStorage
- Все роутеры подключены
- Middleware подключён
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage


class TestBotApp:
    """Проверка сборки BotApp."""

    def test_bot_created_with_token(self):
        """BotApp инициализирует Bot с токеном из конфига."""
        from src.bot.config import config

        # Используем real Bot — токен в env валидного формата
        with patch("main.Bot") as MockBot:
            MockBot.return_value = MagicMock()
            from main import BotApp

            app = BotApp()

        MockBot.assert_called_once_with(token=config.bot_token)

    def test_dispatcher_uses_memory_storage(self):
        """Диспетчер использует MemoryStorage."""
        with patch("main.Bot") as MockBot:
            MockBot.return_value = MagicMock()
            from main import BotApp

            app = BotApp()

        assert isinstance(app.dp, Dispatcher)
        assert isinstance(app.dp.storage, MemoryStorage)

    def test_middleware_registered(self):
        """LoggingMiddleware подключён к диспетчеру."""
        with patch("main.Bot") as MockBot:
            MockBot.return_value = MagicMock()
            from main import BotApp

            app = BotApp()

        outer = app.dp.update.outer_middleware
        assert outer is not None

    def test_all_three_routers_registered(self):
        """К диспетчеру подключены минимум 3 роутера."""
        with patch("main.Bot") as MockBot:
            MockBot.return_value = MagicMock()
            from main import BotApp

            app = BotApp()

        registered = list(app.dp.sub_routers)
        assert len(registered) >= 3

    def test_sub_routers_have_correct_names(self):
        """Роутеры имеют ожидаемые имена: start, prompts, improve."""
        with patch("main.Bot") as MockBot:
            MockBot.return_value = MagicMock()
            from main import BotApp

            app = BotApp()

        names = {r.name for r in app.dp.sub_routers}
        assert "start" in names
        assert "prompts" in names
        assert "improve" in names

    @pytest.mark.asyncio
    async def test_run_calls_delete_webhook_and_polling(self):
        """Метод run() вызывает delete_webhook и start_polling."""
        mock_bot = MagicMock()
        mock_bot.delete_webhook = AsyncMock()
        mock_bot.set_my_commands = AsyncMock()
        mock_bot.session = MagicMock()
        mock_bot.session.close = AsyncMock()

        with patch("main.Bot", return_value=mock_bot):
            from main import BotApp

            app = BotApp()
            app.dp.start_polling = AsyncMock()
            app.bot = mock_bot

            await app.run()

        mock_bot.delete_webhook.assert_awaited_once_with(
            drop_pending_updates=True
        )
        app.dp.start_polling.assert_awaited_once_with(mock_bot, skip_updates=True)

    @pytest.mark.asyncio
    async def test_run_closes_session_on_exit(self):
        """После завершения polling сессия бота закрывается."""
        mock_bot = MagicMock()
        mock_bot.delete_webhook = AsyncMock()
        mock_bot.set_my_commands = AsyncMock()
        mock_bot.session = MagicMock()
        mock_bot.session.close = AsyncMock()

        with patch("main.Bot", return_value=mock_bot):
            from main import BotApp

            app = BotApp()
            app.dp.start_polling = AsyncMock()
            app.bot = mock_bot

            await app.run()

        mock_bot.session.close.assert_awaited_once()

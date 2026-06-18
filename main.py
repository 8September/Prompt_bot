import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from src.bot.config import config
from src.bot.handlers import start_router, prompts_router, improve_router
from src.bot.keyboards import get_main_reply_keyboard
from src.bot.logger import logger
from src.bot.middlewares import LoggingMiddleware


COMMANDS = [
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="help", description="Как пользоваться ботом"),
]


class BotApp:
    """
    Главный класс приложения.
    Собирает бота, диспетчер, роутеры и middleware в одном месте.
    """

    def __init__(self) -> None:
        self.bot = Bot(token=config.bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self._setup_middlewares()
        self._setup_routers()

    def _setup_middlewares(self) -> None:
        """Подключаем middleware к диспетчеру."""
        self.dp.update.middleware(LoggingMiddleware())

    def _setup_routers(self) -> None:
        """Подключаем все роутеры к диспетчеру."""
        self.dp.include_router(start_router)
        self.dp.include_router(prompts_router)
        self.dp.include_router(improve_router)

    async def _set_commands(self) -> None:
        """Устанавливает меню команд бота (кнопка / в поле ввода)."""
        await self.bot.set_my_commands(COMMANDS)
        logger.info("Меню команд установлено")

    async def run(self) -> None:
        """Запускаем бота в режиме polling."""
        logger.info("Бот запускается...")
        try:
            await self._set_commands()
            await self.bot.delete_webhook(drop_pending_updates=True)
            await self.dp.start_polling(
                self.bot,
                skip_updates=True,
            )
        except Exception as e:
            logger.critical(f"Критическая ошибка запуска бота: {e}")
            raise
        finally:
            await self.bot.session.close()
            logger.info("Бот остановлен")


async def main() -> None:
    app = BotApp()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())

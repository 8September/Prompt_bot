from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from src.bot.logger import logger


class LoggingMiddleware(BaseMiddleware):
    """
    Перехватывает все входящие обновления до хендлера.
    Логирует user_id, username, тип и содержимое обновления.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        update: Update = data.get("event_update")

        if update and update.message:
            msg = update.message
            logger.info(
                "Входящее сообщение | "
                f"user_id={msg.from_user.id} | "
                f"username=@{msg.from_user.username} | "
                f"text={msg.text!r}"
            )
        elif update and update.callback_query:
            cb = update.callback_query
            logger.info(
                "Callback query | "
                f"user_id={cb.from_user.id} | "
                f"username=@{cb.from_user.username} | "
                f"data={cb.data!r}"
            )

        return await handler(event, data)

from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()


@dataclass(frozen=True)
class Config:
    """Конфигурация бота. frozen=True — нельзя случайно изменить настройки."""

    bot_token: str
    log_level: str
    log_file: str

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN не найден в .env файле")
        return cls(
            bot_token=token,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "logs/bot.log"),
        )


# Единственный экземпляр на весь проект
config = Config.from_env()

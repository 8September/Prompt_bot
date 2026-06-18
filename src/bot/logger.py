import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.bot.config import config


def setup_logger() -> logging.Logger:
    """
    Настраивает и возвращает логгер для всего проекта.
    Пишет одновременно в файл и в консоль.
    RotatingFileHandler — файл не вырастет до бесконечности:
    максимум 5 МБ, потом создаётся новый файл. Хранится 3 файла.
    """
    # Создаём папку logs/ если её нет
    log_path = Path(config.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("prompt_bot")
    logger.setLevel(config.log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Хендлер для файла — с ротацией
    file_handler = RotatingFileHandler(
        filename=config.log_file,
        maxBytes=5 * 1024 * 1024,  # 5 МБ
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # Хендлер для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()

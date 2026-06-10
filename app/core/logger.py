from logging import Logger, StreamHandler
import logging
from logging.handlers import RotatingFileHandler
import os
from .config import settings

def get_logger() -> Logger:
    file_path = settings.log_file
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    formatter = logging.Formatter(
        settings.log_format, 
        datefmt=settings.log_datefmt
    )
    level = settings.log_level

    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    logger = logging.getLogger()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(level)

    logger.info("Logger setup complete")

    return logger

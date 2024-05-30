import logging
import logging.config
from logging import Logger
import sys
from types import TracebackType
from energy_box_control.config import CONFIG


def uncaught_exception_hook(
    type: type[BaseException], value: BaseException, tb: TracebackType | None
):
    logging.error(f"An unhandled error raised {type}\n{value}\n{tb}")


sys.excepthook = uncaught_exception_hook


def get_logger(logger_name: str) -> Logger:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s %(message)s - In method %(funcName)s on line %(lineno)d",
        stream=sys.stdout,
    )
    logger = logging.getLogger(logger_name)
    logger.setLevel(CONFIG.logging_level)
    return logger

"""Structured Logging setup using structlog."""
import logging
import sys
from typing import Any
import structlog
from core.config import settings


def setup_logging(log_level: Any = None, json_format: bool | None = None) -> None:
    """Configures structured JSON logging for production and human-readable for dev."""
    if log_level is None:
        level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    elif isinstance(log_level, str):
        level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        level = log_level

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    use_json = json_format if json_format is not None else not settings.DEBUG
    if not use_json:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


def get_logger(name: str = "amip") -> Any:
    """Returns a structured bound logger instance."""
    return structlog.get_logger(name)

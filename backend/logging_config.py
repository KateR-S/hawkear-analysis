"""Structured logging configuration using structlog.

LOG_LEVEL  – controls verbosity (default: DEBUG).
             Set to INFO or WARNING in production (e.g. via Railway env vars).
LOG_FORMAT – controls renderer: "json" (default) or "console" for human-readable output.
             When LOG_LEVEL is DEBUG and LOG_FORMAT is not explicitly set, "console" is used
             so that local development gets colourised, pretty output.
"""
import logging
import os
import sys

import structlog


def configure_logging() -> None:
    log_level_name = os.getenv("LOG_LEVEL", "DEBUG").upper()
    log_level = getattr(logging, log_level_name, logging.DEBUG)

    # Default to console renderer locally (DEBUG level), JSON in production.
    default_format = "console" if log_level == logging.DEBUG else "json"
    log_format = os.getenv("LOG_FORMAT", default_format).lower()

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if log_format == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Quiet down noisy third-party loggers in non-debug environments.
    if log_level > logging.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

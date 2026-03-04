import json
import logging
import os
import time
from time import struct_time
from typing import Any


class ConsoleFormatter(logging.Formatter):
    """Plain-text formatter with dot-separated milliseconds and correlation ID.

    Output: 2023-03-08 15:48:21.450 - trace_id - logger_name - LEVEL - message
    """

    @staticmethod
    def converter(t: float | None) -> struct_time:
        return time.gmtime(t)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        ct = self.converter(record.created)
        t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
        return f"{t}.{int(record.msecs):03d}"


class JsonFormatter(logging.Formatter):
    """Structured JSON formatter for file output."""

    @staticmethod
    def converter(t: float | None) -> struct_time:
        return time.gmtime(t)

    def format(self, record: logging.LogRecord) -> str:
        ct = self.converter(record.created)
        t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
        timestamp = f"{t}.{int(record.msecs):03d}"
        log_record = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "correlation_id", "-"),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(log_record)


def get_logging_config(log_file_path: str, log_level: str = "INFO") -> dict[str, Any]:
    log_dir = os.path.dirname(log_file_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation_id": {
                "()": "asgi_correlation_id.CorrelationIdFilter",
                "default_value": "-",
            }
        },
        "formatters": {
            "console": {
                "()": "src.config.logging_config.ConsoleFormatter",
                "fmt": "%(asctime)s - %(correlation_id)s - %(name)s - %(levelname)s - %(message)s",
            },
            "json": {
                "()": "src.config.logging_config.JsonFormatter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console",
                "filters": ["correlation_id"],
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "json",
                "filters": ["correlation_id"],
                "filename": log_file_path,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"],
        },
        "loggers": {
            "uvicorn": {"handlers": [], "propagate": True},
            "uvicorn.access": {"handlers": [], "propagate": True},
            "uvicorn.error": {"handlers": [], "propagate": True},
            "alembic": {"handlers": [], "propagate": True},
        },
    }

"""Structured logging setup with secret redaction.

Any log record whose message or args contain known secret substrings
(API keys, Mongo URIs with credentials, etc.) gets those values redacted
before they reach any handler.
"""
from __future__ import annotations

import json
import logging
import re
import sys
from typing import Any

_SECRET_ENV_KEYS = (
    "llm_api_key",
    "pinecone_api_key",
    "mongodb_uri",
    "LLM_API_KEY",
    "PINECONE_API_KEY",
    "MONGODB_URI",
)

# Redact common secret-shaped substrings: xAI keys (xai-...), bearer tokens,
# and mongodb connection strings with embedded credentials.
_PATTERNS = [
    re.compile(r"xai-[A-Za-z0-9]{10,}"),
    re.compile(r"(mongodb(?:\+srv)?://)([^:@/]+):([^@/]+)@"),
    re.compile(r"(sk-[A-Za-z0-9]{10,})"),
    re.compile(r"(Bearer\s+)[A-Za-z0-9._-]{10,}"),
]


def _redact(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = _PATTERNS[1].sub(r"\1***:***@", text)
    for pattern in (_PATTERNS[0], _PATTERNS[2]):
        text = pattern.sub("***REDACTED***", text)
    text = _PATTERNS[3].sub(r"\1***REDACTED***", text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = _redact(record.msg)
            if record.args:
                def _redact_arg(value):
                    return _redact(value) if isinstance(value, str) else value

                if isinstance(record.args, dict):
                    record.args = {k: _redact_arg(v) for k, v in record.args.items()}
                else:
                    record.args = tuple(_redact_arg(a) for a in record.args)
        except Exception:  # pragma: no cover - never let logging crash the app
            pass
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return _redact(json.dumps(payload, default=str))


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Avoid duplicate handlers when configure_logging is called more than once
    # (e.g. during tests that create the app multiple times).
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactingFilter())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

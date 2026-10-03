import contextvars
import json
import logging

request_id_var = contextvars.ContextVar("request_id", default=None)

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}
_SENSITIVE = {"password", "token", "authorization", "access", "refresh", "text", "prompt", "content", "message_text"}


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        for k, v in record.__dict__.items():
            if k not in _RESERVED and k != "request_id" and k.lower() not in _SENSITIVE:
                payload[k] = v
        if record.exc_info:
            payload["error_type"] = record.exc_info[0].__name__
            payload["traceback"] = self.formatException(record.exc_info)  # server logs only
        return json.dumps(payload, default=str, ensure_ascii=False)

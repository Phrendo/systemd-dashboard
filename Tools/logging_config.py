import json
import logging
import logging.config
from dotenv import dotenv_values

# -------------------------------------------------------------------
# LOAD ENV
# -------------------------------------------------------------------
config = dotenv_values("Tools/.env")
APP_NAME = config["APP_NAME"]

# -------------------------------------------------------------------
# CUSTOM JSON FORMATTER
# -------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """
    A formatter that converts the LogRecord into a JSON string,
    storing the exception in a top-level 'error' field if present.
    """
    def format(self, record):
        # Build standard log fields
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "filename": record.filename,
            "line": record.lineno,
            "app_name": getattr(record, "app_name", "N/A"),
            "error": getattr(record, "error", "")
        }
        return json.dumps(log_record)

# -------------------------------------------------------------------
# LOGGING CONFIG
# -------------------------------------------------------------------
def get_logging_config():
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": "INFO"
            }
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console"]
        }
    }

def init_logging():
    logging.config.dictConfig(get_logging_config())
    logger = logging.getLogger()

    class AppFilter(logging.Filter):
        def filter(self, record):
            record.app_name = APP_NAME  # Inject APP_NAME into every log record
            return True

    logger.addFilter(AppFilter())
    return logger

# -------------------------------------------------------------------
# USAGE EXAMPLE
# -------------------------------------------------------------------
if __name__ == "__main__":
    logger = init_logging()
    logger.info("Structured logging to console is working!")

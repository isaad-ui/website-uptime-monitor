import os
import logging

# --- Request settings ---

# How long to wait for a website to respond before giving up (seconds).
# Override by setting the REQUEST_TIMEOUT environment variable.
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "10"))

# Maximum number of history records returned when viewing history.
# Override by setting the MAX_HISTORY_DISPLAY environment variable.
MAX_HISTORY_DISPLAY = int(os.environ.get("MAX_HISTORY_DISPLAY", "100"))

# --- Logging settings ---

# Minimum log level to record: DEBUG, INFO, WARNING, ERROR
# DEBUG shows everything including redirect details and response times.
# INFO shows normal operations (checks started, results saved).
# WARNING shows recoverable problems (unexpected status codes).
# ERROR shows failures (timeouts, SSL errors, connection failures).
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Optional path to a log file. If empty, logs go to the terminal only.
# Example: LOG_FILE=logs/uptime.log
LOG_FILE = os.environ.get("LOG_FILE", "")

# Maximum size of a single log file before it rotates (bytes). Default 1 MB.
LOG_MAX_BYTES = int(os.environ.get("LOG_MAX_BYTES", str(1 * 1024 * 1024)))

# Number of rotated log files to keep. Older files are deleted automatically.
LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", "3"))

# --- Validate values ---

if REQUEST_TIMEOUT < 1 or REQUEST_TIMEOUT > 60:
    raise ValueError(
        f"REQUEST_TIMEOUT must be between 1 and 60 seconds, got {REQUEST_TIMEOUT}"
    )

if MAX_HISTORY_DISPLAY < 1:
    raise ValueError(
        f"MAX_HISTORY_DISPLAY must be at least 1, got {MAX_HISTORY_DISPLAY}"
    )

valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
if LOG_LEVEL not in valid_log_levels:
    raise ValueError(
        f"LOG_LEVEL must be one of {valid_log_levels}, got {LOG_LEVEL!r}"
    )


def setup_logging():
    """
    Configure the root logger based on environment settings.

    Call this once at application startup. All other modules then use:
        import logging
        logger = logging.getLogger(__name__)
    """
    handlers = []

    # Always log to the terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                          datefmt="%Y-%m-%d %H:%M:%S")
    )
    handlers.append(console_handler)

    # Optionally also log to a rotating file
    if LOG_FILE:
        from logging.handlers import RotatingFileHandler

        # Create the directory if it doesn't exist
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                              datefmt="%Y-%m-%d %H:%M:%S")
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        handlers=handlers,
        force=True,  # replace any handlers already attached (e.g. during tests)
    )

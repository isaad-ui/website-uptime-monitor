import os

# How long to wait for a website to respond before giving up (seconds).
# Override by setting the REQUEST_TIMEOUT environment variable.
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "10"))

# Maximum number of history records returned when viewing history.
# Override by setting the MAX_HISTORY_DISPLAY environment variable.
MAX_HISTORY_DISPLAY = int(os.environ.get("MAX_HISTORY_DISPLAY", "100"))

# Validate values so bad configuration fails early with a clear message.
if REQUEST_TIMEOUT < 1 or REQUEST_TIMEOUT > 60:
    raise ValueError(f"REQUEST_TIMEOUT must be between 1 and 60 seconds, got {REQUEST_TIMEOUT}")

if MAX_HISTORY_DISPLAY < 1:
    raise ValueError(f"MAX_HISTORY_DISPLAY must be at least 1, got {MAX_HISTORY_DISPLAY}")

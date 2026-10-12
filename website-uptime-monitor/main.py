
import requests
import time
import json
import os
from datetime import datetime
from urllib.parse import urlparse
import pip_system_certs.wrapt_requests  # fixes SSL on Windows

# --- NEW: path to the history file, sits next to this script ---
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")

# --- NEW: function that saves one check result to history.json ---
def save_history(url, status_code, uptime_status, response_time_ms):
    """Append a single check result to history.json."""

    # Build the record we want to save
    record = {
        "url": url,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status_code": status_code,
        "uptime_status": uptime_status,
        "response_time_ms": round(response_time_ms, 2) if response_time_ms is not None else None,
    }

    # Load existing history if the file already exists, otherwise start fresh
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    else:
        history = []

    # Add the new record and write everything back
    history.append(record)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    print(f"History saved to {HISTORY_FILE}")

# --- Your original code below — unchanged except for save_history() calls ---

url = input("Enter website URL: ").strip()

if not url.startswith(("http://", "https://")):
    url = "https://" + url

if not urlparse(url).hostname:
    print("Invalid URL")
else:
    try:
        start = time.perf_counter()
        response = requests.get(url, timeout=10)
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\nStatus code: {response.status_code}")
        print(f"Response time: {elapsed:.2f} ms")

        if response.status_code < 400:
            print("Status: UP")
            uptime_status = "UP"
        else:
            print("Status: DOWN")
            uptime_status = "DOWN"

        # --- NEW: save the successful check ---
        save_history(url, response.status_code, uptime_status, elapsed)

    except requests.exceptions.Timeout:
        print("Request timed out.")
        # --- NEW: record a timeout as DOWN, no status code or response time ---
        save_history(url, None, "DOWN", None)

    except requests.exceptions.ConnectionError:
        print("Could not connect to website.")
        # --- NEW: record a connection failure as DOWN ---
        save_history(url, None, "DOWN", None)

    except requests.exceptions.RequestException as error:
        print(f"Request failed: {error}")
        # --- NEW: record any other request failure as DOWN ---
        save_history(url, None, "DOWN", None)

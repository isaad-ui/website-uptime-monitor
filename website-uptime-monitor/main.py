
import requests
import time
import json
import os
from datetime import datetime
from urllib.parse import urlparse
import pip_system_certs.wrapt_requests

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")

def save_history(url, status_code, uptime_status, response_time_ms):
    record = {
        "url": url,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status_code": status_code,
        "uptime_status": uptime_status,
        "response_time_ms": round(response_time_ms, 2) if response_time_ms is not None else None,
    }

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    else:
        history = []

    history.append(record)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    print(f"History saved to {HISTORY_FILE}")

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

        save_history(url, response.status_code, uptime_status, elapsed)

    except requests.exceptions.Timeout:
        print("Request timed out.")
        save_history(url, None, "DOWN", None)

    except requests.exceptions.ConnectionError:
        print("Could not connect to website.")
        save_history(url, None, "DOWN", None)

    except requests.exceptions.RequestException as error:
        print(f"Request failed: {error}")
        save_history(url, None, "DOWN", None)

import logging
import re
import requests
import requests.exceptions
import time
import json
import os
import ipaddress
import socket
import argparse
from datetime import datetime
from urllib.parse import urlparse
import pip_system_certs.wrapt_requests
from config import REQUEST_TIMEOUT, MAX_HISTORY_DISPLAY, setup_logging

logger = logging.getLogger(__name__)

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
HISTORY_TMP = HISTORY_FILE + ".tmp"


# ---------- security ----------

PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def is_private_ip(hostname):
    """Return True if hostname resolves to a private/loopback address."""
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
        return any(ip in net for net in PRIVATE_NETWORKS)
    except (socket.gaierror, ValueError):
        return False


def validate_url(raw: str) -> tuple[str | None, str | None]:
    """
    Normalise and validate a URL.
    Returns (url, error_message). error_message is None when valid.

    Rules:
    - Strip leading/trailing whitespace.
    - Only http:// and https:// schemes are allowed.
    - Any other scheme (ftp://, javascript:, etc.) is rejected before prepending https://.
    - Add https:// when no scheme is present.
    - Reject empty, localhost, private IPs, and unparseable hostnames.
    """
    raw = raw.strip()

    if not raw:
        return None, "Invalid URL: URL must not be empty."

    # Reject non-http schemes before we do anything else.
    # This catches ftp://, javascript:, file://, data:, etc.
    # We check both "scheme://" and bare "scheme:" (e.g. javascript:alert(1)).
    scheme_match = re.match(r'^([a-zA-Z][a-zA-Z0-9+\-.]*):(.{0,2})', raw)
    if scheme_match:
        scheme = scheme_match.group(1).lower()
        after = scheme_match.group(2)
        # Allow http and https only; reject anything else that looks like a scheme
        if scheme not in ("http", "https"):
            logger.warning("Rejected unsupported URL scheme %r", scheme)
            sep = "://" if after.startswith("//") else ":"
            return None, f"Invalid URL: only http:// and https:// are supported (got {scheme}{sep})."

    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw

    parsed = urlparse(raw)
    hostname = parsed.hostname

    if not hostname or hostname in ("", "."):
        logger.warning("URL validation failed — could not parse hostname: %r", raw)
        return None, "Invalid URL: could not parse hostname."

    if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
        logger.warning("Blocked request to localhost from input: %r", raw)
        return None, "Blocked: localhost is not allowed."

    if is_private_ip(hostname):
        logger.warning("Blocked request to private IP for hostname: %s", hostname)
        return None, "Blocked: private/internal IP addresses are not allowed."

    logger.debug("URL validated: %s", raw)
    return raw, None


# ---------- history ----------

def load_history():
    """Load history from file. Return empty list on any error."""
    if not os.path.exists(HISTORY_FILE):
        logger.debug("History file not found, starting with empty list")
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
        result = data if isinstance(data, list) else []
        logger.debug("Loaded %d history records", len(result))
        return result
    except json.JSONDecodeError:
        logger.error("History file contains invalid JSON — returning empty list")
        return []
    except OSError as e:
        logger.error("Could not read history file: %s", e)
        return []


def save_history(url, status_code, uptime_status, response_time_ms):
    """Append one check result to history.json using an atomic write."""
    record = {
        "url": url,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status_code": status_code,
        "uptime_status": uptime_status,
        "response_time_ms": round(response_time_ms, 2) if response_time_ms is not None else None,
    }

    history = load_history()
    history.append(record)

    try:
        with open(HISTORY_TMP, "w") as f:
            json.dump(history, f, indent=2)
        os.replace(HISTORY_TMP, HISTORY_FILE)
        logger.info("History saved — %s %s (code=%s, ms=%s)",
                    uptime_status, url, status_code, record["response_time_ms"])
        print(f"History saved to {HISTORY_FILE}")
    except OSError as e:
        logger.error("Failed to save history for %s: %s", url, e)
        print("Warning: could not save history.")


def print_history(filter_url=None, filter_status=None):
    """Print saved history with optional filters."""
    history = load_history()

    if not history:
        print("No history found.")
        return

    if filter_url:
        history = [r for r in history if filter_url.lower() in r["url"].lower()]
    if filter_status:
        history = [r for r in history if r["uptime_status"] == filter_status.upper()]

    if not history:
        print("No records match your filter.")
        return

    history = history[-MAX_HISTORY_DISPLAY:]
    print(f"\n{'Time':<22} {'URL':<40} {'Status':<7} {'Code':<6} {'ms'}")
    print("-" * 85)
    for r in history:
        code = str(r["status_code"]) if r["status_code"] is not None else "None"
        ms = f"{r['response_time_ms']:.2f}" if r["response_time_ms"] is not None else "None"
        print(f"{r['checked_at']:<22} {r['url']:<40} {r['uptime_status']:<7} {code:<6} {ms}")


# ---------- check ----------

def check_website(url):
    """
    Run the uptime check.
    Returns (status_code, uptime_status, elapsed_ms, error_msg).
    error_msg is None on success.
    """
    logger.info("Checking %s", url)
    try:
        start = time.perf_counter()
        response = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        elapsed = (time.perf_counter() - start) * 1000

        if response.history:
            logger.debug("Redirected %d hop(s): %s -> %s",
                         len(response.history), url, response.url)
            print(f"Redirected ({len(response.history)} hop(s)) -> {response.url}")

        uptime_status = "UP" if response.status_code < 400 else "DOWN"
        logger.info("Result: %s | code=%d | %.0f ms | %s",
                    uptime_status, response.status_code, elapsed, url)
        return response.status_code, uptime_status, elapsed, None

    except requests.exceptions.SSLError:
        logger.error("SSL error checking %s", url)
        return None, "DOWN", None, "SSL certificate error."

    except requests.exceptions.Timeout:
        logger.warning("Timeout after %ds checking %s", REQUEST_TIMEOUT, url)
        return None, "DOWN", None, "Request timed out."

    except requests.exceptions.ConnectionError as e:
        # Distinguish DNS failures from general connection errors
        msg = str(e).lower()
        if "name or service not known" in msg or "nodename nor servname" in msg or "getaddrinfo" in msg:
            logger.warning("DNS resolution failed for %s", url)
            return None, "DOWN", None, "Could not resolve hostname."
        logger.warning("Connection error checking %s", url)
        return None, "DOWN", None, "Could not connect to website."

    except requests.exceptions.TooManyRedirects:
        logger.warning("Too many redirects for %s", url)
        return None, "DOWN", None, "Too many redirects."

    except requests.exceptions.RequestException as e:
        logger.error("Unexpected request error for %s: %s", url, e)
        return None, "DOWN", None, f"Request failed: {e}"


# ---------- main ----------

def main():
    setup_logging()
    logger.debug("Application started")

    parser = argparse.ArgumentParser(description="Website Uptime Monitor")
    parser.add_argument("--history", action="store_true", help="Show saved check history")
    parser.add_argument("--url", help="Filter history by URL (partial match)")
    parser.add_argument("--status", choices=["UP", "DOWN"], help="Filter history by status")
    args = parser.parse_args()

    if args.history:
        print_history(filter_url=args.url, filter_status=args.status)
        logger.debug("Application exiting after history display")
        return

    raw = input("Enter website URL: ").strip()
    if not raw:
        print("No URL entered.")
        logger.warning("User submitted empty URL input")
        return

    url, error = validate_url(raw)
    if error:
        print(error)
        return

    status_code, uptime_status, elapsed, err_msg = check_website(url)

    if err_msg:
        print(err_msg)
    else:
        print(f"\nStatus code: {status_code}")
        print(f"Response time: {elapsed:.2f} ms")

    print(f"Status: {uptime_status}")
    save_history(url, status_code, uptime_status, elapsed)
    logger.debug("Application exiting normally")


if __name__ == "__main__":
    main()

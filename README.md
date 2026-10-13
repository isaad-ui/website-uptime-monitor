# Website Uptime Monitor

![Tests](https://github.com/isaad-ui/website-uptime-monitor/actions/workflows/tests.yml/badge.svg)

A command-line tool that checks whether a website is up or down, measures its response time, and saves every check to a local `history.json` file.

---

## Features

- Checks any website URL for availability
- Measures response time in milliseconds
- Reports HTTP status code and UP/DOWN status
- Detects and reports redirect chains
- Handles SSL errors, timeouts, DNS failures, and connection errors gracefully
- Distinguishes DNS failures from connection errors in logs and output
- Blocks requests to localhost and private IP addresses (SSRF protection)
- Saves every check to `history.json` automatically using atomic writes
- View and filter saved history from the terminal
- Structured logging with configurable levels and optional log file rotation
- 28 automated tests covering validation, security, storage, checks, and logging

---

## Requirements

- Python 3.8 or higher
- pip

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/isaad-ui/website-uptime-monitor.git
cd website-uptime-monitor/website-uptime-monitor
```

2. Install dependencies:

```bash
pip install -r ../requirements.txt
```

> **Windows only:** `pip-system-certs` fixes SSL certificate verification on Windows. If you are on Linux or Mac, remove that line from `requirements.txt` before installing and remove the `import pip_system_certs.wrapt_requests` line from `main.py`.

---

## Usage

### Check a website

```bash
python main.py
```

You will be prompted to enter a URL:

```
Enter website URL: github.com
```

You can enter a URL with or without `https://` — the tool adds it automatically.

**Example output (site is up):**

```
Status code: 200
Response time: 312.45 ms
Status: UP
History saved to /path/to/history.json
```

**Example output (redirect):**

```
Redirected (1 hop(s)) -> https://www.example.com/
Status code: 200
Response time: 408.12 ms
Status: UP
History saved to /path/to/history.json
```

**Example output (site is down):**

```
SSL certificate error.
Status: DOWN
History saved to /path/to/history.json
```

### View history

```bash
python main.py --history
```

**Filter by URL (partial match):**

```bash
python main.py --history --url github
```

**Filter by status:**

```bash
python main.py --history --status DOWN
```

**Combine filters:**

```bash
python main.py --history --url github --status UP
```

**Example output:**

```
Time                   URL                                      Status  Code   ms
-------------------------------------------------------------------------------------
2026-10-12 14:05:33    https://github.com                       UP      200    312.45
2026-10-12 14:06:45    http://fake-site.com                     DOWN    None   None
```

---

## Security

- Requests to `localhost`, `127.0.0.1`, and private IP ranges (`10.x`, `172.16.x`, `192.168.x`) are blocked to prevent server-side request forgery (SSRF).
- No secrets, API keys, or credentials are stored anywhere in the project.
- History writes are atomic — a crash mid-write cannot corrupt the existing file.

---

## History file

Every check is appended to `history.json` in the same folder as `main.py`. The file is created automatically on the first run.

**Example `history.json`:**

```json
[
  {
    "url": "https://github.com",
    "checked_at": "2026-10-12 14:05:33",
    "status_code": 200,
    "uptime_status": "UP",
    "response_time_ms": 312.45
  },
  {
    "url": "http://fake-site.com",
    "checked_at": "2026-10-12 14:06:45",
    "status_code": null,
    "uptime_status": "DOWN",
    "response_time_ms": null
  }
]
```

> **Note:** `history.json` is excluded from version control. If you move the project to another machine, copy `history.json` manually to preserve your history.
>
> **JSON storage limitation:** JSON works well for hundreds of records. If you run thousands of checks, consider migrating to SQLite using Python's built-in `sqlite3` module.

---

## Running tests

```bash
cd website-uptime-monitor
python -m pytest test_main.py -v
```

All 21 tests should pass. Tests cover:

- URL normalisation and validation
- Localhost and private IP blocking
- History file loading (including corrupt and missing files)
- Website check responses: 200, 404, 500, timeout, SSL error, connection error, too many redirects

---

## Deployment

This is a CLI tool — it runs locally on your machine. There is no web server or API to host.

To run it on any machine:

1. Install Python 3.8+
2. Clone the repo and install dependencies (see Installation above)
3. Run `python main.py`

To check a site on a schedule:

- **Windows:** Task Scheduler
- **Linux/Mac:** `cron`

### Logging

By default the application logs to the terminal at `INFO` level. You can change this with environment variables.

**Log levels** (from most to least verbose):
- `DEBUG` — shows redirect hops, response times, every validation step
- `INFO` — shows each check started and its result (default)
- `WARNING` — shows timeouts, DNS failures, blocked URLs
- `ERROR` — shows SSL errors, history write failures, unexpected exceptions

**Change the log level:**

```bash
# Windows PowerShell
$env:LOG_LEVEL="DEBUG"
python main.py

# Linux / macOS
LOG_LEVEL=DEBUG python main.py
```

**Save logs to a rotating file:**

```bash
LOG_FILE=logs/uptime.log python main.py
```

This creates `logs/uptime.log`. When it reaches 1 MB it rotates automatically, keeping 3 old files. Both size and count are configurable — see `.env.example`.

**What gets logged vs what goes in `history.json`:**

| | Logs | history.json |
|--|------|-------------|
| Purpose | Debugging and diagnostics | Record of every check |
| Format | Timestamped text lines | Structured JSON |
| Persists | Optional (requires `LOG_FILE`) | Always |
| In Git | No (`.gitignore`d) | No (`.gitignore`d) |

**Common errors and their meaning:**

| Message | Cause |
|---------|-------|
| `SSL certificate error` | Site has an invalid or expired SSL certificate |
| `Request timed out` | Site took longer than `REQUEST_TIMEOUT` seconds to respond |
| `Could not resolve hostname` | DNS lookup failed — check the URL spelling |
| `Could not connect to website` | Host found but connection refused or reset |
| `Too many redirects` | Site redirects in an infinite loop |
| `Blocked: localhost is not allowed` | URL pointed to localhost (SSRF protection) |
| `Blocked: private/internal IP` | URL resolved to a private network address |

---

## Deployment checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] On Linux/Mac: remove `pip-system-certs` from `requirements.txt` and its import from `main.py`
- [ ] Tests pass: `python -m pytest test_main.py -v`
- [ ] Script runs without errors: `python main.py`
- [ ] `history.json` backed up if migrating from another machine

---

## Architecture

```
website-uptime-monitor/
├── requirements.txt          # pinned dependencies
├── README.md
└── website-uptime-monitor/
    ├── main.py               # all logic: validation, checking, history, CLI
    ├── test_main.py          # 21 automated tests (unittest + pytest)
    └── history.json          # local check history (gitignored)
```

`main.py` is structured as four layers:

1. **Security** — `validate_url`, `is_private_ip`: block bad input before any network call
2. **History** — `load_history`, `save_history`, `print_history`: read/write/display JSON records
3. **Check** — `check_website`: make the HTTP request, return structured result
4. **CLI** — `main`: parse arguments, call the layers above, print output

---

## Screenshots

> Add a screenshot of the terminal output here.

---

## License

MIT

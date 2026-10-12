# Website Uptime Monitor

A command-line tool that checks whether a website is up or down, measures its response time, and saves every check to a local `history.json` file.

---

## Features

- Checks any website URL for availability
- Measures response time in milliseconds
- Reports HTTP status code and UP/DOWN status
- Saves every check to `history.json` automatically
- Handles timeouts and connection errors gracefully
- Works on Windows (uses system SSL certificates)

---

## Requirements

- Python 3.8 or higher
- pip

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/isaad-ui/website-uptime-monitor.git
cd website-uptime-monitor
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

> **Note:** `pip-system-certs` is a Windows-only package that fixes SSL verification issues. If you are on Linux or Mac, remove that line from `requirements.txt` before installing.

---

## Usage

```bash
cd website-uptime-monitor
python main.py
```

You will be prompted to enter a URL:

```
Enter website URL: github.com
```

You can enter a URL with or without `https://` — the tool adds it automatically.

**Example output:**

```
Status code: 200
Response time: 312.45 ms
Status: UP
History saved to /path/to/history.json
```

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

> **Important for deployment:** `history.json` is excluded from version control (listed in `.gitignore`). If you copy this project to another machine or a server, the history starts fresh. To keep history across machines, back up `history.json` manually or store it on a shared/persistent drive.

---

## Deployment

This is a CLI tool — it runs locally on your machine. There is no web server or API to host.

To run it on any machine:

1. Install Python 3.8+
2. Clone the repo and install dependencies (see Installation above)
3. Run `python main.py`

If you want to run it on a schedule (e.g. check a site every hour), use:

- **Windows:** Task Scheduler
- **Linux/Mac:** `cron`

---

## Deployment checklist

- [ ] Python 3.8+ installed on the target machine
- [ ] Dependencies installed via `pip install -r requirements.txt`
- [ ] `history.json` backed up if you are migrating from another machine
- [ ] On Linux/Mac: `pip-system-certs` removed from `requirements.txt`
- [ ] Script runs without errors: `python main.py`

---

## Screenshots

> Add a screenshot of the terminal output here.

---

## License

MIT

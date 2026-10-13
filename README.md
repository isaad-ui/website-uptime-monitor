# Website Uptime Monitor

![Tests](https://github.com/isaad-ui/website-uptime-monitor/actions/workflows/tests.yml/badge.svg)

A full-stack monitoring application that checks whether websites are up or down, tracks response times, saves check history, and displays results in a React dashboard.

---

## Features

- Check any public website URL for availability
- Measures and displays HTTP status code and response time in milliseconds
- Detects redirect chains and reports hops
- Handles SSL errors, timeouts, DNS failures, and connection errors
- Blocks requests to localhost and private IP addresses (SSRF protection)
- Saves every check to persistent JSON history with atomic writes
- React dashboard with real-time statistics and filterable history table
- Auto-refreshes every 30 seconds with a manual refresh button
- Shows API health status — distinguishes backend downtime from a website being DOWN
- History filtering by URL and UP/DOWN status with pagination
- Structured logging with configurable levels and optional log file rotation
- Configurable via environment variables
- 67 automated tests (28 CLI + 22 API + 17 frontend)
- GitHub Actions CI runs all tests and the production build on every push

---

## Technology stack

| Layer | Technology |
|-------|-----------|
| Monitoring logic | Python 3, `requests` |
| API | FastAPI, uvicorn |
| Frontend | React 18, Vite |
| Testing (Python) | pytest, unittest.mock |
| Testing (frontend) | Vitest, Testing Library |
| Storage | JSON file with atomic writes |
| CI | GitHub Actions |

---

## Project structure

```
website-uptime-monitor/
├── .github/
│   ├── workflows/tests.yml        # CI: Python tests + frontend tests + build
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── backend/
│   ├── api.py                     # FastAPI app — POST /check, GET /history, GET /stats
│   └── test_api.py                # 22 API tests
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx      # Root component, auto-refresh, API health
│   │   │   ├── WebsiteCheckForm.jsx
│   │   │   ├── StatisticsCards.jsx
│   │   │   ├── HistoryTable.jsx
│   │   │   ├── HistoryFilters.jsx
│   │   │   ├── StatusBadge.jsx
│   │   │   ├── StatCard.jsx
│   │   │   ├── LoadingSpinner.jsx
│   │   │   └── Dashboard.test.jsx # 17 frontend tests
│   │   ├── services/
│   │   │   └── api.js             # All fetch calls — checkWebsite, getHistory, getStats
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css              # Design system — dark theme, responsive
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── .env.example
├── website-uptime-monitor/
│   ├── main.py                    # CLI — validation, SSRF, check, history, logging
│   ├── config.py                  # Environment variable configuration
│   └── test_main.py               # 28 CLI tests
├── .env.example                   # Backend environment variables
├── requirements.txt
├── CONTRIBUTING.md
└── LICENSE
```

---

## Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- pip and npm

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/isaad-ui/website-uptime-monitor.git
cd website-uptime-monitor
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Windows only:** `pip-system-certs` fixes SSL certificate verification on Windows.
> On Linux or macOS, remove `pip-system-certs` from `requirements.txt` and remove
> `import pip_system_certs.wrapt_requests` from `website-uptime-monitor/main.py`.

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

> **Windows SSL note:** If `npm install` fails with `UNABLE_TO_VERIFY_LEAF_SIGNATURE`,
> run `npm config set strict-ssl false` once, then retry.

### 4. Configure environment variables (optional)

```bash
# Backend
cp .env.example .env

# Frontend
cp frontend/.env.example frontend/.env
```

The defaults work for local development without any changes.

---

## Running the application

**Terminal 1 — start the backend:**

```bash
cd backend
uvicorn api:app --reload --port 8000
```

**Terminal 2 — start the frontend:**

```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

The interactive API documentation is available at **http://localhost:8000/docs**.

### CLI (no frontend needed)

```bash
cd website-uptime-monitor
python main.py
# Enter website URL: github.com

# View history
python main.py --history

# Filter history
python main.py --history --url github --status UP
```

---

## Environment variables

### Backend (`.env` or shell)

| Variable | Default | Description |
|----------|---------|-------------|
| `REQUEST_TIMEOUT` | `10` | Seconds before a check times out (1–60) |
| `MAX_HISTORY_DISPLAY` | `100` | Max records shown by `--history` |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `LOG_FILE` | *(empty)* | Path to a log file — empty means terminal only |
| `LOG_MAX_BYTES` | `1048576` | Log file rotation size in bytes (1 MB) |
| `LOG_BACKUP_COUNT` | `3` | Number of rotated log files to keep |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/check` | Check a website |
| `GET` | `/history` | Retrieve check history |
| `GET` | `/stats` | Retrieve monitoring statistics |

### POST /check

**Request:**
```json
{ "url": "github.com" }
```

**Response:**
```json
{
  "url": "https://github.com",
  "checked_at": "2026-10-13 10:00:00",
  "status": "UP",
  "status_code": 200,
  "response_time_ms": 312.45,
  "error": null
}
```

### GET /history

Query parameters: `url` (partial match), `status` (`UP`/`DOWN`), `limit` (1–1000, default 100)

### GET /stats

Query parameters: `url` (partial match)

**Response:**
```json
{
  "total_checks": 10,
  "up_count": 9,
  "down_count": 1,
  "uptime_percent": 90.0,
  "average_response_ms": 287.33,
  "last_checked": "2026-10-13 10:00:00"
}
```

---

## Running tests

### Python tests (CLI + API)

```bash
# CLI tests
cd website-uptime-monitor
python -m pytest test_main.py -v

# API tests
cd backend
python -m pytest test_api.py -v
```

### Frontend tests

```bash
cd frontend
npm test
```

### All tests pass locally:

| Suite | Tests | Result |
|-------|-------|--------|
| CLI (`test_main.py`) | 28 | ✅ Pass |
| API (`test_api.py`) | 22 | ✅ Pass |
| Frontend (`Dashboard.test.jsx`) | 17 | ✅ Pass |

---

## Production build

```bash
cd frontend
npm run build
```

The optimised output is written to `frontend/dist/`. Serve it with any static file host (Netlify, Vercel, GitHub Pages, nginx).

Set `VITE_API_URL` to your production backend URL before building:

```bash
VITE_API_URL=https://api.your-domain.com npm run build
```

---

## Deployment

This project has two independently deployable parts:

### Backend (FastAPI)
- Deploy to any server that runs Python: Railway, Render, Fly.io, a VPS
- Set `CORS` origins in `backend/api.py` to your frontend's production domain
- Use a process manager (`systemd`, `supervisor`) or the platform's native process runner
- `history.json` is written to the same directory as `main.py` — use a persistent disk volume

### Frontend (React)
- Run `npm run build` and deploy `frontend/dist/` to Netlify, Vercel, or any static host
- Set `VITE_API_URL` to your backend's public URL before building
- No server required — it's a static site

### CORS in production
Update `backend/api.py` to allow your frontend domain:
```python
allow_origins=["https://your-frontend.netlify.app"]
```

---

## Security

- Requests to `localhost`, `127.0.0.1`, and private IP ranges are blocked (SSRF protection)
- No secrets are stored in source code or committed to Git
- History writes are atomic — a crash mid-write cannot corrupt the file
- Logging never records passwords, tokens, or credentials
- `frontend/.env` and `.env` are gitignored

---

## Known limitations

- History is stored in a single JSON file. For thousands of records, migrate to SQLite
- No user authentication — anyone with access to the API can check URLs and read history
- No scheduled automatic monitoring — checks are triggered manually via the dashboard or CLI

---

## Screenshots

> Add a screenshot of the dashboard here.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and code style guide.

---

## License

MIT — see [LICENSE](LICENSE)

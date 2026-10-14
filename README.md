# Website Uptime Monitor

![Tests](https://github.com/isaad-ui/website-uptime-monitor/actions/workflows/tests.yml/badge.svg)

A full-stack web application that checks whether websites are up or down, tracks response times, saves check history, and displays results in a live React dashboard.

**Live demo:** [website-uptime-monitor.netlify.app](https://website-uptime-monitor.netlify.app)

---

## Features

- Check any public website URL for availability
- Displays HTTP status code and response time in milliseconds
- Detects and reports redirect chains
- Handles SSL errors, timeouts, DNS failures, and connection errors gracefully
- Blocks requests to localhost and private IP addresses (SSRF protection)
- Rejects dangerous URL schemes — `javascript:`, `ftp://`, `file://`
- Saves every check to persistent history with atomic writes
- React dashboard with live statistics and filterable history table
- Auto-refreshes every 30 seconds with a manual refresh button
- Distinguishes backend downtime from a monitored website being DOWN
- Relative timestamps ("2m ago") and readable date formatting
- History filtering by URL and UP/DOWN status with pagination
- Structured logging with configurable levels and optional log file rotation
- 34 CLI tests, 22 API tests, 17 frontend tests
- GitHub Actions CI runs all tests on every push

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
| Backend hosting | Render |
| Frontend hosting | Netlify |
| CI | GitHub Actions |

---

## Project structure

```
website-uptime-monitor/
├── .github/
│   ├── workflows/tests.yml         # CI: Python + frontend tests + build
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── backend/
│   ├── api.py                      # FastAPI — POST /check, GET /history, GET /stats
│   └── test_api.py                 # 22 API tests
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx       # Root — auto-refresh, API health indicator
│   │   │   ├── WebsiteCheckForm.jsx
│   │   │   ├── StatisticsCards.jsx
│   │   │   ├── HistoryTable.jsx
│   │   │   ├── HistoryFilters.jsx
│   │   │   ├── StatusBadge.jsx
│   │   │   ├── StatCard.jsx
│   │   │   ├── LoadingSpinner.jsx
│   │   │   └── Dashboard.test.jsx  # 17 frontend tests
│   │   ├── services/api.js         # All fetch calls to the backend
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css               # Expo Luminous design system
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── .env.example
├── website-uptime-monitor/
│   ├── main.py                     # CLI — validation, SSRF, check, history, logging
│   ├── config.py                   # Environment variable configuration
│   └── test_main.py                # 34 CLI tests
├── render.yaml                     # Render deployment config
├── runtime.txt                     # Python version for Render
├── .env.example                    # Backend environment variables
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

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/isaad-ui/website-uptime-monitor.git
cd website-uptime-monitor
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

> **Windows SSL note:** If `npm install` fails with `UNABLE_TO_VERIFY_LEAF_SIGNATURE`,
> run `npm config set strict-ssl false` once, then retry.

### 4. Start the backend

```bash
cd backend
uvicorn api:app --reload --port 8000
```

### 5. Start the frontend

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**. API docs at **http://localhost:8000/docs**.

> **Windows note:** If the dashboard shows "API unavailable", create `frontend/.env` with:
> ```
> VITE_API_URL=http://127.0.0.1:8000
> ```
> Then restart the frontend.

---

## CLI usage (no frontend needed)

```bash
cd website-uptime-monitor

# Check a website
python main.py

# View history
python main.py --history

# Filter history
python main.py --history --url github --status UP
```

---

## Environment variables

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `REQUEST_TIMEOUT` | `10` | Seconds before a check times out (1–60) |
| `MAX_HISTORY_DISPLAY` | `100` | Max records shown by `--history` |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `LOG_FILE` | *(empty)* | Path to log file — empty means terminal only |
| `CORS_ORIGIN` | *(empty)* | Production frontend URL for CORS |

### Frontend

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
  "checked_at": "2026-10-14 10:00:00",
  "status": "UP",
  "status_code": 200,
  "response_time_ms": 312.45,
  "error": null
}
```

### GET /history

Query parameters: `url` (partial match), `status` (`UP`/`DOWN`), `limit` (1–1000)

### GET /stats

```json
{
  "total_checks": 10,
  "up_count": 9,
  "down_count": 1,
  "uptime_percent": 90.0,
  "average_response_ms": 287.33,
  "last_checked": "2026-10-14 10:00:00"
}
```

---

## Running tests

```bash
# CLI tests (34)
cd website-uptime-monitor
python -m pytest test_main.py -v

# API tests (22)
cd backend
python -m pytest test_api.py -v

# Frontend tests (17)
cd frontend
npm test
```

| Suite | Tests | Status |
|-------|-------|--------|
| CLI | 34 | ✅ Pass |
| API | 22 | ✅ Pass |
| Frontend | 17 | ✅ Pass |

---

## Deployment

### Backend — Render

1. Create a new **Web Service** on [Render](https://render.com)
2. Connect `isaad-ui/website-uptime-monitor`
3. Settings:
   - Root Directory: `backend`
   - Build Command: `pip install -r ../requirements.txt`
   - Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `CORS_ORIGIN` = your Netlify URL

### Frontend — Netlify

1. Create a new site on [Netlify](https://netlify.com) from GitHub
2. Settings:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `frontend/dist`
3. Add environment variable: `VITE_API_URL` = your Render URL
4. Trigger a redeploy

---

## Security

- Dangerous URL schemes rejected (`javascript:`, `ftp://`, `file://`)
- Requests to localhost and private IP ranges blocked (SSRF protection)
- No secrets in source code or Git history
- Atomic history writes prevent data corruption on crash
- CORS restricted to known frontend origins

---

## Known limitations

- History stored in a single JSON file — suitable for hundreds of records
- No user authentication — single shared history
- No scheduled automatic monitoring — checks are triggered manually

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE)

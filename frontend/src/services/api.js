/**
 * api.js — all communication with the FastAPI backend lives here.
 *
 * Components import these functions. They never call fetch() directly.
 * This keeps API logic in one place and makes testing easier.
 *
 * The base URL comes from an environment variable so it can be changed
 * without editing source code. Vite exposes variables prefixed with VITE_.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/**
 * checkWebsite(url)
 * POST /check
 * Sends a URL to the backend for checking. Returns the result.
 *
 * Returns: { url, checked_at, status, status_code, response_time_ms, error }
 * Throws ApiError on HTTP errors or network failures.
 */
export async function checkWebsite(url) {
  return request('POST', '/check', { url })
}

/**
 * getHistory({ url, status, limit })
 * GET /history
 * Fetches saved check history with optional filters.
 *
 * Returns: array of { url, checked_at, status, status_code, response_time_ms }
 */
export async function getHistory({ url = '', status = '', limit = 100 } = {}) {
  const params = new URLSearchParams()
  if (url) params.set('url', url)
  if (status) params.set('status', status)
  if (limit) params.set('limit', String(limit))
  const query = params.toString()
  return request('GET', `/history${query ? '?' + query : ''}`)
}

/**
 * getStats({ url })
 * GET /stats
 * Fetches monitoring statistics, optionally filtered to one site.
 *
 * Returns: { total_checks, up_count, down_count, uptime_percent,
 *            average_response_ms, last_checked }
 */
export async function getStats({ url = '' } = {}) {
  const params = new URLSearchParams()
  if (url) params.set('url', url)
  const query = params.toString()
  return request('GET', `/stats${query ? '?' + query : ''}`)
}

/**
 * checkApiHealth()
 * GET /
 * Confirms the backend is reachable.
 */
export async function checkApiHealth() {
  return request('GET', '/')
}

// ---------- internal helpers ----------

/**
 * ApiError — thrown when the backend returns an error or is unreachable.
 * Components catch this and display a friendly message.
 *
 * .status     — HTTP status code (null when the network is down)
 * .detail     — error message from the API or a fallback string
 * .isNetwork  — true when the backend itself is unreachable
 */
export class ApiError extends Error {
  constructor(message, { status = null, detail = null, isNetwork = false } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail ?? message
    this.isNetwork = isNetwork
  }
}

async function request(method, path, body) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) {
    options.body = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(BASE_URL + path, options)
  } catch {
    // fetch() itself throws when the server is completely unreachable
    throw new ApiError('Cannot reach the monitoring API. Is the backend running?', {
      isNetwork: true,
    })
  }

  if (!response.ok) {
    let detail = `Server returned ${response.status}`
    try {
      const data = await response.json()
      detail = data.detail ?? detail
    } catch {
      // response body is not JSON — keep the fallback message
    }
    throw new ApiError(detail, { status: response.status, detail })
  }

  return response.json()
}

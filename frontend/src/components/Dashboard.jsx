/**
 * Dashboard
 *
 * The root component. Renders the header, check form, stats, and history.
 *
 * Auto-refresh: statistics and history refresh every REFRESH_INTERVAL ms.
 * A manual refresh button is always available.
 * A new check from the form also triggers a refresh.
 *
 * State held here (not in children) so one refresh key updates both
 * StatisticsCards and HistoryTable simultaneously.
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import WebsiteCheckForm from './WebsiteCheckForm'
import StatisticsCards  from './StatisticsCards'
import HistoryTable     from './HistoryTable'
import { checkApiHealth, ApiError } from '../services/api'

// Auto-refresh interval in milliseconds. 30 s is reasonable for a dashboard.
// Lower values increase backend load without adding much value.
const REFRESH_INTERVAL = 30_000

export default function Dashboard() {
  const [refreshKey, setRefreshKey]       = useState(0)
  const [lastUpdated, setLastUpdated]     = useState(null)
  const [apiStatus, setApiStatus]         = useState('unknown') // 'ok' | 'down' | 'unknown'
  const [refreshing, setRefreshing]       = useState(false)
  const refreshTimerRef                   = useRef(null)

  // Refresh data and update the "last updated" timestamp
  const refresh = useCallback(async (showSpinner = false) => {
    if (showSpinner) setRefreshing(true)
    try {
      await checkApiHealth()
      setApiStatus('ok')
    } catch {
      setApiStatus('down')
    }
    setRefreshKey(k => k + 1)
    setLastUpdated(new Date())
    if (showSpinner) setRefreshing(false)
  }, [])

  // Check API health on mount, then poll
  useEffect(() => {
    refresh()
    refreshTimerRef.current = setInterval(() => refresh(), REFRESH_INTERVAL)
    return () => clearInterval(refreshTimerRef.current)
  }, [refresh])

  // Called by WebsiteCheckForm after a successful check
  function handleCheckComplete() {
    refresh()
  }

  function formatLastUpdated(date) {
    if (!date) return null
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="dashboard-header__inner">
          <div className="dashboard-header__title">
            <span className="dashboard-header__icon" aria-hidden="true">📡</span>
            <h1>Website Uptime Monitor</h1>
          </div>
          <div className="dashboard-header__meta">
            {apiStatus === 'down' && (
              <span className="api-status api-status--down" role="alert">
                ⚠ API unavailable
              </span>
            )}
            {apiStatus === 'ok' && (
              <span className="api-status api-status--ok" aria-label="API connected">
                ● API connected
              </span>
            )}
            {lastUpdated && (
              <span className="last-updated">
                Updated {formatLastUpdated(lastUpdated)}
              </span>
            )}
            <button
              className="btn btn--ghost btn--sm"
              onClick={() => refresh(true)}
              disabled={refreshing}
              aria-label="Refresh dashboard"
            >
              {refreshing ? '↻ Refreshing…' : '↻ Refresh'}
            </button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        <WebsiteCheckForm onCheckComplete={handleCheckComplete} />
        <StatisticsCards refreshKey={refreshKey} />
        <HistoryTable    refreshKey={refreshKey} />
      </main>

      <footer className="dashboard-footer">
        <p>
          Website Uptime Monitor ·{' '}
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            API docs
          </a>
        </p>
      </footer>
    </div>
  )
}

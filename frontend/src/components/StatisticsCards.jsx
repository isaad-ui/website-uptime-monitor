import { useState, useEffect } from 'react'
import { getStats, ApiError } from '../services/api'
import LoadingSpinner from './LoadingSpinner'

/** Format "2026-10-14 09:27:37" as "2 minutes ago" style relative time */
function timeAgo(datetimeStr) {
  if (!datetimeStr) return null
  const past = new Date(datetimeStr.replace(' ', 'T'))
  const diffMs = Date.now() - past.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1)  return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHrs = Math.floor(diffMins / 60)
  if (diffHrs < 24)  return `${diffHrs}h ago`
  const diffDays = Math.floor(diffHrs / 24)
  return `${diffDays}d ago`
}

export default function StatisticsCards({ refreshKey = 0 }) {
  const [stats, setStats]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getStats()
      .then(data => { if (!cancelled) { setStats(data); setLoading(false) } })
      .catch(err => {
        if (!cancelled) {
          setError(err instanceof ApiError && err.isNetwork
            ? 'Cannot reach the API.'
            : 'Failed to load statistics.')
          setLoading(false)
        }
      })
    return () => { cancelled = true }
  }, [refreshKey])

  if (loading) return (
    <section className="stats-section" aria-label="Statistics">
      <h2 className="section-title">Statistics</h2>
      <div className="stats-loading"><LoadingSpinner label="Loading statistics…" /></div>
    </section>
  )

  if (error) return (
    <section className="stats-section" aria-label="Statistics">
      <h2 className="section-title">Statistics</h2>
      <div className="alert alert--error" role="alert">{error}</div>
    </section>
  )

  const uptimePct = stats.uptime_percent ?? 0
  const avgMs = stats.average_response_ms !== null
    ? `${Math.round(stats.average_response_ms)} ms`
    : '—'
  const lastChecked = timeAgo(stats.last_checked)

  return (
    <section className="stats-section" aria-label="Statistics">
      <h2 className="section-title">Statistics</h2>
      <div className="stat-cards">

        <div className="stat-card">
          <span className="stat-card__value">{stats.total_checks}</span>
          <span className="stat-card__label">Total Checks</span>
        </div>

        <div className="stat-card stat-card--success">
          <span className="stat-card__value">{stats.up_count}</span>
          <span className="stat-card__label">Up</span>
        </div>

        <div className="stat-card stat-card--danger">
          <span className="stat-card__value">{stats.down_count}</span>
          <span className="stat-card__label">Down</span>
        </div>

        <div className={`stat-card stat-card--${uptimePct >= 90 ? 'success' : uptimePct >= 50 ? 'warning' : 'danger'}`}>
          <span className="stat-card__value">{uptimePct}%</span>
          <span className="stat-card__label">Uptime</span>
        </div>

        <div className="stat-card">
          <span className="stat-card__value">{avgMs}</span>
          <span className="stat-card__label">Avg Response (UP)</span>
        </div>

        {lastChecked && (
          <div className="stat-card">
            <span className="stat-card__value stat-card__value--sm">{lastChecked}</span>
            <span className="stat-card__label">Last Checked</span>
          </div>
        )}

      </div>
    </section>
  )
}

/**
 * StatisticsCards
 *
 * Fetches stats from GET /stats and renders four summary cards.
 * Refreshes whenever the `refreshKey` prop changes (parent increments it
 * after a new check completes).
 *
 * Props:
 *   refreshKey  number  increment this to trigger a refresh
 */
import { useState, useEffect } from 'react'
import { getStats, ApiError } from '../services/api'
import StatCard from './StatCard'
import LoadingSpinner from './LoadingSpinner'

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

  const avgMs = stats.average_response_ms !== null
    ? `${stats.average_response_ms.toFixed(0)} ms`
    : '—'

  return (
    <section className="stats-section" aria-label="Statistics">
      <h2 className="section-title">Statistics</h2>
      <div className="stat-cards">
        <StatCard label="Total Checks"     value={stats.total_checks}              accent="neutral" />
        <StatCard label="Checks Up"        value={stats.up_count}                  accent="success" />
        <StatCard label="Checks Down"      value={stats.down_count}                accent="danger"  />
        <StatCard label="Uptime"           value={`${stats.uptime_percent ?? 0}%`} accent={stats.uptime_percent >= 90 ? 'success' : 'warning'} />
        <StatCard label="Avg Response"     value={avgMs}                           accent="neutral" />
        {stats.last_checked && (
          <StatCard label="Last Checked"   value={stats.last_checked}              accent="neutral" />
        )}
      </div>
    </section>
  )
}

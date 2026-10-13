/**
 * HistoryTable
 *
 * Fetches history from GET /history and renders it in a table with filters.
 * Refreshes whenever `refreshKey` changes.
 *
 * Props:
 *   refreshKey  number  increment to trigger a data refresh
 */
import { useState, useEffect } from 'react'
import { getHistory, ApiError } from '../services/api'
import StatusBadge from './StatusBadge'
import HistoryFilters from './HistoryFilters'
import LoadingSpinner from './LoadingSpinner'

const PAGE_SIZE = 20

export default function HistoryTable({ refreshKey = 0 }) {
  const [allRecords, setAllRecords] = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)
  const [filters, setFilters]       = useState({ url: '', status: '' })
  const [page, setPage]             = useState(1)

  // Fetch fresh data whenever refreshKey changes
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    getHistory({ limit: 500 })
      .then(data => {
        if (!cancelled) {
          setAllRecords(data)
          setLoading(false)
          setPage(1)
        }
      })
      .catch(err => {
        if (!cancelled) {
          setError(err instanceof ApiError && err.isNetwork
            ? 'Cannot reach the API.'
            : 'Failed to load history.')
          setLoading(false)
        }
      })

    return () => { cancelled = true }
  }, [refreshKey])

  // Reset to page 1 when filters change
  useEffect(() => { setPage(1) }, [filters])

  // Apply filters client-side (data is already loaded)
  const filtered = allRecords
    .filter(r => !filters.url    || r.url.toLowerCase().includes(filters.url.toLowerCase()))
    .filter(r => !filters.status || r.status === filters.status)

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const pageRecords = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <section className="history-section" aria-label="Check history">
      <div className="history-header">
        <h2 className="section-title">History</h2>
        <span className="history-count">
          {filtered.length} record{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      <HistoryFilters filters={filters} onFiltersChange={setFilters} />

      {loading && (
        <div className="history-loading">
          <LoadingSpinner label="Loading history…" />
        </div>
      )}

      {error && !loading && (
        <div className="alert alert--error" role="alert">{error}</div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="empty-state" role="status">
          {allRecords.length === 0
            ? 'No checks recorded yet. Use the form above to check a website.'
            : 'No records match your filters.'}
        </div>
      )}

      {!loading && !error && pageRecords.length > 0 && (
        <>
          <div className="table-wrapper">
            <table className="history-table">
              <thead>
                <tr>
                  <th scope="col">Time</th>
                  <th scope="col">URL</th>
                  <th scope="col">Status</th>
                  <th scope="col">Code</th>
                  <th scope="col">Response (ms)</th>
                </tr>
              </thead>
              <tbody>
                {pageRecords.map((r, i) => (
                  <tr key={i} className={r.status === 'DOWN' ? 'row--down' : ''}>
                    <td className="cell--time">{r.checked_at}</td>
                    <td className="cell--url" title={r.url}>{r.url}</td>
                    <td><StatusBadge status={r.status} size="sm" /></td>
                    <td>{r.status_code ?? '—'}</td>
                    <td>{r.response_time_ms !== null && r.response_time_ms !== undefined
                      ? r.response_time_ms.toFixed(0)
                      : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <nav className="pagination" aria-label="History pagination">
              <button
                className="btn btn--ghost btn--sm"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                ← Prev
              </button>
              <span className="pagination__info">
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn--ghost btn--sm"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next →
              </button>
            </nav>
          )}
        </>
      )}
    </section>
  )
}

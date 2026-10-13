/**
 * HistoryFilters
 *
 * Renders filter controls for the history table.
 *
 * Props:
 *   filters         { url, status }
 *   onFiltersChange(newFilters)  called when any filter changes
 */
export default function HistoryFilters({ filters, onFiltersChange }) {
  function handleUrl(e) {
    onFiltersChange({ ...filters, url: e.target.value })
  }

  function handleStatus(e) {
    onFiltersChange({ ...filters, status: e.target.value })
  }

  function handleClear() {
    onFiltersChange({ url: '', status: '' })
  }

  const hasFilters = filters.url || filters.status

  return (
    <div className="history-filters" role="search" aria-label="Filter history">
      <label htmlFor="filter-url" className="filter-label">URL</label>
      <input
        id="filter-url"
        type="text"
        className="filter-input"
        placeholder="Filter by URL…"
        value={filters.url}
        onChange={handleUrl}
      />

      <label htmlFor="filter-status" className="filter-label">Status</label>
      <select
        id="filter-status"
        className="filter-select"
        value={filters.status}
        onChange={handleStatus}
      >
        <option value="">All</option>
        <option value="UP">UP</option>
        <option value="DOWN">DOWN</option>
      </select>

      {hasFilters && (
        <button
          type="button"
          className="btn btn--ghost btn--sm"
          onClick={handleClear}
        >
          Clear filters
        </button>
      )}
    </div>
  )
}

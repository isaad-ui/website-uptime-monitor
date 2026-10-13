/**
 * StatCard — a summary number card used in the statistics section.
 *
 * Props:
 *   label    string   e.g. "Total Checks"
 *   value    string|number  e.g. 42
 *   accent   string   "neutral" | "success" | "danger" | "warning" (default "neutral")
 */
export default function StatCard({ label, value, accent = 'neutral' }) {
  return (
    <div className={`stat-card stat-card--${accent}`}>
      <span className="stat-card__value">{value ?? '—'}</span>
      <span className="stat-card__label">{label}</span>
    </div>
  )
}

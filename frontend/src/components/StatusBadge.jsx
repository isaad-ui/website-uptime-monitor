/**
 * StatusBadge — displays "UP" or "DOWN" as a coloured pill.
 *
 * Props:
 *   status  string  "UP" | "DOWN"
 *   size    string  "sm" | "md" (default "md")
 */
export default function StatusBadge({ status, size = 'md' }) {
  const isUp = status === 'UP'
  return (
    <span
      className={`status-badge status-badge--${isUp ? 'up' : 'down'} status-badge--${size}`}
      aria-label={`Status: ${status}`}
    >
      {status}
    </span>
  )
}

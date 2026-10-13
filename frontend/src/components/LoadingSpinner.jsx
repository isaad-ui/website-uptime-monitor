/**
 * LoadingSpinner — a simple accessible spinner.
 *
 * Props:
 *   label  string  screen-reader text (default "Loading…")
 *   size   string  "sm" | "md" (default "md")
 */
export default function LoadingSpinner({ label = 'Loading…', size = 'md' }) {
  return (
    <span
      className={`spinner spinner--${size}`}
      role="status"
      aria-label={label}
    />
  )
}

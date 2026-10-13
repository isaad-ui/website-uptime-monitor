/**
 * WebsiteCheckForm
 *
 * Lets the user type a URL and check it immediately.
 * Shows the result (or error) inline below the form.
 *
 * Props:
 *   onCheckComplete(result)  called after a successful check so the
 *                            Dashboard can refresh history and stats.
 */
import { useState } from 'react'
import { checkWebsite, ApiError } from '../services/api'
import StatusBadge from './StatusBadge'
import LoadingSpinner from './LoadingSpinner'

export default function WebsiteCheckForm({ onCheckComplete }) {
  const [url, setUrl]           = useState('')
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)   // successful check result
  const [error, setError]       = useState(null)   // string error message
  const [inputError, setInputError] = useState('') // inline validation

  function validateInput(value) {
    if (!value.trim()) return 'Please enter a URL.'
    return ''
  }

  async function handleSubmit(e) {
    e.preventDefault()

    const validationMsg = validateInput(url)
    if (validationMsg) {
      setInputError(validationMsg)
      return
    }

    setInputError('')
    setResult(null)
    setError(null)
    setLoading(true)

    try {
      const data = await checkWebsite(url.trim())
      setResult(data)
      if (onCheckComplete) onCheckComplete(data)
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        // Validation rejection from the backend (e.g. localhost blocked)
        setInputError(err.detail)
      } else if (err instanceof ApiError && err.isNetwork) {
        setError('Cannot reach the monitoring API. Make sure the backend is running.')
      } else {
        setError(err instanceof ApiError ? err.detail : 'An unexpected error occurred.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="check-form-section" aria-label="Check a website">
      <h2 className="section-title">Check a Website</h2>

      <form className="check-form" onSubmit={handleSubmit} noValidate>
        <div className="check-form__row">
          <label htmlFor="url-input" className="sr-only">
            Website URL
          </label>
          <input
            id="url-input"
            type="url"
            className={`check-form__input${inputError ? ' check-form__input--error' : ''}`}
            placeholder="https://example.com or example.com"
            value={url}
            onChange={e => { setUrl(e.target.value); setInputError('') }}
            disabled={loading}
            aria-describedby={inputError ? 'url-error' : undefined}
            aria-invalid={!!inputError}
          />
          <button
            type="submit"
            className="btn btn--primary"
            disabled={loading}
            aria-busy={loading}
          >
            {loading ? <><LoadingSpinner size="sm" label="Checking…" /> Checking…</> : 'Check'}
          </button>
        </div>

        {inputError && (
          <p id="url-error" className="form-error" role="alert">
            {inputError}
          </p>
        )}
      </form>

      {error && (
        <div className="alert alert--error" role="alert">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className={`check-result check-result--${result.status.toLowerCase()}`} role="region" aria-label="Check result">
          <div className="check-result__header">
            <StatusBadge status={result.status} size="md" />
            <span className="check-result__url">{result.url}</span>
          </div>
          <dl className="check-result__details">
            {result.status_code !== null && result.status_code !== undefined && (
              <>
                <dt>HTTP Status</dt>
                <dd>{result.status_code}</dd>
              </>
            )}
            {result.response_time_ms !== null && result.response_time_ms !== undefined && (
              <>
                <dt>Response Time</dt>
                <dd>{result.response_time_ms.toFixed(0)} ms</dd>
              </>
            )}
            <dt>Checked At</dt>
            <dd>{result.checked_at}</dd>
            {result.error && (
              <>
                <dt>Detail</dt>
                <dd className="check-result__error">{result.error}</dd>
              </>
            )}
          </dl>
        </div>
      )}
    </section>
  )
}

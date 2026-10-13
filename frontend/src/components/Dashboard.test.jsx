/**
 * Dashboard tests
 *
 * All fetch calls are mocked — tests never hit the real backend.
 * We mock the api.js module so components receive controlled responses.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import Dashboard from './Dashboard'

// Mock the entire api module
vi.mock('../services/api', () => ({
  checkApiHealth: vi.fn(),
  checkWebsite:   vi.fn(),
  getHistory:     vi.fn(),
  getStats:       vi.fn(),
  ApiError:       class ApiError extends Error {
    constructor(msg, opts = {}) {
      super(msg)
      this.name = 'ApiError'
      this.status = opts.status ?? null
      this.detail = opts.detail ?? msg
      this.isNetwork = opts.isNetwork ?? false
    }
  },
}))

import * as api from '../services/api'

const SAMPLE_STATS = {
  total_checks: 10, up_count: 9, down_count: 1,
  uptime_percent: 90.0, average_response_ms: 250.5,
  last_checked: '2026-10-13 10:00:00',
}

const SAMPLE_HISTORY = [
  { url: 'https://github.com', checked_at: '2026-10-13 10:00:00', status: 'UP',   status_code: 200, response_time_ms: 312 },
  { url: 'https://example.com', checked_at: '2026-10-13 09:00:00', status: 'DOWN', status_code: null, response_time_ms: null },
]

beforeEach(() => {
  vi.clearAllMocks()
  api.checkApiHealth.mockResolvedValue({ status: 'ok' })
  api.getStats.mockResolvedValue(SAMPLE_STATS)
  api.getHistory.mockResolvedValue(SAMPLE_HISTORY)
})

describe('Dashboard', () => {
  it('renders the app title', async () => {
    render(<Dashboard />)
    expect(screen.getByText('Website Uptime Monitor')).toBeInTheDocument()
  })

  it('shows API connected status when backend is reachable', async () => {
    render(<Dashboard />)
    await waitFor(() => {
      expect(screen.getByText(/API connected/i)).toBeInTheDocument()
    })
  })

  it('shows API unavailable when backend is down', async () => {
    const { ApiError } = await import('../services/api')
    api.checkApiHealth.mockRejectedValue(new ApiError('down', { isNetwork: true }))
    render(<Dashboard />)
    await waitFor(() => {
      expect(screen.getByText(/API unavailable/i)).toBeInTheDocument()
    })
  })

  it('renders statistics after load', async () => {
    render(<Dashboard />)
    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument()   // total checks
      expect(screen.getByText('90%')).toBeInTheDocument()   // uptime
    })
  })

  it('renders history rows', async () => {
    render(<Dashboard />)
    await waitFor(() => {
      expect(screen.getByText('https://github.com')).toBeInTheDocument()
      expect(screen.getByText('https://example.com')).toBeInTheDocument()
    })
  })

  it('shows empty state when history is empty', async () => {
    api.getHistory.mockResolvedValue([])
    render(<Dashboard />)
    await waitFor(() => {
      expect(screen.getByText(/No checks recorded yet/i)).toBeInTheDocument()
    })
  })

  it('shows refresh button', async () => {
    render(<Dashboard />)
    expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument()
  })

  it('clicking refresh re-fetches stats and history', async () => {
    render(<Dashboard />)
    await waitFor(() => screen.getByText('https://github.com'))

    fireEvent.click(screen.getByRole('button', { name: /refresh/i }))

    await waitFor(() => {
      // getStats called at least twice (mount + refresh)
      expect(api.getStats.mock.calls.length).toBeGreaterThanOrEqual(2)
    })
  })
})

describe('WebsiteCheckForm inside Dashboard', () => {
  it('renders the URL input', async () => {
    render(<Dashboard />)
    expect(screen.getByPlaceholderText(/https:\/\/example\.com/i)).toBeInTheDocument()
  })

  it('shows validation error when submitted empty', async () => {
    render(<Dashboard />)
    fireEvent.click(screen.getByRole('button', { name: /^check$/i }))
    await waitFor(() => {
      expect(screen.getByText(/please enter a url/i)).toBeInTheDocument()
    })
  })

  it('shows UP result after successful check', async () => {
    api.checkWebsite.mockResolvedValue({
      url: 'https://github.com',
      checked_at: '2026-10-13 10:00:00',
      status: 'UP',
      status_code: 200,
      response_time_ms: 312,
      error: null,
    })
    render(<Dashboard />)
    const input = screen.getByPlaceholderText(/https:\/\/example\.com/i)
    fireEvent.change(input, { target: { value: 'github.com' } })
    fireEvent.click(screen.getByRole('button', { name: /^check$/i }))
    await waitFor(() => {
      expect(screen.getAllByText('UP').length).toBeGreaterThan(0)
    })
  })

  it('shows DOWN result with error message', async () => {
    api.checkWebsite.mockResolvedValue({
      url: 'https://example.com',
      checked_at: '2026-10-13 10:00:00',
      status: 'DOWN',
      status_code: null,
      response_time_ms: null,
      error: 'Request timed out.',
    })
    render(<Dashboard />)
    const input = screen.getByPlaceholderText(/https:\/\/example\.com/i)
    fireEvent.change(input, { target: { value: 'example.com' } })
    fireEvent.click(screen.getByRole('button', { name: /^check$/i }))
    await waitFor(() => {
      expect(screen.getAllByText('DOWN').length).toBeGreaterThan(0)
      expect(screen.getByText('Request timed out.')).toBeInTheDocument()
    })
  })

  it('shows network error when API is unreachable', async () => {
    const { ApiError } = await import('../services/api')
    api.checkWebsite.mockRejectedValue(
      new ApiError('Cannot reach API', { isNetwork: true })
    )
    render(<Dashboard />)
    const input = screen.getByPlaceholderText(/https:\/\/example\.com/i)
    fireEvent.change(input, { target: { value: 'github.com' } })
    fireEvent.click(screen.getByRole('button', { name: /^check$/i }))
    await waitFor(() => {
      expect(screen.getByText(/backend is running/i)).toBeInTheDocument()
    })
  })

  it('shows 422 validation error inline on the input', async () => {
    const { ApiError } = await import('../services/api')
    api.checkWebsite.mockRejectedValue(
      new ApiError('Blocked: localhost is not allowed.', { status: 422, detail: 'Blocked: localhost is not allowed.' })
    )
    render(<Dashboard />)
    const input = screen.getByPlaceholderText(/https:\/\/example\.com/i)
    fireEvent.change(input, { target: { value: 'localhost' } })
    fireEvent.click(screen.getByRole('button', { name: /^check$/i }))
    await waitFor(() => {
      expect(screen.getByText(/localhost is not allowed/i)).toBeInTheDocument()
    })
  })
})

describe('HistoryFilters inside Dashboard', () => {
  it('filtering by URL narrows the table', async () => {
    render(<Dashboard />)
    await waitFor(() => screen.getByText('https://github.com'))

    const urlInput = screen.getByPlaceholderText(/filter by url/i)
    fireEvent.change(urlInput, { target: { value: 'github' } })

    await waitFor(() => {
      expect(screen.getByText('https://github.com')).toBeInTheDocument()
      expect(screen.queryByText('https://example.com')).not.toBeInTheDocument()
    })
  })

  it('filtering by DOWN status shows only down records', async () => {
    render(<Dashboard />)
    await waitFor(() => screen.getByText('https://github.com'))

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'DOWN' } })

    await waitFor(() => {
      expect(screen.queryByText('https://github.com')).not.toBeInTheDocument()
      expect(screen.getByText('https://example.com')).toBeInTheDocument()
    })
  })

  it('shows no-match message when nothing passes filter', async () => {
    render(<Dashboard />)
    await waitFor(() => screen.getByText('https://github.com'))

    const urlInput = screen.getByPlaceholderText(/filter by url/i)
    fireEvent.change(urlInput, { target: { value: 'xyz-does-not-exist' } })

    await waitFor(() => {
      expect(screen.getByText(/no records match/i)).toBeInTheDocument()
    })
  })
})

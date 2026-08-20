import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import WarningBanner, { isBannerWorthy } from './WarningBanner'

const makeWarning = (overrides = {}) => ({
  id: 'w1',
  level: 'AMBER',
  weather_type: 'rain',
  headline: 'Heavy rain may cause flooding',
  issued: '2026-08-20T09:00:00Z',
  valid_from: '2026-08-21T06:00:00Z',
  valid_to: '2026-08-21T18:00:00Z',
  locations: ['Home'],
  ...overrides,
})

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function mockFetchOk(warnings) {
  fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ warnings }) })
}

describe('WarningBanner — isBannerWorthy', () => {
  it('accepts red', () => {
    expect(isBannerWorthy('RED')).toBe(true)
  })

  it('accepts amber', () => {
    expect(isBannerWorthy('AMBER')).toBe(true)
  })

  it('rejects yellow', () => {
    expect(isBannerWorthy('YELLOW')).toBe(false)
  })

  it('rejects an unknown level', () => {
    expect(isBannerWorthy('MYSTERY')).toBe(false)
  })

  it('rejects a missing level', () => {
    expect(isBannerWorthy(undefined)).toBe(false)
  })
})

describe('WarningBanner — nothing to show', () => {
  it('renders nothing when the warnings list is empty', async () => {
    mockFetchOk([])
    const { container } = render(<WarningBanner />)
    await waitFor(() => expect(fetch).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing while the API has not responded', () => {
    fetch.mockReturnValueOnce(new Promise(() => {}))
    const { container } = render(<WarningBanner />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when the API call fails', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'))
    const { container } = render(<WarningBanner />)
    await waitFor(() => expect(fetch).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when the API returns a non-ok status', async () => {
    fetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) })
    const { container } = render(<WarningBanner />)
    await waitFor(() => expect(fetch).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when the only warning is yellow', async () => {
    mockFetchOk([makeWarning({ level: 'YELLOW' })])
    const { container } = render(<WarningBanner />)
    await waitFor(() => expect(fetch).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })
})

describe('WarningBanner — content', () => {
  it('fetches from /api/weather/warnings', async () => {
    mockFetchOk([makeWarning()])
    render(<WarningBanner />)
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith('/api/weather/warnings')
    )
  })

  it('shows the warning headline', async () => {
    mockFetchOk([makeWarning()])
    render(<WarningBanner />)
    await waitFor(() =>
      expect(
        screen.getByText(/Heavy rain may cause flooding/)
      ).toBeInTheDocument()
    )
  })

  it('names the severity', async () => {
    mockFetchOk([makeWarning()])
    render(<WarningBanner />)
    await waitFor(() => expect(screen.getByText(/Amber/)).toBeInTheDocument())
  })

  it('names a single affected location', async () => {
    mockFetchOk([makeWarning({ locations: ['Home'] })])
    render(<WarningBanner />)
    await waitFor(() => expect(screen.getByText(/Home/)).toBeInTheDocument())
  })

  it('joins two affected locations with an ampersand', async () => {
    mockFetchOk([makeWarning({ locations: ['Home', 'Guildford'] })])
    render(<WarningBanner />)
    await waitFor(() =>
      expect(screen.getByText(/Home & Guildford/)).toBeInTheDocument()
    )
  })

  it('carries a weather warning label', async () => {
    mockFetchOk([makeWarning()])
    render(<WarningBanner />)
    await waitFor(() =>
      expect(screen.getByText(/Weather warning/i)).toBeInTheDocument()
    )
  })
})

describe('WarningBanner — severity roles', () => {
  it('announces an amber warning as a status', async () => {
    mockFetchOk([makeWarning({ level: 'AMBER' })])
    render(<WarningBanner />)
    await waitFor(() => expect(screen.getByRole('status')).toBeInTheDocument())
  })

  it('announces a red warning as an alert', async () => {
    mockFetchOk([makeWarning({ level: 'RED' })])
    render(<WarningBanner />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })

  it('lets the most severe warning govern the banner', async () => {
    mockFetchOk([
      makeWarning({ level: 'AMBER', headline: 'Amber headline' }),
      makeWarning({ id: 'w2', level: 'RED', headline: 'Red headline' }),
    ])
    render(<WarningBanner />)
    await waitFor(() =>
      expect(screen.getByText(/Red headline/)).toBeInTheDocument()
    )
    expect(screen.queryByText(/Amber headline/)).not.toBeInTheDocument()
  })
})

describe('WarningBanner — multiple warnings', () => {
  it('summarises additional warnings as a count', async () => {
    mockFetchOk([
      makeWarning({ id: 'a', headline: 'First' }),
      makeWarning({ id: 'b', headline: 'Second' }),
      makeWarning({ id: 'c', headline: 'Third' }),
    ])
    render(<WarningBanner />)
    await waitFor(() => expect(screen.getByText(/First/)).toBeInTheDocument())
    expect(screen.getByText(/\+2 more/i)).toBeInTheDocument()
  })

  it('shows no count for a single warning', async () => {
    mockFetchOk([makeWarning()])
    render(<WarningBanner />)
    await waitFor(() => expect(screen.getByText(/Amber/)).toBeInTheDocument())
    expect(screen.queryByText(/more/i)).not.toBeInTheDocument()
  })

  it('does not count a suppressed yellow warning', async () => {
    // +1 more would point at something the user can never see.
    mockFetchOk([
      makeWarning({ id: 'y', level: 'YELLOW', headline: 'Yellow one' }),
      makeWarning({ id: 'a', level: 'AMBER', headline: 'Amber one' }),
    ])
    render(<WarningBanner />)
    await waitFor(() =>
      expect(screen.getByText(/Amber one/)).toBeInTheDocument()
    )
    expect(screen.queryByText(/more/i)).not.toBeInTheDocument()
  })
})

import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import TravelCard from './TravelCard'

const makeRoute = (overrides = {}) => ({
  travel_time_seconds: 1800,
  delay_seconds: 50,
  distance_meters: 20000,
  description: 'via A3 and M25',
  delay_colour: 'green',
  ...overrides,
})

const makeApiResponse = (overrides = {}) => ({
  home_to_work: [makeRoute(), makeRoute({ description: 'via A316' })],
  home_to_nursery: [makeRoute(), makeRoute({ description: 'via B321' })],
  incidents: [],
  is_stale: false,
  ...overrides,
})

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function mockFetchOk(data) {
  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => data,
  })
}

function mockFetchError() {
  fetch.mockRejectedValueOnce(new Error('Network error'))
}

describe('TravelCard — loading and error states', () => {
  it('shows a loading indicator while the API has not responded', async () => {
    fetch.mockReturnValueOnce(new Promise(() => {})) // never resolves
    render(<TravelCard />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('fetches from /api/travel', async () => {
    mockFetchOk(makeApiResponse())
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByText('Home → Work')).toBeInTheDocument()
    )
    expect(fetch).toHaveBeenCalledWith('/api/travel')
  })

  it('shows an error message when the API call fails', async () => {
    mockFetchError()
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByRole('alert')).toBeInTheDocument()
    )
  })

  it('shows an error message when the API returns a non-ok HTTP status', async () => {
    fetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) })
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByRole('alert')).toBeInTheDocument()
    )
  })
})

describe('TravelCard — route display', () => {
  it('renders 2 route cards under the Home → Work heading', async () => {
    mockFetchOk(makeApiResponse())
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByText('Home → Work')).toBeInTheDocument()
    )
    const section = screen.getByText('Home → Work').closest('section')
    const cards = section.querySelectorAll('[data-testid="route-card"]')
    expect(cards).toHaveLength(2)
  })

  it('renders 2 route cards under the Home → Nursery heading', async () => {
    mockFetchOk(makeApiResponse())
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByText('Home → Nursery')).toBeInTheDocument()
    )
    const section = screen.getByText('Home → Nursery').closest('section')
    const cards = section.querySelectorAll('[data-testid="route-card"]')
    expect(cards).toHaveLength(2)
  })

  it('does not render the Home → Work section when home_to_work is empty', async () => {
    mockFetchOk(makeApiResponse({ home_to_work: [] }))
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByText('Home → Nursery')).toBeInTheDocument()
    )
    expect(screen.queryByText('Home → Work')).not.toBeInTheDocument()
  })

  it('does not render the Home → Nursery section when home_to_nursery is empty', async () => {
    mockFetchOk(makeApiResponse({ home_to_nursery: [] }))
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByText('Home → Work')).toBeInTheDocument()
    )
    expect(screen.queryByText('Home → Nursery')).not.toBeInTheDocument()
  })

  it('displays the route description text', async () => {
    mockFetchOk(
      makeApiResponse({
        home_to_work: [makeRoute({ description: 'via A3 and M25' })],
        home_to_nursery: [],
      })
    )
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByText('via A3 and M25')).toBeInTheDocument()
    )
  })

  it('displays travel time in minutes', async () => {
    mockFetchOk(
      makeApiResponse({
        home_to_work: [makeRoute({ travel_time_seconds: 2700 })],
        home_to_nursery: [],
      })
    )
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByText('45 min')).toBeInTheDocument()
    )
  })
})

describe('TravelCard — colour states', () => {
  it('applies green colour indicator for a green-state route', async () => {
    mockFetchOk(
      makeApiResponse({
        home_to_work: [makeRoute({ delay_colour: 'green' })],
        home_to_nursery: [],
      })
    )
    render(<TravelCard />)
    await waitFor(() =>
      expect(
        document.querySelector('[data-colour="green"]')
      ).toBeInTheDocument()
    )
  })

  it('applies amber colour indicator for an amber-state route', async () => {
    mockFetchOk(
      makeApiResponse({
        home_to_work: [makeRoute({ delay_colour: 'amber' })],
        home_to_nursery: [],
      })
    )
    render(<TravelCard />)
    await waitFor(() =>
      expect(
        document.querySelector('[data-colour="amber"]')
      ).toBeInTheDocument()
    )
  })

  it('applies red colour indicator for a red-state route', async () => {
    mockFetchOk(
      makeApiResponse({
        home_to_work: [makeRoute({ delay_colour: 'red' })],
        home_to_nursery: [],
      })
    )
    render(<TravelCard />)
    await waitFor(() =>
      expect(
        document.querySelector('[data-colour="red"]')
      ).toBeInTheDocument()
    )
  })
})

describe('TravelCard — incidents', () => {
  it('shows incident description when incidents are present', async () => {
    mockFetchOk(
      makeApiResponse({
        incidents: [
          { type: 'ROAD_WORKS', description: 'Roadworks on A3', road: 'A3' },
        ],
      })
    )
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByText('Roadworks on A3')).toBeInTheDocument()
    )
  })

  it('does not render an incident section when there are no incidents', async () => {
    mockFetchOk(makeApiResponse({ incidents: [] }))
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByText('Home → Work')).toBeInTheDocument()
    )
    expect(
      screen.queryByTestId('incident-list')
    ).not.toBeInTheDocument()
  })
})

describe('TravelCard — stale indicator', () => {
  it('shows a stale data warning when is_stale is true', async () => {
    mockFetchOk(makeApiResponse({ is_stale: true }))
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByTestId('stale-warning')).toBeInTheDocument()
    )
  })

  it('does not show a stale warning when is_stale is false', async () => {
    mockFetchOk(makeApiResponse({ is_stale: false }))
    render(<TravelCard />)
    await waitFor(() =>
      expect(screen.getByText('Home → Work')).toBeInTheDocument()
    )
    expect(screen.queryByTestId('stale-warning')).not.toBeInTheDocument()
  })
})

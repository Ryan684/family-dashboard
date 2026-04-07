import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import DogWalkCard from './DogWalkCard'

const makeRoute = (overrides = {}) => ({
  id: 'park-loop',
  name: 'Park Loop',
  description: 'Flat pavement path',
  duration_minutes: 25,
  distance_km: 2.1,
  surface: 'pavement',
  mud_sensitivity: 1,
  suitable: true,
  ...overrides,
})

const makeApiResponse = (overrides = {}) => ({
  eligible: true,
  conditions: 'Dry',
  routes: [
    makeRoute(),
    makeRoute({ id: 'river-trail', name: 'River Trail', duration_minutes: 45, distance_km: 3.8, mud_sensitivity: 3, suitable: true }),
    makeRoute({ id: 'mixed-loop', name: 'Mixed Loop', duration_minutes: 35, distance_km: 3.0, mud_sensitivity: 2, suitable: true }),
  ],
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

function mockFetchStatus(status) {
  fetch.mockResolvedValueOnce({ ok: false, status })
}

describe('DogWalkCard — eligibility gate', () => {
  it('does not render the card when eligible is false', async () => {
    mockFetchOk({ eligible: false, conditions: null, routes: [] })
    const { container } = render(<DogWalkCard />)
    await waitFor(() => expect(fetch).toHaveBeenCalled())
    expect(container.firstChild).toBeNull()
  })

  it('renders the card when eligible is true', async () => {
    mockFetchOk(makeApiResponse())
    render(<DogWalkCard />)
    await waitFor(() => expect(screen.getByTestId('dog-walk-card')).toBeInTheDocument())
  })
})

describe('DogWalkCard — loading and error states', () => {
  it('shows a loading indicator while the API has not responded', () => {
    fetch.mockReturnValueOnce(new Promise(() => {}))
    render(<DogWalkCard />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows an error message when the API call fails', async () => {
    mockFetchError()
    render(<DogWalkCard />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })

  it('shows an error message when the API returns a non-ok status', async () => {
    mockFetchStatus(500)
    render(<DogWalkCard />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })
})

describe('DogWalkCard — route display', () => {
  it('displays the top recommended route name prominently', async () => {
    mockFetchOk(makeApiResponse())
    render(<DogWalkCard />)
    await waitFor(() => expect(screen.getByTestId('dog-walk-card')).toBeInTheDocument())
    expect(screen.getByTestId('top-route-name')).toHaveTextContent('Park Loop')
  })

  it('displays the top route duration', async () => {
    mockFetchOk(makeApiResponse())
    render(<DogWalkCard />)
    await waitFor(() => expect(screen.getByTestId('dog-walk-card')).toBeInTheDocument())
    expect(screen.getByTestId('top-route-name').closest('[data-testid="top-route"]') ?? screen.getByTestId('dog-walk-card'))
      .toHaveTextContent('25 min')
  })

  it('displays the top route distance', async () => {
    mockFetchOk(makeApiResponse())
    render(<DogWalkCard />)
    await waitFor(() => expect(screen.getByTestId('dog-walk-card')).toBeInTheDocument())
    expect(screen.getByTestId('dog-walk-card')).toHaveTextContent('2.1 km')
  })

  it('displays the conditions label', async () => {
    mockFetchOk(makeApiResponse({ conditions: 'Wet' }))
    render(<DogWalkCard />)
    await waitFor(() => expect(screen.getByTestId('conditions-label')).toBeInTheDocument())
    expect(screen.getByTestId('conditions-label')).toHaveTextContent('Wet')
  })

  it('lists all routes in the card', async () => {
    mockFetchOk(makeApiResponse())
    render(<DogWalkCard />)
    await waitFor(() => expect(screen.getByTestId('dog-walk-card')).toBeInTheDocument())
    expect(screen.getAllByTestId(/^route-item-/)).toHaveLength(3)
  })

  it('visually distinguishes unsuitable routes', async () => {
    mockFetchOk(
      makeApiResponse({
        routes: [
          makeRoute(),
          makeRoute({ id: 'river-trail', name: 'River Trail', mud_sensitivity: 3, suitable: false }),
        ],
      })
    )
    render(<DogWalkCard />)
    await waitFor(() => expect(screen.getByTestId('dog-walk-card')).toBeInTheDocument())
    const unsuitable = screen.getByTestId(/^route-item-river-trail/)
    expect(unsuitable).toHaveAttribute('data-suitable', 'false')
  })

  it('fetches from /api/dog-walk', async () => {
    mockFetchOk(makeApiResponse())
    render(<DogWalkCard />)
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/dog-walk'))
  })
})

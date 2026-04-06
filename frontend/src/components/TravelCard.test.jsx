import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import TravelCard from './TravelCard'
import App from '../App'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const makeRoute = (overrides = {}) => ({
  travel_time_seconds: 1800,
  delay_seconds: 50,
  distance_meters: 20000,
  description: 'via A3 and M25',
  delay_colour: 'green',
  ...overrides,
})

const makeCommuter = (overrides = {}) => ({
  name: 'Ryan',
  mode: 'office',
  drops: [],
  routes: [makeRoute(), makeRoute({ description: 'via A316' })],
  incidents: [],
  ...overrides,
})

const makeApiResponse = (overrides = {}) => ({
  commuters: [makeCommuter()],
  is_stale: false,
  ...overrides,
})

// ---------------------------------------------------------------------------
// TravelCard — individual commuter card (pure presentational)
// ---------------------------------------------------------------------------

describe('TravelCard — header', () => {
  it('shows the commuter name in the card header', () => {
    render(<TravelCard commuter={makeCommuter({ name: 'Ryan' })} />)
    expect(screen.getByText('Ryan')).toBeInTheDocument()
  })

  it('shows a different commuter name', () => {
    render(<TravelCard commuter={makeCommuter({ name: 'Emily' })} />)
    expect(screen.getByText('Emily')).toBeInTheDocument()
  })
})

describe('TravelCard — route display', () => {
  it('renders 2 route cards', () => {
    render(<TravelCard commuter={makeCommuter()} />)
    const cards = document.querySelectorAll('[data-testid="route-card"]')
    expect(cards).toHaveLength(2)
  })

  it('displays the route description', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ description: 'via A3 and M25' })],
    })
    render(<TravelCard commuter={commuter} />)
    expect(screen.getByText('via A3 and M25')).toBeInTheDocument()
  })

  it('displays travel time in minutes', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ travel_time_seconds: 2700 })],
    })
    render(<TravelCard commuter={commuter} />)
    expect(screen.getByText('45 min')).toBeInTheDocument()
  })
})

describe('TravelCard — colour states', () => {
  it('applies green colour indicator', () => {
    render(
      <TravelCard
        commuter={makeCommuter({
          routes: [makeRoute({ delay_colour: 'green' })],
        })}
      />
    )
    expect(document.querySelector('[data-colour="green"]')).toBeInTheDocument()
  })

  it('applies amber colour indicator', () => {
    render(
      <TravelCard
        commuter={makeCommuter({
          routes: [makeRoute({ delay_colour: 'amber' })],
        })}
      />
    )
    expect(document.querySelector('[data-colour="amber"]')).toBeInTheDocument()
  })

  it('applies red colour indicator', () => {
    render(
      <TravelCard
        commuter={makeCommuter({
          routes: [makeRoute({ delay_colour: 'red' })],
        })}
      />
    )
    expect(document.querySelector('[data-colour="red"]')).toBeInTheDocument()
  })
})

describe('TravelCard — incidents', () => {
  it('shows incident description when incidents are present', () => {
    const commuter = makeCommuter({
      incidents: [{ type: 'ROAD_WORKS', description: 'Roadworks on A3', road: 'A3' }],
    })
    render(<TravelCard commuter={commuter} />)
    expect(screen.getByText('Roadworks on A3')).toBeInTheDocument()
  })

  it('does not render an incident section when there are no incidents', () => {
    render(<TravelCard commuter={makeCommuter({ incidents: [] })} />)
    expect(screen.queryByTestId('incident-list')).not.toBeInTheDocument()
  })
})

describe('TravelCard — destination label', () => {
  it('shows "Work" as destination for office mode with no drops', () => {
    render(<TravelCard commuter={makeCommuter({ mode: 'office', drops: [] })} />)
    expect(screen.getByText('Work')).toBeInTheDocument()
  })

  it('shows "Home" as destination for wfh mode with drops', () => {
    render(<TravelCard commuter={makeCommuter({ mode: 'wfh', drops: ['dog'] })} />)
    expect(screen.getByText('Home')).toBeInTheDocument()
  })
})

// ---------------------------------------------------------------------------
// App — dashboard layout with per-commuter cards
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

const WEATHER_STUB = {
  current: {
    temperature_celsius: 10,
    apparent_temperature_celsius: 8,
    weather_description: 'Cloudy',
    wind_speed_kmh: 15,
    humidity_percent: 70,
  },
  forecast: [],
}

const CALENDAR_STUB = { events: [] }

function mockFetchByUrl(travelData) {
  fetch.mockImplementation((url) => {
    if (url === '/api/travel') {
      return Promise.resolve({ ok: true, json: async () => travelData })
    }
    if (url === '/api/weather') {
      return Promise.resolve({ ok: true, json: async () => WEATHER_STUB })
    }
    if (url === '/api/calendar') {
      return Promise.resolve({ ok: true, json: async () => CALENDAR_STUB })
    }
    return Promise.reject(new Error(`Unexpected fetch: ${url}`))
  })
}

function mockFetchError() {
  fetch.mockImplementation((url) => {
    if (url === '/api/travel') return Promise.reject(new Error('Network error'))
    if (url === '/api/weather') {
      return Promise.resolve({ ok: true, json: async () => WEATHER_STUB })
    }
    if (url === '/api/calendar') {
      return Promise.resolve({ ok: true, json: async () => CALENDAR_STUB })
    }
    return Promise.reject(new Error(`Unexpected fetch: ${url}`))
  })
}

describe('App — travel section rendering', () => {
  it('shows 2 travel cards when both commuters are active', async () => {
    mockFetchByUrl(
      makeApiResponse({
        commuters: [makeCommuter({ name: 'Ryan' }), makeCommuter({ name: 'Emily' })],
      })
    )
    render(<App />)
    await waitFor(() => expect(screen.getByText('Ryan')).toBeInTheDocument())
    expect(screen.getByText('Emily')).toBeInTheDocument()
    expect(screen.getAllByTestId('travel-card')).toHaveLength(2)
  })

  it('shows 1 travel card when only one commuter is active', async () => {
    mockFetchByUrl(makeApiResponse({ commuters: [makeCommuter({ name: 'Ryan' })] }))
    render(<App />)
    await waitFor(() => expect(screen.getByText('Ryan')).toBeInTheDocument())
    expect(screen.getAllByTestId('travel-card')).toHaveLength(1)
  })

  it('hides the travel section when commuters array is empty', async () => {
    mockFetchByUrl(makeApiResponse({ commuters: [] }))
    render(<App />)
    await waitFor(() => expect(screen.queryByTestId('travel-section')).not.toBeInTheDocument())
  })

  it('shows a loading indicator while the API has not responded', async () => {
    fetch.mockImplementation(() => new Promise(() => {}))
    render(<App />)
    const statuses = screen.getAllByRole('status')
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses.some((el) => el.textContent.includes('Loading travel'))).toBe(true)
  })

  it('shows an error message when the API call fails', async () => {
    mockFetchError()
    render(<App />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })

  it('shows a stale data warning when is_stale is true', async () => {
    mockFetchByUrl(makeApiResponse({ is_stale: true }))
    render(<App />)
    await waitFor(() =>
      expect(screen.getByTestId('stale-warning')).toBeInTheDocument()
    )
  })

  it('shows each commuter only on their own card', async () => {
    mockFetchByUrl(
      makeApiResponse({
        commuters: [
          makeCommuter({
            name: 'Ryan',
            incidents: [{ type: 'ROAD_WORKS', description: 'Roadworks on A3', road: 'A3' }],
          }),
          makeCommuter({ name: 'Emily', incidents: [] }),
        ],
      })
    )
    render(<App />)
    await waitFor(() => expect(screen.getByText('Ryan')).toBeInTheDocument())
    expect(screen.getByText('Roadworks on A3')).toBeInTheDocument()
    // Emily card should have no incident list
    const emilyCard = screen.getByText('Emily').closest('[data-testid="travel-card"]')
    expect(emilyCard.querySelector('[data-testid="incident-list"]')).toBeNull()
  })
})

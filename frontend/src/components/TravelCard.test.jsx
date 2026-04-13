import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import TravelCard from './TravelCard'

vi.mock('leaflet', () => ({
  default: {
    map: vi.fn(() => ({ remove: vi.fn(), fitBounds: vi.fn() })),
    tileLayer: vi.fn(() => ({ addTo: vi.fn() })),
    polyline: vi.fn(() => ({ addTo: vi.fn(), getBounds: vi.fn(() => ({})) })),
    circleMarker: vi.fn(() => ({ addTo: vi.fn() })),
    latLngBounds: vi.fn(() => ({})),
  },
}))
// Note: data-commuter="Ryan" attribute used for per-card selection in multi-commuter scenarios

const makeRoute = (overrides = {}) => ({
  travel_time_seconds: 1800,
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

// ── Loading & error states ──────────────────────────────────────────────────

describe('TravelCard — loading state', () => {
  it('shows a loading indicator when loading is true', () => {
    render(<TravelCard loading={true} commuters={[]} isStale={false} error={null} />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})

describe('TravelCard — error state', () => {
  it('shows an error message when error is set', () => {
    render(<TravelCard loading={false} commuters={[]} isStale={false} error="Network error" />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})

// ── Card presence ───────────────────────────────────────────────────────────

describe('TravelCard — card presence', () => {
  it('renders 2 travel cards when 2 commuters are active', () => {
    const commuters = [
      makeCommuter({ name: 'Ryan' }),
      makeCommuter({ name: 'Emily' }),
    ]
    render(<TravelCard loading={false} commuters={commuters} isStale={false} error={null} />)
    expect(screen.getAllByTestId('travel-card')).toHaveLength(2)
  })

  it('renders 1 travel card when only 1 commuter is active', () => {
    render(
      <TravelCard
        loading={false}
        commuters={[makeCommuter({ name: 'Ryan' })]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getAllByTestId('travel-card')).toHaveLength(1)
  })

  it('renders nothing when commuters array is empty', () => {
    const { container } = render(
      <TravelCard loading={false} commuters={[]} isStale={false} error={null} />
    )
    expect(screen.queryByTestId('travel-card')).not.toBeInTheDocument()
    expect(container.firstChild).toBeNull()
  })
})

// ── Card content ────────────────────────────────────────────────────────────

describe('TravelCard — card content', () => {
  it('shows the commuter name in the card header', () => {
    render(
      <TravelCard
        loading={false}
        commuters={[makeCommuter({ name: 'Ryan' })]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('Ryan')).toBeInTheDocument()
  })

  it('shows the correct name for each commuter', () => {
    const commuters = [
      makeCommuter({ name: 'Ryan' }),
      makeCommuter({ name: 'Emily' }),
    ]
    render(<TravelCard loading={false} commuters={commuters} isStale={false} error={null} />)
    expect(screen.getByText('Ryan')).toBeInTheDocument()
    expect(screen.getByText('Emily')).toBeInTheDocument()
  })

  it('renders 2 route cards per commuter', () => {
    render(
      <TravelCard
        loading={false}
        commuters={[makeCommuter({ name: 'Ryan' })]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getAllByTestId('route-card')).toHaveLength(2)
  })

  it('shows the route description', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ description: 'via A3 and M25' })],
    })
    render(
      <TravelCard loading={false} commuters={[commuter]} isStale={false} error={null} />
    )
    expect(screen.getByText('via A3 and M25')).toBeInTheDocument()
  })

  it('displays travel time in minutes for sub-hour journeys', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ travel_time_seconds: 2700 })],
    })
    render(
      <TravelCard loading={false} commuters={[commuter]} isStale={false} error={null} />
    )
    expect(screen.getByText('45 min')).toBeInTheDocument()
  })

  it('displays travel time as hours and minutes for journeys over 60 minutes', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ travel_time_seconds: 7500 })], // 125 min = 2 hrs 5 min
    })
    render(
      <TravelCard loading={false} commuters={[commuter]} isStale={false} error={null} />
    )
    expect(screen.getByText('2 hrs 5 min')).toBeInTheDocument()
  })

  it('displays exactly 1 hr for a 60-minute journey', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ travel_time_seconds: 3600 })],
    })
    render(
      <TravelCard loading={false} commuters={[commuter]} isStale={false} error={null} />
    )
    expect(screen.getByText('1 hr 0 min')).toBeInTheDocument()
  })

  it('displays whole hours when there are no remaining minutes', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ travel_time_seconds: 7200 })], // exactly 2 hours
    })
    render(
      <TravelCard loading={false} commuters={[commuter]} isStale={false} error={null} />
    )
    expect(screen.getByText('2 hrs 0 min')).toBeInTheDocument()
  })
})

// ── Colour states ───────────────────────────────────────────────────────────

describe('TravelCard — colour states', () => {
  it('applies green colour indicator for a green-state route', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ delay_colour: 'green' })],
    })
    render(
      <TravelCard loading={false} commuters={[commuter]} isStale={false} error={null} />
    )
    expect(document.querySelector('[data-colour="green"]')).toBeInTheDocument()
  })

  it('applies amber colour indicator for an amber-state route', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ delay_colour: 'amber' })],
    })
    render(
      <TravelCard loading={false} commuters={[commuter]} isStale={false} error={null} />
    )
    expect(document.querySelector('[data-colour="amber"]')).toBeInTheDocument()
  })

  it('applies red colour indicator for a red-state route', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ delay_colour: 'red' })],
    })
    render(
      <TravelCard loading={false} commuters={[commuter]} isStale={false} error={null} />
    )
    expect(document.querySelector('[data-colour="red"]')).toBeInTheDocument()
  })
})

// ── Incidents ───────────────────────────────────────────────────────────────

describe('TravelCard — incidents', () => {
  it('shows incident description when incidents are present', () => {
    const commuter = makeCommuter({
      incidents: [{ type: 'ROAD_WORKS', description: 'Roadworks on A3', road: 'A3' }],
    })
    render(
      <TravelCard loading={false} commuters={[commuter]} isStale={false} error={null} />
    )
    expect(screen.getByText('Roadworks on A3')).toBeInTheDocument()
  })

  it('does not render an incident section when there are no incidents', () => {
    render(
      <TravelCard
        loading={false}
        commuters={[makeCommuter({ incidents: [] })]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.queryByTestId('incident-list')).not.toBeInTheDocument()
  })

  it("shows only Ryan's incidents on Ryan's card, not Emily's", () => {
    const commuters = [
      makeCommuter({
        name: 'Ryan',
        incidents: [{ type: 'ROAD_WORKS', description: 'Roadworks on A3', road: 'A3' }],
      }),
      makeCommuter({ name: 'Emily', incidents: [] }),
    ]
    render(<TravelCard loading={false} commuters={commuters} isStale={false} error={null} />)
    const ryanCard = document.querySelector('[data-commuter="Ryan"]')
    const emilyCard = document.querySelector('[data-commuter="Emily"]')
    expect(ryanCard.querySelector('[data-testid="incident-list"]')).toBeInTheDocument()
    expect(emilyCard.querySelector('[data-testid="incident-list"]')).not.toBeInTheDocument()
  })
})

// ── Route destination labels ────────────────────────────────────────────────

describe('TravelCard — route destination labels', () => {
  it('shows "Work" as destination label for office mode', () => {
    render(
      <TravelCard
        loading={false}
        commuters={[makeCommuter({ mode: 'office', drops: [] })]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText(/Work/)).toBeInTheDocument()
  })

  it('shows "Home" as destination label for wfh mode with drops', () => {
    render(
      <TravelCard
        loading={false}
        commuters={[makeCommuter({ mode: 'wfh', drops: ['dog'] })]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText(/Home/)).toBeInTheDocument()
  })
})

// ── Route map ───────────────────────────────────────────────────────────────

describe('TravelCard — route map', () => {
  it('shows a route map when encoded_polyline is present', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ encoded_polyline: '??' })],
    })
    render(<TravelCard loading={false} commuters={[commuter]} isStale={false} error={null} />)
    expect(screen.getByTestId('route-map')).toBeInTheDocument()
  })

  it('does not show a route map when encoded_polyline is absent', () => {
    render(
      <TravelCard
        loading={false}
        commuters={[makeCommuter({ routes: [makeRoute()] })]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.queryByTestId('route-map')).not.toBeInTheDocument()
  })

  it('does not show a route map when encoded_polyline is empty string', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ encoded_polyline: '' })],
    })
    render(<TravelCard loading={false} commuters={[commuter]} isStale={false} error={null} />)
    expect(screen.queryByTestId('route-map')).not.toBeInTheDocument()
  })
})

// ── Stale indicator ─────────────────────────────────────────────────────────

describe('TravelCard — stale indicator', () => {
  it('shows stale data warning when isStale is true', () => {
    render(
      <TravelCard
        loading={false}
        commuters={[makeCommuter()]}
        isStale={true}
        error={null}
      />
    )
    expect(screen.getByTestId('stale-warning')).toBeInTheDocument()
  })

  it('does not show stale warning when isStale is false', () => {
    render(
      <TravelCard
        loading={false}
        commuters={[makeCommuter()]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.queryByTestId('stale-warning')).not.toBeInTheDocument()
  })
})

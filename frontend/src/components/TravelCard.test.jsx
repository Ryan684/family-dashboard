import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import TravelCard from './TravelCard'

// Note: data-commuter="Ryan" attribute used for per-card selection in multi-commuter scenarios

const makeRoute = (overrides = {}) => ({
  travel_time_seconds: 1800,
  description: 'via A3 and M25',
  delay_colour: 'green',
  delay_seconds: 0,
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
    render(
      <TravelCard loading={true} commuters={[]} isStale={false} error={null} />
    )
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})

describe('TravelCard — error state', () => {
  it('shows an error message when error is set', () => {
    render(
      <TravelCard
        loading={false}
        commuters={[]}
        isStale={false}
        error="Network error"
      />
    )
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
    render(
      <TravelCard
        loading={false}
        commuters={commuters}
        isStale={false}
        error={null}
      />
    )
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
    render(
      <TravelCard
        loading={false}
        commuters={commuters}
        isStale={false}
        error={null}
      />
    )
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
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('via A3 and M25')).toBeInTheDocument()
  })

  it('displays travel time in minutes for sub-hour journeys', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ travel_time_seconds: 2700 })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('45 min')).toBeInTheDocument()
  })

  it('displays travel time as hours and minutes for journeys over 60 minutes', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ travel_time_seconds: 7500 })], // 125 min = 2 hrs 5 min
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('2 hrs 5 min')).toBeInTheDocument()
  })

  it('displays exactly 1 hr for a 60-minute journey', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ travel_time_seconds: 3600 })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('1 hr 0 min')).toBeInTheDocument()
  })

  it('displays whole hours when there are no remaining minutes', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ travel_time_seconds: 7200 })], // exactly 2 hours
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
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
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(document.querySelector('[data-colour="green"]')).toBeInTheDocument()
  })

  it('applies amber colour indicator for an amber-state route', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ delay_colour: 'amber' })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(document.querySelector('[data-colour="amber"]')).toBeInTheDocument()
  })

  it('applies red colour indicator for a red-state route', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ delay_colour: 'red' })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(document.querySelector('[data-colour="red"]')).toBeInTheDocument()
  })
})

// ── Delay minutes ────────────────────────────────────────────────────────────

describe('TravelCard — delay minutes', () => {
  it('shows the delay minutes alongside the status label when delayed', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ delay_colour: 'amber', delay_seconds: 480 })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('+8 min · Slow')).toBeInTheDocument()
  })

  it('shows only the status label with no "+" prefix when delay_seconds is zero', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ delay_colour: 'green', delay_seconds: 0 })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('On time')).toBeInTheDocument()
  })
})

// ── Incidents ───────────────────────────────────────────────────────────────

describe('TravelCard — incidents', () => {
  it('shows incident description when incidents are present', () => {
    const commuter = makeCommuter({
      incidents: [
        { type: 'ROAD_WORKS', description: 'Roadworks on A3', road: 'A3' },
      ],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
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
        incidents: [
          { type: 'ROAD_WORKS', description: 'Roadworks on A3', road: 'A3' },
        ],
      }),
      makeCommuter({ name: 'Emily', incidents: [] }),
    ]
    render(
      <TravelCard
        loading={false}
        commuters={commuters}
        isStale={false}
        error={null}
      />
    )
    const ryanCard = document.querySelector('[data-commuter="Ryan"]')
    const emilyCard = document.querySelector('[data-commuter="Emily"]')
    expect(
      ryanCard.querySelector('[data-testid="incident-list"]')
    ).toBeInTheDocument()
    expect(
      emilyCard.querySelector('[data-testid="incident-list"]')
    ).not.toBeInTheDocument()
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

// ── Distance display ────────────────────────────────────────────────────────

describe('TravelCard — distance display', () => {
  it('renders distance in miles when distance_meters is provided', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ description: 'via A3', distance_meters: 25000 })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText(/15\.5 mi/)).toBeInTheDocument()
  })

  it('renders distance inline with the route description', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ description: 'via A3', distance_meters: 25000 })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('via A3 · 15.5 mi')).toBeInTheDocument()
  })

  it('omits the distance when distance_meters is null', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ description: 'via A3', distance_meters: null })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.queryByText(/\bmi\b/)).not.toBeInTheDocument()
  })

  it('omits the distance when distance_meters is absent', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ description: 'via A3' })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.queryByText(/\bmi\b/)).not.toBeInTheDocument()
  })

  it('rounds to one decimal place', () => {
    // 16093 m = 9.999... mi → rounds to 10.0 mi
    const commuter = makeCommuter({
      routes: [makeRoute({ description: 'via A3', distance_meters: 16093 })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText(/10\.0 mi/)).toBeInTheDocument()
  })
})

// ── Route map ───────────────────────────────────────────────────────────────

describe('TravelCard — route map', () => {
  it('never renders a route map regardless of polyline data', () => {
    const commuter = makeCommuter({
      routes: [makeRoute({ encoded_polyline: '??' })],
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
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

// ── Departure time display ───────────────────────────────────────────────────

describe('TravelCard — departure time display', () => {
  it('shows departure time when departure_time is provided', () => {
    const commuter = makeCommuter({ departure_time: '07:30', eta: '08:15' })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('Dep 07:30')).toBeInTheDocument()
  })

  it('shows ETA alongside departure time', () => {
    const commuter = makeCommuter({ departure_time: '07:30', eta: '08:15' })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('ETA 08:15')).toBeInTheDocument()
  })

  it('does not render a departure time element when departure_time is absent', () => {
    const commuter = makeCommuter()
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.queryByTestId('commuter-departure')).not.toBeInTheDocument()
  })

  it('does not render a departure time element when departure_time is null', () => {
    const commuter = makeCommuter({ departure_time: null })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.queryByTestId('commuter-departure')).not.toBeInTheDocument()
  })
})

// ── ETA display ─────────────────────────────────────────────────────────────

describe('TravelCard — ETA display', () => {
  it('shows ETA when commuter.eta is provided', () => {
    const commuter = makeCommuter({ eta: '08:15' })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('ETA 08:15')).toBeInTheDocument()
  })

  it('does not render an ETA element when eta is null', () => {
    const commuter = makeCommuter({ eta: null })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.queryByTestId('commuter-eta')).not.toBeInTheDocument()
  })

  it('does not render an ETA element when eta field is absent', () => {
    const commuter = makeCommuter() // no eta field
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.queryByTestId('commuter-eta')).not.toBeInTheDocument()
  })

  it('shows the correct ETA for each commuter independently', () => {
    const commuters = [
      makeCommuter({ name: 'Ryan', eta: '08:00' }),
      makeCommuter({ name: 'Emily', eta: '09:30' }),
    ]
    render(
      <TravelCard
        loading={false}
        commuters={commuters}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('ETA 08:00')).toBeInTheDocument()
    expect(screen.getByText('ETA 09:30')).toBeInTheDocument()
  })
})

// ── Latest departure display ────────────────────────────────────────────────

describe('TravelCard — latest departure display', () => {
  it('shows the latest departure when latest_departure is provided', () => {
    const commuter = makeCommuter({
      departure_time: '07:10',
      latest_departure: '07:03',
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('Leave by 07:03')).toBeInTheDocument()
  })

  it('renders the latest departure below the intended departure time', () => {
    const commuter = makeCommuter({
      departure_time: '07:10',
      latest_departure: '07:03',
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    const departure = screen.getByTestId('commuter-departure')
    const latest = screen.getByTestId('commuter-latest-departure')
    expect(
      departure.compareDocumentPosition(latest) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy()
  })

  it('does not render a latest departure element when latest_departure is null', () => {
    const commuter = makeCommuter({
      departure_time: '07:10',
      latest_departure: null,
    })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(
      screen.queryByTestId('commuter-latest-departure')
    ).not.toBeInTheDocument()
  })

  it('does not render a latest departure element when the field is absent', () => {
    const commuter = makeCommuter({ departure_time: '07:10' })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(
      screen.queryByTestId('commuter-latest-departure')
    ).not.toBeInTheDocument()
  })

  it('shows the latest departure when no departure time is configured', () => {
    const commuter = makeCommuter({ latest_departure: '07:03' })
    render(
      <TravelCard
        loading={false}
        commuters={[commuter]}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('Leave by 07:03')).toBeInTheDocument()
  })

  it('shows each commuter their own latest departure', () => {
    const commuters = [
      makeCommuter({ name: 'Ryan', latest_departure: '07:03' }),
      makeCommuter({ name: 'Emily', latest_departure: '08:14' }),
    ]
    render(
      <TravelCard
        loading={false}
        commuters={commuters}
        isStale={false}
        error={null}
      />
    )
    expect(screen.getByText('Leave by 07:03')).toBeInTheDocument()
    expect(screen.getByText('Leave by 08:14')).toBeInTheDocument()
  })
})

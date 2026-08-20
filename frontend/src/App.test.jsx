import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, afterEach } from 'vitest'
import App from './App'

// Mock non-travel child components so they don't make their own fetch calls
vi.mock('./components/ClockCard', () => ({
  default: () => <div data-testid="clock-card" />,
}))
vi.mock('./components/WeatherCard', () => ({
  default: () => <div data-testid="weather-card" />,
}))
vi.mock('./components/CalendarCard', () => ({
  default: () => <div data-testid="calendar-card" />,
}))
vi.mock('./components/TomorrowCard', () => ({
  default: () => <div data-testid="tomorrow-card" />,
}))
vi.mock('./components/WarningBanner', () => ({
  default: () => <div data-testid="warning-banner" />,
}))

const makeRoute = (colour = 'green') => ({
  travel_time_seconds: 1800,
  description: 'via A3',
  delay_colour: colour,
})

const makeCommuter = (name, routeColour = 'green') => ({
  name,
  mode: 'office',
  drops: [],
  routes: [makeRoute(routeColour), makeRoute(routeColour)],
  incidents: [],
})

function makeTravelResponse(commuters) {
  return { commuters, is_stale: false }
}

function mockTravelFetch(travel) {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.resolve({ ok: true, json: async () => travel }))
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('App — travel section grid reflow', () => {
  it('renders 2 travel cards when both commuters are active', async () => {
    mockTravelFetch(
      makeTravelResponse([makeCommuter('Ryan'), makeCommuter('Emily')])
    )
    render(<App />)
    await waitFor(() =>
      expect(screen.getAllByTestId('travel-card')).toHaveLength(2)
    )
  })

  it('renders 1 travel card when only one commuter is active', async () => {
    mockTravelFetch(makeTravelResponse([makeCommuter('Ryan')]))
    render(<App />)
    await waitFor(() =>
      expect(screen.getAllByTestId('travel-card')).toHaveLength(1)
    )
  })

  it('hides the travel section when commuters array is empty', async () => {
    mockTravelFetch(makeTravelResponse([]))
    render(<App />)
    await waitFor(() =>
      expect(screen.queryByTestId('travel-section')).not.toBeInTheDocument()
    )
  })

  it('shows the travel section when at least one commuter is active', async () => {
    mockTravelFetch(makeTravelResponse([makeCommuter('Ryan')]))
    render(<App />)
    await waitFor(() =>
      expect(screen.getByTestId('travel-section')).toBeInTheDocument()
    )
  })

  it('hides the travel section when is_stale is true even with commuters', async () => {
    mockTravelFetch({ commuters: [makeCommuter('Ryan')], is_stale: true })
    render(<App />)
    await waitFor(() =>
      expect(screen.queryByTestId('travel-section')).not.toBeInTheDocument()
    )
  })

  it('shows the travel section while loading (before fetch resolves)', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise(() => {}))
    ) // never resolves
    render(<App />)
    // Initially travelLoading=true, so travel section is shown in loading state
    expect(screen.getByTestId('travel-section')).toBeInTheDocument()
  })

  it('shows the tomorrow section when the travel section is hidden', async () => {
    mockTravelFetch({ commuters: [makeCommuter('Ryan')], is_stale: true })
    render(<App />)
    await waitFor(() =>
      expect(screen.getByTestId('tomorrow-section')).toBeInTheDocument()
    )
  })

  it('hides the tomorrow section when the travel section is shown', async () => {
    mockTravelFetch(makeTravelResponse([makeCommuter('Ryan')]))
    render(<App />)
    await waitFor(() =>
      expect(screen.getByTestId('travel-section')).toBeInTheDocument()
    )
    expect(screen.queryByTestId('tomorrow-section')).not.toBeInTheDocument()
  })

  it('shows the tomorrow section when there are no commuters', async () => {
    mockTravelFetch(makeTravelResponse([]))
    render(<App />)
    await waitFor(() =>
      expect(screen.getByTestId('tomorrow-section')).toBeInTheDocument()
    )
  })

  it('hides the tomorrow section while travel is still loading', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise(() => {}))
    )
    render(<App />)
    expect(screen.queryByTestId('tomorrow-section')).not.toBeInTheDocument()
  })

  it('mounts both alert straps at once when a red route makes AlertBanner visible', async () => {
    // WarningBanner is stubbed above; this proves App mounts it unconditionally
    // alongside AlertBanner rather than one suppressing the other. The visual
    // consequence of both being live at once — the weather column's second
    // location losing detail under the bottom fade — is confirmed by rendering
    // the real app; see the comment above <WarningBanner /> in App.jsx and
    // weather_warning_banner.feature's "both straps active" scenario.
    mockTravelFetch(makeTravelResponse([makeCommuter('Ryan', 'red')]))
    render(<App />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(screen.getByTestId('warning-banner')).toBeInTheDocument()
  })

  it('shows travel error state when fetch returns a non-ok HTTP status', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({ ok: false, status: 500, json: async () => ({}) })
      )
    )
    render(<App />)
    // Wait for error state specifically — not just loading
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(screen.getByTestId('travel-section')).toBeInTheDocument()
  })

  it('shows travel error state when fetch rejects', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new Error('Network error')))
    )
    render(<App />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(screen.getByTestId('travel-section')).toBeInTheDocument()
  })
})

describe('App — masthead', () => {
  it('does not render the "Family Dashboard" / weekday-Edition heading row', async () => {
    mockTravelFetch(makeTravelResponse([]))
    render(<App />)
    await waitFor(() =>
      expect(screen.queryByTestId('travel-section')).not.toBeInTheDocument()
    )
    expect(screen.queryByText(/Family Dashboard/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Edition/i)).not.toBeInTheDocument()
  })
})

describe('App — stale indicator', () => {
  it('does not show stale warning when is_stale is false', async () => {
    mockTravelFetch({ commuters: [makeCommuter('Ryan')], is_stale: false })
    render(<App />)
    await waitFor(() =>
      expect(screen.getAllByTestId('travel-card')).toHaveLength(1)
    )
    expect(screen.queryByTestId('stale-warning')).not.toBeInTheDocument()
  })
})

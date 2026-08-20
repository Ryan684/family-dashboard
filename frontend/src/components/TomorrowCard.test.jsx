import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import TomorrowCard from './TomorrowCard'

const makeTomorrowLocation = (overrides = {}) => ({
  name: 'Home',
  icon: 'rain',
  weather_description: 'Light rain',
  daily_high_celsius: 17,
  daily_rainfall: { total_mm: 3.1, probability_percent: 70 },
  rain_windows: [{ start_hour: 14, end_hour: 17 }],
  ...overrides,
})

const makeApiResponse = (overrides = {}) => ({
  locations: [],
  tomorrow: {
    weekday: 'Wednesday',
    locations: [makeTomorrowLocation()],
  },
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

describe('TomorrowCard — loading and error states', () => {
  it('shows a loading indicator while the API has not responded', () => {
    fetch.mockReturnValueOnce(new Promise(() => {}))
    render(<TomorrowCard />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('fetches from /api/weather', async () => {
    mockFetchOk(makeApiResponse())
    render(<TomorrowCard />)
    await waitFor(() =>
      expect(screen.getByText('Light rain')).toBeInTheDocument()
    )
    expect(fetch).toHaveBeenCalledWith('/api/weather')
  })

  it('shows an error message when the API call fails', async () => {
    mockFetchError()
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })

  it('shows an error message when the API returns a non-ok status', async () => {
    fetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) })
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })
})

describe('TomorrowCard — no column label', () => {
  it('does not render a "Tomorrow" section label', async () => {
    mockFetchOk(makeApiResponse())
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByText('Tomorrow')).not.toBeInTheDocument()
  })

  it('does not show a weekday name anywhere', async () => {
    mockFetchOk(makeApiResponse())
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByText(/Wednesday/)).not.toBeInTheDocument()
  })
})

describe('TomorrowCard — location block', () => {
  it('displays the location name', async () => {
    mockFetchOk(makeApiResponse())
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
  })

  it('displays the daily high as the headline figure', async () => {
    mockFetchOk(makeApiResponse())
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('17°C')).toBeInTheDocument())
  })

  it('displays the weather description', async () => {
    mockFetchOk(makeApiResponse())
    render(<TomorrowCard />)
    await waitFor(() =>
      expect(screen.getByText('Light rain')).toBeInTheDocument()
    )
  })

  it('does not render a current temperature', async () => {
    mockFetchOk(
      makeApiResponse({
        locations: [
          {
            name: 'Home',
            current: { temperature_celsius: 8, weather_description: 'Overcast' },
            daily_high_celsius: 12,
          },
        ],
      })
    )
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('17°C')).toBeInTheDocument())
    expect(screen.queryByText('8°C')).not.toBeInTheDocument()
  })

  // The glyph is drawn from divs rather than an icon font, so these assert the
  // branch is taken at all; the shapes themselves are inline styles that jsdom
  // does not evaluate.
  it('renders a block for a sun glyph', async () => {
    mockFetchOk(
      makeApiResponse({
        tomorrow: {
          weekday: 'Wednesday',
          locations: [makeTomorrowLocation({ icon: 'sun' })],
        },
      })
    )
    render(<TomorrowCard />)
    await waitFor(() =>
      expect(screen.getByTestId('tomorrow-location-block')).toBeInTheDocument()
    )
  })

  it('renders a block for a cloud glyph', async () => {
    mockFetchOk(
      makeApiResponse({
        tomorrow: {
          weekday: 'Wednesday',
          locations: [makeTomorrowLocation({ icon: 'cloud' })],
        },
      })
    )
    render(<TomorrowCard />)
    await waitFor(() =>
      expect(screen.getByTestId('tomorrow-location-block')).toBeInTheDocument()
    )
  })

  it('renders a block when the icon is missing entirely', async () => {
    mockFetchOk(
      makeApiResponse({
        tomorrow: {
          weekday: 'Wednesday',
          locations: [makeTomorrowLocation({ icon: undefined })],
        },
      })
    )
    render(<TomorrowCard />)
    await waitFor(() =>
      expect(screen.getByTestId('tomorrow-location-block')).toBeInTheDocument()
    )
  })

  it('hides the description when it is absent', async () => {
    mockFetchOk(
      makeApiResponse({
        tomorrow: {
          weekday: 'Wednesday',
          locations: [makeTomorrowLocation({ weather_description: null })],
        },
      })
    )
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('17°C')).toBeInTheDocument())
    expect(screen.queryByText('Light rain')).not.toBeInTheDocument()
  })

  it('renders one block per tomorrow location', async () => {
    mockFetchOk(
      makeApiResponse({
        tomorrow: {
          weekday: 'Wednesday',
          locations: [
            makeTomorrowLocation({ name: 'Home' }),
            makeTomorrowLocation({ name: 'Guildford' }),
          ],
        },
      })
    )
    render(<TomorrowCard />)
    await waitFor(() =>
      expect(screen.getAllByTestId('tomorrow-location-block')).toHaveLength(2)
    )
  })
})

describe('TomorrowCard — rainfall', () => {
  it('displays rainfall total and probability', async () => {
    mockFetchOk(makeApiResponse())
    render(<TomorrowCard />)
    await waitFor(() =>
      expect(screen.getByText(/Rain: 3\.1 mm · 70% chance/)).toBeInTheDocument()
    )
  })

  it('does not show a rainfall line when total_mm is 0', async () => {
    mockFetchOk(
      makeApiResponse({
        tomorrow: {
          weekday: 'Wednesday',
          locations: [
            makeTomorrowLocation({
              daily_rainfall: { total_mm: 0, probability_percent: 20 },
            }),
          ],
        },
      })
    )
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByText(/Rain:/)).not.toBeInTheDocument()
  })

  it('does not show a rainfall line when daily_rainfall is absent', async () => {
    mockFetchOk(
      makeApiResponse({
        tomorrow: {
          weekday: 'Wednesday',
          locations: [makeTomorrowLocation({ daily_rainfall: undefined })],
        },
      })
    )
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByText(/Rain:/)).not.toBeInTheDocument()
  })
})

describe('TomorrowCard — rain windows', () => {
  it('displays rain windows when present', async () => {
    mockFetchOk(makeApiResponse())
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('2–5pm')).toBeInTheDocument())
  })

  it('does not show a rain window row when rain_windows is empty', async () => {
    mockFetchOk(
      makeApiResponse({
        tomorrow: {
          weekday: 'Wednesday',
          locations: [makeTomorrowLocation({ rain_windows: [] })],
        },
      })
    )
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByTestId('tomorrow-rain-windows')).not.toBeInTheDocument()
  })

  it('does not show a rain window row when rain_windows is absent', async () => {
    mockFetchOk(
      makeApiResponse({
        tomorrow: {
          weekday: 'Wednesday',
          locations: [makeTomorrowLocation({ rain_windows: undefined })],
        },
      })
    )
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByTestId('tomorrow-rain-windows')).not.toBeInTheDocument()
  })
})

describe('TomorrowCard — unavailable states', () => {
  it('shows an unavailable status when the payload has no tomorrow block', async () => {
    mockFetchOk({ locations: [], is_stale: false })
    render(<TomorrowCard />)
    await waitFor(() =>
      expect(screen.getByText(/Tomorrow unavailable/)).toBeInTheDocument()
    )
  })

  it('shows an unavailable status when tomorrow has no locations', async () => {
    mockFetchOk(
      makeApiResponse({ tomorrow: { weekday: 'Wednesday', locations: [] } })
    )
    render(<TomorrowCard />)
    await waitFor(() =>
      expect(screen.getByText(/Tomorrow unavailable/)).toBeInTheDocument()
    )
  })
})

describe('TomorrowCard — stale indicator', () => {
  // The weather card renders beside this one from the same endpoint and already
  // carries the indicator, so a second one is duplication — and does not fit.
  it('does not show a stale warning when is_stale is true', async () => {
    mockFetchOk(makeApiResponse({ is_stale: true }))
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByTestId('stale-warning')).not.toBeInTheDocument()
  })

  it('does not show a stale warning when is_stale is false', async () => {
    mockFetchOk(makeApiResponse({ is_stale: false }))
    render(<TomorrowCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByTestId('stale-warning')).not.toBeInTheDocument()
  })
})

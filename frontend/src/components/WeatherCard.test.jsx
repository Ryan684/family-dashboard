import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import WeatherCard from './WeatherCard'

const makeLocation = (overrides = {}) => ({
  name: 'Home',
  current: {
    temperature_celsius: 15,
    apparent_temperature_celsius: 12,
    weather_description: 'Partly cloudy',
    wind_speed_kmh: 18,
    humidity_percent: 72,
  },
  daily_high_celsius: 19,
  daily_rainfall: { total_mm: 4.2, probability_percent: 60 },
  rain_windows: [{ start_hour: 8, end_hour: 10 }, { start_hour: 14, end_hour: 16 }],
  ...overrides,
})

const makeApiResponse = (overrides = {}) => ({
  locations: [makeLocation()],
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

describe('WeatherCard — loading and error states', () => {
  it('shows a loading indicator while the API has not responded', () => {
    fetch.mockReturnValueOnce(new Promise(() => {}))
    render(<WeatherCard />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('fetches from /api/weather', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('Partly cloudy')).toBeInTheDocument()
    )
    expect(fetch).toHaveBeenCalledWith('/api/weather')
  })

  it('shows an error message when the API call fails', async () => {
    mockFetchError()
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })

  it('shows an error message when the API returns a non-ok HTTP status', async () => {
    fetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) })
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })
})

describe('WeatherCard — empty locations', () => {
  it('shows a status message when locations array is empty', async () => {
    mockFetchOk({ locations: [], is_stale: true })
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByRole('status')).toBeInTheDocument()
    )
  })

  it('renders no location blocks when locations is empty', async () => {
    mockFetchOk({ locations: [], is_stale: true })
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByRole('status')).toBeInTheDocument()
    )
    expect(screen.queryAllByTestId('weather-location-block')).toHaveLength(0)
  })
})

describe('WeatherCard — location block', () => {
  it('displays the location name', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
  })

  it('displays the current temperature in °C', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByText('15°C')).toBeInTheDocument())
  })

  it('displays the weather description', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('Partly cloudy')).toBeInTheDocument()
    )
  })

  it('displays the daily high as "High: X°C"', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText(/High: 19°C/)).toBeInTheDocument()
    )
  })

  it('does not display "Feels like"', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.queryByText(/Feels like/)).not.toBeInTheDocument()
    )
  })

  it('does not display hourly forecast entries', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryAllByTestId('forecast-entry')).toHaveLength(0)
  })
})

describe('WeatherCard — rainfall', () => {
  it('displays rainfall in "Rain: X mm · Y% chance" format', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText(/Rain: 4\.2 mm · 60% chance/)).toBeInTheDocument()
    )
  })

  it('uses "X% chance" not just "X%"', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText(/60% chance/)).toBeInTheDocument()
    )
  })

  it('does not show a rainfall line when daily_rainfall is absent', async () => {
    const location = makeLocation()
    delete location.daily_rainfall
    delete location.rain_windows
    mockFetchOk(makeApiResponse({ locations: [location] }))
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByText(/Rain:/)).not.toBeInTheDocument()
  })

  it('does not show a rainfall line when daily_rainfall is null', async () => {
    mockFetchOk(makeApiResponse({ locations: [makeLocation({ daily_rainfall: null })] }))
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByText(/Rain:/)).not.toBeInTheDocument()
  })
})

describe('WeatherCard — rain windows', () => {
  it('displays formatted hour ranges when rain_windows are present', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('8–10am, 2–4pm')).toBeInTheDocument()
    )
  })

  it('shows "all day" when total rainy hours is 18 or more', async () => {
    // One window of 18 hours: 0–18
    mockFetchOk(makeApiResponse({ locations: [makeLocation({ rain_windows: [{ start_hour: 0, end_hour: 18 }] })] }))
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('all day')).toBeInTheDocument()
    )
  })

  it('does not show "all day" when total rainy hours is 17', async () => {
    mockFetchOk(makeApiResponse({ locations: [makeLocation({ rain_windows: [{ start_hour: 0, end_hour: 17 }] })] }))
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByText('all day')).not.toBeInTheDocument()
    expect(screen.getByText(/12am–5pm/)).toBeInTheDocument()
  })

  it('hides the rain window row when rain_windows is empty', async () => {
    mockFetchOk(makeApiResponse({ locations: [makeLocation({ rain_windows: [] })] }))
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByTestId('rain-windows')).not.toBeInTheDocument()
  })

  it('hides the rain window row when rain_windows is absent', async () => {
    const location = makeLocation()
    delete location.rain_windows
    mockFetchOk(makeApiResponse({ locations: [location] }))
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.queryByTestId('rain-windows')).not.toBeInTheDocument()
  })

  it('formats a single-hour window without a range', async () => {
    mockFetchOk(makeApiResponse({ locations: [makeLocation({ rain_windows: [{ start_hour: 11, end_hour: 12 }] })] }))
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('11am')).toBeInTheDocument()
    )
  })

  it('formats a pm-only window', async () => {
    mockFetchOk(makeApiResponse({ locations: [makeLocation({ rain_windows: [{ start_hour: 14, end_hour: 17 }] })] }))
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('2–5pm')).toBeInTheDocument()
    )
  })

  it('formats a window crossing noon', async () => {
    mockFetchOk(makeApiResponse({ locations: [makeLocation({ rain_windows: [{ start_hour: 11, end_hour: 14 }] })] }))
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('11am–2pm')).toBeInTheDocument()
    )
  })

  it('formats a noon-start window as pm', async () => {
    // start_hour=12 must be labelled pm, not am
    mockFetchOk(makeApiResponse({ locations: [makeLocation({ rain_windows: [{ start_hour: 12, end_hour: 14 }] })] }))
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('12–2pm')).toBeInTheDocument()
    )
  })

  it('formats a window ending at noon as crossing noon', async () => {
    // end_hour=12 (noon) must be treated as pm, crossing from am
    mockFetchOk(makeApiResponse({ locations: [makeLocation({ rain_windows: [{ start_hour: 10, end_hour: 12 }] })] }))
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('10am–12pm')).toBeInTheDocument()
    )
  })

  it('formats a noon single-hour window as "12pm"', async () => {
    mockFetchOk(makeApiResponse({ locations: [makeLocation({ rain_windows: [{ start_hour: 12, end_hour: 13 }] })] }))
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('12pm')).toBeInTheDocument()
    )
  })
})

describe('WeatherCard — multiple locations', () => {
  it('renders one block per location', async () => {
    mockFetchOk(
      makeApiResponse({
        locations: [
          makeLocation({ name: 'Home' }),
          makeLocation({ name: "Ryan's Office", daily_high_celsius: 17 }),
        ],
      })
    )
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('Home')).toBeInTheDocument()
    )
    expect(screen.getByText("Ryan's Office")).toBeInTheDocument()
    expect(screen.getAllByTestId('weather-location-block')).toHaveLength(2)
  })

  it('displays each location name distinctly', async () => {
    mockFetchOk(
      makeApiResponse({
        locations: [
          makeLocation({ name: 'Home', current: { ...makeLocation().current, weather_description: 'Overcast' } }),
          makeLocation({ name: "Robyn's Office", current: { ...makeLocation().current, weather_description: 'Clear sky' } }),
        ],
      })
    )
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.getByText("Robyn's Office")).toBeInTheDocument()
  })

  it('shows a single block when only one location is returned', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() => expect(screen.getByText('Home')).toBeInTheDocument())
    expect(screen.getAllByTestId('weather-location-block')).toHaveLength(1)
  })
})

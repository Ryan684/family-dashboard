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

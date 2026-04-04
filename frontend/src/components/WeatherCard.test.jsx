import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import WeatherCard from './WeatherCard'

const makeForecastEntry = (overrides = {}) => ({
  time: '2026-04-04T09:00',
  temperature_celsius: 14,
  weather_description: 'Clear sky',
  precipitation_probability: 10,
  ...overrides,
})

const makeApiResponse = (overrides = {}) => ({
  current: {
    temperature_celsius: 15,
    apparent_temperature_celsius: 12,
    weather_description: 'Partly cloudy',
    wind_speed_kmh: 18,
    humidity_percent: 72,
  },
  forecast: [
    makeForecastEntry({ time: '2026-04-04T09:00' }),
    makeForecastEntry({ time: '2026-04-04T10:00' }),
    makeForecastEntry({ time: '2026-04-04T11:00' }),
    makeForecastEntry({ time: '2026-04-04T12:00' }),
    makeForecastEntry({ time: '2026-04-04T13:00' }),
    makeForecastEntry({ time: '2026-04-04T14:00' }),
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
    await waitFor(() =>
      expect(screen.getByRole('alert')).toBeInTheDocument()
    )
  })

  it('shows an error message when the API returns a non-ok HTTP status', async () => {
    fetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) })
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByRole('alert')).toBeInTheDocument()
    )
  })
})

describe('WeatherCard — current conditions', () => {
  it('displays the current temperature in °C', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('15°C')).toBeInTheDocument()
    )
  })

  it('displays the weather description', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('Partly cloudy')).toBeInTheDocument()
    )
  })

  it('displays the apparent temperature as "Feels like X°C"', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText(/Feels like 12°C/)).toBeInTheDocument()
    )
  })

  it('displays the wind speed in km/h', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText(/18 km\/h/)).toBeInTheDocument()
    )
  })

  it('displays the humidity as a percentage', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText(/72%/)).toBeInTheDocument()
    )
  })
})

describe('WeatherCard — forecast', () => {
  it('renders 6 forecast entries', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getAllByTestId('forecast-entry')).toHaveLength(6)
    )
  })

  it('displays the hour from each forecast time', async () => {
    mockFetchOk(makeApiResponse())
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('09:00')).toBeInTheDocument()
    )
  })

  it('displays the temperature for each forecast entry', async () => {
    mockFetchOk(
      makeApiResponse({
        forecast: [makeForecastEntry({ temperature_celsius: 14 })],
      })
    )
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getAllByText('14°C').length).toBeGreaterThan(0)
    )
  })

  it('displays the weather description for each forecast entry', async () => {
    mockFetchOk(
      makeApiResponse({
        forecast: [makeForecastEntry({ weather_description: 'Clear sky' })],
      })
    )
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText('Clear sky')).toBeInTheDocument()
    )
  })

  it('displays the precipitation probability for each forecast entry', async () => {
    mockFetchOk(
      makeApiResponse({
        forecast: [makeForecastEntry({ precipitation_probability: 40 })],
      })
    )
    render(<WeatherCard />)
    await waitFor(() =>
      expect(screen.getByText(/40%/)).toBeInTheDocument()
    )
  })
})

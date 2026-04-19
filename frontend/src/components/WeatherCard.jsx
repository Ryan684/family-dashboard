import { useState, useEffect } from 'react'

const STYLES_ID = 'weather-card-styles'

function injectStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLES_ID)) return
  const style = document.createElement('style')
  style.id = STYLES_ID
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;700&display=swap');

    :root {
      --wc-bg:             #0A1628;
      --wc-surface:        #0F1E38;
      --wc-border:         #1A2D4A;
      --wc-text-primary:   #E8F0FE;
      --wc-text-secondary: #5B7AA3;
      --wc-accent:         #00D4AA;
      --wc-red:            #E8523E;
    }

    .wc-wrap {
      font-family: 'Space Grotesk', 'Helvetica Neue', sans-serif;
      color: var(--wc-text-primary);
      padding: 32px 40px;
    }

    .wc-location {
      padding-bottom: 36px;
    }

    .wc-location + .wc-location {
      border-top: 1px solid var(--wc-border);
      padding-top: 36px;
    }

    .wc-location-name {
      font-size: 24px;
      font-weight: 400;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--wc-text-secondary);
      margin-bottom: 8px;
    }

    .wc-location-temp {
      font-family: 'Space Grotesk', 'Helvetica Neue', sans-serif;
      font-size: 64px;
      font-weight: 700;
      line-height: 1;
      color: var(--wc-text-primary);
      margin-bottom: 12px;
    }

    .wc-location-desc {
      font-size: 32px;
      font-weight: 300;
      color: var(--wc-text-primary);
      margin-bottom: 10px;
    }

    .wc-location-meta {
      display: flex;
      gap: 24px;
      font-size: 24px;
      font-weight: 300;
      color: var(--wc-text-secondary);
    }

    .wc-loading {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 160px;
      font-size: 24px;
      color: var(--wc-text-secondary);
    }

    .wc-error {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 160px;
      font-size: 24px;
      color: var(--wc-red);
      padding: 24px;
      text-align: center;
    }
  `
  document.head.appendChild(style)
}

function hourNum(h) {
  const mod = h % 12
  return mod === 0 ? 12 : mod
}

function formatHour(h) {
  return `${hourNum(h)}${h < 12 ? 'am' : 'pm'}`
}

function formatWindow({ start_hour, end_hour }) {
  if (end_hour - start_hour === 1) return formatHour(start_hour)
  if (start_hour >= 12 === end_hour >= 12) {
    return `${hourNum(start_hour)}–${formatHour(end_hour)}`
  }
  return `${formatHour(start_hour)}–${formatHour(end_hour)}`
}

function formatRainWindows(windows) {
  if (!windows || windows.length === 0) return null
  const totalHours = windows.reduce((sum, w) => sum + (w.end_hour - w.start_hour), 0)
  if (totalHours >= 18) return 'all day'
  return windows.map(formatWindow).join(', ')
}

function LocationBlock({ location }) {
  const { name, current, daily_high_celsius, daily_rainfall, rain_windows } = location
  const rainfallText =
    daily_rainfall != null
      ? `Rain: ${daily_rainfall.total_mm} mm · ${daily_rainfall.probability_percent}% chance`
      : null
  const windowsText = formatRainWindows(rain_windows)
  return (
    <div className="wc-location" data-testid="weather-location-block">
      <div className="wc-location-name">{name}</div>
      <div className="wc-location-temp">{current.temperature_celsius}°C</div>
      <div className="wc-location-desc">{current.weather_description}</div>
      <div className="wc-location-meta">
        <span>High: {daily_high_celsius}°C</span>
        {rainfallText && <span>{rainfallText}</span>}
      </div>
      {windowsText && (
        <div className="wc-location-meta" data-testid="rain-windows">{windowsText}</div>
      )}
    </div>
  )
}

function WeatherCard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    injectStyles()

    let cancelled = false

    fetch('/api/weather')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((json) => {
        if (!cancelled) {
          setData(json)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <div className="wc-loading" role="status">
        Loading weather…
      </div>
    )
  }

  if (error) {
    return (
      <div className="wc-error" role="alert">
        Unable to load weather data
      </div>
    )
  }

  const locations = data?.locations ?? []

  if (locations.length === 0) {
    return (
      <div className="wc-loading" role="status">
        Weather unavailable
      </div>
    )
  }

  return (
    <div className="wc-wrap">
      {locations.map((location, i) => (
        <LocationBlock key={i} location={location} />
      ))}
    </div>
  )
}

export default WeatherCard

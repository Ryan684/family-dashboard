import { useState, useEffect } from 'react'

const STYLES_ID = 'weather-card-styles'

function injectStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLES_ID)) return
  const style = document.createElement('style')
  style.id = STYLES_ID
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700&family=Jost:wght@300;400&display=swap');

    :root {
      --wc-bg:             #1A1714;
      --wc-surface:        #232019;
      --wc-border:         #2E2B26;
      --wc-text-primary:   #F8F5EF;
      --wc-text-secondary: #7A756E;
      --wc-accent:         #5BA4CF;
      --wc-red:            #D95F4B;
    }

    .wc-wrap {
      font-family: 'Jost', 'Helvetica Neue', sans-serif;
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
      font-family: 'Big Shoulders Display', 'Impact', sans-serif;
      font-size: 96px;
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

    .wc-location-high {
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

function LocationBlock({ location }) {
  const { name, current, daily_high_celsius } = location
  return (
    <div className="wc-location" data-testid="weather-location-block">
      <div className="wc-location-name">{name}</div>
      <div className="wc-location-temp">{current.temperature_celsius}°C</div>
      <div className="wc-location-desc">{current.weather_description}</div>
      <div className="wc-location-high">High: {daily_high_celsius}°C</div>
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

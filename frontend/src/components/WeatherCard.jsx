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
      --wc-rain:           #5BA4CF;
      --wc-red:            #D95F4B;
    }

    .wc-wrap {
      font-family: 'Jost', 'Helvetica Neue', sans-serif;
      color: var(--wc-text-primary);
      padding: 32px 40px;
    }

    .wc-current {
      margin-bottom: 40px;
    }

    .wc-temp {
      font-family: 'Big Shoulders Display', 'Impact', sans-serif;
      font-size: 96px;
      font-weight: 700;
      line-height: 1;
      color: var(--wc-text-primary);
      margin-bottom: 12px;
    }

    .wc-description {
      font-size: 36px;
      font-weight: 300;
      color: var(--wc-text-primary);
      margin-bottom: 16px;
    }

    .wc-meta {
      display: flex;
      gap: 32px;
      flex-wrap: wrap;
    }

    .wc-meta-item {
      font-size: 24px;
      font-weight: 300;
      color: var(--wc-text-secondary);
    }

    .wc-forecast {
      display: flex;
      gap: 12px;
      overflow-x: auto;
    }

    .wc-forecast-entry {
      flex: 1;
      min-width: 100px;
      background: var(--wc-surface);
      border: 1px solid var(--wc-border);
      border-radius: 12px;
      padding: 20px 16px;
      text-align: center;
    }

    .wc-forecast-time {
      font-size: 24px;
      font-weight: 400;
      color: var(--wc-text-secondary);
      margin-bottom: 10px;
    }

    .wc-forecast-temp {
      font-family: 'Big Shoulders Display', 'Impact', sans-serif;
      font-size: 40px;
      font-weight: 700;
      color: var(--wc-text-primary);
      margin-bottom: 8px;
    }

    .wc-forecast-desc {
      font-size: 20px;
      font-weight: 300;
      color: var(--wc-text-secondary);
      margin-bottom: 8px;
      min-height: 26px;
    }

    .wc-forecast-precip {
      font-size: 24px;
      font-weight: 300;
      color: var(--wc-rain);
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

function formatHour(isoTime) {
  return isoTime.slice(11, 16)
}

function ForecastEntry({ entry }) {
  return (
    <div className="wc-forecast-entry" data-testid="forecast-entry">
      <div className="wc-forecast-time">{formatHour(entry.time)}</div>
      <div className="wc-forecast-temp">{entry.temperature_celsius}°C</div>
      <div className="wc-forecast-desc">{entry.weather_description}</div>
      <div className="wc-forecast-precip">{entry.precipitation_probability}%</div>
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

  const { current, forecast } = data

  return (
    <div className="wc-wrap">
      <div className="wc-current">
        <div className="wc-temp">{current.temperature_celsius}°C</div>
        <div className="wc-description">{current.weather_description}</div>
        <div className="wc-meta">
          <span className="wc-meta-item">
            Feels like {current.apparent_temperature_celsius}°C
          </span>
          <span className="wc-meta-item">{current.wind_speed_kmh} km/h</span>
          <span className="wc-meta-item">{current.humidity_percent}%</span>
        </div>
      </div>

      <div className="wc-forecast">
        {forecast.map((entry, i) => (
          <ForecastEntry key={i} entry={entry} />
        ))}
      </div>
    </div>
  )
}

export default WeatherCard

import { useState, useEffect } from 'react'
import StaleTag from './StaleTag'
import { formatRainWindows } from '../weatherFormat'

function WeatherGlyph({ kind = 'cloud', size = 56 }) {
  const s = size
  const base = { position: 'relative', width: s, height: s, flexShrink: 0 }

  if (kind === 'sun') {
    return (
      <div style={base}>
        <div
          style={{
            position: 'absolute',
            inset: s * 0.18,
            borderRadius: '50%',
            background: 'var(--warn)',
            opacity: 0.95,
          }}
        />
      </div>
    )
  }

  if (kind === 'rain') {
    return (
      <div style={base}>
        <div
          style={{
            position: 'absolute',
            left: s * 0.06,
            top: s * 0.22,
            width: s * 0.82,
            height: s * 0.32,
            borderRadius: 999,
            background: 'var(--ink-dim)',
            opacity: 0.55,
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: s * 0.22,
            top: s * 0.1,
            width: s * 0.42,
            height: s * 0.36,
            borderRadius: '50%',
            background: 'var(--ink-dim)',
            opacity: 0.55,
          }}
        />
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: s * (0.22 + i * 0.18),
              top: s * 0.62,
              width: 2,
              height: s * 0.22,
              background: 'var(--ok)',
              opacity: 0.75,
              borderRadius: 2,
            }}
          />
        ))}
      </div>
    )
  }

  // default: cloud
  return (
    <div style={base}>
      <div
        style={{
          position: 'absolute',
          left: s * 0.06,
          top: s * 0.32,
          width: s * 0.82,
          height: s * 0.36,
          borderRadius: 999,
          background: 'var(--ink-dim)',
          opacity: 0.55,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: s * 0.22,
          top: s * 0.18,
          width: s * 0.42,
          height: s * 0.42,
          borderRadius: '50%',
          background: 'var(--ink-dim)',
          opacity: 0.55,
        }}
      />
    </div>
  )
}

function LocationBlock({ location }) {
  const {
    name,
    current,
    daily_high_celsius,
    daily_rainfall,
    rain_windows,
    icon,
  } = location
  const windowsText = formatRainWindows(rain_windows)

  return (
    <div
      style={{ display: 'flex', alignItems: 'flex-start', gap: 24 }}
      data-testid="weather-location-block"
    >
      <WeatherGlyph kind={icon ?? 'cloud'} size={56} />
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          flex: 1,
          minWidth: 0,
        }}
      >
        <div
          style={{
            fontFamily: 'var(--f-mono)',
            fontSize: 16,
            letterSpacing: '0.22em',
            textTransform: 'uppercase',
            color: 'var(--ink-faint)',
            fontWeight: 500,
          }}
        >
          {name}
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 16,
            flexWrap: 'wrap',
          }}
        >
          <div
            style={{
              fontFamily: 'var(--f-display)',
              fontWeight: 400,
              fontSize: 88,
              lineHeight: 0.9,
              color: 'var(--ink)',
              letterSpacing: '-0.03em',
              fontFeatureSettings: '"lnum","tnum"',
            }}
          >
            {current.temperature_celsius}°C
          </div>
          <div
            style={{
              fontFamily: 'var(--f-display)',
              fontStyle: 'italic',
              fontSize: 28,
              color: 'var(--ink-dim)',
              lineHeight: 1.1,
            }}
          >
            {current.weather_description}
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            gap: 36,
            flexWrap: 'wrap',
            alignItems: 'baseline',
            fontFamily: 'var(--f-display)',
            fontSize: 24,
            color: 'var(--ink-dim)',
            fontFeatureSettings: '"lnum","tnum"',
          }}
        >
          <span>High: {daily_high_celsius}°C</span>
          {daily_rainfall && daily_rainfall.total_mm > 0 && (
            <span>
              Rain: {daily_rainfall.total_mm} mm ·{' '}
              {daily_rainfall.probability_percent}% chance
            </span>
          )}
        </div>

        {windowsText && (
          <div
            style={{
              fontFamily: 'var(--f-mono)',
              fontSize: 15,
              letterSpacing: '0.18em',
              textTransform: 'uppercase',
              color: 'var(--ink-faint)',
              fontWeight: 500,
              marginTop: 2,
              fontVariantNumeric: 'tabular-nums',
            }}
            data-testid="rain-windows"
          >
            {windowsText}
          </div>
        )}
      </div>
    </div>
  )
}

const POLL_INTERVAL_MS = 60_000

function WeatherCard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    function fetchWeather() {
      fetch('/api/weather')
        .then((res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`)
          return res.json()
        })
        .then((json) => {
          if (!cancelled) {
            setData(json)
            setLoading(false)
            setError(null)
          }
        })
        .catch((err) => {
          if (!cancelled) {
            setError(err.message)
            setLoading(false)
          }
        })
    }

    fetchWeather()
    const id = setInterval(fetchWeather, POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          minHeight: 160,
          fontFamily: 'var(--f-mono)',
          fontSize: 18,
          letterSpacing: '0.1em',
          color: 'var(--ink-faint)',
        }}
        role="status"
      >
        Loading weather…
      </div>
    )
  }

  if (error) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          minHeight: 160,
          fontFamily: 'var(--f-display)',
          fontStyle: 'italic',
          fontSize: 28,
          color: 'var(--alert)',
          padding: '24px 0',
        }}
        role="alert"
      >
        Unable to load weather data
      </div>
    )
  }

  const locations = data?.locations ?? []

  if (locations.length === 0) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          minHeight: 160,
          fontFamily: 'var(--f-mono)',
          fontSize: 18,
          color: 'var(--ink-faint)',
        }}
        role="status"
      >
        Weather unavailable
      </div>
    )
  }

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
      {/* No "Weather" label: the column's content — temperatures, rain figures —
          already identifies it at a glance, and the label was pure redundancy
          on every render. The row still appears when stale, because that IS
          new information, not decoration — and reclaiming it in the common
          case is what keeps the second location's detail on screen when the
          traffic and weather alert straps are both up (weather's own window
          contains travel's, so this row is never occupied during that case). */}
      {data.is_stale && <StaleTag />}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {locations.map((loc, i) => (
          <div key={loc.name ?? i}>
            {i > 0 && (
              <div
                style={{
                  height: 1,
                  background: 'var(--rule)',
                  marginBottom: 20,
                }}
                aria-hidden="true"
              />
            )}
            <LocationBlock location={loc} />
          </div>
        ))}
      </div>
    </section>
  )
}

export default WeatherCard

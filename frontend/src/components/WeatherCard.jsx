import { useState, useEffect } from 'react'

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
            left: s * 0.06, top: s * 0.22,
            width: s * 0.82, height: s * 0.32,
            borderRadius: 999,
            background: 'var(--ink-dim)',
            opacity: 0.55,
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: s * 0.22, top: s * 0.10,
            width: s * 0.42, height: s * 0.36,
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
          left: s * 0.06, top: s * 0.32,
          width: s * 0.82, height: s * 0.36,
          borderRadius: 999,
          background: 'var(--ink-dim)',
          opacity: 0.55,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: s * 0.22, top: s * 0.18,
          width: s * 0.42, height: s * 0.42,
          borderRadius: '50%',
          background: 'var(--ink-dim)',
          opacity: 0.55,
        }}
      />
    </div>
  )
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
  const { name, current, daily_high_celsius, daily_rainfall, rain_windows, icon } = location
  const windowsText = formatRainWindows(rain_windows)

  return (
    <div
      style={{ display: 'flex', alignItems: 'flex-start', gap: 24 }}
      data-testid="weather-location-block"
    >
      <WeatherGlyph kind={icon ?? 'cloud'} size={56} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1, minWidth: 0 }}>
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

        <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, flexWrap: 'wrap' }}>
          <div
            style={{
              fontFamily: 'var(--f-display)',
              fontWeight: 400,
              fontSize: 88,
              lineHeight: 0.9,
              color: 'var(--ink)',
              letterSpacing: '-0.03em',
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
          }}
        >
          <span>High: {daily_high_celsius}°C</span>
          {daily_rainfall && (
            <span>
              Rain: {daily_rainfall.total_mm} mm · {daily_rainfall.probability_percent}% chance
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

function WeatherCard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
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
      <div
        style={{
          fontFamily: 'var(--f-mono)',
          fontSize: 18,
          letterSpacing: '0.22em',
          textTransform: 'uppercase',
          color: 'var(--ink-dim)',
          fontWeight: 500,
        }}
      >
        Weather
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
        {locations.map((loc, i) => (
          <div key={loc.name ?? i}>
            {i > 0 && (
              <div
                style={{ height: 1, background: 'var(--rule)', marginBottom: 28 }}
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

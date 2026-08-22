import { formatRainWindows } from '../weatherFormat'

/* Shared by WeatherCard (today) and TomorrowCard (tomorrow) — same glyph, same
   type sizes, same layout, for both days. A location either carries `current`
   (today: a live reading distinct from the day's high, so both are shown) or
   doesn't (tomorrow: no live reading exists, so the day's high is the headline
   figure and the separate "High:" line is redundant and omitted). */

export function WeatherGlyph({ kind = 'cloud', size = 56 }) {
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

export function LocationBlock({ location }) {
  const { name, current, daily_high_celsius, daily_rainfall, rain_windows, icon } =
    location
  const windowsText = formatRainWindows(rain_windows)
  const headlineTemp = current ? current.temperature_celsius : daily_high_celsius
  const headlineDescription = current
    ? current.weather_description
    : location.weather_description

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
            {headlineTemp}°C
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
            {headlineDescription}
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
          {current && <span>High: {daily_high_celsius}°C</span>}
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

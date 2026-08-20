import { useState, useEffect } from 'react'
import { formatRainWindows } from '../weatherFormat'

/* Purpose: a next-day planning glance — coat, wet school run — read from ~1m on
   a wall display, in the column freed when the travel section is hidden.

   Direction: "the almanac column". Today's card is a weather report: a big live
   number, present tense. Tomorrow is a printed forecast entry — quieter and more
   typographic, set like a line in an almanac rather than a second dashboard
   readout. It reuses today's exact type system one step down the hierarchy: the
   headline figure is 48px against today's 88px, and hierarchy is carried by size
   rather than colour, because dimming would cost legibility at viewing distance.

   The 28px rhythm and the hairline between blocks are load-bearing: today's
   "Home" row and tomorrow's "Home" row land on a shared baseline, which is what
   makes the pair read as a comparison rather than two unrelated lists. */

function TomorrowGlyph({ kind = 'cloud', size = 40 }) {
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
            opacity: 0.8,
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
            opacity: 0.45,
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
            opacity: 0.45,
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
              opacity: 0.6,
              borderRadius: 2,
            }}
          />
        ))}
      </div>
    )
  }

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
          opacity: 0.45,
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
          opacity: 0.45,
        }}
      />
    </div>
  )
}

function TomorrowBlock({ location }) {
  const {
    name,
    icon,
    weather_description,
    daily_high_celsius,
    daily_rainfall,
    rain_windows,
  } = location
  const windowsText = formatRainWindows(rain_windows)

  return (
    <div
      style={{ display: 'flex', alignItems: 'flex-start', gap: 20 }}
      data-testid="tomorrow-location-block"
    >
      <TomorrowGlyph kind={icon ?? 'cloud'} size={40} />
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
              fontSize: 48,
              lineHeight: 0.95,
              color: 'var(--ink)',
              letterSpacing: '-0.02em',
              fontFeatureSettings: '"lnum","tnum"',
            }}
          >
            {daily_high_celsius}°C
          </div>
          {weather_description && (
            <div
              style={{
                fontFamily: 'var(--f-display)',
                fontStyle: 'italic',
                fontSize: 26,
                color: 'var(--ink-dim)',
                lineHeight: 1.1,
              }}
            >
              {weather_description}
            </div>
          )}
        </div>

        {/* Rainfall and rain windows share one mono caption register — tomorrow's
            precision does not warrant a second type size the way today's does. */}
        {daily_rainfall && daily_rainfall.total_mm > 0 && (
          <div
            style={{
              fontFamily: 'var(--f-mono)',
              fontSize: 15,
              letterSpacing: '0.12em',
              color: 'var(--ink-faint)',
              fontWeight: 500,
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            Rain: {daily_rainfall.total_mm} mm ·{' '}
            {daily_rainfall.probability_percent}% chance
          </div>
        )}

        {windowsText && (
          <div
            style={{
              fontFamily: 'var(--f-mono)',
              fontSize: 15,
              letterSpacing: '0.18em',
              textTransform: 'uppercase',
              color: 'var(--ink-faint)',
              fontWeight: 500,
              fontVariantNumeric: 'tabular-nums',
            }}
            data-testid="tomorrow-rain-windows"
          >
            {windowsText}
          </div>
        )}
      </div>
    </div>
  )
}

/* No StaleTag here, deliberately. This column only ever renders beside the
   weather column, both read /api/weather, so both go stale at the same moment —
   a second "cached" tag is duplication. It also would not fit: heading plus tag
   overflow this column's width and wrap to two lines, which drops the first
   location block below its neighbour and breaks the shared baseline that makes
   the two columns read as a comparison. */
function SectionHeading({ weekday }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <div
        style={{
          fontFamily: 'var(--f-mono)',
          fontSize: 18,
          letterSpacing: '0.22em',
          textTransform: 'uppercase',
          color: 'var(--ink-dim)',
          fontWeight: 500,
          whiteSpace: 'nowrap',
        }}
      >
        {/* The weekday is the differentiator — without it, two adjacent columns
            of temperatures read as a duplication bug rather than a comparison. */}
        Tomorrow{weekday ? ` · ${weekday}` : ''}
      </div>
    </div>
  )
}

const POLL_INTERVAL_MS = 60_000

function TomorrowCard() {
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
        Loading tomorrow…
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
        Unable to load tomorrow&apos;s forecast
      </div>
    )
  }

  const tomorrow = data?.tomorrow
  const locations = tomorrow?.locations ?? []

  // A cache written before this feature shipped has no tomorrow key at all, so
  // the placeholder keeps the column from rendering empty between two rules.
  if (locations.length === 0) {
    return (
      <section style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
        <SectionHeading weekday={tomorrow?.weekday} />
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            minHeight: 120,
            fontFamily: 'var(--f-mono)',
            fontSize: 18,
            color: 'var(--ink-faint)',
          }}
          role="status"
        >
          Tomorrow unavailable
        </div>
      </section>
    )
  }

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
      <SectionHeading weekday={tomorrow.weekday} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
        {locations.map((loc, i) => (
          <div key={loc.name ?? i}>
            {i > 0 && (
              <div
                style={{
                  height: 1,
                  background: 'var(--rule)',
                  marginBottom: 28,
                }}
                aria-hidden="true"
              />
            )}
            <TomorrowBlock location={loc} />
          </div>
        ))}
      </div>
    </section>
  )
}

export default TomorrowCard

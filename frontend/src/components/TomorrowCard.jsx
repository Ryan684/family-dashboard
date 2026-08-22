import { useState, useEffect } from 'react'
import { LocationBlock } from './WeatherLocationBlock'

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

  const locations = data?.tomorrow?.locations ?? []

  // A cache written before this feature shipped has no tomorrow key at all, so
  // the placeholder keeps the column from rendering empty between two rules.
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
        Tomorrow unavailable
      </div>
    )
  }

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
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

export default TomorrowCard

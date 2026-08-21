import { useState, useEffect } from 'react'
import StaleTag from './StaleTag'
import { LocationBlock } from './WeatherLocationBlock'

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

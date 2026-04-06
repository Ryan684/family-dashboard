import { useState, useEffect } from 'react'

const STYLES_ID = 'travel-card-styles'

function injectStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLES_ID)) return
  const style = document.createElement('style')
  style.id = STYLES_ID
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700&family=Jost:wght@300;400&display=swap');

    :root {
      --tc-bg:          #1A1714;
      --tc-surface:     #232019;
      --tc-border:      #2E2B26;
      --tc-text-primary:   #F8F5EF;
      --tc-text-secondary: #7A756E;
      --tc-green:       #4CAF82;
      --tc-amber:       #E8A838;
      --tc-red:         #D95F4B;
      --tc-stale:       #7A756E;
    }

    .tc-wrap {
      font-family: 'Jost', 'Helvetica Neue', sans-serif;
      color: var(--tc-text-primary);
      padding: 32px 40px;
    }

    .tc-group {
      margin-bottom: 40px;
    }

    .tc-group-heading {
      font-family: 'Jost', sans-serif;
      font-size: 24px;
      font-weight: 400;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--tc-text-secondary);
      margin: 0 0 20px 0;
    }

    .tc-routes {
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
    }

    .tc-route-card {
      flex: 1;
      min-width: 260px;
      background: var(--tc-surface);
      border: 1px solid var(--tc-border);
      border-radius: 12px;
      padding: 24px 28px;
      position: relative;
      overflow: hidden;
    }

    .tc-colour-bar {
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      border-radius: 12px 0 0 12px;
    }

    .tc-colour-bar[data-colour="green"] { background: var(--tc-green); }
    .tc-colour-bar[data-colour="amber"] { background: var(--tc-amber); }
    .tc-colour-bar[data-colour="red"]   { background: var(--tc-red); box-shadow: 0 0 12px rgba(217, 95, 75, 0.4); }

    .tc-travel-time {
      font-family: 'Big Shoulders Display', 'Impact', sans-serif;
      font-size: 56px;
      font-weight: 700;
      line-height: 1;
      color: var(--tc-text-primary);
      margin-bottom: 8px;
    }

    .tc-description {
      font-size: 24px;
      font-weight: 300;
      color: var(--tc-text-secondary);
      margin-bottom: 0;
    }

    .tc-incidents {
      margin-top: 8px;
      padding: 20px 24px;
      background: rgba(217, 95, 75, 0.08);
      border: 1px solid rgba(217, 95, 75, 0.25);
      border-radius: 10px;
    }

    .tc-incidents-heading {
      font-size: 20px;
      font-weight: 400;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--tc-red);
      margin: 0 0 12px 0;
    }

    .tc-incident-item {
      font-size: 24px;
      font-weight: 300;
      color: var(--tc-text-primary);
      padding: 6px 0;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
    }

    .tc-incident-item:first-of-type {
      border-top: none;
    }

    .tc-incident-road {
      font-size: 20px;
      color: var(--tc-red);
      margin-right: 10px;
    }

    .tc-stale {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 20px;
      color: var(--tc-stale);
      margin-bottom: 24px;
      padding: 8px 16px;
      border: 1px solid var(--tc-border);
      border-radius: 6px;
    }

    .tc-loading {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 160px;
      font-size: 24px;
      color: var(--tc-text-secondary);
    }

    .tc-error {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 160px;
      font-size: 24px;
      color: var(--tc-red);
      padding: 24px;
      text-align: center;
    }
  `
  document.head.appendChild(style)
}

function formatMinutes(seconds) {
  return `${Math.round(seconds / 60)} min`
}

function RouteCard({ route }) {
  return (
    <div className="tc-route-card" data-testid="route-card">
      <div className="tc-colour-bar" data-colour={route.delay_colour} />
      <div className="tc-travel-time">{formatMinutes(route.travel_time_seconds)}</div>
      {route.description ? (
        <div className="tc-description">{route.description}</div>
      ) : null}
    </div>
  )
}

function RouteGroup({ heading, routes }) {
  return (
    <section className="tc-group">
      <h2 className="tc-group-heading">{heading}</h2>
      <div className="tc-routes">
        {routes.map((route, i) => (
          <RouteCard key={i} route={route} />
        ))}
      </div>
    </section>
  )
}

function IncidentList({ incidents }) {
  if (!incidents || incidents.length === 0) return null
  return (
    <div className="tc-incidents" data-testid="incident-list">
      <h3 className="tc-incidents-heading">Traffic incidents</h3>
      {incidents.map((inc, i) => (
        <div key={i} className="tc-incident-item">
          {inc.road ? (
            <span className="tc-incident-road">{inc.road}</span>
          ) : null}
          {inc.description}
        </div>
      ))}
    </div>
  )
}

function TravelCard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    injectStyles()

    let cancelled = false

    fetch('/api/travel')
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
      <div className="tc-loading" role="status">
        Loading travel data…
      </div>
    )
  }

  if (error) {
    return (
      <div className="tc-error" role="alert">
        Unable to load travel data
      </div>
    )
  }

  return (
    <div className="tc-wrap">
      {data.is_stale ? (
        <div className="tc-stale" data-testid="stale-warning">
          Showing cached data — outside morning window
        </div>
      ) : null}

      {data.home_to_work && data.home_to_work.length > 0 ? (
        <RouteGroup heading="Home → Work" routes={data.home_to_work} />
      ) : null}

      {data.home_to_nursery && data.home_to_nursery.length > 0 ? (
        <RouteGroup heading="Home → Nursery" routes={data.home_to_nursery} />
      ) : null}

      <IncidentList incidents={data.incidents} />
    </div>
  )
}

export default TravelCard

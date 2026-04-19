const STYLES_ID = 'travel-card-styles'

function injectStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLES_ID)) return
  const style = document.createElement('style')
  style.id = STYLES_ID
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Outfit:wght@300;400&display=swap');

    :root {
      --tc-bg:             #FAF7F2;
      --tc-surface:        #FFFFFF;
      --tc-border:         #DDD8D0;
      --tc-text-primary:   #1A1714;
      --tc-text-secondary: #6B6560;
      --tc-green:          #2D7A4F;
      --tc-amber:          #C47C18;
      --tc-red:            #B33A2E;
      --tc-stale:          #6B6560;
    }

    .tc-section {
      font-family: 'Outfit', 'Helvetica Neue', sans-serif;
      color: var(--tc-text-primary);
      padding: 32px 40px;
      display: flex;
      flex-direction: column;
      gap: 40px;
    }

    .tc-stale {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 20px;
      color: var(--tc-stale);
      padding: 8px 16px;
      border: 1px solid var(--tc-border);
      border-radius: 6px;
      align-self: flex-start;
    }

    /* ── Per-commuter card ─────────────────────────────── */

    .tc-commuter {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .tc-commuter-header {
      display: flex;
      align-items: baseline;
      gap: 16px;
      margin-bottom: 4px;
    }

    .tc-commuter-name {
      font-family: 'Outfit', sans-serif;
      font-size: 26px;
      font-weight: 400;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--tc-text-secondary);
      margin: 0;
    }

    .tc-commuter-dest {
      font-size: 20px;
      font-weight: 300;
      color: var(--tc-border);
      letter-spacing: 0.06em;
    }

    .tc-routes {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
    }

    /* ── Route card ────────────────────────────────────── */

    .tc-route-card {
      flex: 1;
      min-width: 200px;
      background: var(--tc-surface);
      border: 1px solid var(--tc-border);
      border-radius: 12px;
      padding: 20px 24px;
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
    .tc-colour-bar[data-colour="red"]   {
      background: var(--tc-red);
      box-shadow: 0 0 12px rgba(217, 95, 75, 0.4);
    }

    .tc-travel-time {
      font-family: 'DM Serif Display', Georgia, serif;
      font-size: 52px;
      font-weight: 400;
      line-height: 1;
      color: var(--tc-text-primary);
      margin-bottom: 6px;
    }

    .tc-description {
      font-size: 22px;
      font-weight: 300;
      color: var(--tc-text-secondary);
    }

    /* ── Incidents ─────────────────────────────────────── */

    .tc-incidents {
      padding: 16px 20px;
      background: rgba(217, 95, 75, 0.08);
      border: 1px solid rgba(217, 95, 75, 0.25);
      border-radius: 10px;
    }

    .tc-incidents-heading {
      font-size: 18px;
      font-weight: 400;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--tc-red);
      margin: 0 0 10px 0;
    }

    .tc-incident-item {
      font-size: 22px;
      font-weight: 300;
      color: var(--tc-text-primary);
      padding: 4px 0;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
    }

    .tc-incident-item:first-of-type {
      border-top: none;
    }

    .tc-incident-road {
      font-size: 18px;
      color: var(--tc-red);
      margin-right: 8px;
    }

    /* ── Status states ─────────────────────────────────── */

    .tc-loading {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 160px;
      font-size: 24px;
      color: var(--tc-text-secondary);
      font-family: 'Outfit', 'Helvetica Neue', sans-serif;
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
      font-family: 'Outfit', 'Helvetica Neue', sans-serif;
    }
  `
  document.head.appendChild(style)
}

function formatDuration(seconds) {
  const totalMinutes = Math.round(seconds / 60)
  if (totalMinutes < 60) return `${totalMinutes} min`
  const hrs = Math.floor(totalMinutes / 60)
  const mins = totalMinutes % 60
  return `${hrs} ${hrs === 1 ? 'hr' : 'hrs'} ${mins} min`
}

function destinationLabel(mode) {
  return mode === 'office' ? 'Work' : 'Home'
}

function RouteCard({ route }) {
  return (
    <div className="tc-route-card" data-testid="route-card">
      <div className="tc-colour-bar" data-colour={route.delay_colour} />
      <div className="tc-travel-time">{formatDuration(route.travel_time_seconds)}</div>
      {route.description ? (
        <div className="tc-description">{route.description}</div>
      ) : null}
    </div>
  )
}

function IncidentList({ incidents }) {
  if (!incidents || incidents.length === 0) return null
  return (
    <div className="tc-incidents" data-testid="incident-list">
      <h3 className="tc-incidents-heading">Traffic incidents</h3>
      {incidents.map((inc, i) => (
        <div key={i} className="tc-incident-item">
          {inc.road ? <span className="tc-incident-road">{inc.road}</span> : null}
          {inc.description}
        </div>
      ))}
    </div>
  )
}

function CommuterCard({ commuter }) {
  injectStyles()
  return (
    <div
      className="tc-commuter"
      data-testid="travel-card"
      data-commuter={commuter.name}
    >
      <div className="tc-commuter-header">
        <h2 className="tc-commuter-name">{commuter.name}</h2>
        <span className="tc-commuter-dest">→ {destinationLabel(commuter.mode)}</span>
      </div>
      <div className="tc-routes">
        {commuter.routes.map((route, i) => (
          <RouteCard key={i} route={route} />
        ))}
      </div>
      <IncidentList incidents={commuter.incidents} />
    </div>
  )
}

function TravelCard({ commuters = [], isStale = false, loading = false, error = null }) {
  injectStyles()

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

  if (commuters.length === 0) {
    return null
  }

  return (
    <div className="tc-section">
      {isStale ? (
        <div className="tc-stale" data-testid="stale-warning">
          Showing cached data — outside morning window
        </div>
      ) : null}
      {commuters.map((commuter) => (
        <CommuterCard key={commuter.name} commuter={commuter} />
      ))}
    </div>
  )
}

export default TravelCard

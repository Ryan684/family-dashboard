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
    }

    .tc-card {
      font-family: 'Jost', 'Helvetica Neue', sans-serif;
      color: var(--tc-text-primary);
      padding: 32px 40px;
    }

    .tc-card-header {
      font-family: 'Big Shoulders Display', 'Impact', sans-serif;
      font-size: 32px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--tc-text-secondary);
      margin: 0 0 16px 0;
    }

    .tc-destination {
      font-size: 20px;
      font-weight: 400;
      letter-spacing: 0.14em;
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
      min-width: 220px;
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
    }

    .tc-incidents {
      margin-top: 20px;
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
  `
  document.head.appendChild(style)
  return null
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

function TravelCard({ commuter }) {
  injectStyles()

  const destination = commuter.mode === 'office' ? 'Work' : 'Home'

  return (
    <div className="tc-card" data-testid="travel-card">
      <h2 className="tc-card-header">{commuter.name}</h2>
      <div className="tc-destination">{destination}</div>
      <div className="tc-routes">
        {commuter.routes.map((route, i) => (
          <RouteCard key={i} route={route} />
        ))}
      </div>
      <IncidentList incidents={commuter.incidents} />
    </div>
  )
}

export default TravelCard

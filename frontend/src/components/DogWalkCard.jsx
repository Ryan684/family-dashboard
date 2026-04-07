import { useState, useEffect } from 'react'

const STYLES_ID = 'dog-walk-card-styles'

function injectStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLES_ID)) return
  const style = document.createElement('style')
  style.id = STYLES_ID
  style.textContent = `
    .dwc {
      height: 100%;
      padding: 28px 32px;
      display: flex;
      flex-direction: column;
      gap: 0;
      background: #1A1714;
      color: #F8F5EF;
      font-family: 'Jost', 'Helvetica Neue', sans-serif;
    }

    .dwc__header {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      margin-bottom: 20px;
    }

    .dwc__label {
      font-family: 'Big Shoulders Display', sans-serif;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: #7A7168;
    }

    .dwc__conditions {
      font-family: 'Jost', sans-serif;
      font-size: 13px;
      font-weight: 400;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 4px 12px;
      border-radius: 2px;
    }

    .dwc__conditions[data-label="Dry"] {
      background: rgba(74, 160, 100, 0.15);
      color: #6BCF8A;
      border: 1px solid rgba(74, 160, 100, 0.35);
    }

    .dwc__conditions[data-label="Wet"] {
      background: rgba(210, 155, 60, 0.15);
      color: #D4A355;
      border: 1px solid rgba(210, 155, 60, 0.35);
    }

    .dwc__conditions[data-label="Very wet"] {
      background: rgba(200, 80, 70, 0.15);
      color: #C8544A;
      border: 1px solid rgba(200, 80, 70, 0.35);
    }

    .dwc__conditions[data-label="Unknown"] {
      background: rgba(122, 113, 104, 0.15);
      color: #7A7168;
      border: 1px solid rgba(122, 113, 104, 0.35);
    }

    .dwc__hero {
      flex: 0 0 auto;
      padding-bottom: 20px;
      border-bottom: 1px solid #2A2622;
      margin-bottom: 20px;
    }

    .dwc__hero-name {
      font-family: 'Big Shoulders Display', sans-serif;
      font-size: 52px;
      font-weight: 700;
      line-height: 1;
      color: #F8F5EF;
      margin-bottom: 10px;
      letter-spacing: -0.01em;
    }

    .dwc__hero-meta {
      display: flex;
      gap: 20px;
      align-items: center;
    }

    .dwc__hero-stat {
      font-size: 26px;
      font-weight: 300;
      color: #B0A99E;
      letter-spacing: 0.02em;
    }

    .dwc__hero-stat span {
      font-size: 14px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #5A5349;
      margin-left: 3px;
    }

    .dwc__hero-desc {
      margin-top: 8px;
      font-size: 18px;
      font-weight: 300;
      color: #7A7168;
      letter-spacing: 0.01em;
    }

    .dwc__list-label {
      font-size: 11px;
      font-weight: 400;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: #4A433D;
      margin-bottom: 12px;
    }

    .dwc__list {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0;
      overflow: hidden;
    }

    .dwc__route {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid #2A2622;
      transition: opacity 0.15s ease;
    }

    .dwc__route:last-child {
      border-bottom: none;
    }

    .dwc__route[data-suitable="false"] {
      opacity: 0.35;
    }

    .dwc__route-name {
      font-size: 24px;
      font-weight: 400;
      color: #F8F5EF;
      letter-spacing: 0.01em;
    }

    .dwc__route[data-suitable="false"] .dwc__route-name {
      text-decoration: line-through;
      text-decoration-color: #4A433D;
    }

    .dwc__route-right {
      display: flex;
      gap: 16px;
      align-items: center;
    }

    .dwc__route-stat {
      font-size: 20px;
      font-weight: 300;
      color: #7A7168;
      white-space: nowrap;
    }

    .dwc__route-surface {
      font-size: 11px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #4A433D;
      padding: 3px 8px;
      border: 1px solid #2A2622;
      border-radius: 2px;
    }

    .dwc__loading {
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #4A433D;
      font-size: 14px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }

    .dwc__error {
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #C8544A;
      font-size: 16px;
      font-weight: 300;
    }
  `
  document.head.appendChild(style)
}

export default function DogWalkCard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    injectStyles()
    fetch('/api/dog-walk')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((json) => {
        setData(json)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="dwc">
        <div className="dwc__loading" role="status">Loading</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dwc">
        <div className="dwc__error" role="alert">Unable to load walk routes</div>
      </div>
    )
  }

  if (!data?.eligible) {
    return null
  }

  const routes = data.routes ?? []
  const topRoute = routes[0] ?? null
  const conditions = data.conditions ?? 'Unknown'

  return (
    <div className="dwc" data-testid="dog-walk-card">
      <div className="dwc__header">
        <span className="dwc__label">Dog Walk</span>
        {conditions && (
          <span
            className="dwc__conditions"
            data-label={conditions}
            data-testid="conditions-label"
          >
            {conditions}
          </span>
        )}
      </div>

      {topRoute && (
        <div className="dwc__hero" data-testid="top-route">
          <div className="dwc__hero-name" data-testid="top-route-name">
            {topRoute.name}
          </div>
          <div className="dwc__hero-meta">
            <div className="dwc__hero-stat">
              {topRoute.duration_minutes} <span>min</span>
            </div>
            <div className="dwc__hero-stat">
              {topRoute.distance_km} <span>km</span>
            </div>
          </div>
          {topRoute.description && (
            <div className="dwc__hero-desc">{topRoute.description}</div>
          )}
        </div>
      )}

      {routes.length > 0 && (
        <div className="dwc__list">
          <div className="dwc__list-label">All routes</div>
          {routes.map((route) => (
            <div
              key={route.id}
              className="dwc__route"
              data-suitable={String(route.suitable)}
              data-testid={`route-item-${route.id}`}
            >
              <span className="dwc__route-name">{route.name}</span>
              <div className="dwc__route-right">
                <span className="dwc__route-stat">
                  {route.duration_minutes} min · {route.distance_km} km
                </span>
                {route.surface && (
                  <span className="dwc__route-surface">{route.surface}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

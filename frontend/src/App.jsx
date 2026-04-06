import { useState, useEffect } from 'react'
import ClockCard from './components/ClockCard'
import TravelCard from './components/TravelCard'
import WeatherCard from './components/WeatherCard'
import CalendarCard from './components/CalendarCard'
import AlertBanner from './components/AlertBanner'

const STYLES_ID = 'app-styles'

function injectStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLES_ID)) return
  const style = document.createElement('style')
  style.id = STYLES_ID
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700&family=Jost:wght@300;400&display=swap');

    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html, body, #root {
      height: 100%;
    }

    body {
      background: #1A1714;
      color: #F8F5EF;
      font-family: 'Jost', 'Helvetica Neue', sans-serif;
    }

    .app-shell {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }

    .app-clock {
      border-bottom: 1px solid #2A2622;
    }

    /* Grid: travel cards span left, weather + calendar on right */
    .app-grid {
      display: grid;
      gap: 1px;
      flex: 1;
      background: #2A2622;
    }

    /* 0 commuters: 2-col, weather + calendar side by side */
    .app-grid--0 {
      grid-template-columns: 1fr 1fr;
    }

    /* 1 commuter: 3-col, travel takes 2 cols */
    .app-grid--1 {
      grid-template-columns: 2fr 1fr 1fr;
    }

    /* 2 commuters: 2-col grid, travel cards in first col stacked, or 2+2 */
    .app-grid--2 {
      grid-template-columns: 1fr 1fr 1fr 1fr;
    }

    .app-cell {
      background: #1A1714;
    }

    .app-cell--travel-2 {
      grid-column: span 2;
    }

    .app-travel-section {
      display: contents;
    }

    .app-status {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 160px;
      font-size: 24px;
      color: #7A756E;
    }

    .app-error {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 160px;
      font-size: 24px;
      color: #D95F4B;
    }

    .app-stale {
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 20px;
      color: #7A756E;
      padding: 12px 40px;
      background: #1A1714;
      border-bottom: 1px solid #2A2622;
    }
  `
  document.head.appendChild(style)
}

const POLL_INTERVAL_MS = 60_000

function App() {
  const [travelData, setTravelData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    injectStyles()

    let cancelled = false

    function fetchTravel() {
      fetch('/api/travel')
        .then((res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`)
          return res.json()
        })
        .then((json) => {
          if (!cancelled) {
            setTravelData(json)
            setLoading(false)
          }
        })
        .catch((err) => {
          if (!cancelled) {
            setError(err.message)
            setLoading(false)
          }
        })
    }

    fetchTravel()
    const id = setInterval(fetchTravel, POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  const commuters = travelData ? travelData.commuters : []
  const count = commuters.length

  function renderTravelContent() {
    if (loading) {
      return (
        <div className="app-cell app-status" role="status">
          Loading travel data…
        </div>
      )
    }
    if (error) {
      return (
        <div className="app-cell app-error" role="alert">
          Unable to load travel data
        </div>
      )
    }
    return commuters.map((commuter) => (
      <div key={commuter.name} className="app-cell">
        <TravelCard commuter={commuter} />
      </div>
    ))
  }

  const gridClass = loading || error ? 'app-grid app-grid--1' : `app-grid app-grid--${count}`

  return (
    <div className="app-shell">
      <div className="app-clock">
        <ClockCard />
      </div>

      <AlertBanner travelData={travelData} />

      {travelData && travelData.is_stale ? (
        <div className="app-stale" data-testid="stale-warning">
          Showing cached data — outside morning window
        </div>
      ) : null}

      <div className={gridClass}>
        {count > 0 || loading || error ? (
          <div className={count === 2 ? 'app-cell app-cell--travel-2' : 'app-cell'} data-testid="travel-section">
            <div style={{ display: 'flex', height: '100%' }}>
              {renderTravelContent()}
            </div>
          </div>
        ) : null}
        <div className="app-cell">
          <WeatherCard />
        </div>
        <div className="app-cell">
          <CalendarCard />
        </div>
      </div>
    </div>
  )
}

export default App

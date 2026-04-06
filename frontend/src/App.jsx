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

    /* Grid with travel section (1 or 2 commuters) */
    .app-grid {
      display: grid;
      gap: 1px;
      flex: 1;
      background: #2A2622;
    }

    .app-grid[data-commuters="1"] {
      grid-template-columns: 1fr 1fr 1fr;
    }

    .app-grid[data-commuters="2"] {
      grid-template-columns: 2fr 1fr 1fr;
    }

    /* Grid without travel section */
    .app-grid-no-travel {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1px;
      flex: 1;
      background: #2A2622;
    }

    .app-cell {
      background: #1A1714;
    }
  `
  document.head.appendChild(style)
}

const POLL_INTERVAL_MS = 60_000

function App() {
  const [travelData, setTravelData] = useState(null)
  const [travelLoading, setTravelLoading] = useState(true)
  const [travelError, setTravelError] = useState(null)

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
            setTravelLoading(false)
          }
        })
        .catch((err) => {
          if (!cancelled) {
            setTravelError(err.message)
            setTravelLoading(false)
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

  const commuters = travelData?.commuters ?? []
  const isStale = travelData?.is_stale ?? false
  const commuterCount = commuters.length

  const showTravel = travelLoading || travelError || commuterCount > 0

  return (
    <div className="app-shell">
      <div className="app-clock">
        <ClockCard />
      </div>

      <AlertBanner travelData={travelData} />

      {showTravel ? (
        <div className="app-grid" data-commuters={commuterCount} data-testid="travel-section">
          <div className="app-cell">
            <TravelCard
              commuters={commuters}
              isStale={isStale}
              loading={travelLoading}
              error={travelError}
            />
          </div>
          <div className="app-cell">
            <WeatherCard />
          </div>
          <div className="app-cell">
            <CalendarCard />
          </div>
        </div>
      ) : (
        <div className="app-grid-no-travel">
          <div className="app-cell">
            <WeatherCard />
          </div>
          <div className="app-cell">
            <CalendarCard />
          </div>
        </div>
      )}
    </div>
  )
}

export default App

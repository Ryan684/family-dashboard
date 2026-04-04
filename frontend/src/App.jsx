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

    .app-grid {
      display: grid;
      grid-template-columns: 2fr 1fr 1fr;
      grid-template-rows: auto auto;
      gap: 1px;
      flex: 1;
      background: #2A2622;
    }

    .app-cell {
      background: #1A1714;
    }

    .app-cell--travel {
      grid-column: 1 / 2;
      grid-row: 1 / 2;
    }

    .app-cell--weather {
      grid-column: 2 / 3;
      grid-row: 1 / 2;
    }

    .app-cell--calendar {
      grid-column: 3 / 4;
      grid-row: 1 / 2;
    }
  `
  document.head.appendChild(style)
}

const POLL_INTERVAL_MS = 60_000

function App() {
  const [travelData, setTravelData] = useState(null)

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
          if (!cancelled) setTravelData(json)
        })
        .catch(() => {
          // AlertBanner stays hidden on error
        })
    }

    fetchTravel()
    const id = setInterval(fetchTravel, POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  return (
    <div className="app-shell">
      <div className="app-clock">
        <ClockCard />
      </div>

      <AlertBanner travelData={travelData} />

      <div className="app-grid">
        <div className="app-cell app-cell--travel">
          <TravelCard />
        </div>
        <div className="app-cell app-cell--weather">
          <WeatherCard />
        </div>
        <div className="app-cell app-cell--calendar">
          <CalendarCard />
        </div>
      </div>
    </div>
  )
}

export default App

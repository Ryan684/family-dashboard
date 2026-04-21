import { useState, useEffect, useRef } from 'react'
import ClockCard from './components/ClockCard'
import TravelCard from './components/TravelCard'
import WeatherCard from './components/WeatherCard'
import CalendarCard from './components/CalendarCard'
import AlertBanner from './components/AlertBanner'

const POLL_INTERVAL_MS = 60_000

const label = (text, dim = false) => ({
  fontFamily: 'var(--f-mono)',
  fontSize: 18,
  letterSpacing: '0.22em',
  textTransform: 'uppercase',
  color: dim ? 'var(--ink-faint)' : 'var(--ink-dim)',
  fontWeight: 500,
  whiteSpace: 'nowrap',
  display: 'inline',
  children: text,
})

function App() {
  const [travelData, setTravelData] = useState(null)
  const [travelLoading, setTravelLoading] = useState(true)
  const [travelError, setTravelError] = useState(null)

  const stageRef = useRef(null)
  const frameRef = useRef(null)

  useEffect(() => {
    function fit() {
      const s = stageRef.current
      const f = frameRef.current
      if (!s || !f) return
      const scale = Math.min(s.clientWidth / 1920, s.clientHeight / 1080)
      const x = (s.clientWidth - 1920 * scale) / 2
      const y = (s.clientHeight - 1080 * scale) / 2
      f.style.transform = `translate(${x}px,${y}px) scale(${scale})`
    }
    fit()
    window.addEventListener('resize', fit)
    return () => window.removeEventListener('resize', fit)
  }, [])

  useEffect(() => {
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

  const gridCols = showTravel ? '1.6fr 1px 1fr 1px 1.1fr' : '1fr 1px 1fr'

  return (
    <div ref={stageRef} className="dash-stage">
      <div
        ref={frameRef}
        className="dash-frame fd-reveal"
        style={{
          padding: '72px 96px 80px',
          display: 'flex',
          flexDirection: 'column',
          gap: 40,
        }}
      >
        {/* masthead */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div
            style={{
              fontFamily: 'var(--f-mono)',
              fontSize: 18,
              letterSpacing: '0.22em',
              textTransform: 'uppercase',
              color: 'var(--ink-dim)',
              fontWeight: 500,
            }}
          >
            Family Dashboard
          </div>
          <div
            style={{
              fontFamily: 'var(--f-mono)',
              fontSize: 18,
              letterSpacing: '0.22em',
              textTransform: 'uppercase',
              color: 'var(--ink-faint)',
              fontWeight: 500,
            }}
          >
            {new Date().toLocaleDateString('en-GB', { weekday: 'long' })} Edition
          </div>
        </div>

        {/* hairline rule */}
        <div style={{ height: 1, background: 'var(--rule)' }} aria-hidden="true" />

        {/* hero clock */}
        <ClockCard />

        {/* alert strap */}
        <AlertBanner travelData={travelData} />

        {/* content columns */}
        <div
          style={{
            flex: 1,
            minHeight: 0,
            display: 'grid',
            gridTemplateColumns: gridCols,
            gap: 48,
            paddingTop: 12,
          }}
        >
          {showTravel && (
            <>
              <div data-testid="travel-section">
                <TravelCard
                  commuters={commuters}
                  isStale={isStale}
                  loading={travelLoading}
                  error={travelError}
                />
              </div>
              <div style={{ width: 1, background: 'var(--rule)' }} aria-hidden="true" />
            </>
          )}
          <WeatherCard />
          <div style={{ width: 1, background: 'var(--rule)' }} aria-hidden="true" />
          <CalendarCard />
        </div>
      </div>
    </div>
  )
}

export default App

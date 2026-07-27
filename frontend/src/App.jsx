import { useState, useEffect, useRef } from 'react'
import ClockCard from './components/ClockCard'
import TravelCard from './components/TravelCard'
import WeatherCard from './components/WeatherCard'
import CalendarCard from './components/CalendarCard'
import AlertBanner from './components/AlertBanner'

const POLL_INTERVAL_MS = 60_000

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
            setTravelError(null)
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
  const showTravel =
    travelLoading || travelError || (!isStale && commuterCount > 0)

  // Calendar and weather run narrower than travel's twin commuter columns, so they
  // get a larger share of the freed-up width; ratios still sum to the same total.
  const gridCols = showTravel
    ? '1.5fr 1px 0.9fr 1px 1.3fr'
    : '0.85fr 1px 1.15fr'

  return (
    <div ref={stageRef} className="dash-stage">
      <div
        ref={frameRef}
        className="dash-frame fd-reveal"
        style={{
          padding: '88px 96px 80px',
          display: 'flex',
          flexDirection: 'column',
          gap: 32,
        }}
      >
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
            gridTemplateRows: 'minmax(0, 1fr)',
            gap: 48,
            paddingTop: 16,
            overflow: 'hidden',
          }}
        >
          {showTravel && (
            <>
              <DashColumn testId="travel-section">
                <TravelCard
                  commuters={commuters}
                  isStale={isStale}
                  loading={travelLoading}
                  error={travelError}
                />
              </DashColumn>
              <div
                style={{ width: 1, background: 'var(--rule)' }}
                aria-hidden="true"
              />
            </>
          )}
          <DashColumn>
            <WeatherCard />
          </DashColumn>
          <div
            style={{ width: 1, background: 'var(--rule)' }}
            aria-hidden="true"
          />
          <DashColumn>
            <CalendarCard />
          </DashColumn>
        </div>
      </div>
    </div>
  )
}

/* Fills its grid row and keeps its heading pinned to the same top edge as
   its neighbours, so the Commute / Weather / Calendar labels always sit on
   one scannable line. The trailing fade hides any excess below the fold on
   an unusually busy day instead of letting it render past the kiosk frame,
   invisible. */
function DashColumn({ children, testId }) {
  return (
    <div
      data-testid={testId}
      style={{
        position: 'relative',
        height: '100%',
        minHeight: 0,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {children}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 0,
          height: 64,
          background: 'linear-gradient(to bottom, transparent, var(--bg) 85%)',
          pointerEvents: 'none',
        }}
      />
    </div>
  )
}

export default App

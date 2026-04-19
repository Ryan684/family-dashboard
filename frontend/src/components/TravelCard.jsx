const DELAY_META = {
  green: { color: 'var(--ok)',    label: 'On time' },
  amber: { color: 'var(--warn)',  label: 'Slow' },
  red:   { color: 'var(--alert)', label: 'Delayed' },
}

/* sr-only: text node discoverable by getByText but visually hidden */
const srOnly = {
  position: 'absolute',
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: 'hidden',
  clip: 'rect(0,0,0,0)',
  border: 0,
  whiteSpace: 'nowrap',
}

function formatKm(meters) {
  return `${(meters / 1000).toFixed(1)} km`
}

/* Returns "45 min", "1 hr 0 min", "2 hrs 5 min" — matches test expectations */
function formatTimeString(seconds) {
  const m = Math.round(seconds / 60)
  if (m < 60) return `${m} min`
  const h = Math.floor(m / 60)
  const r = m % 60
  return `${h} ${h === 1 ? 'hr' : 'hrs'} ${r} min`
}

/* Returns { bigNum, unit } for large-numeral visual display */
function formatTimeDisplay(seconds) {
  const m = Math.round(seconds / 60)
  if (m < 60) return { bigNum: String(m), unit: 'min' }
  const h = Math.floor(m / 60)
  const r = m % 60
  if (r === 0) return { bigNum: String(h), unit: h === 1 ? 'hr' : 'hrs' }
  return { bigNum: `${h}:${String(r).padStart(2, '0')}`, unit: h === 1 ? 'hr' : 'hrs' }
}

function RouteRow({ route, primary = false }) {
  if (!route) return null
  const meta = DELAY_META[route.delay_colour] || DELAY_META.green
  const delaySec =
    route.travel_time_seconds - (route.static_duration_seconds ?? route.travel_time_seconds)
  const delayMin = Math.round(delaySec / 60)
  const { bigNum, unit } = formatTimeDisplay(route.travel_time_seconds)
  const timeStr = formatTimeString(route.travel_time_seconds)
  const isRed = route.delay_colour === 'red'

  return (
    <div style={{ display: 'flex', gap: 22, alignItems: 'stretch' }} data-testid="route-card">
      {/* vertical delay bar — hairline, coloured, pulses when red */}
      <div
        data-colour={route.delay_colour}
        style={{
          width: isRed ? 3 : 2,
          background: meta.color,
          borderRadius: 2,
          alignSelf: 'stretch',
          flexShrink: 0,
          ...(isRed
            ? { boxShadow: `0 0 14px ${meta.color}`, animation: 'fd-pulse 2.4s ease-in-out infinite' }
            : null),
        }}
      />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0 }}>
        {/* sr-only span carries the combined time string for getByText */}
        <span style={srOnly}>{timeStr}</span>

        {/* big visual numeral + unit */}
        <div
          style={{ display: 'flex', alignItems: 'baseline', gap: 14 }}
          aria-hidden="true"
        >
          <div
            style={{
              fontFamily: 'var(--f-display)',
              fontSize: primary ? 104 : 68,
              color: 'var(--ink)',
              lineHeight: 0.9,
              letterSpacing: '-0.03em',
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {bigNum}
          </div>
          <div
            style={{
              fontFamily: 'var(--f-display)',
              fontStyle: 'italic',
              fontSize: primary ? 34 : 26,
              color: 'var(--ink-dim)',
              lineHeight: 1,
            }}
          >
            {unit}
          </div>
        </div>

        {/* delay status label */}
        <div
          style={{
            fontFamily: 'var(--f-mono)',
            fontSize: 14,
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            color: meta.color,
            fontWeight: 500,
          }}
        >
          {delayMin > 0 ? `+${delayMin} min · ${meta.label}` : meta.label}
        </div>

        {/* route description + distance */}
        {route.description ? (
          <div
            style={{
              fontFamily: 'var(--f-display)',
              fontStyle: 'italic',
              fontSize: primary ? 24 : 20,
              color: 'var(--ink-dim)',
              marginTop: 4,
            }}
          >
            {route.description}
            {route.distance_meters != null ? ` · ${formatKm(route.distance_meters)}` : null}
          </div>
        ) : null}
      </div>
    </div>
  )
}

function IncidentList({ incidents }) {
  if (!incidents || incidents.length === 0) return null
  return (
    <div
      style={{
        marginTop: 10,
        padding: '16px 20px',
        background: 'var(--alert-tint)',
        borderLeft: '2px solid var(--alert)',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}
      data-testid="incident-list"
    >
      <div
        style={{
          fontFamily: 'var(--f-mono)',
          fontSize: 13,
          letterSpacing: '0.22em',
          textTransform: 'uppercase',
          color: 'var(--alert)',
          fontWeight: 500,
        }}
      >
        Incidents
      </div>
      {incidents.map((inc, i) => (
        <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'baseline' }}>
          {inc.road && (
            <span
              style={{
                fontFamily: 'var(--f-mono)',
                fontSize: 14,
                color: 'var(--alert)',
                letterSpacing: '0.1em',
                fontWeight: 500,
                minWidth: 38,
              }}
            >
              {inc.road}
            </span>
          )}
          <span style={{ fontFamily: 'var(--f-display)', fontSize: 22, color: 'var(--ink)' }}>
            {inc.description}
          </span>
        </div>
      ))}
    </div>
  )
}

function CommuterColumn({ commuter }) {
  const { name, mode, drops, routes, incidents } = commuter
  const destination = mode === 'office' ? 'Work' : 'Home'
  const [primary, alt] = routes

  return (
    <div
      style={{ display: 'flex', flexDirection: 'column', gap: 22 }}
      data-testid="travel-card"
      data-commuter={name}
    >
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 18 }}>
        <div
          style={{
            fontFamily: 'var(--f-display)',
            fontSize: 56,
            color: 'var(--ink)',
            lineHeight: 0.9,
            letterSpacing: '-0.02em',
          }}
        >
          {name}
        </div>
        <div
          style={{
            fontFamily: 'var(--f-display)',
            fontStyle: 'italic',
            fontSize: 30,
            color: 'var(--ink-dim)',
          }}
        >
          → {destination}
        </div>
      </div>

      {drops?.length > 0 && (
        <div
          style={{
            fontFamily: 'var(--f-mono)',
            fontSize: 13,
            letterSpacing: '0.22em',
            textTransform: 'uppercase',
            color: 'var(--ink-faint)',
            fontWeight: 500,
          }}
        >
          via {drops.join(' → ')}
        </div>
      )}

      <div style={{ height: 1, background: 'var(--rule)', margin: '4px 0' }} aria-hidden="true" />

      <RouteRow route={primary} primary />
      {alt && (
        <>
          <div
            style={{ height: 1, background: 'var(--rule)', opacity: 0.6 }}
            aria-hidden="true"
          />
          <RouteRow route={alt} />
        </>
      )}

      <IncidentList incidents={incidents} />
    </div>
  )
}

function StaleTag() {
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 10,
        fontFamily: 'var(--f-mono)',
        fontSize: 14,
        letterSpacing: '0.2em',
        textTransform: 'uppercase',
        color: 'var(--ink-faint)',
        fontWeight: 500,
      }}
      data-testid="stale-warning"
    >
      <span
        style={{
          display: 'inline-block',
          width: 8,
          height: 8,
          borderRadius: 999,
          background: 'var(--ink-faint)',
          flexShrink: 0,
        }}
        aria-hidden="true"
      />
      Cached · outside window
    </div>
  )
}

function TravelCard({ commuters = [], isStale = false, loading = false, error = null }) {
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
        Loading travel data…
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
        Unable to load travel data
      </div>
    )
  }

  if (commuters.length === 0) {
    return null
  }

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
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
          Commute
        </div>
        {isStale && <StaleTag />}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${commuters.length}, minmax(0,1fr))`,
          gap: 56,
        }}
      >
        {commuters.map((commuter) => (
          <CommuterColumn key={commuter.name} commuter={commuter} />
        ))}
      </div>
    </section>
  )
}

export default TravelCard

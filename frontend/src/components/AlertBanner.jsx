function hasRedRoute(travelData) {
  if (!travelData || travelData.is_stale) return false
  const commuters = travelData.commuters || []
  return commuters.some((c) =>
    (c.routes || []).some((r) => r.delay_colour === 'red')
  )
}

function buildAlertMessage(travelData) {
  if (!travelData) return null
  const commuters = travelData.commuters || []

  for (const c of commuters) {
    const redRoute = (c.routes || []).find((r) => r.delay_colour === 'red')
    if (!redRoute) continue
    const delayMin = Math.round((redRoute.delay_seconds ?? 0) / 60)
    const extra = Math.max(10, delayMin)
    return {
      label: `${c.name} — heavy traffic`,
      detail: `Leave ${extra} min early`,
    }
  }
  return null
}

function AlertBanner({ travelData }) {
  if (!hasRedRoute(travelData)) return null

  const msg = buildAlertMessage(travelData)

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 32,
        padding: '10px 0',
        borderTop: '1px solid var(--alert)',
        borderBottom: '1px solid var(--alert)',
        background: 'var(--alert-tint)',
        animation: 'fd-pulse-soft 3.2s ease-in-out infinite',
      }}
      role="alert"
    >
      <div
        style={{
          fontFamily: 'var(--f-mono)',
          fontSize: 14,
          letterSpacing: '0.3em',
          textTransform: 'uppercase',
          color: 'var(--alert)',
          fontWeight: 500,
          paddingLeft: 4,
        }}
      >
        Morning alert
      </div>
      <div
        style={{ width: 1, height: 28, background: 'var(--rule)' }}
        aria-hidden="true"
      />
      <div
        style={{
          fontFamily: 'var(--f-display)',
          fontStyle: 'italic',
          fontSize: 26,
          color: 'var(--ink)',
          flex: 1,
          lineHeight: 1.1,
        }}
      >
        {msg ? (
          <>
            {msg.label}
            <span style={{ color: 'var(--ink-dim)' }}> — {msg.detail}</span>
          </>
        ) : (
          'Heavy traffic — leave early today'
        )}
      </div>
    </div>
  )
}

export default AlertBanner

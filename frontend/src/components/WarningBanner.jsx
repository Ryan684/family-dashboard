import { useState, useEffect } from 'react'

/* Purpose: tell the household, at a glance from across the room, that the Met
   Office has a severe weather warning covering somewhere they are going today
   or tomorrow.

   Direction: "a wire-service bulletin". Deliberately the same three-part
   skeleton as the morning traffic alert it stacks above — mono uppercase label,
   hairline rule, headline in display italic — because two straps of visibly
   different species would read as unrelated systems rather than one dashboard
   speaking twice. Severity is carried by colour and by whether it pulses, not
   by a different layout. */

const SEVERITY = {
  RED: {
    label: 'Red',
    colour: 'var(--alert)',
    tint: 'var(--alert-tint)',
    role: 'alert',
    // Pulsing has to mean something. Red is the only level urgent enough to
    // earn motion on a display that is otherwise still.
    animation: 'fd-pulse-soft 3.2s ease-in-out infinite',
  },
  AMBER: {
    label: 'Amber',
    colour: 'var(--warn)',
    tint: 'var(--warn-tint)',
    role: 'status',
    animation: undefined,
  },
}

/* Yellow warnings fire several times a week in a UK winter, often for routine
   rain and wind. A permanently lit strap is one nobody reads — and it would
   train the household to ignore the same strap when it carries a red warning.
   The backend returns yellow regardless; this is the single place that decides
   not to show it. */
export function isBannerWorthy(level) {
  return level === 'RED' || level === 'AMBER'
}

export function formatLocations(locations) {
  if (!locations || locations.length === 0) return ''
  if (locations.length === 1) return locations[0]
  return `${locations.slice(0, -1).join(', ')} & ${locations[locations.length - 1]}`
}

const POLL_INTERVAL_MS = 60_000

function WarningBanner() {
  const [warnings, setWarnings] = useState([])

  useEffect(() => {
    let cancelled = false

    function fetchWarnings() {
      fetch('/api/weather/warnings')
        .then((res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`)
          return res.json()
        })
        .then((json) => {
          if (!cancelled) setWarnings(json.warnings ?? [])
        })
        .catch(() => {
          // A kiosk strap reading "couldn't load warnings" is worse than
          // silence, so a failure simply leaves the banner absent.
          if (!cancelled) setWarnings([])
        })
    }

    fetchWarnings()
    const id = setInterval(fetchWarnings, POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  // Filter before counting: "+1 more" must never point at a warning the
  // household has no way to see.
  const shown = warnings.filter((w) => isBannerWorthy(w.level))
  if (shown.length === 0) return null

  const primary =
    shown.find((w) => w.level === 'RED') ?? shown[0]
  const severity = SEVERITY[primary.level]
  const others = shown.length - 1
  const where = formatLocations(primary.locations)

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 32,
        padding: '10px 0',
        borderTop: `1px solid ${severity.colour}`,
        borderBottom: `1px solid ${severity.colour}`,
        background: severity.tint,
        animation: severity.animation,
      }}
      role={severity.role}
    >
      <div
        style={{
          fontFamily: 'var(--f-mono)',
          fontSize: 14,
          letterSpacing: '0.3em',
          textTransform: 'uppercase',
          color: severity.colour,
          fontWeight: 500,
          paddingLeft: 4,
          whiteSpace: 'nowrap',
        }}
      >
        Weather warning
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
          minWidth: 0,
        }}
      >
        {severity.label} — {primary.headline}
        {where && <span style={{ color: 'var(--ink-dim)' }}>, {where}</span>}
      </div>
      {others > 0 && (
        <div
          style={{
            fontFamily: 'var(--f-mono)',
            fontSize: 14,
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            color: 'var(--ink-faint)',
            fontWeight: 500,
            whiteSpace: 'nowrap',
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          +{others} more
        </div>
      )}
    </div>
  )
}

export default WarningBanner

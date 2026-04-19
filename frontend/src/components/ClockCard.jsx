import { useState, useEffect } from 'react'

function isoWeek(d) {
  const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()))
  const dayNum = t.getUTCDay() || 7
  t.setUTCDate(t.getUTCDate() + 4 - dayNum)
  const yearStart = new Date(Date.UTC(t.getUTCFullYear(), 0, 1))
  return Math.ceil(((t - yearStart) / 86400000 + 1) / 7)
}

/* sr-only: accessible text discoverable by getByText but visually hidden */
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

function ClockCard() {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 10_000)
    return () => clearInterval(id)
  }, [])

  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  const weekday = now.toLocaleDateString('en-GB', { weekday: 'long' })
  const day = now.getDate()
  const month = now.toLocaleDateString('en-GB', { month: 'long' })
  const week = `Week ${String(isoWeek(now)).padStart(2, '0')}`

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* giant serif time — single text node so getByText('HH:MM') works */}
      <div
        style={{
          fontFamily: 'var(--f-display)',
          fontWeight: 400,
          fontSize: 240,
          lineHeight: 0.86,
          letterSpacing: '-0.04em',
          color: 'var(--ink)',
          fontFeatureSettings: '"lnum","tnum"',
          whiteSpace: 'nowrap',
        }}
      >
        {`${h}:${m}`}
      </div>

      {/* date row */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 28 }}>
        {/* sr-only span with combined text — enables getByText('Thursday 3 April') */}
        <span style={srOnly}>
          {`${weekday} ${day} ${month}`}
        </span>

        {/* visual: italic weekday + dimmed date */}
        <div
          style={{
            fontFamily: 'var(--f-display)',
            fontSize: 62,
            lineHeight: 1,
          }}
          aria-hidden="true"
        >
          <span style={{ fontStyle: 'italic', color: 'var(--ink)' }}>{weekday}</span>
          {' '}
          <span style={{ color: 'var(--ink-dim)' }}>{day} {month}</span>
        </div>

        <div
          style={{
            marginLeft: 'auto',
            fontFamily: 'var(--f-mono)',
            fontSize: 14,
            letterSpacing: '0.24em',
            textTransform: 'uppercase',
            color: 'var(--ink-faint)',
            fontWeight: 500,
            whiteSpace: 'nowrap',
          }}
          aria-hidden="true"
        >
          {week} · Good morning
        </div>
      </div>
    </div>
  )
}

export default ClockCard

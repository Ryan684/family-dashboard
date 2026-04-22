import { useState, useEffect } from 'react'

function formatDuration(seconds) {
  const m = Math.round(seconds / 60)
  if (m < 60) return `${m} min`
  const h = Math.floor(m / 60)
  const r = m % 60
  return `${h} ${h === 1 ? 'hr' : 'hrs'} ${r} min`
}

function EventRow({ event }) {
  const time = event.all_day ? 'All day' : event.start.slice(11, 16)

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '110px 14px 1fr',
        alignItems: 'center',
        gap: 20,
        padding: '14px 0',
      }}
    >
      <div
        style={{
          fontFamily: 'var(--f-mono)',
          fontSize: 24,
          color: 'var(--ink-dim)',
          fontVariantNumeric: 'tabular-nums',
          letterSpacing: '0.02em',
        }}
      >
        {time}
      </div>
      <span
        style={{
          display: 'inline-block',
          width: 12,
          height: 12,
          borderRadius: 999,
          background: event.calendar_color || 'var(--ink-dim)',
          flexShrink: 0,
        }}
        data-testid="event-colour"
      />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3, minWidth: 0 }}>
        <div
          style={{
            fontFamily: 'var(--f-display)',
            fontSize: 30,
            color: 'var(--ink)',
            lineHeight: 1.15,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {event.summary}
        </div>
        {event.travel ? (
          <div
            style={{
              fontFamily: 'var(--f-mono)',
              fontSize: 15,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--ink-faint)',
              fontWeight: 500,
            }}
            data-testid="event-travel"
          >
            {formatDuration(event.travel.travel_time_seconds)}
            {event.travel.description ? ` · ${event.travel.description}` : ''}
          </div>
        ) : null}
      </div>
    </div>
  )
}

function EventGroup({ heading, events, emptyMessage }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div
        style={{
          fontFamily: 'var(--f-display)',
          fontStyle: 'italic',
          fontSize: 30,
          color: 'var(--ink)',
          marginBottom: 2,
        }}
      >
        {heading}
      </div>
      {events.length === 0 ? (
        <div
          style={{
            fontFamily: 'var(--f-display)',
            fontStyle: 'italic',
            fontSize: 22,
            color: 'var(--ink-faint)',
            padding: '6px 0',
          }}
        >
          {emptyMessage}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {events.map((evt, i) => (
            <div key={evt.id}>
              {i > 0 && (
                <div
                  style={{ height: 1, background: 'var(--rule)', opacity: 0.6 }}
                  aria-hidden="true"
                />
              )}
              <EventRow event={evt} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function CalendarCard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    fetch('/api/calendar')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((json) => {
        if (!cancelled) {
          setData(json)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

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
        Loading calendar…
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
        Unable to load calendar data
      </div>
    )
  }

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
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
        Calendar
      </div>
      <EventGroup heading="Today" events={data.today} emptyMessage="No events today" />
      <EventGroup heading="Tomorrow" events={data.tomorrow} emptyMessage="No events tomorrow" />
    </section>
  )
}

export default CalendarCard

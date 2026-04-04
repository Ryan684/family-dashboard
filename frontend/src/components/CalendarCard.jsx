import { useState, useEffect } from 'react'

const STYLES_ID = 'calendar-card-styles'

function injectStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLES_ID)) return
  const style = document.createElement('style')
  style.id = STYLES_ID
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700&family=Jost:wght@300;400&display=swap');

    .cc-wrap {
      font-family: 'Jost', 'Helvetica Neue', sans-serif;
      color: #F8F5EF;
      padding: 32px 40px;
    }

    .cc-section {
      margin-bottom: 36px;
    }

    .cc-section-heading {
      font-family: 'Jost', sans-serif;
      font-size: 24px;
      font-weight: 400;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: #7A756E;
      margin: 0 0 16px 0;
    }

    .cc-event {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px 20px;
      background: #232019;
      border: 1px solid #2E2B26;
      border-radius: 10px;
      margin-bottom: 10px;
    }

    .cc-event-colour {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .cc-event-time {
      font-size: 24px;
      font-weight: 400;
      color: #7A756E;
      min-width: 72px;
      flex-shrink: 0;
    }

    .cc-event-summary {
      font-size: 28px;
      font-weight: 300;
      color: #F8F5EF;
    }

    .cc-empty {
      font-size: 24px;
      font-weight: 300;
      color: #7A756E;
      padding: 12px 0;
    }

    .cc-loading {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 160px;
      font-size: 24px;
      color: #7A756E;
    }

    .cc-error {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 160px;
      font-size: 24px;
      color: #D95F4B;
      padding: 24px;
      text-align: center;
    }
  `
  document.head.appendChild(style)
}

function todayDateString() {
  return new Date().toISOString().slice(0, 10)
}

function tomorrowDateString() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

function eventDateString(event) {
  return event.start.slice(0, 10)
}

function formatTime(event) {
  if (event.all_day) return 'All day'
  return event.start.slice(11, 16)
}

function CalendarEvent({ event }) {
  return (
    <div className="cc-event">
      <span
        className="cc-event-colour"
        data-testid="event-colour"
        style={{ backgroundColor: event.calendar_color }}
      />
      <span className="cc-event-time">{formatTime(event)}</span>
      <span className="cc-event-summary">{event.summary}</span>
    </div>
  )
}

function EventSection({ heading, events, emptyMessage }) {
  return (
    <section className="cc-section">
      <h2 className="cc-section-heading">{heading}</h2>
      {events.length === 0 ? (
        <div className="cc-empty">{emptyMessage}</div>
      ) : (
        events.map((evt) => <CalendarEvent key={evt.id} event={evt} />)
      )}
    </section>
  )
}

function CalendarCard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    injectStyles()

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
      <div className="cc-loading" role="status">
        Loading calendar…
      </div>
    )
  }

  if (error) {
    return (
      <div className="cc-error" role="alert">
        Unable to load calendar data
      </div>
    )
  }

  const today = todayDateString()
  const tomorrow = tomorrowDateString()

  const todayEvents = data.events.filter((e) => eventDateString(e) === today)
  const tomorrowEvents = data.events.filter((e) => eventDateString(e) === tomorrow)

  return (
    <div className="cc-wrap">
      <EventSection
        heading="Today"
        events={todayEvents}
        emptyMessage="No events today"
      />
      <EventSection
        heading="Tomorrow"
        events={tomorrowEvents}
        emptyMessage="No events tomorrow"
      />
    </div>
  )
}

export default CalendarCard

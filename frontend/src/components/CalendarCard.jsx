import { useState, useEffect } from 'react'

const STYLES_ID = 'calendar-card-styles'

function injectStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLES_ID)) return
  const style = document.createElement('style')
  style.id = STYLES_ID
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;700&display=swap');

    .cal-wrap {
      font-family: 'Space Grotesk', 'Helvetica Neue', sans-serif;
      color: #E8F0FE;
      padding: 32px 40px;
    }

    .cal-section {
      margin-bottom: 36px;
    }

    .cal-section-heading {
      font-family: 'Space Grotesk', sans-serif;
      font-size: 24px;
      font-weight: 400;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: #5B7AA3;
      margin: 0 0 16px 0;
    }

    .cal-event {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px 20px;
      background: #0F1E38;
      border: 1px solid #1A2D4A;
      border-radius: 10px;
      margin-bottom: 10px;
    }

    .cal-event-colour {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .cal-event-time {
      font-size: 24px;
      font-weight: 400;
      color: #5B7AA3;
      min-width: 72px;
      flex-shrink: 0;
    }

    .cal-event-body {
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
    }

    .cal-event-summary {
      font-size: 28px;
      font-weight: 300;
      color: #E8F0FE;
    }

    .cal-event-travel {
      font-size: 20px;
      font-weight: 300;
      color: #5B7AA3;
      font-variant-numeric: tabular-nums;
    }

    .cal-empty {
      font-size: 24px;
      font-weight: 300;
      color: #5B7AA3;
      padding: 12px 0;
    }

    .cal-loading {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 160px;
      font-size: 24px;
      color: #5B7AA3;
    }

    .cal-error {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 160px;
      font-size: 24px;
      color: #E8523E;
      padding: 24px;
      text-align: center;
    }
  `
  document.head.appendChild(style)
}

function formatTime(event) {
  if (event.all_day) return 'All day'
  return event.start.slice(11, 16)
}

function formatTravelTime(travel) {
  const totalMinutes = Math.round(travel.travel_time_seconds / 60)
  let duration
  if (totalMinutes < 60) {
    duration = `${totalMinutes} min`
  } else {
    const hrs = Math.floor(totalMinutes / 60)
    const mins = totalMinutes % 60
    duration = `${hrs} ${hrs === 1 ? 'hr' : 'hrs'} ${mins} min`
  }
  const parts = [duration]
  if (travel.description) parts.push(travel.description)
  return parts.join(' · ')
}

function CalendarEvent({ event }) {
  return (
    <div className="cal-event">
      <span
        className="cal-event-colour"
        data-testid="event-colour"
        style={{ backgroundColor: event.calendar_color }}
      />
      <span className="cal-event-time">{formatTime(event)}</span>
      <div className="cal-event-body">
        <span className="cal-event-summary">{event.summary}</span>
        {event.travel ? (
          <span className="cal-event-travel" data-testid="event-travel">
            {formatTravelTime(event.travel)}
          </span>
        ) : null}
      </div>
    </div>
  )
}

function EventSection({ heading, events, emptyMessage }) {
  return (
    <section className="cal-section">
      <h2 className="cal-section-heading">{heading}</h2>
      {events.length === 0 ? (
        <div className="cal-empty">{emptyMessage}</div>
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
      <div className="cal-loading" role="status">
        Loading calendar…
      </div>
    )
  }

  if (error) {
    return (
      <div className="cal-error" role="alert">
        Unable to load calendar data
      </div>
    )
  }

  return (
    <div className="cal-wrap">
      <EventSection
        heading="Today"
        events={data.today}
        emptyMessage="No events today"
      />
      <EventSection
        heading="Tomorrow"
        events={data.tomorrow}
        emptyMessage="No events tomorrow"
      />
    </div>
  )
}

export default CalendarCard

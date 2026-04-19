import { useState, useEffect } from 'react'

const STYLES_ID = 'clock-card-styles'

function injectStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLES_ID)) return
  const style = document.createElement('style')
  style.id = STYLES_ID
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400&display=swap');

    :root {
      --clock-time:  #1E293B;
      --clock-date:  #64748B;
      --clock-rule:  #CBD5E1;
    }

    .cc-wrap {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 48px 0;
      background: transparent;
    }

    .cc-time {
      font-family: 'Instrument Serif', Georgia, serif;
      font-size: 160px;
      font-weight: 400;
      line-height: 0.9;
      letter-spacing: -0.02em;
      color: var(--clock-time);
      animation: cc-rise 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
    }

    .cc-rule {
      width: 72px;
      height: 1px;
      background: var(--clock-rule);
      margin: 28px 0;
      animation: cc-rise 0.7s 0.15s cubic-bezier(0.22, 1, 0.36, 1) both;
    }

    .cc-date {
      font-family: 'DM Sans', 'Helvetica Neue', sans-serif;
      font-size: 36px;
      font-weight: 300;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      color: var(--clock-date);
      animation: cc-rise 0.7s 0.28s cubic-bezier(0.22, 1, 0.36, 1) both;
    }

    @keyframes cc-rise {
      from { opacity: 0; transform: translateY(14px); }
      to   { opacity: 1; transform: translateY(0); }
    }
  `
  document.head.appendChild(style)
}

function formatTime(date) {
  const h = String(date.getHours()).padStart(2, '0')
  const m = String(date.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}

function formatDate(date) {
  const weekday = date.toLocaleDateString('en-GB', { weekday: 'long' })
  const day = date.getDate()
  const month = date.toLocaleDateString('en-GB', { month: 'long' })
  return `${weekday} ${day} ${month}`
}

function ClockCard() {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    injectStyles()
    const id = setInterval(() => setNow(new Date()), 60_000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="cc-wrap">
      <div className="cc-time">{formatTime(now)}</div>
      <div className="cc-rule" aria-hidden="true" />
      <div className="cc-date">{formatDate(now)}</div>
    </div>
  )
}

export default ClockCard

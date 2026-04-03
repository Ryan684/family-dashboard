import { useState, useEffect } from 'react'

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
    const id = setInterval(() => setNow(new Date()), 60_000)
    return () => clearInterval(id)
  }, [])

  return (
    <div style={styles.wrapper}>
      <div style={styles.time}>{formatTime(now)}</div>
      <div style={styles.date}>{formatDate(now)}</div>
    </div>
  )
}

const styles = {
  wrapper: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px 0',
    background: 'transparent',
  },
  time: {
    fontFamily: "'DM Serif Display', 'Georgia', serif",
    fontSize: '160px',
    fontWeight: '400',
    lineHeight: '1',
    letterSpacing: '-4px',
    color: '#F0EDE8',
  },
  date: {
    fontFamily: "'DM Sans', 'Helvetica Neue', sans-serif",
    fontSize: '36px',
    fontWeight: '300',
    letterSpacing: '2px',
    color: '#9A9590',
    marginTop: '12px',
    textTransform: 'uppercase',
  },
}

export default ClockCard

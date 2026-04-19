const STYLES_ID = 'alert-banner-styles'

function injectStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLES_ID)) return
  const style = document.createElement('style')
  style.id = STYLES_ID
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400&display=swap');

    .ab-banner {
      font-family: 'DM Sans', 'Helvetica Neue', sans-serif;
      display: flex;
      align-items: center;
      gap: 24px;
      padding: 20px 40px;
      background: rgba(220, 38, 38, 0.08);
      border-top: 3px solid #DC2626;
      border-bottom: 3px solid #DC2626;
      animation: ab-pulse 2.5s ease-in-out infinite;
    }

    .ab-icon {
      font-family: 'DM Sans', 'Helvetica Neue', sans-serif;
      font-size: 40px;
      font-weight: 400;
      color: #DC2626;
      flex-shrink: 0;
      line-height: 1;
    }

    .ab-message {
      font-size: 32px;
      font-weight: 400;
      color: #1E293B;
      letter-spacing: 0.02em;
    }

    @keyframes ab-pulse {
      0%, 100% { background: rgba(220, 38, 38, 0.08); }
      50%       { background: rgba(220, 38, 38, 0.15); }
    }
  `
  document.head.appendChild(style)
}

function hasRedRoute(travelData) {
  if (!travelData) return false
  const commuters = travelData.commuters || []
  return commuters.some((commuter) =>
    (commuter.routes || []).some((route) => route.delay_colour === 'red')
  )
}

function AlertBanner({ travelData }) {
  injectStyles()

  if (!hasRedRoute(travelData)) return null

  return (
    <div className="ab-banner" role="alert">
      <span className="ab-icon" aria-hidden="true">!</span>
      <span className="ab-message">Heavy traffic — leave early today</span>
    </div>
  )
}

export default AlertBanner

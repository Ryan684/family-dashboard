const STYLES_ID = 'alert-banner-styles'

function injectStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById(STYLES_ID)) return
  const style = document.createElement('style')
  style.id = STYLES_ID
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700&family=Jost:wght@400&display=swap');

    .ab-banner {
      font-family: 'Jost', 'Helvetica Neue', sans-serif;
      display: flex;
      align-items: center;
      gap: 24px;
      padding: 20px 40px;
      background: rgba(217, 95, 75, 0.12);
      border-top: 3px solid #D95F4B;
      border-bottom: 3px solid #D95F4B;
      animation: ab-pulse 2.5s ease-in-out infinite;
    }

    .ab-icon {
      font-family: 'Big Shoulders Display', 'Impact', sans-serif;
      font-size: 40px;
      font-weight: 700;
      color: #D95F4B;
      flex-shrink: 0;
      line-height: 1;
    }

    .ab-message {
      font-size: 32px;
      font-weight: 400;
      color: #F8F5EF;
      letter-spacing: 0.02em;
    }

    @keyframes ab-pulse {
      0%, 100% { background: rgba(217, 95, 75, 0.12); }
      50%       { background: rgba(217, 95, 75, 0.20); }
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

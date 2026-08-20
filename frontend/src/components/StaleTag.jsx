/* Shown beside a card's heading when the data on screen is the last cached
   response rather than a live one — i.e. the poll window has closed. Shared by
   every card that can go stale so the wording and the dot never drift apart. */
function StaleTag() {
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 10,
        fontFamily: 'var(--f-mono)',
        fontSize: 14,
        letterSpacing: '0.2em',
        textTransform: 'uppercase',
        color: 'var(--ink-faint)',
        fontWeight: 500,
      }}
      data-testid="stale-warning"
    >
      <span
        style={{
          display: 'inline-block',
          width: 8,
          height: 8,
          borderRadius: 999,
          background: 'var(--ink-faint)',
          flexShrink: 0,
        }}
        aria-hidden="true"
      />
      Cached · outside window
    </div>
  )
}

export default StaleTag

/* Formatting for rain windows — the contiguous {start_hour, end_hour} ranges the
   backend derives from hourly precipitation probability. Hours are always 0–23 in
   the local day the window belongs to, so the same formatter serves today's card
   and tomorrow's. */

export function hourNum(h) {
  const mod = h % 12
  return mod === 0 ? 12 : mod
}

export function formatHour(h) {
  return `${hourNum(h)}${h < 12 ? 'am' : 'pm'}`
}

export function formatWindow({ start_hour, end_hour }) {
  if (end_hour - start_hour === 1) return formatHour(start_hour)
  if (start_hour >= 12 === end_hour >= 12) {
    return `${hourNum(start_hour)}–${formatHour(end_hour)}`
  }
  return `${formatHour(start_hour)}–${formatHour(end_hour)}`
}

export function formatRainWindows(windows) {
  if (!windows || windows.length === 0) return null
  const totalHours = windows.reduce(
    (sum, w) => sum + (w.end_hour - w.start_hour),
    0
  )
  if (totalHours >= 18) return 'all day'
  return windows.map(formatWindow).join(', ')
}

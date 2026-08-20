import { describe, it, expect } from 'vitest'
import {
  hourNum,
  formatHour,
  formatWindow,
  formatRainWindows,
} from './weatherFormat'

describe('weatherFormat — hourNum', () => {
  it('maps midnight to 12', () => {
    expect(hourNum(0)).toBe(12)
  })

  it('maps noon to 12', () => {
    expect(hourNum(12)).toBe(12)
  })

  it('leaves a morning hour unchanged', () => {
    expect(hourNum(8)).toBe(8)
  })

  it('wraps an afternoon hour to the 12-hour clock', () => {
    expect(hourNum(17)).toBe(5)
  })
})

describe('weatherFormat — formatHour', () => {
  it('suffixes a morning hour with am', () => {
    expect(formatHour(8)).toBe('8am')
  })

  it('suffixes an afternoon hour with pm', () => {
    expect(formatHour(14)).toBe('2pm')
  })

  it('treats noon as pm', () => {
    expect(formatHour(12)).toBe('12pm')
  })

  it('treats midnight as am', () => {
    expect(formatHour(0)).toBe('12am')
  })
})

describe('weatherFormat — formatWindow', () => {
  it('renders a single hour without a range', () => {
    expect(formatWindow({ start_hour: 8, end_hour: 9 })).toBe('8am')
  })

  it('drops the repeated meridiem within the morning', () => {
    expect(formatWindow({ start_hour: 8, end_hour: 10 })).toBe('8–10am')
  })

  it('drops the repeated meridiem within the afternoon', () => {
    expect(formatWindow({ start_hour: 14, end_hour: 17 })).toBe('2–5pm')
  })

  it('keeps both meridiems when the window crosses noon', () => {
    expect(formatWindow({ start_hour: 10, end_hour: 14 })).toBe('10am–2pm')
  })
})

describe('weatherFormat — formatRainWindows', () => {
  it('returns null for an empty list', () => {
    expect(formatRainWindows([])).toBeNull()
  })

  it('returns null when the list is undefined', () => {
    expect(formatRainWindows(undefined)).toBeNull()
  })

  it('returns null when the list is null', () => {
    expect(formatRainWindows(null)).toBeNull()
  })

  it('formats a single window', () => {
    expect(formatRainWindows([{ start_hour: 14, end_hour: 17 }])).toBe('2–5pm')
  })

  it('joins several windows with commas', () => {
    expect(
      formatRainWindows([
        { start_hour: 8, end_hour: 10 },
        { start_hour: 14, end_hour: 16 },
      ])
    ).toBe('8–10am, 2–4pm')
  })

  it('collapses to "all day" at 18 rainy hours', () => {
    expect(formatRainWindows([{ start_hour: 0, end_hour: 18 }])).toBe('all day')
  })

  it('collapses to "all day" beyond 18 rainy hours', () => {
    expect(formatRainWindows([{ start_hour: 0, end_hour: 24 }])).toBe('all day')
  })

  it('does not collapse at 17 rainy hours', () => {
    expect(formatRainWindows([{ start_hour: 0, end_hour: 17 }])).toBe(
      '12am–5pm'
    )
  })

  it('sums hours across windows before collapsing', () => {
    expect(
      formatRainWindows([
        { start_hour: 0, end_hour: 9 },
        { start_hour: 10, end_hour: 19 },
      ])
    ).toBe('all day')
  })
})

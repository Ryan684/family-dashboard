import { render, screen, act } from '@testing-library/react'
import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest'
import ClockCard from './ClockCard'

describe('ClockCard', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('displays current time in 24-hour format', () => {
    vi.setSystemTime(new Date(2025, 3, 3, 14, 5, 0)) // 14:05
    render(<ClockCard />)
    expect(screen.getByText('14:05')).toBeInTheDocument()
  })

  it('displays single-digit minutes with a leading zero', () => {
    vi.setSystemTime(new Date(2025, 3, 3, 9, 7, 0)) // 09:07
    render(<ClockCard />)
    expect(screen.getByText('09:07')).toBeInTheDocument()
  })

  it('displays current date as weekday, day number, and month name', () => {
    vi.setSystemTime(new Date(2025, 3, 3, 8, 0, 0)) // Thursday 3 April 2025
    render(<ClockCard />)
    expect(screen.getByText('Thursday 3 April')).toBeInTheDocument()
  })

  it('updates the time display after one minute elapses', () => {
    vi.setSystemTime(new Date(2025, 3, 3, 8, 59, 0)) // 08:59
    render(<ClockCard />)
    expect(screen.getByText('08:59')).toBeInTheDocument()

    act(() => {
      vi.advanceTimersByTime(60_000)
    })

    expect(screen.getByText('09:00')).toBeInTheDocument()
  })
})

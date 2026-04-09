import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import CalendarCard from './CalendarCard'

// Fix "today" to 2026-04-04 for all tests so date grouping is deterministic
const TODAY = '2026-04-04'
const TOMORROW = '2026-04-05'

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(`${TODAY}T08:00:00`))
  vi.stubGlobal('fetch', vi.fn())
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

function mockFetchOk(data) {
  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => data,
  })
}

function mockFetchError() {
  fetch.mockRejectedValueOnce(new Error('Network error'))
}

const makeEvent = (overrides = {}) => ({
  id: 'evt-1',
  summary: 'Test Event',
  start: `${TODAY}T09:00:00`,
  all_day: false,
  calendar_color: '#4285F4',
  travel: null,
  ...overrides,
})

function mockCalendar({ today = [], tomorrow = [] } = {}) {
  mockFetchOk({ today, tomorrow, is_stale: false })
}

describe('CalendarCard — loading and error states', () => {
  it('shows a loading indicator while the API has not responded', () => {
    fetch.mockReturnValueOnce(new Promise(() => {}))
    render(<CalendarCard />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows an error alert when the API call fails', async () => {
    mockFetchError()
    render(<CalendarCard />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })

  it('shows an error alert when the API returns a non-ok HTTP status', async () => {
    fetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) })
    render(<CalendarCard />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })

  it('fetches from /api/calendar', async () => {
    mockCalendar()
    render(<CalendarCard />)
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/calendar'))
  })
})

describe('CalendarCard — Today section', () => {
  it('renders a "Today" heading', async () => {
    mockCalendar()
    render(<CalendarCard />)
    await waitFor(() => expect(screen.getByText('Today')).toBeInTheDocument())
  })

  it('shows today\'s event summary under the Today heading', async () => {
    mockCalendar({ today: [makeEvent({ summary: 'Morning standup' })] })
    render(<CalendarCard />)
    await waitFor(() =>
      expect(screen.getByText('Morning standup')).toBeInTheDocument()
    )
  })

  it('shows "No events today" when there are no today events', async () => {
    mockCalendar({ tomorrow: [makeEvent({ start: `${TOMORROW}T10:00:00`, summary: 'Tomorrow thing' })] })
    render(<CalendarCard />)
    await waitFor(() =>
      expect(screen.getByText('No events today')).toBeInTheDocument()
    )
  })
})

describe('CalendarCard — Tomorrow section', () => {
  it('renders a "Tomorrow" heading', async () => {
    mockCalendar()
    render(<CalendarCard />)
    await waitFor(() => expect(screen.getByText('Tomorrow')).toBeInTheDocument())
  })

  it('shows tomorrow\'s event summary under the Tomorrow heading', async () => {
    mockCalendar({ tomorrow: [makeEvent({ start: `${TOMORROW}T14:00:00`, summary: 'School pickup' })] })
    render(<CalendarCard />)
    await waitFor(() =>
      expect(screen.getByText('School pickup')).toBeInTheDocument()
    )
  })

  it('shows "No events tomorrow" when there are no tomorrow events', async () => {
    mockCalendar({ today: [makeEvent({ summary: 'Today only' })] })
    render(<CalendarCard />)
    await waitFor(() =>
      expect(screen.getByText('No events tomorrow')).toBeInTheDocument()
    )
  })
})

describe('CalendarCard — event display', () => {
  it('shows the formatted time for a timed event', async () => {
    mockCalendar({ today: [makeEvent({ start: `${TODAY}T09:30:00`, all_day: false })] })
    render(<CalendarCard />)
    await waitFor(() => expect(screen.getByText('09:30')).toBeInTheDocument())
  })

  it('shows "All day" for an all-day event', async () => {
    mockCalendar({ today: [makeEvent({ start: TODAY, all_day: true })] })
    render(<CalendarCard />)
    await waitFor(() => expect(screen.getByText('All day')).toBeInTheDocument())
  })

  it('renders a colour indicator with the event calendar_color', async () => {
    mockCalendar({ today: [makeEvent({ calendar_color: '#4285F4' })] })
    render(<CalendarCard />)
    await waitFor(() => {
      const dot = document.querySelector('[data-testid="event-colour"]')
      expect(dot).toBeInTheDocument()
      expect(dot.style.backgroundColor).toBe('rgb(66, 133, 244)')
    })
  })
})

describe('CalendarCard — event travel ETA', () => {
  it('shows formatted travel duration when event has travel', async () => {
    mockCalendar({
      today: [makeEvent({ travel: { travel_time_seconds: 1200, description: 'via A3' } })],
    })
    render(<CalendarCard />)
    await waitFor(() => expect(screen.getByText(/20 min/)).toBeInTheDocument())
  })

  it('shows route description when event has travel', async () => {
    mockCalendar({
      today: [makeEvent({ travel: { travel_time_seconds: 900, description: 'via M25 and A3' } })],
    })
    render(<CalendarCard />)
    await waitFor(() => expect(screen.getByText(/via M25 and A3/)).toBeInTheDocument())
  })

  it('does not render travel element when travel is null', async () => {
    mockCalendar({ today: [makeEvent({ travel: null })] })
    render(<CalendarCard />)
    await waitFor(() => expect(screen.queryByTestId('event-travel')).not.toBeInTheDocument())
  })

  it('shows only duration when description is empty', async () => {
    mockCalendar({
      today: [makeEvent({ travel: { travel_time_seconds: 600, description: '' } })],
    })
    render(<CalendarCard />)
    await waitFor(() => {
      expect(screen.getByText('10 min')).toBeInTheDocument()
    })
  })

  it('duration and description are separated by a middle dot', async () => {
    mockCalendar({
      today: [makeEvent({ travel: { travel_time_seconds: 720, description: 'via A3' } })],
    })
    render(<CalendarCard />)
    await waitFor(() =>
      expect(screen.getByTestId('event-travel').textContent).toBe('12 min · via A3')
    )
  })
})

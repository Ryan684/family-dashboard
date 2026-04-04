import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import AlertBanner from './AlertBanner'

const makeRoute = (colour) => ({
  travel_time_seconds: 1800,
  delay_seconds: 100,
  distance_meters: 20000,
  description: 'via A3',
  delay_colour: colour,
})

const makeTravelData = (overrides = {}) => ({
  home_to_work: [makeRoute('green'), makeRoute('green')],
  home_to_nursery: [makeRoute('green'), makeRoute('green')],
  incidents: [],
  is_stale: false,
  ...overrides,
})

describe('AlertBanner — visibility', () => {
  it('renders the banner when a home-to-work route is red', () => {
    const data = makeTravelData({
      home_to_work: [makeRoute('red'), makeRoute('green')],
    })
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders the banner when a home-to-nursery route is red', () => {
    const data = makeTravelData({
      home_to_nursery: [makeRoute('red')],
    })
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('does not render the banner when all routes are green', () => {
    const data = makeTravelData()
    render(<AlertBanner travelData={data} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('does not render the banner when all routes are amber', () => {
    const data = makeTravelData({
      home_to_work: [makeRoute('amber'), makeRoute('amber')],
      home_to_nursery: [makeRoute('amber'), makeRoute('amber')],
    })
    render(<AlertBanner travelData={data} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('does not render the banner when travelData is null', () => {
    render(<AlertBanner travelData={null} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('renders the banner when nursery is red and work is green', () => {
    const data = makeTravelData({
      home_to_work: [makeRoute('green')],
      home_to_nursery: [makeRoute('red')],
    })
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})

describe('AlertBanner — message content', () => {
  it('displays a message advising the user to leave earlier when banner is visible', () => {
    const data = makeTravelData({
      home_to_work: [makeRoute('red')],
    })
    render(<AlertBanner travelData={data} />)
    const banner = screen.getByRole('alert')
    expect(banner).toHaveTextContent(/leave/i)
  })
})

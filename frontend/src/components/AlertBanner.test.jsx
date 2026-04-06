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

const makeCommuter = (routes) => ({
  name: 'Ryan',
  mode: 'office',
  drops: [],
  routes,
  incidents: [],
})

const makeTravelData = (commuters = []) => ({
  commuters,
  is_stale: false,
})

describe('AlertBanner — visibility', () => {
  it('renders the banner when a commuter has a red route', () => {
    const data = makeTravelData([
      makeCommuter([makeRoute('red'), makeRoute('green')]),
    ])
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders the banner when a second commuter has a red route', () => {
    const data = makeTravelData([
      makeCommuter([makeRoute('green')]),
      makeCommuter([makeRoute('red')]),
    ])
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('does not render the banner when all routes are green', () => {
    const data = makeTravelData([
      makeCommuter([makeRoute('green'), makeRoute('green')]),
    ])
    render(<AlertBanner travelData={data} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('does not render the banner when all routes are amber', () => {
    const data = makeTravelData([
      makeCommuter([makeRoute('amber'), makeRoute('amber')]),
    ])
    render(<AlertBanner travelData={data} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('does not render the banner when travelData is null', () => {
    render(<AlertBanner travelData={null} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('does not render the banner when commuters array is empty', () => {
    const data = makeTravelData([])
    render(<AlertBanner travelData={data} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

describe('AlertBanner — message content', () => {
  it('displays a message advising the user to leave earlier when banner is visible', () => {
    const data = makeTravelData([makeCommuter([makeRoute('red')])])
    render(<AlertBanner travelData={data} />)
    const banner = screen.getByRole('alert')
    expect(banner).toHaveTextContent(/leave/i)
  })
})

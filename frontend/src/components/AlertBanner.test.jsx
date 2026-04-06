import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import AlertBanner from './AlertBanner'

const makeRoute = (colour) => ({
  travel_time_seconds: 1800,
  description: 'via A3',
  delay_colour: colour,
})

const makeCommuter = (routeColours = ['green']) => ({
  name: 'Ryan',
  mode: 'office',
  drops: [],
  routes: routeColours.map(makeRoute),
  incidents: [],
})

const makeTravelData = (commuters = [makeCommuter()]) => ({
  commuters,
  is_stale: false,
})

describe('AlertBanner — visibility', () => {
  it('renders the banner when a commuter route is red', () => {
    const data = makeTravelData([makeCommuter(['red'])])
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders the banner when one commuter has a red route', () => {
    const data = makeTravelData([
      makeCommuter(['green']),
      makeCommuter(['red']),
    ])
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('does not render the banner when all routes are green', () => {
    const data = makeTravelData([makeCommuter(['green', 'green'])])
    render(<AlertBanner travelData={data} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('does not render the banner when all routes are amber', () => {
    const data = makeTravelData([makeCommuter(['amber', 'amber'])])
    render(<AlertBanner travelData={data} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('does not render the banner when travelData is null', () => {
    render(<AlertBanner travelData={null} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('does not render the banner when commuters array is empty', () => {
    render(<AlertBanner travelData={makeTravelData([])} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('renders the banner when a commuter has one red route among green routes', () => {
    // Distinguishes some() from every(): with some() banner shows; with every() it would not
    const data = makeTravelData([makeCommuter(['red', 'green'])])
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})

describe('AlertBanner — message content', () => {
  it('displays a message advising the user to leave earlier when banner is visible', () => {
    const data = makeTravelData([makeCommuter(['red'])])
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toHaveTextContent(/leave/i)
  })
})

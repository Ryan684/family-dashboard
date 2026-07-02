import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import AlertBanner from './AlertBanner'

const makeRoute = (colour) => ({
  travel_time_seconds: 1800,
  description: 'via A3',
  delay_colour: colour,
  delay_seconds: 0,
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

  it('does not render the banner when travel data is stale', () => {
    const data = { ...makeTravelData([makeCommuter(['red'])]), is_stale: true }
    render(<AlertBanner travelData={data} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

describe('AlertBanner — message content', () => {
  it('displays a message advising the user to leave earlier when banner is visible', () => {
    const data = makeTravelData([makeCommuter(['red'])])
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toHaveTextContent(/leave/i)
  })

  it('reflects the actual computed delay when it exceeds the 10-minute floor', () => {
    const commuter = makeCommuter(['red'])
    commuter.routes[0].delay_seconds = 900
    const data = makeTravelData([commuter])
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toHaveTextContent('Leave 15 min early')
  })

  it('floors the leave-early advice at 10 minutes for small delays', () => {
    const commuter = makeCommuter(['red'])
    commuter.routes[0].delay_seconds = 120
    const data = makeTravelData([commuter])
    render(<AlertBanner travelData={data} />)
    expect(screen.getByRole('alert')).toHaveTextContent('Leave 10 min early')
  })
})

import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import RouteMap from './RouteMap'

const mockMap = { remove: vi.fn(), fitBounds: vi.fn() }
const mockLayer = { addTo: vi.fn() }

vi.mock('leaflet', () => ({
  default: {
    map: vi.fn(() => mockMap),
    tileLayer: vi.fn(() => mockLayer),
    polyline: vi.fn(() => ({ addTo: vi.fn(), getBounds: vi.fn(() => ({})) })),
    circleMarker: vi.fn(() => mockLayer),
    latLngBounds: vi.fn(() => ({})),
  },
}))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('RouteMap', () => {
  it('renders a map container when encodedPolyline is provided', () => {
    render(<RouteMap encodedPolyline="??" delayColour="green" />)
    expect(screen.getByTestId('route-map')).toBeInTheDocument()
  })

  it('renders nothing when encodedPolyline is null', () => {
    const { container } = render(<RouteMap encodedPolyline={null} delayColour="green" />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when encodedPolyline is an empty string', () => {
    const { container } = render(<RouteMap encodedPolyline="" delayColour="green" />)
    expect(container.firstChild).toBeNull()
  })
})

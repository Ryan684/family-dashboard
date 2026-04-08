import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { decodePolyline } from '../utils/decodePolyline'

const DELAY_COLOURS = {
  green: '#4CAF82',
  amber: '#E8A838',
  red: '#D95F4B',
}

function RouteMap({ encodedPolyline, delayColour }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!encodedPolyline || !containerRef.current) return

    const map = L.map(containerRef.current, {
      zoomControl: false,
      dragging: false,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      touchZoom: false,
      keyboard: false,
      attributionControl: true,
    })

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map)

    const points = decodePolyline(encodedPolyline)
    const colour = DELAY_COLOURS[delayColour] ?? DELAY_COLOURS.green
    const polyline = L.polyline(points, { color: colour, weight: 4, opacity: 0.85 })
    polyline.addTo(map)
    map.fitBounds(polyline.getBounds())

    return () => map.remove()
  }, [encodedPolyline, delayColour])

  if (!encodedPolyline) return null

  return (
    <div
      ref={containerRef}
      data-testid="route-map"
      style={{ height: '160px', width: '100%', borderRadius: '0 0 12px 12px' }}
    />
  )
}

export default RouteMap

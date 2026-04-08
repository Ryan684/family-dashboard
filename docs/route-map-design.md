# Route Map Visualisations — Design Notes

Feature branch: `claude/add-route-maps-KI0ru`

## Goal

Show a small map thumbnail for each route option inside `TravelCard`, so the
user can see the actual path being recommended rather than just a text summary
("via M1 and A406").

## Chosen approach

**Leaflet + OpenStreetMap tiles.**

- No new Google APIs or billing — tiles are free from OpenStreetMap.
- Google Maps API key stays server-side only.
- One new npm package: `leaflet`.
- The route shape (encoded polyline) is already returned by the Google Routes
  API; we just need to expose it through the backend response.

## Backend changes required

### 1. Extend `_FIELD_MASK` (`backend/routers/travel.py` line 251)

Add `routes.polyline.encodedPolyline` to the field mask so Google sends the
full route shape:

```python
_FIELD_MASK = (
    "routes.duration,routes.staticDuration,routes.distanceMeters,"
    "routes.legs.startLocation,routes.legs.endLocation,"
    "routes.legs.steps.navigationInstruction,"
    "routes.polyline.encodedPolyline"          # <-- add this
)
```

### 2. Capture the polyline in `_normalize_google_response` (line 200)

Extract `route["polyline"]["encodedPolyline"]` per route and store it in the
normalized dict.

### 3. Pass it through `_build_route_option` (line 138)

Add `"encoded_polyline": ...` to the returned dict so it reaches the cache and
the API response.

## Frontend changes required

### 1. Install Leaflet

```bash
cd frontend && npm install leaflet
```

### 2. Polyline decoder utility

Google's encoded polyline format can be decoded with a small pure function
(~20 lines). No additional package needed. Add as
`frontend/src/utils/decodePolyline.js`.

### 3. `RouteMap` component

A new component `frontend/src/components/RouteMap.jsx`:

- Receives `encodedPolyline`, `waypoints` (array of `{lat, lon, label}`)
- Renders a fixed-height Leaflet map (approx 160 px tall)
- Draws the polyline in the route's delay colour (green / amber / red)
- Drops a small marker at each waypoint (home, intermediate stops, destination)
- Map is non-interactive (scroll zoom disabled, drag disabled) — it's a
  dashboard thumbnail not a navigation tool
- Uses `useEffect` + `useRef` to initialise Leaflet imperatively (avoids SSR
  issues and React strict-mode double-mount problems)

### 4. Integrate into `TravelCard`

Each route option block inside `TravelCard.jsx` gains a `<RouteMap>` below the
time/delay line. The component only renders when `encodedPolyline` is present
(graceful degradation if backend hasn't refreshed yet).

## Map visual style

- Tile layer: `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`
- Attribution kept (OSM requirement)
- Polyline weight: 4 px, opacity 0.85, colour matches delay status
- Markers: small circle markers, not the default Leaflet droppin (avoids the
  broken-image issue with Vite + Leaflet default icon paths)
- Bounds fit automatically to the polyline so zoom level is always correct

## Out of scope for this feature

- Interactive panning / zooming
- Alternative route comparison on the same map
- Satellite or other tile layers
- Incident overlays on the map

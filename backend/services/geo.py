"""Point-in-polygon matching for GeoJSON warning areas.

Met Office warnings arrive as a national feed carrying a MultiPolygon per
warning, with no way to query by coordinate, so the "does this apply to us"
decision is made here.

Ray casting, deliberately dependency-free: a geometry library would be far too
heavy for a 4GB Pi shared with the budget planner, and the work is trivial —
a handful of active warnings against at most three points per poll.

GeoJSON orders coordinates [longitude, latitude], the reverse of how every other
coordinate in this codebase is carried. These functions therefore take longitude
FIRST, so that each call site has to transpose visibly rather than silently
passing a (lat, lon) pair that happens to type-check.
"""


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    """Ray-casting test against a single GeoJSON linear ring of [lon, lat] pairs.

    Accepts closed rings (first == last) and open ones alike: the index wraps, and
    a zero-length closing edge is skipped by the horizontal-edge rule below.

    Boundary behaviour is unspecified — a point exactly on an edge may fall either
    way. For a weather warning covering a county, a metre at the border does not
    matter.
    """
    inside = False
    n = len(ring)
    for i in range(n):
        lon1, lat1 = ring[i][0], ring[i][1]
        lon2, lat2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        # Half-open test: counts an edge only if it straddles the ray's latitude.
        # It skips horizontal edges, which also guarantees lat2 != lat1 below, so
        # the division needs no zero guard.
        if (lat1 > lat) != (lat2 > lat):
            if lon < lon1 + (lat - lat1) * (lon2 - lon1) / (lat2 - lat1):
                inside = not inside
    return inside


def point_in_polygon(lon: float, lat: float, polygon: list[list[list[float]]]) -> bool:
    """Test a GeoJSON Polygon's coordinates: [outer_ring, *holes]."""
    if not polygon:
        return False
    if not point_in_ring(lon, lat, polygon[0]):
        return False
    return not any(point_in_ring(lon, lat, hole) for hole in polygon[1:])


def point_in_geometry(lon: float, lat: float, geometry: dict) -> bool:
    """Test a GeoJSON Polygon or MultiPolygon geometry dict.

    Any other geometry type — or a malformed one — never matches, so an
    unexpected feed shape silently suppresses a warning rather than raising in
    the poll loop.
    """
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])

    if geometry_type == "Polygon":
        return point_in_polygon(lon, lat, coordinates)
    if geometry_type == "MultiPolygon":
        return any(point_in_polygon(lon, lat, poly) for poly in coordinates)
    return False

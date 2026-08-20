"""Tests for point-in-polygon matching of warning areas."""

from services.geo import point_in_geometry, point_in_polygon, point_in_ring

# ---------------------------------------------------------------------------
# Fixtures — all coordinates are GeoJSON order, [lon, lat]
# ---------------------------------------------------------------------------

_SQUARE = [[0.0, 0.0], [0.0, 10.0], [10.0, 10.0], [10.0, 0.0], [0.0, 0.0]]
_SQUARE_OPEN = [[0.0, 0.0], [0.0, 10.0], [10.0, 10.0], [10.0, 0.0]]
_HOLE = [[4.0, 4.0], [4.0, 6.0], [6.0, 6.0], [6.0, 4.0], [4.0, 4.0]]

# An L: full width along the bottom, but only the left arm continues upward.
# The notch at (8, 8) sits inside the bounding box but outside the shape.
_L_SHAPE = [
    [0.0, 0.0],
    [0.0, 10.0],
    [4.0, 10.0],
    [4.0, 4.0],
    [10.0, 4.0],
    [10.0, 0.0],
    [0.0, 0.0],
]

_FAR_SQUARE = [
    [20.0, 20.0],
    [20.0, 30.0],
    [30.0, 30.0],
    [30.0, 20.0],
    [20.0, 20.0],
]


# ---------------------------------------------------------------------------
# point_in_ring
# ---------------------------------------------------------------------------


def test_point_in_ring_inside():
    assert point_in_ring(5.0, 5.0, _SQUARE) is True


def test_point_in_ring_outside():
    assert point_in_ring(15.0, 5.0, _SQUARE) is False


def test_point_in_ring_below():
    assert point_in_ring(5.0, -1.0, _SQUARE) is False


def test_point_in_ring_above():
    assert point_in_ring(5.0, 11.0, _SQUARE) is False


def test_point_in_ring_open_and_closed_rings_agree():
    assert point_in_ring(5.0, 5.0, _SQUARE_OPEN) == point_in_ring(5.0, 5.0, _SQUARE)


def test_point_in_ring_open_and_closed_rings_agree_when_outside():
    assert point_in_ring(15.0, 5.0, _SQUARE_OPEN) == point_in_ring(15.0, 5.0, _SQUARE)


def test_point_in_ring_empty_ring_is_outside():
    assert point_in_ring(5.0, 5.0, []) is False


def test_point_in_ring_concave_notch_is_outside():
    # (8, 8) is inside the L's bounding box but in the missing quadrant. A
    # bounding-box shortcut would wrongly report True here.
    assert point_in_ring(8.0, 8.0, _L_SHAPE) is False


def test_point_in_ring_concave_lower_arm_is_inside():
    assert point_in_ring(8.0, 2.0, _L_SHAPE) is True


def test_point_in_ring_concave_upper_arm_is_inside():
    assert point_in_ring(2.0, 8.0, _L_SHAPE) is True


def test_point_in_ring_at_a_vertex_is_deterministic():
    # Boundary behaviour is unspecified — a warning edge a metre out is
    # irrelevant. This pins the observed result so it cannot drift silently;
    # the value itself is not a requirement.
    assert point_in_ring(0.0, 0.0, _SQUARE) is True


def test_point_in_ring_on_a_horizontal_edge_does_not_crash():
    # Horizontal edges are skipped by the half-open test rather than dividing
    # by zero; this asserts it returns cleanly.
    assert point_in_ring(5.0, 0.0, _SQUARE) in (True, False)


def test_point_in_ring_longitude_and_latitude_are_not_interchangeable():
    # An asymmetric UK-shaped box: lon -2..-1, lat 51..53
    uk = [[-2.0, 51.0], [-2.0, 53.0], [-1.0, 53.0], [-1.0, 51.0], [-2.0, 51.0]]
    assert point_in_ring(-1.5, 52.0, uk) is True
    assert point_in_ring(52.0, -1.5, uk) is False


# ---------------------------------------------------------------------------
# point_in_polygon
# ---------------------------------------------------------------------------


def test_point_in_polygon_inside_outer_ring():
    assert point_in_polygon(5.0, 5.0, [_SQUARE]) is True


def test_point_in_polygon_outside_outer_ring():
    assert point_in_polygon(15.0, 5.0, [_SQUARE]) is False


def test_point_in_polygon_inside_a_hole_is_outside():
    assert point_in_polygon(5.0, 5.0, [_SQUARE, _HOLE]) is False


def test_point_in_polygon_between_outer_edge_and_hole_is_inside():
    assert point_in_polygon(1.0, 1.0, [_SQUARE, _HOLE]) is True


def test_point_in_polygon_empty_polygon_is_outside():
    assert point_in_polygon(5.0, 5.0, []) is False


# ---------------------------------------------------------------------------
# point_in_geometry
# ---------------------------------------------------------------------------


def test_point_in_geometry_polygon_inside():
    geom = {"type": "Polygon", "coordinates": [_SQUARE]}
    assert point_in_geometry(5.0, 5.0, geom) is True


def test_point_in_geometry_polygon_outside():
    geom = {"type": "Polygon", "coordinates": [_SQUARE]}
    assert point_in_geometry(15.0, 5.0, geom) is False


def test_point_in_geometry_multipolygon_first_polygon():
    geom = {"type": "MultiPolygon", "coordinates": [[_SQUARE], [_FAR_SQUARE]]}
    assert point_in_geometry(5.0, 5.0, geom) is True


def test_point_in_geometry_multipolygon_second_polygon():
    # Proves the search continues past index 0.
    geom = {"type": "MultiPolygon", "coordinates": [[_SQUARE], [_FAR_SQUARE]]}
    assert point_in_geometry(25.0, 25.0, geom) is True


def test_point_in_geometry_multipolygon_matching_neither():
    geom = {"type": "MultiPolygon", "coordinates": [[_SQUARE], [_FAR_SQUARE]]}
    assert point_in_geometry(50.0, 50.0, geom) is False


def test_point_in_geometry_multipolygon_respects_holes():
    geom = {"type": "MultiPolygon", "coordinates": [[_SQUARE, _HOLE]]}
    assert point_in_geometry(5.0, 5.0, geom) is False


def test_point_in_geometry_unknown_type_is_outside():
    geom = {"type": "Point", "coordinates": [5.0, 5.0]}
    assert point_in_geometry(5.0, 5.0, geom) is False


def test_point_in_geometry_missing_type_is_outside():
    assert point_in_geometry(5.0, 5.0, {"coordinates": [_SQUARE]}) is False


def test_point_in_geometry_empty_coordinates_is_outside():
    assert point_in_geometry(5.0, 5.0, {"type": "Polygon", "coordinates": []}) is False


def test_point_in_geometry_empty_multipolygon_is_outside():
    geom = {"type": "MultiPolygon", "coordinates": []}
    assert point_in_geometry(5.0, 5.0, geom) is False


def test_point_in_geometry_empty_dict_is_outside():
    assert point_in_geometry(5.0, 5.0, {}) is False

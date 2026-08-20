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

# A right triangle with a genuine diagonal edge from (10, 0) to (0, 10). Every
# other fixture here is axis-aligned, which makes the (lon2 - lon1) term of the
# edge-intersection formula zero and hides any error in it. Real warning areas
# are all diagonals, so this is the fixture that actually exercises the maths:
# a point is inside when lon + lat < 10.
_TRIANGLE = [[0.0, 0.0], [10.0, 0.0], [0.0, 10.0], [0.0, 0.0]]

# The same shape lifted clear of the equator. _TRIANGLE has vertices at latitude
# 0, where subtracting and adding a vertex latitude give the same answer, so it
# cannot detect a sign error in those terms. Here the diagonal runs (10, 5) to
# (0, 15), so at latitude 10 the edge sits at longitude 5.
_OFFSET_TRIANGLE = [[0.0, 5.0], [10.0, 5.0], [0.0, 15.0], [0.0, 5.0]]


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


def test_point_in_ring_diagonal_edge_inside_near_origin():
    assert point_in_ring(1.0, 1.0, _TRIANGLE) is True


def test_point_in_ring_diagonal_edge_inside_near_hypotenuse():
    # 4 + 4 = 8 < 10, so just inside the diagonal.
    assert point_in_ring(4.0, 4.0, _TRIANGLE) is True


def test_point_in_ring_diagonal_edge_outside_beyond_hypotenuse():
    # 6 + 6 = 12 > 10 — inside the bounding box, outside the triangle. This is
    # the case that pins the edge-intersection arithmetic.
    assert point_in_ring(6.0, 6.0, _TRIANGLE) is False


def test_point_in_ring_diagonal_edge_outside_far_corner():
    assert point_in_ring(9.0, 9.0, _TRIANGLE) is False


def test_point_in_ring_diagonal_edge_asymmetric_point():
    # Deliberately asymmetric in lon and lat: 8 + 1 = 9 < 10 inside,
    # 1 + 8 = 9 also inside, but they exercise different edges.
    assert point_in_ring(8.0, 1.0, _TRIANGLE) is True
    assert point_in_ring(1.0, 8.0, _TRIANGLE) is True


def test_point_in_ring_diagonal_edge_just_outside_asymmetric():
    assert point_in_ring(9.5, 1.0, _TRIANGLE) is False


def test_point_in_ring_offset_diagonal_inside():
    # At latitude 10 the diagonal sits at longitude 5, so 2 is inside.
    assert point_in_ring(2.0, 10.0, _OFFSET_TRIANGLE) is True


def test_point_in_ring_offset_diagonal_just_outside():
    # 6 is past the edge at longitude 5 — only just, which is what makes this
    # sensitive to the divisor in the intersection formula.
    assert point_in_ring(6.0, 10.0, _OFFSET_TRIANGLE) is False


def test_point_in_ring_offset_diagonal_well_outside():
    assert point_in_ring(9.0, 10.0, _OFFSET_TRIANGLE) is False


def test_point_in_ring_offset_diagonal_near_the_wide_end():
    # Latitude 6 is near the triangle's base, where it is almost full width.
    assert point_in_ring(8.0, 6.0, _OFFSET_TRIANGLE) is True


def test_point_in_ring_offset_diagonal_near_the_narrow_end():
    # Latitude 14 is near the apex, where the shape is only one wide.
    assert point_in_ring(2.0, 14.0, _OFFSET_TRIANGLE) is False


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


def test_point_in_geometry_multipolygon_without_coordinates_is_outside():
    # A typed geometry carrying no coordinates at all must return cleanly rather
    # than raising — iterating None inside the poll loop would lose the forecast.
    assert point_in_geometry(5.0, 5.0, {"type": "MultiPolygon"}) is False


def test_point_in_geometry_polygon_without_coordinates_is_outside():
    assert point_in_geometry(5.0, 5.0, {"type": "Polygon"}) is False

Feature: Point-in-polygon matching for warning areas
  Met Office severe weather warnings arrive as a national feed with a GeoJSON
  MultiPolygon per warning; there is no way to ask the API "what applies at this
  latitude and longitude". Deciding whether a warning covers home or an office is
  therefore done here, in process.

  Ray casting, with no new dependency: a geometry library would be far too heavy
  for a 4GB Pi shared with the budget planner, and the load is trivial — a handful
  of active warnings against at most three points per poll.

  GeoJSON orders coordinates [longitude, latitude], the opposite of how every
  other coordinate in this codebase is carried, so these functions take longitude
  first to force each call site to transpose visibly.

  Scenario: A point inside a simple square is matched
    Given a square polygon
    And a point in the middle of it
    When the point is tested against the polygon
    Then the point is inside

  Scenario: A point outside a simple square is not matched
    Given a square polygon
    And a point beyond its edge
    When the point is tested against the polygon
    Then the point is outside

  Scenario: A point inside a hole is not matched
    Given a square polygon with a square hole cut out of its middle
    And a point inside the hole
    When the point is tested against the polygon
    Then the point is outside

  Scenario: A point inside the ring but outside the hole is matched
    Given a square polygon with a square hole cut out of its middle
    And a point between the outer edge and the hole
    When the point is tested against the polygon
    Then the point is inside

  Scenario: A concave polygon does not match points in its bounding box
    Given an L-shaped polygon
    And a point in the notch of the L
    When the point is tested against the polygon
    Then the point is outside

  Scenario: A closed ring and an open ring give the same result
    Given a square polygon whose first and last coordinates are identical
    And the same polygon without the repeated closing coordinate
    When a point is tested against both
    Then both results are the same

  Scenario: Latitude and longitude are not interchangeable
    Given a polygon spanning longitude -2 to -1 and latitude 51 to 53
    When longitude -1.5 and latitude 52 are tested
    Then the point is inside
    And when the two values are swapped the point is outside

  Scenario: A MultiPolygon matches a point in its second polygon
    Given a MultiPolygon of two separate squares
    And a point inside the second square
    When the point is tested against the geometry
    Then the point is inside

  Scenario: A MultiPolygon does not match a point in neither polygon
    Given a MultiPolygon of two separate squares
    And a point in neither
    When the point is tested against the geometry
    Then the point is outside

  Scenario: A plain Polygon geometry is supported
    Given a geometry of type "Polygon"
    And a point inside it
    When the point is tested against the geometry
    Then the point is inside

  Scenario: An unknown geometry type never matches
    Given a geometry of type "Point"
    When any point is tested against the geometry
    Then the point is outside

  Scenario: An empty coordinates list never matches
    Given a geometry with an empty coordinates list
    When any point is tested against the geometry
    Then the point is outside

  Scenario: A geometry with no type never matches
    Given a geometry dict with no type key
    When any point is tested against the geometry
    Then the point is outside

/**
 * Decode a Google encoded polyline string into an array of [lat, lng] pairs.
 * https://developers.google.com/maps/documentation/utilities/polylinealgorithm
 */
export function decodePolyline(encoded) {
  const result = []
  let index = 0
  let lat = 0
  let lng = 0

  while (index < encoded.length) {
    let shift = 0
    let value = 0
    let byte

    do {
      byte = encoded.charCodeAt(index++) - 63
      value |= (byte & 0x1f) << shift
      shift += 5
    } while (byte >= 0x20)

    lat += value & 1 ? ~(value >> 1) : value >> 1

    shift = 0
    value = 0

    do {
      byte = encoded.charCodeAt(index++) - 63
      value |= (byte & 0x1f) << shift
      shift += 5
    } while (byte >= 0x20)

    lng += value & 1 ? ~(value >> 1) : value >> 1

    result.push([lat / 1e5, lng / 1e5])
  }

  return result
}

import { describe, it, expect } from 'vitest'
import { decodePolyline } from './decodePolyline'

describe('decodePolyline', () => {
  it('returns empty array for empty string', () => {
    expect(decodePolyline('')).toEqual([])
  })

  it('decodes a single point at the origin (0, 0)', () => {
    // '?' = ASCII 63, 63 - 63 = 0 → lat 0, lng 0
    expect(decodePolyline('??')).toEqual([[0, 0]])
  })

  it('decodes a single positive point', () => {
    // 'A' = ASCII 65, 65 - 63 = 2 → value 2, bit 0 clear → delta = 2>>1 = 1 → 1e-5
    expect(decodePolyline('AA')).toEqual([[0.00001, 0.00001]])
  })

  it('decodes a single negative point', () => {
    // '@' = ASCII 64, 64 - 63 = 1 → value 1, bit 0 set → delta = ~(1>>1) = ~0 = -1 → -1e-5
    const result = decodePolyline('@@')
    expect(result[0][0]).toBeCloseTo(-0.00001, 5)
    expect(result[0][1]).toBeCloseTo(-0.00001, 5)
  })

  it('decodes two points using delta encoding', () => {
    // '??' = (0, 0), 'AA' = delta (+1e-5, +1e-5) → second point (1e-5, 1e-5)
    const result = decodePolyline('??AA')
    expect(result).toHaveLength(2)
    expect(result[0]).toEqual([0, 0])
    expect(result[1][0]).toBeCloseTo(0.00001, 5)
    expect(result[1][1]).toBeCloseTo(0.00001, 5)
  })

  it('handles multi-byte chunks (values requiring more than one 5-bit group)', () => {
    // Encode lat=1.0: 1.0 * 1e5 = 100000, <<1 = 200000
    // 200000 in chunks: 0,10,24,3 (with continuation bits) + 63 → '_','i','b','E' for both lat and lng
    const result = decodePolyline('_ibE_ibE')
    expect(result[0][0]).toBeCloseTo(1.0, 4)
    expect(result[0][1]).toBeCloseTo(1.0, 4)
  })
})

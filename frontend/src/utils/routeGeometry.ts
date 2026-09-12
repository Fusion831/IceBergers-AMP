/**
 * AMIP Polar Route Geometry Utilities
 * Generates smooth, continuous hydrodynamic flowing curves from discrete waypoints
 * using Centripetal Catmull-Rom spline interpolation with antimeridian unwrapping.
 *
 * CRITICAL: Every interpolated point is clamped against the Antarctic coastline
 * table so the rendered spline curve NEVER visually crosses continental land —
 * even if the spline would naturally dip south between two safe waypoints.
 */

import COASTLINE_RAW from '../data/antarctica_coastline_table.json';

// Build integer-indexed lookup table: lon (int, -180..180) -> southernmost safe latitude
const COASTLINE_TABLE: Record<number, number> = {};
for (const [k, v] of Object.entries(COASTLINE_RAW as Record<string, number>)) {
  COASTLINE_TABLE[parseInt(k, 10)] = v;
}

/**
 * Returns the northernmost land boundary of Antarctica at the given longitude.
 * Any latitude strictly south of this value is continental ice/land.
 * We keep a 0.30° safety buffer above the raw coastline table value.
 */
function getAntarcticLandLimitLat(lon: number): number {
  // Normalize longitude to [-180, 180]
  const normLon = ((lon % 360) + 540) % 360 - 180;
  const intLon = Math.round(normLon);

  // Known maritime access channel overrides
  if (normLon >= 74.0 && normLon <= 78.0) return -69.45; // Prydz Bay / Bharati anchorage
  if (normLon >= 10.0 && normLon <= 14.0) return -70.05; // India Bay / Maitri maritime access

  return COASTLINE_TABLE[intLon] ?? -65.5;
}

/**
 * Clamp a latitude so it stays at least `buffer` degrees north of the
 * Antarctic land boundary at the given longitude. Only applied south of -55°
 * to avoid false clamping in temperate waters.
 */
function clampAboveLand(lat: number, lon: number, bufferDeg = 0.30): number {
  if (lat > -55.0) return lat; // no clamping needed in open ocean
  const limit = getAntarcticLandLimitLat(lon);
  return Math.max(lat, limit + bufferDeg);
}

export function createSmoothFlowPath(
  points: [number, number][],
  samplesPerSegment = 6
): [number, number][] {
  if (!points || points.length < 2) return points || [];
  if (points.length === 2) {
    // Straight segment: just interpolate and clamp
    const result: [number, number][] = [];
    for (let t = 0; t <= samplesPerSegment; t++) {
      const u = t / samplesPerSegment;
      const lng = points[0][0] + u * (points[1][0] - points[0][0]);
      const rawLat = points[0][1] + u * (points[1][1] - points[0][1]);
      const lat = clampAboveLand(rawLat, lng);
      result.push([Number(lng.toFixed(4)), Number(lat.toFixed(4))]);
    }
    return result;
  }

  // 1. Unwrap longitudes so that antimeridian crossings (-180 / +180) are continuous
  //    This prevents the spline from taking the wrong path around the world.
  const unwrappedLons: number[] = [points[0][0]];
  for (let i = 1; i < points.length; i++) {
    const prev = unwrappedLons[i - 1];
    const curr = points[i][0];
    // Shortest angular difference in [-180, 180]
    const diff = ((curr - prev + 180) % 360 + 360) % 360 - 180;
    unwrappedLons.push(prev + diff);
  }

  const result: [number, number][] = [];

  for (let i = 0; i < points.length - 1; i++) {
    // Catmull-Rom requires the point before and after the segment
    const iMinus1 = Math.max(0, i - 1);
    const iPlus2 = Math.min(points.length - 1, i + 2);

    const p0: [number, number] = [unwrappedLons[iMinus1], points[iMinus1][1]];
    const p1: [number, number] = [unwrappedLons[i], points[i][1]];
    const p2: [number, number] = [unwrappedLons[i + 1], points[i + 1][1]];
    const p3: [number, number] = [unwrappedLons[iPlus2], points[iPlus2][1]];

    for (let t = 0; t < samplesPerSegment; t++) {
      const u = t / samplesPerSegment;
      const u2 = u * u;
      const u3 = u2 * u;

      // Standard Catmull-Rom basis functions (alpha = 0.5)
      const f0 = -0.5 * u3 + u2 - 0.5 * u;
      const f1 = 1.5 * u3 - 2.5 * u2 + 1.0;
      const f2 = -1.5 * u3 + 2.0 * u2 + 0.5 * u;
      const f3 = 0.5 * u3 - 0.5 * u2;

      // Compute spline coordinates in unwrapped longitude space
      const rawLng = f0 * p0[0] + f1 * p1[0] + f2 * p2[0] + f3 * p3[0];
      const rawLat = f0 * p0[1] + f1 * p1[1] + f2 * p2[1] + f3 * p3[1];

      // Re-normalize longitude into [-180, 180] AFTER the spline computation
      const lng = ((rawLng + 180) % 360 + 360) % 360 - 180;

      // CRITICAL: Clamp latitude above the Antarctic land boundary at this longitude
      const lat = clampAboveLand(rawLat, lng);

      result.push([Number(lng.toFixed(4)), Number(lat.toFixed(4))]);
    }
  }

  // Ensure exact destination waypoint is preserved (clamped)
  const lastPt = points[points.length - 1];
  result.push([lastPt[0], clampAboveLand(lastPt[1], lastPt[0])]);

  return result;
}

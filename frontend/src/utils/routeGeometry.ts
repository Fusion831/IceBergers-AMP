/**
 * AMIP Polar Route Geometry Utilities
 * Generates smooth, continuous hydrodynamic flowing curves from discrete waypoints
 * using Catmull-Rom spline interpolation.
 */

export function createSmoothFlowPath(
  points: [number, number][],
  samplesPerSegment = 24
): [number, number][] {
  if (!points || points.length < 3) return points || [];

  const result: [number, number][] = [];

  for (let i = 0; i < points.length - 1; i++) {
    const p0 = i === 0 ? points[0] : points[i - 1];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = i + 2 < points.length ? points[i + 2] : p2;

    for (let t = 0; t < samplesPerSegment; t++) {
      const u = t / samplesPerSegment;
      const u2 = u * u;
      const u3 = u2 * u;

      // Catmull-Rom spline basis formula
      const f0 = -0.5 * u3 + u2 - 0.5 * u;
      const f1 = 1.5 * u3 - 2.5 * u2 + 1.0;
      const f2 = -1.5 * u3 + 2.0 * u2 + 0.5 * u;
      const f3 = 0.5 * u3 - 0.5 * u2;

      const lng = f0 * p0[0] + f1 * p1[0] + f2 * p2[0] + f3 * p3[0];
      const lat = f0 * p0[1] + f1 * p1[1] + f2 * p2[1] + f3 * p3[1];

      result.push([Number(lng.toFixed(5)), Number(lat.toFixed(5))]);
    }
  }

  // Ensure exact final waypoint is preserved at destination
  result.push(points[points.length - 1]);
  return result;
}

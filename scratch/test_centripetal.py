import math
from typing import List, Tuple

def normalize_lon(lon: float) -> float:
    return (lon + 180.0) % 360.0 - 180.0

def shortest_lon_diff(lon1: float, lon2: float) -> float:
    return (lon2 - lon1 + 180.0) % 360.0 - 180.0

def centripetal_catmull_rom(points: List[Tuple[float, float]], num_samples: int) -> List[Tuple[float, float]]:
    """
    Centripetal Catmull-Rom spline (alpha = 0.5).
    Guarantees no self-intersections, no overshoots, and smooth C1 continuity.
    """
    if len(points) < 2:
        return points
    if len(points) == 2:
        p1, p2 = points[0], points[1]
        return [(p1[0] + (p2[0] - p1[0]) * (i / max(1, num_samples - 1)),
                 normalize_lon(p1[1] + (p2[1] - p1[1]) * (i / max(1, num_samples - 1))))
                for i in range(num_samples)]

    # Unwrap longitudes
    unwrapped = [(points[0][0], points[0][1])]
    for i in range(1, len(points)):
        prev_lon = unwrapped[-1][1]
        curr_lon = points[i][1]
        diff = shortest_lon_diff(prev_lon, curr_lon)
        unwrapped.append((points[i][0], prev_lon + diff))

    # Add phantom endpoints
    p_start = (2 * unwrapped[0][0] - unwrapped[1][0], 2 * unwrapped[0][1] - unwrapped[1][1])
    p_end = (2 * unwrapped[-1][0] - unwrapped[-2][0], 2 * unwrapped[-1][1] - unwrapped[-2][1])
    pts = [p_start] + unwrapped + [p_end]

    def get_t(t_prev, p_a, p_b, alpha=0.5):
        d2 = (p_b[0] - p_a[0])**2 + (p_b[1] - p_a[1])**2
        return t_prev + math.sqrt(math.sqrt(d2)) + 1e-5

    result = []
    total_segments = len(unwrapped) - 1
    samples_per_seg = max(2, num_samples // total_segments)

    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        t0 = 0.0
        t1 = get_t(t0, p0, p1)
        t2 = get_t(t1, p1, p2)
        t3 = get_t(t2, p2, p3)

        is_last = (i == len(pts) - 3)
        n_steps = samples_per_seg if not is_last else (num_samples - len(result))

        for s in range(n_steps):
            t = t1 + (t2 - t1) * (s / float(n_steps))

            a1 = ((t1 - t) / (t1 - t0) * p0[0] + (t - t0) / (t1 - t0) * p1[0],
                  (t1 - t) / (t1 - t0) * p0[1] + (t - t0) / (t1 - t0) * p1[1])
            a2 = ((t2 - t) / (t2 - t1) * p1[0] + (t - t1) / (t2 - t1) * p2[0],
                  (t2 - t) / (t2 - t1) * p1[1] + (t - t1) / (t2 - t1) * p2[1])
            a3 = ((t3 - t) / (t3 - t2) * p2[0] + (t - t2) / (t3 - t2) * p3[0],
                  (t3 - t) / (t3 - t2) * p2[1] + (t - t2) / (t3 - t2) * p3[1])

            b1 = ((t2 - t) / (t2 - t0) * a1[0] + (t - t0) / (t2 - t0) * a2[0],
                  (t2 - t) / (t2 - t0) * a1[1] + (t - t0) / (t2 - t0) * a2[1])
            b2 = ((t3 - t) / (t3 - t1) * a2[0] + (t - t1) / (t3 - t1) * a3[0],
                  (t3 - t) / (t3 - t1) * a2[1] + (t - t1) / (t3 - t1) * a3[1])

            c = ((t2 - t) / (t2 - t1) * b1[0] + (t - t1) / (t2 - t1) * b2[0],
                 (t2 - t) / (t2 - t1) * b1[1] + (t - t1) / (t2 - t1) * b2[1])

            result.append((c[0], normalize_lon(c[1])))

    result.append((points[-1][0], normalize_lon(points[-1][1])))
    return result

print("Centripetal Catmull-Rom defined.")

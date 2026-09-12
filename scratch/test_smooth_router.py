import sys, os, math, json
sys.path.extend([
    'packages/core/src', 'packages/domain/src', 'packages/data_access/src',
    'packages/models/src', 'packages/iceberg_physics/src', 'packages/risk_engine/src',
    'packages/routing/src', 'packages/services/src', 'apps/backend/src', '.'
])

from datetime import datetime, timezone
from domain.coordinates import GeoPoint
from domain.vessel import VesselProfile
from domain.enums import RouteObjective
from routing.amip_custom_router import _get_antarctic_land_limit_lat, _ICEBERGS_LIST
from typing import List, Tuple

def normalize_lon(lon: float) -> float:
    return (lon + 180.0) % 360.0 - 180.0

def shortest_lon_diff(lon1: float, lon2: float) -> float:
    return (lon2 - lon1 + 180.0) % 360.0 - 180.0

def haversine_nm(lat1, lon1, lat2, lon2):
    r = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(shortest_lon_diff(lon1, lon2))
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return 2.0 * r * math.asin(math.sqrt(max(0.0, min(1.0, a))))

def spherical_slerp(lat1: float, lon1: float, lat2: float, lon2: float, f: float) -> Tuple[float, float]:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    l1, l2 = math.radians(lon1), math.radians(lon2)
    v1 = (math.cos(p1) * math.cos(l1), math.cos(p1) * math.sin(l1), math.sin(p1))
    v2 = (math.cos(p2) * math.cos(l2), math.cos(p2) * math.sin(l2), math.sin(p2))
    dot = max(-1.0, min(1.0, v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]))
    theta = math.acos(dot)
    if theta < 1e-6:
        return lat1, lon1
    sin_theta = math.sin(theta)
    w1 = math.sin((1.0 - f) * theta) / sin_theta
    w2 = math.sin(f * theta) / sin_theta
    vx = w1 * v1[0] + w2 * v2[0]
    vy = w1 * v1[1] + w2 * v2[1]
    vz = w1 * v1[2] + w2 * v2[2]
    r = math.sqrt(vx*vx + vy*vy + vz*vz)
    lat = math.degrees(math.asin(vz / r))
    lon = math.degrees(math.atan2(vy, vx))
    return lat, normalize_lon(lon)

def catmull_rom_sphere(points: List[Tuple[float, float]], num_samples: int) -> List[Tuple[float, float]]:
    if len(points) < 2:
        return points
    if len(points) == 2:
        return [spherical_slerp(points[0][0], points[0][1], points[1][0], points[1][1], i / max(1, num_samples - 1)) for i in range(num_samples)]
    
    unwrapped_lons = [points[0][1]]
    for i in range(1, len(points)):
        prev_lon = unwrapped_lons[-1]
        curr_lon = points[i][1]
        diff = shortest_lon_diff(prev_lon, curr_lon)
        unwrapped_lons.append(prev_lon + diff)
    
    pts = [(points[i][0], unwrapped_lons[i]) for i in range(len(points))]
    full_pts = [pts[0]] + pts + [pts[-1]]
    
    result = []
    total_segments = len(pts) - 1
    samples_per_seg = max(2, num_samples // total_segments)
    
    for i in range(1, len(full_pts) - 2):
        p0 = full_pts[i - 1]
        p1 = full_pts[i]
        p2 = full_pts[i + 1]
        p3 = full_pts[i + 2]
        is_last_seg = (i == len(full_pts) - 3)
        n_steps = samples_per_seg if not is_last_seg else (num_samples - len(result))
        for s in range(n_steps):
            t = s / float(n_steps)
            t2 = t * t
            t3 = t2 * t
            f0 = -0.5 * t3 + t2 - 0.5 * t
            f1 = 1.5 * t3 - 2.5 * t2 + 1.0
            f2 = -1.5 * t3 + 2.0 * t2 + 0.5 * t
            f3 = 0.5 * t3 - 0.5 * t2
            lat = f0 * p0[0] + f1 * p1[0] + f2 * p2[0] + f3 * p3[0]
            lon = f0 * p0[1] + f1 * p1[1] + f2 * p2[1] + f3 * p3[1]
            result.append((lat, normalize_lon(lon)))
            
    result.append((points[-1][0], normalize_lon(points[-1][1])))
    return result

def smooth_iceberg_avoidance(waypoints: List[Tuple[float, float]], safety_margin_nm: float = 20.0) -> List[Tuple[float, float]]:
    pts = list(waypoints)
    for b in _ICEBERGS_LIST:
        b_lat, b_lon = b["lat"], b["lon"]
        b_radius = b["radius_nm"] + safety_margin_nm
        threat_indices = []
        min_dist = 9999.0
        closest_idx = -1
        for idx, (lat, lon) in enumerate(pts):
            d = haversine_nm(lat, lon, b_lat, b_lon)
            if d < b_radius:
                threat_indices.append(idx)
            if d < min_dist:
                min_dist = d
                closest_idx = idx
        if min_dist < b_radius and closest_idx != -1:
            deflection_needed = (b_radius - min_dist) / 60.0 + 0.30
            sigma = 2.5
            for k in range(max(1, closest_idx - 5), min(len(pts) - 1, closest_idx + 6)):
                factor = math.exp(-0.5 * ((k - closest_idx) / sigma) ** 2)
                cur_lat, cur_lon = pts[k]
                new_lat = min(cur_lat + deflection_needed * factor, -45.0)
                pts[k] = (new_lat, cur_lon)
    return pts

def plan_test_leg(lat1, lon1, lat2, lon2, obj_name):
    lon_diff = shortest_lon_diff(lon1, lon2)
    direct_dist = haversine_nm(lat1, lon1, lat2, lon2)
    
    # Check if direct great-circle cuts land
    crosses_continent = False
    if abs(lon_diff) > 35.0 and (lat1 < -55.0 or lat2 < -55.0):
        crosses_continent = True
    else:
        for f in [0.15, 0.30, 0.50, 0.70, 0.85]:
            i_lat, i_lon = spherical_slerp(lat1, lon1, lat2, lon2, f)
            if i_lat <= _get_antarctic_land_limit_lat(i_lon) + 0.3:
                crosses_continent = True
                break
            if -75.0 <= i_lon <= -53.0 and i_lat < -61.5:
                crosses_continent = True
                break

    if obj_name == 'SHORTEST':
        target_apex = -64.0
        bias = 0.0
    elif obj_name == 'BALANCED':
        target_apex = -63.0
        bias = 1.0
    elif obj_name == 'FASTEST':
        target_apex = -58.5
        bias = 2.5
    elif obj_name == 'SAFEST':
        target_apex = -54.0
        bias = 4.0
    else: # FUEL_EFFICIENT
        target_apex = -56.0
        bias = 2.0

    if not crosses_continent:
        num_pts = max(24, int(direct_dist / 80.0))
        pts = []
        for i in range(num_pts + 1):
            f = i / float(num_pts)
            s_lat, s_lon = spherical_slerp(lat1, lon1, lat2, lon2, f)
            # Gentle oceanic objective curvature
            if -68.0 < s_lat < -35.0:
                s_lat = min(s_lat + math.sin(f * math.pi) * bias, -30.0)
            pts.append((s_lat, s_lon))
    else:
        # Build smooth anchor nodes
        anchors = [(lat1, lon1)]
        # Departure pilotage node easing out of coastal shelf
        if lat1 < -66.0:
            dep_lat = lat1 + 2.0
            dep_lon = normalize_lon(lon1 + 0.15 * lon_diff)
            anchors.append((dep_lat, dep_lon))
        
        # Drake passage checks
        drake_node = (-57.0, -66.0)
        if -75.0 <= lon1 <= -53.0 and not (-75.0 <= lon2 <= -53.0):
            anchors.append(drake_node)
            
        # Circumpolar arc anchors
        start_lon = anchors[-1][1]
        arc_diff = shortest_lon_diff(start_lon, lon2)
        n_anchors = max(4, int(abs(arc_diff) / 14.0))
        for s in range(1, n_anchors):
            f = s / float(n_anchors)
            a_lon = normalize_lon(start_lon + f * arc_diff)
            # Smooth parabolic arc between departure, target_apex, and arrival
            curve = math.sin(f * math.pi)
            interp_base = lat1 + f * (lat2 - lat1)
            a_lat = interp_base + curve * (target_apex - interp_base)
            
            # Keep north of Enderby Land and continental limits
            land_lim = _get_antarctic_land_limit_lat(a_lon)
            a_lat = max(a_lat, land_lim + 0.6)
            if -75.0 <= a_lon <= -53.0:
                a_lat = max(a_lat, -57.5)
            anchors.append((a_lat, a_lon))
            
        if not (-75.0 <= lon1 <= -53.0) and (-75.0 <= lon2 <= -53.0):
            anchors.append(drake_node)
            
        # Arrival pilotage node easing into destination shelf
        if lat2 < -66.0:
            arr_lat = lat2 + 2.0
            arr_lon = normalize_lon(lon2 - 0.15 * lon_diff)
            anchors.append((arr_lat, arr_lon))
            
        anchors.append((lat2, lon2))
        
        num_samples = max(35, int(direct_dist / 65.0))
        pts = catmull_rom_sphere(anchors, num_samples)

    # Apply iceberg avoidance
    pts = smooth_iceberg_avoidance(pts)
    
    # Enforce land safety
    sanitized = []
    for lat, lon in pts:
        coast = _get_antarctic_land_limit_lat(lon)
        s_lat = max(lat, coast + 0.25) if lat < -60.0 else lat
        sanitized.append((round(s_lat, 4), round(lon, 4)))
        
    return sanitized

# Test with Bharati -> Maitri
for obj in ['SHORTEST', 'BALANCED', 'FASTEST', 'SAFEST', 'FUEL_EFFICIENT']:
    res = plan_test_leg(-69.41, 76.19, -69.95, 11.73, obj)
    land_hits = sum(1 for lat, lon in res if lat < _get_antarctic_land_limit_lat(lon) - 0.05)
    berg_hits = 0
    for lat, lon in res:
        for b in _ICEBERGS_LIST:
            d = haversine_nm(lat, lon, b['lat'], b['lon'])
            if d < b['radius_nm'] + 5.0:
                berg_hits += 1
    dist = sum(haversine_nm(res[i][0], res[i][1], res[i+1][0], res[i+1][1]) for i in range(len(res)-1))
    print(f"Bharati->Maitri {obj:15s}: Wps={len(res)}, Dist={dist:.1f} NM, LandHits={land_hits}, BergHits={berg_hits}")

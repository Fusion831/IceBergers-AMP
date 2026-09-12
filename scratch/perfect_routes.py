import json
import math

with open('scratch/coastline_table.json', 'r') as f:
    COASTLINE_TABLE = {int(k): v for k, v in json.load(f).items()}

with open('frontend/src/data/icebergs_all_73.json', 'r') as f:
    icebergs_raw = json.load(f)

ICEBERGS = []
for feat in icebergs_raw.get('features', []):
    b_id = feat.get('id')
    obs = feat.get('latestObservation', {})
    b_lat = obs.get('latitude')
    b_lon = obs.get('longitude')
    l_km = float(obs.get('length_km') or 15.0)
    w_km = float(obs.get('width_km') or 8.0)
    radius_nm = max(6.0, (l_km / 1.852) / 2.0 + 4.0)
    if b_lat is not None and b_lon is not None:
        ICEBERGS.append({
            'id': b_id,
            'lat': float(b_lat),
            'lon': float(b_lon),
            'radius_nm': radius_nm
        })

print(f'Loaded {len(ICEBERGS)} icebergs and {len(COASTLINE_TABLE)} coastline entries.')

def normalize_lon(lon: float) -> float:
    return (lon + 180.0) % 360.0 - 180.0

def shortest_lon_diff(lon1: float, lon2: float) -> float:
    return (lon2 - lon1 + 180.0) % 360.0 - 180.0

def haversine_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians((lon2 - lon1 + 180.0) % 360.0 - 180.0)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return 2.0 * r * math.asin(math.sqrt(max(0.0, min(1.0, a))))

def get_coastline_lat(lon: float) -> float:
    """Returns the northernmost coastline/shelf latitude at this longitude."""
    n_lon = int(round(normalize_lon(lon)))
    # Specific known maritime access channels
    if 74.0 <= lon <= 78.0:
        return -69.45  # Prydz Bay / Bharati anchorage
    if 10.0 <= lon <= 14.0:
        return -70.05  # India Bay / Maitri maritime access
    return COASTLINE_TABLE.get(n_lon, -65.5)

def avoid_icebergs(lat: float, lon: float, safety_margin_nm: float = 18.0) -> tuple[float, float, list]:
    """Nudge point northward if it breaches an iceberg's safety radius."""
    curr_lat, curr_lon = lat, lon
    hits = []
    # Up to 3 avoidance iterations
    for _ in range(3):
        nudged = False
        for b in ICEBERGS:
            d = haversine_distance_nm(curr_lat, curr_lon, b['lat'], b['lon'])
            threat_dist = b['radius_nm'] + safety_margin_nm
            if d < threat_dist:
                hits.append((b['id'], d))
                # Deflect northward into open water
                # 1 degree of latitude is ~60 NM
                deflection_deg = (threat_dist - d) / 60.0 + 0.15
                curr_lat = min(curr_lat + deflection_deg, -45.0)
                nudged = True
        if not nudged:
            break
    return curr_lat, curr_lon, hits

# Test point near Iceberg D37 (-69.21, 36.36)
test_lat, test_lon = -69.21, 36.36
n_lat, n_lon, h = avoid_icebergs(test_lat, test_lon)
print(f'Test near D37: original=({test_lat}, {test_lon}) -> nudged=({n_lat:.2f}, {n_lon:.2f}), avoided: {h}')
d_after = haversine_distance_nm(n_lat, n_lon, -69.21, 36.36)
print(f'Distance from D37 after nudge: {d_after:.1f} NM (safety threshold passed: {d_after >= 24.0})')

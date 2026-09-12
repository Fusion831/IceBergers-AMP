import urllib.request
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
    radius_nm = max(5.0, (l_km / 1.852) / 2.0 + 3.5)
    if b_lat is not None and b_lon is not None:
        ICEBERGS.append({
            'id': b_id,
            'lat': float(b_lat),
            'lon': float(b_lon),
            'radius_nm': radius_nm
        })

def haversine_nm(lat1, lon1, lat2, lon2):
    r = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians((lon2 - lon1 + 180.0) % 360.0 - 180.0)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return 2.0 * r * math.asin(math.sqrt(max(0.0, min(1.0, a))))

def get_coastline_lat(lon):
    n_lon = int(round((lon + 180.0) % 360.0 - 180.0))
    if 74.0 <= lon <= 78.0:
        return -69.45
    if 10.0 <= lon <= 14.0:
        return -70.05
    return COASTLINE_TABLE.get(n_lon, -65.5)

print("=== 1. TESTING CANONICAL ROUTES DATASET ===")
with open('frontend/src/data/canonical_routes.json', 'r') as f:
    canon = json.load(f)

for r_name, r in canon.items():
    wps = r.get('waypoints', [])
    land_hits = 0
    berg_hits = 0
    for lon, lat in wps:
        coast = get_coastline_lat(lon)
        if lat < (coast - 0.05):
            land_hits += 1
        for b in ICEBERGS:
            d = haversine_nm(lat, lon, b['lat'], b['lon'])
            if d < b['radius_nm'] + 5.0:
                berg_hits += 1
    print(f"  {r_name:15s}: Dist={r['distanceNM']} NM, TransitDays={r['transitDays']}d, LandHits={land_hits}, IcebergHits={berg_hits}")

print("\n=== 2. TESTING DYNAMIC PLAN-VOYAGE API ===")
test_pairs = [
    ('bharati', 'maitri'),
    ('cape-town', 'bharati'),
    ('punta-arenas', 'bharati')
]

for orig, dest in test_pairs:
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/v1/routes/plan-voyage',
        data=json.dumps({
            'origin_station_id': orig,
            'destination_station_id': dest,
            'objectives': ['FASTEST', 'SHORTEST', 'SAFEST', 'FUEL_EFFICIENT', 'BALANCED']
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"\nVoyage: {orig} -> {dest} (routes count: {len(data.get('routes', []))})")
        for r in data.get('routes', []):
            obj = r['objective']
            m = r['metrics']
            wps = r['waypoints']
            land_hits = 0
            berg_hits = 0
            for wp in wps:
                pt = wp.get('point') or wp.get('position', {})
                lat = pt.get('latitude')
                lon = pt.get('longitude')
                coast = get_coastline_lat(lon)
                if lat < (coast - 0.05):
                    land_hits += 1
                for b in ICEBERGS:
                    d = haversine_nm(lat, lon, b['lat'], b['lon'])
                    if d < b['radius_nm'] + 5.0:
                        berg_hits += 1
            fuel = m.get('estimated_fuel_mt') or m.get('estimated_fuel_tonnes')
            print(f"  {obj:15s}: Dist={m['distance_nm']} NM, Days={m['duration_days']}d, Fuel={fuel} MT | LandHits={land_hits}, IcebergHits={berg_hits}")

import sys
import os
sys.path.extend([
    os.path.abspath("packages/core/src"),
    os.path.abspath("packages/domain/src"),
    os.path.abspath("packages/data_access/src"),
    os.path.abspath("packages/models/src"),
    os.path.abspath("packages/iceberg_physics/src"),
    os.path.abspath("packages/risk_engine/src"),
    os.path.abspath("packages/routing/src"),
    os.path.abspath("packages/services/src"),
    os.path.abspath("apps/backend/src")
])

import urllib.request
import json
from data_access.environment_provider import default_environment_provider
from domain.coordinates import GeoPoint
from datetime import datetime, timezone

url = 'http://127.0.0.1:8000/api/v1/routes/plan-voyage'
p = {'origin_station_id': 'mcmurdo', 'destination_station_id': 'punta-arenas', 'objectives': ['FASTEST']}
req = urllib.request.Request(url, data=json.dumps(p).encode('utf-8'), headers={'Content-Type': 'application/json'})
r = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
wps = r['routes'][0]['waypoints']

t = datetime(2024, 1, 1, tzinfo=timezone.utc)
land_count = 0
for i, wp in enumerate(wps):
    pt = GeoPoint(latitude=wp['point']['latitude'], longitude=wp['point']['longitude'])
    env = default_environment_provider.get_point_environment(pt, t)
    is_land = env.get("is_land", False)
    depth = env.get("bathymetry_depth_m", 0)
    sic = env.get("sea_ice_concentration", 0)
    if is_land or depth <= 0:
        land_count += 1
    print(f"WP {i:2d}: lat={pt.latitude:6.2f}, lon={pt.longitude:6.2f}, is_land={is_land}, depth={depth:6.1f}m, sic={sic:.2f}")

print(f"\nTotal points over land/shallow ground: {land_count} out of {len(wps)}")

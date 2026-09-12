import sys
sys.path.extend([
    'packages/core/src', 'packages/domain/src', 'packages/data_access/src',
    'packages/models/src', 'packages/iceberg_physics/src', 'packages/risk_engine/src',
    'packages/routing/src', 'packages/services/src', 'apps/backend/src', '.'
])

from datetime import datetime, timezone
from domain.coordinates import GeoPoint
from domain.vessel import VesselProfile
from domain.enums import RouteObjective
from routing.amip_custom_router import AMIPCustomRouter, _get_antarctic_land_limit_lat, _ICEBERGS_LIST
import math

def haversine_nm(lat1, lon1, lat2, lon2):
    r = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians((lon2 - lon1 + 180.0) % 360.0 - 180.0)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return 2.0 * r * math.asin(math.sqrt(max(0.0, min(1.0, a))))

router = AMIPCustomRouter(mode='corridor')
v = VesselProfile()
t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)

p_bharati = GeoPoint(latitude=-69.41, longitude=76.19)
p_maitri = GeoPoint(latitude=-69.95, longitude=11.73)

for obj in [RouteObjective.FASTEST, RouteObjective.SHORTEST, RouteObjective.SAFEST, RouteObjective.FUEL_EFFICIENT, RouteObjective.BALANCED]:
    alt = router.optimize_leg(origin=p_bharati, destination=p_maitri, departure_time=t0, vessel=v, objective=obj)
    wps = [(wp.point.latitude, wp.point.longitude) for wp in alt.waypoints]
    
    land_hits = 0
    iceberg_hits = 0
    for lat, lon in wps:
        coast = _get_antarctic_land_limit_lat(lon)
        if lat < (coast - 0.05):
            land_hits += 1
            print(f"  Land collision at ({lon:.2f}, {lat:.2f}) vs coast {coast:.2f}")
        for b in _ICEBERGS_LIST:
            d = haversine_nm(lat, lon, b['lat'], b['lon'])
            if d < b['radius_nm'] + 5.0:
                iceberg_hits += 1
                b_id = b['id']
                print(f"  Iceberg breach with {b_id} at ({lon:.2f}, {lat:.2f}), dist={d:.1f} NM")

    print(f"{obj.name:15s}: Wps={len(wps)}, Dist={alt.metrics.distance_nm} NM, LandHits={land_hits}, IcebergHits={iceberg_hits}")

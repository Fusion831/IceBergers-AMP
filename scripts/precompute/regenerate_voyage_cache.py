"""
Regenerate and freeze voyage_cache.json with Pareto-consistent multi-objective polar routes.
Covers all 6 gateway ports x 8 Antarctic stations = 48 station pairs x 5 objectives = 240 routes.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.extend([
    str(ROOT_DIR),
    str(ROOT_DIR / 'apps' / 'backend' / 'src'),
    str(ROOT_DIR / 'packages' / 'core' / 'src'),
    str(ROOT_DIR / 'packages' / 'domain' / 'src'),
    str(ROOT_DIR / 'packages' / 'data_access' / 'src'),
    str(ROOT_DIR / 'packages' / 'models' / 'src'),
    str(ROOT_DIR / 'packages' / 'iceberg_physics' / 'src'),
    str(ROOT_DIR / 'packages' / 'risk_engine' / 'src'),
    str(ROOT_DIR / 'packages' / 'routing' / 'src'),
    str(ROOT_DIR / 'packages' / 'services' / 'src'),
])

from routing.amip_custom_router import AMIPCustomRouter
from domain.coordinates import GeoPoint
from domain.vessel import VesselProfile
from domain.enums import RouteObjective
from api.routers.routes import STATIONS_CATALOG

TARGET_CACHE_PATH = ROOT_DIR / "frontend" / "src" / "data" / "voyage_cache.json"

def main():
    origins = [s for s in STATIONS_CATALOG if s["type"] == "Gateway Port"]
    destinations = [s for s in STATIONS_CATALOG if s["type"] == "Antarctic Station"]

    print(f"=== REGENERATING VOYAGE CACHE ===")
    print(f"Origins ({len(origins)}): {[o['id'] for o in origins]}")
    print(f"Destinations ({len(destinations)}): {[d['id'] for d in destinations]}")
    print(f"Total pairs to compute: {len(origins) * len(destinations)}")

    router = AMIPCustomRouter(mode="corridor")
    vessel = VesselProfile()
    dep_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

    cache: dict = {}
    pair_count = 0

    for orig in origins:
        orig_pt = GeoPoint(latitude=orig["latitude"], longitude=orig["longitude"])
        for dest in destinations:
            pair_count += 1
            pair_key = f"{orig['id']}|{dest['id']}"
            dest_pt = GeoPoint(latitude=dest["latitude"], longitude=dest["longitude"])

            # Compute Pareto-enforced multi-objective alternatives
            alternatives = router.optimize_all_alternatives(
                origin=orig_pt,
                destination=dest_pt,
                departure_time=dep_time,
                vessel=vessel,
                objectives=[
                    RouteObjective.FASTEST,
                    RouteObjective.SAFEST,
                    RouteObjective.SHORTEST,
                    RouteObjective.FUEL_EFFICIENT,
                    RouteObjective.BALANCED,
                ],
            )

            serialized_routes = [alt.model_dump(mode="json") for alt in alternatives]

            cache[pair_key] = {
                "origin": {"name": orig["name"], "latitude": orig["latitude"], "longitude": orig["longitude"]},
                "destination": {"name": dest["name"], "latitude": dest["latitude"], "longitude": dest["longitude"]},
                "departure_time": dep_time.isoformat(),
                "vessel_id": "sagar-kanya",
                "routes": serialized_routes,
            }

            # Quick status line
            shortest_m = next(r["metrics"] for r in serialized_routes if r["objective"] == "SHORTEST")
            fastest_m = next(r["metrics"] for r in serialized_routes if r["objective"] == "FASTEST")
            print(f"[{pair_count:02d}/48] {pair_key:<25} | Shortest: {shortest_m['distance_nm']} nm | Fastest: {fastest_m['duration_days']} d")

    # Serialize to target file
    print(f"\nWriting cache to {TARGET_CACHE_PATH}...")
    with open(TARGET_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

    file_size_mb = os.path.getsize(TARGET_CACHE_PATH) / (1024 * 1024)
    print(f"SUCCESS: {len(cache)} pairs saved. File size: {file_size_mb:.2f} MB")

if __name__ == "__main__":
    main()
